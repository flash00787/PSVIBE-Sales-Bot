"""
PS Vibe Customer Bot — Gemini AI integration.
System prompt builder, Gemini client, _ai_reply(), search_member, rate limiting.
"""
import asyncio
import hashlib
import json
import logging
import os
import re
import time
import urllib.request
import urllib.error
from typing import Optional

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ── Model Fallback Chain ──────────────────────────────────────────────────────
# Tried in order. First success wins.
MODEL_CHAIN = [
    # Top 3 Gemini models (best Burmese → fallback)
    {"provider": "gemini",       "model": "gemini-3.5-flash"},
    {"provider": "gemini",       "model": "gemini-3.1-flash-lite"},
    {"provider": "gemini",       "model": "gemini-2.5-flash"},
    # DeepSeek via OpenRouter (last resort)
    {"provider": "openrouter",   "model": "deepseek/deepseek-v4-flash"},
]

try:
    from google import genai as _genai
    from google.genai import types as _genai_types
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False
    logging.warning("google-genai not installed — AI replies disabled")

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from .data.prompts import now_mmt, _build_ai_system_prompt, _detect_sentiment
from . import api as _api

# ── AI Query Cache ────────────────────────────────────────────────────────────
_ai_query_cache: dict[str, dict] = {}
_AI_QUERY_CACHE_TTL = 120  # seconds


def _get_cached_ai(query: str, system_prompt: str) -> Optional[str]:
    """Return cached response if within TTL, else None."""
    key = hashlib.md5(f"{query}:{system_prompt}".encode()).hexdigest()
    entry = _ai_query_cache.get(key)
    if entry and time.time() - entry["ts"] < _AI_QUERY_CACHE_TTL:
        return entry["response"]
    return None


def _set_cached_ai(query: str, system_prompt: str, response: str) -> None:
    """Store AI response in cache."""
    key = hashlib.md5(f"{query}:{system_prompt}".encode()).hexdigest()
    _ai_query_cache[key] = {"response": response, "ts": time.time()}


# ── Gemini Client ─────────────────────────────────────────────────────────────
_gemini_client: Optional["_genai.Client"] = None
_client_init_lock = asyncio.Lock()  # Prevent init race

async def _get_gemini_client() -> Optional["_genai.Client"]:
    global _gemini_client
    async with _client_init_lock:
        if _gemini_client is not None:
            return _gemini_client
        if not _GEMINI_AVAILABLE or not GEMINI_API_KEY:
            return None
        try:
            _gemini_client = _genai.Client(api_key=GEMINI_API_KEY)
            logging.info("Gemini AI client ready (gemini-2.5-flash)")
        except Exception as e:
            logging.error("Gemini client init failed: %s", e)
    return _gemini_client


# ── Rate Limiting — per-user AI cooldown (1 call per 3 seconds) ───────────────
_ai_last_call: dict[int, float] = {}
_AI_COOLDOWN = 3.0  # seconds


def _check_ai_rate_limit(user_id: int) -> bool:
    """Return True if user is allowed to make an AI call. False if in cooldown."""
    now = asyncio.get_event_loop().time()
    last = _ai_last_call.get(user_id, 0)
    if now - last < _AI_COOLDOWN:
        return False
    _ai_last_call[user_id] = now
    return True


# ── OpenRouter HTTP Client ────────────────────────────────────────────────────

class _TextResponse:
    """Wrapper to make plain-text responses look like Gemini Response objects."""
    def __init__(self, text: str):
        self._text = text

    @property
    def text(self) -> str:
        return self._text

    @property
    def candidates(self) -> list:
        return []


def _contents_to_openrouter_messages(contents: list) -> list[dict]:
    """Convert Gemini Content objects to OpenRouter-compatible message dicts."""
    messages = []
    for c in contents:
        role = c.role
        if role == "model":
            role = "assistant"
        text = ""
        for part in (c.parts or []):
            t = getattr(part, "text", None)
            if t:
                text += t
        messages.append({"role": role, "content": text})
    return messages


def _call_openrouter_sync(messages: list[dict], system_prompt: str, model: str) -> str:
    """Call OpenRouter API synchronously. Returns text content."""
    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            *messages,
        ],
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ps-vibe.com",
            "X-Title": "PS VIBE Customer Bot",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content and data.get("error"):
                raise RuntimeError(f"OpenRouter API error: {data['error']}")
            logging.info("OpenRouter (%s) response: %d chars", model, len(content))
            return content.strip()
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        raise RuntimeError(f"OpenRouter HTTP {e.code}: {err_body}") from e


