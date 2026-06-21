
"""PS VIBE Bot — Handler module.
"""
from bot import (
    BTN_BACK, BTN_BACK_MAIN, BTN_CANCEL, BTN_CHANGE_GAME,
    BTN_CONSOLE_INSTALL, BTN_END_SESSION, BTN_GAME_LIB_MENU, BTN_START_SESSION,
    BTN_FOOD_NOTE, BTN_SSD_MANAGE, BTN_STATUS_BOARD, CONSOLE_MENU, END_SESSION_SELECT,
    _delete_session_game,
    _psvibe_get, _psvibe_get_async, add_console_game, _psvibe_post_async,
    calc_duration, cmd_cancel, end_booking, end_booking_async, fetch_console_games,
    fetch_console_status, get_games_on_console, get_games_on_console_async, now_mmt,
    show_console_menu, show_game_menu, show_main_menu,
    prompt_book_console,
)

from bot.api_client import api_fetch_console_status_async
from bot.handlers.booking_flow import _SESSION_TOTAL_MINS, _remind_key
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import asyncio, logging, re, json, time, os
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta

# ── Feedback helpers ──────────────────────────────────────────────────────────
_CUSTOMER_BOT_TOKEN = os.environ.get("CUSTOMER_BOT_TOKEN", "")

async def _send_feedback_to_customer(chat_id: str, booking_id: str):
    """Send a star-rating inline keyboard to a customer after session ends.
    Uses Customer Bot's token so callbacks route to Customer Bot handlers."""
    if not _CUSTOMER_BOT_TOKEN:
        logger.warning("Feedback: CUSTOMER_BOT_TOKEN not set, skipping")
        return
    try:
        import urllib.request as _req
        kb = {
            "inline_keyboard": [[
                {"text": "1 ⭐", "callback_data": f"fb:1:{booking_id}"},
                {"text": "2 ⭐⭐", "callback_data": f"fb:2:{booking_id}"},
                {"text": "3 ⭐⭐⭐", "callback_data": f"fb:3:{booking_id}"},
                {"text": "4 ⭐⭐⭐⭐", "callback_data": f"fb:4:{booking_id}"},
                {"text": "5 ⭐⭐⭐⭐⭐", "callback_data": f"fb:5:{booking_id}"},
            ]]
        }
        payload = json.dumps({
            "chat_id": chat_id,
            "text": (
                "🎮 <b>ဒီနေ့ PS VIBE မှာ ဂိမ်းဆော့ပေးတဲ့အတွက် ကျေးဇူးတင်ပါတယ်!</b>\n\n"
                "အတွေ့အကြုံလေး Rating ပေးပေးပါဦးနော် 🙏"
            ),
            "parse_mode": "HTML",
            "reply_markup": json.dumps(kb),
        }).encode("utf-8")
        url = f"https://api.telegram.org/bot{_CUSTOMER_BOT_TOKEN}/sendMessage"
        req = _req.Request(url, data=payload, headers={"Content-Type": "application/json"})
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, lambda: _req.urlopen(req, timeout=10))
        result = json.loads(resp.read().decode())
        if result.get("ok"):
            logger.info("Feedback sent to chat=%s bk=%s", chat_id, booking_id)
        else:
            logger.warning("Feedback send failed: %s", result.get("description", "unknown"))
    except Exception as e:
        logger.warning("Feedback send error (non-critical): %s", e)



