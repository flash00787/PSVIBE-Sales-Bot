from bot import (
    BOOK_CONSOLE, BOOK_DUP_WARN, BOOK_GAME, BOOK_LINK, BOOK_MEMBER,
    BOOK_MINS, BTN_BACK, BTN_BACK_MAIN, BTN_BOOK_PROCEED, BTN_CANCEL,
    BTN_NO_RESELECT, BTN_SBK_CONFIRMED, BTN_SBK_CONFIRM_BOOK,
    BTN_SBK_CUSTOM, BTN_SBK_NEW, BTN_SBK_SKIP_GAME, BTN_SBK_SKIP_PHONE,
    BTN_SBK_WAITLIST, BTN_SKIP_GAME, BTN_SKIP_TIMER, BTN_SSD_TRANSFER,
    CONSOLE_MENU, MAIN_MENU, N8N_BOOKING_WEBHOOK, SBK_CONFIRM,
    SBK_CONSOLE, SBK_CUST_NAME, SBK_DATE, SBK_DUR, SBK_GAME, SBK_TIME,
    SSD_XFER_SSD, STAFF_NOTIFY_CHAT, VALID_CONSOLES,
    _replit_get_async, _replit_patch_async,
    add_console_game, add_console_game_async, _delete_session_game,     calc_duration,
    check_disc_session_conflict, cmd_cancel, create_booking, create_booking_async,
    fetch_console_games, fetch_console_games_async, fetch_console_status, fetch_games, fetch_games_async,
    fetch_members, fetch_staff, get_consoles_with_game, get_consoles_with_game_async,
    get_games_on_console, get_games_on_console_async, now_mmt, show_admin_menu, show_console_menu,
    show_main_menu, today_str,
    fetch_members_async,
)

"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta
import asyncio
from bot.handlers.booking_flow import _cancel_remind, _remind_loop, _REMIND_TASKS, _remind_key
from bot.handlers.notify import _notify_customer


async def _sbk_console_kb() -> list:
    """Return keyboard of all consoles with live+reserved status via API."""
    try:
        data = {"consoles": [{"id": c["id"], "type": c.get("type",""), "liveStatus": c.get("status","Free")} for c in fetch_console_status()]}
        consoles = data.get("consoles", []) if isinstance(data, dict) else []
    except Exception as e:
        logging.warning("Failed to fetch consoles via API for staff booking keyboard: %s", e)
        consoles = []
    if not consoles:
        # fallback to local fetch
        try:
            consoles = [{"id": c["id"], "type": c.get("type",""), "liveStatus": c.get("status","Free")}
                        for c in fetch_console_status()]
        except Exception as e:
            logging.warning("Failed to fetch console status (staff booking fallback): %s", e)
            return [[c] for c in sorted(VALID_CONSOLES)] + [[BTN_BACK, BTN_CANCEL]]
    else:
        # Map API keys to expected format (console_id→id, status→liveStatus)
        mapped = []
        for c in consoles:
            if "id" not in c and "console_id" in c:
                c["id"] = c["console_id"]
            if "liveStatus" not in c and "status" in c:
                c["liveStatus"] = c["status"]
            if "type" not in c:
                c["type"] = c.get("console_type", "")
            mapped.append(c)
        consoles = mapped
    rows = []
    row  = []
    for c in sorted(consoles, key=lambda x: x["id"]):
        live = c.get("liveStatus", "Free")
        if live == "Free":
            icon = "✅"
        elif live == "Reserved":
            icon = "🟡"
        else:
            icon = "🔴"
        label = f"{c['id']} ({c.get('type','?')}) {icon}"
        row.append(label)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([BTN_BACK, BTN_CANCEL])
    return rows

