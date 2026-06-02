"""
PS Vibe Customer Bot — Booking Conversation Handlers
All 16 states use ReplyKeyboardMarkup for selection.
InlineKeyboard is used only for dynamic member/game lists where ReplyKeyboard is impractical.
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
    BK_DUP_WARN, BK_DISC_WARN, BK_CON_CONFLICT,
    BK_END, MAIN_MENU_KB, CONSOLE_TYPES, DURATION_OPTS,
    BTN_BOOK_ANYWAY, BTN_BOOK_GOBACK,
    BTN_DISC_GAME, BTN_DISC_TIME,
    _bk_intercept_menu,
)
from .data.prompts import today_mmt, OPEN_HOUR, CLOSE_HOUR

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
TODAY = today_mmt
BK_END = -1  # sentinel for end

BTN_CANCEL = "❌ ပယ်ဖျက်မည်"
BTN_MEM_YES = "ရှိပါတယ်"
BTN_MEM_NO = "မရှိဘူး (Guest)"
BTN_CONFIRM_YES = "✅ မှန်ပါသည်"
BTN_CONFIRM_NO = "❌ မဟုတ်ပါ"
BTN_NOT_SURE = "🤷 မရွေးတတ်ပါ"
BTN_CONFIRM_BOOK = "✅ Confirm Booking"
BTN_SKIP = "⏭️ Skip"

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
        [BTN_CANCEL],
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
    rows.append(["✏️ Custom Time", BTN_CANCEL])
    return _rp_kb(rows)


def _make_console_keyboard() -> ReplyKeyboardMarkup:
    """Build console type selection reply keyboard."""
    return _rp_kb([
        CONSOLE_TYPES,
        [BTN_NOT_SURE],
        [BTN_CANCEL],
    ])


def _make_duration_keyboard() -> ReplyKeyboardMarkup:
    """Build duration selection reply keyboard."""
    return _rp_kb([
        DURATION_OPTS[:2],
        DURATION_OPTS[2:4],
        DURATION_OPTS[4:],
        [BTN_CANCEL],
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
    rows.append([BTN_CANCEL])
    return _rp_kb(rows)


def _make_confirm_keyboard() -> ReplyKeyboardMarkup:
    """Build confirmation reply keyboard."""
    return _rp_kb([
        [BTN_CONFIRM_BOOK],
        [BTN_CANCEL],
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
    booked_slots = {b.get("timeSlot", "") for b in bks if b.get("status", "").lower() not in ("cancelled", "done")}
    all_slots = [f"{h:02d}:00" for h in range(OPEN_HOUR, CLOSE_HOUR)]
    return [s for s in all_slots if s not in booked_slots]


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
        f"💻 Console Pref: *{d.get('bk_console_pref', '—')}*",
    ]
    return "\n".join(lines)


def _extract_date_from_text(text: str) -> str | None:
    """Extract YYYY-MM-DD date from text like 'ယနေ့ (Today)  2026-05-30'."""
    m = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    return m.group(1) if m else None


async def _submit_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple[str, bool]:
    """Submit booking to API. Returns (message, success_or_not)."""
    user = update.effective_user
    uid = str(user.id) if user else ""
    payload = {
        "customerName": context.user_data.get("bk_name", ""),
        "phone": context.user_data.get("bk_phone", ""),
        "date": context.user_data.get("bk_date", ""),
        "timeSlot": context.user_data.get("bk_time", ""),
        "consoleType": context.user_data.get("bk_console", "PS5"),
        "durationMins": context.user_data.get("bk_duration_mins", 60),
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
                f"🎮 {payload['consoleType']}  ⏱️ {payload['durationMins']} mins\n"
                f"🕹️ {payload['gameName']}\n\n"
                f"_Staff မှ confirm လုပ်ပြီးပါက အကြောင်းကြားပါမည်_ 🎮"
            )
            asyncio.create_task(_api.track_usage(user, "booking_created"))
            return msg, True
        else:
            return "❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ သို့မဟုတ် Admin ကို ဆက်သွယ်ပါ", False
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


# ══════════════════════════════════════════════════════════════════════════════
#  Booking State Handlers
# ══════════════════════════════════════════════════════════════════════════════


# ── State 0: BK_MEMBER_CHECK — Ask if user has a member card ──────────────────

async def bk_member_check_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle member card Yes/No — works with both ReplyKeyboard text and inline callback."""
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
            await query.edit_message_text("👤 နာမည်ရိုက်ထည့်ပေးပါ:")
            return BK_NAME
        else:
            await query.edit_message_text("❌ Invalid option — please try again.")
            return ConversationHandler.END

    return BK_MEMBER_CHECK


