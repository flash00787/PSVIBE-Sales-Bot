"""
PS Vibe Customer Bot — Booking Conversation Handlers
All 16 states use ReplyKeyboardMarkup for selection.
InlineKeyboard is used only for dynamic member/game lists where ReplyKeyboard is impractical.

UPDATED: Added back buttons throughout + phone last-3-digit member matching
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from . import api as _api
from .handlers import (
    BK_MEMBER_CHECK, BK_MEMBER_SELECT, BK_PHONE_VERIFY, BK_DATA_CONFIRM,
    BK_NAME, BK_PHONE, BK_DATE, BK_TIME,
    BK_CONSOLE, BK_DURATION, BK_GAME, BK_CONSOLE_PREF, BK_CONFIRM,
    BK_DUP_WARN, BK_DISC_WARN, BK_CON_CONFLICT,
    BK_DEPOSIT_METHOD, BK_DEPOSIT_CONFIRM,
    BK_END, MAIN_MENU_KB, CONSOLE_TYPES, DURATION_OPTS,
    BTN_BOOK_ANYWAY, BTN_BOOK_GOBACK,
    BTN_DISC_GAME, BTN_DISC_TIME,
    _bk_intercept_menu,
)
from .data.prompts import today_mmt, OPEN_HOUR, CLOSE_HOUR
from .data.bank_accounts import DEPOSIT_ACCOUNTS, DEPOSIT_FEE_RATIO

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
TODAY = today_mmt
def _push_state(context, state):
    stack = context.user_data.setdefault("_bk_state_stack", [])
    stack.append(state)

def _pop_state(context):
    stack = context.user_data.get("_bk_state_stack", [])
    return stack.pop() if stack else None

def _get_previous_state(context):
    stack = context.user_data.get("_bk_state_stack", [])
    return stack[-1] if stack else None

BK_END = -1  # sentinel for end

BTN_CANCEL = "❌ ပယ်ဖျက်မည်"
BTN_BACK = "🔙 နောက်သို့"
BTN_MEM_YES = "ရှိပါတယ်"
BTN_MEM_NO = "မရှိဘူး (Guest)"
BTN_CONFIRM_YES = "✅ မှန်ပါသည်"
BTN_CONFIRM_NO = "❌ မဟုတ်ပါ"
BTN_NOT_SURE = "🏪 ဆိုင်ရောက်မှ ရွေးမယ်"
BTN_CONFIRM_BOOK = "✅ Confirm Booking"
BTN_SKIP = "⏭️ Skip"
BTN_TRY_AGAIN = "🔄 ထပ်ကြိုးစားမည်"
BTN_RETRY_BOOKING = "🔄 ပြန်ကြိုးစားမယ်"


async def _show_api_error_with_retry(update: Update, context, error_msg: str = "",
                                      retry_action: str = "retry_games") -> int:
    """Show API error with retry button. Returns BK_GAME or stays in current state."""
    user_msg = (
        "⚠️ စနစ်ခဏပြဿနာရှိနေပါတယ်။ ခဏနေပြီးမှ ပြန်ကြိုးစားပေးပါ။\n\n"
        f"{error_msg}"
    )
    kb = _rp_kb([[BTN_RETRY_BOOKING], [BTN_BACK, BTN_CANCEL]])
    # Store retry action in context so we know what to retry
    context.user_data["_bk_retry_action"] = retry_action

    if update.message:
        await update.message.reply_text(user_msg, reply_markup=kb)
    elif update.callback_query:
        await update.callback_query.edit_message_text(user_msg, reply_markup=kb)
        await update.callback_query.answer()
    return BK_GAME  # fallback state — go to game select for retry logic


async def _handle_retry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    """Handle retry button press. Returns next state or None if not a retry."""
    text = (update.message.text or "").strip() if update.message else ""
    if text != BTN_RETRY_BOOKING:
        return None  # not a retry

    action = context.user_data.get("_bk_retry_action", "")
    context.user_data.pop("_bk_retry_action", None)

    msg = update.message if update.message else (update.callback_query.message if update.callback_query else None)
    if msg:
        await msg.reply_text("ခဏစောင့်ပါ — ပြန်ကြိုးစားနေသည် ⏳")

    if action == "retry_games":
        try:
            games = await _api._fetch_games(context.user_data.get("bk_console", ""))
        except Exception:
            return await _show_api_error_with_retry(
                update, context,
                error_msg="Game list ပြန်ဆွဲမရသေးပါ။",
                retry_action="retry_games",
            )
        context.user_data["_bk_game_list"] = games
        context.user_data["_bk_game_page"] = 0
        if not games:
            return await _show_api_error_with_retry(
                update, context,
                error_msg="Game list ပြန်ဆွဲမရသေးပါ — data မရှိပါ။",
                retry_action="retry_games",
            )
        await msg.reply_text(
            f"🕹️ ဆော့မည့်ဂိမ်းရွေးပါ (Total: {len(games)} games):",
            reply_markup=_make_game_keyboard(games),
        )
        return BK_GAME

    elif action == "retry_slots":
        date_str = context.user_data.get("bk_date", "")
        try:
            free_slots = await _get_available_slots(date_str)
        except Exception:
            free_slots = []
        if not free_slots:
            return await _show_api_error_with_retry(
                update, context,
                error_msg="Time slots ပြန်စစ်မရသေးပါ။",
                retry_action="retry_slots",
            )
        await msg.reply_text(
            f"📅 *{date_str}* တွင် ရနိုင်သော အချိန်များ:\n"
            f"ရနိုင်သော slot — *{len(free_slots)} ခု*",
            parse_mode="Markdown",
            reply_markup=_make_time_keyboard(free_slots),
        )
        return BK_TIME

    # Unknown action — go back to start
    return await bk_member_check_entry(update, context)

# ── Helper: build one_time ReplyKeyboardMarkup ─────────────────────────────────

def _rp_kb(rows: list, one_time: bool = True) -> ReplyKeyboardMarkup:
    """Build a one-time ReplyKeyboardMarkup with resize."""
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=one_time)

# ── Reply Keyboard Builders ───────────────────────────────────────────────────

def _make_date_keyboard() -> ReplyKeyboardMarkup:
    """Build date selection reply keyboard: 7 days (Today + Tomorrow + 5 weekdays)."""
    today = datetime.strptime(today_mmt(), "%Y-%m-%d")
    BURMESE_DAYS = ["တနင်္လာ", "အင်္ဂါ", "ဗုဒ္ဓဟူး", "ကြာသပတေး", "သောကြာ", "စနေ", "တနင်္ဂနွေ"]
    DAY_LABELS = [
        "ယနေ့ (Today)",
        "မနက်ဖြန် (Tomorrow)",
    ]
    buttons = []
    for i in range(7):
        d = today + timedelta(days=i)
        if i < len(DAY_LABELS):
            prefix = DAY_LABELS[i]
        else:
            prefix = BURMESE_DAYS[d.weekday()]
        buttons.append([f"{prefix} - {d.strftime('%Y-%m-%d')}"])
    buttons.append([BTN_BACK, BTN_CANCEL])
    return _rp_kb(buttons)


def _make_time_keyboard(free_slots: list[str]) -> ReplyKeyboardMarkup:
    """Build time slot reply keyboard for available hours."""
    rows = []
    row = []
    for slot in free_slots[:12]:  # max 12 slots shown
        row.append(slot)
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(["✏️ Custom Time", BTN_BACK, BTN_CANCEL])
    return _rp_kb(rows)


def _make_console_keyboard() -> ReplyKeyboardMarkup:
    """Build console type selection reply keyboard."""
    return _rp_kb([
        CONSOLE_TYPES,
        [BTN_NOT_SURE],
        [BTN_BACK, BTN_CANCEL],
    ])


def _make_duration_keyboard(max_dur: int = 0) -> ReplyKeyboardMarkup:
    """Build duration selection reply keyboard. If max_dur is set, only show valid durations."""
    opts = DURATION_OPTS
    if max_dur > 0:
        opts = [d for d in DURATION_OPTS if int(d.split()[0]) <= max_dur]
        if not opts:
            opts = [f"{max_dur} mins"]  # Show max available
    return _rp_kb([
        opts[:2],
        opts[2:4],
        opts[4:],
        [BTN_BACK, BTN_CANCEL],
    ])


def _make_game_keyboard(games: list[str], page: int = 0, per_page: int = 6) -> ReplyKeyboardMarkup:
    """Build game selection reply keyboard with pagination."""
    start = page * per_page
    end = start + per_page
    page_games = games[start:end]
    rows = [[g[:50]] for g in page_games]
    nav_row = []
    if page > 0:
        nav_row.append("◀️ Previous")
    if end < len(games):
        nav_row.append("Next ▶️")
    if nav_row:
        rows.append(nav_row)
    rows = [[BTN_NOT_SURE]] + rows
    rows.append([BTN_BACK, BTN_CANCEL])
    return _rp_kb(rows)


def _make_confirm_keyboard() -> ReplyKeyboardMarkup:
    """Build confirmation reply keyboard."""
    return _rp_kb([
        [BTN_CONFIRM_BOOK],
        [BTN_BACK, BTN_CANCEL],
    ])


def _make_warning_keyboard() -> ReplyKeyboardMarkup:
    """Build warning reply keyboard with 'Continue Anyway' and 'Cancel'."""
    return _rp_kb([
        [BTN_BOOK_ANYWAY],
        [BTN_BOOK_GOBACK],
    ])


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_user_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    """Get user's phone from existing bookings or context."""
    uid = str(update.effective_user.id)
    phone = context.user_data.get("bk_phone")
    if not phone:
        phone = await _api._get_linked_phone(int(uid)) if uid.isdigit() else None
    return phone


async def _get_available_slots(date_str: str) -> list[str]:
    """Get available time slots for a given date.

    Uses time-range OVERLAP detection: a booking at 14:30 (60min) blocks the
    14:00 AND 15:00 hourly slots because 14:30-15:30 overlaps both windows.
    """
    try:
        bks = await _api._api_get(f"search-bookings?date={date_str}")
    except Exception:
        bks = []
    if isinstance(bks, dict) and "bookings" in bks:
        bks = bks["bookings"]
    if not isinstance(bks, list):
        bks = []

    # Parse active bookings into (console_id, start_min, end_min) tuples
    active_ranges = []
    for b in bks:
        if b.get("status", "").lower() in ("cancelled", "done", "rejected"):
            continue
        b_time = b.get("timeSlot", "")
        b_console = b.get("console_id", "") or b.get("consoleId", "")
        if not b_time:
            continue
        try:
            bh, bm = map(int, b_time.split(":"))
            b_start = bh * 60 + bm
            b_dur = int(b.get("durationMins") or b.get("duration_mins") or 60)
            b_end = b_start + b_dur
            active_ranges.append((b_console, b_start, b_end))
        except (ValueError, AttributeError):
            continue

    all_slots = [f"{h:02d}:00" for h in range(OPEN_HOUR, CLOSE_HOUR)]

    # Get total console count (with cache)
    try:
        all_consoles = await _api._fetch_consoles()
        total_consoles = len(all_consoles) if all_consoles else 10
    except Exception:
        total_consoles = 10

    # Check each hourly slot: only block when ALL consoles are busy
    available = []
    for slot in all_slots:
        try:
            sh, sm = map(int, slot.split(":"))
            slot_start = sh * 60 + sm
            slot_end = slot_start + 60
        except (ValueError, AttributeError):
            available.append(slot)
            continue

        # Count how many consoles are busy during this slot
        busy_consoles = set()
        for cid, bk_start, bk_end in active_ranges:
            if bk_start < slot_end and bk_end > slot_start:
                busy_consoles.add(cid)

        # Slot is available if at least 1 console is free
        if len(busy_consoles) < total_consoles:
            available.append(slot)

    # [FEATURE] Filter past time slots for today (MMT)
    try:
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        if date_str == today_str:
            now_mmt = datetime.utcnow() + timedelta(hours=6, minutes=30)
            grace = now_mmt + timedelta(minutes=30)
            cutoff = grace.hour * 60 + grace.minute
            available = [
                s for s in available
                if (int(s.split(":")[0]) * 60 + int(s.split(":")[1])) >= cutoff
            ]
    except Exception:
        pass

    return available




def _make_specific_console_keyboard(consoles):
    """Build ReplyKeyboard for specific console selection."""
    buttons = []
    # Auto Assign at the top
    buttons.append([BTN_AUTO_ASSIGN])
    row = []
    for console in consoles:
        cid = console.get("id", "")
        ctype = console.get("type", "")
        label = f"{cid} ({ctype})"
        row.append(label)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([BTN_BACK, BTN_CANCEL])
    return _rp_kb(buttons)


def _calc_session_end_minutes(console: dict) -> int | None:
    """Calculate when an Active session will end (in minutes from midnight).
    Returns None if data is missing."""
    start_str = console.get("start_time", "")  # HH:MM format
    if not start_str:
        # Try start_time_dt as fallback
        start_dt = console.get("start_time_dt", "")
        if start_dt:
            try:
                dt = datetime.strptime(str(start_dt)[:19], "%Y-%m-%d %H:%M:%S")
                return dt.hour * 60 + dt.minute
            except (ValueError, TypeError):
                pass
        return None
    try:
        h, m = map(int, str(start_str).split(":")[:2])
    except (ValueError, AttributeError, TypeError):
        return None
    dur = int(console.get("duration_mins") or 60)
    return h * 60 + m + dur


