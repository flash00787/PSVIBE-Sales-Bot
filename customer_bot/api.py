"""
PS Vibe Customer Bot — Async API layer (aiohttp).
Replaces urllib.request + asyncio.to_thread() with native async HTTP.

Provides:
  - _api_get / _api_post / _api_patch / _api_delete / _tg_send
  - In-memory cache (asyncio.Lock for thread safety)
  - Cached fetchers: _fetch_games, _fetch_games_full, _fetch_members,
    _fetch_consoles, _fetch_contacts, _fetch_config, _fetch_promotions, etc.
  - Rate line builders, bonus table text, game library helpers
"""
import asyncio
import json
import logging
import time
import os
from typing import Optional, Any

import aiohttp

# ── Globals (injected at startup by main.py) ──────────────────────────────────
API_BASE: str = os.environ.get("API_BASE_URL", "").rstrip("/")
_API_KEY: str = ""
CUSTOMER_BOT_TOKEN: str = ""
STAFF_NOTIFY_CHAT: str = ""

# ── In-Memory Cache ───────────────────────────────────────────────────────────
_CACHE: dict = {}
_CACHE_TTL: int = 300  # seconds
_CACHE_LOCK = asyncio.Lock()  # Async lock (was threading.Lock — replaced per refactor spec)

async def _cache_get(key: str) -> Optional[Any]:
    async with _CACHE_LOCK:
        e = _CACHE.get(key)
        if not e:
            return None
        ttl = e.get("ttl", _CACHE_TTL)
        if (time.time() - e["ts"]) < ttl:
            return e["data"]
        return None

async def _cache_set(key: str, data: Any, ttl: int = _CACHE_TTL) -> None:
    async with _CACHE_LOCK:
        _CACHE[key] = {"data": data, "ts": time.time(), "ttl": ttl}

async def _cache_pop(key: str) -> Any:
    async with _CACHE_LOCK:
        return _CACHE.pop(key, None)


async def _cache_sweeper():
    """Periodically purge stale cache entries (every 5 min)."""
    while True:
        await asyncio.sleep(300)
        async with _CACHE_LOCK:
            now = time.time()
            stale = [k for k, v in _CACHE.items() if now - v["ts"] > v.get("ttl", 300)]
            for k in stale:
                del _CACHE[k]
            if stale:
                logging.info("Cache sweep: removed %d stale entries", len(stale))


# ── Retry constants ───────────────────────────────────────────────────────────
_MAX_RETRIES = 4
_RETRY_BASE_DELAY = 1.0


def _should_retry(status: int | None) -> bool:
    """Return True for transient errors worth retrying."""
    if status is None:
        return True  # network error
    return status >= 500


async def _http_request(
    method: str,
    url: str,
    body: dict | None = None,
    timeout: int = 15,
    headers_extra: dict | None = None,
    api_key: bool = True,
) -> Any:
    """Unified async HTTP with exponential-backoff retry (capped at 4s)."""
    headers = {
        "Content-Type": "application/json",
        **(headers_extra or {}),
    }
    # Add api_key as query parameter (API server uses Depends(verify_api_key) which reads ?api_key=)
    if api_key and _API_KEY:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}api_key={_API_KEY}"
    data = json.dumps(body).encode() if body else None

    for attempt in range(_MAX_RETRIES):
        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.request(
                    method, url, headers=headers, data=data
                ) as resp:
                    if resp.status < 400:
                        text = await resp.text()
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            return text
                    # HTTP error — check if retryable
                    try:
                        err_body = await resp.json()
                    except Exception as e:
                        logging.exception("SILENT_1: api.py: suppressed exception: %s", e)
                        err_body = {"error": f"http_{resp.status}"}
                    err_body["__status__"] = resp.status
                    if not _should_retry(resp.status):
                        logging.warning(
                            "%s %s HTTP %s (non-retryable): %s",
                            method, url, resp.status, err_body,
                        )
                        return err_body
                    # Retryable HTTP error (5xx)
                    if attempt < _MAX_RETRIES - 1:
                        delay = min(_RETRY_BASE_DELAY * (2 ** attempt), 4.0)
                        logging.warning(
                            "%s %s HTTP %s attempt %d/%d, retry in %.1fs",
                            method, url, resp.status, attempt + 1, _MAX_RETRIES, delay,
                        )
                        await asyncio.sleep(delay)
                        continue
                    logging.error(
                        "%s %s HTTP %s FAILED after %d attempts",
                        method, url, resp.status, _MAX_RETRIES,
                    )
                    return err_body
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
            if attempt < _MAX_RETRIES - 1:
                delay = min(_RETRY_BASE_DELAY * (2 ** attempt), 4.0)
                logging.warning(
                    "%s %s attempt %d/%d failed (retry in %.1fs): %s",
                    method, url, attempt + 1, _MAX_RETRIES, delay, e,
                )
                await asyncio.sleep(delay)
                continue
            logging.error(
                "%s %s FAILED after %d attempts: %s",
                method, url, _MAX_RETRIES, e,
            )
            return None
        except Exception as e:
            logging.warning("%s %s unexpected error: %s", method, url, e)
            return None
    return None


