"""
PS Vibe Customer Bot — Handlers: commands, message routing, callback handlers.
"""
import asyncio
import logging
import random
import re
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, Update,
)
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from .data.prompts import (
    now_mmt, today_mmt, OPEN_HOUR, CLOSE_HOUR,
    _detect_sentiment, _detect_booking_intent,
    MORNING_GREETINGS, AFTERNOON_GREETINGS, EVENING_GREETINGS,
    PROMO_INTROS, PROMO_EMPTY, PROMO_CLOSING,
)
from . import api as _api
from .ai import _ai_reply, _detect_ai_bypass, _build_faq_template
from .faq_auto_reply import match_faq as _match_faq

# ── Conversation States ───────────────────────────────────────────────────────
(
    BK_MEMBER_CHECK, BK_MEMBER_SELECT, BK_PHONE_VERIFY, BK_DATA_CONFIRM,
    BK_NAME, BK_PHONE, BK_DATE, BK_TIME,
    BK_CONSOLE, BK_DURATION, BK_GAME, BK_CONSOLE_PREF, BK_CONFIRM,
    BK_DUP_WARN, BK_DISC_WARN, BK_CON_CONFLICT,
) = range(16)
# BK_SPECIFIC_CONSOLE removed — unused state

WL_PREF, WL_NAME, WL_PHONE, WL_CONFIRM = range(100, 104)

# ── Button Labels ─────────────────────────────────────────────────────────────
BTN_BOOK        = "📅 Booking လုပ်မည်"
BTN_STATUS      = "🎮 Console Status"
BTN_MYBOOKINGS  = "📋 My Bookings"
BTN_GAMES       = "🕹️ Game Library"
BTN_RATE        = "💰 Rate"
BTN_HELP_BTN    = "ℹ️ Help"
BTN_REFRESH     = "🔄 Refresh"
BTN_CONTACT     = "📞 Contact"
BTN_LOCATION    = "📍 Location"
BTN_PROMOTIONS  = "🎁 Promotions"
BTN_BALANCE     = "💳 Balance"
BTN_REFER       = "👥 Refer a Friend"

BTN_FOOD        = "🍕 Food Menu"
BTN_CANCEL      = "❌ ပယ်ဖျက်မည်"
BTN_BACK        = "🔙 နောက်သို့"
BTN_CONFIRM     = "✅ Confirm Booking"
BTN_NOT_SURE    = "🤷 မရွေးတတ်ပါ"
BTN_BOOK_ANYWAY = "⚠️ ဒါပေမဲ့ ဆက်တင်မည်"
BTN_BOOK_GOBACK = "🔙 မတင်တော့ပါ"
BTN_DISC_OK     = "✅ ရပါတယ်"
BTN_DISC_GAME   = "🎮 ဂိမ်း ပြောင်းရွေးမည်"
BTN_DISC_TIME   = "⏰ အချိန် ပြောင်းမည်"
BTN_CHANGE_TIME_CONFLICT = "⏰ အချိန် ပြောင်းမည်"

# Main menu keyboard
MAIN_MENU_KB = ReplyKeyboardMarkup([
    [BTN_BOOK,       BTN_STATUS],
    [BTN_MYBOOKINGS, BTN_GAMES],
    [BTN_FOOD,       BTN_RATE],
    [BTN_PROMOTIONS, BTN_BALANCE],
    [BTN_REFER,      BTN_CONTACT],
    [BTN_LOCATION,   BTN_HELP_BTN],
    [BTN_REFRESH],
], resize_keyboard=True)

CONSOLE_TYPES = ["PS5", "PS5 Pro"]
DURATION_OPTS = ["30 mins", "60 mins", "90 mins", "120 mins", "180 mins"]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_hour(h: int) -> str:
    if h == 0: return "12:00 AM"
    if h == 12: return "12:00 PM"
    if h < 12: return f"{h}:00 AM"
    return f"{h - 12}:00 PM"


