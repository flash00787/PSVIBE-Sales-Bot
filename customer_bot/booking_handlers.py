"""
PS Vibe Customer Bot — Booking Conversation Handlers
Implements all 16 booking flow states (previously stubbed with lambda u,c: None).
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from . import api as _api
from .handlers import (
    BK_MEMBER_CHECK, BK_MEMBER_SELECT, BK_PHONE_VERIFY, BK_DATA_CONFIRM,
    BK_NAME, BK_PHONE, BK_DATE, BK_TIME,
    BK_CONSOLE, BK_DURATION, BK_GAME, BK_CONSOLE_PREF, BK_CONFIRM,
    BK_DUP_WARN, BK_DISC_WARN, BK_CON_CONFLICT,
    BK_END, MAIN_MENU_KB, CONSOLE_TYPES, DURATION_OPTS,
)
from .data.prompts import today_mmt, OPEN_HOUR, CLOSE_HOUR

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
TODAY = today_mmt
BK_END = -1  # sentinel for end

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_date_keyboard() -> InlineKeyboardMarkup:
    """Build date selection keyboard: Today, Tomorrow, Day After."""
    today = datetime.strptime(today_mmt(), "%Y-%m-%d")
    dates = [
        (today, "ယနေ့ (Today)"),
        (today + timedelta(days=1), "မနက်ဖြန် (Tomorrow)"),
        (today + timedelta(days=2), "သဘက်ခါ (Day After)"),
    ]
    buttons = []
    for d, label in dates:
        ds = d.strftime("%Y-%m-%d")
        buttons.append([InlineKeyboardButton(label, callback_data=f"bkdate:{ds}")])
    buttons.append([InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="bkdate:cancel")])
    return InlineKeyboardMarkup(buttons)


def _make_time_keyboard(free_slots: list[str]) -> InlineKeyboardMarkup:
    """Build time slot keyboard for available hours."""
    buttons = []
    row = []
    for slot in free_slots[:12]:  # max 12 slots shown
        row.append(InlineKeyboardButton(slot, callback_data=f"bktime:{slot}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("✏️ Custom Time", callback_data="bk_custom:ask")])
    buttons.append([InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="bktime:cancel")])
    return InlineKeyboardMarkup(buttons)


def _make_console_keyboard() -> InlineKeyboardMarkup:
    """Build console type selection keyboard."""
    buttons = [[InlineKeyboardButton(t, callback_data=f"bk_con:{t}")] for t in CONSOLE_TYPES]
    buttons.append([InlineKeyboardButton("🤷 မရွေးတတ်ပါ", callback_data="bk_con:not_sure")])
    buttons.append([InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="bk_con:cancel")])
    return InlineKeyboardMarkup(buttons)


def _make_duration_keyboard() -> InlineKeyboardMarkup:
    """Build duration selection keyboard."""
    buttons = []
    row = []
    for i, dur in enumerate(DURATION_OPTS):
        mins = int(dur.split()[0])
        row.append(InlineKeyboardButton(dur, callback_data=f"bk_dur:{mins}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="bk_dur:cancel")])
    return InlineKeyboardMarkup(buttons)


def _make_game_keyboard(games: list[str], page: int = 0, per_page: int = 6) -> InlineKeyboardMarkup:
    """Build game selection keyboard with pagination."""
    start = page * per_page
    end = start + per_page
    page_games = games[start:end]
    buttons = [[InlineKeyboardButton(g[:50], callback_data=f"bk_game:{g[:50]}")] for g in page_games]

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Previous", callback_data=f"bk_game_page:{page - 1}"))
    if end < len(games):
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"bk_game_page:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("🤷 မရွေးတတ်ပါ", callback_data="bk_game:not_sure")])
    buttons.append([InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="bk_game:cancel")])
    return InlineKeyboardMarkup(buttons)


def _make_confirm_keyboard() -> InlineKeyboardMarkup:
    """Build confirmation keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Booking", callback_data="bk_ok:yes")],
        [InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="bk_ok:no")],
    ])


def _make_warning_keyboard(continue_cb: str, back_cb: str = "bk_ok:no") -> InlineKeyboardMarkup:
    """Build warning keyboard with 'Continue Anyway' and 'Go Back'."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚠️ ဒါပေမဲ့ ဆက်တင်မည်", callback_data=continue_cb)],
        [InlineKeyboardButton("🔙 မတင်တော့ပါ", callback_data=back_cb)],
    ])


async def _get_user_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    """Get user's phone from existing bookings or context."""
    uid = str(update.effective_user.id)
    phone = context.user_data.get("bk_phone")
    if not phone:
        phone = await _api._get_linked_phone(int(uid)) if uid.isdigit() else None
    return phone