# ── Response validation ───────────────────────────────────────────────────────
_HTTP_OK_MIN: int = 200
_HTTP_OK_MAX: int = 299

_Response = Any  # json-parsed dict | str | error dict | None


def unwrap_response(response):
    """Extract data from API response dict.

    If the API wraps responses in {"success": true, "data": ...},
    extract and return the inner ".data" payload.
    """
    if isinstance(response, dict) and "success" in response:
        return response.get("data", response)
    return response



def _is_ok_response(data: _Response) -> bool:
    """Return True if data looks like a successful API response (not error/None)."""
    if data is None:
        return False
    if isinstance(data, dict) and "__status__" in data:
        return False
    return True


def _validate_response(data: _Response, path: str, method: str = "GET") -> _Response:
    """Validate API response; raise ValueError on 4xx/5xx or network failure."""
    if data is None:
        raise ValueError(f"api {method} /api/{path} failed (network/retry-exhausted)")
    if isinstance(data, dict) and "__status__" in data:
        raise ValueError(
            f"api {method} /api/{path} -> HTTP {data['__status__']} {data.get('error', '')}"
        )
    return unwrap_response(data)


# ── Public API helpers ────────────────────────────────────────────────────────

async def _api_get(path: str, timeout: int = 10) -> _Response:
    """Async GET to internal API (default 10s timeout)."""
    if not API_BASE:
        logging.warning("api_get: API_BASE not set")
        return None
    raw = await _http_request("GET", f"{API_BASE}/api/{path}", timeout=timeout)
    return _validate_response(raw, path, "GET")


async def _api_post(path: str, body: dict, timeout: int = 15) -> _Response:
    """Async POST JSON to internal API (default 15s timeout)."""
    if not API_BASE:
        return None
    raw = await _http_request("POST", f"{API_BASE}/api/{path}", body=body, timeout=timeout)
    return _validate_response(raw, path, "POST")


async def _api_patch(path: str, body: dict, timeout: int = 15) -> _Response:
    """Async PATCH JSON to internal API (default 15s timeout)."""
    if not API_BASE:
        return None
    raw = await _http_request("PATCH", f"{API_BASE}/api/{path}", body=body, timeout=timeout)
    return _validate_response(raw, path, "PATCH")


async def _api_put(path: str, timeout: int = 10) -> _Response:
    """Async PUT to internal API (no body, default 10s timeout)."""
    if not API_BASE:
        return None
    raw = await _http_request("PUT", f"{API_BASE}/api/{path}", timeout=timeout)
    return _validate_response(raw, path, "PUT")


async def _api_delete(path: str, timeout: int = 10) -> _Response:
    """Async DELETE to internal API (default 10s timeout)."""
    if not API_BASE:
        return None
    raw = await _http_request("DELETE", f"{API_BASE}/api/{path}", timeout=timeout)
    return _validate_response(raw, path, "DELETE")