def _split_message(text: str, limit: int = 4000) -> list[str]:
    """Split long text into Telegram-safe chunks."""
    if len(text) <= limit:
        return [text]
    chunks = []
    while len(text) > limit:
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = text.rfind(" ", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    if text:
        chunks.append(text)
    return chunks


def _step_hdr(step: int, total: int, title: str) -> str:
    bar = "●" * step + "○" * (total - step)
    return f"*Step {step}/{total} — {title}*\n{bar}\n\n"


def _bk_step(d: dict, base: int) -> tuple[int, int]:
    """Determine current booking step."""
    if not d.get("bk_name"):
        return 1, 8
    if not d.get("bk_date"):
        return 2, 8
    if not d.get("bk_time"):
        return 3, 8
    if not d.get("bk_console"):
        return 4, 8
    if not d.get("bk_duration_mins"):
        return 5, 8
    if not d.get("bk_game"):
        return 6, 8
    if not d.get("bk_console_pref"):
        return 7, 8
    return 8, 8


async def _bk_intercept_menu(text: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if text is a menu button.

    Returns ConversationHandler.END for one-shot commands,
    BK_MEMBER_CHECK for booking (to continue conversation flow).
    """
    menu_actions = {
        BTN_STATUS:     cmd_console_status,
        BTN_MYBOOKINGS: cmd_mybookings,
        BTN_GAMES:      cmd_game_library,
        BTN_FOOD:       cmd_food_menu,
        BTN_HELP_BTN:   cmd_help,
        BTN_RATE:       cmd_rate,
        BTN_REFRESH:    cmd_refresh,
        BTN_CONTACT:    cmd_contact,
        BTN_LOCATION:   cmd_location,
        BTN_PROMOTIONS: cmd_promotions,
        BTN_BALANCE:    cmd_balance,
        BTN_REFER:      cmd_refer,
        BTN_BOOK:       cmd_book,
    }
    if text in menu_actions:
        next_state = await menu_actions[text](update, context)
        # If cmd_book returns BK_MEMBER_CHECK, preserve it for conversation flow
        if text == BTN_BOOK and next_state is not None:
            return next_state
        return ConversationHandler.END
    return None


# ── Main Menu ─────────────────────────────────────────────────────────────────

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to PS Vibe!* 🎮\n_⏰ Open daily — 9:00 AM to 9:00 PM_",
        parse_mode="Markdown",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  Command Handlers
# ══════════════════════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ── Referral deep-link parsing (e.g., ?start=ref_12345) ──
    referred_by = None
    if context.args and len(context.args) > 0:
        arg = context.args[0]
        if arg.startswith("ref_"):
            referrer_id = arg[4:]  # Extract "12345" from "ref_12345"
            context.user_data["referred_by"] = referrer_id
            referred_by = referrer_id
            # Fire-and-forget: track referral via API
            asyncio.create_task(_api._api_post("track_referral", {
                "referrer_id": referrer_id,
                "referred_user_id": str(update.effective_user.id),
                "referred_username": update.effective_user.username or "",
            }))

    asyncio.create_task(_api.track_usage(update.effective_user, "session_start", detail="User started the bot"))
    name = update.effective_user.first_name or "ညီ/မ"
    uid  = str(update.effective_user.id)

    # Check for today active bookings (exclude cancelled/rejected)
    today_bks_raw = await _api._api_get(f"search-bookings?telegram_chat_id={uid}")
    today_bks = []
    if isinstance(today_bks_raw, dict) and "bookings" in today_bks_raw:
        today_bks = [b for b in today_bks_raw["bookings"] if str(b.get("status", "")).lower() in ("pending", "confirmed", "active")]
    elif isinstance(today_bks_raw, list):
        today_bks = [b for b in today_bks_raw if str(b.get("status", "")).lower() in ("pending", "confirmed", "active")]

    banner = ""
    if today_bks:
        b = today_bks[0]
        banner = (
            f"\n🎟️ *ယနေ့ Booking ရှိသည်း*\n"
            f"⏰ {b.get('timeSlot','?')}  🎮 {b.get('consoleType','')}  "
            f"🕹️ {b.get('gameName') or '—'}\n"
            f"📌 {'Confirmed' if b.get('status')=='confirmed' else b.get('status','')}\n"
        )

    mmt_now = now_mmt()
    hour = mmt_now.hour
    if hour < 12:
        time_greet = random.choice([
            f"မင်္ဂလာနံနက်ခင်းပါဗျ *{name}*! စောစောစီးစီး ဂိမ်းဆော့ဖို့ အားအင်အပြည့်ပဲလား? 😉",
            f"ဟိုင်း *{name}*! မင်္ဂလာရှိတဲ့ မနက်ခင်းလေးပါ။ ဒီနေ့ ဘာဂိမ်းနဲ့ စမလဲ? 🎮",
            f"Good morning *{name}* ဗျ! မနက်ကတည်းက Vibe ကောင်းနေပြီ 🔥",
            f"မနက်ကတည်းက ဂိမ်းစိတ်ပါနေပြီ *{name}* — ဘယ် console ကူသွားမလဲ? 😄",
        ])
    elif hour < 17:
        time_greet = random.choice([
            f"မင်္ဂလာနေ့လယ်ခင်းပါ *{name}*! နေပူပူမှာ အေးအေးလူလူ ဂိမ်းဆော့ဖို့ PS Vibe က စောင့်နေတယ်နော် 😎",
            f"ဟေ့ *{name}*! နေ့လယ်မှာ ဂိမ်းတစ်ပွဲ ဆော့ရင် မဆိုးဘူးနော် 🎮",
            f"ဒီနေ့ lunch break မှာ PS Vibe တစ်ချက် ကြည့်ဖြစ်တာ ကောင်းပြီ *{name}* 😁",
            f"ညနေ မကျသေးဘူး *{name}*၊ ဒါပေမဲ့ ဂိမ်းဆော့ဖို့ အချိန်ပေးလို့ ရပြီနော် 🕹️",
        ])
    else:
        time_greet = random.choice([
            f"မင်္ဂလာညချမ်းပါ *{name}*! တစ်နေ့ကုန် ပင်ပန်းတာ PS Vibe မှာ ဖြေလိုက်တော့! 🔥",
            f"ညနေလေးမှာ PS5 ဆော့ဖို့ အဆင်သင့်ပဲလား *{name}*? 🎮",
            f"ဟိုင်း *{name}*! ညကျပြီ — PS5 session လေးတက်မလား? 😏",
        ])

    # Add referral welcome if user came via referral link
    referral_msg = ""
    discord_msg = (
        "\n\n"
        "💬 PS VIBE Discord Community\n"
        "ဂိမ်းအကြောင်းတွေ ဆွေးနွေးဖို့နဲ့ အတူတူဆော့မယ့် အဖွဲ့ရှာဖို့ "
        "ကျွန်တော်တို့ PS VIBE ရဲ့ Discord Community လေးထဲ ဝင်ထားလို့ ရတယ်ဗျ။\n"
        "Promotion အသစ်တွေ Tournament တွေလုပ်ရင်လည်း အဲ့ဒီမှာ အရင်ဆုံး announce လုပ်မှာမို့\n"
        "👉 ဒီလင့်ခ်လေးကနေ join ထားလို့ရတယ်နော်: https://discord.gg/9axZwfQEFu"
    )

    if referred_by:
        referral_msg = f"\n🎉 *Referral* link ကနေ ဝင်လာတာပါနော်! (ref: `{referred_by}`) ကြိုဆိုပါတယ်!"

    await update.message.reply_text(
        time_greet + referral_msg + banner + discord_msg,
        parse_mode="Markdown",
        reply_markup=MAIN_MENU_KB,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *PS Vibe — Help*\n\n"
        "📅 Booking — ကြိုတင် ဘိုကင် ယူရန်\n"
        "🎮 Console Status — ဂိမ်းစက်တွေ အားနေလား/ဆော်နေလား ကြည့်မည်\n"
        "📋 My Bookings — ကို့့ booking မှတ်တမ်း\n"
        "🕹️ Game Library — ဆိုင်တွင် ရရှိနိုင်သော ဂိမ်းများ\n"
        "💰 Rate — နှုန်းထားများ\n"
        "🎁 Promotions — လက်ရှိ ပရိုမိုးရှင်းများ\n"
        "📞 Contact — Admin နှင့် ဆက်သွယ်ရန်\n"
        "🔄 Refresh — Chat reset လုပ်ရန်\n\n"
        "⏰ Open daily 9:00 AM — 9:00 PM\n\n"
        "💬 ဘာမဆို ဒီ chat မှာ ရိုက်ပေးဆိုလို့ ရတယ် — AI ကူညီပေးမှာ 🤖",
        parse_mode="Markdown",
        reply_markup=MAIN_MENU_KB,
    )


async def cmd_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contacts = await _api._fetch_contacts()
    lines = ["📞 *Contact Admin*\n"]
    buttons = []
    if contacts:
        for c in contacts:
            label = c.get("label") or c.get("name", "Admin")
            uname = c.get("username", "")
            if uname:
                buttons.append([InlineKeyboardButton(label, url=f"https://t.me/{uname}")])
                lines.append(f"💬 {label}")
    if not buttons:
        buttons.append([InlineKeyboardButton("PS Vibe Admin", url="https://t.me/psvibeofficial")])
        lines.append("💬 PS Vibe Admin")
    lines.append("\n📱 09 773355 915")
    kb = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("\n".join(lines), reply_markup=kb)


async def cmd_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📍 *PS VIBE Location*\n\n"
        "No. 17, Mau Pin Street\n"
        "Sanchaung, Yangon\n\n"
        "🗺️ [Open in Google Maps](https://maps.app.goo.gl/epFwr5WfJPsoMFg4A)",
        parse_mode="Markdown",
        reply_markup=MAIN_MENU_KB,
    )


async def cmd_promotions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    promos = await _api._fetch_promotions()
    config = await _api._fetch_config()
    FB_LINK = config.get("social_links", {}).get("facebook", "https://www.facebook.com/ps5gamecenter") if config else "https://www.facebook.com/ps5gamecenter"

    if not promos:
        empty_msg = random.choice(PROMO_EMPTY)
        await update.message.reply_text(
            f"🎁 *Promotions*\n\n{empty_msg}\n\n🎮 [PS Vibe Facebook Page]({FB_LINK})",
            parse_mode="Markdown",
        )
        return

    intro = random.choice(PROMO_INTROS)
    lines = [f"🎁 *Promotions*\n{intro}\n"]

    for i, p in enumerate(promos, 1):
        lines.append(_format_promotion(p, i))

    closing = random.choice(PROMO_CLOSING)
    lines.append(f"\n{closing}")
    lines.append(f"🎮 [PS Vibe Facebook Page]({FB_LINK})")

    await update.message.reply_text("\n".join(lines))


def _format_promotion(promo: dict, index: int) -> str:
    promo_type = promo.get("type", "general")
    title = promo.get("title", "Promotion")
    desc = promo.get("description", "")
    valid = promo.get("valid_until", "")
    emoji = promo.get("emoji", "🎁")
    conditions = promo.get("conditions", "")

    if promo_type == "discount":
        discount = promo.get("discount_percent", "")
        type_str = f" — {discount}% OFF!" if discount else ""
        title_line = f"{emoji} *{index}. {title}*{type_str}"
    elif promo_type == "free_item":
        item = promo.get("item_name", "item")
        title_line = f"{emoji} *{index}. {title}* — FREE {item}!"
    elif promo_type == "bundle":
        bundle_items = promo.get("bundle_items", "")
        title_line = f"{emoji} *{index}. {title}* — Bundle: {bundle_items}" if bundle_items else f"{emoji} *{index}. {title}* — Bundle Deal!"
    elif promo_type == "cashback":
        cashback = promo.get("cashback_percent", "")
        type_str = f" — {cashback}% Cashback!" if cashback else ""
        title_line = f"{emoji} *{index}. {title}*{type_str}"
    else:
        title_line = f"{emoji} *{index}. {title}*"

    lines = [f"\n{title_line}"]
    if desc:
        lines.append(f"   {desc}")
    if conditions:
        lines.append(f"   📋 Conditions: {conditions}")
    if valid:
        lines.append(f"   ⏳ Valid until: {valid}")
    return "\n".join(lines)


async def cmd_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🔄 *Chat ကို Refresh လုပ်ပြီးပြီ*\n"
        "_Conversation state အားလုံး ရှင်းလင်းပြီးပါပြီ —_\n"
        "_Menu မှ ထပ်မံ ရွေးချယ်နိုင်ပါပြီ_ 👇",
        parse_mode="Markdown",
        reply_markup=MAIN_MENU_KB,
    )
    return ConversationHandler.END


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    asyncio.create_task(_api.track_usage(update.effective_user, "session_visit", detail="Opened main menu"))
    await show_main_menu(update, context)



async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ စစ်ဆေးနေသည်...")
    today = today_mmt()
    now_str = now_mmt().strftime("%H:%M")

    consoles, bks = await asyncio.gather(
        _api._fetch_consoles(),
        _api._api_get(f"search-bookings?date={today}"),
    )
    consoles = consoles or []
    bks = bks if isinstance(bks, list) else []

    free  = sum(1 for c in consoles if c.get("status","").lower() == "free")
    total = len(consoles)

    upcoming = sorted(
        [b for b in bks if (b.get("timeSlot") or "") > now_str],
        key=lambda x: x.get("timeSlot",""),
    )

    open_slots = [f"{h:02d}:00" for h in range(9, 21) if f"{h:02d}:00" > now_str]
    booked_slots = {b.get("timeSlot","") for b in bks}
    free_slots = [s for s in open_slots if s not in booked_slots]

    lines = [
        f"📅 *ယနေ့ Overview*  |  {today}  {now_str} MMT\n",
        f"🖥️ Console: *{free}/{total}* free",
    ]

    if free_slots:
        lines.append(f"⏰ ကျန်နေသော Slot: *{len(free_slots)} ခု*")
        slot_rows = "  ".join(free_slots[:8])
        lines.append(f"   {slot_rows}")
    else:
        lines.append("😔 ယနေ့ ကျန် Slot မရှိတော့ပါ")

    if upcoming:
        lines.append("")
        lines.append(f"📌 *ဘုတ်ထားသော Slot ({len(upcoming)} ခု)*")
        for b in upcoming[:5]:
            lines.append(
                f"  ⏰ {b['timeSlot']}  🎮 {b.get('consoleType','')}  "
                f"⏱️ {b.get('durationMins','?')} min"
            )

    lines += ["", "_Booking လုပ်ရန် 📅 Booking ကို နှိပ်ပါ_"]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_food_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Food & Beverage menu with prices."""
    await update.message.reply_text("🍕 Loading food menu...")
    resp = await _api._api_get("fetch_food_menu")
    if not resp:
        await update.message.reply_text(
            "⚠️ Food Menu မရပါ - နောက်မှ ကြိုးစားပါ",
            reply_markup=MAIN_MENU_KB,
        )
        return
    grouped = resp or {}
    if isinstance(grouped, dict) and grouped:
        lines = ["🍕 **PS VIBE Food Menu**"]
        cat_emoji = {"Soft Drinks": "\U0001f964", "Coffee": "\u2615", "Instant Noodles": "\U0001f35c", "Snacks": "\U0001f95f", "Other": "\U0001f95a", "Food": "\U0001f354"}
        cat_order = ["Soft Drinks","Coffee", "Instant Noodles", "Snacks", "Candy", "Other", "Food"]
        for cat in cat_order:
            items = grouped.get(cat, {})
            if items:
                emoji = cat_emoji.get(cat, "\U0001f372")
                lines.append(f"\n\n{emoji} **{cat}**")
                for name, price in items.items():
                    lines.append(f"\n  - {name} = **{price:,} Ks**")
        msg = "".join(lines)
        await update.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=MAIN_MENU_KB,
        )
    else:
        await update.message.reply_text(
            "⚠️ No food items available yet.",
            reply_markup=MAIN_MENU_KB,
        )

async def cmd_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rate_lines = await _api._build_rate_lines()
    if rate_lines:
        text = "💰 *PS Vibe Rate*\n\n" + "\n".join(rate_lines)
    else:
        text = "💰 *PS Vibe Rate*\n\n📞 Rate အသေးစိတ်အတွက် Admin ကို ဆက်သွယ်ရပါ"
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid  = user.id
    name = user.first_name or ""
    username = f"@{user.username}" if user.username else "(username မရှိ)"
    await update.message.reply_text(
        f"👤 *Telegram Info*\n\n"
        f"ID: `{uid}`\n"
        f"Name: {name}\n"
        f"Username: {username}\n\n"
        f"_Member linking အတွက် ID ကို Admin ထံ ပေးပါ_",
        parse_mode="Markdown",
    )


async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    asyncio.create_task(_api.track_usage(update.effective_user, "balance"))
    chat_id = update.effective_chat.id
    member_id = await _api._get_linked_member_id(chat_id)
    if not member_id:
        await update.message.reply_text(
            "🔒 *Balance စစ်ဆေးရန် မရနိုင်သေးပါ*\n\n"
            "သင်၏ Telegram account သည် PS VIBE member card နှင့် မချိတ်ဆက်ရသေးပါ။\n\n"
            "Balance စစ်ဆေးနိုင်ရန် —\n"
            "📅 Booking တစ်ကြိမ် တင်ပေးပါ (system မှ auto-link လုပ်ပေးမည်)\n"
            "📲 သို့မဟုတ် Staff ကို ဆက်သွယ်ပေးပါ",
            parse_mode="Markdown",
        )
        return
    await update.message.reply_text("⏳ Balance စစ်ဆေးနေသည်...", parse_mode="Markdown")
    from .ai import _search_member
    result = await _search_member(member_id)
    if result.get("found") and not result.get("multiple"):
        name     = result.get("name", "?")
        bal      = result.get("balance_mins", 0)
        spend    = result.get("net_spend", 0)
        rank     = result.get("rank", "Normal")
        mid_disp = result.get("member_id", member_id)
        MASTER_THR = 300000; IMMORTAL_THR = 1000000
        if spend >= IMMORTAL_THR:
            prog = ""
        elif spend >= MASTER_THR:
            pct = min(100, int((spend - MASTER_THR) / (IMMORTAL_THR - MASTER_THR) * 100))
            filled = pct // 10; bar = "🟣" * filled + "⬜" * (10 - filled)
            prog = f"\n📈 Immortal တက်ရန်: {bar} {pct}%  ({IMMORTAL_THR - spend:,} Ks ကျန်)"
        else:
            pct = min(100, int(spend / MASTER_THR * 100))
            filled = pct // 10; bar = "🟡" * filled + "⬜" * (10 - filled)
            prog = f"\n📈 Master တက်ရန်: {bar} {pct}%  ({MASTER_THR - spend:,} Ks ကျန်)"
        hours = bal // 60; mins = bal % 60
        bal_str = f"{hours}h {mins}m" if hours else f"{mins} min"
        await update.message.reply_text(
            f"💳 *{name}* (`{mid_disp}`)\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⏱️ Balance: *{bal_str}*\n"
            f"💰 Total Spend: *{spend:,} Ks*\n"
            f"🏆 Rank: *{rank}*"
            f"{prog}",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"⚠️ Member card (`{member_id}`) data မတွေ့ပါ\nStaff ကို ဆက်သွယ်ပေးပါ",
            parse_mode="Markdown",
        )


async def cmd_game_library(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from .data.games import _is_real_game, TITLE_ALIASES, TITLE_ALIASES, TITLE_ALIASES
    await update.message.reply_text("⏳ Game list ကြည့်နေတယ်...")
    await _api._cache_pop("games_full")
    games = await _api._fetch_games_full()

    if not games:
        await update.message.reply_text("⚠️ Game data မရဘူး — ခဏနေ ပြန်ကြိုးစားပါ")
        return

    def _is_shown_game(g: dict) -> bool:
        title  = (g.get("title")  or "").strip()
        st     = (g.get("status") or "").strip()
        if not _is_real_game(title):
            return False
        # Skip "Not Installed" games
        return True

    real_games = sorted(
        [g for g in games if _is_shown_game(g)],
        key=lambda x: x.get("title", "").lower()
    )

    now_str = now_mmt().strftime("%H:%M")

    def _plat(g: dict) -> str:
        return (g.get("platform") or "").strip().upper()

    ps5_games  = [g for g in real_games if _plat(g) == "PS5"]
    ps4_games  = [g for g in real_games if _plat(g) == "PS4"]
    both_games = [g for g in real_games if _plat(g) not in {"PS5", "PS4"}]
    has_platform = bool(ps5_games or ps4_games)

    def _game_line(g: dict, indent: str = "  ") -> str:
        raw     = g.get("title", "-")
        title   = TITLE_ALIASES.get(raw.lower(), raw)
        genre   = (g.get("genre")   or "").strip()
        players = (g.get("players") or "").strip().lower()
        mode_icon = ""
        if players == "solo":
            mode_icon = " 🎯"
        elif players == "multi":
            mode_icon = " 👥"
        elif players == "both":
            mode_icon = " 🎯👥"
        genre_tag = f" | {genre}" if genre else ""
        return f"{indent}▶ {title}{genre_tag}{mode_icon}"

    solo_games  = [g for g in real_games if g.get("players","").strip().lower() == "solo"]
    multi_games = [g for g in real_games if g.get("players","").strip().lower() == "multi"]
    both_games_m = [g for g in real_games if g.get("players","").strip().lower() == "both"]
    lines = [
        f"🕹️ PS Vibe Game Library  |  {now_str} MMT",
        f"ဆိုင်မှာ ကစားလို့ရသောဂိမ်း — {len(real_games)} titles",
        f"🎯 Solo: {len(solo_games)}  |  👥 Multi: {len(multi_games)}  |  🎯👥 Both: {len(both_games_m)}",
    ]

    if has_platform:
        if ps5_games:
            lines.append(f"\n🎮 PS5  —  {len(ps5_games)} titles")
            for g in ps5_games:
                lines.append(_game_line(g))
        if ps4_games:
            lines.append(f"\n📀 PS4  —  {len(ps4_games)} titles")
            for g in ps4_games:
                lines.append(_game_line(g))
        if both_games:
            lines.append(f"\n🎯 PS4 & PS5  —  {len(both_games)} titles")
            for g in both_games:
                lines.append(_game_line(g))
    else:
        for g in real_games:
            lines.append(f"▶ {g.get('title', '-')}")

    lines += [
        "\n",
        "👥 = Multiplayer available",
        "ဂိမ်းအကြောင်း သိချင်ရင် AI ကို တိုက်ရိုက် မေးပါ 🤖",
    ]

    full_text = "\n".join(lines)
    for chunk in _split_message(full_text, 4000):
        await update.message.reply_text(chunk)

    await update.message.reply_text(
        "ဂိမ်းနာမည် ရိုက်ပြီး ရှာနိုင်တယ်နော် — AI ကို မေးလည်း ��တယ် 🤖"
    )
    await update.message.reply_text("─" * 22)


async def cmd_console_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ စစ်ဆေးနေသည်...")
    await _api._cache_pop("consoles")

    consoles, today_bks = await asyncio.gather(
        _api._fetch_consoles(),
        _api._api_get(f"search-bookings?date={today_mmt()}"),
    )

    if not consoles:
        await update.message.reply_text("⚠️ Console data မရပါ — နောက်မှ ကြိုးစားပါ")
        return

    from datetime import datetime as _dt

    dur_map: dict[str, int] = {}
    bk_list = today_bks.get("bookings", []) if isinstance(today_bks, dict) else (today_bks or [])
    for b in bk_list:
        cid_b = b.get("console_id", "")
        dur = 0
        if isinstance(b.get("end_time"), str):
            dur = max(0, int((_dt.fromisoformat(b["end_time"]) - _dt.fromisoformat(b["start_time"])).total_seconds() / 60))
        elif isinstance(b.get("start_time"), str):
            dur = max(0, int((_dt.now() - _dt.fromisoformat(b["start_time"])).total_seconds() / 60))
        if cid_b and dur:
            dur_map[cid_b] = dur

    now_str = now_mmt().strftime("%H:%M")

    lines = [
        f"🎮 Console Status  |  {today_mmt()}  {now_str} MMT\n",
    ]

    for c in consoles:
        cid = c.get("id", "?")
        ctype = c.get("type", "PS5")
        status = c.get("status", "unknown").lower()
        icon = {"free": "🟢", "active": "🔴", "inactive": "⚫", "reserved": "🟡"}.get(status, "⚪")
        dur = dur_map.get(cid, 0)
        dur_str = f" ({dur} min)" if dur else ""
        label = {
            "free": "FREE", "active": "IN USE", "inactive": "OFF",
            "reserved": "RESERVED",
        }.get(status, status.upper())
        lines.append(f"{icon} {cid} ({ctype}) — {label}{dur_str}")

    lines += ["", "📅 Booking လုပ်ရန် Booking ကို နှိပ်ပါ"]
    await update.message.reply_text("\n".join(lines))


# ── Booking Entry Points ──────────────────────────────────────────────────────

async def cmd_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    asyncio.create_task(_api.track_usage(update.effective_user, "book_start"))
    context.user_data["bk_reserved_console"] = None
    kb = ReplyKeyboardMarkup(
        [["ရှိပါတယ်"], ["မရှိဘူး (Guest)"], ["❌ ပယ်ဖျက်မည်"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        "\U0001f4c5 *Booking Form*\n\nMember Card ရှိပါသလား?\n\n( နောက်သို့ သွားရန် ❌ ပယ်ဖျက်မည် ကိုနှိပ်ပါ )",
        parse_mode="Markdown",
        reply_markup=kb,
    )
    return BK_MEMBER_CHECK


async def cmd_book_from_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ဟုတ်ကဲ့ပါ! Booking တင်ဖို့အတွက် form လေး ဖြည့်ပေးပါနော် 🎮")
    return await cmd_book(update, context)


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Booking ဖျက်လိုက်ပြီနော်",
        reply_markup=MAIN_MENU_KB,
    )
    return ConversationHandler.END


# ── Feedback ──────────────────────────────────────────────────────────────────

async def cmd_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    asyncio.create_task(_api.track_usage(update.effective_user, "feedback"))
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("1 ⭐",           callback_data="fb:1:"),
        InlineKeyboardButton("2 ⭐⭐",         callback_data="fb:2:"),
        InlineKeyboardButton("3 ⭐⭐⭐",       callback_data="fb:3:"),
        InlineKeyboardButton("4 ⭐⭐⭐⭐",     callback_data="fb:4:"),
        InlineKeyboardButton("5 ⭐⭐⭐⭐⭐",   callback_data="fb:5:"),
    ]])
    await update.message.reply_text(
        "🎮 ဒီနေ့ ဂိမ်းဆော့ရတဲ့ အတွေ့အကြုံ လေး\n"
        "အဆင်ပြေရင် Rating လေး ပေးပေးပါဦးနော် 🙏",
        parse_mode="HTML",
        reply_markup=kb,
    )


