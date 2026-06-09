
"""PS VIBE Bot — Handler module.
"""
from bot import (
    BTN_BACK, BTN_BACK_MAIN, BTN_CANCEL, BTN_CHANGE_GAME,
    BTN_CONSOLE_INSTALL, BTN_END_SESSION, BTN_GAME_LIB_MENU, BTN_START_SESSION,
    BTN_SSD_MANAGE, BTN_STATUS_BOARD, CONSOLE_MENU, END_SESSION_SELECT,
    _delete_session_game,
    _replit_get, _replit_get_async, add_console_game, _replit_post_async,
    calc_duration, cmd_cancel, end_booking, end_booking_async, fetch_console_games,
    fetch_console_status, get_games_on_console, get_games_on_console_async, now_mmt,
    show_console_menu, show_game_menu, show_main_menu,
    prompt_book_console,
)

from bot.api_client import api_fetch_console_status_async
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import asyncio, logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta



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
        if "T" in _st:
            try:
                from datetime import datetime as _dt
                _st = _dt.fromisoformat(_st).strftime("%H:%M")
            except Exception:
                pass
        _normalized.append({
            "id": _c.get("console_id") or _c.get("id", "?"),
            "type": _c.get("console_type") or _c.get("type", ""),
            "liveStatus": _c.get("status") or _c.get("liveStatus", "Free"),
            "member": _c.get("current_member") or _c.get("member"),
            "startTime": _st,
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

    now_str = now_mmt().strftime("%H:%M")
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
            # Calculate end time
            dur = c.get("reservedDuration") or c.get("durationMins") or 60
            try:
                sh, sm = map(int, rsv_at.split(":"))
                total_m = sh * 60 + sm + int(dur)
                end_str = f"{total_m // 60:02d}:{total_m % 60:02d}"
                time_range = f"{rsv_at}–{end_str}"
            except Exception as e:
                logger.error("cmd_console_status: %s", e, exc_info=True)
                time_range = rsv_at
            detail = f"Reserved {time_range} — {rsv_who}"
        else:
            icon   = "🔴"
            mbr    = c.get("member") or "Guest"
            since  = f" since {c['startTime']}" if c.get("startTime") else ""
            detail = f"Active — {mbr}{since}"

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
        [BTN_STATUS_BOARD,   BTN_GAME_LIB_MENU],
        [BTN_CONSOLE_INSTALL, BTN_SSD_MANAGE],
        [BTN_BACK_MAIN],
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

    ok = await end_booking_async(bk_id) if bk_id else False
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
    # Clean up Session game entry for this console
    _delete_session_game(cid)
    # Try to find linked booking_id from bookings store
    _linked_bk_id = ""
    try:
        _bks = await _replit_get_async(f"bookings?memberId={mbr}") or []
        if not isinstance(_bks, list):
            _bks = _bks.get("bookings", []) if isinstance(_bks, dict) else []
        for _b in _bks:
            if (_b.get("status") in ("confirmed", "arrived")
                    and (_b.get("consoleId") or "").strip() == cid):
                _linked_bk_id = str(_b.get("id", ""))
                break
    except Exception as e:
        logger.error("step_end_session: %s", e, exc_info=True)
        pass
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
    return await launch_session_sale(update, context, cid, mbr, total_mins, session_staff,
                                     booking_id=_linked_bk_id)

# Duplicate import removed - already imported at top