async def cmd_console_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show live console status — uses API (Sheet + PostgreSQL reservations)."""
    await update.message.reply_text("⏳ Console status ဆွဲနေသည်…", parse_mode="Markdown")

    data = await api_fetch_console_status_async()
    api_consoles = (data.get("consoles", []) if isinstance(data, dict) else (data if isinstance(data, list) else []))

    if not api_consoles:
        # Fallback: Google Sheet only (no reservations)
        try:
            raw = fetch_console_status()
            api_consoles = [{"id": c["id"], "type": c.get("type", ""),
                             "liveStatus": c["status"],
                             "member": c.get("member"), "startTime": c.get("start"),
                             "reservedFor": None, "reservedAt": None, "reservedDuration": None}
                            for c in raw]
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            return

    # Normalize API keys -> handler-expected keys (MySQL API returns console_id/status/current_member/start_time)
    _normalized = []
    for _c in api_consoles:
        _st = (_c.get("start_time") or _c.get("startTime") or "")
        _st_dt = _c.get("start_time_dt") or ""
        if "T" in _st:
            try:
                from datetime import datetime as _dt
                _st = _dt.fromisoformat(_st).strftime("%I:%M %p")
            except Exception:
                pass
        elif ":" in _st and not _st.endswith("M"):
            # Convert HH:MM API format to H:MM AM/PM
            try:
                parts = _st.strip().split(":")
                h, m = int(parts[0]), int(parts[1][:2])
                ampm = "AM" if h < 12 else "PM"
                h12 = h % 12
                if h12 == 0:
                    h12 = 12
                _st = f"{h12}:{m:02d} {ampm}"
            except Exception:
                pass
        _normalized.append({
            "id": _c.get("console_id") or _c.get("id", "?"),
            "type": _c.get("console_type") or _c.get("type", ""),
            "liveStatus": _c.get("status") or _c.get("liveStatus", "Free"),
            "member": _c.get("current_member") or _c.get("member"),
            "startTime": _st,
            "startTimeDt": _st_dt,
            "durationMins": _c.get("duration_mins") or 0,
            "reservedFor": _c.get("reservedFor") or _c.get("reserved_for"),
            "reservedAt": _c.get("reservedAt") or _c.get("reserved_at"),
            "reservedDuration": _c.get("reservedDuration") or _c.get("reserved_duration"),
            "staff_name": _c.get("staff_name"),
            "booking_id": _c.get("booking_id"),
        })
    api_consoles = _normalized

    free_list  = [c for c in api_consoles if c.get("liveStatus", "Free") == "Free"]
    busy_list  = [c for c in api_consoles if c.get("liveStatus", "Free") in ("Active", "Scheduled")]
    rsv_list   = [c for c in api_consoles if c.get("liveStatus", "Free") == "Reserved"]

    now_str = now_mmt().strftime("%I:%M %p")
    lines = [
        f"🕹️ *Console Status Board*  |  {now_str} MMT",
        "━━━━━━━━━━━━━━━━━━",
        f"✅ Free: {len(free_list)}  |  🔴 Active: {len(busy_list)}  |  🟡 Reserved: {len(rsv_list)}",
        "━━━━━━━━━━━━━━━━━━",
    ]

    for c in sorted(api_consoles, key=lambda x: x.get("id", "")):
        cid    = c.get("id", "?")
        ctype  = c.get("type", "")
        live   = c.get("liveStatus", "Free")
        ctype_str = f" ({ctype})" if ctype else ""

        if live == "Free":
            icon   = "🟢"
            detail = "Free"
        elif live == "Reserved":
            icon      = "🟡"
            rsv_who   = c.get("reservedFor") or c.get("member") or "Guest"
            rsv_at    = c.get("reservedAt") or c.get("startTime") or "—"
            # Calculate end time (only if we have a valid start time)
            dur = c.get("reservedDuration") or c.get("durationMins") or 60
            try:
                dur = int(dur)
            except (ValueError, TypeError):
                dur = 60
            if rsv_at == "—" or ":" not in rsv_at:
                time_range = rsv_at
            else:
                try:
                    # Parse rsv_at which is already AM/PM format
                    rsv_clean = rsv_at.replace(" AM","").replace(" PM","")
                    sh, sm = map(int, rsv_clean.split(":"))
                    is_pm = "PM" in rsv_at
                    if is_pm and sh != 12:
                        sh += 12
                    elif not is_pm and sh == 12:
                        sh = 0
                    total_m = sh * 60 + sm + dur
                    end_h = total_m // 60
                    end_m = total_m % 60
                    end_ampm = "AM" if end_h < 12 else "PM"
                    end_h12 = end_h % 12
                    if end_h12 == 0:
                        end_h12 = 12
                    end_str = f"{end_h12}:{end_m:02d} {end_ampm}"
                    time_range = f"{rsv_at}–{end_str}"
                except Exception as e:
                    logger.error("cmd_console_status: %s", e, exc_info=True)
                    time_range = rsv_at
            detail = f"Reserved {time_range} — {rsv_who}"
        else:
            icon   = "🔴"
            mbr    = c.get("member") or "Guest"

            # ── Timer calculation ──
            timer_str = ""
            st_dt = c.get("startTimeDt", "")
            try:
                dur_mins = int(c.get("durationMins") or 0)
            except (ValueError, TypeError):
                dur_mins = 0
            since = f" since {c['startTime']}" if c.get("startTime") else ""
            if st_dt:
                try:
                    from datetime import datetime as _dt, timezone, timedelta
                    def _fmt(m: int) -> str:
                        hh = m // 60
                        rr = m % 60
                        if hh > 0 and rr > 0: return f"{hh}h{rr}m"
                        if hh > 0: return f"{hh}h"
                        return f"{m}m"
                    _start = _dt.strptime(st_dt, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=6, minutes=30)))
                    _now = now_mmt()  # offset-aware
                    _elapsed = int((_now - _start).total_seconds() // 60)
                    if dur_mins > 0:
                        _remaining = max(0, dur_mins - _elapsed)
                        _end_dt = _start + timedelta(minutes=dur_mins)
                        _end_str = _end_dt.strftime("%I:%M %p").lstrip("0")
                        if _elapsed < dur_mins:
                            timer_str = f"  ⏱ {_fmt(_elapsed)}/{_fmt(dur_mins)} ({_fmt(_remaining)} left · ends {_end_str})"
                        else:
                            _over = _elapsed - dur_mins
                            timer_str = f"  ⏱ {_fmt(_elapsed)}/{_fmt(dur_mins)} (OVER +{_fmt(_over)} · was {_end_str})"
                    else:
                        timer_str = f"  ⏱ {_fmt(_elapsed)} elapsed"
                except Exception as e:
                    logger.error("cmd_console_status timer: %s", e, exc_info=True)

            detail = f"Active — {mbr}{since}{timer_str}"

        # For Active consoles, show current session game only
        game_str = ""
        if live in ("Active", "Scheduled"):
            session_games = [
                r["game_title"] for r in fetch_console_games()
                if r.get("console_id","").upper() == cid.upper()
                and r.get("install_type") == "Session"
                and r.get("game_title")
            ]
            if session_games:
                game_str = "\n    🎮 " + session_games[0]

        lines.append(f"{icon} *{cid}*{ctype_str}: {detail}{game_str}")

    full_msg = "\n".join(lines)
    if len(full_msg) > 4000:
        chunks = []
        current = ""
        for line in lines:
            if len(current) + len(line) + 1 > 4000 and current:
                chunks.append(current)
                current = line
            else:
                current = current + "\n" + line if current else line
        if current:
            chunks.append(current)
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode="Markdown")
    else:
        await update.message.reply_text(full_msg, parse_mode="Markdown")

async def show_console_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Console Management submenu — accessible from Main Menu and Admin Panel."""
    kb = [
        [BTN_START_SESSION,  BTN_END_SESSION],
        [BTN_FOOD_NOTE,      BTN_STATUS_BOARD],
        [BTN_CONSOLE_INSTALL, BTN_SSD_MANAGE],
        [BTN_GAME_LIB_MENU,  BTN_BACK_MAIN],
    ]
    await update.message.reply_text(
        "🕹️ *Console Management*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Action ရွေးပါ ↓",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return CONSOLE_MENU

async def step_console_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.handlers.main_menu import show_main_menu
    from bot.handlers.games import show_game_menu
    from bot.handlers.ginst import show_ginst_menu
    choice = update.message.text.strip()
    if choice == BTN_BACK_MAIN:
        return await show_main_menu(update, context)
    if choice == BTN_START_SESSION:
        return await prompt_book_console(update, context)
    if choice == BTN_END_SESSION:
        return await prompt_end_session(update, context)
    if choice == BTN_STATUS_BOARD:
        await cmd_console_status(update, context)
        return await show_console_menu(update, context)
    if choice == BTN_GAME_LIB_MENU:
        return await show_game_menu(update, context)
    if choice == BTN_CONSOLE_INSTALL:
        return await show_ginst_menu(update, context)
    if choice == BTN_SSD_MANAGE:
        from bot.handlers.ssd_disc import show_ssd_menu
        return await show_ssd_menu(update, context)
    if choice == BTN_FOOD_NOTE:
        # Show active console list for food note
        try:
            cons = fetch_console_status()
        except Exception:
            cons = []
        active_consoles = [c for c in cons if c.get("id") and c.get("status", "").lower() in ("in use", "active")]
        if not active_consoles:
            await update.message.reply_text("❌ Active session ရှိသော Console မရှိပါ။")
            return await show_console_menu(update, context)
        msg = "🍔 Food Order ထည့်ရန် Console ရွေးပါ:"
        kb = [[c["id"]] for c in active_consoles]
        kb.append([BTN_BACK])
        context.user_data["_food_note_pick"] = True
        await update.message.reply_text(
            msg,
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
        )
        return CONSOLE_MENU
    # Check if in food note console picker mode
    if context.user_data.pop("_food_note_pick", False):
        from bot.handlers.sales import cmd_session_food_order
        from bot import _psvibe_get_async
        # Find linked booking_id for this console
        _bk_id = ""
        try:
            _bks = await _psvibe_get_async("bookings") or []
            if not isinstance(_bks, list):
                _bks = _bks.get("bookings", []) if isinstance(_bks, dict) else []
            for _b in _bks:
                if (_b.get("status") in ("arrived", "in_use", "Active")
                        and (_b.get("consoleId") or _b.get("consoleType") or "").strip() == choice):
                    _bk_id = str(_b.get("id", ""))
                    break
        except Exception as e:
            logger.error("food_note booking lookup: %s", e)
        target = {"id": choice, "member": "", "staff": "", "booking_id": _bk_id}
        logger.warning("food_note_booking: choice=%s _bk_id=%s", choice, _bk_id)
        return await cmd_session_food_order(update, context, target)
    return await show_console_menu(update, context)

async def prompt_end_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of active sessions for the user to pick and end."""
    try:
        consoles = fetch_console_status()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await show_console_menu(update, context)

    active = [c for c in consoles if c["status"] == "Active"]
    if not active:
        await update.message.reply_text(
            "ℹ️ လက်ရှိ Active session မရှိပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK]], resize_keyboard=True),
        )
        return CONSOLE_MENU

    lines = ["⏹️ <b>Session ဆုံးမည် — Console ရွေးပါ</b>\n━━━━━━━━━━━━━━━━━━"]
    kb    = []
    for c in active:
        _, dur_fmt = calc_duration(c["start"]) if c.get("start") else (0, "?")
        mbr  = c.get("member") or "Guest"
        ctype = f" ({c['type']})" if c.get("type") else ""
        lines.append(f"🔴 <b>{c['id']}</b>{ctype}  |  👤 {mbr}  |  ⏱ {dur_fmt}")
        kb.append([c["id"] + (f" ({c['type']})" if c.get("type") else "")])
    kb.append([BTN_BACK])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return END_SESSION_SELECT

async def step_end_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User picked a console to end — find its booking and end it."""
    _t0 = time.monotonic()
    text = update.message.text.strip()
    if text in (BTN_BACK, BTN_BACK_MAIN):
        return await show_console_menu(update, context)
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)

    cid = text.split("(")[0].strip()
    try:
        consoles = fetch_console_status()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await show_console_menu(update, context)

    target = next((c for c in consoles if c["id"] == cid and c["status"] == "Active"), None)
    if not target:
        await update.message.reply_text(
            f"⚠️ <b>{cid}</b> မှာ Active session မတွေ့ပါ\nStatus စစ်ကြည့်ပါ",
            parse_mode="HTML",
        )
        return await prompt_end_session(update, context)

    bk_id   = target.get("booking_id", "")
    start_t = target.get("start", "")
    mbr     = target.get("member") or "Guest"
    session_staff = target.get("staff", "")
    total_mins, dur_fmt = calc_duration(start_t) if start_t else (0, "?")
    # 🐛 Fix: Check _SESSION_TOTAL_MINS for extended minutes.
    # calc_duration only returns elapsed wall-clock time from start_t.
    # If staff extended the session via the extend button, _SESSION_TOTAL_MINS
    # has the accumulated planned total. Use the max of both values.
    _ext_chat_id = update.effective_chat.id
    _ext_key = _remind_key(cid, _ext_chat_id)
    _planned_total = _SESSION_TOTAL_MINS.get(_ext_key, 0)
    if _planned_total > total_mins:
        total_mins = _planned_total
        # Recompute display format with new total
        hrs  = total_mins // 60
        mins_rem = total_mins % 60
        dur_fmt = f"{hrs}h {mins_rem}m" if hrs > 0 else f"{mins_rem}m"

    ok = await end_booking_async(bk_id) if bk_id else True
    logger.warning("step_t end_booking: %dms", (time.monotonic() - _t0) * 1000)

    # ── Feedback: send star rating to linked booking customer ──
    _send_feedback_async = None
    try:
        _booking_detail = await _psvibe_get_async(f"bookings/{bk_id}") if bk_id else None
        _cust_chat_id = (_booking_detail or {}).get("telegram_chat_id") or (_booking_detail or {}).get("telegramChatId", "")
        if _cust_chat_id:
            _cust_chat_id = str(_cust_chat_id).strip()
            if _cust_chat_id:
                _send_feedback_async = asyncio.create_task(_send_feedback_to_customer(_cust_chat_id, str(bk_id)))
    except Exception as _fe:
        logger.warning("Feedback trigger prep failed (non-critical): %s", _fe)
    if not ok:
        if bk_id:
            await update.message.reply_text(f"❌ Booking ID {bk_id} ရှာမတွေ့ပါ")
        else:
            await update.message.reply_text("❌ Booking ID မတွေ့ပါ — Console မှာ active session မရှိတော့ပါ")
        return await show_console_menu(update, context)

    end_t = now_mmt().strftime("%H:%M")

    # ── SSD Transfer Warning ────────────────────────────────────────────────
    ssd_warn = ""
    ssd_transfers = [
        r for r in fetch_console_games()
        if r["console_id"].upper() == cid.upper()
        and "SSD Transfer" in r.get("install_type", "")
    ]
    if ssd_transfers:
        game_names = [r["game_title"] for r in ssd_transfers]
        ssd_warn = (
            f"\n\n⚠️ <b>SSD ပြန်ရွေ့ပါ!</b>\n"
            f"ဤ console မှ SSD ထဲ ပြန်ရွေ့ရမည့် ဂိမ်းများ:\n"
            + "\n".join(f"  📀 {g}" for g in game_names)
        )

    # Show current session game if any
    session_games = [
        r["game_title"] for r in fetch_console_games()
        if r["console_id"].upper() == cid.upper() and r["install_type"] == "Session"
    ]
    game_line = f"\n🎮 Game     : <b>{session_games[0]}</b>" if session_games else ""

    await update.message.reply_text(
        f"✅ <b>Session ဆုံးပြီ!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕹️ Console  : <b>{cid}</b>\n"
        f"👤 Member   : <b>{mbr}</b>"
        f"{game_line}\n"
        f"🕐 Start    : <b>{start_t}</b>\n"
        f"🕑 End      : <b>{end_t}</b>\n"
        f"⏱ Duration : <b>{dur_fmt}</b> ({total_mins} mins)\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 Sales Voucher ဖွင့်နေသည်..."
        f"{ssd_warn}",
        parse_mode="HTML",
    )
    logger.warning("step_t after_voucher_msg: %dms", (time.monotonic() - _t0) * 1000)
    # Clean up Session game entry for this console
    _delete_session_game(cid)
    logger.warning("step_t after_delete_game: %dms", (time.monotonic() - _t0) * 1000)
    # Use booking_id from console status (already found). After end_booking_async above,
    # the booking status is 'Done' so a second member-based lookup would fail to find it.
    # Only fall back to member lookup if bk_id was empty.
    # Cast to str: API may return int, but food_cart URL building expects string.
    _linked_bk_id = str(bk_id) if bk_id else ""
    if not _linked_bk_id:
        try:
            _bks = await _psvibe_get_async("bookings?status=Active") or []
            if not isinstance(_bks, list):
                _bks = _bks.get("bookings", []) if isinstance(_bks, dict) else []
            for _b in _bks:
                if (_b.get("consoleId") or _b.get("consoleType") or "").strip() == cid:
                    _linked_bk_id = str(_b.get("id", ""))
                    break
        except Exception:
            pass
    logger.warning("step_t linked_bk_id=%s food_cart_lookup: %dms", _linked_bk_id, (time.monotonic() - _t0) * 1000)
    # ── CashBack Coupon: Auto-generate via MySQL API ──
    try:
        from bot.api_client import api_post
        member_id_for_coupon = mbr if mbr not in ("Guest", "0 (Guest)", "") else ""
        if member_id_for_coupon and total_mins > 0:
            gen_result = await asyncio.to_thread(
                api_post, "coupons/generate",
                {"member_id": member_id_for_coupon, "session_minutes": total_mins}
            )
            if gen_result and isinstance(gen_result, dict):
                cd = gen_result.get("coupon") or (gen_result.get("data") or {}).get("coupon")
                if cd and cd.get("code"):
                    context.user_data["_cashback_coupon"] = cd["code"]
                    context.user_data["_cashback_coupon_mins"] = cd.get("minutes", total_mins)
                    logger.warning("COUPON GEN OK: code=%s mins=%s member=%s", cd["code"], cd.get("minutes", total_mins), member_id_for_coupon)
                else:
                    logger.warning("COUPON GEN: no coupon in response: gen_result=%s", gen_result)
    except Exception as cb_e:
        logger.warning("Cashback coupon generation failed (non-critical): %s", cb_e)

    from bot.handlers.sales import launch_session_sale
    _t5 = time.monotonic()
    _pre_ms = (_t5 - _t0) * 1000
    _ls_result = await launch_session_sale(update, context, cid, mbr, total_mins, session_staff,
                                           booking_id=_linked_bk_id)
    _total_ms = (time.monotonic() - _t0) * 1000
    logger.warning("CONSOLE_TIME step_end_session: pre_sale=%dms sale=%dms total=%dms", _pre_ms, _total_ms - _pre_ms, _total_ms)
    return _ls_result

# Duplicate import removed - already imported at top