async def cb_feedback_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    parts = (query.data or "").split(":")
    if len(parts) < 2:
        return
    try:
        rating = int(parts[1])
    except ValueError:
        return
    bk_id  = parts[2] if len(parts) > 2 else ""
    stars  = "⭐" * rating
    user   = query.from_user
    tg_id  = str(user.id)
    uname  = user.username or ""

    if rating >= 4:
        asyncio.create_task(_api._api_post("feedback/submit", {
            "tg_id": tg_id, "username": uname, "booking_id": bk_id,
            "rating": rating, "comment": "", "console_id": "",
        }))
        thank_msg = f"{stars} <b>ကျေးဇူးတင်ပါတယ်!</b>\n\nPS VIBE မှာ ဆော့ပေးတဲ့အတွက် ကျေးဇူးတင်ပါတယ်! 🎮\nနောက်တစ်ကြိမ်လည်း ကြိုဆိုပါတယ်! 🙌"
        try:
            await query.edit_message_text(thank_msg, parse_mode="HTML")
        except Exception as e:
            logging.exception("handlers: suppressed exception: %s", e)
    else:
        context.user_data["_fb_rating"] = rating
        context.user_data["_fb_bk_id"]  = bk_id
        context.user_data["_fb_tg_id"]  = tg_id
        context.user_data["_fb_uname"]  = uname
        if rating == 3:
            thank_msg = f"{stars} <b>ကျေးဇူးတင်ပါတယ်!</b>\n\nပိုကောင်းအောင် ကြိုးစားပါမည် 💪"
        else:
            thank_msg = f"{stars} <b>ကျေးဇူးတင်ပါတယ်!</b>\n\nဝမ်းနည်းပါတယ် 😔 ဘာပြဿနာ ရှိခဲ့လဲ ပြောပေးပါ"
        comment_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("💬 Comment ထည့်မည်", callback_data=f"fbc:{rating}:{bk_id}"),
            InlineKeyboardButton("✅ OK ပြီပြီ",        callback_data="fbskip"),
        ]])
        try:
            await query.edit_message_text(thank_msg, parse_mode="HTML", reply_markup=comment_kb)
        except Exception as e:
            logging.exception("handlers: suppressed exception: %s", e)