async def _get_available_consoles(date_str, time_str, duration_mins=60):
    """Fetch available consoles for a given date/time, filtering out busy ones.

    Two-level filter:
    1. Console real-time status (skip Active/Reserved consoles)
    2. Booking time-range overlap detection (skip consoles with conflicting bookings)
    """
    logger = logging.getLogger(__name__)
    logger.info("_get_available_consoles: date=%s time=%s dur=%s", date_str, time_str, duration_mins)
    try:
        consoles_raw = await _api._fetch_consoles()
        bks = await _api._api_get(f"search-bookings?date={date_str}")
    except Exception as e:
        logger.warning("_get_available_consoles: API fetch failed — %s", e)
        return []
    if not consoles_raw:
        return []
    logger.info("_get_available_consoles: raw bks type=%s", type(bks).__name__)
    if isinstance(bks, dict):
        logger.info("_get_available_consoles: bks keys=%s", list(bks.keys())[:10])
        if "bookings" in bks:
            bks = bks["bookings"]
    if not isinstance(bks, list):
        bks = []
    logger.info("_get_available_consoles: %d bookings to check", len(bks))

    # Parse target time range
    try:
        target_h, target_m = map(int, time_str.split(":"))
        target_start = target_h * 60 + target_m
        target_end = target_start + duration_mins
    except (ValueError, AttributeError):
        target_start = 0
        target_end = duration_mins

    # Build set of console IDs that have conflicting bookings
    conflicting = set()
    for b in bks:
        b_status = b.get("status", "").lower()
        if b_status in ("cancelled", "done", "rejected"):
            continue
        b_console = b.get("console_id", "") or b.get("consoleId", "")
        if not b_console:
            continue
        b_slot = b.get("timeSlot", "")
        if not b_slot:
            continue
        try:
            bh, bm = map(int, b_slot.split(":"))
            b_start = bh * 60 + bm
            # Use actual booking duration, fallback to 60 (not user's preference)
            b_dur = int(b.get("durationMins") or b.get("duration_mins") or 60)
            b_end = b_start + b_dur
            # Standard overlap: booking_start < target_end AND booking_end > target_start
            if b_start < target_end and b_end > target_start:
                conflicting.add(b_console)
        except (ValueError, AttributeError):
            continue

    # ── Today? Use live status as additional guard (session started manually, no booking record) ──
    _now_mmt = datetime.utcnow() + timedelta(hours=6, minutes=30)
    today_str = _now_mmt.strftime("%Y-%m-%d")
    is_today = (date_str == today_str)

    available = []
    for console in consoles_raw:
        cid = console.get("id", "")
        cstatus = console.get("status", "").lower()
        # ── Today? Check Active sessions — skip only if session won't end before target ──
        # For future dates, current live status is irrelevant — the booking overlap
        # check below (search-bookings) already catches any time conflicts.
        if is_today and cstatus == "active":
            # Check if Active session will end before the target booking time
            session_end = _calc_session_end_minutes(console)
            if session_end is None or session_end > target_start:
                continue  # Session overlaps with target time — skip
            # Session ends before target — console will be free, allow booking
        elif is_today and cstatus == "reserved":
            # Reserved is display-only — treat as available for booking
            pass
        if cid in conflicting:
            continue
        available.append(console)
    logger.info("_get_available_consoles: conflicting=%s available=%d consoles", conflicting, len(available))
    return available


async def _get_max_duration_for_console(date_str: str, time_str: str, console_id: str, max_dur: int = 480):
    """Calculate max available duration (in minutes) for a specific console at a time.
    Returns (max_dur_mins, next_booking_time) tuple — next_booking_time is "HH:MM" or empty.
    max_dur_mins = 0 if console is completely unavailable."""
    logger = logging.getLogger(__name__)
    try:
        consoles_raw = await _api._fetch_consoles()
        bks = await _api._api_get(f"search-bookings?date={date_str}")
    except Exception as e:
        logger.warning("_get_max_duration_for_console: API fetch failed — %s", e)
        return 0, ""

    if not consoles_raw:
        return 0, ""

    if isinstance(bks, dict):
        if "bookings" in bks:
            bks = bks["bookings"]
    if not isinstance(bks, list):
        bks = []

    # Check console real-time status
    console_found = None
    for c in consoles_raw:
        if c.get("id", "").upper() == console_id.upper():
            console_found = c
            break
    if not console_found:
        return 0, ""
    status = console_found.get("status", "").lower()
    if status not in ("free", "reserved"):
        return 0, ""  # Console is Active/Unavailable

    # Parse target time
    try:
        target_h, target_m = map(int, time_str.split(":"))
        target_start = target_h * 60 + target_m
    except (ValueError, AttributeError):
        return 0, ""

    # Build conflict intervals for this console only
    conflicts = []
    for b in bks:
        b_status = b.get("status", "").lower()
        if b_status in ("cancelled", "done", "rejected"):
            continue
        b_console = (b.get("console_id") or b.get("consoleId") or "").upper()
        if not b_console:
            continue
        if b_console == console_id.upper():
            try:
                t = b.get("start_time") or b.get("startTime") or b.get("timeSlot") or b.get("time_slot") or b.get("time", "")
                if isinstance(t, str) and len(t) >= 16:
                    t = t[11:16]  # Extract HH:MM from datetime string
                elif isinstance(t, str) and ":" in t:
                    t = t.split(":")[:2]
                    t = f"{int(t[0]):02d}:{int(t[1]):02d}"
                else:
                    continue
                bh, bm = map(int, t.split(":"))
                b_start = bh * 60 + bm
                b_dur = int(b.get("durationMins") or b.get("duration_mins") or b.get("duration", 60))
                b_end = b_start + b_dur
                conflicts.append((b_start, b_end))
            except (ValueError, AttributeError) as e:
                logger.warning("_get_max_duration: failed to parse booking %s — %s", b.get("id", "?"), e)
                continue

    # Sort conflicts by start time
    conflicts.sort()

    # Find the earliest conflict that overlaps with target_start
    next_conflict_start = target_start + max_dur  # default: max_dur available
    for c_start, c_end in conflicts:
        if c_start < target_start + 1 and c_end > target_start:
            # Overlapping — this booking blocks us
            next_conflict_start = c_start
            break
        elif c_start > target_start:
            # Future booking — we can only go up to this
            next_conflict_start = min(next_conflict_start, c_start)
            break

    if next_conflict_start <= target_start:
        return 0, ""  # Completely blocked

    max_mins = next_conflict_start - target_start
    nb_h = next_conflict_start // 60
    nb_m = next_conflict_start % 60
    next_time = f"{nb_h:02d}:{nb_m:02d}"
    return max_mins, next_time


def _get_next_available_times(consoles_raw, bookings, target_start_minutes, target_end_minutes, target_date=""):
    """Find when each console becomes available after a busy target slot.

    Returns list of {console_id, console_type, free_from (minutes), free_from_str (HH:MM)}.
    """
    # Build per-console booking intervals (confirmed, checked_in, Active, pending only)
    console_bookings = {}
    for b in bookings:
        b_status = b.get("status", "").lower()
        if b_status in ("cancelled", "done", "rejected"):
            continue
        b_console = b.get("console_id", "") or b.get("consoleId", "")
        if not b_console:
            continue
        b_slot = b.get("timeSlot", "")
        if not b_slot:
            continue
        try:
            bh, bm = map(int, b_slot.split(":"))
            b_start = bh * 60 + bm
            b_dur = int(b.get("durationMins") or b.get("duration_mins") or 60)
            b_end = b_start + b_dur
            console_bookings.setdefault(b_console, []).append((b_start, b_end))
        except (ValueError, AttributeError):
            continue

    # ── Live session detection for TODAY ──
    is_today = False
    now_mmt = datetime.utcnow() + timedelta(hours=6, minutes=30)
    if target_date:
        today_str = now_mmt.strftime("%Y-%m-%d")
        is_today = (target_date == today_str)

    if is_today:
        now_minutes = now_mmt.hour * 60 + now_mmt.minute
        for console in consoles_raw:
            c_status = (console.get("status") or "").lower()
            if c_status not in ("active", "reserved"):
                continue
            start_time = console.get("start_time")
            if not start_time:
                continue
            cid = console.get("id", "")
            if not cid:
                continue
            try:
                # Parse start_time (may be "2026-06-19T12:30:00" or "2026-06-19 12:30:00")
                st_str = str(start_time).replace(" ", "T")
                st_dt = datetime.fromisoformat(st_str)
                # start_time from console_status is already in MMT (local time)
                session_start = st_dt.hour * 60 + st_dt.minute

                # Check for a matching booking with the same console and overlapping time
                expected_end = None
                for b_start, b_end in console_bookings.get(cid, []):
                    if b_start <= session_start < b_end:
                        expected_end = b_end
                        break

                if expected_end is None:
                    # Walk-in: no matching booking, use default 60 min
                    expected_end = session_start + 60

                # If session is already over, skip it
                if now_minutes >= expected_end:
                    continue

                # Add to console_bookings (duplicate check: skip if identical interval exists)
                existing = console_bookings.get(cid, [])
                if (session_start, expected_end) not in existing:
                    console_bookings.setdefault(cid, []).append((session_start, expected_end))
                    logger.info(
                        "_get_next_available_times: live session console=%s start=%d end=%d now=%d walkin=%s",
                        cid, session_start, expected_end, now_minutes,
                        expected_end == session_start + 60
                    )
            except (ValueError, TypeError) as e:
                logger.warning("_get_next_available_times: failed to parse start_time for %s — %s", cid, e)
                continue

    # Sort each console's bookings by start time
    for cid in console_bookings:
        console_bookings[cid].sort(key=lambda x: x[0])

    gap_mins = target_end_minutes - target_start_minutes

    results = []
    for console in consoles_raw:
        cid = console.get("id", "")
        ctype = console.get("type", "")
        bk_list = console_bookings.get(cid, [])

        # Find earliest gap of at least gap_mins starting from target_start
        free_from = target_start_minutes

        if bk_list:
            # Push free_from past any overlapping bookings
            for bk_start, bk_end in bk_list:
                if bk_start < free_from + gap_mins and bk_end > free_from:
                    free_from = max(free_from, bk_end)
                elif bk_start >= free_from + gap_mins:
                    break

            # Final pass to catch any remaining overlaps after adjustments
            for bk_start, bk_end in bk_list:
                if bk_start < free_from + gap_mins and bk_end > free_from:
                    free_from = max(free_from, bk_end)

        hh = free_from // 60
        mm = free_from % 60
        free_from_str = f"{hh:02d}:{mm:02d}"

        results.append({
            "console_id": cid,
            "console_type": ctype,
            "free_from": free_from,
            "free_from_str": free_from_str,
        })

    # Sort by earliest available first
    results.sort(key=lambda x: x["free_from"])
    return results