async def _get_available_slots(date_str: str) -> list[str]:
    """Get available time slots for a given date."""
    # Get confirmed bookings for the date
    try:
        bks = await _api._api_get(f"bookings/search?date={date_str}&status=confirmed")
    except Exception:
        bks = []
    bks = bks if isinstance(bks, list) else []
    booked_slots = {b.get("timeSlot", "") for b in bks}

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


# ══════════════════════════════════════════════════════════════════════════════
#  Booking State Handlers
# ══════════════════════════════════════════════════════════════════════════════


# ── State 0: BK_MEMBER_CHECK — Ask if user has a member card ──────────────────

async def bk_member_check_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called after cmd_book — present member card Yes/No."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    member_id = context.user_data.get("bk_member_id")

    if data == "bk_mem:yes":
        # User says they have a member card — search by phone
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
                await query.edit_message_text(
                    f"👤 Member found: *{m.get('name', '?')}*\n📞 Phone: *{phone}*\n\n✅ မှန်ကန်ပါသလား?",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ မှန်ပါသည်", callback_data="bk_dc:yes")],
                        [InlineKeyboardButton("❌ မဟုတ်ပါ", callback_data="bk_dc:no")],
                    ]),
                )
                return BK_DATA_CONFIRM
            elif len(matched) > 1:
                # Multiple members — show selection
                buttons = []
                for mid, m in matched[:10]:
                    label = f"{m.get('name','?')} ({m.get('phone','?')})"
                    buttons.append([InlineKeyboardButton(label, callback_data=f"bk_sel:{mid}")])
                buttons.append([InlineKeyboardButton("❌ မရှိပါ", callback_data="bk_sel:none")])
                await query.edit_message_text(
                    "👥 သင့် member profile *များစွာ* တွေ့ရှိပါသည် — ရွေးပေးပါ:",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
                return BK_MEMBER_SELECT
        # No phone match — let them pick member by ID
        await query.edit_message_text(
            "📋 Member ID ရိုက်ထည့်ပေးပါ (သို့မဟုတ် member card နံပါတ်):\n\n"
            "_Member card မရှိပါက 'no' ဟုရိုက်ပါ_",
            parse_mode="Markdown",
        )
        return BK_MEMBER_SELECT

    elif data == "bk_mem:no":
        # No member card — go to name entry
        await query.edit_message_text(
            "👤 နာမည်ရိုက်ထည့်ပေးပါ:",
        )
        return BK_NAME
    else:
        await query.edit_message_text("❌ Invalid option — please try again.")
        return ConversationHandler.END


# ── State 1: BK_MEMBER_SELECT — Select a member ──────────────────────────────

async def bk_member_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle member selection callback or manual ID input."""
    # Check if it's a callback query
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data.startswith("bk_sel:"):
            mid = data.split(":", 1)[1]
            if mid == "none":
                await query.edit_message_text("👤 နာမည်ရိုက်ထည့်ပေးပါ:")
                return BK_NAME

            # Look up member
            members = await _api._fetch_members()
            m = members.get(mid)
            if m:
                context.user_data["bk_member_id"] = mid
                context.user_data["bk_name"] = m.get("name", "")
                context.user_data["bk_phone"] = m.get("phone", "")
                context.user_data["bk_member_data"] = m
                # Ask for phone verification
                phone = m.get("phone", "")
                masked = phone[-4:] if len(phone) >= 4 else phone
                await query.edit_message_text(
                    f"👤 *{m.get('name','?')}*\n"
                    f"📞 ဖုန်းနံပါတ် နောက်ဆုံး ၄ လုံး: *...{masked}*\n\n"
                    f"မှန်ကန်ပါက ✅ နှိပ်ပါ — သို့မဟုတ် ဖုန်းနံပါတ် အပြည့် ရိုက်ထည့်ပါ",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ မှန်ပါသည်", callback_data="bk_dc:yes")],
                        [InlineKeyboardButton("❌ မဟုတ်ပါ", callback_data="bk_dc:no")],
                    ]),
                )
                return BK_DATA_CONFIRM
            else:
                await query.edit_message_text("❌ Member မတွေ့ပါ — နာမည်ရိုက်ထည့်ပါ:")
                return BK_NAME
        else:
            await query.edit_message_text("❌ Invalid selection.")
            return ConversationHandler.END

    # MessageHandler: manual member ID input
    text = (update.message.text or "").strip().lower()
    if text == "no" or text == "မရှိပါ":
        await update.message.reply_text("👤 နာမည်ရိုက်ထည့်ပေးပါ:")
        return BK_NAME

    # Try to look up by member ID
    members = await _api._fetch_members()
    m = members.get(text)
    if m:
        context.user_data["bk_member_id"] = text
        context.user_data["bk_name"] = m.get("name", "")
        context.user_data["bk_phone"] = m.get("phone", "")
        context.user_data["bk_member_data"] = m
        phone = m.get("phone", "")
        masked = phone[-4:] if len(phone) >= 4 else phone
        await update.message.reply_text(
            f"👤 *{m.get('name','?')}*\n"
            f"📞 ဖုန်းနံပါတ် နောက်ဆုံး ၄ လုံး: *...{masked}*\n\n"
            f"မှန်ကန်ပါက ✅ နှိပ်ပါ — သို့မဟုတ် ဖုန်းနံပါတ် အပြည့် ရိုက်ထည့်ပါ",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ မှန်ပါသည်", callback_data="bk_dc:yes")],
                [InlineKeyboardButton("❌ မဟုတ်ပါ", callback_data="bk_dc:no")],
            ]),
        )
        return BK_DATA_CONFIRM
    else:
        await update.message.reply_text(
            f"❌ Member ID `{text}` မတွေ့ပါ\n"
            "ထပ်ကြိုးစားပါ — သို့မဟုတ် 'no' ဟုရိုက်ပြီး member မရှိဘဲ ဆက်လုပ်ပါ",
            parse_mode="Markdown",
        )
        return BK_MEMBER_SELECT


# ── State 2: BK_PHONE_VERIFY — Verify phone number ──────────────────────────

async def bk_phone_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify phone number entered by user."""
    member = context.user_data.get("bk_member_data", {})
    expected_phone = member.get("phone", "")
    text = (update.message.text or "").strip()

    if text == expected_phone or (len(text) >= 4 and expected_phone.endswith(text)):
        # Phone verified
        await update.message.reply_text(
            "✅ ဖုန်းနံပါတ် မှန်ကန်ပါသည်!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Confirm & Continue", callback_data="bk_dc:yes")],
                [InlineKeyboardButton("❌ မဟုတ်ပါ", callback_data="bk_dc:no")],
            ]),
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
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_dc:yes":
        # Confirmed — skip to date selection
        await query.edit_message_text("📅 ဘိုကင်လုပ်မည့် ရက်ရွေးပါ:")
        await query.message.reply_text(
            "📅 ဘယ်ရက်မှာ လာဆော့မလဲ?",
            reply_markup=_make_date_keyboard(),
        )
        return BK_DATE
    elif data == "bk_dc:no":
        # Not correct — go to manual name entry
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
    if not text:
        await update.message.reply_text("ဖုန်းနံပါတ် ထည့်ပေးပါ:")
        return BK_PHONE

    # Basic validation: allow digits, spaces, +, -
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
    """Handle date selection callback."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bkdate:cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    if data.startswith("bkdate:"):
        date_str = data.split(":", 1)[1]
        context.user_data["bk_date"] = date_str

        # Get available slots
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
    """Handle time slot selection callback."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bktime:cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

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

    if data.startswith("bk_custom:"):
        # This would handle the custom time message input
        # But the main.py routes bk_custom: to CallbackQueryHandler, so this catches
        # the actual text input would come through BK_END or a separate handler
        pass

    # Check if it's a text message with custom time
    if update.message:
        text = (update.message.text or "").strip()
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
            await update.message.reply_text("⚠️ HH:MM format ဖြင့် ရိုက်ထည့်ပါ (ဥပမာ: 14:00)")
            return BK_TIME

    await query.edit_message_text("❌ Invalid time selection.")
    return BK_TIME