async def cb_feedback_comment_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    parts = (query.data or "").split(":")
    rating = parts[1] if len(parts) > 1 else "?"
    bk_id  = parts[2] if len(parts) > 2 else ""
    context.user_data["_fb_rating"] = rating
    context.user_data["_fb_bk_id"]  = bk_id
    context.user_data["_fb_waiting_comment"] = True
    try:
        await query.edit_message_text(
            "💬 <b>Comment ရေးပေးပါ</b>\n\nဘာ improve လုပ်ရမလဲ ပြောပေးပါ 🙏",
            parse_mode="HTML",
        )
    except Exception as e:
        logging.exception("handlers: suppressed exception: %s", e)


async def cb_feedback_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer("ကျေးဇူးတင်ပါတယ်! 🙏", show_alert=False)
    rating  = context.user_data.pop("_fb_rating", None)
    bk_id   = context.user_data.pop("_fb_bk_id", "")
    tg_id   = context.user_data.pop("_fb_tg_id", str(query.from_user.id))
    uname   = context.user_data.pop("_fb_uname", query.from_user.username or "")
    context.user_data.pop("_fb_waiting_comment", None)
    if rating is not None:
        asyncio.create_task(_api._api_post("feedback/submit", {
            "tg_id": tg_id, "username": uname, "booking_id": bk_id,
            "rating": rating, "comment": "", "console_id": "",
        }))
    try:
        await query.edit_message_text("✅ <b>ကျေးဇူးတင်ပါတယ်!</b>", parse_mode="HTML")
    except Exception as e:
        logging.exception("handlers: suppressed exception: %s", e)


