from bot.handlers.booking_flow import _post_n8n_booking_reminder

# ── Staff Booking State Stack (for proper Back navigation) ─────────────────
def _sbk_push(context, state):
    """Push current state onto navigation stack."""
    stack = context.user_data.setdefault("_sbk_state_stack", [])
    stack.append(state)

def _sbk_pop(context):
    """Pop and return previous state, or None if stack is empty."""
    stack = context.user_data.get("_sbk_state_stack", [])
    return stack.pop() if stack else None

def _sbk_back(context, update, fallback_fn):
    """Handle Back button: pop stack, return to previous state or fallback."""
    prev = _sbk_pop(context)
    if prev is not None:
        return prev
    # Stack empty → go to admin menu or booking hub
    if context.user_data.get("sbk_from_hub"):
        return fallback_fn  # will be awaited by caller
    from bot.handlers.admin import show_admin_menu
    return show_admin_menu


from bot import (
    BOOK_CHECKIN_BIND, BOOK_CONSOLE, BOOK_DUP_WARN, BOOK_GAME, BOOK_MEMBER,
    BOOK_MINS, BTN_BACK, BTN_BACK_MAIN, BTN_BOOK_PROCEED, BTN_CANCEL,
    BTN_NO_RESELECT, BTN_SBK_CONFIRMED, BTN_SBK_CONFIRM_BOOK,
    BTN_SBK_CUSTOM, BTN_SBK_NEW, BTN_SBK_SKIP_GAME, BTN_SBK_SKIP_PHONE,
    BTN_SBK_WAITLIST, BTN_SKIP_GAME, BTN_SKIP_TIMER, BTN_SSD_TRANSFER,
    CONSOLE_MENU, MAIN_MENU, N8N_BOOKING_WEBHOOK, SBK_CONFIRM,
    SBK_CONSOLE, SBK_CUST_NAME, SBK_PHONE, SBK_DATE, SBK_TIME,
    SBK_DURATION, SSD_XFER_SSD, STAFF_NOTIFY_CHAT, STAFF_NOTIFY_THREAD, VALID_CONSOLES,
    _psvibe_get_async, _psvibe_patch_async, _psvibe_post_async,
    add_console_game, add_console_game_async, _delete_session_game,     calc_duration,
    check_disc_session_conflict, cmd_cancel, create_booking, create_booking_async,
    ConsoleStatusError,
    fetch_console_games, fetch_console_games_async, fetch_console_status, fetch_console_status_async, fetch_games, fetch_games_async,
    fetch_members, fetch_staff, get_consoles_with_game, get_consoles_with_game_async,
    get_games_on_console, get_games_on_console_async, now_mmt, show_admin_menu, show_console_menu,
    show_main_menu, today_str,
    fetch_members_async,
    api_fetch_member_data_async,
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
from bot.handlers.booking_flow import _cancel_remind, _remind_loop, _REMIND_TASKS, _remind_key, add_no_timer_console, remove_no_timer_console
from bot.handlers.notify import _notify_customer, get_customer_chat_id

# Track advance reminder tasks for cancellation
_ADVANCE_REMIND_TASKS: dict[str, asyncio.Task] = {}

def _cancel_advance_reminder(bk_id: int) -> bool:
    """Cancel a pending advance reminder task for a booking."""
    key = f"adv_{bk_id}"
    task = _ADVANCE_REMIND_TASKS.pop(key, None)
    if task and not task.done():
        task.cancel()
        return True
    return False


async def _sbk_console_kb(date_str: str = None, time_slot: str = None) -> list:
    """Return keyboard of all consoles with availability for the selected time slot.

    When date_str+time_slot are provided, checks booking conflicts AND live Active
    session end times (from console_status). A console currently Active will show ✅
    if its session ends before the selected time.
    """
    try:
        consoles = fetch_console_status()
    except ConsoleStatusError:
        logging.warning("Staff booking: fetch_console_status failed — API server may be down")
        # Fall back to all consoles without live status indicators
        return [[c] for c in sorted(VALID_CONSOLES)] + [[BTN_BACK, BTN_CANCEL]]
    except Exception as e:
        logging.warning("Failed to fetch console status (staff booking): %s", e)
        return [[c] for c in sorted(VALID_CONSOLES)] + [[BTN_BACK, BTN_CANCEL]]

    # ── If date + time provided, override live status with future availability ──
    conflict_cids = set()  # consoles that have a conflict at the selected time
    active_ends_before = {}  # cid -> True if Active session ends before target
    if date_str and time_slot:
        try:
            from datetime import datetime as _dt
            # Parse selected start time
            sel_dt = _dt.strptime(f"{date_str} {time_slot}", "%Y-%m-%d %H:%M")
            sel_min = sel_dt.hour * 60 + sel_dt.minute
            today_str = _dt.utcnow().strftime("%Y-%m-%d")
            is_today = (date_str == today_str)

            # ── Check console_status for Active sessions (today only) ──
            if is_today:
                for c in consoles:
                    cid = c.get("id") or c.get("console_id", "")
                    cstatus = (c.get("status") or "").lower()
                    if cstatus != "active":
                        continue
                    start_str = c.get("start_time", "")
                    if not start_str:
                        continue
                    try:
                        h, m = map(int, str(start_str).split(":")[:2])
                        dur = int(c.get("duration_mins") or 0)
                        if dur <= 0:
                            continue
                        end_min = h * 60 + m + dur
                        if end_min > sel_min:
                            conflict_cids.add(cid)
                    except (ValueError, TypeError, AttributeError):
                        pass

            # ── Check bookings API for conflicts ──
            all_bks = []
            for st in ("Active", "confirmed", "pending", "pending_check_in"):
                try:
                    raw = await _psvibe_get_async(f"bookings?status={st}")
                    if isinstance(raw, list):
                        all_bks.extend(raw)
                    elif isinstance(raw, dict):
                        all_bks.extend(raw.get("bookings", []))
                except Exception:
                    pass
            for b in all_bks:
                b_date = (b.get("date") or "")[:10]
                if b_date != date_str:
                    continue
                b_slot = b.get("timeSlot", "")
                b_dur = int(b.get("durationMins") or 60)
                if not b_slot:
                    continue
                try:
                    b_start = _dt.strptime(f"{b_date} {b_slot}", "%Y-%m-%d %H:%M")
                    from datetime import timedelta
                    b_end = b_start + timedelta(minutes=b_dur)
                    # Conflict if selected time falls within booking window
                    if b_start <= sel_dt < b_end:
                        conflict_cids.add((b.get("consoleId") or b.get("console_id") or "").strip())
                except Exception:
                    pass
        except Exception as e:
            logging.warning("_sbk_console_kb: future-avail check failed: %s", e)

    rows = []
    row  = []
    for c in sorted(consoles, key=lambda x: x.get("id", x.get("console_id", ""))):
        cid = c.get("id") or c.get("console_id", "")
        if date_str and time_slot:
            # Future availability mode: check console_status + booking conflicts at selected time
            if cid in conflict_cids:
                icon = "🔴"
            else:
                icon = "✅"  # will be free at selected time (even if currently Active)
        else:
            # Live status mode (current behavior)
            live = c.get("status", c.get("liveStatus", "Free"))
            if live == "Free":
                icon = "✅"
            elif live == "Reserved":
                icon = "🟡"
            else:
                icon = "🔴"
        ctype = c.get("type") or c.get("console_type", "")
        label = f"{cid} ({ctype}) {icon}" if ctype else f"{cid} {icon}"
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
    pending_bks   = await _psvibe_get_async("bookings?status=pending") or []
    confirmed_bks = await _psvibe_get_async("bookings?status=confirmed") or []

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
            f"👤 {b.get('customerName') or '—'}  📞 {b.get('phone') or '—'}\n"
            f"📅 {b['date']}  ⏰ {b['timeSlot']}\n"
            f"🕹️ Console: {b.get('console_id') or b.get('consoleType') or '—'}  ⏱️ {b['durationMins']} mins\n"
            f"🎮 Game: {b.get('gameName') or '—'}\n"
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
    bookings = await _psvibe_get_async("bookings?status=confirmed") or []
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

    for b in bookings[:30]:
        console_hint = b.get("console_id") or b.get("consoleType", "?")
        is_today = b.get("date", "") == today_s
        today_tag = "  🔵 Today" if is_today else ""
        _cname = (b.get('customerName') or '').strip()
        _phone = (b.get('phone') or '').strip()
        # If customerName is the same as phone or looks like a phone number (09xxx), skip 👤
        if _cname and _cname != _phone and not _cname.startswith('09'):
            _name_line = f"👤 {_cname}  📞 {_phone}\n"
        else:
            _name_line = f"📞 {_phone}\n"
        card = (
            f"✅ *Booking #{b['id']}*{today_tag}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{_name_line}"
            f"📅 {b['date']}  ⏰ {b['timeSlot']}\n"
            f"🕹️ Console: {console_hint}  ⏱️ {b.get('durationMins', '?')} mins\n"
            f"🎮 Game: {b.get('gameName') or '—'}\n"
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
    context.user_data["_sbk_state_stack"] = []  # fresh navigation stack
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
    return SBK_DATE

async def step_sbk_console(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle console selection."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text in (BTN_BACK, BTN_BACK_MAIN):
        prev = _sbk_pop(context)
        if prev is not None:
            return prev
        if context.user_data.get("sbk_from_hub"):
            return await cmd_staff_book_hub(update, context)
        return await show_admin_menu(update, context)

    cid, ctype = _sbk_parse_console_label(text)
    # Use cached valid set from _sbk_console_kb (avoids extra API call) + VALID_CONSOLES
    valid = context.user_data.get("_sbk_valid_consoles", set()) | set(VALID_CONSOLES)
    if not valid:
        # Cold path: no cached data yet, fetch live
        try:
            all_c = fetch_console_status()
            valid = {c["id"] for c in all_c} if all_c else VALID_CONSOLES
        except Exception:
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
    _sbk_push(context, SBK_CONSOLE)
    return SBK_CUST_NAME

async def step_sbk_cust_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle customer name / member selection."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        prev = _sbk_pop(context)
        if prev is not None:
            return prev
        # Fallback: go back to console selection
        rows = await _sbk_console_kb()
        # Cache valid console IDs for step_sbk_console validation
        try:
            all_c = fetch_console_status()
            context.user_data["_sbk_valid_consoles"] = {c["id"] for c in all_c if c.get("id")}
        except Exception:
            context.user_data["_sbk_valid_consoles"] = set(VALID_CONSOLES)
        await update.message.reply_text(
            "🕹️ Console ပြန်ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True),
        )
        return SBK_CONSOLE

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
    _sbk_push(context, SBK_CUST_NAME)
    return SBK_PHONE

async def step_sbk_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone → then ask booking duration (mins)."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        prev = _sbk_pop(context)
        if prev is not None:
            return prev
        # Fallback
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

    # Ask duration (mins) — then game, then confirm
    kb = [
        ["30", "60", "90"],
        ["120", "150", "180"],
        ["240", "300", "360"],
        ["420", "480"],
        [BTN_BACK, BTN_CANCEL],
    ]
    await update.message.reply_text(
        "⏱️ ကစားမည့် မိနစ် (Duration) ရွေးပါ:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    _sbk_push(context, SBK_PHONE)
    return SBK_DURATION

async def step_sbk_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date → then ask time slot."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text in (BTN_BACK, BTN_BACK_MAIN):
        prev = _sbk_pop(context)
        if prev is not None:
            return prev
        if context.user_data.get("sbk_from_hub"):
            return await cmd_staff_book_hub(update, context)
        return await show_admin_menu(update, context)

    if text == BTN_SBK_CUSTOM:
        await update.message.reply_text(
            "📅 ရက် ရိုက်ထည့်ပါ (format: M/D/YYYY)\nဥပမာ: 5/10/2026",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK, BTN_CANCEL]], resize_keyboard=True),
        )
        return SBK_DATE

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
            return SBK_DATE

    context.user_data["sbk_date"] = date_str

    # Build time slot keyboard with proper overlap-based availability indicators
    all_hours = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00",
                 "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"]
    # Minimum assumed duration for overlap checking (since actual duration
    # isn't selected until after console step — 30 min is a safe lower bound)
    MIN_SLOT_DUR = 30
    unavailable = set()
    try:
        parts_date = date_str.split("/")
        if len(parts_date) == 3:
            api_date = f"{parts_date[2]}-{parts_date[0].zfill(2)}-{parts_date[1].zfill(2)}"
            # Fetch ALL active/confirmed/pending bookings (no date filter in API)
            all_bookings = []
            for st in ("Active", "confirmed", "pending", "pending_check_in"):
                try:
                    raw = await _psvibe_get_async(f"bookings?status={st}")
                    if isinstance(raw, list):
                        all_bookings.extend(raw)
                    elif isinstance(raw, dict):
                        all_bookings.extend(raw.get("bookings", []))
                except Exception:
                    pass
            for b in all_bookings:
                # Filter to selected date only
                b_date = (b.get("date") or "")[:10]
                if b_date != api_date:
                    continue
                b_slot = b.get("timeSlot", "")
                if not b_slot:
                    continue
                b_dur = int(b.get("durationMins") or 60)
                # Parse booking start/end in minutes since midnight
                try:
                    bh, bm = map(int, b_slot.split(":")[:2])
                    b_start = bh * 60 + bm
                    b_end = b_start + b_dur
                except (ValueError, TypeError, AttributeError):
                    # Fallback: mark the exact hour
                    bh = b_slot.split(":")[0]
                    unavailable.add(f"{bh}:00")
                    continue
                # Check each time slot for overlap with this booking
                # Two windows overlap if: slot_start < booking_end AND slot_end > booking_start
                for slot in all_hours:
                    if slot in unavailable:
                        continue
                    try:
                        sh, sm = map(int, slot.split(":"))
                        s_start = sh * 60 + sm
                        s_end = s_start + MIN_SLOT_DUR
                        if s_start < b_end and s_end > b_start:
                            unavailable.add(slot)
                    except (ValueError, TypeError):
                        pass
    except Exception:
        pass
    row = []
    rows = []
    for slot in all_hours:
        icon = "🔴" if slot in unavailable else "🟢"
        label = f"{icon} {slot}"
        row.append(label)
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    kb = rows + [[BTN_BACK, BTN_CANCEL]]
    free_count = len([s for s in all_hours if s not in unavailable])
    await update.message.reply_text(
        f"📅 {date_str}\n\n⏰ Time Slot ရွေးပါ — 🟢 Available: {free_count}/{len(all_hours)} slots",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    _sbk_push(context, SBK_DATE)
    return SBK_TIME

async def step_sbk_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time slot -> check avail and show console selection."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        prev = _sbk_pop(context)
        if prev is not None:
            return prev
        # Fallback: show date selection
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
        return SBK_DATE

    import re as _re2
    # Strip icon prefix (🟢/🔴) if present
    time_clean = _re2.sub(r'^[🟢🔴]\s*', '', text)
    if not _re2.match(r"^\d{1,2}:\d{2}$", time_clean):
        await update.message.reply_text("⚠️ Time format: HH:MM  (ဥပမာ: 14:30)")
        return SBK_TIME

    context.user_data["sbk_time"] = time_clean

    # Pass date+time so _sbk_console_kb can check future availability
    sbk_date = context.user_data.get("sbk_date", "")
    api_date = ""
    if sbk_date:
        parts = sbk_date.split("/")
        if len(parts) == 3:
            api_date = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
    rows = await _sbk_console_kb(date_str=api_date, time_slot=time_clean)
    # Cache valid console IDs for step_sbk_console validation (avoids extra API call)
    try:
        all_c = fetch_console_status()
        context.user_data["_sbk_valid_consoles"] = {c["id"] for c in all_c if c.get("id")}
    except Exception:
        context.user_data["_sbk_valid_consoles"] = set(VALID_CONSOLES)
    if rows and len(rows) > 1:
        await update.message.reply_text(
            "✅ Available Consoles:\n\nConsole ID ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True),
        )
    else:
        await update.message.reply_text(
            "⚠️ Free console မရှိပါ\nနေ့ရက်အသစ် ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK, BTN_CANCEL]], resize_keyboard=True),
        )
    _sbk_push(context, SBK_TIME)
    return SBK_CONSOLE
async def step_sbk_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle duration → ask game."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        prev = _sbk_pop(context)
        if prev is not None:
            return prev
        # Fallback: re-ask time
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
        return SBK_TIME

    try:
        dur = int(text)
    except ValueError:
        await update.message.reply_text("⚠️ ဂဏန်းသာ ထည့်ပါ သို့ keyboard မှ ရွေးပါ")
        return SBK_DURATION
    if dur < 1 or dur > 1440:
        await update.message.reply_text("⚠️ Duration သည် 1-1440 မိနစ်ကြား ဖြစ်ရပါမည်")
        return SBK_DURATION
    context.user_data["sbk_dur"] = dur

    # Build game keyboard
    try:
        games = await fetch_games_async()
        game_names = [g["title"] for g in games if g.get("title")]
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
    _sbk_push(context, SBK_DURATION)
    return SBK_CONFIRM


async def _sbk_advance_reminder(bot, booking_id: int, cid: str, ctype: str, name: str, phone: str,
                                 date_str: str, time_str: str, dur: int, game: str, staff: str,
                                 tg_chat: str = ""):
    """Send 30-min advance reminder to admin group for a confirmed booking.
    Auto-cancels itself if booking is no longer confirmed at reminder time.
    DISABLED — n8n webhook handles reminders instead (Gap #5 fix)."""
    return
    key = f"adv_{booking_id}"
    _ADVANCE_REMIND_TASKS[key] = asyncio.current_task()  # type: ignore
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
        remind_dt = booking_dt - timedelta(minutes=30)
        now_mmt_dt = now_mmt()

        # If remind time already passed but booking is still in the future, fire immediately
        if remind_dt <= now_mmt_dt:
            if booking_dt <= now_mmt_dt:
                return  # Booking already started — no reminder needed
            # Booking is < 30 min away — fire immediately

        seconds_until_remind = max(1, int((remind_dt - now_mmt_dt).total_seconds()))
        await asyncio.sleep(seconds_until_remind)

        # ⚠️ Verify booking is still active before sending
        bk_data = await _psvibe_get_async(f"bookings/{booking_id}")
        if isinstance(bk_data, dict):
            if "booking" in bk_data:
                bk_data = bk_data["booking"]
        status = (bk_data or {}).get("status", "") if isinstance(bk_data, dict) else ""
        if status not in ("confirmed", "pending", "pending_check_in"):
            logger.info("_sbk_advance_reminder: bk#%s status=%s — skipping reminder", booking_id, status)
            return

        notify_text = (
            f"\u23f0 <b>Booking #{booking_id} Reminder!</b>\n"
            f"\u23f1\ufe0f <b>30 \u1019\u102d\u1014\u1037\u1001\u103a\u1021\u101c\u102d\u102f</b> \u1000\u103c\u102e\u1019\u1000\u103a\n"
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

        # 📱 Also notify customer if they have a Telegram chat ID
        if tg_chat:
            cust_notify_text = (
                f"\u23f0 <b>PS VIBE — Booking Reminder!</b>\n"
                f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
                f"\u267f {date_str}  \u23f0 {time_str}\n"
                f"\u267f Duration: <b>{dur} mins</b>  \u2694\ufe0f {game or '---'}\n"
                f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
                f"\u23f1\ufe0f <b>30 \u1019\u102d\u1014\u1037\u1001\u103a\u1021\u101c\u102d\u102f</b> \u1000\u103c\u102d\u102f\u1010\u1000\u103a \u101b\u1031\u102c\u1000\u103a\u1015\u102b\n"
                f"\u26a0\ufe0f \u1021\u1001\u103b\u102d\u1014\u103a\u1019\u103e\u102c \u101c\u102c\u101c\u102c\u1019\u103b\u1010\u103a \u1015\u103c\u1004\u103a\u1006\u1004\u103a\u1015\u102b!"
            )
            await asyncio.to_thread(_notify_customer, tg_chat, cust_notify_text)
            logger.info("_sbk_advance_reminder: Booking #%s customer reminder sent to %s", booking_id, tg_chat)
    except asyncio.CancelledError:
        logger.info("_sbk_advance_reminder: bk#%s cancelled", booking_id)
    except Exception as e:
        logger.error("_sbk_advance_reminder: %s", e, exc_info=True)
    finally:
        _ADVANCE_REMIND_TASKS.pop(key, None)

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

        # Look up customer's telegram_chat_id from phone (for auto-cancel notifications)
        # fetch_members_async() returns member ID strings; resolve phone → member_id via API
        tg_chat_id = ""
        if phone and phone != "—":
            try:
                from bot.handlers.notify import get_customer_chat_id as _gcci
                mids = await fetch_members_async()
                if mids and isinstance(mids, list):
                    # Find member_id matching the phone by fetching each member's data
                    for mid in mids[:30]:  # limit to avoid too many API calls
                        if not isinstance(mid, str):
                            # Old format — dict with phone
                            if str(mid.get("phone", "")).strip() == phone.strip():
                                _found_id = mid.get("member_id") or mid.get("id", "")
                                if _found_id:
                                    tg_chat_id = await asyncio.to_thread(_gcci, _found_id) or ""
                                break
                        else:
                            # New format — member ID string; fetch full data
                            try:
                                mdata = await api_fetch_member_data_async(mid)
                                if mdata and str(mdata.get("phone", "")).strip() == phone.strip():
                                    tg_chat_id = await asyncio.to_thread(_gcci, mid) or ""
                                    break
                            except Exception:
                                continue
            except Exception as _e:
                logger.warning("step_sbk_confirm: tg_chat lookup failed: %s", _e)

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
            "telegramChatId": tg_chat_id,
        }

        # ── Client-side overlap check before submitting ──────────────────
        # Convert date from M/D/YYYY → YYYY-MM-DD for the conflict API
        import re as _re_cf
        _cf_date = date
        _dm = _re_cf.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", date)
        if _dm:
            _cf_date = f"{_dm.group(3)}-{_dm.group(1).zfill(2)}-{_dm.group(2).zfill(2)}"
        try:
            cf_result = await _psvibe_post_async("booking-conflicts", {
                "date": _cf_date,
                "time_slot": slot,
                "duration_mins": int(dur),
                "console_id": cid,
            })
            if cf_result and cf_result.get("has_conflict"):
                conflicts = cf_result.get("conflicts", [])
                _c = conflicts[0] if conflicts else {}
                _c_id = _c.get("id", "?")
                _c_cid = _c.get("console_id", cid)
                _c_status = _c.get("status", "")
                await update.message.reply_text(
                    f"⚠️ <b>Booking Conflict!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🕹️ Console <b>{_c_cid}</b> တွင် {_cf_date} {slot} မှ\n"
                    f"Booking <b>#{_c_id}</b> ({_c_status}) စာရင်းရှိပြီးဖြစ်ပါသည်\n\n"
                    "⏮️ Back နှိပ်၍ အခြား Console/Time ပြန်ရွေးပါ",
                    parse_mode="HTML",
                )
                kb = [[BTN_BACK, BTN_CANCEL]]
                await update.message.reply_text(
                    "ပြန်သွားရန် ⏮️ Back နှိပ်ပါ",
                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
                )
                return SBK_CONFIRM
        except Exception as _ce:
            logger.warning("step_sbk_confirm: pre-check conflict API failed: %s — proceeding", _ce)

        # ── Submit booking to API ────────────────────────────────────────
        result = await _psvibe_post_async("bookings", payload)

        # Handle connection failure (no response)
        if not result:
            await update.message.reply_text(
                "❌ Booking create မအောင်မြင်ပါ\nAPI ချိတ်ဆက်မရပါ — ထပ်ကြိုးစားပါ",
            )
            return await show_main_menu(update, context)

        # Handle HTTP 4xx/5xx error responses
        _http_sc = result.get("status_code")
        if _http_sc is not None and _http_sc >= 400:
            _err_msg = result.get("message") or result.get("error") or "Unknown error"
            if _http_sc == 409:
                # 409 Conflict — show API's conflict message
                await update.message.reply_text(
                    f"⚠️ <b>Booking Conflict!</b>\n━━━━━━━━━━━━━━━━━━\n{_err_msg}\n\n"
                    "⏮️ Back နှိပ်၍ အခြား Console/Time ပြန်ရွေးပါ",
                    parse_mode="HTML",
                )
            else:
                await update.message.reply_text(
                    f"❌ Booking create မအောင်မြင်ပါ\n"
                    f"Error #{_http_sc}: {_err_msg}\n\n"
                    "⏮️ Back နှိပ်၍ ပြန်စစ်ပြီး ထပ်ကြိုးစားပါ",
                )
            kb = [[BTN_BACK, BTN_CANCEL]]
            await update.message.reply_text(
                "ပြန်သွားရန် ⏮️ Back နှိပ်ပါ",
                reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            )
            return SBK_CONFIRM

        # Handle success=false at HTTP 200 level (API validation errors, etc.)
        if isinstance(result, dict) and result.get("success") is False:
            _api_err = result.get("error") or result.get("message") or "Unknown error"
            await update.message.reply_text(
                f"❌ Booking create မအောင်မြင်ပါ\n{_api_err}\n\n"
                "⏮️ Back နှိပ်၍ ပြန်စစ်ပြီး ထပ်ကြိုးစားပါ",
            )
            kb = [[BTN_BACK, BTN_CANCEL]]
            await update.message.reply_text(
                "ပြန်သွားရန် ⏮️ Back နှိပ်ပါ",
                reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            )
            return SBK_CONFIRM

        # Handle unexpected response format (no booking id)
        if "id" not in result:
            await update.message.reply_text(
                "❌ Booking create မအောင်မြင်ပါ\nထပ်ကြိုးစားပါ",
            )
            return await show_main_menu(update, context)

        bk_id = result["id"]

        # ── Admin Notification (with dedup + message_id tracking) ──
        admin_msg_id = ""
        if STAFF_NOTIFY_CHAT:
            notif = (
                f"📅 <b>New Staff Booking #{bk_id}</b>\n"
                f"🕹️ {cid} ({ctype})\n"
                f"👤 {name}  📞 {phone}\n"
                f"📅 {date}  ⏰ {slot}\n"
                f"⏱️ {dur} mins  🎮 {game or '—'}\n"
                f"Created by {staff}"
            )
            # ── Delete old admin notifications for same phone+date ──
            try:
                _prev = await _psvibe_get_async(f"bookings/by-phone-date?phone={phone}&date={_cf_date}")
                if _prev and isinstance(_prev, list):
                    for _pb in _prev:
                        _old = _pb.get("admin_notify_msg_id")
                        if _old and (_pb.get("id") != bk_id):
                            try:
                                await context.bot.delete_message(
                                    chat_id=int(STAFF_NOTIFY_CHAT),
                                    message_id=int(_old)
                                )
                            except Exception:
                                pass  # message may already be deleted
            except Exception:
                pass  # best-effort cleanup
            # ── Send notification via Sale Bot (to capture message_id) ──
            try:
                sent = await context.bot.send_message(
                    chat_id=int(STAFF_NOTIFY_CHAT),
                    text=notif,
                    parse_mode="HTML",
                    message_thread_id=STAFF_NOTIFY_THREAD,
                )
                admin_msg_id = str(sent.message_id)
            except Exception:
                # Fallback: use Customer Bot token
                await asyncio.to_thread(_notify_customer, STAFF_NOTIFY_CHAT, notif)

        # ── Store admin_msg_id on booking ──
        if admin_msg_id:
            try:
                await _psvibe_patch_async(f"admin-notify/{bk_id}", {"admin_notify_msg_id": admin_msg_id})
            except Exception:
                pass  # non-critical

        # 📱 Send confirmation notification to customer (if tg_chat_id is known)
        if tg_chat_id and CUSTOMER_BOT_TOKEN:
            _cust_msg = (
                "မင်္ဂလာပါ 🙏\n\n"
                f"သင်၏ Booking (#{bk_id}) ကို အတည်ပြုပြီးပါပြီ။\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🕹️ Console: {cid} ({ctype})\n"
                f"📅 {date}  ⏰ {slot}\n"
                f"⏱️ {dur} mins  🎮 {game or '—'}\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"PS Vibe မှ ကြိုဆိုပါသည်! ✨\n"
                f"Play The Game. Share The VIBE!"
            )
            await asyncio.to_thread(_notify_customer, tg_chat_id, _cust_msg)
            logger.info(f"step_sbk_confirm: Customer notification sent for BK#{bk_id} to {tg_chat_id}")

        # Fire n8n reminder webhook (non-blocking)
        asyncio.create_task(_post_n8n_booking_reminder(
            bk_id=bk_id, customer_name=name, phone=phone,
            console_id=cid, console_type=ctype,
            date_str=date, time_slot=slot, duration_mins=int(dur),
            tg_chat=tg_chat_id,
        ))

        # DISABLED — n8n webhook handles reminders (Gap #5 fix)
        # asyncio.create_task(_sbk_advance_reminder(
        #     context.bot, bk_id=bk_id, cid=cid, ctype=ctype, name=name, phone=phone,
        #     date_str=date, time_str=slot, dur=int(dur), game=game, staff=staff,
        #     tg_chat=tg_chat_id,
        # ))

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
        prev = _sbk_pop(context)
        if prev is not None:
            return prev
        # Fallback: re-show game selection
        dur = context.user_data.get("sbk_dur", 60)
        context.user_data.pop("sbk_game", None)
        try:
            games = await fetch_games_async()
            game_names = [g["title"] for g in games if g.get("title")]
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
    context.user_data["bk_origin"] = origin
    try:
        consoles = await fetch_console_status_async()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return CONSOLE_MENU
    free = [c for c in consoles if c["status"] in ("Free", "Reserved")]
    if not free:
        await update.message.reply_text(
            "⚠️ လက်ရှိ Free ဖြစ်သော Console မရှိပါ\n"
            "Active session များ ဦးစွာ ဆုံးအောင်လုပ်ပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK]], resize_keyboard=True),
        )
        return CONSOLE_MENU
    # ── Step 0: Show console selection FIRST ────────────────────────────
    return await _show_console_select(update, context, free, consoles)

async def _show_console_select(update: Update, context: ContextTypes.DEFAULT_TYPE, free_consoles=None, all_consoles=None):
    """Show the console selection keyboard."""
    if free_consoles is None:
        try:
            consoles = await fetch_console_status_async()
            free_consoles = [c for c in consoles if c["status"] in ("Free", "Reserved")]
            all_consoles = consoles
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            return CONSOLE_MENU
    # Cache ALL valid console IDs for step_book_console validation (avoids extra API call)
    if all_consoles:
        context.user_data["_bk_valid_consoles"] = {c["id"] for c in all_consoles if c.get("id")}
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

async def step_book_console(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    logging.warning("DBG: step_book_console: text=%s", text)
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text in (BTN_BACK, BTN_BACK_MAIN):
        return await show_console_menu(update, context)

    # Extract console ID (text may include " (PS5)" suffix)
    cid = text.split("(")[0].strip()
    # Use cached valid set from prompt_book_console (no extra API call) + VALID_CONSOLES
    valid = context.user_data.get("_bk_valid_consoles", set()) | set(VALID_CONSOLES)
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

    # ── Check for checked_in customers to optionally bind ─────────────────
    try:
        today = now_mmt().strftime("%Y-%m-%d")
        chk_raw = await _psvibe_get_async("bookings?status=checked_in&date=" + today) or []
        if isinstance(chk_raw, dict):
            chk_raw = chk_raw.get("bookings", chk_raw.get("data", []))
        if not isinstance(chk_raw, list):
            chk_raw = [chk_raw] if chk_raw else []

        from datetime import datetime as _dt
        pending_bks = [
            b for b in chk_raw if isinstance(b, dict)
            and b.get("status") == "checked_in"
            and b.get("date", "") == today
        ]
    except Exception as e:
        logger.error("step_book_console: checkin fetch %s", e, exc_info=True)
        pending_bks = []

    if pending_bks:
        kb_rows = [["⏭️ Bind မလုပ်ဘဲ ဆက်သွား"]]
        for b in pending_bks:
            bk_id   = b.get("id", "?")
            member  = b.get("customerName") or b.get("member_id") or b.get("memberId") or "Guest"
            bk_time = b.get("timeSlot") or ""
            game    = b.get("gameName") or ""
            label   = f"#{bk_id} | {member}"
            if bk_time:
                label += f" | {bk_time}"
            if game:
                label += f" | {game}"
            kb_rows.append([label])
        kb_rows.append([BTN_BACK, BTN_CANCEL])
        context.user_data["_bk_checkin_list"] = pending_bks

        await update.message.reply_text(
            f"🕹️ <b>{cid}</b> Console\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📋 Checked‑In Customer ရှိသည် — Bind လုပ်မည်လား?\n\n"
            "<i>Bind လုပ်လျှင် Member / Game autofill ဖြစ်မည်</i>\n"
            "မလိုဘဲ ဆက်သွားလျှင် ⏭️ နှိပ်ပါ",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
        )
        return BOOK_CHECKIN_BIND

    # No check-ins — continue to member selection
    members = await fetch_members_async()
    # Fetch member names for display labels (ID → Name map)
    member_names = {}
    try:
        raw = await _psvibe_get_async("fetch_members")
        if isinstance(raw, list):
            member_names = {m.get("id", ""): (m.get("name") or "").strip() for m in raw if isinstance(m, dict)}
    except Exception:
        pass
    kb = [["0 (Guest)"]] + \
         [[f"{m} — {member_names.get(m, '')}" if member_names.get(m) else m] for m in members] + \
         [[BTN_BACK, BTN_CANCEL]]
    await update.message.reply_text(
        f"🕹️ *{cid}* — session\n\n"
        "👤 Member ရွေးပါ (သို့) ရိုက်ရှာပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return BOOK_MEMBER

async def step_book_checkin_bind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle checked-in customer binding after console selection."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text in (BTN_BACK, BTN_BACK_MAIN):
        context.user_data.pop("_bk_checkin_list", None)
        return await prompt_book_console(update, context)
    if text == "⏭️ Bind မလုပ်ဘဲ ဆက်သွား":
        context.user_data.pop("_bk_checkin_list", None)
        # Continue to member selection (same as original step_book_console end)
        from bot import fetch_members_async
        members = await fetch_members_async()
        member_names = {}
        try:
            raw = await _psvibe_get_async("fetch_members")
            if isinstance(raw, list):
                member_names = {m.get("id", ""): (m.get("name") or "").strip() for m in raw if isinstance(m, dict)}
        except Exception:
            pass
        kb = [["0 (Guest)"]] + \
             [[f"{m} — {member_names.get(m, '')}" if member_names.get(m) else m] for m in members] + \
             [[BTN_BACK, BTN_CANCEL]]
        cid = context.user_data.get("bk_console", "")
        await update.message.reply_text(
            f"🕹️ *{cid}* — session\n\n"
            "👤 Member ရွေးပါ (သို့) ရိုက်ရှာပါ:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
        )
        return BOOK_MEMBER

    pending_bks = context.user_data.pop("_bk_checkin_list", [])
    selected_bk = None
    for b in pending_bks:
        bk_id = b.get("id", "?")
        if text.startswith(f"#{bk_id} "):
            selected_bk = b
            break

    if not selected_bk:
        await update.message.reply_text("⚠️ Keyboard မှ ရွေးပေးပါ")
        context.user_data["_bk_checkin_list"] = pending_bks
        return BOOK_CHECKIN_BIND

    bk_id   = selected_bk.get("id")
    member  = selected_bk.get("customerName") or selected_bk.get("member_id") or selected_bk.get("memberId") or "Guest"
    game    = selected_bk.get("gameName") or ""
    dur     = selected_bk.get("durationMins") or 0
    bk_console = (selected_bk.get("console_id") or selected_bk.get("consoleId") or "?").strip()
    cid = context.user_data.get("bk_console", "")

    # NOTE: Do NOT call PATCH bookings/{bk_id}/status here to set Active
    # The actual status transition (checked_in → Active) is handled by
    # _do_create_booking → POST sessions/start with linked_booking_id.
    # Doing both causes sessions/start to fail because the booking
    # is already Active and no longer checked_in.
    api_failed = False

    # 📱 Send confirmation notification to customer (best-effort)
    try:
        _tg_chat = (selected_bk.get("telegramChatId") or selected_bk.get("telegram_chat_id") or "").strip()
        if _tg_chat and CUSTOMER_BOT_TOKEN:
            _date = selected_bk.get("date") or selected_bk.get("booking_date", "") or ""
            _time = selected_bk.get("timeSlot") or selected_bk.get("start_time", "") or ""
            if _time and len(_time) > 5:
                _time = _time[11:16] if "T" in str(_time) else str(_time)[:5]
            _ctype = selected_bk.get("consoleType") or cid or ""
            _dur = selected_bk.get("durationMins") or 0
            _cust_msg = (
                "မင်္ဂလာပါ 🙏\n\n"
                f"သင်၏ Booking (#{bk_id}) Check-In ပြီးပါပြီ။\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🕹️ Console: {cid} ({_ctype})\n"
                f"📅 {_date}  ⏰ {_time}\n"
                f"⏱️ {_dur} mins\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"PS Vibe မှ ကြိုဆိုပါသည်! ✨\n"
                f"Play The Game. Share The VIBE!"
            )
            await asyncio.to_thread(_notify_customer, _tg_chat, _cust_msg)
            logger.info(f"checkin_bind: Customer notification sent for BK#{bk_id} to {_tg_chat}")
    except Exception as e:
        logger.warning(f"checkin_bind: Customer notify failed for #{bk_id}: {e}")

    if api_failed:
        await update.message.reply_text(
            f"⚠️ Booking #{bk_id} bind လုပ်ရန် API error ဖြစ်နေပါသည်။\n\n"
            f"Console <b>{cid}</b> အတွက် Member ကို ကိုယ်တိုင်ရွေးပါ။\n\n"
            f"<i>ဆက်သွားရန် Member တစ်ခုရွေးပါ</i>",
            parse_mode="HTML",
        )
        context.user_data["_bk_checkin_list"] = []
        # Fall through to member selection (same as skip logic)
        from bot import fetch_members_async
        members = await fetch_members_async()
        member_names = {}
        try:
            raw = await _psvibe_get_async("fetch_members")
            if isinstance(raw, list):
                member_names = {m.get("id", ""): (m.get("name") or "").strip() for m in raw if isinstance(m, dict)}
        except Exception:
            pass
        kb = [["0 (Guest)"]] + \
             [[f"{m} — {member_names.get(m, '')}" if member_names.get(m) else m] for m in members] + \
             [[BTN_BACK, BTN_CANCEL]]
        await update.message.reply_text(
            f"🕹️ *{cid}* — session\n\n"
            "👤 Member ရွေးပါ (သို့) ရိုက်ရှာပါ:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
        )
        return BOOK_MEMBER

    context.user_data["bk_member"]       = member
    context.user_data["bk_game"]         = game
    context.user_data["bk_planned_mins"] = int(dur) if dur else 0
    context.user_data["_bk_linked_id"]   = bk_id

    try:
        staff_list = fetch_staff()
        staff = staff_list[0] if len(staff_list) == 1 else context.user_data.get("staff_name", "")
    except Exception:
        staff = context.user_data.get("staff_name", "")
    context.user_data["bk_staff"] = staff

    await update.message.reply_text(
        f"✅ <b>Checked‑in #{bk_id} Bind လုပ်ပြီ!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕹️ Console : <b>{cid}</b>\n"
        f"👤 Member  : <b>{member}</b>\n"
        f"🎮 Game    : <b>{game or '—'}</b>\n"
        f"⏱️ Duration: <b>{dur or '—'} mins</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"အချက်အလက်များ autofill ဖြစ်ပြီ — ဆက်သွားမည်",
        parse_mode="HTML",
    )
    return await prompt_book_mins(update, context)

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
        # Fetch member names for search-result display
        member_names = {}
        try:
            raw = await _psvibe_get_async("fetch_members")
            if isinstance(raw, list):
                member_names = {m.get("id", ""): (m.get("name") or "").strip() for m in raw if isinstance(m, dict)}
        except Exception:
            pass
    except Exception as e:
        await update.message.reply_text(f"❌ Member list ဖတ်မရပါ: {e}\nထပ်ကြိုးစားပါ")
        return BOOK_MEMBER

    member_id = "Guest"

    # Strip " — Name" suffix from display label (e.g., "1 — PSV_A_001" → "1")
    _raw_text = text.split(" — ")[0].strip() if " — " in text else text

    if _raw_text == "0 (Guest)":
        member_id = "Guest"
    elif _raw_text in members:
        member_id = _raw_text
    else:
        # partial search against IDs AND names
        matches = [m for m in members if _raw_text.upper() in m.upper() or _raw_text.upper() in member_names.get(m, "").upper()]
        if len(matches) == 1:
            member_id = matches[0]
        elif matches:
            kb = [["0 (Guest)"]] + \
                 [[f"{m} — {member_names.get(m, '')}" if member_names.get(m) else m] for m in matches] + \
                 [[BTN_BACK, BTN_CANCEL]]
            await update.message.reply_text(
                f"🔍 <b>{len(matches)}</b> ကိုက်ညီသည် — ရွေးပါ:",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
            )
            return BOOK_MEMBER
        else:
            member_id = _raw_text  # allow free-text (walk-in not in sheet)

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
        ["420", "480"],
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
    MAX_SESSION_MINS = 1440  # 24 hours
    if text != BTN_SKIP_TIMER:
        try:
            planned_mins = int(text)
        except ValueError:
            await update.message.reply_text("⚠️ ဂဏန်းသာ ထည့်ပါ သို့ keyboard မှ ရွေးပါ")
            context.user_data["bk_member"] = member_id
            context.user_data["bk_staff"]  = staff
            return await prompt_book_mins(update, context)
        if planned_mins < 1:
            await update.message.reply_text(f"⚠️ အနည်းဆုံး ၁ မိနစ် ထည့်ပါ")
            context.user_data["bk_member"] = member_id
            context.user_data["bk_staff"]  = staff
            return await prompt_book_mins(update, context)
        if planned_mins > MAX_SESSION_MINS:
            await update.message.reply_text(f"⚠️ အများဆုံး {MAX_SESSION_MINS} မိနစ် (၂၄ နာရီ) သာ ခွင့်ပြုပါတယ်")
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
        # FIX 2.4: Use dedicated sessions/start endpoint
        payload = {
            "console_id": cid,
            "member_id": member_id,
            "game_name": game,
            "duration_mins": planned_mins if planned_mins > 0 else 0,
            "booking_date": now_mmt().strftime("%Y-%m-%d"),
        }
        # If linked to a checked-in booking, pass the ID to transition it to Active
        if _linked_cust_bk:
            payload["linked_booking_id"] = int(_linked_cust_bk)
        result = await _psvibe_post_async("sessions/start", payload)
        if not result or not result.get("booking_id"):
            err_msg = (result or {}).get("error", "") or str(result) or "API returned empty response"
            await update.message.reply_text(f"❌ Session start မအောင်မြင်ပါ: {err_msg}")
            logger.error("_do_create_booking: start-session failed: %s", result)
            return await show_console_menu(update, context)
        bk_id = result.get("booking_id")
        if not bk_id:
            await update.message.reply_text("❌ booking_id not returned from API")
            return await show_console_menu(update, context)
        linked = result.get("linked_booking", False)
        # H2: Show warning if pending/confirmed booking overlaps (staff walk-in)
        _warn = result.get("warning") or result.get("data", {}).get("warning", "")
        if _warn:
            await update.message.reply_text(
                f"{_warn}\n\n🟢 Session ဆက်လက်စတင်ပါမည် — customer နောက်ကျပါက ဤ console အားသုံးနိုင်ပါသည်",
                parse_mode="HTML",
            )
        logger.info("start-session success: booking_id=%s linked=%s", bk_id, linked)
    except Exception as e:
        await update.message.reply_text(f"❌ Session start မအောင်မြင်ပါ: {e}")
        logger.exception("_do_create_booking: %s", e)
        return await show_console_menu(update, context)
    # Store linked booking ID for session-end tracking
    if _linked_cust_bk or linked:
        context.user_data["_bk_linked_id"] = _linked_cust_bk or bk_id

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
    # Track No Timer sessions
    if planned_mins <= 5:
        add_no_timer_console(cid)
    else:
        remove_no_timer_console(cid)
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
                         planned_mins, end_t, delay_secs, getattr(update.effective_message, 'message_thread_id', 0) or STAFF_NOTIFY_THREAD)
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