async def _handle_member_yes_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shared logic when user says they have a member card."""
    phone = await _get_user_phone(update, context)
    if phone:
        members = await _api._fetch_members()
        phone_norm = phone.replace(" ", "").replace("-", "")
        matched = [
            (mid, m) for mid, m in members.items()
            if (m.get("phone") or "").replace(" ", "").replace("-", "") == phone_norm
        ]
        if len(matched) == 1:
            mid, m = matched[0]
            context.user_data["bk_member_id"] = mid
            context.user_data["bk_name"] = m.get("name", "")
            context.user_data["bk_phone"] = phone
            context.user_data["bk_member_data"] = m
            context.user_data["bk_expected_phone"] = m.get("phone", "")
            msg = (
                f"👤 Member found: *{m.get('name', '?')}*\n"
                f"📞 ဖုန်းနံပါတ်နောက်ဆုံး ၃/၄ လုံးရိုက်ပါ (သို့မဟုတ် 'no' ရိုက်ပြီး ကျော်ပါ):"
            )
            if update.message:
                await update.message.reply_text(msg, parse_mode="Markdown")
            else:
                await update.callback_query.edit_message_text(msg, parse_mode="Markdown")
            return BK_PHONE_VERIFY
        elif len(matched) > 1:
            buttons = []
            for mid, m in matched[:10]:
                label = f"{m.get('name','?')} ({m.get('phone','?')})"
                buttons.append([InlineKeyboardButton(label, callback_data=f"bk_sel:{mid}")])
            buttons.append([InlineKeyboardButton("❌ မရှိပါ", callback_data="bk_sel:none")])
            msg = "👥 သင့် member profile *များစွာ* တွေ့ရှိပါသည် — ရွေးပေးပါ:"
            if update.message:
                await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
            else:
                await update.callback_query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
            return BK_MEMBER_SELECT

    # No phone match — go directly to phone verification
    context.user_data["bk_member_id"] = None
    context.user_data["bk_expected_phone"] = None
    msg = "📞 Phone last digits (or type no to skip):"
    if update.message:
        await update.message.reply_text(msg)
    else:
        await update.callback_query.edit_message_text(msg)
    return BK_PHONE_VERIFY


# ── State 1: BK_MEMBER_SELECT — Select a member ──────────────────────────────

async def bk_member_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle member selection — works with both inline callback and text input."""
    text = (update.message.text or "").strip() if update.message else ""

    # Check for menu buttons
    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

    # Handle cancel
    if not update.callback_query and text == BTN_CANCEL:
        return await _cleanup_and_end(update, context)

    # Handle callback (existing inline path)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""
        if data.startswith("bk_sel:"):
            mid = data.split(":", 1)[1]
            if mid == "none":
                await query.edit_message_text("👤 နာမည်ရိုက်ထည့်ပေးပါ:")
                return BK_NAME
            return await _lookup_and_confirm_member(update, context, mid)

    # Text input: member ID or "no"
    NO_MEMBER_TEXTS = {"မရှိပါ", "မရှိဘူး", "မရှိဘူး (Guest)", "Guest"}
    if text.lower() == "no" or text in NO_MEMBER_TEXTS or text.lower() in {t.lower() for t in NO_MEMBER_TEXTS}:
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
    msg = (
        f"👤 *{m.get('name','?')}*\n"
        f"📞 ဖုန်းနံပါတ် နောက်ဆုံး ၄ လုံး: *...{masked}*\n\n"
        f"မှန်ကန်ပါက ✅ နှိပ်ပါ — သို့မဟုတ် ဖုန်းနံပါတ် အပြည့် ရိုက်ထည့်ပါ"
    )
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=_rp_kb([[BTN_CONFIRM_YES, BTN_CONFIRM_NO]]))
    elif update.callback_query:
        await update.callback_query.edit_message_text(msg, parse_mode="Markdown", reply_markup=_rp_kb([[BTN_CONFIRM_YES, BTN_CONFIRM_NO]]))
    return BK_DATA_CONFIRM