# ══════════════════════════════════════════════════════════════════════════════
#  Global Message Handler / Menu Routing
# ══════════════════════════════════════════════════════════════════════════════

async def handle_menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    # Feedback comment waiting
    if context.user_data.get("_fb_waiting_comment"):
        text_msg = update.message.text or ""
        rating = context.user_data.pop("_fb_rating", "?")
        bk_id  = context.user_data.pop("_fb_bk_id", "")
        context.user_data.pop("_fb_waiting_comment", None)
        user  = update.effective_user
        tg_id = str(user.id)
        uname = user.username or ""
        _fb_tg_id = context.user_data.pop("_fb_tg_id", tg_id)
        _fb_uname = context.user_data.pop("_fb_uname", uname)
        asyncio.create_task(_api._api_post("feedback/submit", {
            "tg_id": _fb_tg_id, "username": _fb_uname,
            "booking_id": bk_id, "rating": rating,
            "comment": text_msg[:500], "console_id": "",
        }))
        await update.message.reply_text(
            "✅ <b>Comment ပေးပို့ပြီးပါပြီ — ကျေးဇူးတင်ပါတယ်!</b>\n\nပိုကောင်းအောင် ကြိုးစားပါမည် 💪",
            parse_mode="HTML",
        )
        return

    # Reschedule custom time input
    if context.user_data.get("rs_awaiting_custom_time"):
        return  # handled in main.py's handler registration

    # Keyword routing
    if text == BTN_BOOK or text.lower() in ("/book",):
        return await cmd_book(update, context)
    if text == BTN_STATUS:
        return await cmd_console_status(update, context)
    if text == BTN_MYBOOKINGS:
        return await cmd_mybookings(update, context)
    if text == BTN_GAMES:
        return await cmd_game_library(update, context)
    if text == BTN_FOOD:
        return await cmd_food_menu(update, context)
    if text in (BTN_HELP_BTN, "/help"):
        return await cmd_help(update, context)
    if text == BTN_RATE:
        return await cmd_rate(update, context)
    if text == BTN_REFRESH:
        return await cmd_refresh(update, context)
    if text == BTN_CONTACT:
        return await cmd_contact(update, context)
    if text == BTN_LOCATION:
        return await cmd_location(update, context)
    if text == BTN_PROMOTIONS:
        return await cmd_promotions(update, context)
    if text == BTN_BALANCE:
        return await cmd_balance(update, context)
    if text == BTN_REFER:
        return await cmd_refer(update, context)

    # Text cancel: "cancel #42"
    m = re.match(r'^cancel\s+#?(\d+)$', text.lower())
    if m:
        return await _text_cancel_booking(update, context, int(m.group(1)))