def _sbk_parse_console_label(text: str) -> tuple[str, str]:
    """Extract (console_id, console_type) from keyboard label like 'C - 01 (PS5 Pro) ✅'."""
    # Format: "C - 01 (PS5 Pro) ✅" or "C - 01 (PS5) 🔴"
    import re
    m = re.match(r"^(C\s*-\s*\d+)\s*\(([^)]+)\)", text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    cid = text.split("(")[0].strip().split("✅")[0].strip().split("🔴")[0].strip().split("🟡")[0].strip()
    return cid, "PS Console"

async def cmd_staff_book_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Booking hub: show pending bookings + navigation to confirmed bookings."""
    context.user_data["sbk_from_hub"] = True

    # Fetch counts for both statuses in parallel (sync thread)
    pending_bks   = await _replit_get_async("bookings?status=pending") or []
    confirmed_bks = await _replit_get_async("bookings?status=confirmed") or []

    n_pending   = len(pending_bks)   if isinstance(pending_bks,   list) else 0
    n_confirmed = len(confirmed_bks) if isinstance(confirmed_bks, list) else 0

    await update.message.reply_text(
        f"📅 *Customer Booking*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 Pending: *{n_pending}* ခု  |  ✅ Confirmed: *{n_confirmed}* ခု",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [[BTN_SBK_NEW], [BTN_SBK_CONFIRMED], [BTN_SBK_WAITLIST], [BTN_BACK_MAIN]],
            resize_keyboard=True,
        ),
    )

    if not pending_bks:
        await update.message.reply_text(
            "📋 *Pending Bookings မရှိပါ*",
            parse_mode="Markdown",
        )
        return MAIN_MENU

    await update.message.reply_text(
        f"📋 *Pending Bookings — {n_pending} ခု*\n"
        f"━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown",
    )
    for b in pending_bks:
        card = (
            f"🎫 *Booking #{b['id']}*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 {b['customerName']}  📞 {b.get('phone') or '—'}\n"
            f"📅 {b['date']}  🕐 {b['timeSlot']}\n"
            f"🎮 {b['consoleType']}  ⏱️ {b['durationMins']} mins\n"
            f"🕹️ {b.get('gameName') or '-'}\n"
            f"🏷️ Console ID: {b.get('console_id') or b.get('consoleId') or '—'}"
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data=f"bkm:approve:{b['id']}"),
            InlineKeyboardButton("❌ Reject",  callback_data=f"bkm:reject:{b['id']}"),
        ]])
        await update.message.reply_text(card, parse_mode="Markdown", reply_markup=kb)
    return MAIN_MENU

async def cmd_confirmed_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show upcoming confirmed bookings with Cancel button each."""
    await update.message.reply_text("⏳ Confirmed bookings စစ်နေသည်...")
    bookings = await _replit_get_async("bookings?status=confirmed") or []
    if not isinstance(bookings, list):
        bookings = []

    now_str  = now_mmt().strftime("%H:%M")
    today_s  = now_mmt().strftime("%-m/%-d/%Y")

    # Sort: today first (upcoming slots), then future dates
    def sort_key(b):
        return (b.get("date", ""), b.get("timeSlot", ""))
    bookings = sorted(bookings, key=sort_key)

    if not bookings:
        await update.message.reply_text(
            "✅ *Confirmed Bookings မရှိပါ*",
            parse_mode="Markdown",
        )
        return MAIN_MENU

    await update.message.reply_text(
        f"✅ *Confirmed Bookings — {len(bookings)} ခု*\n"
        f"━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown",
    )

    for b in bookings[:15]:
        console_hint = b.get("console_id") or b.get("consoleType", "?")
        is_today = b.get("date", "") == today_s
        today_tag = "  🔵 Today" if is_today else ""
        card = (
            f"✅ *Booking #{b['id']}*{today_tag}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 {b['customerName']}  📞 {b.get('phone') or '—'}\n"
            f"📅 {b['date']}  🕐 {b['timeSlot']}\n"
            f"🎮 {console_hint}  ⏱️ {b.get('durationMins', '?')} mins\n"
            f"🕹️ {b.get('gameName') or '-'}\n"
            f"🏷️ Console ID: {b.get('console_id') or b.get('consoleId') or '—'}"
        )
        kb = InlineKeyboardMarkup([[
                        InlineKeyboardButton("✅ Check In", callback_data=f"bkm:checkin:{b['id']}"),
InlineKeyboardButton("🚫 Cancel", callback_data=f"bkc:{b['id']}"),
        ]])
        await update.message.reply_text(card, parse_mode="Markdown", reply_markup=kb)

    return MAIN_MENU

async def cmd_staff_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: ask date first, then time, then check availability."""
    from_hub = context.user_data.get("sbk_from_hub", False)
    # Clear everything EXCEPT the hub flag
    sbk_from_hub = context.user_data.pop("sbk_from_hub", False)
    context.user_data.clear()
    if sbk_from_hub or from_hub:
        context.user_data["sbk_from_hub"] = True

    today    = now_mmt().date()
    tomorrow = today + timedelta(days=1)
    d2       = today + timedelta(days=2)
    def dfmt(d): return d.strftime("%-m/%-d/%Y")
    kb = [
        [dfmt(today) + " (ယနေ့)", dfmt(tomorrow) + " (မနက်ဖြန်)"],
        [dfmt(d2)],
        [BTN_SBK_CUSTOM],
        [BTN_BACK, BTN_CANCEL],
    ]
    await update.message.reply_text(
        "📅 *Customer Advance Booking*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ပထမဦးစွာ ရက်စွဲရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SBK_TIME

async def step_sbk_console(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle console selection."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text in (BTN_BACK, BTN_BACK_MAIN):
        if context.user_data.get("sbk_from_hub"):
            return await cmd_staff_book_hub(update, context)
        return await show_admin_menu(update, context)

    cid, ctype = _sbk_parse_console_label(text)
    # validate against known consoles
    try:
        all_c = fetch_console_status()
        valid = {c["id"] for c in all_c}
    except Exception as e:
        logging.warning("Failed to validate console IDs (staff booking): %s", e)
        valid = VALID_CONSOLES
    if cid not in valid:
        await update.message.reply_text("⚠️ Keyboard မှ Console ရွေးပေးပါ")
        return await cmd_staff_booking(update, context)

    context.user_data["sbk_console_id"]   = cid
    context.user_data["sbk_console_type"] = ctype

    # Offer member list for quick selection
    try:
        members = await fetch_members_async()
    except Exception as e:
        logging.warning("Failed to fetch members for staff booking: %s", e)
        members = []
    kb = [["👤 Guest (Walk-in)"]] + [[m] for m in members[:20]] + [[BTN_BACK, BTN_CANCEL]]
    await update.message.reply_text(
        f"🕹️ Console: <b>{cid}</b>  ({ctype})\n\n"
        "👤 Customer name ထည့်ပါ\n"
        "( Member list မှ ရွေး သို့ Manual ရိုက် )",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SBK_CUST_NAME

async def step_sbk_cust_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle customer name / member selection."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await cmd_staff_booking(update, context)

    name = "Guest" if text == "👤 Guest (Walk-in)" else text
    context.user_data["sbk_cust_name"] = name

    # Ask phone
    kb = [[BTN_SBK_SKIP_PHONE], [BTN_BACK, BTN_CANCEL]]
    await update.message.reply_text(
        f"👤 Customer: <b>{name}</b>\n\n"
        "📞 Phone number ထည့်ပါ (optional — Skip နှိပ်နိုင်)",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SBK_DATE

async def step_sbk_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone → then ask booking date."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        # Go back to customer name step (preserve context)
        name = context.user_data.get("sbk_cust_name", "")
        kb = [[BTN_SBK_SKIP_PHONE], [BTN_BACK, BTN_CANCEL]]
        await update.message.reply_text(
            "👤 Customer: <b>" + name + "</b>\n\n📞 Phone number ထည့်ပါ (optional — Skip နှိပ်နိုင်)",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return SBK_CUST_NAME

    phone = "—" if text == BTN_SBK_SKIP_PHONE else text
    context.user_data["sbk_phone"] = phone

    # Ask date
    today    = now_mmt().date()
    tomorrow = today + timedelta(days=1)
    d2       = today + timedelta(days=2)
    def dfmt(d): return d.strftime("%-m/%-d/%Y")
    kb = [
        [dfmt(today) + " (ယနေ့)", dfmt(tomorrow) + " (မနက်ဖြန်)"],
        [dfmt(d2)],
        [BTN_SBK_CUSTOM],
        [BTN_BACK, BTN_CANCEL],
    ]
    await update.message.reply_text(
        "📅 Booking Date ရွေးပါ:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SBK_TIME

async def step_sbk_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date → then ask time slot."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        # re-ask phone
        name = context.user_data.get("sbk_cust_name", "")
        kb = [[BTN_SBK_SKIP_PHONE], [BTN_BACK, BTN_CANCEL]]
        await update.message.reply_text(
            f"👤 Customer: <b>{name}</b>\n\n📞 Phone number ထည့်ပါ:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return SBK_DATE

    if text == BTN_SBK_CUSTOM:
        await update.message.reply_text(
            "📅 ရက် ရိုက်ထည့်ပါ (format: M/D/YYYY)\nဥပမာ: 5/10/2026",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK, BTN_CANCEL]], resize_keyboard=True),
        )
        return SBK_TIME

    # Parse date from label like "5/4/2026 (ယနေ့)"
    import re as _re
    m = _re.match(r"(\d{1,2}/\d{1,2}/\d{4})", text)
    if m:
        date_str = m.group(1)
    else:
        # try direct parse e.g. "5/4/2026"
        parts = text.split("/")
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            date_str = text
        else:
            await update.message.reply_text("⚠️ ရက် format မမှန်ပါ (M/D/YYYY)")
            return SBK_TIME

    context.user_data["sbk_date"] = date_str

    # Build time slot keyboard
    slots = [
        ["10:00", "11:00", "12:00"],
        ["13:00", "14:00", "15:00"],
        ["16:00", "17:00", "18:00"],
        ["19:00", "20:00", "21:00"],
        ["22:00"],
    ]
    kb = slots + [[BTN_BACK, BTN_CANCEL]]
    await update.message.reply_text(
        f"📅 {date_str}\n\n⏰ Time Slot ရွေးပါ (HH:MM):",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SBK_DUR

async def step_sbk_dur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time slot -> check avail and show console selection."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        today    = now_mmt().date()
        tomorrow = today + timedelta(days=1)
        d2       = today + timedelta(days=2)
        def dfmt(d): return d.strftime("%-m/%-d/%Y")
        kb = [
            [dfmt(today) + " (ယနော)", dfmt(tomorrow) + " (မနက်ဖြန်)"],
            [dfmt(d2)],
            [BTN_SBK_CUSTOM],
            [BTN_BACK, BTN_CANCEL],
        ]
        await update.message.reply_text(
            "📅 Booking Date ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return SBK_TIME

    import re as _re2
    if not _re2.match(r"^\d{1,2}:\d{2}$", text):
        await update.message.reply_text("⚠️ Time format: HH:MM  (ဥပမာ: 14:30)")
        return SBK_DUR

    context.user_data["sbk_time"] = text

    rows = await _sbk_console_kb()
    if rows and len(rows) > 1:
        await update.message.reply_text(
            "✅ Available Consoles:\n\nConsole ID ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True),
        )
    else:
        await update.message.reply_text(
            "⚠️ Free console မရှိပါ\nေန့ရက်အသစ်ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK, BTN_CANCEL]], resize_keyboard=True),
        )
    return SBK_CONSOLE
async def step_sbk_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle duration → ask game."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        # re-ask time
        slots = [
            ["10:00", "11:00", "12:00"],
            ["13:00", "14:00", "15:00"],
            ["16:00", "17:00", "18:00"],
            ["19:00", "20:00", "21:00"],
            ["22:00"],
        ]
        await update.message.reply_text(
            "⏰ Time Slot ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(slots + [[BTN_BACK, BTN_CANCEL]], resize_keyboard=True),
        )
        return SBK_DUR

    try:
        dur = int(text)
    except ValueError:
        await update.message.reply_text("⚠️ ဂဏန်းသာ ထည့်ပါ သို့ keyboard မှ ရွေးပါ")
        return SBK_GAME
    context.user_data["sbk_dur"] = dur

    # Build game keyboard
    try:
        games = await fetch_games_async()
        game_names = [g["title"] for g in games if g.get("title")][:30]
    except Exception as e:
        logging.warning("Failed to fetch games for staff booking: %s", e)
        game_names = []

    kb = [[BTN_SBK_SKIP_GAME]]
    row = []
    for g in game_names:
        row.append(g)
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([BTN_BACK, BTN_CANCEL])

    await update.message.reply_text(
        f"⏱️ Duration: <b>{dur} mins</b>\n\n"
        "🎮 Game ရွေးပါ (optional):",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SBK_CONFIRM


async def _sbk_advance_reminder(bot, booking_id: int, cid: str, ctype: str, name: str, phone: str,
                                 date_str: str, time_str: str, dur: int, game: str, staff: str):
    """Send 10-min advance reminder to admin group for a confirmed booking."""
    try:
        # Parse date and time - handle M/D/YYYY format
        import re as _re
        m = _re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", date_str)
        if not m:
            logger.warning("_sbk_advance_reminder: bad date_format=%s", date_str)
            return
        mo, da, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        parts = time_str.split(":")
        if len(parts) != 2:
            logger.warning("_sbk_advance_reminder: bad time_format=%s", time_str)
            return
        hr, mi = int(parts[0]), int(parts[1])
        
        booking_dt = datetime(yr, mo, da, hr, mi, 0, tzinfo=timezone(timedelta(hours=6, minutes=30)))
        remind_dt = booking_dt - timedelta(minutes=10)
        now_utc = datetime.now(timezone.utc)
        
        # If remind time already passed but booking is still in the future, skip
        if remind_dt <= now_utc:
            if booking_dt > now_utc:
                # Less than 10 min away - fire immediately
                pass
            else:
                return  # Booking already started
        
        seconds_until_remind = max(1, int((remind_dt - now_utc).total_seconds()))
        await asyncio.sleep(seconds_until_remind)
        
        notify_text = (
            f"\u23f0 <b>Booking #{booking_id} Reminder!</b>\n"
            f"\u23f1\ufe0f <b>10 \u1019\u102d\u1014\u1037\u1001\u103a\u1021\u101c\u102d\u102f</b> \u1000\u103c\u102e\u1019\u1000\u103a\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"\u2b07 Customer: <b>{name}</b>  \u2139 {phone}\n"
            f"\u267f {date_str}  \u23f0 {time_str}\n"
            f"\u267f Duration: <b>{dur} mins</b>  \u2694\ufe0f {game or '---'}\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"Staff: {staff}"
        )
        if STAFF_NOTIFY_CHAT:
            await bot.send_message(
                chat_id=int(STAFF_NOTIFY_CHAT),
                text=notify_text,
                parse_mode="HTML",
            )
            logger.info("_sbk_advance_reminder: Booking #%s reminder sent to admin", booking_id)
    except Exception as e:
        logger.error("_sbk_advance_reminder: %s", e, exc_info=True)

async def step_sbk_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """SBK_CONFIRM state — phase 1: receive game name and show summary.
       Phase 2: receive BTN_SBK_CONFIRM_BOOK and create the booking.
    """
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)

    # ── Phase 2: create booking (user pressed confirm) ─────────────────────
    if text == BTN_SBK_CONFIRM_BOOK:
        cid      = context.user_data.get("sbk_console_id", "")
        ctype    = context.user_data.get("sbk_console_type", "")
        name     = context.user_data.get("sbk_cust_name", "Guest")
        phone    = context.user_data.get("sbk_phone", "—")
        date     = context.user_data.get("sbk_date", "")
        slot     = context.user_data.get("sbk_time", "")
        dur      = context.user_data.get("sbk_dur", 60)
        game     = context.user_data.get("sbk_game", "")
        staff    = update.effective_user.full_name or "Staff"

        await update.message.reply_text("⏳ Booking ဖန်တီးနေသည်...", reply_markup=ReplyKeyboardRemove())

        payload = {
            "customerName": name,
            "phone":        phone,
            "date":         date,
            "timeSlot":     slot,
            "consoleType":  ctype,
            "console_id":    cid,
            "durationMins": int(dur),
            "gameName":     game or None,
            "status":       "confirmed",
            "source":       "staff",
            "staffNote":    f"Console: {cid} | Booked by {staff}",
        }

        result = await _replit_post_async("bookings", payload)
        if not result or "id" not in result:
            await update.message.reply_text(
                "❌ Booking create မအောင်မြင်ပါ\nAPI စစ်ပြီး ထပ်ကြိုးစားပါ",
            )
            return await show_main_menu(update, context)

        bk_id = result["id"]

        # Notify staff group
        if STAFF_NOTIFY_CHAT:
            notif = (
                f"📅 <b>New Staff Booking #{bk_id}</b>\n"
                f"🕹️ {cid} ({ctype})\n"
                f"👤 {name}  📞 {phone}\n"
                f"📅 {date}  ⏰ {slot}\n"
                f"⏱️ {dur} mins  🎮 {game or '—'}\n"
                f"Created by {staff}"
            )
            await asyncio.to_thread(_notify_customer, STAFF_NOTIFY_CHAT, notif)

        # Fire n8n reminder webhook (non-blocking)
        asyncio.create_task(_post_n8n_booking_reminder(
            bk_id=bk_id, customer_name=name, phone=phone,
            console_id=cid, console_type=ctype,
            date_str=date, time_slot=slot, duration_mins=int(dur),
            tg_chat="",
        ))

        # Schedule 10-min advance reminder (non-blocking)
        asyncio.create_task(_sbk_advance_reminder(
            context.bot, bk_id=bk_id, cid=cid, ctype=ctype, name=name, phone=phone,
            date_str=date, time_str=slot, dur=int(dur), game=game, staff=staff,
        ))

        await update.message.reply_text(
            f"✅ <b>Booking #{bk_id} Created!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🕹️ Console  : <b>{cid}</b>  ({ctype})\n"
            f"👤 Customer : <b>{name}</b>  📞 {phone}\n"
            f"📅 {date}  ⏰ {slot}\n"
            f"⏱️ {dur} mins  🎮 {game or '—'}\n"
            f"Status: <b>Confirmed ✅</b>\n"
            f"{'📲 Reminder scheduled via n8n' if N8N_BOOKING_WEBHOOK else ''}",
            parse_mode="HTML",
        )
        context.user_data.clear()
        return await show_main_menu(update, context)

    # ── BTN_BACK: re-show game selection ──────────────────────────────────
    if text == BTN_BACK:
        dur = context.user_data.get("sbk_dur", 60)
        context.user_data.pop("sbk_game", None)
        try:
            games = await fetch_games_async()
            game_names = [g["title"] for g in games if g.get("title")][:30]
        except Exception as e:
            logger.error("step_sbk_confirm: %s", e, exc_info=True)
            game_names = []
        kb = [[BTN_SBK_SKIP_GAME]]
        row = []
        for g in game_names:
            row.append(g)
            if len(row) == 2:
                kb.append(row)
                row = []
        if row:
            kb.append(row)
        kb.append([BTN_BACK, BTN_CANCEL])
        await update.message.reply_text(
            f"⏱️ Duration: <b>{dur} mins</b>\n\n🎮 Game ရွေးပါ:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return SBK_CONFIRM

    # ── Phase 1: receive game name, show summary ───────────────────────────
    game = "" if text == BTN_SBK_SKIP_GAME else text
    context.user_data["sbk_game"] = game

    cid   = context.user_data.get("sbk_console_id", "")
    ctype = context.user_data.get("sbk_console_type", "")
    name  = context.user_data.get("sbk_cust_name", "")
    phone = context.user_data.get("sbk_phone", "—")
    date  = context.user_data.get("sbk_date", "")
    slot  = context.user_data.get("sbk_time", "")
    dur   = context.user_data.get("sbk_dur", 0)

    # ── SSD transfer check ─────────────────────────────────────────────────
    ssd_warning = ""
    context.user_data["sbk_needs_ssd"] = False
    if game:
        installed = await get_games_on_console_async(cid)
        installed_lower = [g.lower() for g in installed]
        if game.lower() not in installed_lower:
            # check if game exists on any console (installed anywhere)
            consoles_with_game = await get_consoles_with_game_async(game)
            ssd_consoles = [
                r["console_id"] for r in await fetch_console_games_async()
                if r["game_title"].lower() == game.lower()
                and r["install_type"] == "Portable SSD"
            ]
            if consoles_with_game:
                context.user_data["sbk_needs_ssd"] = True
                ssd_warning = (
                    f"\n⚠️ <b>SSD Transfer လိုသည်!</b>\n"
                    f"「{game}」 ကို {cid} မှာ Install မရှိပါ\n"
                    f"{'🔌 SSD (' + ', '.join(ssd_consoles) + ') မှ transfer လိုမည်' if ssd_consoles else '📋 Install မှတ်တမ်း စစ်ဆေးပါ'}\n"
                )
            else:
                ssd_warning = f"\n📝 <i>「{game}」 Install မှတ်တမ်း မရှိသေးပါ</i>\n"

    # Disc session conflict check for staff booking
    disc_warn_staff = check_disc_session_conflict(game, slot) if game and slot else ""

    summary = (
        f"📋 <b>Booking Summary — စစ်ဆေးပါ</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕹️ Console  : <b>{cid}</b>  ({ctype})\n"
        f"👤 Customer : <b>{name}</b>\n"
        f"📞 Phone    : {phone}\n"
        f"📅 Date     : <b>{date}</b>\n"
        f"⏰ Time     : <b>{slot}</b>\n"
        f"⏱️ Duration : <b>{dur} mins</b>\n"
        f"🎮 Game     : {game or '—'}"
        f"{ssd_warning}\n"
        + (f"\n{disc_warn_staff}\n" if disc_warn_staff else "")
        + f"━━━━━━━━━━━━━━━━━━\n"
        f"ဤ booking ကို create မည်လား?"
    )
    kb = [[BTN_SBK_CONFIRM_BOOK], [BTN_BACK, BTN_CANCEL]]
    await update.message.reply_text(
        summary, parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SBK_CONFIRM

async def prompt_book_console(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              origin: str = "console"):
    """Show available consoles for booking. origin='console'|'admin'."""
    logging.warning("DBG: prompt_book_console start, origin=%s", origin)
    context.user_data["bk_origin"] = origin
    try:
        consoles = fetch_console_status()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return CONSOLE_MENU
    free = [c for c in consoles if c["status"] == "Free"]
    if not free:
        await update.message.reply_text(
            "⚠️ လက်ရှိ Free ဖြစ်သော Console မရှိပါ\n"
            "Active session များ ဦးစွာ ဆုံးအောင်လုပ်ပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK]], resize_keyboard=True),
        )
        return CONSOLE_MENU
    # ── Step 0: Check for today's confirmed/arrived bookings ─────────────────
    return await prompt_book_link(update, context, free)

async def prompt_book_link(update: Update, context: ContextTypes.DEFAULT_TYPE, free_consoles=None):
    """Ask staff whether to link this session to a confirmed booking (optional)."""
    try:
        today = today_str()
        bks_raw = await _replit_get_async("bookings") or []
        # Include confirmed + arrived; filter to today only
        # Also apply a 30-min past window so check-in'd bookings are still linkable
        from datetime import datetime as _dt
        _now_mmt = now_mmt()
        _cutoff_str = (_now_mmt.replace(hour=0, minute=0, second=0, microsecond=0))
        def _in_window(b):
            ts = b.get("timeSlot", "")
            if not ts:
                return True  # no time info — include it
            try:
                h, m = map(int, ts.split(":"))
                bk_dt = _now_mmt.replace(hour=h, minute=m, second=0, microsecond=0)
                # Show if booking time is within past 30 min or in the future
                diff_mins = (_now_mmt - bk_dt).total_seconds() / 60
                return diff_mins <= 30
            except Exception as e:
                logger.error("_in_window: %s", e, exc_info=True)
                return True
        pending_bks = [
            b for b in bks_raw if isinstance(b, dict)
            if b.get("status") in ("confirmed", "arrived")
            and b.get("date", "") == today
            and _in_window(b)
        ]
    except Exception as e:
        logger.error("_in_window: %s", e, exc_info=True)
        pending_bks = []

    if not pending_bks:
        return await _show_console_select(update, context, free_consoles)

    kb_rows = []
    for b in pending_bks:
        bk_id   = b.get("id", "?")
        member  = b.get("memberId") or "Guest"
        console = (b.get("console_id") or "?").strip()
        bk_time = b.get("timeSlot") or ""
        game    = b.get("gameName") or ""
        label   = f"#{bk_id} | {console} | {member}"
        if bk_time:
            label += f" | {bk_time}"
        if game:
            label += f" | {game}"
        kb_rows.append([label])
    kb_rows.append(["⏭️ Booking မရှိဘဲ ဆက်သွား"])
    kb_rows.append([BTN_BACK, BTN_CANCEL])

    context.user_data["_bk_link_list"] = pending_bks
    await update.message.reply_text(
        "▶️ <b>New Console Session</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📋 ဒီနေ့ Confirmed Booking ရှိသည် — Session နှင့် ချိတ်ဆက်မည်လား?\n\n"
        "<i>Booking ရွေးလျှင် Member / Console / Game autofill ဖြစ်မည်</i>\n"
        "မရှိဘဲ ဆက်သွားလျှင် ⏭️ နှိပ်ပါ",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return BOOK_LINK

async def _show_console_select(update: Update, context: ContextTypes.DEFAULT_TYPE, free_consoles=None):
    """Show the console selection keyboard."""
    logging.warning("DBG: _show_console_select called, free_consoles=%s", free_consoles)
    if free_consoles is None:
        try:
            consoles = fetch_console_status()
            free_consoles = [c for c in consoles if c["status"] == "Free"]
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            return CONSOLE_MENU
    kb = [[c["id"] + (f" ({c['type']})" if c.get("type") else "")] for c in free_consoles]
    kb += [[BTN_BACK, BTN_CANCEL]]
    await update.message.reply_text(
        "▶️ *New Console Session*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🕹️ Console ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return BOOK_CONSOLE

async def step_book_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle booking-link selection. Autofill or skip."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text in (BTN_BACK, BTN_BACK_MAIN):
        return await show_console_menu(update, context)
    if text == "⏭️ Booking မရှိဘဲ ဆက်သွား":
        context.user_data.pop("_bk_link_list", None)
        return await _show_console_select(update, context)

    pending_bks = context.user_data.pop("_bk_link_list", [])
    selected_bk = None
    for b in pending_bks:
        bk_id = b.get("id", "?")
        if text.startswith(f"#{bk_id} "):
            selected_bk = b
            break

    if not selected_bk:
        await update.message.reply_text("⚠️ Keyboard မှ ရွေးပေးပါ")
        context.user_data["_bk_link_list"] = pending_bks
        return BOOK_LINK

    bk_id   = selected_bk.get("id")
    console = (selected_bk.get("console_id") or "").strip()
    member  = selected_bk.get("memberId") or "Guest"
    game    = selected_bk.get("gameName") or ""
    dur     = selected_bk.get("durationMins") or 0

    try:
        consoles = fetch_console_status()
        free_ids = {c["id"] for c in consoles if c["status"] == "Free"}
    except Exception as e:
        logger.error("step_book_link: %s", e, exc_info=True)
        free_ids = set()

    # Allow if console is Free OR Scheduled (reserved but not yet Active/in-session)
    try:
        consoles_full = fetch_console_status()
        console_status_map = {c["id"]: c["status"] for c in consoles_full}
    except Exception as e:
        logger.error("step_book_link: %s", e, exc_info=True)
        console_status_map = {}
    console_current_status = console_status_map.get(console, "Free")
    if console and console_current_status == "Active":
        await update.message.reply_text(
            f"⚠️ <b>{console}</b> ယခု Session တက်နေပြီ (Active)\n"
            f"Console ကို ကိုယ်တိုင် ရွေးပါ",
            parse_mode="HTML",
        )
        context.user_data["_bk_linked_id"] = bk_id
        return await _show_console_select(update, context)
    elif console and console not in free_ids and console_current_status != "Scheduled":
        await update.message.reply_text(
            f"⚠️ <b>{console}</b> ယခု Free မဟုတ်ပါ\n"
            f"Console ကို ကိုယ်တိုင် ရွေးပါ",
            parse_mode="HTML",
        )
        context.user_data["_bk_linked_id"] = bk_id
        return await _show_console_select(update, context)

    context.user_data["bk_console"]      = console
    context.user_data["bk_member"]       = member
    context.user_data["bk_game"]         = game
    context.user_data["bk_planned_mins"] = int(dur)
    context.user_data["_bk_linked_id"]   = bk_id

    try:
        staff_list = fetch_staff()
        staff = staff_list[0] if len(staff_list) == 1 else context.user_data.get("staff_name", "")
    except Exception as e:
        logger.error("step_book_link: %s", e, exc_info=True)
        staff = context.user_data.get("staff_name", "")
    context.user_data["bk_staff"] = staff

    await update.message.reply_text(
        f"✅ <b>Booking #{bk_id} ချိတ်ဆက်ပြီ!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕹️ Console : <b>{console}</b>\n"
        f"👤 Member  : <b>{member}</b>\n"
        f"🎮 Game    : <b>{game or '—'}</b>\n"
        f"⏱️ Duration: <b>{dur or '—'} mins</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"အချက်အလက်များ autofill ဖြစ်ပြီ — ဆက်သွားမည်",
        parse_mode="HTML",
    )
    return await prompt_book_mins(update, context)

async def step_book_console(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    logging.warning("DBG: step_book_console: text=%s", text)
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text in (BTN_BACK, BTN_BACK_MAIN):
        return await show_console_menu(update, context)

    # Extract console ID (text may include " (PS5)" suffix)
    cid = text.split("(")[0].strip()
    valid = {c["id"] for c in fetch_console_status()} or VALID_CONSOLES
    if cid not in valid:
        await update.message.reply_text("⚠️ Keyboard မှ Console ရွေးပေးပါ")
        return await prompt_book_console(update, context)

    context.user_data["bk_console"] = cid
    # --- Console already Active guard -----------------------------------------------
    try:
        all_consoles = fetch_console_status()
        active_consoles = [c for c in all_consoles if c.get("id","").upper() == cid.upper() and c.get("status","Free") in ("Active", "Scheduled")]
        if active_consoles:
            mbr  = active_consoles[0].get("member") or "Guest"
            game = active_consoles[0].get("game") or ""
            game_txt = (" (" + game + ")") if game else ""
            msg = (
                "\u26a0\ufe0f <b>" + cid + "</b> \u1000 <b>Active</b> \u1016\u103c\u102d\u1014\u103a\u1035\u1014\u1031\u102b\u103a\u1015\u102b\u1010\u1030\u1000\u103b!\n"
                + "\U0001f464 " + mbr + game_txt + "\n"
                + "Session \u101e\u1031\u102c\u1004\u1039\u1019\u103e\u102c\u101e\u102c \u1011\u1000\u1039\u1016\u102d\u1014\u1039\u1004\u103d\u1032\u1037\u1021\u102c:\u1014\u1031\u102b\u103a\u1015\u1031\u1000\u103b!"
        )
            await update.message.reply_text(msg, parse_mode="HTML")
            return await prompt_book_console(update, context)
    except Exception as e:
        logger.error("step_book_console: active-check %s", e, exc_info=True)
        pass
    # ---------------------------------------------------------------------------------

    members = await fetch_members_async()
    kb = [["0 (Guest)"]] + [[m] for m in members] + [[BTN_BACK, BTN_CANCEL]]
    await update.message.reply_text(
        f"🕹️ *{cid}* — session\n\n"
        "👤 Member ID ရွေးပါ (သို့) ရိုက်ရှာပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return BOOK_MEMBER

async def step_book_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    logging.warning("DBG: step_book_member: text=%s", text)
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_book_console(update, context)
    if text == BTN_BACK_MAIN:
        return await show_main_menu(update, context)

    cid = context.user_data.get("bk_console", "")
    try:
        members = await fetch_members_async()
    except Exception as e:
        await update.message.reply_text(f"❌ Member list ဖတ်မရပါ: {e}\nထပ်ကြိုးစားပါ")
        return BOOK_MEMBER

    member_id = "Guest"

    if text == "0 (Guest)":
        member_id = "Guest"
    elif text in members:
        member_id = text
    else:
        # partial search
        matches = [m for m in members if text.upper() in m.upper()]
        if len(matches) == 1:
            member_id = matches[0]
        elif matches:
            kb = [["0 (Guest)"]] + [[m] for m in matches] + [[BTN_BACK, BTN_CANCEL]]
            await update.message.reply_text(
                f"🔍 <b>{len(matches)}</b> ကိုက်ညီသည် — ရွေးပါ:",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
            )
            return BOOK_MEMBER
        else:
            member_id = text  # allow free-text (walk-in not in sheet)

    try:
        staff_list = fetch_staff()
        staff = staff_list[0] if len(staff_list) == 1 else context.user_data.get("staff_name", "")
    except Exception as e:
        logger.error("step_book_member: %s", e, exc_info=True)
        staff = context.user_data.get("staff_name", "")

    # ── Duplicate session guard (non-guest only) ─────────────────────────
    if member_id not in ("Guest", "0 (Guest)"):
        try:
            all_consoles = fetch_console_status()
        except Exception as e:
            logger.error("step_book_member: %s", e, exc_info=True)
            all_consoles = []
        existing = [
            c for c in all_consoles
            if c.get("member") == member_id and c.get("status") in ("Active", "Scheduled")
        ]
        if existing:
            # Build list of all active sessions for this member
            session_lines = []
            for ex in existing:
                s = ex.get("start", "?")
                _, dfmt = calc_duration(s) if s and s != "?" else (0, "?")
                session_lines.append(f"🕹️ <b>{ex['id']}</b>  |  🕐 {s} ({dfmt})")
            sessions_text = "\n".join(session_lines)
            # Store pending booking params for the confirm handler
            context.user_data["bk_pending_member"] = member_id
            context.user_data["bk_pending_staff"]  = staff
            await update.message.reply_text(
                f"⚠️ <b>ထပ်နေသော Session {len(existing)} ခုရှိသည်!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 Member  : <b>{member_id}</b>\n"
                f"{sessions_text}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"ဒီ member ကို <b>{cid}</b> မှာ ထပ် session ဖွင့်မည်လား?",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(
                    [[BTN_BOOK_PROCEED], [BTN_NO_RESELECT]],
                    resize_keyboard=True,
                ),
            )
            return BOOK_DUP_WARN
    # ────────────────────────────────────────────────────────────────────

    # Save resolved member+staff and ask which game first
    context.user_data["bk_member"] = member_id
    context.user_data["bk_staff"]  = staff
    return await prompt_book_game(update, context)

async def prompt_book_game(update, context):
    """Ask which game the customer will play this session.
    Only shows games installed on the selected console.
    Offers SSD Transfer button if game is not yet installed.
    """
    cid       = context.user_data.get("bk_console", "")
    cid = cid.replace(" ", "")  # normalize spaces in console ID
    member_id = context.user_data.get("bk_member", "Guest")
    installed = await get_games_on_console_async(cid)
    kb_rows: list = []
    if installed:
        row: list = []
        for t in installed:
            row.append(t)
            if len(row) == 2:
                kb_rows.append(row)
                row = []
        if row:
            kb_rows.append(row)
        note = f"📋 <b>{cid}</b> တွင် ထည့်ထားသော ဂိမ်း {len(installed)} ခု"
    else:
        note = f"⚠️ <b>{cid}</b> တွင် ဂိမ်း မထည့်ရသေးပါ — SSD မှ Transfer ဦးလုပ်ပါ"
    kb_rows.append([BTN_SSD_TRANSFER])
    kb_rows.append([BTN_SKIP_GAME])
    kb_rows.append([BTN_BACK, BTN_CANCEL])
    await update.message.reply_text(
        f"🎮 <b>ဘယ် Game ကစားမည်?</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕹️ Console : <b>{cid}</b>  👤 <b>{member_id}</b>\n"
        f"{note}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"မပါသော ဂိမ်း ဆော့မည်ဆို <b>🔄 SSD Transfer</b> နှိပ်ပါ",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return BOOK_GAME

async def step_book_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game selection for the session."""
    text = update.message.text.strip()
    logging.warning("DBG: step_book_game: text=%s, bk_console=%s", text, context.user_data.get("bk_console", ""))
    cid       = context.user_data.get("bk_console", "")
    member_id = context.user_data.get("bk_member", "Guest")
    staff     = context.user_data.get("bk_staff", "")
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        context.user_data["bk_member"] = member_id
        context.user_data["bk_staff"]  = staff
        return BOOK_MEMBER
    if text == BTN_SSD_TRANSFER:
        # Redirect to SSD transfer, auto-fill target console = bk_console
        context.user_data["ssd_return_to_session"] = True
        context.user_data["ssd_xfer_target_cons"]  = cid
        await update.message.reply_text(
            f"🔄 <b>SSD → {cid} Transfer</b>\n\nSSD ကို ရွေးပါ:",
            parse_mode="HTML",
            reply_markup=_ssd_kb(),
        )
        return SSD_XFER_SSD
    game = "" if text == BTN_SKIP_GAME else text
    context.user_data["bk_game"] = game
    return await prompt_book_mins(update, context)

async def prompt_book_mins(update, context):
    """Ask for planned play duration so a 5-min reminder can be scheduled."""
    cid       = context.user_data.get("bk_console", "")
    member_id = context.user_data.get("bk_member", "Guest")
    kb = [
        ["30", "60", "90"],
        ["120", "150", "180"],
        ["240", "300", "360"],
        [BTN_SKIP_TIMER],
        [BTN_BACK, BTN_CANCEL],
    ]
    await update.message.reply_text(
        f"⏱️ <b>Play Duration (Timer)</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕹️ Console : <b>{cid}</b>  👤 <b>{member_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"ကစားမည့် မိနစ် ရွေးပါ (5min မတိုင်ခင် auto-remind ပေးမည်)\n"
        f"မလိုပါက Skip နှိပ်ပါ",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return BOOK_MINS

async def step_book_mins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle planned-mins input and finalize the booking."""
    text      = update.message.text.strip()
    cid       = context.user_data.get("bk_console", "")
    member_id = context.user_data.pop("bk_member", "Guest")
    staff     = context.user_data.pop("bk_staff", "")

    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        # Go back to game selection
        context.user_data["bk_member"] = member_id
        context.user_data["bk_staff"]  = staff
        return await prompt_book_game(update, context)

    planned_mins = 0
    if text != BTN_SKIP_TIMER:
        try:
            planned_mins = int(text)
        except ValueError:
            await update.message.reply_text("⚠️ ဂဏန်းသာ ထည့်ပါ သို့ keyboard မှ ရွေးပါ")
            context.user_data["bk_member"] = member_id
            context.user_data["bk_staff"]  = staff
            return await prompt_book_mins(update, context)

    game = context.user_data.pop("bk_game", "")
    return await _do_create_booking(update, context, cid, member_id, staff, planned_mins, game)

async def _do_create_booking(update, context, cid: str, member_id: str,
                              staff: str, planned_mins: int = 0, game: str = ""):
    """Actually create the booking, show confirmation, and schedule timer if set."""
    logging.warning("DBG: _do_create_booking: cid=%s member=%s staff=%s mins=%d game=%s", cid, member_id, staff, planned_mins, game)
    # Pre-compute planned end time so it can be stored in Console_Booking col F.
    # This lets the customer bot detect disc-game conflicts accurately.
    _planned_end = ""
    if planned_mins > 0:
        _end_pre = now_mmt() + timedelta(minutes=planned_mins)
        _planned_end = _end_pre.strftime("%H:%M")
    # Check if this session is linked to a customer booking
    _linked_cust_bk = context.user_data.pop("_bk_linked_id", "")
    _notes = game
    if _linked_cust_bk:
        _notes = f"{game} [BK#{_linked_cust_bk}]" if game else f"[BK#{_linked_cust_bk}]"
    try:
        bk_id = await create_booking_async(cid, member_id, staff, notes=_notes, planned_end=_planned_end)
    except Exception as e:
        await update.message.reply_text(f"❌ Session save မအောင်မြင်ပါ: {e}")
        return await show_console_menu(update, context)
    # Store linked booking ID for session-end tracking
    if _linked_cust_bk:
        context.user_data["_bk_linked_id"] = _linked_cust_bk

    # Track current session game in Console_Games (type = "Session")
    if game:
        try:
            # Remove any previous Session entry for this console first
            _delete_session_game(cid)
            await add_console_game_async(cid, game, "Session", f"BK:{bk_id}")
        except Exception as e:
            logger.error("_do_create_booking: %s", e, exc_info=True)
            pass

    now      = now_mmt()
    start_t  = now.strftime("%H:%M")
    timer_line = ""
    game_line  = f"\n🎮 Game    : <b>{game}</b>" if game else ""
    if planned_mins > 5:
        end_dt     = now + timedelta(minutes=planned_mins)
        end_t      = end_dt.strftime("%H:%M")
        delay_secs = (planned_mins - 5) * 60
        chat_id    = update.effective_chat.id
        # Use STAFF_NOTIFY_CHAT as canonical remind key so that
        # cb_extend_timer (which embeds _target_chat in callback data) uses the same key.
        _remind_chat_id = int(STAFF_NOTIFY_CHAT) if STAFF_NOTIFY_CHAT else chat_id

        remind_dt = now + timedelta(minutes=planned_mins - 5)
        remind_t = remind_dt.strftime("%H:%M")
        # Bot loop fires at "5 min before end", with inline-keyboard Extend/Done buttons.
        _cancel_remind(cid, _remind_chat_id)   # clear any stale task for this console
        task = asyncio.create_task(
            _remind_loop(context.bot, _remind_chat_id, cid, member_id,
                         planned_mins, end_t, delay_secs)
        )
        _REMIND_TASKS[_remind_key(cid, _remind_chat_id)] = task
        timer_line = f"\n⏰ Timer    : <b>{planned_mins} mins</b> (remind @ {remind_t} — ဆုံးတဲ့အချိန် 5min ကြားတိုင်း repeat)"

    await update.message.reply_text(
        f"✅ <b>Session စတင်ပြီ!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪪 ID      : <code>{bk_id}</code>\n"
        f"🕹️ Console : <b>{cid}</b>\n"
        f"👤 Member  : <b>{member_id}</b>"
        f"{game_line}\n"
        f"🕐 Start   : <b>{start_t}</b>"
        f"{timer_line}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Session ဆုံးသောအခါ ⏹️ Session ဆုံး နှိပ်ပါ",
        parse_mode="HTML",
    )
    return await show_console_menu(update, context)

async def step_book_dup_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Proceed / Back after duplicate-session warning during booking."""
    text = update.message.text.strip()
    cid         = context.user_data.get("bk_console", "")
    member_id   = context.user_data.pop("bk_pending_member", "Guest")
    staff       = context.user_data.pop("bk_pending_staff", "")

    if text == BTN_BOOK_PROCEED:
        # Proceed with game selection step
        context.user_data["bk_member"] = member_id
        context.user_data["bk_staff"]  = staff
        return await prompt_book_game(update, context)

    # BTN_NO_RESELECT / BTN_CANCEL / anything else → back to member selection
    context.user_data["bk_console"] = cid
    return BOOK_MEMBER