def _format_booking_summary(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Format booking summary from user_data."""
    d = context.user_data
    lines = [
        "📋 *Booking Summary*",
        "━━━━━━━━━━━━━━━━━━",
        f"👤 Name: *{d.get('bk_name', '—')}*",
        f"📞 Phone: *{d.get('bk_phone', '—')}*",
        f"📅 Date: *{d.get('bk_date', '—')}*",
        f"⏰ Time: *{d.get('bk_time', '—')}*",
        f"🎮 Console: *{d.get('bk_console', '—')}*",
        f"⏱️ Duration: *{d.get('bk_duration_mins', '—')} mins*",
        f"🕹️ Game: *{d.get('bk_game', '—')}*",
    ]
    return "\n".join(lines)


def _extract_date_from_text(text: str) -> str | None:
    """Extract YYYY-MM-DD date from text like 'ယနေ့ (Today)  2026-05-30'."""
    m = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    return m.group(1) if m else None


async def _match_member_by_last_digits(last_digits: str) -> list[tuple[str, dict]]:
    """Match members by last N digits of phone number. Returns [(mid, member_dict), ...]"""
    if not last_digits or len(last_digits) < 2:
        return []
    members = await _api._fetch_members()
    matched = []
    for mid, m in members.items():
        phone = (m.get("phone") or "").replace(" ", "").replace("-", "")
        if phone.endswith(last_digits):
            matched.append((mid, m))
    return matched


async def _submit_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple[str, bool]:
    """Submit booking to API. Returns (message, success_or_not)."""
    user = update.effective_user
    uid = str(user.id) if user else ""

    # AUTO-ASSIGN: Pick first free console matching selected type
    console_id = context.user_data.get("bk_specific_console_id", "")
    console_type = context.user_data.get("bk_console") or context.user_data.get("bk_console_pref", "PS5")
    date_str = context.user_data.get("bk_date", "")
    time_str = context.user_data.get("bk_time", "")
    duration_mins = context.user_data.get("bk_duration_mins", 60)

    # FINAL AVAILABILITY CHECK: Always validate before submission
    if date_str and time_str:
        try:
            available = await _get_available_consoles(date_str, time_str, duration_mins)
            if console_type != "Any":
                available = [c for c in available if c.get("type", "").lower() == console_type.lower()]
            available_ids = {c.get("id", "") for c in available}
            if console_id:
                # Customer picked a specific console — validate it's still available
                if console_id not in available_ids:
                    # Calculate max available duration for this console
                    max_dur, next_booking = await _get_max_duration_for_console(date_str, time_str, console_id)
                    if max_dur > 0:
                        context.user_data["_bk_max_duration"] = max_dur
                        next_info = f"⏱️ {next_booking} မှာ Booking ရှိနေလို့ *{max_dur} min* ပဲ ရပါတော့မယ် ခင်ဗျ" if next_booking else f"⏱️ Max duration: *{max_dur} min* သာရပါမည်။"
                        return (
                            f"❌ Console {console_id} သည် {duration_mins} min အတွက် မရနိုင်ပါ။\n\n"
                            f"{next_info}\n"
                            f"Duration ပြန်ရွေးပါ 👇",
                            False,
                            True,  # go_back_to_duration=True
                        )
                    return (
                        f"❌ Console {console_id} သည် ထိုအချိန်တွင် မရနိုင်တော့ပါ။ ပြန်ရွေးပါ。",
                        False,
                        False,
                    )
            elif available:
                # Let API server auto-assign atomically (FOR UPDATE lock) — avoid race condition
                console_id = ""  # Server picks first free console in transaction
                context.user_data.pop("bk_specific_console_id", None)
            else:
                # No console available for this duration — find max possible duration
                # Pick any console of matching type to calculate max_dur
                max_dur = 0
                try:
                    all_consoles = await _api._fetch_consoles()
                    for c in all_consoles:
                        c_type = c.get("type", "")
                        c_status = c.get("status", "").lower()
                        if console_type == "Any" or c_type.lower() == console_type.lower():
                            if c_status in ("free", "reserved"):
                                cid = c.get("id", "")
                                if cid:
                                    max_dur, next_booking = await _get_max_duration_for_console(date_str, time_str, cid)
                                    if max_dur > 0:
                                        break  # First console with availability
                except Exception:
                    pass
                if max_dur > 0:
                    context.user_data["_bk_max_duration"] = max_dur
                    next_info = f"⏱️ {next_booking} မှာ Booking ရှိနေလို့ *{max_dur} min* ပဲ ရပါတော့မယ် ခင်ဗျ" if next_booking else f"⏱️ Max duration: *{max_dur} min* သာရပါမည်။"
                    return (
                        f"❌ {console_type} တွင် {duration_mins} min အတွက် console မရနိုင်ပါ။\n\n"
                        f"{next_info}\n"
                        f"Duration ပြန်ရွေးပါ 👇",
                        False,
                        True,  # go_back_to_duration
                    )
                # No console available at all — show generic error
                return (
                    f"❌ {console_type} တွင် ထိုအချိန်၌ console အားလုံး မရနိုင်ပါ。\n\n"
                    "အခြားအချိန် သို့မဟုတ် အခြား console အမျိုးအစားကို ထပ်ရွေးပါ။\n"
                    "🔄 /start — ပြန်ကြိုးစားရန်\n\n📲 Admin သို့ ဆက်သွယ်ရန်: https://t.me/psvibeofficial"
                ), False, False
        except Exception as e:
            logging.warning("_submit_booking: _get_available_consoles failed — %s", e)

    assigned_console_label = ""
    if console_id:
        assigned_console_label = f" ({console_id})"

    payload = {
        "customerName": context.user_data.get("bk_name", ""),
        "phone": context.user_data.get("bk_phone", ""),
        "date": date_str,
        "timeSlot": time_str,
        "consoleType": console_type,
        "console_id": console_id,
        "durationMins": duration_mins,
        "gameName": context.user_data.get("bk_game", ""),
        "telegramChatId": uid,
        "memberId": context.user_data.get("bk_member_id", ""),
        "username": user.username or "",
        "status": "pending",
    }
    try:
        result = await _api._api_post("bookings", payload)
        if result and isinstance(result, dict) and result.get("id"):
            bk_id = result["id"]
            context.user_data["_bk_last_id"] = bk_id
            _console_display = f"{payload['consoleType']}{assigned_console_label}"
            msg = (
                "မင်္ဂလာပါ 🙏\n\n"
                f"သင်၏ Booking (#{bk_id}) အား လက်ခံရရှိပါပြီ။\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                f"📅 {payload['date']}  ⏰ {payload['timeSlot']}\n"
                f"🕹️ Console: {_console_display}\n"
                f"⏱️ {payload['durationMins']} mins  🎮 {payload['gameName']}\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                f"💰 Deposit အာမခံငွေ 30% သွင်းရန်လိုအပ်ပါတယ်။\n"
                "⬇️ အောက်တွင် ဆက်လက်ဆောင်ရွက်ပါ။\n"
                "Play The Game. Share The VIBE!"
            )
            asyncio.create_task(_api.track_usage(user, "booking_created"))
            return msg, True, False
        else:
            err_msg = str(result) if result else "unknown"
            # Try to calculate max available duration
            max_dur = 0
            if console_id and date_str and time_str:
                try:
                    max_dur, next_booking = await _get_max_duration_for_console(date_str, time_str, console_id)
                except Exception:
                    pass
            if max_dur > 0 and max_dur < duration_mins:
                context.user_data["_bk_max_duration"] = max_dur
                next_info = f"⏱️ {next_booking} မှာ Booking ရှိနေလို့ *{max_dur} min* ပဲ ရပါတော့မယ် ခင်ဗျ" if next_booking else f"⏱️ Max duration: *{max_dur} min* သာရပါမည်။"
                return (
                    f"❌ Booking မအောင်မြင်ပါ\n"
                    f"Console {console_id} ({console_type}) သည် {duration_mins} min အတွက် မရနိုင်ပါ။\n\n"
                    f"{next_info}\n"
                    f"Duration ပြန်ရွေးပါ 👇"
                ), False, True
            return (
                "❌ Booking မအောင်မြင်ပါ\n"
                f"Console {console_id} ({console_type}) သည် ထိုအချိန်တွင် မရနိုင်ပါ။\n\n"
                "အခြားအချိန် သို့မဟုတ် အခြား console ကို ထပ်ရွေးပါ။\n"
                "🔄 /start — ပြန်ကြိုးစားရန်\n\n📲 Admin သို့ ဆက်သွယ်ရန်: https://t.me/psvibeofficial"
            ), False, False
    except ValueError as e:
        # API returned HTTP error (e.g., 409 Conflict) — treat as booking failure, not crash
        logger.warning("Booking API error (ValueError): %s", e)
        max_dur = 0
        # Try max_duration even for API errors
        if console_id and date_str and time_str:
            try:
                max_dur, next_booking = await _get_max_duration_for_console(date_str, time_str, console_id)
            except Exception:
                pass
        # If no console_id (auto-assign with empty available), try any matching console
        if max_dur <= 0 and not console_id and date_str and time_str and console_type:
            try:
                all_consoles = await _api._fetch_consoles()
                for c in all_consoles:
                    c_type = c.get("type", "")
                    c_status = c.get("status", "").lower()
                    if console_type == "Any" or c_type.lower() == console_type.lower():
                        if c_status in ("free", "reserved"):
                            dur, _nb = await _get_max_duration_for_console(date_str, time_str, c.get("id", ""))
                            if dur > max_dur:
                                max_dur = dur
                            if max_dur > 0:
                                break
            except Exception:
                pass
        if max_dur > 0 and max_dur < duration_mins:
            context.user_data["_bk_max_duration"] = max_dur
            next_info = f"⏱️ {next_booking} မှာ Booking ရှိနေလို့ *{max_dur} min* ပဲ ရပါတော့မယ် ခင်ဗျ" if next_booking else f"⏱️ Max duration: *{max_dur} min* သာရပါမည်။"
            return (
                f"❌ Booking မအောင်မြင်ပါ\n"
                f"{duration_mins} min အတွက် {console_type} console မရနိုင်ပါ။\n\n"
                f"{next_info}\n"
                f"Duration ပြန်ရွေးပါ 👇"
            ), False, True
        return "❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ\n📲 Admin သို့ ဆက်သွယ်ရန်: https://t.me/psvibeofficial", False, False
    except Exception as e:
        logger.error("Booking submission failed (unexpected): %s", e)
        return "❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ\n📲 Admin သို့ ဆက်သွယ်ရန်: https://t.me/psvibeofficial", False, False


async def _cleanup_and_end(update: Update, context: ContextTypes.DEFAULT_TYPE, msg: str = "❌ Booking ဖျက်လိုက်ပါပြီ"):
    """Clear user_data and send end message with main menu."""
    context.user_data.clear()
    if update.callback_query:
        await update.callback_query.edit_message_text(msg)
        await update.callback_query.message.reply_text("👋", reply_markup=MAIN_MENU_KB)
    elif update.message:
        await update.message.reply_text(msg, reply_markup=MAIN_MENU_KB)
    return ConversationHandler.END


def _get_previous_state(context) -> int | None:
    """Get the previous state from user_data stack, or None."""
    stack = context.user_data.get("_bk_state_stack", [])
    return stack[-1] if stack else None


def _push_state(context, state: int):
    """Push current state onto stack."""
    stack = context.user_data.setdefault("_bk_state_stack", [])
    stack.append(state)
    # Keep stack manageable (max 20)
    if len(stack) > 20:
        stack.pop()


def _pop_state(context) -> int | None:
    """Pop and return previous state."""
    stack = context.user_data.get("_bk_state_stack", [])
    if stack:
        return stack.pop()
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  Booking State Handlers
# ══════════════════════════════════════════════════════════════════════════════


# ── State 0: BK_MEMBER_CHECK — Ask if user has a member card ──────────────────

async def bk_member_check_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle member card Yes/No — entry point for booking flow."""
    asyncio.create_task(_api.track_usage(update.effective_user, "book_step_member_check", detail="Booking: member check"))
    text = (update.message.text or "").strip() if update.message else ""

    # Intercept menu buttons
    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

    # Handle ReplyKeyboard text
    if not update.callback_query and text in (BTN_MEM_YES, "ရှိပါတယ်"):
        return await _handle_member_yes_text(update, context)
    elif not update.callback_query and (text in (BTN_MEM_NO, "မရှိဘူး (Guest)", "မရှိဘူး") or text.lower() == "no"):
        context.user_data.pop("bk_member_id", None)
        context.user_data.pop("bk_member_data", None)
        _push_state(context, BK_MEMBER_CHECK)
        await update.message.reply_text("👤 နာမည်ရိုက်ထည့်ပေးပါ:")
        return BK_NAME
    elif not update.callback_query and text == BTN_CANCEL:
        return await _cleanup_and_end(update, context)

    # Handle callback (existing inline path - keep for safety)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data == "bk_mem:yes":
            return await _handle_member_yes_text(update, context)
        elif data == "bk_mem:no":
            context.user_data.pop("bk_member_id", None)
            context.user_data.pop("bk_member_data", None)
            _push_state(context, BK_MEMBER_CHECK)
            await query.edit_message_text("👤 နာမည်ရိုက်ထည့်ပေးပါ:")
            return BK_NAME
        else:
            await query.edit_message_text("❌ Invalid option — please try again.")
            return ConversationHandler.END

    return BK_MEMBER_CHECK


async def _handle_member_yes_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User has a member card — always ask for last 3 digits of phone."""
    _push_state(context, BK_MEMBER_CHECK)
    msg = (
        "မင်္ဂလာပါ! 🎮\n\n"
        "ကျေးဇူးပြုပြီး သင့် **ဖုန်းနံပါတ်နောက်ဆုံး ၃ လုံး** ကို ရိုက်ထည့်ပေးပါ။\n"
        "(ဥပမာ: ဖုန်းနံပါတ် 09-xxx-xxx-**123** → `123` ရိုက်ပါ)\n\n"
        "Member မဟုတ်ရင် `no` ရိုက်ပြီး Guest အဖြစ်ဆက်လုပ်ပါ။"
    )
    msg_source = update.message if update.message else (update.callback_query.message if update.callback_query else None)
    kb = ReplyKeyboardMarkup(
        [["no (Guest)"], [BTN_BACK, BTN_CANCEL]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    if msg_source:
        if update.message:
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=kb)
        elif update.callback_query:
            await update.callback_query.edit_message_text(msg, parse_mode="Markdown")
            await update.callback_query.message.reply_text(msg, parse_mode="Markdown", reply_markup=kb)
    return BK_PHONE_VERIFY


# ── State 1: BK_MEMBER_SELECT — Select a member ──────────────────────────────

async def bk_member_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle member selection when multiple matches found."""
    text = (update.message.text or "").strip() if update.message else ""

    # Check for menu buttons
    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

    # Handle back/cancel
    if not update.callback_query:
        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)
        if text == BTN_BACK:
            _pop_state(context)
            return await bk_member_check_entry(update, context)

    # Handle callback (existing inline path)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""
        if data.startswith("bk_sel:"):
            mid = data.split(":", 1)[1]
            if mid == "none":
                _push_state(context, BK_MEMBER_SELECT)
                await query.edit_message_text("👤 နာမည်ရိုက်ထည့်ပေးပါ:")
                return BK_NAME
            return await _lookup_and_confirm_member(update, context, mid)

    # Text input
    NO_MEMBER_TEXTS = {"မရှိပါ", "မရှိဘူး", "မရှိဘူး (Guest)", "Guest"}
    if text.lower() == "no" or text in NO_MEMBER_TEXTS or text.lower() in {t.lower() for t in NO_MEMBER_TEXTS}:
        _push_state(context, BK_MEMBER_SELECT)
        await update.message.reply_text("👤 နာမည်ရိုက်ထည့်ပေးပါ:")
        return BK_NAME

    if text:
        members = await _api._fetch_members()
        m = members.get(text.lower())
        if m:
            return await _lookup_and_confirm_member(update, context, text)
        else:
            await update.message.reply_text(
                f"❌ Member ID `{text}` မတွေ့ပါ\n"
                "ထပ်ကြိုးစားပါ — သို့မဟုတ် 'no' ဟုရိုက်ပြီး member မရှိဘဲ ဆက်လုပ်ပါ",
                parse_mode="Markdown",
            )
            return BK_MEMBER_SELECT

    return BK_MEMBER_SELECT


async def _lookup_and_confirm_member(update: Update, context: ContextTypes.DEFAULT_TYPE, mid: str):
    """Look up member by ID and show confirmation."""
    members = await _api._fetch_members()
    m = members.get(mid)
    if not m:
        msg = "❌ Member မတွေ့ပါ — နာမည်ရိုက်ထည့်ပါ:"
        if update.message:
            await update.message.reply_text(msg)
        elif update.callback_query:
            await update.callback_query.edit_message_text(msg)
        return BK_NAME

    context.user_data["bk_member_id"] = mid
    context.user_data["bk_phone"] = m.get("phone", "")
    context.user_data["bk_member_data"] = m
    _name = m.get("name", "") or ""
    phone = m.get("phone", "")
    masked = phone[-4:] if len(phone) >= 4 else phone
    if not _name.strip():
        # Member has no name → force manual entry
        _push_state(context, BK_MEMBER_SELECT)
        msg = (
            f'⚠️ *Member ရှိပါသည်* သို့သော် "နာမည်" မထည့်ထားပါ။\n'
            f"📞 ဖုန်းနံပါတ် နောက်ဆုံး ၄ လုံး: *...{masked}*\n\n"
            f"👤 နာမည် ရိုက်ထည့်ပေးပါ:"
        )
        if update.message:
            await update.message.reply_text(msg, parse_mode="Markdown")
        elif update.callback_query:
            await update.callback_query.edit_message_text(msg, parse_mode="Markdown")
        return BK_NAME
    context.user_data["bk_name"] = _name
    _push_state(context, BK_MEMBER_SELECT)
    msg = (
        f"👤 *{_name}*\n"
        f"📞 ဖုန်းနံပါတ် နောက်ဆုံး ၄ လုံး: *...{masked}*\n\n"
        f"မှန်ကန်ပါက ✅ နှိပ်ပါ — သို့မဟုတ် ဖုန်းနံပါတ် အပြည့် ရိုက်ထည့်ပါ"
    )
    kb = _rp_kb([[BTN_CONFIRM_YES, BTN_CONFIRM_NO], [BTN_BACK, BTN_CANCEL]])
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=kb)
    elif update.callback_query:
        await update.callback_query.edit_message_text(msg, parse_mode="Markdown", reply_markup=kb)
    return BK_DATA_CONFIRM


# ── State 2: BK_PHONE_VERIFY — Verify phone last-3-digits ────────────────────