# FAQ Auto-Reply -- DISABLED
# faq_answer = _match_faq(text)
# if faq_answer:
#     await update.message.reply_text(faq_answer, parse_mode='HTML')
#     return

    # Unknown free-text -> sentiment check -> Gemini AI
    # Skip AI for button texts, commands, and short non-question texts
    _skip_ai_patterns = [
        r"^[\u2705\u274c\U0001f504\U0001f4c5\U0001f3ae\U0001f4b0\U0001f4cb\U0001f579\U0001f519\U0001f937\u26a0\U00002139\U0001f4b3\U0001f465\U0001f4de\U0001f4cd\U0001f381]",
        r"^(ok|yes|no|hello|hi|bye|thanks|thank you|good|bad)$",
        r"^(cancel|menu|back|home|start|help|book|booking|status|rate|games|balance|refresh)$",
        r"^[/]",
    ]
    _skip_ai = False
    for pat in _skip_ai_patterns:
        if re.match(pat, text.lower()):
            _skip_ai = True
            break
    if _skip_ai:
        await update.message.reply_text(
            "\u2139\ufe0f Menu \u1011\u1032\u1000 button \u1010\u103d\u101e\u102f\u1036\u1038\u1015\u102b\u104b "
            "\u1012\u102b\u1019\u103e\u1019\u101f\u102f\u1010\u103a \u1019\u1031\u1038\u1001\u103b\u1004\u103a\u1010\u102c\u1000\u102d\u102f "
            "\u1021\u1004\u103a\u1039\u1002\u101c\u102d\u1015\u103a\u101c\u102d\u102f \u101b\u102d\u102f\u1000\u103a\u1019\u1031\u1038\u1014\u102d\u102f\u1004\u103a\u1015\u102b\u1010\u101a\u103a\u104b"
        )
        return

    # Unknown free-text → sentiment check → Gemini AI
    sentiment = _detect_sentiment(text)
    priority_care = sentiment == "frustrated"
    if priority_care:
        logging.info("Priority Care triggered for user %s: %r",
                     update.effective_user.id if update.effective_user else "?",
                     text[:60])

    # Flexible food menu match (text-only variants)
    ft = text.lower().strip()
    if ft in ("food menu", "food ပါ", "food ကြည့်မယ်"):
        return await cmd_food_menu(update, context)

    # C1 FAQ Bypass — instant reply for common queries (no AI call)
    bypass, intent = _detect_ai_bypass(text)
    if bypass:
        # For balance/rank checks, fetch member data for personalized reply
        member_data = None
        if intent in ("balance_check", "rank_check"):
            try:
                from .ai import _search_member
                member = await _search_member(text)  # search by user text
                if member.get("found"):
                    member_data = {
                        "mins": member.get("balance_mins", 0),
                        "rank": member.get("rank", "Bronze"),
                    }
            except Exception:
                pass
        faq_reply = _build_faq_template(intent, member_data)
        if faq_reply:
            from telegram.constants import ParseMode
            from .ai import _to_mdv2 as _esc
            await update.message.reply_text(_esc(faq_reply), parse_mode=ParseMode.MARKDOWN_V2)
            return
    await _ai_reply(update, context, text, priority_care=priority_care)