# ── Member search / rank helpers ──────────────────────────────────────────────

def _compute_rank(net_spend: float, master_threshold: float, immortal_threshold: float) -> str:
    if immortal_threshold > 0 and net_spend >= immortal_threshold:
        return "Immortal"
    if master_threshold > 0 and net_spend >= master_threshold:
        return "Master"
    return "Warrior"


async def _search_member(query: str) -> dict:
    """Search member by ID, phone, or name. Returns profile dict."""
    members = await _api._fetch_members()
    q = query.strip()
    q_norm  = q.upper().replace(" ", "").replace("-", "").replace("_", "")
    q_phone = q.replace(" ", "").replace("-", "")
    q_lower = q.lower()

    cfg = await _api._fetch_config()
    master_thr   = float(cfg.get("master_threshold", 0) or 0)
    immortal_thr = float(cfg.get("immortal_threshold", 0) or 0)

    matches = []
    for mid, m in members.items():
        mid_norm = mid.upper().replace(" ", "").replace("-", "").replace("_", "")
        m_phone  = (m.get("phone") or "").strip().replace(" ", "").replace("-", "")
        m_name   = (m.get("name")  or "").strip().lower()

        id_hit    = q_norm == mid_norm
        phone_hit = q_phone and q_phone == m_phone
        name_hit  = q_lower and (q_lower == m_name or
                                  (len(q_lower) >= 3 and q_lower in m_name))

        if id_hit or phone_hit or name_hit:
            net_spend = float(m.get("net_spend", 0) or 0)
            rank      = _compute_rank(net_spend, master_thr, immortal_thr)
            matches.append({
                "member_id":    mid,
                "name":         m.get("name", ""),
                "phone":        m.get("phone", ""),
                "balance_mins": int(m.get("wallet_mins", 0)),
                "rank":         rank,
                "net_spend":    int(net_spend),
            })

    if not matches:
        return {"found": False, "query": q}
    if len(matches) == 1:
        result = {"found": True, "count": 1, **matches[0]}
        if matches[0]["balance_mins"] < 30:
            result["suggest_topup"] = True
        return result
    return {
        "found": True, "count": len(matches), "multiple": True,
        "matches": [
            {"member_id": m["member_id"], "name": m["name"],
             "phone": m["phone"], "rank": m["rank"]}
            for m in matches[:5]
        ],
    }


# ── Search Tool Definition ────────────────────────────────────────────────────

_SEARCH_TOOL = None
_search_tool_lock = asyncio.Lock()

async def _build_search_tool():
    global _SEARCH_TOOL
    async with _search_tool_lock:
        if _SEARCH_TOOL is not None:
            return _SEARCH_TOOL
        if not _GEMINI_AVAILABLE:
            return None
        _SEARCH_TOOL = _genai_types.Tool(
            function_declarations=[
                _genai_types.FunctionDeclaration(
                    name="search_member",
                    description=(
                        "Look up a PS Vibe member's full profile from Google Sheets — "
                        "returns balance_mins (remaining gaming minutes), rank (Warrior/Master/Immortal), "
                        "net_spend (total spend), name, phone, and member_id. "
                        "ALWAYS call this for ANY question about a specific member's balance, rank, tier, "
                        "benefits, or status. Never guess or assume member data."
                    ),
                    parameters=_genai_types.Schema(
                        type=_genai_types.Type.OBJECT,
                        properties={
                            "query": _genai_types.Schema(
                                type=_genai_types.Type.STRING,
                                description="Search term: Member ID (e.g. PSV-001), phone, or full name",
                            )
                        },
                        required=["query"],
                    ),
                )
            ]
        )
    return _SEARCH_TOOL


# ── MarkdownV2 escape ─────────────────────────────────────────────────────────

def _to_mdv2(text: str) -> str:
    """Escape text for Telegram MarkdownV2, preserving *bold* markers."""
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text, flags=re.DOTALL)
    parts = re.split(r'(\*[^*\n]+\*)', text)
    _esc_all   = re.compile(r'([_*\[\]()~`>#+\-=|{}.!\\])')
    _esc_inner = re.compile(r'([_\[\]()~`>#+\-=|{}.!\\])')
    out = []
    for part in parts:
        if re.match(r'^\*[^*\n]+\*$', part):
            inner = _esc_inner.sub(r'\\\1', part[1:-1])
            out.append(f'*{inner}*')
        else:
            out.append(_esc_all.sub(r'\\\1', part))
    return ''.join(out)


# ── AI Reply ──────────────────────────────────────────────────────────────────