async def _tg_send(body: dict, timeout: int = 10) -> _Response:
    """Async send message via Telegram Bot API (default 10s timeout)."""
    return await _http_request(
        "POST",
        f"https://api.telegram.org/bot{CUSTOMER_BOT_TOKEN}/sendMessage",
        body=body,
        timeout=timeout,
        api_key=False,
    )


# ── Cached Fetchers ───────────────────────────────────────────────────────────

async def _fetch_games(console_type: str = "") -> list[str]:
    """Return all game TITLES from Game_Library sheet."""
    all_games = await _fetch_games_full()
    titles = []
    for g in all_games:
        title  = (g.get("title") or "").strip()
        status = (g.get("status") or "").strip()
        if not title:
            continue
        is_not_installed = status.lower() == "not installed"
        has_console      = "C -" in status or "c -" in status.lower()
        is_ref_error     = status == "#REF!"
        if not (is_not_installed or has_console or is_ref_error):
            continue
        titles.append(title)
    return sorted(titles)


async def _fetch_games_full() -> list[dict]:
    """Fetch full game objects (title, platform, genre, players, status, notes) — 10-min cache."""
    cached = await _cache_get("games_full")
    if cached is not None:
        return cached
    try:
        data = await _api_get("fetch_games")
        games = (data or {}).get("data", [])
    except ValueError as e:
        logging.warning("fetch_games_full: %s", e)
        games = []
    await _cache_set("games_full", games, ttl=600)
    return games


async def _fetch_members() -> dict:
    """Fetch member list from API, enrich each ID with detail data.

    Flow:
      1. GET /api/fetch_members  → flat ID list  e.g. ["PSV-001", "PSV-002", ...]
      2. For each ID → GET /api/fetch_member_data/{id}  to get name/phone/wallet/spend
      3. Build and cache {member_id: {name, phone, wallet_mins, net_spend, rank_raw, ...}}
    Cached for 300 s.
    """
    cached = await _cache_get("members")
    if cached is not None:
        return cached

    members: dict = {}
    try:
        # Step 1 — get flat ID list
        ids = await _api_get("fetch_members")
        if not isinstance(ids, list):
            logging.warning("fetch_members: unexpected response type %s", type(ids))
            return {}

        # Step 2 — enrich each ID with member details (concurrency-limited)
        sem = asyncio.Semaphore(10)  # max 10 concurrent detail fetches

        async def _fetch_one(mid: str) -> None:
            async with sem:
                try:
                    detail = await _api_get(f"fetch_member_data/{mid}")
                    detail = (detail or {}).get("data", {}) if isinstance(detail, dict) else {}
                    if isinstance(detail, dict) and "name" in detail:
                        members[mid] = {
                            "name":         detail.get("name", ""),
                            "phone":        detail.get("phone", ""),
                            "email":        detail.get("email", ""),
                            "wallet_mins":  detail.get("wallet_mins", 0),
                            "net_spend":    detail.get("net_spend", 0),
                            "rank_raw":     detail.get("rank_raw", "Warrior"),
                        }
                except ValueError:
                    logging.debug("fetch_members: member %s not found or error", mid)
                except Exception as exc:
                    logging.warning("fetch_members: detail fetch failed for %s: %s", mid, exc)

        tasks = [asyncio.create_task(_fetch_one(mid)) for mid in ids]
        if tasks:
            await asyncio.gather(*tasks)

    except ValueError as e:
        logging.warning("fetch_members: %s", e)

    if members:
        await _cache_set("members", members)
    return members


async def _is_tracked_customer(chat_id: int) -> bool:
    phone = await _get_linked_phone(chat_id)
    return phone is not None