async def _text_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, booking_id: int):
    uid = str(update.effective_user.id)
    data = await _api._api_get(f"bookings/{booking_id}")
    if not isinstance(data, dict) or str(data.get("telegramChatId", "")) != uid:
        await update.message.reply_text(f"❌ Booking #{booking_id} မတွေ့ပါ သို့မဟုတ် ကိုယ့် booking မဟုတ်ပါ")
        return
    st = data.get("status", "")
    if st not in ("pending", "confirmed"):
        await update.message.reply_text(f"⚠️ Booking #{booking_id} ({st}) ပယ်ဖျက်လို့ မရတော့ပါ")
        return
    cust_name = update.effective_user.full_name or "Customer"
    # cancel_booking is @app.put, no body needed
    try:
        result = await _api._api_put(f"cancel_booking/{booking_id}")
    except Exception:
        result = None
    if result:
        await update.message.reply_text(
            f"🚫 *Booking #{booking_id} ပယ်ဖျက်လိုက်ပြီ*",
            parse_mode="Markdown",
        )
        staff_chat = _api.STAFF_NOTIFY_CHAT
        if staff_chat:
            await _api._tg_send({
                "chat_id": staff_chat,
                "text": (
                    f"🚫 <b>Booking #{booking_id} — Customer Cancelled</b>\n"
                    f"👤 {cust_name} မှ ပယ်ဖျက်သည်"
                ),
                "parse_mode": "HTML",
            })
    else:
        await update.message.reply_text("❌ ပယ်ဖျက်မှု မအောင်မြင်ပါ — Admin ကို ဆက်သွယ်ပါ")