def _resp_text(resp) -> str:
    """Extract text from Gemini response robustly."""
    try:
        t = resp.text
        if t:
            return t.strip()
    except Exception as e:
        logging.exception("_extract_resp_text: resp.text failed: %s", e)
    for cand in (resp.candidates or []):
        for part in (cand.content.parts or []):
            pt = getattr(part, "text", None)
            if pt:
                return pt.strip()
    return ""


# Cached system prompts (rebuilt every 60s)
_prompt_cache: dict[str, tuple[float, str]] = {}
_PROMPT_CACHE_TTL = 60  # seconds


async def _get_cached_system_prompt(priority_care: bool = False) -> str:
    """Return cached or freshly-built system prompt. 60s TTL."""
    now = asyncio.get_event_loop().time()
    cache_key = f"_ai_prompt_{priority_care}_{now_mmt().hour}"
    cached = _prompt_cache.get(cache_key)
    if cached and (now - cached[0]) < _PROMPT_CACHE_TTL:
        return cached[1]

    # Need button label references for the prompt
    from .handlers import BTN_CONTACT, BTN_GAMES

    prompt = await _build_ai_system_prompt(
        priority_care=priority_care,
        fetch_config_fn=_api._fetch_config,
        build_rate_lines_fn=_api._build_rate_lines,
        build_bonus_table_fn=_api._build_bonus_table_text,
        fetch_games_full_fn=_api._fetch_games_full,
        build_live_game_library_fn=_build_live_game_library_sync,
        btc_contact=BTN_CONTACT,
        btn_games=BTN_GAMES,
    )
    _prompt_cache[cache_key] = (now, prompt)
    return prompt


async def _build_live_game_library_sync(games):
    """Bridge: use data/games.py builder with already-fetched games."""
    from .data.games import _build_live_game_library_text
    return _build_live_game_library_text(lambda: games)