async def _get_linked_phone(chat_id: int) -> str | None:
    """Return phone from most recent non-cancelled booking for this chat_id."""
    try:
        data = await _api_get(f"bookings/search?telegram_chat_id={chat_id}")
    except ValueError as e:
        logging.warning("get_linked_phone: %s", e)
        return None
    if not data:
        return None
    bookings = data if isinstance(data, list) else []
    for b in sorted(bookings, key=lambda x: x.get("createdAt", ""), reverse=True):
        if b.get("status", "") == "cancelled":
            continue
        phone = (b.get("phone") or "").strip()
        if phone:
            return phone
    return None


async def _get_linked_member_id(chat_id: int) -> str | None:
    """Return member_id whose phone matches this chat_id's booking history."""
    phone = await _get_linked_phone(chat_id)
    if not phone:
        return None
    phone_norm = phone.replace(" ", "").replace("-", "")
    members = await _fetch_members()
    for mid, m in members.items():
        m_phone = (m.get("phone") or "").strip().replace(" ", "").replace("-", "")
        if m_phone and m_phone == phone_norm:
            return mid
    return None


async def _fetch_consoles() -> list:
    """Fetch console list from Sheets API (cached)."""
    cached = await _cache_get("consoles")
    if cached is not None:
        return cached
    try:
        data = await _api_get("fetch_console_status")
        raw_consoles = (data or {}).get("data", [])
        consoles = []
        for x in raw_consoles:
            if isinstance(x, dict):
                if "mult" in x and "multiplier" not in x:
                    x["multiplier"] = x.pop("mult")
                consoles.append(x)
    except ValueError as e:
        logging.warning("fetch_consoles: %s", e)
        consoles = []
    if consoles:
        await _cache_set("consoles", consoles)
    return consoles


async def _fetch_contacts() -> list:
    """Fetch admin contacts from Setting sheet (5-min cache)."""
    cached = await _cache_get("contacts")
    if cached is not None:
        return cached
    try:
        data = await _api_get("fetch_staff")
        raw = (data or {}).get("data", [])
        contacts = [{"username": s.get("username", "")} for s in raw if isinstance(s, dict)]
    except ValueError as e:
        logging.warning("fetch_contacts: %s", e)
        contacts = []
    await _cache_set("contacts", contacts, ttl=300)
    return contacts


async def _fetch_promotions() -> list[dict]:
    """Fetch active promotions (60s TTL)."""
    cached = await _cache_get("promotions")
    if cached is not None:
        return cached
    try:
        data = await _api_get("fetch_promotions_cached")
        promos = (data or {}).get("data", [])
    except ValueError as e:
        logging.warning("fetch_promotions: %s", e)
        promos = []
    await _cache_set("promotions", promos, ttl=60)
    return promos


async def _fetch_config() -> dict:
    """Fetch bot config (base_rate, multipliers, etc.) via API (10-min cache)."""
    cached = await _cache_get("config")
    if cached is not None:
        return cached
    try:
        data = await _api_get("sheets/config")
        data = (data or {}).get("data", {}) if isinstance(data, dict) else {}
        if data:
            await _cache_set("config", data, ttl=600)
        return data or {}
    except ValueError as e:
        logging.warning("fetch_config: %s", e)
        return {}


async def _fetch_sales_data() -> dict:
    """Fetch sales data for promotion analytics (30-min cache)."""
    cached = await _cache_get("sales_data")
    if cached is not None:
        return cached
    try:
        raw = await _api_get("analytics/daily_sales")
        raw = (raw or {}).get("data", {}) if isinstance(raw, dict) else {}
        data = {
            "today_sales": raw.get("total_sales_ks", 0),
            "weekly_sales": 0,
            "active_members": raw.get("voucher_count", 0),
            "top_games": [],
        }
        if data:
            await _cache_set("sales_data", data, ttl=1800)
            return data
    except Exception as e:
        logging.warning("fetch_sales_data failed: %s", e)
    return {}


# ── Formatting helpers ────────────────────────────────────────────────────────