# ── Stub: mybookings, refer (delegated to booking.py) ─────────────────────────

async def cmd_mybookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from .booking import cmd_mybookings as _impl
    return await _impl(update, context)


async def cmd_refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from .booking import cmd_refer as _impl
    return await _impl(update, context)


async def cmd_waitlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from .booking import cmd_waitlist as _impl
    return await _impl(update, context)

BUFFER_GLOBAL_WAIT = 0.25

# ── Booking conversation states (0-15) ────────────────────────────────────────
(
    BK_MEMBER_CHECK, BK_MEMBER_SELECT, BK_PHONE_VERIFY, BK_DATA_CONFIRM,
    BK_NAME, BK_PHONE, BK_DATE, BK_TIME,
    BK_CONSOLE, BK_DURATION, BK_GAME, BK_CONSOLE_PREF, BK_CONFIRM,
    BK_DUP_WARN, BK_DISC_WARN, BK_CON_CONFLICT,
) = range(16)
# BK_SPECIFIC_CONSOLE removed — unused state
BK_END = -1

# ── Waitlist conversation states (100-103) ────────────────────────────────────
WL_PREF, WL_NAME, WL_PHONE, WL_CONFIRM = range(100, 104)

async def cmd_my_coupons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show customer's CashBack coupons."""
    chat_id = update.effective_chat.id
    member_id = await _api._get_linked_member_id(chat_id)
    if not member_id:
        await update.message.reply_text(
            "No coupons found.\n"
            "Visit PS VIBE on June 6-7 to get your CashBack Coupon!",
            parse_mode="Markdown",
        )
        return

    try:
        data = await _api._api_get(f"coupons/list?member_id={member_id}")
        coupons = []
        if isinstance(data, dict):
            inner = data.get("coupons") or data.get("data", {}).get("coupons", [])
            if isinstance(inner, list):
                coupons = inner
        elif isinstance(data, list):
            coupons = data
    except Exception as e:
        await update.message.reply_text("Failed to fetch coupons: " + str(e)[:100])
        return

    if not coupons:
        await update.message.reply_text(
            "No CashBack Coupons yet.\n"
            "Visit PS VIBE on June 6-7!",
            parse_mode="Markdown",
        )
        return

    lines = ["🎟️ *Your CashBack Coupons*"]
    for c in coupons:
        code = c.get("code") or c.get("coupon_code") or "?"
        balance = c.get("balance_minutes") or c.get("original_minutes") or 0
        expiry = c.get("expiry_date") or ""
        status = c.get("status") or "active"

        if status == "active":
            icon = "✅ Active"
        elif status == "used":
            icon = "✅ Used"
        elif status == "expired":
            icon = "❌ Expired"
        else:
            icon = "❌ " + status

        expiry_fmt = expiry[:10] if expiry else "N/A"

        lines.append("")
        lines.append(f"🎫 *{code}*")
        lines.append(f"   {balance} mins remaining")
        lines.append(f"   Exp: {expiry_fmt}")
        lines.append(f"   Status: {icon}")

    lines.append("")
    lines.append("💡 Show this code to staff to redeem!")

    await update.message.reply_text(
        chr(10).join(lines),
        parse_mode="Markdown",
    )