async def _ai_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
    user_text: str, priority_care: bool = False,
) -> None:
    """Pass free-text message to Gemini AI and reply; supports search_member tool."""
    from .handlers import show_main_menu

    # Rate limit check
    user_id = update.effective_user.id
    if not _check_ai_rate_limit(user_id):
        # Silently skip — user is sending too fast
        logging.info("AI rate limit hit for user %s", user_id)
        return

    client = await _get_gemini_client()
    if not client:
        await show_main_menu(update, context)
        return

    search_tool = await _build_search_tool()
    system_prompt = await _get_cached_system_prompt(priority_care)

    # ── Check AI query cache (skip Gemini for duplicate queries within 120s) ───
    cached_reply = _get_cached_ai(user_text, system_prompt)
    if cached_reply:
        logging.info("AI cache HIT for user %s — returning cached response", user_id)
        reply_mdv2 = _to_mdv2(cached_reply)

        # Log to sheet + track usage
        user = update.effective_user
        user_name = (user.full_name if user else "") or "Unknown"
        asyncio.create_task(_api.log_to_sheet(
            user_name, user_text, cached_reply, "neutral",
            tg_id=str(user.id) if user else "", username=(user.username or "") if user else "",
        ))
        asyncio.create_task(_api.track_usage(user, "ai_chat_cached"))

        try:
            await update.message.reply_text(reply_mdv2, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            logging.exception("send_reply_markdown failed, falling back to raw: %s", e)
            await update.message.reply_text(cached_reply)
        return

    # ── Typing indicator loop ─────────────────────────────────────────────────
    _typing_active = True

    async def _keep_typing():
        while _typing_active:
            try:
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id, action="typing"
                )
            except Exception as e:
                logging.exception("_keep_typing: send_chat_action failed: %s", e)
            await asyncio.sleep(4)

    _typing_task = asyncio.create_task(_keep_typing())

    try:
        # ── Chat history (last 4 turns, 8 items) ──────────────────────────────
        if "ai_history" not in context.user_data:
            context.user_data["ai_history"] = []
        raw_history: list[dict] = context.user_data["ai_history"][-8:]
        history = [
            _genai_types.Content(role=h["role"], parts=[_genai_types.Part(text=h["text"])])
            for h in raw_history
        ]

        # ── Call AI (with function calling) using model fallback chain ────────
        def _call_gemini_sync():
            """Turn 1: intent detection with tools. Tries MODEL_CHAIN in order."""

            def _gen_with_model(contents, config, model, retries=4, backoff=1):
                """Call Gemini with retries for transient errors."""
                for attempt in range(retries):
                    try:
                        return client.models.generate_content(
                            model=model,
                            contents=contents,
                            config=config,
                        )
                    except Exception as _exc:
                        err = str(_exc)
                        if attempt < retries - 1 and (
                            "503" in err or "UNAVAILABLE" in err or "502" in err
                        ):
                            import time as _time
                            logging.warning(
                                "Gemini %s on attempt %d — retrying in %ds",
                                err[:60], attempt + 1, backoff,
                            )
                            _time.sleep(backoff)
                            backoff = min(backoff * 2, 4)
                        else:
                            raise

            cfg_tools = _genai_types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=[search_tool] if search_tool else [],
                max_output_tokens=300,
                temperature=0.7,
                thinking_config=_genai_types.ThinkingConfig(thinking_budget=0),
            )
            base_contents: list = list(history) + [
                _genai_types.Content(
                    role="user", parts=[_genai_types.Part(text=user_text)],
                )
            ]

            last_error = None
            for entry in MODEL_CHAIN:
                try:
                    if entry["provider"] == "openrouter":
                        # OpenRouter: direct text response, no function calling
                        logging.info(
                            "Turn 1: trying OpenRouter %s (no function calling)",
                            entry["model"],
                        )
                        or_messages = _contents_to_openrouter_messages(base_contents)
                        text = _call_openrouter_sync(
                            or_messages, system_prompt, entry["model"]
                        )
                        return _TextResponse(text), None, None
                    else:
                        # Gemini: full SDK call with function calling
                        logging.info("Turn 1: trying Gemini %s", entry["model"])
                        resp = _gen_with_model(
                            base_contents, cfg_tools, entry["model"]
                        )

                        # Detect function call
                        fn_call = None
                        query = None
                        cand0_parts = []
                        if resp.candidates:
                            cand0_parts = getattr(
                                getattr(resp.candidates[0], "content", None),
                                "parts", None,
                            ) or []
                        for part in cand0_parts:
                            fc = getattr(part, "function_call", None)
                            if fc and getattr(fc, "name", ""):
                                fn_call = fc
                                query = (fc.args.get("query") or "").strip()
                                break

                        if fn_call and fn_call.name == "search_member":
                            return resp, fn_call, query

                        return resp, None, None

                except Exception as exc:
                    err = str(exc)
                    logging.warning(
                        "Turn 1: provider %s/%s failed: %s",
                        entry["provider"], entry["model"], err[:120],
                    )
                    last_error = exc
                    continue

            # All providers in chain failed
            logging.error(
                "Turn 1: ALL models in chain failed, last error: %s", last_error,
            )
            return _TextResponse(""), None, None

        # Run Gemini in thread (SDK is sync)
        resp, fn_call, search_query = await asyncio.to_thread(_call_gemini_sync)

        if fn_call and search_query:
            try:
                fn_result = await _search_member(search_query)
            except Exception as exc:
                logging.warning("search_member error: %s", exc)
                fn_result = {"found": False, "query": search_query}

            logging.info("search_member(%r) → %s", search_query, fn_result)

            # Turn 2: fresh TEXT-ONLY call with member data as context
            # Uses the same MODEL_CHAIN fallback
            def _call_gemini_with_result():
                """Turn 2: text-only response with member data. Tries MODEL_CHAIN."""
                cfg_text = _genai_types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=300,
                    temperature=0.7,
                    thinking_config=_genai_types.ThinkingConfig(thinking_budget=0),
                )

                fn_json = json.dumps(fn_result, ensure_ascii=False)
                augmented_msg = (
                    f"{user_text}\n\n"
                    f"[Member lookup result: {fn_json}]\n\n"
                    "Please respond to the customer with their balance and rank "
                    "information in Burmese, using the data above."
                )

                contents = list(history) + [
                    _genai_types.Content(
                        role="user",
                        parts=[_genai_types.Part(text=augmented_msg)],
                    ),
                ]

                for entry in MODEL_CHAIN:
                    try:
                        if entry["provider"] == "openrouter":
                            logging.info(
                                "Turn 2: trying OpenRouter %s", entry["model"],
                            )
                            or_messages = _contents_to_openrouter_messages(contents)
                            text = _call_openrouter_sync(
                                or_messages, system_prompt, entry["model"],
                            )
                            return _TextResponse(text)
                        else:
                            # Gemini with retries
                            logging.info("Turn 2: trying Gemini %s", entry["model"])
                            for attempt in range(4):
                                try:
                                    return client.models.generate_content(
                                        model=entry["model"],
                                        contents=contents,
                                        config=cfg_text,
                                    )
                                except Exception as _exc:
                                    err = str(_exc)
                                    if attempt < 3 and (
                                        "503" in err or "UNAVAILABLE" in err or "502" in err
                                    ):
                                        import time as _time
                                        backoff = min(2 ** attempt, 4)
                                        logging.warning(
                                            "Gemini Turn2 %s on attempt %d — retrying in %ds",
                                            err[:60], attempt + 1, backoff,
                                        )
                                        _time.sleep(backoff)
                                    else:
                                        raise
                    except Exception as exc:
                        err = str(exc)
                        logging.warning(
                            "Turn 2: provider %s/%s failed: %s",
                            entry["provider"], entry["model"], err[:120],
                        )
                        continue

                # All providers failed in Turn 2
                logging.error("Turn 2: ALL models in chain failed")
                return _TextResponse("")

            resp = await asyncio.to_thread(_call_gemini_with_result)

        # Extract reply text once; log diagnostics when empty (fallback)
        reply_raw = _resp_text(resp)
        is_fallback = not reply_raw
        if is_fallback:
            cands = getattr(resp, "candidates", []) or []
            finish = getattr(cands[0], "finish_reason", "?") if cands else "no-candidates"
            parts_info = []
            if cands:
                for p in (getattr(getattr(cands[0], "content", None), "parts", None) or []):
                    fc_name = getattr(getattr(p, "function_call", None), "name", "")
                    parts_info.append(f"fn:{fc_name}" if fc_name else f"text:{bool(getattr(p,'text',''))}")
            logging.warning("Empty final response — finish=%s parts=%s", finish, parts_info)
            reply_raw = "😔 AI reply ပေးရာတွင် ပြဿနာ ဖြစ်ပေါ်ခဲ့သည်။ ခဏကြာ ပြန်ကြိုးစားပါ။"

        # ── Store in AI query cache (non-fallback only) ──────────────────────
        if not is_fallback:
            _set_cached_ai(user_text, system_prompt, reply_raw)

        # Stop typing indicator
        _typing_active = False
        _typing_task.cancel()

        reply_mdv2 = _to_mdv2(reply_raw)

        # Fire-and-forget logging
        user = update.effective_user
        user_name = (user.full_name if user else "") or "Unknown"
        sentiment_label = "frustrated" if priority_care else "neutral"
        tg_id_str = str(user.id) if user else ""
        username_str = (user.username or "") if user else ""

        asyncio.create_task(_api.log_to_sheet(
            user_name, user_text, reply_raw, sentiment_label,
            tg_id=tg_id_str, username=username_str,
        ))
        asyncio.create_task(_api.track_usage(user, "ai_chat"))

        # Update conversation history — skip fallback to avoid poisoning
        if not is_fallback:
            context.user_data["ai_history"] = (raw_history + [
                {"role": "user",  "text": user_text},
                {"role": "model", "text": reply_raw},
            ])[-8:]

        # Send reply
        try:
            await update.message.reply_text(reply_mdv2, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            logging.exception("send_reply_markdown failed, falling back to raw: %s", e)
            await update.message.reply_text(reply_raw)

    except Exception as e:
        _typing_active = False
        try:
            _typing_task.cancel()
        except Exception as _cancel_err:
            logging.exception("_ai_reply: cancel typing task failed: %s", _cancel_err)

        err_str = str(e)
        logging.error("Gemini AI error: %s", e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            delay_match = re.search(r'retry in (\d+)', err_str)
            delay_hint = f" \\({delay_match.group(1)} စက္ကန့်အကြာ ပြန်ကြိုးစားပါ\\)" if delay_match else " \\(မိနစ်အနည်းငယ်အကြာ ပြန်ကြိုးစားပါ\\)"
            await update.message.reply_text(
                "⏳ AI လက်ရှိ busy ဖြစ်နေပါသည်" + delay_hint + "။ "
                "Menu မှ တစ်ဆင့် ဆက်လက်သုံးနိုင်ပါသည် 👇",
            )
        elif "503" in err_str or "UNAVAILABLE" in err_str:
            await update.message.reply_text(
                "😔 AI service ခဏတာ ရပ်နေပါတယ်ခင်ဗျာ။ မိနစ်အနည်းငယ် ကြာပြီးရင် ပြန်ကြိုးစားပေးပါ။",
            )
        else:
            await update.message.reply_text(
                "😔 ခဏတာ ပြဿနာ တက်နေပါတယ်ခင်ဗျာ။ ကြာနည်းနည်းပြီးရင် ပြန်ကြိုးစားပေးပါ။",
            )