# ── State 8: BK_CONSOLE — Select console type ──────────────────────────────

async def bk_console_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle console type selection."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_con:cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

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


# ── State 9: BK_DURATION — Select duration ─────────────────────────────────

async def bk_duration_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle duration selection."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_dur:cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    if data.startswith("bk_dur:"):
        try:
            mins = int(data.split(":", 1)[1])
        except ValueError:
            await query.edit_message_text("❌ Invalid duration.")
            return BK_DURATION

        context.user_data["bk_duration_mins"] = mins
        await query.edit_message_text("🕹️ Game list ဆွဲနေသည်...")

        # Fetch games
        games = await _api._fetch_games(context.user_data.get("bk_console", ""))
        context.user_data["_bk_game_list"] = games
        context.user_data["_bk_game_page"] = 0

        if not games:
            await query.edit_message_text(
                "⚠️ Game list မရဘူး — skip လုပ်မလား?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⏭️ Skip", callback_data="bk_game:not_sure")],
                ]),
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


# ── State 10: BK_GAME — Select game ─────────────────────────────────────

async def bk_game_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game selection callback."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_game:cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

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

        await query.edit_message_text(
            f"🕹️ Game: *{context.user_data['bk_game']}*\n\n"
            "💻 Console preference ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=_make_console_keyboard(),
        )
        return BK_CONSOLE_PREF

    await query.edit_message_text("❌ Invalid game selection.")
    return BK_GAME