async def bk_phone_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Match last-3-digits against all members' phone numbers."""
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == BTN_CANCEL:
        return await _cleanup_and_end(update, context)

    if text == BTN_BACK:
        _pop_state(context)
        return await bk_member_check_entry(update, context)

    # Allow skip to manual entry
    NO_MEMBER_TEXTS = {"မရှိပါ", "မရှိဘူး", "မရှိဘူး (Guest)", "Guest"}
    if text.lower() == "no" or text in NO_MEMBER_TEXTS or text.lower() in {t.lower() for t in NO_MEMBER_TEXTS}:
        _push_state(context, BK_PHONE_VERIFY)
        await update.message.reply_text("👤 နာမည်အမှန် ရိုက်ထည့်ပေးပါ:")
        context.user_data.pop("bk_member_id", None)
        context.user_data.pop("bk_member_data", None)
        return BK_NAME

    # Clean input - extract only digits
    digits_only = re.sub(r'\D', '', text)

    # Validate: must be at least 2 digits
    if len(digits_only) < 2 or len(digits_only) > 6:
        kb = ReplyKeyboardMarkup(
            [["no (Guest)"], [BTN_BACK, BTN_CANCEL]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(
            "⚠️ ဖုန်းနံပါတ်နောက်ဆုံး **၃ လုံး** ကိုသာ ရိုက်ထည့်ပေးပါ။\n\n"
            "(ဥပမာ: `123`)  သို့မဟုတ် member မဟုတ်ရင် `no` ရိုက်ပါ။",
            parse_mode="Markdown",
            reply_markup=kb,
        )
        return BK_PHONE_VERIFY

    # Match against all members by last digits
    matched = await _match_member_by_last_digits(digits_only)

    if len(matched) == 1:
        # Single match — auto-fill and confirm
        mid, m = matched[0]
        context.user_data["bk_member_id"] = mid
        context.user_data["bk_phone"] = m.get("phone", "")
        context.user_data["bk_member_data"] = m
        _name = m.get("name", "") or ""
        phone = m.get("phone", "")
        masked = phone[-4:] if len(phone) >= 4 else phone
        balance = m.get("wallet_mins", m.get("balance_mins", m.get("balance", "N/A")))
        balance_warn = ""
        if isinstance(balance, (int, float)) and balance <= 0:
            balance_warn = "\n⚠️ *Balance မရှိပါ — Top Up လုပ်ရန်လိုပါမည်*"
        elif str(balance).strip() in ("0", "0.0", "N/A", ""):
            balance_warn = "\n⚠️ *Balance အချက်အလက် မရှိပါ — Top Up လုပ်ရန်လိုပါမည်*"

        if not _name.strip():
            # Member has no name → force manual entry
            _push_state(context, BK_PHONE_VERIFY)
            msg = (
                f"✅ *Member တွေ့ရှိပါသည်!*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📞 ဖုန်း: ...{masked}\n"
                f"💰 Balance: *{balance} mins*"
                f"{balance_warn}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ Member ရှိသော်လည်း \"နာမည်\" မထည့်ထားပါ။\n"
                f"👤 နာမည် ရိုက်ထည့်ပေးပါ:"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
            return BK_NAME
        context.user_data["bk_name"] = _name

        _push_state(context, BK_PHONE_VERIFY)
        msg = (
            f"✅ *Member တွေ့ရှိပါသည်!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 အမည်: *{_name}*\n"
            f"📞 ဖုန်း: ...{masked}\n"
            f"💰 Balance: *{balance} mins*"
            f"{balance_warn}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"မှန်ကန်ပါက ✅ မှန်ပါသည် ကိုနှိပ်ပါ။\n"
            f"မဟုတ်ပါက ❌ မဟုတ်ပါ ကိုနှိပ်ပြီး ကိုယ်တိုင်ရိုက်ထည့်ပါ။"
        )
        kb = _rp_kb([[BTN_CONFIRM_YES, BTN_CONFIRM_NO], [BTN_BACK, BTN_CANCEL]])
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=kb)
        return BK_DATA_CONFIRM

    elif len(matched) > 1:
        # Multiple matches — show list
        buttons = []
        for mid, m in matched[:10]:
            label = f"{m.get('name','?')} (...{m.get('phone','')[-4:]})"
            buttons.append([InlineKeyboardButton(label, callback_data=f"bk_sel:{mid}")])
        buttons.append([InlineKeyboardButton("❌ ကျွန်တော်မဟုတ်ပါ", callback_data="bk_sel:none")])

        msg = (
            f"👥 ဖုန်းနောက်ဆုံး `{digits_only}` နဲ့ကိုက်တဲ့ member *{len(matched)} ယောက်* တွေ့ပါသည်။\n\n"
            "ကျေးဇူးပြုပြီး သင့် profile ကို ရွေးချယ်ပါ:"
        )
        await update.message.reply_text(
            msg, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return BK_MEMBER_SELECT

    else:
        # No match
        kb = ReplyKeyboardMarkup(
            [["no (Guest)"], [BTN_BACK, BTN_CANCEL]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(
            f"❌ ဖုန်းနောက်ဆုံး `{digits_only}` နဲ့ကိုက်တဲ့ member မတွေ့ပါ။\n\n"
            "ထပ်ကြိုးစားလိုပါက နောက်ထပ် ၃ လုံးရိုက်ပါ၊\n"
            "Member မဟုတ်ရင် `no` ရိုက်ပြီး Guest အဖြစ်ဆက်လုပ်ပါ။",
            parse_mode="Markdown",
            reply_markup=kb,
        )
        return BK_PHONE_VERIFY


# ── State 3: BK_DATA_CONFIRM — Confirm member data ──────────────────────────

async def bk_data_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm member data or go to manual name entry."""
    text = (update.message.text or "").strip() if update.message else ""

    # Handle ReplyKeyboard text
    if not update.callback_query:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        if text == BTN_BACK:
            prev = _pop_state(context)
            # Go back to phone verify
            return await _handle_member_yes_text(update, context)

        if text in (BTN_CONFIRM_YES, "✅ မှန်ပါသည်"):
            # Keep member data, proceed to date selection
            _push_state(context, BK_DATA_CONFIRM)
            await update.message.reply_text(
                "📅 ဘိုကင်လုပ်မည့် ရက်ရွေးပါ:",
                reply_markup=_make_date_keyboard(),
            )
            return BK_DATE

        elif text in (BTN_CONFIRM_NO, "❌ မဟုတ်ပါ"):
            context.user_data.pop("bk_member_id", None)
            context.user_data.pop("bk_member_data", None)
            _push_state(context, BK_DATA_CONFIRM)
            await update.message.reply_text("👤 နာမည်အမှန် ရိုက်ထည့်ပေးပါ:")
            return BK_NAME

        return BK_DATA_CONFIRM

    # Callback path (keep for safety)
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_dc:yes":
        _push_state(context, BK_DATA_CONFIRM)
        await query.edit_message_text("📅 ဘိုကင်လုပ်မည့် ရက်ရွေးပါ:")
        await query.message.reply_text(
            "📅 ဘယ်ရက်မှာ လာဆော့မလဲ?",
            reply_markup=_make_date_keyboard(),
        )
        return BK_DATE
    elif data == "bk_dc:no":
        context.user_data.pop("bk_member_id", None)
        context.user_data.pop("bk_member_data", None)
        _push_state(context, BK_DATA_CONFIRM)
        await query.edit_message_text("👤 နာမည်အမှန် ရိုက်ထည့်ပေးပါ:")
        return BK_NAME
    else:
        await query.edit_message_text("❌ Invalid option.")
        return ConversationHandler.END


# ── State 4: BK_NAME — Enter customer name ──────────────────────────────────

async def bk_name_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store customer name and ask for phone."""
    asyncio.create_task(_api.track_usage(update.effective_user, "book_step_name", detail="Booking: name entry"))
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == BTN_CANCEL:
        return await _cleanup_and_end(update, context)

    if text == BTN_BACK:
        prev = _pop_state(context)
        if prev == BK_PHONE_VERIFY:
            return await _handle_member_yes_text(update, context)
        return await bk_member_check_entry(update, context)

    if not text or len(text) < 1:
        await update.message.reply_text("နာမည် ထည့်ပေးပါ:")
        return BK_NAME

    context.user_data["bk_name"] = text
    _push_state(context, BK_NAME)
    await update.message.reply_text(
        f"👤 နာမည်: *{text}*\n\n📞 ဖုန်းနံပါတ် ရိုက်ထည့်ပေးပါ:",
        parse_mode="Markdown",
    )
    return BK_PHONE


# ── State 5: BK_PHONE — Enter phone number ─────────────────────────────────

async def bk_phone_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store phone number and proceed to date selection."""
    asyncio.create_task(_api.track_usage(update.effective_user, "book_step_phone", detail="Booking: phone entry"))
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == BTN_CANCEL:
        return await _cleanup_and_end(update, context)

    if text == BTN_BACK:
        _pop_state(context)
        _push_state(context, BK_PHONE)
        await update.message.reply_text("👤 နာမည်ရိုက်ထည့်ပေးပါ:")
        return BK_NAME

    if not text:
        await update.message.reply_text("ဖုန်းနံပါတ် ထည့်ပေးပါ:")
        return BK_PHONE

    cleaned = re.sub(r'[^\d+]', '', text)
    if len(cleaned) < 7:
        await update.message.reply_text(
            "⚠️ ဖုန်းနံပါတ် မှန်ကန်ပုံမရပါ — ထပ်ရိုက်ပေးပါ:"
        )
        return BK_PHONE
    # Myanmar phone validation: must start with 09 or +959, 9-11 digits
    mm_phone = re.sub(r'[\s\-]', '', text)
    if mm_phone.startswith('+959'):
        mm_phone = '09' + mm_phone[4:]
    if not re.match(r'^09\d{7,9}$', mm_phone):
        await update.message.reply_text(
            "⚠️ မြန်မာဖုန်းနံပါတ် (09xxxxxxxxx) မှန်ကန်စွာ ထည့်ပါ\n"
            "ဥပမာ: 09773355915"
        )
        return BK_PHONE

    context.user_data["bk_phone"] = text
    _push_state(context, BK_PHONE)
    await update.message.reply_text(
        f"📞 ဖုန်း: *{text}*\n\n📅 ဘိုကင်လုပ်မည့် ရက်ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=_make_date_keyboard(),
    )
    return BK_DATE


# ── State 6: BK_DATE — Select booking date ─────────────────────────────────

async def bk_date_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date selection — works with ReplyKeyboard text and inline callback."""
    asyncio.create_task(_api.track_usage(update.effective_user, "book_step_date", detail="Booking: date selection"))
    text = (update.message.text or "").strip() if update.message else ""

    # Handle ReplyKeyboard text
    if not update.callback_query:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        if text == BTN_BACK:
            prev = _pop_state(context)
            # Check which state to go back to
            if context.user_data.get("bk_member_data") or context.user_data.get("bk_member_id"):
                # Came from member flow → go back to data confirm
                await _show_data_confirm(update, context)
                return BK_DATA_CONFIRM
            if context.user_data.get("bk_phone") and context.user_data.get("bk_name"):
                # Manual flow with phone → go back to phone
                await update.message.reply_text("📞 ဖုန်းနံပါတ် ရိုက်ထည့်ပေးပါ:")
                return BK_PHONE
            # Go all the way back to member check
            return await bk_member_check_entry(update, context)

        # Try to extract date from text like "ယနေ့ (Today)  2026-05-30"
        date_str = _extract_date_from_text(text)
        if not date_str:
            await update.message.reply_text(
                "📅 ကျေးဇူးပြုပြီး ရက်စွဲကို ရွေးချယ်ပါ:",
                reply_markup=_make_date_keyboard(),
            )
            return BK_DATE

        context.user_data["bk_date"] = date_str
        _push_state(context, BK_DATE)
        await update.message.reply_text("⏳ Available slots စစ်ဆေးနေသည်...")
        try:
            free_slots = await _get_available_slots(date_str)
        except Exception:
            free_slots = []

        if not free_slots:
            await update.message.reply_text(
                f"😔 *{date_str}* တွင် slot အားလုံး ပြည့်နေပါပြီ\n\n"
                "အခြားရက်ကို ရွေးပေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_date_keyboard(),
            )
            return BK_DATE

        await update.message.reply_text(
            f"📅 *{date_str}* တွင် ရနိုင်သော အချိန်များ:\n"
            f"ရနိုင်သော slot — *{len(free_slots)} ခု*",
            parse_mode="Markdown",
            reply_markup=_make_time_keyboard(free_slots),
        )
        return BK_TIME

    # Callback path (keep for safety)
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bkdate:cancel":
        return await _cleanup_and_end(update, context)

    if data.startswith("bkdate:"):
        date_str = data.split(":", 1)[1]
        context.user_data["bk_date"] = date_str

        await query.edit_message_text("⏳ Available slots စစ်ဆေးနေသည်...")
        try:
            free_slots = await _get_available_slots(date_str)
        except Exception:
            free_slots = []

        if not free_slots:
            await query.edit_message_text(
                f"😔 *{date_str}* တွင် slot အားလုံး ပြည့်နေပါပြီ\n\n"
                "အခြားရက်ကို ရွေးပေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_date_keyboard(),
            )
            return BK_DATE

        await query.edit_message_text(
            f"📅 *{date_str}* တွင် ရနိုင်သော အချိန်များ:\n"
            f"ရနိုင်သော slot — *{len(free_slots)} ခု*",
            parse_mode="Markdown",
            reply_markup=_make_time_keyboard(free_slots),
        )
        return BK_TIME

    await query.edit_message_text("❌ Invalid date selection.")
    return BK_DATE


async def _show_data_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show member data confirmation message."""
    m = context.user_data.get("bk_member_data", {})
    name = m.get("name", context.user_data.get("bk_name", "?"))
    phone = m.get("phone", context.user_data.get("bk_phone", "?"))
    balance = m.get("balance_mins", m.get("balance", "N/A"))
    masked = phone[-4:] if len(phone) >= 4 else phone
    msg = (
        f"👤 *{name}*\n"
        f"📞 ...{masked} | 💰 *{balance} mins*\n\n"
        "မှန်ကန်ပါက ✅ နှိပ်ပါ၊ မဟုတ်ပါက ❌ နှိပ်ပြီး ကိုယ်တိုင်ရိုက်ထည့်ပါ။"
    )
    kb = _rp_kb([[BTN_CONFIRM_YES, BTN_CONFIRM_NO], [BTN_BACK, BTN_CANCEL]])
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=kb)
    elif update.callback_query:
        await update.callback_query.edit_message_text(msg, parse_mode="Markdown", reply_markup=kb)


# ── State 7: BK_TIME — Select time slot ────────────────────────────────────

async def bk_time_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time slot selection — works with ReplyKeyboard text and inline callback."""
    asyncio.create_task(_api.track_usage(update.effective_user, "book_step_time", detail="Booking: time selection"))
    text = (update.message.text or "").strip() if update.message else ""

    # Handle ReplyKeyboard text
    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        # Handle retry button
        if text == BTN_RETRY_BOOKING:
            retry_result = await _handle_retry(update, context)
            if retry_result is not None:
                return retry_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        if text == BTN_BACK:
            _pop_state(context)
            await update.message.reply_text(
                "📅 ဘိုကင်လုပ်မည့် ရက်ရွေးပါ:",
                reply_markup=_make_date_keyboard(),
            )
            return BK_DATE

        if text == "✏️ Custom Time":
            await update.message.reply_text(
                "✏️ လိုချင်သော အချိန်ကို HH:MM format ဖြင့် ရိုက်ထည့်ပါ\n"
                "(ဥပမာ: 14:30, 10:00)\n\n"
                f"⏰ Operating hours: {OPEN_HOUR}:00 - {CLOSE_HOUR}:00",
            )
            return BK_TIME

        # Check if it's a valid time slot (HH:00 format)
        m_hour = re.match(r'^(\d{2}):00$', text)
        if m_hour:
            hour = int(m_hour.group(1))
            if OPEN_HOUR <= hour < CLOSE_HOUR:
                context.user_data["bk_time"] = text
                _push_state(context, BK_TIME)
                await update.message.reply_text(
                    f"⏰ အချိန်: *{text}*\n\n🎮 Console အမျိုးအစား ရွေးပါ:",
                    parse_mode="Markdown",
                    reply_markup=_make_console_keyboard(),
                )
                return BK_CONSOLE

        # Check custom time HH:MM — validate availability before accepting
        m = re.match(r'^(\d{1,2}):(\d{2})$', text)
        if m:
            hour, minute = int(m.group(1)), int(m.group(2))
            if OPEN_HOUR <= hour < CLOSE_HOUR and 0 <= minute <= 59:
                time_str = f"{hour:02d}:{minute:02d}"

                # Validate custom time against existing bookings
                date_str = context.user_data.get("bk_date", "")
                if date_str:
                    try:
                        bks = await _api._api_get(f"search-bookings?date={date_str}")
                        if isinstance(bks, dict) and "bookings" in bks:
                            bks = bks["bookings"]
                        if not isinstance(bks, list):
                            bks = []
                        dur = context.user_data.get("bk_duration_mins", 60)
                        req_start = hour * 60 + minute
                        req_end = req_start + dur
                        blocked = False
                        for b in bks:
                            if b.get("status", "").lower() in ("cancelled", "done"):
                                continue
                            b_slot = b.get("timeSlot", "")
                            if not b_slot:
                                continue
                            try:
                                bh, bm = map(int, b_slot.split(":"))
                                b_start = bh * 60 + bm
                                b_dur = int(b.get("durationMins") or b.get("duration_mins") or 60)
                                b_end = b_start + b_dur
                                if b_start < req_end and b_end > req_start:
                                    blocked = True
                                    break
                            except (ValueError, AttributeError):
                                continue
                        if blocked:
                            free_slots = await _get_available_slots(date_str)
                            slot_list = ", ".join(free_slots[:6]) if free_slots else "မရှိပါ"
                            await update.message.reply_text(
                                f"⚠️ *{time_str}* အချိန်တွင် booking ရှိပြီးသားပါ။\n\n"
                                f"ရနိုင်သော slot များ: {slot_list}\n"
                                f"အခြားအချိန်ရွေးပါ သို့မဟုတ် HH:MM ထပ်ရိုက်ပါ:",
                                parse_mode="Markdown",
                            )
                            return BK_TIME
                    except Exception:
                        pass  # If validation fails, allow proceeding (API will catch)

                context.user_data["bk_time"] = time_str
                _push_state(context, BK_TIME)
                await update.message.reply_text(
                    f"⏰ Custom Time: *{time_str}*\n\n🎮 Console အမျိုးအစား ရွေးပါ:",
                    parse_mode="Markdown",
                    reply_markup=_make_console_keyboard(),
                )
                return BK_CONSOLE
            else:
                await update.message.reply_text(
                    f"⚠️ မမှန်ကန်သော အချိန် — {OPEN_HOUR}:00 မှ {CLOSE_HOUR}:00 အတွင်း "
                    "HH:MM format ဖြင့် ထည့်ပေးပါ",
                )
                return BK_TIME
        else:
            date_str = context.user_data.get("bk_date", "")
            free_slots = await _get_available_slots(date_str) if date_str else []
            await update.message.reply_text(
                "⚠️ ကျေးဇူးပြုပြီး အချိန်ကို ရွေးချယ်ပါ (သို့မဟုတ် HH:MM format ဖြင့် ရိုက်ထည့်ပါ):",
                reply_markup=_make_time_keyboard(free_slots) if free_slots else _make_date_keyboard(),
            )
            return BK_TIME

    # Callback path (keep for safety)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data == "bktime:cancel":
            return await _cleanup_and_end(update, context)

        if data.startswith("bktime:"):
            time_str = data.split(":", 1)[1]
            context.user_data["bk_time"] = time_str
            await query.edit_message_text(
                f"⏰ အချိန်: *{time_str}*\n\n🎮 Console အမျိုးအစား ရွေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_console_keyboard(),
            )
            return BK_CONSOLE

        if data == "bk_custom:ask":
            await query.edit_message_text(
                "✏️ လိုချင်သော အချိန်ကို HH:MM format ဖြင့် ရိုက်ထည့်ပါ\n"
                "(ဥပမာ: 14:30, 10:00)\n\n"
                f"⏰ Operating hours: {OPEN_HOUR}:00 - {CLOSE_HOUR}:00",
            )
            return BK_TIME

        await query.edit_message_text("❌ Invalid time selection.")
        return BK_TIME

    return BK_TIME


# ── State 8: BK_CONSOLE — Select console type ──────────────────────────────

async def bk_console_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle console type selection."""
    asyncio.create_task(_api.track_usage(update.effective_user, "book_step_console", detail="Booking: console selection"))
    text = (update.message.text or "").strip() if update.message else ""

    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        # Handle retry button
        if text == BTN_RETRY_BOOKING:
            retry_result = await _handle_retry(update, context)
            if retry_result is not None:
                return retry_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        if text == BTN_BACK:
            _pop_state(context)
            date_str = context.user_data.get("bk_date", "")
            free_slots = await _get_available_slots(date_str) if date_str else []
            await update.message.reply_text(
                f"📅 *{date_str}* — အချိန်ရွေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_time_keyboard(free_slots) if free_slots else _make_date_keyboard(),
            )
            return BK_TIME

        if text in CONSOLE_TYPES:
            context.user_data["bk_console"] = text
            _push_state(context, BK_CONSOLE)
            # Show available specific consoles instead of jumping to duration
            date_str = context.user_data.get("bk_date", "")
            time_str = context.user_data.get("bk_time", "")
            dur = context.user_data.get("bk_duration_mins", 60)
            if date_str and time_str:
                try:
                    available = await _get_available_consoles(date_str, time_str, dur)
                    if text != "Any":
                        available = [c for c in available if c.get("type", "").lower() == text.lower()]
                    if available:
                        await update.message.reply_text(
                            f"🎮 *{text}* အတွက် ရနိုင်သော Console များ:",
                            parse_mode="Markdown",
                            reply_markup=_make_specific_console_keyboard(available),
                        )
                        return BK_CONSOLE_PREF
                except Exception as e:
                    logging.warning("bk_console_select: _get_available_consoles failed — %s", e)
            # ── No consoles available at this time — show next available times ──
            if date_str and time_str:
                try:
                    target_h, target_m = map(int, time_str.split(":"))
                    target_start = target_h * 60 + target_m
                    target_end = target_start + dur
                    consoles_raw = await _api._fetch_consoles()
                    if text != "Any":
                        consoles_raw = [c for c in consoles_raw if c.get("type", "").lower() == text.lower()]
                    bks = await _api._api_get(f"search-bookings?date={date_str}")
                    if isinstance(bks, dict) and "bookings" in bks:
                        bks = bks["bookings"]
                    if not isinstance(bks, list):
                        bks = []
                    next_times = _get_next_available_times(consoles_raw, bks, target_start, target_end, date_str)
                    if next_times:
                        lines = [f"🎮 *{text}* စက်များ {time_str} တွင် မအားသေးပါ。\n"]
                        for nt in next_times:
                            lines.append(f"{nt['console_id']} → {nt['free_from_str']} နောက်ပိုင်း ရနိုင်ပါမည်")
                        lines.append("\n⏰ အခြားအချိန်ရွေးရန် Back နှိပ်ပါ")
                        await update.message.reply_text(
                            "\n".join(lines),
                            parse_mode="Markdown",
                            reply_markup=_rp_kb([[BTN_BACK], [BTN_CANCEL]]),
                        )
                        return BK_CONSOLE
                except Exception as e:
                    logging.warning("bk_console_select: _get_next_available_times failed — %s", e)
            # Fallback: no specific consoles or data missing → go to duration
            await update.message.reply_text(
                f"🎮 Console: *{text}*\n\n⏱️ ကြာချိန် ရွေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_duration_keyboard(),
            )
            return BK_DURATION
        elif text in (BTN_NOT_SURE, "🤷 မရွေးတတ်ပါ"):
            context.user_data["bk_console"] = "Any"
            _push_state(context, BK_CONSOLE)
            # Show available specific consoles
            date_str = context.user_data.get("bk_date", "")
            time_str = context.user_data.get("bk_time", "")
            dur = context.user_data.get("bk_duration_mins", 60)
            if date_str and time_str:
                try:
                    available = await _get_available_consoles(date_str, time_str, dur)
                    if available:
                        await update.message.reply_text(
                            "🎮 *Any* — ရနိုင်သော Console များ:",
                            parse_mode="Markdown",
                            reply_markup=_make_specific_console_keyboard(available),
                        )
                        return BK_CONSOLE_PREF
                except Exception as e:
                    logging.warning("bk_console_select(Any): _get_available_consoles failed — %s", e)
            # ── No consoles available at this time — show next available times ──
            if date_str and time_str:
                try:
                    target_h, target_m = map(int, time_str.split(":"))
                    target_start = target_h * 60 + target_m
                    target_end = target_start + dur
                    all_consoles = await _api._fetch_consoles()
                    bks = await _api._api_get(f"search-bookings?date={date_str}")
                    if isinstance(bks, dict) and "bookings" in bks:
                        bks = bks["bookings"]
                    if not isinstance(bks, list):
                        bks = []
                    next_times = _get_next_available_times(all_consoles, bks, target_start, target_end, date_str)
                    if next_times:
                        lines = ["🎮 *Any* — စက်များ " + time_str + " တွင် မအားသေးပါ。\n"]
                        for nt in next_times:
                            lines.append(f"{nt['console_id']} → {nt['free_from_str']} နောက်ပိုင်း ရနိုင်ပါမည်")
                        lines.append("\n⏰ အခြားအချိန်ရွေးရန် Back နှိပ်ပါ")
                        await update.message.reply_text(
                            "\n".join(lines),
                            parse_mode="Markdown",
                            reply_markup=_rp_kb([[BTN_BACK], [BTN_CANCEL]]),
                        )
                        return BK_CONSOLE
                except Exception as e:
                    logging.warning("bk_console_select(Any): _get_next_available_times failed — %s", e)
            # Fallback
            await update.message.reply_text(
                "🎮 Console: *Any*\n\n⏱️ ကြာချိန် ရွေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_duration_keyboard(),
            )
            return BK_DURATION
        else:
            await update.message.reply_text(
                "🎮 ကျေးဇူးပြုပြီး console အမျိုးအစား ရွေးပါ:",
                reply_markup=_make_console_keyboard(),
            )
            return BK_CONSOLE

    # Callback path (keep for safety)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data == "bk_con:cancel":
            return await _cleanup_and_end(update, context)

        if data.startswith("bk_con:"):
            con = data.split(":", 1)[1]
            context.user_data["bk_console"] = "Any" if con == "not_sure" else con
            await query.edit_message_text(
                f"🎮 Selected: *{context.user_data['bk_console']}*")
            await query.message.reply_text(
                "⏱️ ကြာချိန် ရွေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_duration_keyboard(),
            )
            return BK_DURATION

        await query.edit_message_text("❌ Invalid console selection.")
        return BK_CONSOLE

    return BK_CONSOLE


# ── State 9: BK_DURATION — Select duration ─────────────────────────────────

async def bk_duration_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle duration selection."""
    asyncio.create_task(_api.track_usage(update.effective_user, "book_step_duration", detail="Booking: duration selection"))
    text = (update.message.text or "").strip() if update.message else ""

    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        # Handle retry button
        if text == BTN_RETRY_BOOKING:
            retry_result = await _handle_retry(update, context)
            if retry_result is not None:
                return retry_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        if text == BTN_BACK:
            _pop_state(context)
            # Try to go back to specific console selection
            date_str = context.user_data.get("bk_date", "")
            time_str = context.user_data.get("bk_time", "")
            dur = context.user_data.get("bk_duration_mins", 60)
            pref = context.user_data.get("bk_console", "") or context.user_data.get("bk_console_pref", "")
            if date_str and time_str and pref:
                try:
                    available = await _get_available_consoles(date_str, time_str, dur)
                    if pref != "Any":
                        available = [c for c in available if c.get("type", "").lower() == pref.lower()]
                    if available:
                        spec_kb = _make_specific_console_keyboard(available)
                        await update.message.reply_text(
                            f"\ud83c\udfae <b>{pref}</b> \u1021\u1010\u103ack\u1039\u101e \u101b\u1014\u1039\u1014\u102d\u102f\u1000\u103c console \u1019\u103b\u102c\u1038:\n\u1021\u102c\u1031\u1037\u1019\u103d \u1010\u102d\u102f\u1000\u103c\u103d\u1031\u1038 \u101b\u103d\u1031\u1038\u1015\u102b \u101e\u102d\u102f\u101b\u103d\u1019\u1039\u1019\u102d '\u1018\u101a\u103a\u1005\u1000\u103a\u1016\u103c\u1005\u103a\u1016\u103c\u1005\u103a \u101b\u1015\u102b\u1010\u101a\u103a' \u1000\u102d\u102f \u101b\u103d\u1031\u1038\u1015\u102b:",
                            parse_mode="HTML",
                            reply_markup=spec_kb,
                        )
                        return BK_CONSOLE_PREF
                except Exception:
                    pass
            # Fallback: go to console type selection
            await update.message.reply_text(
                "🎮 Console အမျိုးအစား ရွေးပါ:",
                reply_markup=_make_console_keyboard(),
            )
            return BK_CONSOLE

        m = re.match(r'^(\d+)\s*mins?$', text)
        if m:
            mins = int(m.group(1))
            if mins in [int(d.split()[0]) for d in DURATION_OPTS]:
                context.user_data["bk_duration_mins"] = mins
                _push_state(context, BK_DURATION)
                await update.message.reply_text("🕹️ Game list ဆွဲနေသည်...")

                try:
                    games = await _api._fetch_games(context.user_data.get("bk_console", ""))
                except Exception as e:
                    logger.error("bk_duration_select: _fetch_games failed: %s", e)
                    return await _show_api_error_with_retry(
                        update, context,
                        error_msg="Game list မရပါ — API server ခဏပြဿနာရှိနေသည်။",
                        retry_action="retry_games",
                    )
                context.user_data["_bk_game_list"] = games
                context.user_data["_bk_game_page"] = 0

                if not games:
                    await update.message.reply_text(
                        "⚠️ Game list မရဘူး — skip လုပ်မလား?",
                        reply_markup=_rp_kb([[BTN_SKIP], [BTN_BACK, BTN_CANCEL]]),
                    )
                    return BK_GAME

                await update.message.reply_text(
                    f"⏱️ Duration: *{mins} mins*\n\n"
                    f"🕹️ ဆော့မည့်ဂိမ်းရွေးပါ (Total: {len(games)} games):",
                    parse_mode="Markdown",
                    reply_markup=_make_game_keyboard(games),
                )
                return BK_GAME

        await update.message.reply_text(
            "⏱️ ကျေးဇူးပြုပြီး ကြာချိန်ကို ရွေးပါ:",
            reply_markup=_make_duration_keyboard(),
        )
        return BK_DURATION

    # Callback path (keep for safety)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data == "bk_dur:cancel":
            return await _cleanup_and_end(update, context)

        if data.startswith("bk_dur:"):
            try:
                mins = int(data.split(":", 1)[1])
            except ValueError:
                await query.edit_message_text("❌ Invalid duration.")
                return BK_DURATION

            context.user_data["bk_duration_mins"] = mins
            await query.edit_message_text("🕹️ Game list ဆွဲနေသည်...")

            try:
                games = await _api._fetch_games(context.user_data.get("bk_console", ""))
            except Exception as e:
                logger.error("bk_duration_select(cb): _fetch_games failed: %s", e)
                return await _show_api_error_with_retry(
                    update, context,
                    error_msg="Game list မရပါ — API server ခဏပြဿနာရှိနေသည်။",
                    retry_action="retry_games",
                )

            context.user_data["_bk_game_list"] = games
            context.user_data["_bk_game_page"] = 0

            if not games:
                await query.edit_message_text(
                    "⚠️ Game list မရဘူး — data မရှိပါ။ skip လုပ်မလား?",
                    reply_markup=_rp_kb([[BTN_SKIP], [BTN_BACK, BTN_CANCEL]]),
                )
                return BK_GAME

            await query.edit_message_text(
                f"⏱️ Duration: *{mins} mins*\n\n"
                f"🕹️ ဆော့မည့်ဂိမ်းရွေးပါ (Total: {len(games)} games):",
                parse_mode="Markdown",
                reply_markup=_make_game_keyboard(games),
            )
            return BK_GAME

        await query.edit_message_text("❌ Invalid duration selection.")
        return BK_DURATION

    return BK_DURATION


# ── State 10: BK_GAME — Select game ─────────────────────────────────────

async def bk_game_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game selection."""
    asyncio.create_task(_api.track_usage(update.effective_user, "book_step_game", detail="Booking: game selection"))
    text = (update.message.text or "").strip() if update.message else ""

    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        # Handle retry button
        if text == BTN_RETRY_BOOKING:
            retry_result = await _handle_retry(update, context)
            if retry_result is not None:
                return retry_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        if text == BTN_BACK:
            _pop_state(context)
            await update.message.reply_text(
                "⏱️ ကြာချိန် ရွေးပါ:",
                reply_markup=_make_duration_keyboard(),
            )
            return BK_DURATION

        if text in (BTN_NOT_SURE, "🤷 မရွေးတတ်ပါ"):
            context.user_data["bk_game"] = "Any"
            _push_state(context, BK_GAME)
            summary = _format_booking_summary(context)
            await update.message.reply_text(
                f"🕹️ Game: *Any*\n\n{summary}\n\n✅ Confirm လုပ်မလား?",
                parse_mode="Markdown",
                reply_markup=_make_confirm_keyboard(),
            )
            return BK_CONFIRM

        if text == BTN_SKIP:
            context.user_data["bk_game"] = "Any"
            _push_state(context, BK_GAME)
            summary = _format_booking_summary(context)
            await update.message.reply_text(
                f"🕹️ Game: *Any*\n\n{summary}\n\n✅ Confirm လုပ်မလား?",
                parse_mode="Markdown",
                reply_markup=_make_confirm_keyboard(),
            )
            return BK_CONFIRM

        if text == "◀️ Previous":
            page = context.user_data.get("_bk_game_page", 0) - 1
            if page < 0:
                page = 0
            context.user_data["_bk_game_page"] = page
            games = context.user_data.get("_bk_game_list", [])
            await update.message.reply_text(
                f"🕹️ ဆော့မည့်ဂိမ်းရွေးပါ (Total: {len(games)} games, Page {page + 1}):",
                reply_markup=_make_game_keyboard(games, page),
            )
            return BK_GAME

        if text == "Next ▶️":
            page = context.user_data.get("_bk_game_page", 0) + 1
            context.user_data["_bk_game_page"] = page
            games = context.user_data.get("_bk_game_list", [])
            await update.message.reply_text(
                f"🕹️ ဆော့မည့်ဂိမ်းရွေးပါ (Total: {len(games)} games, Page {page + 1}):",
                reply_markup=_make_game_keyboard(games, page),
            )
            return BK_GAME

        # Treat any other text as a game selection
        games = context.user_data.get("_bk_game_list", [])
        matched = [g for g in games if g[:50] == text[:50]]
        if matched:
            context.user_data["bk_game"] = matched[0]
        else:
            # Free text doesn't match any known game — ask to select from list
            page = context.user_data.get("_bk_game_page", 0)
            await update.message.reply_text(
                f"⚠️ \"{text[:40]}\" သည် game list ထဲတွင် မတွေ့ပါ။\n"
                "ကျေးဇူးပြုပြီး list ထဲမှ ရွေးချယ်ပါ:",
                reply_markup=_make_game_keyboard(games, page),
            )
            return BK_GAME

        _push_state(context, BK_GAME)
        summary = _format_booking_summary(context)
        await update.message.reply_text(
            f"🕹️ Game: *{context.user_data['bk_game']}*\n\n{summary}\n\n✅ Confirm လုပ်မလား?",
            parse_mode="Markdown",
            reply_markup=_make_confirm_keyboard(),
        )
        return BK_CONFIRM

    # Callback path (keep for safety)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data == "bk_game:cancel":
            return await _cleanup_and_end(update, context)

        if data.startswith("bk_game_page:"):
            page = int(data.split(":", 1)[1])
            context.user_data["_bk_game_page"] = page
            games = context.user_data.get("_bk_game_list", [])
            await query.edit_message_text(
                f"🕹️ ဆော့မည့်ဂိမ်းရွေးပါ (Total: {len(games)} games, Page {page + 1}):",
                reply_markup=_make_game_keyboard(games, page),
            )
            return BK_GAME

        if data.startswith("bk_game:"):
            game = data.split(":", 1)[1]
            context.user_data["bk_game"] = "Any" if game == "not_sure" else game
            summary = _format_booking_summary(context)
            await query.edit_message_text(
                f"🕹️ Game: *{context.user_data['bk_game']}*\n\n{summary}\n\n✅ Confirm လုပ်မလား?",
                parse_mode="Markdown",
                reply_markup=_make_confirm_keyboard(),
            )
            return BK_CONFIRM

        await query.edit_message_text("❌ Invalid game selection.")
        return BK_GAME

    return BK_GAME


# ── State 11: BK_CONSOLE_PREF — Console preference ─────────────────────────
BTN_AUTO_ASSIGN = "🔄 ဘယ်စက်ဖြစ်ဖြစ် ရပါတယ်"

async def bk_console_pref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle console preference selection. After type, show available specific consoles."""
    text = (update.message.text or "").strip() if update.message else ""

    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        # Check if user already picked a console type
        has_pref = bool(context.user_data.get("bk_console", "") or context.user_data.get("bk_console_pref", ""))

        # ── AUTO ASSIGN ──
        if text == BTN_AUTO_ASSIGN:
            context.user_data.pop("bk_specific_console_id", None)
            _push_state(context, BK_CONSOLE_PREF)
            dur = context.user_data.get("bk_duration_mins", 60)
            await update.message.reply_text(
                f"\u23f1\ufe0f \u1000\u103c\u102c\u1001\u103b\u102d\u102f\u1004\u103a \u101b\u103d\u1031\u1038\u1015\u102b:",
                parse_mode="Markdown",
                reply_markup=_make_duration_keyboard(),
            )
            return BK_DURATION

        # ── SPECIFIC CONSOLE SELECTED (e.g. "C-01 (PS5)") ──
        if "(" in text and ")" in text:
            parts = text.split("(", 1)
            cid = parts[0].strip()
            ctype = parts[1].rstrip(")").strip() if len(parts) > 1 else ""
            context.user_data["bk_specific_console_id"] = cid
            if ctype:
                context.user_data["bk_console"] = ctype
                context.user_data["bk_console_pref"] = ctype
            _push_state(context, BK_CONSOLE_PREF)
            dur = context.user_data.get("bk_duration_mins", 60)
            await update.message.reply_text(
                f"\u23f1\ufe0f \u1000\u103c\u102c\u1001\u103b\u102d\u102f\u1004\u103a \u101b\u103d\u1031\u1038\u1015\u102b:",
                parse_mode="Markdown",
                reply_markup=_make_duration_keyboard(),
            )
            return BK_DURATION

        # ── CONSOLE TYPE SELECTED (PS5 / PS5 Pro / Any) ──
        if text in CONSOLE_TYPES:
            context.user_data["bk_console"] = text
            context.user_data["bk_console_pref"] = text
            pref = text
        elif text in (BTN_NOT_SURE, "\u1e49\u1037 \u1019\u103d\u101b\u1031\u1021038တတ်ပါ"):
            context.user_data["bk_console"] = "Any"
            context.user_data["bk_console_pref"] = "Any"
            pref = "Any"
        elif text == BTN_BACK:
            _pop_state(context)
            await update.message.reply_text(
                "🎮 Console အမျိုးအစား ရွေးပါ:",
                reply_markup=_make_console_keyboard(),
            )
            return BK_CONSOLE
        else:
            await update.message.reply_text(
                "\ud83d\udcbb \u1000\u103c\u1031\u102c\u103a\u1015\u1030\u1012\u103e\u102d\u1033 console preference \u101b\u103d\u1031\u1038\u1015\u102b:",
                reply_markup=_make_console_keyboard(),
            )
            return BK_CONSOLE_PREF

        # After type selected, try to show available specific consoles
        date_str = context.user_data.get("bk_date", "")
        time_str = context.user_data.get("bk_time", "")
        dur = context.user_data.get("bk_duration_mins", 60)
        if date_str and time_str:
            try:
                available = await _get_available_consoles(date_str, time_str, dur)
                if pref != "Any":
                    available = [c for c in available if c.get("type", "").lower() == pref.lower()]
                if available:
                    spec_kb = _make_specific_console_keyboard(available)
                    await update.message.reply_text(
                        f"\ud83c\udfae <b>{pref}</b> \u1021\u1010\u103ack\u1039\u101e \u101b\u1014\u1039\u1014\u102d\u102f\u1000\u103c console \u1019\u103b\u102c\u1038:\n\u1021\u102c\u1031\u1037\u1019\u103d \u1010\u102d\u102f\u1000\u103c\u103d\u1031\u1038 \u101b\u103d\u1031\u1038\u1015\u102b \u101e\u102d\u102f\u101b\u103d\u1019\u1039\u1019\u102d '\u1018\u101a\u103a\u1005\u1000\u103a\u1016\u103c\u1005\u103a\u1016\u103c\u1005\u103a \u101b\u1015\u102b\u1010\u101a\u103a' \u1000\u102d\u102f \u101b\u103d\u1031\u1038\u1015\u102b:",
                        parse_mode="HTML",
                        reply_markup=spec_kb,
                    )
                    return BK_CONSOLE_PREF
            except Exception as e:
                logging.warning("bk_console_pref: _get_available_consoles failed — %s", e)

        # ── No consoles available at this time — show next available times ──
        if date_str and time_str:
            try:
                target_h, target_m = map(int, time_str.split(":"))
                target_start = target_h * 60 + target_m
                target_end = target_start + dur
                consoles_raw = await _api._fetch_consoles()
                if pref != "Any":
                    consoles_raw = [c for c in consoles_raw if c.get("type", "").lower() == pref.lower()]
                bks = await _api._api_get(f"search-bookings?date={date_str}")
                if isinstance(bks, dict) and "bookings" in bks:
                    bks = bks["bookings"]
                if not isinstance(bks, list):
                    bks = []
                next_times = _get_next_available_times(consoles_raw, bks, target_start, target_end, date_str)
                if next_times:
                    lines = [f"🎮 *{pref}* စက်များ {time_str} တွင် မအားသေးပါ。\n"]
                    for nt in next_times:
                        lines.append(f"{nt['console_id']} → {nt['free_from_str']} နောက်ပိုင်း ရနိုင်ပါမည်")
                    lines.append("\n⏰ အခြားအချိန်ရွေးရန် Back နှိပ်ပါ")
                    await update.message.reply_text(
                        "\n".join(lines),
                        parse_mode="Markdown",
                        reply_markup=_rp_kb([[BTN_BACK], [BTN_CANCEL]]),
                    )
                    return BK_CONSOLE_PREF
            except Exception as e:
                logging.warning("bk_console_pref: _get_next_available_times failed — %s", e)

        # No specific consoles to show - go to duration
        _push_state(context, BK_CONSOLE_PREF)
        dur = context.user_data.get("bk_duration_mins", 60)
        await update.message.reply_text(
            f"\u23f1\ufe0f \u1000\u103c\u102c\u1001\u103b\u102d\u102f\u1004\u103a \u101b\u103d\u1031\u1038\u1015\u102b:",
            parse_mode="Markdown",
            reply_markup=_make_duration_keyboard(),
        )
        return BK_DURATION

    # Callback path (keep for safety)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data == "bk_con:cancel":
            return await _cleanup_and_end(update, context)

        if data.startswith("bk_con:"):
            pref = data.split(":", 1)[1]
            pref = "Any" if pref == "not_sure" else pref
            context.user_data["bk_console"] = pref
            context.user_data["bk_console_pref"] = pref
            _push_state(context, BK_CONSOLE_PREF)
            await query.edit_message_text(
                "\ud83c\udfae Selected: " + pref)
            await query.message.reply_text(
                "\u23f1\ufe0f \u1000\u103c\u102c\u1001\u103b\u102d\u102f\u1004\u103a \u101b\u103d\u1031\u1038\u1015\u102b:",
                parse_mode="Markdown",
                reply_markup=_make_duration_keyboard(),
            )
            return BK_DURATION

        await query.edit_message_text("\u274c Invalid preference selection.")
        return BK_CONSOLE_PREF

    return BK_CONSOLE_PREF


async def bk_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle booking confirmation and submission to API."""
    asyncio.create_task(_api.track_usage(update.effective_user, "book_step_confirm", detail="Booking: confirmation"))
    text = (update.message.text or "").strip() if update.message else ""

    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        # Handle retry button
        if text == BTN_RETRY_BOOKING:
            retry_result = await _handle_retry(update, context)
            if retry_result is not None:
                return retry_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        if text == BTN_BACK:
            _pop_state(context)
            games = context.user_data.get("_bk_game_list", [])
            page = context.user_data.get("_bk_game_page", 0)
            if games:
                await update.message.reply_text(
                    "🕹️ ဆော့မည့်ဂိမ်းရွေးပါ:",
                    reply_markup=_make_game_keyboard(games, page),
                )
            else:
                await update.message.reply_text(
                    "⏱️ ကြာချိန် ရွေးပါ:",
                    reply_markup=_make_duration_keyboard(),
                )
            return BK_GAME

        if text == BTN_CONFIRM_BOOK:
            await update.message.reply_text("⏳ Booking တင်နေသည်...")

            user = update.effective_user
            uid = str(user.id) if user else ""

            date_str = context.user_data.get("bk_date", "")
            time_str = context.user_data.get("bk_time", "")

            # Check for duplicate booking (time-range overlap, not exact match)
            try:
                existing = await _api._api_get(
                    f"search-bookings?telegram_chat_id={uid}&date={date_str}"
                )
                existing = existing.get("bookings", []) if isinstance(existing, dict) else (existing or [])
                existing_active = [b for b in existing if b.get("status", "").lower() not in ("cancelled", "done", "rejected")]

                # Time-range overlap check
                dur = context.user_data.get("bk_duration_mins", 60)
                try:
                    th, tm = map(int, time_str.split(":"))
                    req_start = th * 60 + tm
                    req_end = req_start + dur
                except (ValueError, AttributeError):
                    req_start = req_end = 0

                dupes = []
                for b in existing_active:
                    b_slot = b.get("timeSlot", "")
                    if not b_slot:
                        continue
                    try:
                        bh, bm = map(int, b_slot.split(":"))
                        b_start = bh * 60 + bm
                        b_dur = int(b.get("durationMins") or b.get("duration_mins") or 60)
                        b_end = b_start + b_dur
                        if b_start < req_end and b_end > req_start:
                            dupes.append(b)
                    except (ValueError, AttributeError):
                        continue

                if dupes:
                    await update.message.reply_text(
                        "⚠️ *Duplicate Booking Detected!*\n\n"
                        f"📅 {date_str} ⏰ {time_str} တွင် booking ရှိပြီးသားပါ\n\n"
                        "ဒါပေမဲ့ ဆက်တင်မလား?",
                        parse_mode="Markdown",
                        reply_markup=_make_warning_keyboard(),
                    )
                    _push_state(context, BK_CONFIRM)
                    return BK_DUP_WARN
            except Exception:
                pass

            result = await _submit_booking(update, context)
            msg, ok = result[0], result[1]
            go_back = len(result) > 2 and result[2]
            if ok:
                await update.message.reply_text(msg, parse_mode="Markdown")
                if context.user_data.get("bk_member_id", ""):
                    msg = (
                        "✅ Booking confirmed!\n\n"
                        "⏳ Staff က verify လုပ်ပါလိမ့်မယ်။\n"
                        "PS Vibe မှ ကျေးဇူးတင်ပါသည်! ✨"
                    )
                    await update.message.reply_text(msg, reply_markup=MAIN_MENU_KB)
                    context.user_data.clear()
                    return ConversationHandler.END
                # ── Deposit flow ──
                return await _bk_start_deposit(update, context)
            if go_back:
                max_dur = context.user_data.pop("_bk_max_duration", 0)
                await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=_make_duration_keyboard(max_dur))
                _push_state(context, BK_DURATION)
                return BK_DURATION
            await update.message.reply_text(msg, reply_markup=MAIN_MENU_KB)
            context.user_data.clear()
            return ConversationHandler.END

        return BK_CONFIRM

    # Callback path (keep for safety)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data == "bk_ok:no":
            return await _cleanup_and_end(update, context)

        if data == "bk_ok:yes":
            await query.edit_message_text("⏳ Booking တင်နေသည်...")
            user = update.effective_user
            uid = str(user.id) if user else ""
            date_str = context.user_data.get("bk_date", "")
            time_str = context.user_data.get("bk_time", "")

            # Check for duplicate booking (time-range overlap, not exact match)
            try:
                existing = await _api._api_get(
                    f"search-bookings?telegram_chat_id={uid}&date={date_str}"
                )
                existing = existing.get("bookings", []) if isinstance(existing, dict) else (existing or [])
                existing_active = [b for b in existing if b.get("status", "").lower() not in ("cancelled", "done", "rejected")]

                dur = context.user_data.get("bk_duration_mins", 60)
                try:
                    th, tm = map(int, time_str.split(":"))
                    req_start = th * 60 + tm
                    req_end = req_start + dur
                except (ValueError, AttributeError):
                    req_start = req_end = 0

                dupes = []
                for b in existing_active:
                    b_slot = b.get("timeSlot", "")
                    if not b_slot:
                        continue
                    try:
                        bh, bm = map(int, b_slot.split(":"))
                        b_start = bh * 60 + bm
                        b_dur = int(b.get("durationMins") or b.get("duration_mins") or 60)
                        b_end = b_start + b_dur
                        if b_start < req_end and b_end > req_start:
                            dupes.append(b)
                    except (ValueError, AttributeError):
                        continue

                if dupes:
                    await query.edit_message_text(
                        "⚠️ *Duplicate Booking Detected!*\n\n"
                        f"📅 {date_str} ⏰ {time_str} တွင် booking ရှိပြီးသားပါ\n\n"
                        "ဒါပေမဲ့ ဆက်တင်မလား?",
                        parse_mode="Markdown",
                        reply_markup=_make_warning_keyboard(),
                    )
                    _push_state(context, BK_CONFIRM)
                    return BK_DUP_WARN
            except Exception:
                pass

            result = await _submit_booking(update, context)
            msg, ok = result[0], result[1]
            go_back = len(result) > 2 and result[2]
            if ok:
                await query.edit_message_text(msg, parse_mode="Markdown")
                if context.user_data.get("bk_member_id", ""):
                    msg = (
                        "✅ Booking confirmed!\n\n"
                        "⏳ Staff က verify လုပ်ပါလိမ့်မယ်။\n"
                        "PS Vibe မှ ကျေးဇူးတင်ပါသည်! ✨"
                    )
                    await query.message.reply_text(msg, reply_markup=MAIN_MENU_KB)
                    context.user_data.clear()
                    return ConversationHandler.END
                return await _bk_start_deposit(update, context)
            elif go_back:
                await query.edit_message_text(msg, parse_mode="Markdown")
                max_dur = context.user_data.pop("_bk_max_duration", 0)
                await query.message.reply_text("Duration ပြန်ရွေးပါ 👇", reply_markup=_make_duration_keyboard(max_dur))
                _push_state(context, BK_DURATION)
                return BK_DURATION
            else:
                await query.edit_message_text(msg)
                await query.message.reply_text(reply_markup=MAIN_MENU_KB)
            context.user_data.clear()
            return ConversationHandler.END

        await query.edit_message_text("❌ Invalid confirmation.")
        return BK_CONFIRM

    return BK_CONFIRM


# ── State 13: BK_DUP_WARN — Duplicate booking warning ──────────────────────

async def bk_dup_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle duplicate booking warning."""
    text = (update.message.text or "").strip() if update.message else ""

    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        if text in (BTN_BOOK_GOBACK, "🔙 မတင်တော့ပါ"):
            _pop_state(context)
            summary = _format_booking_summary(context)
            await update.message.reply_text(
                f"{summary}\n\n✅ Confirm လုပ်မလား?",
                parse_mode="Markdown",
                reply_markup=_make_confirm_keyboard(),
            )
            return BK_CONFIRM

        if text in (BTN_BOOK_ANYWAY, "⚠️ ဒါပေမဲ့ ဆက်တင်မည်"):
            await update.message.reply_text("⏳ Booking တင်နေသည် (duplicate warning overridden)...")
            result = await _submit_booking(update, context)
            msg, ok = result[0], result[1]
            go_back = len(result) > 2 and result[2]
            if ok:
                await update.message.reply_text(msg, parse_mode="Markdown")
                if context.user_data.get("bk_member_id", ""):
                    msg = (
                        "✅ Booking confirmed!\n\n"
                        "⏳ Staff က verify လုပ်ပါလိမ့်မယ်။\n"
                        "PS Vibe မှ ကျေးဇူးတင်ပါသည်! ✨"
                    )
                    await update.message.reply_text(msg, reply_markup=MAIN_MENU_KB)
                    context.user_data.clear()
                    return ConversationHandler.END
                return await _bk_start_deposit(update, context)
            elif go_back:
                max_dur = context.user_data.pop("_bk_max_duration", 0)
                await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=_make_duration_keyboard(max_dur))
                _push_state(context, BK_DURATION)
                return BK_DURATION
            else:
                await update.message.reply_text(msg, reply_markup=MAIN_MENU_KB)
            context.user_data.clear()
            return ConversationHandler.END

        return BK_DUP_WARN

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data == "bk_warn:dup_ok":
            await query.edit_message_text("⏳ Booking တင်နေသည် (duplicate warning overridden)...")
            result = await _submit_booking(update, context)
            msg, ok = result[0], result[1]
            go_back = len(result) > 2 and result[2]
            if ok:
                await query.edit_message_text(msg, parse_mode="Markdown")
                if context.user_data.get("bk_member_id", ""):
                    msg = (
                        "✅ Booking confirmed!\n\n"
                        "⏳ Staff က verify လုပ်ပါလိမ့်မယ်။\n"
                        "PS Vibe မှ ကျေးဇူးတင်ပါသည်! ✨"
                    )
                    await query.message.reply_text(msg, reply_markup=MAIN_MENU_KB)
                    context.user_data.clear()
                    return ConversationHandler.END
                return await _bk_start_deposit(update, context)
            elif go_back:
                await query.edit_message_text(msg, parse_mode="Markdown")
                max_dur = context.user_data.pop("_bk_max_duration", 0)
                await query.message.reply_text("Duration ပြန်ရွေးပါ 👇", reply_markup=_make_duration_keyboard(max_dur))
                _push_state(context, BK_DURATION)
                return BK_DURATION
            else:
                await query.edit_message_text(msg)
                await query.message.reply_text(reply_markup=MAIN_MENU_KB)
            context.user_data.clear()
            return ConversationHandler.END
        elif data == "bk_ok:no":
            return await _cleanup_and_end(update, context)

        await query.edit_message_text("❌ Invalid option.")
        return BK_DUP_WARN

    return BK_DUP_WARN


# ── State 14: BK_DISC_WARN — Discount warning ─────────────────────────────

async def bk_disc_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle discount/conflict warning for booking."""
    text = (update.message.text or "").strip() if update.message else ""

    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        if text in (BTN_BOOK_GOBACK, "🔙 မတင်တော့ပါ"):
            return await _cleanup_and_end(update, context)

        if text in (BTN_BOOK_ANYWAY, "⚠️ ဒါပေမဲ့ ဆက်တင်မည်"):
            summary = _format_booking_summary(context)
            await update.message.reply_text(
                summary + "\n\n⚠️ Discount conflicted but continuing...\n✅ Confirm လုပ်မလား?",
                parse_mode="Markdown",
                reply_markup=_make_confirm_keyboard(),
            )
            return BK_CONFIRM

        return BK_DISC_WARN

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data == "bk_warn:disc_ok":
            summary = _format_booking_summary(context)
            await query.edit_message_text(
                summary + "\n\n⚠️ Discount conflicted but continuing...\n✅ Confirm လုပ်မလား?",
                parse_mode="Markdown",
                reply_markup=_make_confirm_keyboard(),
            )
            return BK_CONFIRM
        elif data == "bk_ok:no":
            return await _cleanup_and_end(update, context)

        await query.edit_message_text("❌ Invalid option.")
        return BK_DISC_WARN

    return BK_DISC_WARN


# ── State 15: BK_CON_CONFLICT — Console conflict warning ──────────────────

async def bk_con_conflict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle console conflict warning."""
    text = (update.message.text or "").strip() if update.message else ""

    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        if text in (BTN_BOOK_GOBACK, "🔙 မတင်တော့ပါ"):
            return await _cleanup_and_end(update, context)

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        if text in (BTN_BOOK_ANYWAY, "⚠️ ဒါပေမဲ့ ဆက်တင်မည်"):
            summary = _format_booking_summary(context)
            await update.message.reply_text(
                summary + "\n\n⚠️ Console conflict detected but continuing...\n✅ Confirm လုပ်မလား?",
                parse_mode="Markdown",
                reply_markup=_make_confirm_keyboard(),
            )
            return BK_CONFIRM

        if text == BTN_DISC_TIME:
            date_str = context.user_data.get("bk_date", "")
            free_slots = await _get_available_slots(date_str) if date_str else []
            await update.message.reply_text(
                f"📅 *{date_str}* — အခြားအချိန် ရွေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_time_keyboard(free_slots),
            )
            return BK_TIME

        if text == BTN_DISC_GAME:
            await update.message.reply_text(
                "🎮 အခြား console ရွေးပါ:",
                reply_markup=_make_console_keyboard(),
            )
            return BK_CONSOLE

        return BK_CON_CONFLICT

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data == "bk_warn:conf_ok":
            summary = _format_booking_summary(context)
            await query.edit_message_text(
                summary + "\n\n⚠️ Console conflict detected but continuing...\n✅ Confirm လုပ်မလား?",
                parse_mode="Markdown",
                reply_markup=_make_confirm_keyboard(),
            )
            return BK_CONFIRM
        elif data == "bk_warn:change_time":
            date_str = context.user_data.get("bk_date", "")
            free_slots = await _get_available_slots(date_str)
            await query.edit_message_text(
                f"📅 *{date_str}* — အခြားအချိန် ရွေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_time_keyboard(free_slots),
            )
            return BK_TIME
        elif data == "bk_warn:change_console":
            await query.edit_message_text(
                "🎮 အခြား console ရွေးပါ:",
                reply_markup=_make_console_keyboard(),
            )
            return BK_CONSOLE
        elif data == "bk_ok:no":
            return await _cleanup_and_end(update, context)

        await query.edit_message_text("❌ Invalid option.")
        return BK_CON_CONFLICT

    return BK_CON_CONFLICT


# ══════════════════════════════════════════════════════════════════════════════
#  Deposit Flow — BK_DEPOSIT_METHOD (state 16) / BK_DEPOSIT_CONFIRM (state 17)
#  Inserted after booking confirmation, before checkout
# ══════════════════════════════════════════════════════════════════════════════

BTN_DEPOSIT_KPAY = "KPay"
BTN_DEPOSIT_WAVEPAY = "WavePay"
BTN_DEPOSIT_AYAPAY = "AYA Pay"
BTN_DEPOSIT_SKIP = "⏭️ Deposit မလုပ်ပါ"

DEPOSIT_METHOD_MAP = {
    "kpay":    {"btn": "KPay",    "key": "kpay"},
    "wavepay": {"btn": "WavePay", "key": "wavepay"},
    "aya_pay": {"btn": "AYA Pay", "key": "aya_pay"},
}


def _deposit_method_keyboard() -> ReplyKeyboardMarkup:
    """Build deposit method selection keyboard."""
    return _rp_kb([
        [BTN_DEPOSIT_KPAY, BTN_DEPOSIT_WAVEPAY],
        [BTN_DEPOSIT_AYAPAY],
        [BTN_CANCEL],
    ])


async def _calc_deposit_amount(context: ContextTypes.DEFAULT_TYPE) -> int:
    """Calculate 30% deposit via API (uses actual console rates).
    Returns amount in MMK.
    """
    import asyncio
    from . import api as _api
    
    console_id = context.user_data.get("bk_specific_console_id", "")
    if not console_id:
        # Fallback: guess from bk_console type
        console_type = context.user_data.get("bk_console", "PS5")
        console_id = "C-01" if "pro" not in console_type.lower() else "C-09"
    
    dur_mins = context.user_data.get("bk_duration_mins", 60)
    date_str = context.user_data.get("bk_date", "")
    time_str = context.user_data.get("bk_time", "")
    
    try:
        path = f"deposit/schedule?console={console_id}&duration_mins={dur_mins}&date={date_str}&time={time_str}"
        data = await _api._api_get(path, timeout=10)
        # data is already unwrapped (inner payload) by _api_get via unwrap_response
        if isinstance(data, dict) and data.get("deposit_amount"):
            return max(1000, int(data["deposit_amount"]))
    except Exception as e:
        logger.warning(f"_calc_deposit_amount API failed: {e}")
    
    # Fallback: hardcoded calculation
    hours = max(1, round(dur_mins / 60))
    console_type = context.user_data.get("bk_console", "PS5")
    # Fallback rates match console actual pricing
    if console_type and "pro" in console_type.lower():
        rate_per_hour = 12000  # PS5 Pro = 12,000 Ks/hr
    elif console_type and "ps4" in console_type.lower():
        rate_per_hour = 3000   # PS4 = 3,000 Ks/hr
    else:
        rate_per_hour = 4000   # Standard PS5 = 4,000 Ks/hr
    session_fee = rate_per_hour * hours
    deposit = round(session_fee * DEPOSIT_FEE_RATIO)
    deposit = round(deposit / 500) * 500
    return max(1000, deposit)


async def _bk_start_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: show deposit payment method screen.
    Called after successful booking submission."""
    booking_id = context.user_data.get("_bk_last_id", "?")
    deposit_amount = await _calc_deposit_amount(context)
    context.user_data["_bk_deposit_amount"] = deposit_amount

    msg = (
        f"💰 အပ်ငွေ (Deposit) အနေနဲ့ *{deposit_amount:,} ကျပ်* \n"
        f"(စုစုပေါင်းခန့်မှန်းခြေရဲ့ {int(DEPOSIT_FEE_RATIO * 100)}%) \n"
        f"အာမခံအနေနဲ့ သွင်းပေးရန်လိုအပ်ပါတယ်။\n\n"
        "ကျေးဇူးပြုပြီး ငွေလွှဲမည့် နည်းလမ်းကို ရွေးချယ်ပါ 👇"
    )
    if update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode="Markdown", reply_markup=_deposit_method_keyboard())
    elif update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=_deposit_method_keyboard())
    return BK_DEPOSIT_METHOD


async def bk_deposit_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle BK_DEPOSIT_METHOD — user picks KPay / WavePay / AYA Pay."""
    text = (update.message.text or "").strip() if update.message else ""

    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        if text == BTN_DEPOSIT_SKIP:
            # Skip deposit — go to end
            msg = (
                "✅ Booking confirmed!\n\n"
                "⏳ Staff က verify လုပ်ပါလိမ့်မယ်။\n"
                "PS Vibe မှ ကျေးဇူးတင်ပါသည်! ✨"
            )
            if update.message:
                await update.message.reply_text(msg, reply_markup=MAIN_MENU_KB)
            context.user_data.clear()
            return ConversationHandler.END

        # Map button text to account key
        method_key = None
        for key, info in DEPOSIT_METHOD_MAP.items():
            if text == info["btn"]:
                method_key = key
                break

        if method_key is None:
            await update.message.reply_text(
                "ကျေးဇူးပြုပြီး အောက်ပါ ငွေလွှဲနည်းလမ်းများမှ ရွေးချယ်ပါ 👇",
                reply_markup=_deposit_method_keyboard(),
            )
            return BK_DEPOSIT_METHOD

        # Store selected method
        context.user_data["_bk_deposit_method"] = method_key
        account = DEPOSIT_ACCOUNTS.get(method_key, {"name": "—", "number": "—"})
        deposit_amount = context.user_data.get("_bk_deposit_amount", 3000)

        account_info = (
            f"💳 *{account['name']}*\n"
            f"📱 အကောင့်နံပါတ်: `{account['number']}`\n\n"
            f"💰 *Deposit Amount:* {deposit_amount:,} ကျပ်\n\n"
            "ငွေလွဲပြီးရင် screenshot လေး ပို့ပေးပါခင်ဗျ 🙏"
        )
        await update.message.reply_text(account_info, parse_mode="Markdown")
        return BK_DEPOSIT_CONFIRM

    return BK_DEPOSIT_METHOD


async def bk_deposit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle BK_DEPOSIT_CONFIRM — accept photo/ref from customer."""
    booking_id = context.user_data.get("_bk_last_id", "")
    deposit_method = context.user_data.get("_bk_deposit_method", "") or context.user_data.get("_bk_deposit_method", "")
    deposit_amount = context.user_data.get("_bk_deposit_amount", 0)

    # Determine deposit_ref and ref_type
    deposit_ref = ""
    deposit_ref_type = "text"

    if update.message.photo:
        # User sent a photo — use the largest file_id
        photo = update.message.photo[-1]
        deposit_ref = photo.file_id
        deposit_ref_type = "image"
    elif update.message.text:
        text = update.message.text.strip()

        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        if text == BTN_BACK:
            # Go back to deposit method selection
            await update.message.reply_text(
                "ငွေလွှဲမည့် နည်းလမ်းကို ပြန်ရွေးပါ 👇",
                reply_markup=_deposit_method_keyboard(),
            )
            return BK_DEPOSIT_METHOD

        # Text-only input not allowed — require screenshot
        await update.message.reply_text(
            "❌ ကျေးဇူးပြုပြီး screenshot (ပုံ) ကိုသာ ပို့ပေးပါခင်ဗျ။\n"
            "ငွေလွှဲပြီးရင် screenshot လေး ပို့ပေးပါ 🙏"
        )
        return BK_DEPOSIT_CONFIRM

    if not deposit_ref:
        await update.message.reply_text(
            "❌ ငွေလွှဲပြီးရင် screenshot (ပုံ) လေး ပို့ပေးပါခင်ဗျ။\n"
            "မရှိရင် /cancel ရိုက်ပြီး ထွက်နိုင်ပါတယ်။"
        )
        return BK_DEPOSIT_CONFIRM

    # Call API: POST /api/bookings/{id}/deposit/submit
    try:
        payload = {
            "deposit_method": deposit_method,
            "deposit_ref": deposit_ref,
            "deposit_ref_type": deposit_ref_type,
            "deposit_amount": deposit_amount,
        }
        result = await _api._api_post(f"bookings/{booking_id}/deposit/submit", payload)
        if not result or (isinstance(result, dict) and result.get("__status__", 200) >= 400):
            logger.warning("deposit submit API error for booking %s: %s", booking_id, result)
            await update.message.reply_text(
                "⚠️ Deposit မှတ်တမ်းတင်ရာမှာ error ဖြစ်သွားပါတယ်။\n"
                "Admin ကို ဆက်သွယ်ပါ။\n\n"
                f"📲 https://t.me/psvibeofficial",
                reply_markup=MAIN_MENU_KB,
            )
            context.user_data.clear()
            return ConversationHandler.END
    except Exception as e:
        logger.error("Deposit submit API exception: %s", e)
        # Non-critical — still acknowledge
        pass

    # Send confirmation to customer
    method_label = DEPOSIT_ACCOUNTS.get(deposit_method, {}).get("name", deposit_method.upper())
    confirm_msg = (
        f"✅ Deposit လက်ခံရရှိပါပြီ!\n\n"
        f"📌 Booking #{booking_id}\n"
        f"💳 {method_label}\n"
        f"💰 {deposit_amount:,} ကျပ်\n\n"
        "⏳ Staff မှ အတည်ပြုပြီးပါက သင်၏ Booking အတည်ဖြစ်ပါမည်။\n"
        "Play The Game. Share The VIBE! 🤖"
    )
    await update.message.reply_text(confirm_msg, parse_mode="Markdown", reply_markup=MAIN_MENU_KB)

    # Notify staff group
    try:
        staff_chat = _api.STAFF_NOTIFY_CHAT
        if staff_chat:
            customer_name = context.user_data.get("bk_name", "—")
            phone = context.user_data.get("bk_phone", "—")
            tg_user = update.effective_user
            tg_link = f"tg://user?id={tg_user.id}" if tg_user else "—"

            staff_msg = (
                f"🔔 *Deposit Received*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🆔 Booking #{booking_id}\n"
                f"👤 {customer_name} ([link]({tg_link}))\n"
                f"📞 {phone}\n"
                f"💳 {method_label}\n"
                f"💰 {deposit_amount:,} ကျပ်\n"
                f"📎 Ref: {deposit_ref[:30] if len(deposit_ref) > 30 else deposit_ref}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👉 Verify လုပ်ရန် Dashboard သို့သွားပါ"
            )
            await _api._tg_send({
                "chat_id": staff_chat,
                "text": staff_msg,
                "parse_mode": "Markdown",
            })
            # If screenshot, forward the image to staff group too
            if deposit_ref_type == "image" and hasattr(update.message, "photo") and update.message.photo:
                photo = update.message.photo[-1]
                file_id = photo.file_id
                await _api._http_request(
                    "POST",
                    f"https://api.telegram.org/bot{_api.CUSTOMER_BOT_TOKEN}/sendPhoto",
                    body={"chat_id": staff_chat, "photo": file_id,
                          "caption": f"📸 Deposit SS — Booking #{booking_id}"},
                    timeout=15, api_key=False,
                )
    except Exception as e:
        logger.warning("Staff notification failed for deposit: %s", e)

    context.user_data.clear()
    return ConversationHandler.END


# ── State 7 (text): BK_TIME_TEXT — Custom time text entry ─────────────────────

# NOTE: Custom time handling is now integrated directly into bk_time_select.
# This function is kept for backward compatibility but delegates to bk_time_select.

async def bk_time_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom time text input (delegated to bk_time_select)."""
    return await bk_time_select(update, context)


# ── State -1: BK_END — Fallback handler ────────────────────────────────────

async def bk_catch_all(update, context):
    """Catch-all: prevent unmatched text from falling through to Gemini AI."""
    text = (update.message.text or "").strip() if update.message else ""
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result
    if text == BTN_CANCEL or text.lower() == "cancel":
        context.user_data.clear()
        await update.message.reply_text("Canceled", reply_markup=MAIN_MENU_KB)
        return ConversationHandler.END
    await update.message.reply_text(
        "Please use menu buttons for booking.\nType cancel to exit.",
        parse_mode="Markdown",
    )
    return None

async def bk_end_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fallback handler for BK_END state (sentinel -1)."""
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result
    await update.message.reply_text(
        "Booking session ended. Use 📅 Booking to start a new booking.",
        reply_markup=MAIN_MENU_KB,
    )
    return ConversationHandler.END