# ── State 2: BK_PHONE_VERIFY — Verify phone number ──────────────────────────

async def bk_phone_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify phone number entered by user."""
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == BTN_CANCEL:
        return await _cleanup_and_end(update, context)

    # Allow skip to manual entry
    NO_MEMBER_TEXTS = {"မရှိပါ", "မရှိဘူး", "မရှိဘူး (Guest)", "Guest"}
    if text.lower() == "no" or text in NO_MEMBER_TEXTS or text.lower() in {t.lower() for t in NO_MEMBER_TEXTS}:
        await update.message.reply_text("👤 နာမည်အမှန် ရိုက်ထည့်ပေးပါ:")
        context.user_data.pop("bk_member_id", None)
        context.user_data.pop("bk_member_data", None)
        context.user_data.pop("bk_expected_phone", None)
        return BK_NAME

    expected_phone = context.user_data.get("bk_expected_phone", "")
    member = context.user_data.get("bk_member_data", {})
    if not expected_phone:
        expected_phone = member.get("phone", "")

    if text == expected_phone or (len(text) >= 3 and expected_phone.endswith(text)):
        await update.message.reply_text(
            "✅ ဖုန်းနံပါတ် မှန်ကန်ပါသည်!",
            reply_markup=_rp_kb([[BTN_CONFIRM_YES, BTN_CONFIRM_NO]]),
        )
        return BK_DATA_CONFIRM
    else:
        await update.message.reply_text(
            "❌ ဖုန်းနံပါတ် မကိုက်ညီပါ — ထပ်ကြိုးစားပါ (သို့မဟုတ် 'no' ရိုက်ပြီး skip လုပ်ပါ):",
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

        if text in (BTN_CONFIRM_YES, "✅ မှန်ပါသည်"):
            context.user_data.pop("bk_member_id", None)
            context.user_data.pop("bk_member_data", None)
            await update.message.reply_text(
                "📅 ဘိုကင်လုပ်မည့် ရက်ရွေးပါ:",
                reply_markup=_make_date_keyboard(),
            )
            return BK_DATE
        elif text in (BTN_CONFIRM_NO, "❌ မဟုတ်ပါ"):
            context.user_data.pop("bk_member_id", None)
            context.user_data.pop("bk_member_data", None)
            await update.message.reply_text("👤 နာမည်အမှန် ရိုက်ထည့်ပေးပါ:")
            return BK_NAME
        elif text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)
        return BK_DATA_CONFIRM

    # Callback path (keep for safety)
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_dc:yes":
        context.user_data.pop("bk_member_id", None)
        context.user_data.pop("bk_member_data", None)
        await query.edit_message_text("📅 ဘိုကင်လုပ်မည့် ရက်ရွေးပါ:")
        await query.message.reply_text(
            "📅 ဘယ်ရက်မှာ လာဆော့မလဲ?",
            reply_markup=_make_date_keyboard(),
        )
        return BK_DATE
    elif data == "bk_dc:no":
        context.user_data.pop("bk_member_id", None)
        context.user_data.pop("bk_member_data", None)
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

    if not text or len(text) < 1:
        await update.message.reply_text("နာမည် ထည့်ပေးပါ:")
        return BK_NAME

    context.user_data["bk_name"] = text
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

        # Try to extract date from text like "ယနေ့ (Today)  2026-05-30"
        date_str = _extract_date_from_text(text)
        if not date_str:
            await update.message.reply_text(
                "📅 ကျေးဇူးပြုပြီး ရက်စွဲကို ရွေးချယ်ပါ:",
                reply_markup=_make_date_keyboard(),
            )
            return BK_DATE

        context.user_data["bk_date"] = date_str
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
            if OPEN_HOUR <= hour <= CLOSE_HOUR and minute in (0, 30) and hour != CLOSE_HOUR:
                time_str = f"{hour:02d}:{minute:02d}"
                context.user_data["bk_time"] = time_str
                await update.message.reply_text(
                    f"⏰ Custom Time: *{time_str}*\n\n🎮 Console အမျိုးအစား ရွေးပါ:",
                    parse_mode="Markdown",
                    reply_markup=_make_console_keyboard(),
                )
                return BK_CONSOLE
            else:
                await update.message.reply_text(
                    f"⚠️ မမှန်ကန်သော အချိန် — {OPEN_HOUR}:00 မှ {CLOSE_HOUR}:00 အတွင်း "
                    "နာရီဝက် သို့မဟုတ် နာရီပြည့်ဖြင့် ထည့်ပေးပါ",
                )
                return BK_TIME
        else:
            # Invalid input — show time keyboard again
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
    """Handle console type selection — works with ReplyKeyboard text and inline callback."""
    text = (update.message.text or "").strip() if update.message else ""

    # Handle ReplyKeyboard text
    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        if text in CONSOLE_TYPES:
            context.user_data["bk_console"] = text
            await update.message.reply_text(
                f"🎮 Console: *{text}*\n\n⏱️ ကြာချိန် ရွေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_duration_keyboard(),
            )
            return BK_DURATION
        elif text in (BTN_NOT_SURE, "🤷 မရွေးတတ်ပါ"):
            context.user_data["bk_console"] = "Any"
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
            if con == "not_sure":
                context.user_data["bk_console"] = "Any"
            else:
                context.user_data["bk_console"] = con
            await query.edit_message_text(
                f"🎮 Console: *{context.user_data['bk_console']}*\n\n"
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
    """Handle duration selection — works with ReplyKeyboard text and inline callback."""
    text = (update.message.text or "").strip() if update.message else ""

    # Handle ReplyKeyboard text
    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        # Parse "X mins" format
        m = re.match(r'^(\d+)\s*mins?$', text)
        if m:
            mins = int(m.group(1))
            if mins in [int(d.split()[0]) for d in DURATION_OPTS]:
                context.user_data["bk_duration_mins"] = mins
                await update.message.reply_text("🕹️ Game list ဆွဲနေသည်...")

                games = await _api._fetch_games(context.user_data.get("bk_console", ""))
                context.user_data["_bk_game_list"] = games
                context.user_data["_bk_game_page"] = 0

                if not games:
                    await update.message.reply_text(
                        "⚠️ Game list မရဘူး — skip လုပ်မလား?",
                        reply_markup=_rp_kb([[BTN_SKIP]]),
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
                    reply_markup=_rp_kb([[BTN_SKIP]]),
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
    """Handle game selection — works with ReplyKeyboard text and inline callback."""
    text = (update.message.text or "").strip() if update.message else ""

    # Handle ReplyKeyboard text
    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        if text in (BTN_NOT_SURE, "🤷 မရွေးတတ်ပါ"):
            context.user_data["bk_game"] = "Any"
            summary = _format_booking_summary(context)
            await update.message.reply_text(
                f"🕹️ Game: *Any*\n\n💻 {summary}\n\n\u2705 Confirm \u101c\u102f\u1015\u103a\u1019\u101c\u102c\u1038?",
                parse_mode="Markdown",
                reply_markup=_make_confirm_keyboard(),
            )
            return BK_CONFIRM

        if text == BTN_SKIP:
            context.user_data["bk_game"] = "Any"
            summary = _format_booking_summary(context)
            await update.message.reply_text(
                f"🕹️ Game: *Any*\n\n💻 {summary}\n\n\u2705 Confirm \u101c\u102f\u1015\u103a\u1019\u101c\u102c\u1038?",
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
        # Try exact match first, then partial
        matched = [g for g in games if g[:50] == text[:50]]
        if matched:
            context.user_data["bk_game"] = matched[0]
        else:
            context.user_data["bk_game"] = text[:50]

        summary = _format_booking_summary(context)
        await update.message.reply_text(
            f"🕹️ Game: *{context.user_data['bk_game']}*\n\n💻 {summary}\n\n\u2705 Confirm \u101c\u102f\u1015\u103a\u1019\u101c\u102c\u1038?",
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
            if game == "not_sure":
                context.user_data["bk_game"] = "Any"
            else:
                context.user_data["bk_game"] = game

            summary = _format_booking_summary(context)
            await query.edit_message_text(
                f"🕹️ Game: *{context.user_data['bk_game']}*\n\n💻 {summary}\n\n\u2705 Confirm \u101c\u102f\u1015\u103a\u1019\u101c\u102c\u1038?",
                parse_mode="Markdown",
                reply_markup=_make_confirm_keyboard(),
            )
            return BK_CONFIRM

        await query.edit_message_text("❌ Invalid game selection.")
        return BK_GAME

    return BK_GAME


# ── State 11: BK_CONSOLE_PREF — Console preference ─────────────────────────

async def bk_console_pref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle console preference selection — works with ReplyKeyboard text and inline callback."""
    text = (update.message.text or "").strip() if update.message else ""

    # Handle ReplyKeyboard text
    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

        if text in CONSOLE_TYPES:
            context.user_data["bk_console_pref"] = text
        elif text in (BTN_NOT_SURE, "🤷 မရွေးတတ်ပါ"):
            context.user_data["bk_console_pref"] = "Any"
        else:
            await update.message.reply_text(
                "💻 ကျေးဇူးပြုပြီး console preference ရွေးပါ:",
                reply_markup=_make_console_keyboard(),
            )
            return BK_CONSOLE_PREF

        summary = _format_booking_summary(context)
        await update.message.reply_text(
            summary + "\n\n✅ Confirm လုပ်မလား?",
            parse_mode="Markdown",
            reply_markup=_make_confirm_keyboard(),
        )
        return BK_CONFIRM

    # Callback path (keep for safety)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data == "bk_con:cancel":
            return await _cleanup_and_end(update, context)

        if data.startswith("bk_con:"):
            pref = data.split(":", 1)[1]
            if pref == "not_sure":
                context.user_data["bk_console_pref"] = "Any"
            else:
                context.user_data["bk_console_pref"] = pref

            summary = _format_booking_summary(context)
            await query.edit_message_text(
                summary + "\n\n✅ Confirm လုပ်မလား?",
                parse_mode="Markdown",
                reply_markup=_make_confirm_keyboard(),
            )
            return BK_CONFIRM

        await query.edit_message_text("❌ Invalid preference selection.")
        return BK_CONSOLE_PREF

    return BK_CONSOLE_PREF


# ── State 12: BK_CONFIRM — Confirm booking and submit ──────────────────────

async def bk_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle booking confirmation and submission to API."""
    text = (update.message.text or "").strip() if update.message else ""

    # Handle ReplyKeyboard text
    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)

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
            return await _cleanup_and_end(update, context)

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