# ── State 11: BK_CONSOLE_PREF — Console preference ─────────────────────────

async def bk_console_pref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle console preference selection."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_cp:cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    if data.startswith("bk_cp:"):
        pref = data.split(":", 1)[1]
        if pref == "not_sure":
            context.user_data["bk_console_pref"] = "Any"
        else:
            context.user_data["bk_console_pref"] = pref

        # Show booking summary
        summary = _format_booking_summary(context)
        await query.edit_message_text(
            summary + "\n\n✅ Confirm လုပ်မလား?",
            parse_mode="Markdown",
            reply_markup=_make_confirm_keyboard(),
        )
        return BK_CONFIRM

    await query.edit_message_text("❌ Invalid preference selection.")
    return BK_CONSOLE_PREF


# ── State 12: BK_CONFIRM — Confirm booking and submit ──────────────────────

async def bk_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle booking confirmation and submission to API."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_ok:no":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    if data == "bk_ok:yes":
        await query.edit_message_text("⏳ Booking တင်နေသည်...")

        user = update.effective_user
        uid = str(user.id) if user else ""

        # Check for duplicate booking
        date_str = context.user_data.get("bk_date", "")
        time_str = context.user_data.get("bk_time", "")
        try:
            existing = await _api._api_get(
                f"bookings/search?telegram_chat_id={uid}&date={date_str}&status=confirmed"
            )
            existing = existing if isinstance(existing, list) else []
            dupes = [b for b in existing if b.get("timeSlot") == time_str]
            if dupes:
                await query.edit_message_text(
                    "⚠️ *Duplicate Booking Detected!*\n\n"
                    f"📅 {date_str} ⏰ {time_str} တွင် booking ရှိပြီးသားပါ\n\n"
                    "ဒါပေမဲ့ ဆက်တင်မလား?",
                    parse_mode="Markdown",
                    reply_markup=_make_warning_keyboard("bk_warn:dup_ok"),
                )
                return BK_DUP_WARN
        except Exception:
            pass

        # Submit booking
        payload = {
            "customerName": context.user_data.get("bk_name", ""),
            "phone": context.user_data.get("bk_phone", ""),
            "date": date_str,
            "timeSlot": time_str,
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
                await query.edit_message_text(
                    f"✅ *Booking Confirmed!*\n\n"
                    f"🎫 Booking #{bk_id}\n"
                    f"📅 {date_str}  ⏰ {time_str}\n"
                    f"🎮 {payload['consoleType']}  ⏱️ {payload['durationMins']} mins\n"
                    f"🕹️ {payload['gameName']}\n\n"
                    f"_Staff မှ confirm လုပ်ပြီးပါက အကြောင်းကြားပါမည်_ 🎮",
                    parse_mode="Markdown",
                )
                # Notify staff
                asyncio.create_task(_api.track_usage(user, "booking_created"))
                return ConversationHandler.END
            else:
                await query.edit_message_text(
                    "❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ သို့မဟုတ် Admin ကို ဆက်သွယ်ပါ",
                )
                return ConversationHandler.END
        except Exception as e:
            logger.error("Booking submission failed: %s", e)
            await query.edit_message_text(
                "❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ သို့မဟုတ် Admin ကို ဆက်သွယ်ပါ",
            )
            return ConversationHandler.END

    await query.edit_message_text("❌ Invalid confirmation.")
    return BK_CONFIRM


# ── State 13: BK_DUP_WARN — Duplicate booking warning ──────────────────────

async def bk_dup_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle duplicate booking warning."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_warn:dup_ok":
        # Continue with booking despite duplicate
        await query.edit_message_text("⏳ Booking တင်နေသည် (duplicate warning overridden)...")

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
                await query.edit_message_text(
                    f"✅ *Booking Confirmed!*\n\n"
                    f"🎫 Booking #{bk_id}\n"
                    f"📅 {payload['date']}  ⏰ {payload['timeSlot']}\n"
                    f"🎮 {payload['consoleType']}  ⏱️ {payload['durationMins']} mins\n\n"
                    f"_Staff မှ confirm လုပ်ပြီးပါက အကြောင်းကြားပါမည်_ 🎮",
                    parse_mode="Markdown",
                )
            else:
                await query.edit_message_text("❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ")
        except Exception as e:
            logger.error("Booking submission (dup override) failed: %s", e)
            await query.edit_message_text("❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ")

        return ConversationHandler.END

    elif data == "bk_ok:no":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    await query.edit_message_text("❌ Invalid option.")
    return BK_DUP_WARN


# ── State 14: BK_DISC_WARN — Discount warning ─────────────────────────────

async def bk_disc_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle discount/conflict warning for booking."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_warn:disc_ok":
        # Proceed to confirmation
        summary = _format_booking_summary(context)
        await query.edit_message_text(
            summary + "\n\n⚠️ Discount conflicted but continuing...\n✅ Confirm လုပ်မလား?",
            parse_mode="Markdown",
            reply_markup=_make_confirm_keyboard(),
        )
        return BK_CONFIRM

    elif data == "bk_ok:no":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    await query.edit_message_text("❌ Invalid option.")
    return BK_DISC_WARN


# ── State 15: BK_CON_CONFLICT — Console conflict warning ──────────────────

async def bk_con_conflict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle console conflict warning."""
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_warn:conf_ok":
        # Proceed despite conflict
        summary = _format_booking_summary(context)
        await query.edit_message_text(
            summary + "\n\n⚠️ Console conflict detected but continuing...\n✅ Confirm လုပ်မလား?",
            parse_mode="Markdown",
            reply_markup=_make_confirm_keyboard(),
        )
        return BK_CONFIRM

    elif data == "bk_warn:change_time":
        # Go back to time selection
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
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    await query.edit_message_text("❌ Invalid option.")
    return BK_CON_CONFLICT




# ── State 7: BK_TIME (text input) — Custom time text entry ─────────────────

async def bk_time_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom time text input in BK_TIME state (HH:MM format)."""
    text = (update.message.text or "").strip()
    logger.info("bk_time_text_input received: %s", text)

    m = re.match(r'^(\d{1,2}):(\d{2})$', text)
    if m:
        hour, minute = int(m.group(1)), int(m.group(2))
        if OPEN_HOUR <= hour <= CLOSE_HOUR and minute in (0, 30) and hour != CLOSE_HOUR:
            time_str = f"{hour:02d}:{minute:02d}"
            context.user_data["bk_time"] = time_str
            await update.message.reply_text(
                f"\u23f0 Custom Time: *{time_str}*\n\n"
                "\U0001f3ae Console \u1021\u1019\u103b\u102d\u102f\u1038\u1021\u1005\u102c\u1038 \u101b\u103d\u1031\u1038\u1015\u102b:",
                parse_mode="Markdown",
                reply_markup=_make_console_keyboard(),
            )
            return BK_CONSOLE
        else:
            await update.message.reply_text(
                f"\u26a0\ufe0f \u1019\u1019\u103e\u1014\u103a\u1000\u1014\u103a\u101e\u1031\u102c \u1021\u1001\u103b\u102d\u1014\u103a "
                f"\u2014 {OPEN_HOUR}:00 \u1019\u103e {CLOSE_HOUR}:00 \u1021\u1010\u103d\u1004\u103a\u1038 "
                "\u1014\u102c\u1038\u101b\u102e\u101d\u1000\u103a \u101e\u102d\u102f\u1037\u1019\u101f\u102f\u1010\u103a \u1014\u102c\u1038\u101b\u102e\u1015\u103c\u000a\u1037\u103a\u1016\u103c\u1004\u1037\u103a \u1011\u100a\u1037\u103a\u1015\u1031\u1038\u1015\u102b",
            )
            return BK_TIME
    else:
        await update.message.reply_text(
            "\u26a0\ufe0f HH:MM format \u1016\u103c\u1004\u1037\u103a \u101b\u102d\u102f\u1000\u103a\u1011\u100a\u1037\u103a\u1015\u102b "
            "(\u1025\u1015\u1019\u102c: 14:00, 10:30)",
        )
        return BK_TIME
# ── State -1: BK_END — Fallback handler ────────────────────────────────────

async def bk_end_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fallback handler for BK_END state (sentinel -1)."""
    await update.message.reply_text(
        "Booking session ended. Use 📅 Booking to start a new booking.",
        reply_markup=MAIN_MENU_KB,
    )
    return ConversationHandler.END