async def _build_bonus_table_text(config: dict) -> str:
    """Build human-readable bonus table for AI system prompt."""
    try:
        table = config.get("bonus_table") or []
        if not table:
            return "  (Bonus table not available)"
        header = "  Top-up (Ks)   | Warrior | Master | Immortal"
        sep    = "  " + "-" * 44
        lines  = [header, sep]
        for row in table:
            if len(row) >= 4:
                topup, w, m, i = int(row[0]), int(row[1]), int(row[2]), int(row[3])
                lines.append(f"  {topup:>10,} Ks  | {w:>4} min | {m:>4} min | {i:>5} min")
        return "\n".join(lines)
    except Exception as e:
        logging.exception("SILENT_2: api.py: suppressed exception: %s", e)
        return "  (Bonus table not available)"


async def _build_rate_lines() -> list[str]:
    """Build per-console-type rate lines using base_rate × per-console multiplier."""
    config   = await _fetch_config()
    consoles = await _fetch_consoles()
    base     = config.get("base_rate", 0)
    if not base or not consoles:
        return []

    type_mults: dict[str, set] = {}
    for c in consoles:
        ctype = (c.get("type") or "").strip()
        mult  = c.get("multiplier") or 1.0
        if ctype:
            type_mults.setdefault(ctype, set()).add(float(mult))

    lines = []
    for ctype in sorted(type_mults.keys()):
        mults = sorted(type_mults[ctype])
        icon  = "⭐" if "Pro" in ctype else "🎮"
        if len(mults) == 1:
            rate = int(base * mults[0])
            lines.append(f"   {icon} {ctype} — {rate:,} Ks/hr")
        else:
            lo = int(base * mults[0])
            hi = int(base * mults[-1])
            lines.append(f"   {icon} {ctype} — {lo:,}–{hi:,} Ks/hr")
    return lines


async def _contact_mention() -> str:
    contacts = (await _cache_get("contacts")) or []
    parts = [f"@{c['username']}" for c in contacts if c.get("username")]
    return " | ".join(parts) if parts else "@psvibeofficial"


async def _get_promotion_impact() -> dict:
    promos = await _fetch_promotions()
    sales = await _fetch_sales_data()
    return {
        "active_promotions": len(promos),
        "today_sales": sales.get("today_sales", 0),
        "weekly_sales": sales.get("weekly_sales", 0),
        "members_active": sales.get("active_members", 0),
        "top_games": sales.get("top_games", []),
    }


# ── Logging helpers ───────────────────────────────────────────────────────────

async def log_to_sheet(
    user_name: str, user_query: str, ai_response: str,
    sentiment: str = "neutral", tg_id: str = "", username: str = "",
) -> None:
    """Fire-and-forget: append AI interaction row to Logs sheet."""
    if not API_BASE:
        return
    try:
        await _api_post("sheets/log", {
            "tg_id": tg_id, "username": username,
            "user_name": user_name, "query": user_query[:300],
            "response": ai_response[:500], "sentiment": sentiment,
        })
    except Exception as e:
        logging.warning("log_to_sheet failed: %s", e)


async def track_usage(user, action: str, member_id: str = "", phone: str = "") -> None:
    """Fire-and-forget: upsert user row in Bot_Users sheet."""
    if not API_BASE or not user:
        return
    try:
        await _api_post("bot-users/track", {
            "tg_id": str(user.id),
            "username": user.username or "",
            "user_name": user.full_name or "",
            "action": action,
            "member_id": member_id,
            "phone": phone,
        })
    except Exception as e:
        logging.warning("track_usage failed: %s", e)


# ── Cache warm ────────────────────────────────────────────────────────────────

async def warm_cache() -> None:
    """Pre-fetch slow data at startup."""
    from .data.prompts import now_mmt
    logging.info("Warming cache...")
    await asyncio.gather(
        _fetch_games(),
        _fetch_members(),
        _fetch_consoles(),
        _fetch_contacts(),
        _fetch_config(),
    )
    logging.info(
        "Cache warm — games:%d members:%d contacts:%d",
        len((await _cache_get("games_full")) or []),
        len((await _cache_get("members")) or {}),
        len((await _cache_get("contacts")) or []),
    )

