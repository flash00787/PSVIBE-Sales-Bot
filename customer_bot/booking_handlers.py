"""
PS Vibe Customer Bot — Booking Conversation Handlers
All 16 states use ReplyKeyboardMarkup for selection.
InlineKeyboard is used only for dynamic member/game lists where ReplyKeyboard is impractical.

UPDATED: Added back buttons throughout + phone last-3-digit member matching
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from . import api as _api
from .handlers import (
    BK_MEMBER_CHECK, BK_MEMBER_SELECT, BK_PHONE_VERIFY, BK_DATA_CONFIRM,
    BK_NAME, BK_PHONE, BK_DATE, BK_TIME,
    BK_CONSOLE, BK_DURATION, BK_GAME, BK_CONSOLE_PREF, BK_CONFIRM,
    BK_DUP_WARN, BK_DISC_WARN, BK_CON_CONFLICT, BK_SPECIFIC_CONSOLE,
    BK_END, MAIN_MENU_KB, CONSOLE_TYPES, DURATION_OPTS,
    BTN_BOOK_ANYWAY, BTN_BOOK_GOBACK,
    BTN_DISC_GAME, BTN_DISC_TIME,
    _bk_intercept_menu,
)
from .data.prompts import today_mmt, OPEN_HOUR, CLOSE_HOUR

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
BTN_NOT_SURE = "🤷 မရွေးတတ်ပါ"
BTN_CONFIRM_BOOK = "✅ Confirm Booking"
BTN_SKIP = "⏭️ Skip"
BTN_TRY_AGAIN = "🔄 ထပ်ကြိုးစားမည်"

# ── Helper: build one_time ReplyKeyboardMarkup ─────────────────────────────────

def _rp_kb(rows: list, one_time: bool = True) -> ReplyKeyboardMarkup:
    """Build a one-time ReplyKeyboardMarkup with resize."""
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=one_time)

# ── Reply Keyboard Builders ───────────────────────────────────────────────────

def _make_date_keyboard() -> ReplyKeyboardMarkup:
    """Build date selection reply keyboard: Today, Tomorrow, Day After."""
    today = datetime.strptime(today_mmt(), "%Y-%m-%d")
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    return _rp_kb([
        [f"ယနေ့ (Today)  {today.strftime('%Y-%m-%d')}"],
        [f"မနက်ဖြန် (Tomorrow)  {tomorrow.strftime('%Y-%m-%d')}"],
        [f"သဘက်ခါ (Day After)  {day_after.strftime('%Y-%m-%d')}"],
        [BTN_BACK, BTN_CANCEL],
    ])


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


def _make_duration_keyboard() -> ReplyKeyboardMarkup:
    """Build duration selection reply keyboard."""
    return _rp_kb([
        DURATION_OPTS[:2],
        DURATION_OPTS[2:4],
        DURATION_OPTS[4:],
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
    rows.append([BTN_NOT_SURE])
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
    """Get available time slots for a given date."""
    try:
        bks = await _api._api_get(f"bookings/search?date={date_str}")
    except Exception:
        bks = []
    bks = bks if isinstance(bks, list) else []
    if isinstance(bks, dict) and "bookings" in bks:
        bks = bks["bookings"]
    booked_slots = {b.get("timeSlot", "") for b in bks if b.get("status", "").lower() not in ("cancelled", "done")}
    all_slots = [f"{h:02d}:00" for h in range(OPEN_HOUR, CLOSE_HOUR)]
    available = [s for s in all_slots if s not in booked_slots]

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
    buttons.append([BTN_AUTO_ASSIGN])
    buttons.append([BTN_CANCEL])
    return _rp_kb(buttons)


async def _get_available_consoles(date_str, time_str, duration_mins=60):
    """Fetch available consoles for a given date/time, filtering out busy ones."""
    try:
        consoles_raw = await _api._fetch_consoles()
        bks = await _api._api_get(f"bookings/search?date={date_str}")
    except Exception:
        return []
    if not consoles_raw:
        return []
    bks = bks if isinstance(bks, list) else []
    if isinstance(bks, dict) and "bookings" in bks:
        bks = bks["bookings"]
    try:
        target_h, target_m = map(int, time_str.split(":"))
        target_start = target_h * 60 + target_m
        target_end = target_start + duration_mins
    except (ValueError, AttributeError):
        target_start = 0
        target_end = duration_mins
    conflicting = set()
    for b in bks:
        b_status = b.get("status", "").lower()
        if b_status in ("cancelled", "done"):
            continue
        b_console = b.get("console_id", "") or b.get("consoleId", "")
        if not b_console:
            continue
        b_slot = b.get("timeSlot", "")
        try:
            bh, bm = map(int, b_slot.split(":"))
            b_start = bh * 60 + bm
            b_dur = int(b.get("durationMins", duration_mins))
            b_end = b_start + b_dur
            if b_start < target_end and b_end > target_start:
                conflicting.add(b_console)
        except:
            pass
    available = []
    for console in consoles_raw:
        cid = console.get("id", "")
        cstatus = console.get("status", "").lower()
        if cstatus in ("active", "reserved"):
            continue
        if cid in conflicting:
            continue
        available.append(console)
    return available



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
    
    if not console_id and date_str and time_str:
        try:
            available = await _get_available_consoles(date_str, time_str, duration_mins)
            if console_type != "Any":
                available = [c for c in available if c.get("type", "").lower() == console_type.lower()]
            if available:
                assigned = available[0]
                console_id = assigned.get("id", "")
                console_type = assigned.get("type", console_type)
                context.user_data["bk_console"] = console_type
                context.user_data["bk_specific_console_id"] = console_id
        except Exception:
            pass
    
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
        "username": user.username or "",
        "status": "pending",
    }
    try:
        result = await _api._api_post("bookings", payload)
        if result and isinstance(result, dict) and result.get("id"):
            bk_id = result["id"]
            context.user_data["_bk_last_id"] = bk_id
            msg = (
                f"✅ *Booking Submitted — Pending Confirmation*\n\n"
                f"🎫 Booking #{bk_id}\n"
                f"📅 {payload['date']}  ⏰ {payload['timeSlot']}\n"
                f"🎮 {payload['consoleType']}{assigned_console_label}  ⏱️ {payload['durationMins']} mins\n"
                f"🕹️ {payload['gameName']}\n\n"
                f"_Staff မှ confirm လုပ်ပြီးပါက အကြောင်းကြားပါမည်_ 🎮"
            )
            asyncio.create_task(_api.track_usage(user, "booking_created"))
            return msg, True
        else:
            err_msg = str(result) if result else "unknown"
            return (
                "❌ Booking မအောင်မြင်ပါ\n"
                f"Console {console_id} ({console_type}) သည် ထိုအချိန်တွင် မရနိုင်ပါ။\n\n"
                "အခြားအချိန် သို့မဟုတ် အခြား console ကို ထပ်ရွေးပါ။\n"
                "🔄 /start — ပြန်ကြိုးစားရန်"
            ), False
    except Exception as e:
        logger.error("Booking submission failed: %s", e)
        return "❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ သို့မဟုတ် Admin ကို ဆက်သွယ်ပါ", False


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
        stack.pop(0)


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
        [["no (Guest)"], ["❌ ပယ်ဖျက်မည်"]],
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
    context.user_data["bk_name"] = m.get("name", "")
    context.user_data["bk_phone"] = m.get("phone", "")
    context.user_data["bk_member_data"] = m
    phone = m.get("phone", "")
    masked = phone[-4:] if len(phone) >= 4 else phone
    _push_state(context, BK_MEMBER_SELECT)
    msg = (
        f"👤 *{m.get('name','?')}*\n"
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
            [["no (Guest)"], ["❌ ပယ်ဖျက်မည်"]],
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
        context.user_data["bk_name"] = m.get("name", "")
        context.user_data["bk_phone"] = m.get("phone", "")
        context.user_data["bk_member_data"] = m
        phone = m.get("phone", "")
        masked = phone[-4:] if len(phone) >= 4 else phone
        balance = m.get("balance_mins", m.get("balance", "N/A"))

        _push_state(context, BK_PHONE_VERIFY)
        msg = (
            f"✅ *Member တွေ့ရှိပါသည်!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 အမည်: *{m.get('name', '?')}*\n"
            f"📞 ဖုန်း: ...{masked}\n"
            f"💰 Balance: *{balance} mins*\n"
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
            [["no (Guest)"], ["❌ ပယ်ဖျက်မည်"]],
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
        free_slots = await _get_available_slots(date_str)

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
        free_slots = await _get_available_slots(date_str)

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
    text = (update.message.text or "").strip() if update.message else ""

    # Handle ReplyKeyboard text
    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

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
                date_str = context.user_data.get("bk_date", "")
                await update.message.reply_text(
                    f"⏰ အချိန်: *{text}*\n\n🎮 Console အမျိုးအစား ရွေးပါ:",
                    parse_mode="Markdown",
                    reply_markup=_make_console_keyboard(),
                )
                return BK_CONSOLE

        # Check custom time HH:MM
        m = re.match(r'^(\d{1,2}):(\d{2})$', text)
        if m:
            hour, minute = int(m.group(1)), int(m.group(2))
            if OPEN_HOUR <= hour < CLOSE_HOUR and 0 <= minute <= 59:
                time_str = f"{hour:02d}:{minute:02d}"
                context.user_data["bk_time"] = time_str
                _push_state(context, BK_TIME)
                date_str = context.user_data.get("bk_date", "")
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
    text = (update.message.text or "").strip() if update.message else ""

    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

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
                except Exception:
                    pass
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
                except Exception:
                    pass
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
    text = (update.message.text or "").strip() if update.message else ""

    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        if text == BTN_BACK:
            _pop_state(context)
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

                games = await _api._fetch_games(context.user_data.get("bk_console", ""))
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

            games = await _api._fetch_games(context.user_data.get("bk_console", ""))
            context.user_data["_bk_game_list"] = games
            context.user_data["_bk_game_page"] = 0

            if not games:
                await query.edit_message_text(
                    "⚠️ Game list မရဘူး — skip လုပ်မလား?",
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
    text = (update.message.text or "").strip() if update.message else ""

    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

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
            context.user_data["bk_game"] = text[:50]

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
BTN_AUTO_ASSIGN = "↩️ Auto Assign"

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
            return BK_DATE
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
                        f"\ud83c\udfae <b>{pref}</b> \u1021\u1010\u103ack\u1039\u101e \u101b\u1014\u1039\u1014\u102d\u102f\u1000\u103c console \u1019\u103b\u102c\u1038:\n\u1021\u102c\u1031\u1037\u1019\u103d \u1010\u102d\u102f\u1000\u103c\u103d\u1031\u1038 \u101b\u103d\u1031\u1038\u1015\u102b \u101e\u102d\u102f\u101b\u103d\u1019\u1039\u1019\u102d Auto Assign \u101c\u1031\u102c\u103a\u1015\u102b\u1038:",
                        parse_mode="HTML",
                        reply_markup=spec_kb,
                    )
                    return BK_CONSOLE_PREF
            except Exception:
                pass
        
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
    text = (update.message.text or "").strip() if update.message else ""

    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

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

            # Check for duplicate booking
            try:
                existing = await _api._api_get(
                    f"bookings/search?telegram_chat_id={uid}&date={date_str}"
                )
                existing = existing.get("bookings", []) if isinstance(existing, dict) else (existing or [])
                existing_active = [b for b in existing if b.get("status", "").lower() not in ("cancelled",)]
                dupes = [b for b in existing_active if b.get("timeSlot") == time_str]
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

            msg, ok = await _submit_booking(update, context)
            if ok:
                await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=MAIN_MENU_KB)
            else:
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

            try:
                existing = await _api._api_get(
                    f"bookings/search?telegram_chat_id={uid}&date={date_str}"
                )
                existing = existing.get("bookings", []) if isinstance(existing, dict) else (existing or [])
                existing_active = [b for b in existing if b.get("status", "").lower() not in ("cancelled",)]
                dupes = [b for b in existing_active if b.get("timeSlot") == time_str]
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

            msg, ok = await _submit_booking(update, context)
            if ok:
                await query.edit_message_text(msg, parse_mode="Markdown")
                await query.message.reply_text("🎮", reply_markup=MAIN_MENU_KB)
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
            msg, ok = await _submit_booking(update, context)
            if ok:
                await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=MAIN_MENU_KB)
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
            msg, ok = await _submit_booking(update, context)
            if ok:
                await query.edit_message_text(msg, parse_mode="Markdown")
                await query.message.reply_text("🎮", reply_markup=MAIN_MENU_KB)
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

