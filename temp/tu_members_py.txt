from bot import (
    log_duration,
    BTN_ASSIGN_REFERRAL, BTN_BACK, BTN_BACK_MAIN, BTN_CANCEL,
    BTN_CHECK_MEMBER, BTN_CONFIRM_ID, BTN_CONFIRM_SAVE,
    BTN_FIRST_PURCHASE, BTN_NM_CUSTOM, BTN_NM_GIFT, BTN_PAY_DONE, BTN_SKIP_EMAIL,
    BTN_SKIP_REFERRAL, BTN_TOP_UP, BTN_VIEW_RANKS, MM_LOOKUP, MM_MENU,
    NAV_ROW, NM_AMT, NM_CONFIRM, NM_EMAIL, NM_GIFT_PIN, NM_ID, NM_KPAY,
    NM_NAME, NM_PHONE, NM_REFERRAL, STOCK_ACCESS_PIN, TU_AMT, TU_CONFIRM,
    TU_KPAY, TU_MEMBER, build_rank_bonus_lines, cmd_cancel, display_rank,
    fetch_balance_mins, fetch_base_rate, fetch_bonus_table,
    fetch_member_data, fetch_member_effective_rate, fetch_member_tier,
    fetch_members, fetch_new_member_defaults, fetch_rank_table_display,
    fetch_rank_thresholds, fetch_staff, fetch_payment_methods, get_bonus_mins, get_receipt_kb,
    member_sh, next_member_id, next_member_row_no, next_write_row,
    now_mmt, rank_emoji, save_receipt_json, show_main_menu, step_hdr,
    today_str, topup_sh, update_member_effective_rate,
    fetch_members_async,
    fetch_base_rate_async,
)

try:
    from bot.api_client import api_add_member, api_add_topup
except ImportError:
    def api_add_member(data): return None
    def api_add_topup(data): return None
"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
import asyncio
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta




async def prompt_staff_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    staff_list = fetch_staff()
    kb = [[s] for s in staff_list] + [NAV_ROW]
    await update.message.reply_text(
        step_hdr(1, 7, "Staff Selection") +
        "👤 ဘယ် Staff လဲ ရွေးပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return STAFF_SELECT

async def step_staff_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_main_menu(update, context)

    staff_list = fetch_staff()
    if text not in staff_list:
        await update.message.reply_text("⚠️ ပြသောစာရင်းမှ ရွေးပေးပါ -")
        return STAFF_SELECT

    context.user_data["staff"] = text
    return await prompt_member(update, context)

async def show_mm_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [BTN_FIRST_PURCHASE, BTN_TOP_UP],
        [BTN_CHECK_MEMBER,   BTN_VIEW_RANKS],
        [BTN_BACK_MAIN],
    ]
    await update.message.reply_text(
        "💳 *Member Management*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Option ရွေးပါ ↓",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return MM_MENU

async def show_rank_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and display the full Rank Bonus table from Setting!O1:R5."""
    table = fetch_rank_table_display()
    master_thresh, immortal_thresh = map(int, fetch_rank_thresholds())
    lines = [
        "\U0001f3c6 *Member Rank Bonus*",
        "",
        "Bonus minutes you earn when topping up, based on your rank:",
        "",
        table,
        "",
        "\U0001f4a1 *How to rank up:*",
        f"  \u2694\ufe0f Warrior \u2192 Default rank for all new members",
        f"  \U0001f3c5 Master \u2192 Reach {master_thresh:,} Ks total spend",
        f"  \U0001f48e Immortal \u2192 Reach {immortal_thresh:,} Ks total spend",
    ]
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[BTN_BACK]], resize_keyboard=True),
    )
    return MM_MENU

@log_duration("members:step_mm_menu")
async def step_mm_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text

    if choice == BTN_FIRST_PURCHASE:
        context.user_data["nm_staff"] = ""
        return await prompt_nm_name(update, context)

    if choice == BTN_TOP_UP:
        return await prompt_tu_member(update, context)

    if choice == BTN_CHECK_MEMBER:
        return await prompt_mm_lookup(update, context)

    if choice == BTN_VIEW_RANKS:
        return await show_rank_info(update, context)

    if choice == BTN_ASSIGN_REFERRAL:
        member_id = context.user_data.get("mm_member_id", "")
        if not member_id:
            await update.message.reply_text(
                "⚠️ Member ရွေးပြီးမှ Referral Code သတ်မှတ်နိုင်သည်\n"
                "Check Member ကို ဥးစ်ဝဪ နှိပ်ပါ",
                reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
            )
            return MM_MENU
        return await prompt_referral_code(update, context, member_id)

    if choice in (BTN_BACK_MAIN, BTN_BACK):
        return await show_main_menu(update, context)

    return await show_mm_menu(update, context)

async def prompt_mm_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           search_results: list | None = None, query: str = ""):
    members = await fetch_members_async()
    if search_results is not None:
        display = search_results
        hint    = f"🔍 *\"{query}\"* — {len(display)} ရလဒ် တွေ့သည်\n" if display else f"❌ *\"{query}\"* — မတွေ့ပါ — ထပ်ရှာပါ\n"
    else:
        display = members
        hint    = "🔍 _ID/Name ရိုက်ပြီး ရှာနိုင်သည်_\n" if len(members) > 5 else ""
    kb = [[BTN_BACK]] + [[m] for m in display]
    await update.message.reply_text(
        "🔍 *Check Member*\n\n"
        f"{hint}"
        "ကြည့်ရှုလိုသော Member ID ကို ရွေးပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return MM_LOOKUP

@log_duration("members:step_mm_lookup")
async def step_mm_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_BACK:
        return await show_mm_menu(update, context)

    member_id = text.strip()
    members   = await fetch_members_async()
    if member_id not in members:
        # Treat input as search query — filter by substring match
        q       = member_id.lower()
        results = [m for m in members if q in m.lower()]
        if len(results) == 1:
            # Single match → auto-select
            member_id = results[0]
        else:
            return await prompt_mm_lookup(update, context, search_results=results, query=member_id)

    data                           = fetch_member_data(member_id)
    master_thresh, immortal_thresh = map(int, fetch_rank_thresholds())
    r    = display_rank(data["rank_raw"])
    r_em = rank_emoji(r)
    net  = data["net_spend"]

    # Progress to next tier
    if r == "Warrior" and int(master_thresh) > 0:
        remaining    = max(master_thresh - net, 0)
        progress_ln  = f"🏅 Remaining to Master: *{remaining:,} Ks*"
    elif r == "Master" and int(immortal_thresh) > 0:
        remaining    = max(immortal_thresh - net, 0)
        progress_ln  = f"📊 Immortal ရရန်: *{remaining:,} Ks* လိုသေးသည်"
    else:
        progress_ln  = "🏆 _Top Rank — Immortal!_"

    wallet = data["wallet_mins"]
    wallet_ln = f"💰 Wallet Mins: *{wallet:,} mins*" if wallet is not None else "💰 Wallet Mins: _ဒေတာမရှိ_"

    # Store member_id for referral flow
    referral_code = data.get("referral_code", "")
    referral_ln   = f"\U0001f381 Referral Code: *{referral_code}*\n" if referral_code else ""
    context.user_data["mm_member_id"] = member_id
    mm_kb = [
        [BTN_FIRST_PURCHASE], [BTN_TOP_UP],
        [BTN_CHECK_MEMBER], [BTN_VIEW_RANKS],
        [BTN_ASSIGN_REFERRAL],
        [BTN_BACK_MAIN],
    ]
    email     = data.get("email", "")
    email_ln  = f"📧 Email: *{email}*\n" if email else ""
    await update.message.reply_text(
        f"🔍 *Member Profile*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪪 ID: *{member_id}*\n"
        f"👤 Name: *{data['name']}*\n"
        f"📞 Phone: *{data['phone']}*\n"
        f"{email_ln}"
        f"🎖 Rank: *{r_em} {r}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📈 Ranking Progress: *{net:,} Ks*\n"
        f"{wallet_ln}\n"
        f"{progress_ln}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{referral_ln}"
        f"_(Menu ကို ဆက်လုပ်နိုင်သည်)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(mm_kb, resize_keyboard=True),
    )
    return MM_MENU

async def prompt_nm_staff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    staff_list = fetch_staff()
    kb = [[s] for s in staff_list] + [NAV_ROW]
    await update.message.reply_text(
        step_hdr(1, 6, "Staff Selection") +
        "👤 ဘယ် Staff က Register လုပ်ပေးသလဲ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return NM_STAFF

async def step_nm_staff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_mm_menu(update, context)

    staff_list = fetch_staff()
    if text not in staff_list:
        await update.message.reply_text("⚠️ ပြသောစာရင်းမှ ရွေးပေးပါ -")
        return NM_STAFF

    context.user_data["nm_staff"] = text
    return await prompt_nm_name(update, context)

async def prompt_nm_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        step_hdr(1, 6, "Member Name") +
        "👤 Member Name ရိုက်ပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return NM_NAME

@log_duration("members:step_nm_name")
async def step_nm_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_mm_menu(update, context)

    context.user_data["nm_name"] = text.strip()
    return await prompt_nm_phone(update, context)

async def prompt_nm_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data.get("nm_name", "")
    await update.message.reply_text(
        step_hdr(2, 6, "Phone Number") +
        f"👤 Name: *{name}*\n\n"
        "📞 Phone Number ရိုက်ပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [NAV_ROW], resize_keyboard=True
        ),
    )
    return NM_PHONE

@log_duration("members:step_nm_phone")
async def step_nm_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        context.user_data.pop("nm_name", None)
        return await prompt_nm_name(update, context)
    phone_input = text.strip()
    digits_only = re.sub(r'[\s\-\+\(\)]', '', phone_input)
    if not digits_only.isdigit() or len(digits_only) < 7:
        await update.message.reply_text(
            "⚠️ Phone number မမှန်ပါ — ဂဏန်း ၇ လုံးနှင့်အထက် ရိုက်ပါ",
        )
        return NM_PHONE
    context.user_data["nm_phone"] = phone_input
    # Next → email step
    return await prompt_nm_email(update, context)

async def prompt_nm_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name  = context.user_data.get("nm_name", "")
    phone = context.user_data.get("nm_phone", "-")
    await update.message.reply_text(
        step_hdr(3, 6, "Email Address") +
        f"👤 Name: *{name}*  |  📞 Phone: *{phone}*\n\n"
        "📧 Email ရိုက်ပါ\n"
        "_(n8n မှတဆင့် wallet alert ပို့ရာတွင် သုံးမည်)_\n\n"
        "မရှိလျှင် 'Email မထည့်' နှိပ်ပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [[BTN_SKIP_EMAIL], NAV_ROW], resize_keyboard=True
        ),
    )
    return NM_EMAIL

@log_duration("members:step_nm_email")
async def step_nm_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        context.user_data.pop("nm_phone", None)
        return await prompt_nm_phone(update, context)

    if text == BTN_SKIP_EMAIL:
        context.user_data["nm_email"] = ""
    else:
        # Basic email validation
        email = text.strip().lower()
        if "@" not in email or "." not in email.split("@")[-1]:
            await update.message.reply_text(
                "⚠️ Email format မမှန်ပါ (e.g. name@gmail.com)\n"
                "ထပ်ရိုက်ပါ သို့မဟုတ် ⏩ Skip နှိပ်ပါ -"
            )
            return NM_EMAIL
        context.user_data["nm_email"] = email

    # Auto-generate the member ID now, then show it for confirmation
    context.user_data["nm_id"] = next_member_id()
    return await prompt_nm_id(update, context)

async def prompt_nm_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show auto-generated ID for staff confirmation. Staff can also type a custom ID."""
    name   = context.user_data.get("nm_name", "")
    phone  = context.user_data.get("nm_phone", "-")
    gen_id = context.user_data.get("nm_id", "")
    await update.message.reply_text(
        step_hdr(4, 6, "Member ID") +
        f"👤 Name: *{name}*  |  📞 Phone: *{phone}*\n"
        f"🪪 Auto ID: *{gen_id}*\n\n"
        f"ID မှန်ကန်ပါက ✅ Confirm ID နှိပ်ပါ။\n"
        f"ပြောင်းလဲလိုပါက ID အသစ် ရိုက်ပေးပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [[BTN_CONFIRM_ID], NAV_ROW], resize_keyboard=True
        ),
    )
    return NM_ID

@log_duration("members:step_nm_id")
async def step_nm_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        context.user_data.pop("nm_id", None)
        return await prompt_nm_email(update, context)

    if text != BTN_CONFIRM_ID:
        # Staff typed a custom ID — accept it
        context.user_data["nm_id"] = text.strip()

    # BTN_CONFIRM_ID keeps the auto-generated ID already stored
    return await prompt_nm_amt(update, context)

async def prompt_nm_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show default card price from Setting!B20/B21 with a one-tap confirm button."""
    price, base_mins = fetch_new_member_defaults()
    # Safe int conversion - gspread/API may return strings
    try:
        price = int(str(price).replace(",", ""))
    except (ValueError, TypeError):
        price = 0
    try:
        base_mins = int(str(base_mins).replace(",", ""))
    except (ValueError, TypeError):
        base_mins = 0
    context.user_data["nm_default_price"] = price
    context.user_data["nm_default_mins"]  = base_mins

    # Build a button with the exact default price so step can detect it unambiguously
    default_btn = f"✅ {price:,} Ks (Default)" if price else BTN_NM_CUSTOM
    context.user_data["nm_default_btn"] = default_btn

    price_line = f"*{price:,} Ks*" if price else "_(Setting!B20 မရှိပါ)_"
    mins_line  = f"*{base_mins:,} mins*" if base_mins else "_(Setting!B21 မရှိပါ)_"

    d    = context.user_data
    name = d.get("nm_name", "")
    m_id = d.get("nm_id", "")
    kb   = [[default_btn], [BTN_NM_CUSTOM], NAV_ROW]
    await update.message.reply_text(
        step_hdr(5, 6, "Card Amount") +
        f"👤 *{name}*  |  🪪 *{m_id}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💵 Card Price  : {price_line}\n"
        f"⏱️ Base Mins   : {mins_line}\n\n"
        f"ဤပမာဏ ကောက်ခံမည်လား?\n"
        f"_(ကွဲပြားသော ပမာဏ ✏️ | မဲဖောက်/Influencer/Gift ဆိုလျှင် 🎁 Gift နှိပ်ပါ)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return NM_AMT

@log_duration("members:step_nm_amt")
async def step_nm_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text    = update.message.text
    d       = context.user_data
    default_btn = d.get("nm_default_btn", "")

    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        d.pop("nm_id", None)
        return await prompt_nm_id(update, context)

    # Staff confirmed the default price
    if text == default_btn and default_btn:
        d["nm_amt"]  = d["nm_default_price"]
        d["nm_mins"] = d["nm_default_mins"]
        d.pop("nm_is_gift", None)
        return await prompt_nm_kpay(update, context)

    # Gift / Free card — PIN verify first
    if text == BTN_NM_GIFT:
        d["nm_gift_pending"] = True
        await update.message.reply_text(
            "🔐 *Gift Card — PIN လိုအပ်သည်*\n\n"
            "Admin PIN ထည့်ပါ -",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return NM_GIFT_PIN

    # Staff wants to type a custom amount — re-prompt for free text input
    if text == BTN_NM_CUSTOM:
        default_price = d.get("nm_default_price", 0)
        d["nm_custom_mode"] = True
        d.pop("nm_is_gift", None)
        await update.message.reply_text(
            step_hdr(4, 5, "Card Amount — Custom") +
            f"ကောက်ခံမည့် ပမာဏ (Ks) ရိုက်ပါ -\n"
            f"_(Default: {default_price:,} Ks)_",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return NM_AMT

    # Free-text entry (custom amount typed by staff)
    # Gift from custom amount sub-menu
    if text == BTN_NM_GIFT:
        d["nm_gift_pending"] = True
        d["nm_custom_mode"] = False
        await update.message.reply_text(
            "\U0001f514 *Gift Card \u2014 PIN Required*\n\n"
            "Admin PIN \u1011\u100a\u1039\u1015\u102b\u1038 -",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return NM_GIFT_PIN

    try:
        amt = int(text.replace(",", "").strip())
    except ValueError:
        await update.message.reply_text("⚠️ ဂဏန်းသက်သက် ရိုက်ပေးပါ -")
        return NM_AMT

    if amt < 0:
        await update.message.reply_text("⚠️ ပမာဏ 0 ထက်ကြီးရမည် -")
        return NM_AMT

    # Custom amount uses the same base mins from Setting!B21 (not recalculated)
    d["nm_amt"]  = amt
    d["nm_mins"] = d.get("nm_default_mins", 0)
    d.pop("nm_custom_mode", None)
    d.pop("nm_is_gift", None)
    return await prompt_nm_kpay(update, context)

@log_duration("members:step_nm_gift_pin")
async def step_nm_gift_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify admin PIN before allowing Gift / Free Card."""
    text = update.message.text.strip()
    d    = context.user_data
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        d.pop("nm_gift_pending", None)
        return await prompt_nm_amt(update, context)

    # Always delete the PIN message to keep it private
    try:
        await update.message.delete()
    except Exception as e:
        logger.error("step_nm_gift_pin: %s", e, exc_info=True)
        pass

    if text != STOCK_ACCESS_PIN:
        await update.message.reply_text(
            "❌ *PIN မမှန်ကန်ပါ* — ထပ်ကြိုးစားပါ သို့မဟုတ် ⬅️ Back နှိပ်ပါ -",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return NM_GIFT_PIN

    # PIN correct — set gift data and show review
    d.pop("nm_gift_pending", None)
    d["nm_amt"]     = 0
    d["nm_kpay"]    = 0
    d["nm_cash"]    = 0
    d["nm_mins"]    = d.get("nm_default_mins", 0)
    d["nm_is_gift"] = True
    name = d.get("nm_name", "")
    m_id = d.get("nm_id", "")
    await update.message.reply_text(
        f"📋 *Review — Gift / Free Membership*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 Name: *{name}*\n"
        f"🪪 Member ID: *{m_id}*\n"
        f"📞 Phone: *{d.get('nm_phone', '-')}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎁 Type: *Gift / Free Card*\n"
        f"💵 Amount: *0 Ks*\n"
        f"⏱️ Mins Added: *{d['nm_mins']:,} mins*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"မှန်ကန်ပါသလား? ✅ Confirm & Save နှိပ်ပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[BTN_CONFIRM_SAVE], NAV_ROW], resize_keyboard=True),
    )
    return NM_CONFIRM
async def prompt_nm_kpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show dynamic payment method buttons for New Member."""
    d   = context.user_data
    amt = d.get("nm_amt", 0)

    if "nm_payments" not in d:
        d["nm_payments"] = {}

    if amt <= 0:
        d["nm_kpay"] = 0
        d["nm_cash"] = 0
        return await step_nm_confirm(update, context)

    methods = fetch_payment_methods()
    paid_so_far = sum(d["nm_payments"].values())
    remaining = amt - paid_so_far

    # Auto-confirm when full payment complete
    if remaining <= 0:
        d["nm_kpay"] = d["nm_payments"].get("KPay", 0)
        d["nm_cash"] = d["nm_payments"].get("Cash", 0)
        return await step_nm_confirm(update, context)

    kb = [[m] for m in methods]
    kb.append([BTN_PAY_DONE])
    kb.append(NAV_ROW)

    payment_status = ""
    if d["nm_payments"]:
        ll = []
        for method, ap in d["nm_payments"].items():
            ll.append(f"  \u2022 {method}: *{ap:,} Ks*")
        payment_status = "\n".join(ll)
        payment_status += f"\n  \u2500 Paid: *{paid_so_far:,} Ks*  |  Remaining: *{remaining:,} Ks*\n\n"

    await update.message.reply_text(
        step_hdr(6, 6, "Payment \u2014 Method") +
        f"\U0001f464 *{d.get('nm_name','')}*  |  \U0001faaa *{d.get('nm_id','')}*\n"
        f"\U0001f4b5 Card Amount: *{amt:,} Ks*\n\n"
        f"{payment_status}"
        "\U0001f4b3 Payment Method \u1012\u1039\u101b\u1032\u1015\u102b\u1038 -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return NM_KPAY


@log_duration("members:step_nm_kpay")
async def step_nm_kpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dynamic payment method + amount for New Member."""
    text = update.message.text
    d = context.user_data
    amt = d.get("nm_amt", 0)

    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        context.user_data.pop("nm_amt", None)
        return await prompt_nm_amt(update, context)

    # Check if text is a payment method
    methods = fetch_payment_methods()
    if text in methods:
        if text in d.get("nm_payments", {}):
            already = d["nm_payments"][text]
            await update.message.reply_text(
                f"\u26a0\ufe0f *{text}* ({already:,} Ks) already entered. Choose another method or \u2705 Payment Done.",
                parse_mode="Markdown",
            )
            return NM_KPAY
        d["nm_current_pay_method"] = text
        psf = sum(d.get("nm_payments", {}).values())
        rem = amt - psf
        await update.message.reply_text(
            f"\U0001f4b3 *{text}* \u1015\u1019\u102b\u100f \u101b\u102d\u102f\u1000\u103a\u1015\u102b\n"
            f"\u2501" * 30 + f"\n"
            f"\U0001f4b5 Card Amount: *{amt:,} Ks*  |  Remaining: *{rem:,} Ks*\n"
            f"\u2501" * 30 + f"\n"
            f"(0 - {rem:,}) \u1011\u100a\u1039\u1037\u1015\u102b\u1038 -",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return NM_KPAY

    # Check if text is BTN_PAY_DONE
    if text == BTN_PAY_DONE:
        payments = d.get("nm_payments", {})
        psf = sum(payments.values())
        if psf <= 0:
            await update.message.reply_text("\u26a0\ufe0f \u1021\u1014\u102c\u100a\u1036\u1006\u1031\u1038 payment method \u1010\u1005\u1039 \u1011\u102d\u1004\u1039\u1015\u102b\u1038 -")
            return await prompt_nm_kpay(update, context)
        d["nm_kpay"] = payments.get("KPay", 0)
        d["nm_cash"] = payments.get("Cash", 0)
        # Show review via referral (old flow: step_nm_kpay showed review → referral → confirm)
        return await prompt_nm_referral(update, context)

    # Try to parse as amount for current method
    try:
        method_amt = int(text.replace(",", "").strip())
    except ValueError:
        await update.message.reply_text("\u26a0\ufe0f \u1002\u1014\u103a\u1000\u103e\u1019\u103a\u1001\u1005\u1037\u1001\u1005\u1037 \u101b\u102d\u102f\u1000\u103a\u1015\u102b -")
        return NM_KPAY

    current_method = d.get("nm_current_pay_method", "")
    if not current_method:
        return await prompt_nm_kpay(update, context)

    psf = sum(d.get("nm_payments", {}).values())
    rem = amt - psf
    if method_amt < 0 or method_amt > rem:
        await update.message.reply_text(
            f"\u26a0\ufe0f 0 \u1014\u101c\u1039 {rem:,} \u1000\u1032 \u1014\u1031\u1000\u103a \u1002\u1014\u103a\u1000\u103e  \u101b\u102d\u102f\u1000\u103a\u1015\u102b -",
            parse_mode="Markdown",
        )
        return NM_KPAY

    if "nm_payments" not in d:
        d["nm_payments"] = {}
    d["nm_payments"][current_method] = method_amt
    return await prompt_nm_kpay(update, context)
async def prompt_nm_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask staff to enter a referral code (optional). Both parties get +30 mins."""
    d = context.user_data
    await update.message.reply_text(
        f"🎁 *Referral Code (Optional)*\n"
        f"သူငယ်ချင်းက Referral Code ရှိသေးပါက ကိုယ်ပါ\n"
        f"ရှိသေးပါက Referrer ကို *+30 mins* ရမည်\n"
        f"အလုပ်သူ New Member ကို *+30 mins* ရမည်\n\n"
        f"Code ရှိသေးပါက ရိုက်ပါ သို့ Skip နှိပ်ပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [[BTN_SKIP_REFERRAL], NAV_ROW], resize_keyboard=True
        ),
    )
    return NM_REFERRAL

@log_duration("members:step_nm_referral")
async def step_nm_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle referral code entry. Validate against Card_Wallet col Q."""
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_nm_kpay(update, context)
    if text == BTN_SKIP_REFERRAL:
        context.user_data["nm_referral_code"] = ""
        return await _show_nm_confirm(update, context)
    # Validate referral code
    code = text.strip()
    import re as _re
    if not _re.match(r"^[A-Za-z0-9_\-]{4,20}$", code):
        await update.message.reply_text(
            "⚠️ Code format မမှန်ပါ (4–20 ခရာက်, လုပ်လုပ်/ဂဏန်း/ဒောင်း/underscore သက်)\n"
            "ပြန်ပြန် ရိုက်ပါ -"
        )
        return NM_REFERRAL
    # Look up referrer in Card_Wallet col Q
    referrer_id = ""
    try:
        # Look up referrer via API (MySQL) instead of direct sheet read
        members_list = fetch_members()
        for m_id in (members_list or []):
            try:
                m_data = fetch_member_data(m_id)
                if m_data and isinstance(m_data, dict):
                    ref_code = (m_data.get("referral_code") or "").strip().upper()
                    if ref_code == code.upper():
                        referrer_id = str(m_id).strip()
                        break
            except Exception:
                continue
    except Exception as _e:
        logging.error("nm_referral_lookup: %s", _e)
    if not referrer_id:
        await update.message.reply_text(
            f"⚠️ Referral Code `{code}` ကို မရှိသေးဘူးနော်\n"
            "ပြန်ပြန် ရိုက်ပါ သို့ Skip နှိပ်ပါ -",
            parse_mode="Markdown",
        )
        return NM_REFERRAL
    context.user_data["nm_referral_code"] = code
    context.user_data["nm_referrer_id"]   = referrer_id
    return await _show_nm_confirm(update, context)

async def _show_nm_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the Review Your Entry summary for new member (called from step_nm_kpay and step_nm_referral)."""
    d = context.user_data
    phone_display = d.get("nm_phone", "-")
    email_display = d.get("nm_email", "") or "—"
    ref_code      = d.get("nm_referral_code", "")
    ref_line      = f"\n🎁 Referral Code: *{ref_code}* (+30 mins နှစ်ပါက)" if ref_code else ""
    kb = [[BTN_CONFIRM_SAVE], NAV_ROW]
    await update.message.reply_text(
        f"📋 *Review Your Entry — First Purchase*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 Name: *{d['nm_name']}*\n"
        f"🆔 Member ID: *{d['nm_id']}*\n"
        f"📞 Phone: *{phone_display}*\n"
        f"📧 Email: *{email_display}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💵 Total Amount: *{d['nm_amt']:,} Ks*\n"
        f"⏳ Base Mins (Card): *{d['nm_mins']:,} mins*\n"
        f"🎁 Bonus Mins: *0 mins*\n"
        f"🔥 Total Added Mins: *{d['nm_mins']:,} mins*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💳 Kpay: *{d['nm_kpay']:,} Ks*  |  💵 Cash: *{d['nm_cash']:,} Ks*"
        f"{ref_line}\n\n"
        f"မှန်ကန်ပါသလား? ✅ Confirm & Save နှိပ်ပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return NM_CONFIRM

@log_duration("members:step_nm_confirm")
async def step_nm_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        # Gift cards skip Kpay step — go back to amount selection
        if context.user_data.get("nm_is_gift"):
            context.user_data.pop("nm_is_gift", None)
            return await prompt_nm_amt(update, context)
        return await prompt_nm_kpay(update, context)

    if text != BTN_CONFIRM_SAVE:
        return NM_CONFIRM

    d        = context.user_data
    phone    = d.get("nm_phone", "-")
    is_gift  = d.get("nm_is_gift", False)

    # ── Pre-compute (lightweight sync — reserve rows before background) ──
    row_no   = next_member_row_no()
    cw_row   = next_write_row(member_sh)
    tl_row   = next_write_row(topup_sh)
    nm_staff = d.get("nm_staff", "")

    # Balance = mins just added (new member has no prior balance — Phase B)
    bal_mins = d["nm_mins"]

    # Initial effective rate (gift cards have no rate)
    initial_rate = (round(d["nm_amt"] / d["nm_mins"], 4)
                    if d["nm_mins"] > 0 and not is_gift else 0)

    # Snapshot all fields before clearing user_data
    nm_id    = d["nm_id"];  nm_name = d["nm_name"]
    nm_amt   = d["nm_amt"]; nm_mins = d["nm_mins"]
    nm_kpay  = d["nm_kpay"]; nm_cash = d["nm_cash"]
    nm_email        = d.get("nm_email", "")
    nm_referral_code = d.get("nm_referral_code", "")
    nm_referrer_id   = d.get("nm_referrer_id", "")
    # If referral bonus applies, add +30 to displayed balance
    if nm_referral_code and nm_referrer_id:
        bal_mins = d["nm_mins"] + 30
    today    = today_str()
    nm_vid   = f"NM-{nm_id}-{now_mmt().strftime('%Y%m%d%H%M%S')}"
    tl_type  = "Gift" if is_gift else "First Purchase"

    nm_staff_line = f"\n👤 Registered by: *{nm_staff}*" if nm_staff else ""
    if is_gift:
        msg = (
            f"🎁 *Gift Member Created!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🪪 ID: *{nm_id}*  |  👤 *{nm_name}*\n"
            f"📞 Phone: *{phone}*{nm_staff_line}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎁 Type: *Gift / Free Card*\n"
            f"⏱️ Added: *{nm_mins:,} mins*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Wallet Balance: {bal_mins:,} mins*"
        )
    else:
        msg = (
            f"✅ *Member Created!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🪪 ID: *{nm_id}*  |  👤 *{nm_name}*\n"
            f"📞 Phone: *{phone}*{nm_staff_line}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💵 Amount: *{nm_amt:,} Ks*  |  ⏱️ Added: *{nm_mins:,} mins*\n"
            f"💳 Kpay: *{nm_kpay:,} Ks*  |  💵 Cash: *{nm_cash:,} Ks*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Wallet Balance: {bal_mins:,} mins*"
            + (f"\n🎁 Referral: *{nm_referral_code}* — နှစ်ပါက *+30 mins* bonus" if nm_referral_code else "")
        )

    # Save receipt JSON (local disk — instant)
    _ref_bonus = 30 if (nm_referral_code and nm_referrer_id) else 0
    save_receipt_json(nm_vid, {
        "type": "new_member", "voucher_id": nm_vid, "date": today,
        "name": nm_name, "member_id": nm_id, "phone": phone, "email": nm_email,
        "amount": nm_amt, "mins": nm_mins, "kpay": nm_kpay, "cash": nm_cash,
        "balance_mins": bal_mins, "rank": "New Member",
        "prev_balance": 0, "balance_change": nm_mins + _ref_bonus, "balance_after": bal_mins,
        "is_gift": is_gift,
        "referral_code": nm_referral_code,
        "referral_bonus": _ref_bonus,
    })
    receipt_kb = get_receipt_kb(nm_vid)
    context.user_data.clear()

    # ── RECEIPT — sent BEFORE sheet writes ────────────────────────
    await update.message.reply_text(msg, parse_mode="Markdown",
                                    reply_markup=ReplyKeyboardRemove())
    if receipt_kb:
        await update.message.reply_text("🖨️ Receipt ပုံနှိပ်ရန် -", reply_markup=receipt_kb)

    # ── SHEET WRITES — background ─────────────────────────────────
    async def _nm_bg():
        def _do():
            # 1. Card_Wallet (cols A–D + K + M)
            # Col E = Lifetime Spend (formula in sheet — do NOT overwrite)
            # Col M = Email
            batch = [
                {"range": f"A{cw_row}:H{cw_row}",
                 "values": [[row_no, nm_id, nm_name, phone, "", "", "", bal_mins]]},
                {"range": f"K{cw_row}", "values": [[nm_staff]]},
                {"range": f"I{cw_row}", "values": [[nm_mins]]},
            ]
            if nm_email:
                batch.append({"range": f"M{cw_row}", "values": [[nm_email]]})
            # ── API write (best-effort) ──
            try:
                api_add_member({
                    "member_id": nm_id,
                    "name": nm_name,
                    "phone": phone,
                    "staff": nm_staff,
                    "email": nm_email or "",
                    "row_no": row_no,
                    "initial_mins": bal_mins,
                })
            except Exception as e:
                logging.warning("Member API write failed (GSheet fallback OK): %s", e)
            member_sh.batch_update(batch, value_input_option="USER_ENTERED")
            # 2. TopUp_Log (cols A–C, E–I, J)
            # If referral code used, add +30 bonus mins to new member's added_mins
            _nm_added_mins = nm_mins + (30 if nm_referral_code and nm_referrer_id else 0)
            # ── API write (best-effort) ──
            try:
                api_add_topup({
                    "date": today,
                    "member_id": nm_id,
                    "type": "New Member",
                    "amount": nm_amt,
                    "kpay": nm_kpay,
                    "cash": nm_cash,
                    "mins_added": _nm_added_mins,
                    "staff": nm_staff,
                })
            except Exception as e:
                logging.warning("Topup API write failed (GSheet fallback OK): %s", e)
            topup_sh.batch_update(
                [{"range": f"A{tl_row}:C{tl_row}",
                  "values": [[today, nm_id, "New Member"]]},
                 {"range": f"E{tl_row}:I{tl_row}",
                  "values": [[nm_amt, nm_kpay, nm_cash, _nm_added_mins, tl_type]]},
                 {"range": f"J{tl_row}", "values": [[nm_staff]]}],
                value_input_option="USER_ENTERED",
            )
            # 3. Effective rate (skipped for gift cards)
            if initial_rate > 0:
                update_member_effective_rate(nm_id, initial_rate)
            # 4. Referral bonus: +30 mins to referrer via a new TopUp_Log row
            if nm_referral_code and nm_referrer_id:
                _ref_tl_row = next_write_row(topup_sh)
                # ── API write (best-effort) ──
                try:
                    api_add_topup({
                        "date": today,
                        "member_id": nm_referrer_id,
                        "type": "Referral Bonus",
                        "amount": 0,
                        "kpay": 0,
                        "cash": 0,
                        "mins_added": 30,
                        "staff": nm_staff,
                    })
                except Exception as e:
                    logging.warning("Referral topup API write failed (GSheet fallback OK): %s", e)
                topup_sh.batch_update(
                    [{"range": f"A{_ref_tl_row}:C{_ref_tl_row}",
                      "values": [[today, nm_referrer_id, "Referral Bonus"]]},
                     {"range": f"E{_ref_tl_row}:I{_ref_tl_row}",
                      "values": [[0, 0, 0, 30, "Referral Bonus"]]},
                     {"range": f"J{_ref_tl_row}", "values": [[nm_staff]]}],
                    value_input_option="USER_ENTERED",
                )
                logging.info("referral_bonus: referrer %s +30 mins via TopUp_Log", nm_referrer_id)
                # Update referrer Card_Wallet Column H with +30 bonus mins
                try:
                    # Read referrer wallet via API instead of sheet scan
                    ref_data = fetch_member_data(nm_referrer_id)
                    _ref_prev_bal = ref_data.get("wallet_mins", 0) if isinstance(ref_data, dict) else 0
                    _ref_prev_i = _ref_prev_bal  # total_bought_mins
                    # Write back via sheet (API write path handles MySQL sync)
                    try:
                        _ref_rows_chk = member_sh.get_all_values()
                        for _ri, _rr in enumerate(_ref_rows_chk):
                            if _rr and len(_rr) > 1 and _rr[1].strip() == nm_referrer_id.strip():
                                member_sh.update_cell(_ri + 1, 8, _ref_prev_bal + 30)
                                member_sh.update_cell(_ri + 1, 9, _ref_prev_i + 30)
                                break
                    except Exception:
                        pass
                    logging.info("referral_bonus_wallet: referrer %s %d → %d mins via API", nm_referrer_id, _ref_prev_bal, _ref_prev_bal + 30)
                except Exception as _rte:
                    logging.error("referral_bonus_wallet_update: %s", _rte)
        try:
            await asyncio.to_thread(_do)
        except Exception as _e:
            logging.error("nm_bg_write: %s", _e)
    asyncio.create_task(_nm_bg())

    return await show_main_menu(update, context)

async def prompt_tu_member(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           search_results: list | None = None, query: str = ""):
    members = await fetch_members_async()
    if search_results is not None:
        display = search_results
        hint    = f"🔍 *\"{query}\"* — {len(display)} ရလဒ် တွေ့သည်\n" if display else f"❌ *\"{query}\"* — မတွေ့ပါ — ထပ်ရှာပါ\n"
    else:
        display = members
        hint    = "🔍 _ID/Name ရိုက်ပြီး ရှာနိုင်သည်_\n" if len(members) > 5 else ""
    kb = [[BTN_BACK, BTN_CANCEL]] + [[m] for m in display]
    await update.message.reply_text(
        step_hdr(1, 3, "Select Member") +
        f"{hint}"
        "👤 Member ID ရွေးပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return TU_MEMBER

@log_duration("members:step_tu_member")
async def step_tu_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_mm_menu(update, context)

    member_id = text.strip()
    members   = await fetch_members_async()

    # If not an exact ID, treat as search query
    if member_id not in members:
        q       = member_id.lower()
        results = [m for m in members if q in m.lower()]
        if len(results) == 1:
            member_id = results[0]
        else:
            return await prompt_tu_member(update, context, search_results=results, query=member_id)

    context.user_data["tu_id"] = member_id

    # Single consolidated Card_Wallet read
    data                           = fetch_member_data(member_id)
    master_thresh, immortal_thresh = map(int, fetch_rank_thresholds())
    bonus_table                    = fetch_bonus_table()
    context.user_data["tu_rank"]            = data["rank_raw"]
    context.user_data["tu_total_spend"]     = data["net_spend"]
    context.user_data["tu_phone"]           = data["phone"]
    context.user_data["tu_name"]            = data["name"]
    context.user_data["tu_wallet_mins"]     = data["wallet_mins"]
    context.user_data["tu_master_thresh"]   = master_thresh
    context.user_data["tu_immortal_thresh"] = immortal_thresh
    context.user_data["tu_bonus_table"]     = bonus_table

    return await prompt_tu_amt(update, context)

async def prompt_tu_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_rank        = context.user_data.get("tu_rank", "Warrior")
    bonus_table     = context.user_data.get("tu_bonus_table", [])
    net_spend       = context.user_data.get("tu_total_spend", 0)
    master_thresh   = context.user_data.get("tu_master_thresh", 0)
    immortal_thresh = context.user_data.get("tu_immortal_thresh", 0)
    m_id            = context.user_data.get("tu_id", "")
    tu_name         = context.user_data.get("tu_name", "")
    tu_wallet       = context.user_data.get("tu_wallet_mins")
    wallet_line     = f"\n💰 Current Wallet: *{tu_wallet:,} mins*" if tu_wallet is not None else ""

    r     = display_rank(raw_rank)
    r_em  = rank_emoji(r)

    # Next-tier progress line
    if r == "Warrior" and int(master_thresh) > 0:
        remaining = max(master_thresh - net_spend, 0)
        progress  = (
            f"📈 Ranking Progress: *{net_spend:,} Ks*\n"
            f"🏅 Master ရရန် *{remaining:,} Ks* လိုသေးသည်"
        )
    elif r == "Master" and int(immortal_thresh) > 0:
        remaining = max(immortal_thresh - net_spend, 0)
        progress  = (
            f"📈 Ranking Progress: *{net_spend:,} Ks*\n"
            f"💎 Immortal ရရန် *{remaining:,} Ks* လိုသေးသည်"
        )
    else:
        progress = f"📈 Ranking Progress: *{net_spend:,} Ks*  _(🏆 Top Rank!)_"

    # Rank-specific bonus table
    bonus_lines = build_rank_bonus_lines(r, bonus_table)
    if bonus_lines:
        table_text  = "\n".join(bonus_lines)
        bonus_block = f"\n🎁 *{r_em} {r} Rank Bonus Table:*\n{table_text}\n"
    else:
        bonus_block = ""

    await update.message.reply_text(
        step_hdr(2, 3, "Top-Up Amount") +
        f"🪪 *{m_id}* — {tu_name}{wallet_line}\n"
        f"🎖 Rank: *{r_em} {r}*\n"
        f"{progress}\n"
        f"{bonus_block}\n"
        f"💵 Top Up Amount (Ks) ရိုက်ပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return TU_AMT

@log_duration("members:step_tu_amt")
async def step_tu_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        context.user_data.pop("tu_id", None)
        return await prompt_tu_member(update, context)

    try:
        amt = int(text.replace(",", "").strip())
    except ValueError:
        await update.message.reply_text("⚠️ ဂဏန်းသက်သက် ရိုက်ပေးပါ -")
        return TU_AMT

    if amt <= 0:
        await update.message.reply_text("⚠️ ပမာဏ 0 ထက်ကြီးရမည် -")
        return TU_AMT

    hourly_rate = await fetch_base_rate_async()
    base_mins   = round((amt * 60) / hourly_rate) if hourly_rate else 0
    rank        = context.user_data.get("tu_rank", "Warrior")
    bonus_table = context.user_data.get("tu_bonus_table") or fetch_bonus_table()
    bonus_mins  = get_bonus_mins(rank, amt, bonus_table)
    total_mins  = base_mins + bonus_mins

    context.user_data["tu_amt"]        = amt
    context.user_data["tu_base_mins"]  = base_mins
    context.user_data["tu_bonus_mins"] = bonus_mins
    context.user_data["tu_mins"]       = total_mins   # saved to sheet col H
    return await prompt_tu_kpay(update, context)
async def prompt_tu_kpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show dynamic payment method buttons for Top Up."""
    d   = context.user_data
    amt = d.get("tu_amt", 0)

    if "tu_payments" not in d:
        d["tu_payments"] = {}

    if amt <= 0:
        d["tu_kpay"] = 0
        d["tu_cash"] = 0
        return await step_tu_confirm(update, context)

    methods = fetch_payment_methods()
    paid_so_far = sum(d["tu_payments"].values())
    remaining = amt - paid_so_far

    # Auto-confirm when full payment complete
    if remaining <= 0:
        d["tu_kpay"] = d["tu_payments"].get("KPay", 0)
        d["tu_cash"] = d["tu_payments"].get("Cash", 0)
        return await step_tu_confirm(update, context)

    kb = [[m] for m in methods]
    kb.append([BTN_PAY_DONE])
    kb.append(NAV_ROW)

    payment_status = ""
    if d["tu_payments"]:
        ll = []
        for method, ap in d["tu_payments"].items():
            ll.append(f"  \u2022 {method}: *{ap:,} Ks*")
        payment_status = "\n".join(ll)
        payment_status += f"\n  \u2500 Paid: *{paid_so_far:,} Ks*  |  Remaining: *{remaining:,} Ks*\n\n"

    r   = display_rank(d.get("tu_rank", "Warrior"))
    r_em = rank_emoji(r)
    await update.message.reply_text(
        step_hdr(3, 3, "Payment \u2014 Method") +
        f"\U0001faaa *{d.get('tu_id','')}* \u2014 {d.get('tu_name','')}\n"
        f"\U0001f396 Rank: *{r_em} {r}*  |  \U0001f4b0 Top Up: *{amt:,} Ks*\n"
        f"\u23f1 {d.get('tu_base_mins',0):,} base + {d.get('tu_bonus_mins',0)} bonus mins\n\n"
        f"{payment_status}"
        "\U0001f4b3 Payment Method \u1012\u1039\u101b\u1032\u1015\u102b\u1038 -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return TU_KPAY


@log_duration("members:step_tu_kpay")
async def step_tu_kpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dynamic payment method + amount for Top Up."""
    text = update.message.text
    d = context.user_data
    amt = d.get("tu_amt", 0)

    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        context.user_data.pop("tu_amt", None)
        return await prompt_tu_amt(update, context)

    # Check if text is a payment method
    methods = fetch_payment_methods()
    if text in methods:
        if text in d.get("tu_payments", {}):
            already = d["tu_payments"][text]
            await update.message.reply_text(
                f"\u26a0\ufe0f *{text}* ({already:,} Ks) already entered. Choose another method or \u2705 Payment Done.",
                parse_mode="Markdown",
            )
            return TU_KPAY
        d["tu_current_pay_method"] = text
        psf = sum(d.get("tu_payments", {}).values())
        rem = amt - psf
        await update.message.reply_text(
            f"\U0001f4b3 *{text}* \u1015\u1019\u102b\u100f \u101b\u102d\u102f\u1000\u103a\u1015\u102b\n"
            f"\u2501" * 30 + f"\n"
            f"\U0001f4b0 Top Up: *{amt:,} Ks*  |  Remaining: *{rem:,} Ks*\n"
            f"\u2501" * 30 + f"\n"
            f"(0 - {rem:,}) \u1011\u100a\u1039\u1037\u1015\u102b\u1038 -",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return TU_KPAY

    # Check if text is BTN_PAY_DONE
    if text == BTN_PAY_DONE:
        payments = d.get("tu_payments", {})
        psf = sum(payments.values())
        if psf <= 0:
            await update.message.reply_text("\u26a0\ufe0f \u1021\u1014\u102c\u100a\u1036\u1006\u1031\u1038 payment method \u1010\u1005\u1039 \u1011\u102d\u1004\u1039\u1015\u102b\u1038 -")
            return await prompt_tu_kpay(update, context)
        d["tu_kpay"] = payments.get("KPay", 0)
        d["tu_cash"] = payments.get("Cash", 0)

    # Show review (common for both BTN_PAY_DONE and amount parse)
    r          = display_rank(d.get("tu_rank", "Warrior"))
    r_em       = rank_emoji(r)
    base_mins  = d.get("tu_base_mins", 0)
    bonus_mins = d.get("tu_bonus_mins", 0)
    total_mins = d.get("tu_mins", 0)
    kpay       = d.get("tu_kpay", 0)
    cash       = d.get("tu_cash", 0)
    tu_amt     = d.get("tu_amt", 0)

    # Build dynamic payment display
    payments = d.get("tu_payments", {})
    pay_lines = []
    for method, a in payments.items():
        pay_lines.append(f"  \u2022 {method}: *{a:,} Ks*")
    pay_display = "\n".join(pay_lines)

    net_spend       = d.get("tu_total_spend", 0)
    master_thresh   = d.get("tu_master_thresh", 0)
    immortal_thresh = d.get("tu_immortal_thresh", 0)
    if r == "Warrior" and int(master_thresh) > 0:
        remaining = master_thresh - (net_spend + tu_amt)
        next_tier_ln = (
            f"\n\U0001f4ca After Top-Up Spend: *{net_spend + tu_amt:,} Ks*\n"
            f"\U0001f3c5 Remaining to Master: *{max(remaining,0):,} Ks*"
            + ("\n🎉 *New Tier Unlocked!* 🏅" if remaining <= 0 else "")
        )
    elif r == "Master" and int(immortal_thresh) > 0:
        remaining = immortal_thresh - (net_spend + tu_amt)
        next_tier_ln = (
            f"\n\U0001f4ca After Top-Up Spend: *{net_spend + tu_amt:,} Ks*\n"
            f"\U0001f48e Remaining to Immortal: *{max(remaining,0):,} Ks*"
            + ("\n🎉 *New Tier Unlocked!* 💎" if remaining <= 0 else "")
        )
    else:
        next_tier_ln = "\n\U0001f3c6 _Top Rank \u2014 Immortal!_"

    kb = [[BTN_CONFIRM_SAVE], NAV_ROW]
    await update.message.reply_text(
        f"\U0001f4cb *Review Your Entry \u2014 Top Up*\n"
        f"\u2501" * 30 + f"\n"
        f"\U0001faaa *{d["tu_id"]}* \u2014 {d.get("tu_name","")}\n"
        f"\U0001f396 Rank: *{r_em} {r}*\n"
        f"\u2501" * 30 + f"\n"
        f"\U0001f4b0 Top Up Amount: *{tu_amt:,} Ks*\n"
        f"\u23f1 Base Mins: *{base_mins:,} mins*\n"
        f"\U0001f389 Rank Bonus: *+{bonus_mins} mins*\n"
        f"\U0001f525 Total to be Added: *{total_mins:,} mins*\n"
        f"\u2501" * 30 + f"\n"
        f"{pay_display}"
        f"{next_tier_ln}\n\n"
        f"\u1019\u1039\u1000\u1014\u1039\u1000\u102d\u102f\u1015\u102b\u101e\u101c\u102c\u1038? \u2705 Confirm & Save \u1014\u103a\u102d\u1000\u1039\u1015\u102b\u1038 -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return TU_CONFIRM

    # Try to parse as amount for current method
    try:
        method_amt = int(text.replace(",", "").strip())
    except ValueError:
        await update.message.reply_text("\u26a0\ufe0f \u1002\u1014\u103a\u1000\u103e\u1019\u103a\u1001\u1005\u1037\u1001\u1005\u1037 \u101b\u102d\u102f\u1000\u103a\u1015\u102b -")
        return TU_KPAY

    current_method = d.get("tu_current_pay_method", "")
    if not current_method:
        return await prompt_tu_kpay(update, context)

    psf = sum(d.get("tu_payments", {}).values())
    rem = amt - psf
    if method_amt < 0 or method_amt > rem:
        await update.message.reply_text(
            f"\u26a0\ufe0f 0 \u1014\u101c\u1039 {rem:,} \u1000\u1032 \u1014\u1031\u1000\u103a \u1002\u1014\u103a\u1000\u103e  \u101b\u102d\u102f\u1000\u103a\u1015\u102b -",
            parse_mode="Markdown",
        )
        return TU_KPAY

    if "tu_payments" not in d:
        d["tu_payments"] = {}
    d["tu_payments"][current_method] = method_amt
    return await prompt_tu_kpay(update, context)
@log_duration("members:step_tu_confirm")
async def step_tu_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_tu_kpay(update, context)

    if text != BTN_CONFIRM_SAVE:
        return TU_CONFIRM

    d = context.user_data
    # ── Pre-compute (lightweight sync — reserve row before background) ──
    # 0. Capture tier + balance BEFORE write (needed for col C and rate calc)
    current_tier = fetch_member_tier(d["tu_id"])
    prev_bal     = fetch_balance_mins(d["tu_id"])
    tl_row       = next_write_row(topup_sh)

    # 1. Balance = previous balance + mins just added (Phase B — no sheet re-read)
    bal_mins = prev_bal + d["tu_mins"]

    # 2. Pre-compute new effective rate (weighted average)
    try:
        old_rate = fetch_member_effective_rate(d["tu_id"])
        if old_rate <= 0:
            old_rate = fetch_alltime_effective_rate()
        denom    = prev_bal + d["tu_mins"]
        new_rate = round((prev_bal * old_rate + d["tu_amt"]) / denom, 4) if denom > 0 else 0
    except Exception as _e:
        logging.warning("tu_confirm rate pre-calc: %s", _e)
        new_rate = 0

    # Snapshot all fields before clearing user_data
    tu_id       = d["tu_id"];       tu_amt  = d["tu_amt"]
    tu_kpay     = d["tu_kpay"];     tu_cash = d["tu_cash"]
    tu_mins     = d["tu_mins"];     tu_name = d.get("tu_name", "")
    tu_base     = d.get("tu_base_mins", 0)
    tu_bonus    = d.get("tu_bonus_mins", 0)
    tu_phone    = d.get("tu_phone", "-")
    tu_rank_raw = d.get("tu_rank", "Warrior")
    today       = today_str()
    session_snap = d.get("_session_snap")
    after_topup  = d.get("after_topup")
    added_mins   = tu_mins

    r_saved  = display_rank(tu_rank_raw)
    r_em     = rank_emoji(r_saved)
    bal_line = f"\n💰 *Current Balance: {bal_mins:,} mins*" if bal_mins > 0 else ""
    msg = (
        f"✅ *Top Up သိမ်းဆည်းပြီးပါပြီ!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪪 *{tu_id}* — {tu_name}\n"
        f"🎖 Rank: *{r_em} {r_saved}*\n"
        f"💰 Amount: *{tu_amt:,} Ks*\n"
        f"⏳ Base: *{tu_base:,} mins*  "
        f"🎁 Bonus: *+{tu_bonus:,} mins*\n"
        f"🔥 Total Added: *{tu_mins:,} mins*\n"
        f"💳 Kpay: *{tu_kpay:,} Ks*  |  💵 Cash: *{tu_cash:,} Ks*"
        f"{bal_line}"
    )

    tu_vid = f"TU-{tu_id}-{now_mmt().strftime('%Y%m%d%H%M%S')}"
    save_receipt_json(tu_vid, {
        "type": "topup", "voucher_id": tu_vid, "date": today,
        "member_id": tu_id, "rank": r_saved, "amount": tu_amt,
        "base_mins": tu_base, "bonus_mins": tu_bonus, "total_mins": tu_mins,
        "kpay": tu_kpay, "cash": tu_cash, "phone": tu_phone,
        "balance_mins": bal_mins, "prev_balance": prev_bal,
        "balance_change": tu_mins, "balance_after": bal_mins,
    })
    receipt_kb = get_receipt_kb(tu_vid)
    context.user_data.clear()

    # ── RECEIPT — sent BEFORE sheet writes ────────────────────────
    await update.message.reply_text(msg, parse_mode="Markdown",
                                    reply_markup=ReplyKeyboardRemove())
    if receipt_kb:
        await update.message.reply_text("🖨️ Receipt ပုံနှိပ်ရန် -", reply_markup=receipt_kb)

    # ── SHEET WRITES — background ─────────────────────────────────
    async def _tu_bg():
        def _do():
            # ── API write (best-effort) ──
            try:
                api_add_topup({
                    "date": today,
                    "member_id": tu_id,
                    "type": "Top Up",
                    "amount": tu_amt,
                    "kpay": tu_kpay,
                    "cash": tu_cash,
                    "mins_added": tu_mins,
                    "tier": current_tier,
                })
            except Exception as e:
                logging.warning("Topup API write failed (GSheet fallback OK): %s", e)
            topup_sh.batch_update(
                [{"range": f"A{tl_row}:C{tl_row}",
                  "values": [[today, tu_id, current_tier]]},
                 {"range": f"E{tl_row}:I{tl_row}",
                  "values": [[tu_amt, tu_kpay, tu_cash, tu_mins, "Top Up"]]}],
                value_input_option="USER_ENTERED",
            )
            if new_rate > 0:
                update_member_effective_rate(tu_id, new_rate)
            # Update Card_Wallet Column H with new balance
            try:
                # Read member data via API instead of sheet scan
                tu_data = fetch_member_data(tu_id)
                _current_i = tu_data.get("wallet_mins", 0) if isinstance(tu_data, dict) else 0
                # Write back via sheet (API write path handles MySQL sync)
                try:
                    _tu_rows_chk = member_sh.get_all_values()
                    for _ti, _tr in enumerate(_tu_rows_chk):
                        if _tr and len(_tr) > 1 and _tr[1].strip() == tu_id.strip():
                            member_sh.update_cell(_ti + 1, 8, bal_mins)
                            member_sh.update_cell(_ti + 1, 9, _current_i + tu_mins)
                            break
                except Exception:
                    pass
                logging.info("topup: %s %d → %d mins via API", tu_id, prev_bal, bal_mins)
            except Exception as _te:
                logging.error("topup_wallet_update: %s", _te)
        try:
            await asyncio.to_thread(_do)
        except Exception as _e:
            logging.error("tu_bg_write: %s", _e)
    asyncio.create_task(_tu_bg())

    if after_topup == "console_sale" and session_snap:
        # Restore session data and update wallet balance
        context.user_data.update(session_snap)
        new_wallet  = (session_snap.get("wallet_mins") or 0) + added_mins
        context.user_data["wallet_mins"] = new_wallet
        eff_cost    = session_snap.get("effective_cost_mins", session_snap.get("mins", 0))
        total_mins  = session_snap.get("actual_play_mins", session_snap.get("mins", 0))
        multiplier  = session_snap.get("multiplier", 1.0)
        base_rate   = session_snap.get("base_rate", await fetch_base_rate_async())

        if new_wallet >= eff_cost:
            # Now sufficient after top-up — normal wallet flow
            context.user_data["mins"]      = total_mins
            context.user_data["game_amt"]  = 0
            context.user_data.pop("cash_down_ks", None)
            context.user_data.pop("shortfall_mins", None)
            context.user_data.pop("shortfall_ks", None)
            await update.message.reply_text(
                f"✅ Top Up ပြီးပြီ — balance ပြည့်သည်\n📝 Sales Voucher ဆက်ဖွင့်သည်...",
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            # Still insufficient — Cash Down for remaining shortfall
            new_shortfall_mins = eff_cost - new_wallet
            new_shortfall_ks   = round(new_shortfall_mins * base_rate / 60)
            wallet_play_mins   = int(new_wallet / multiplier) if multiplier > 0 else new_wallet
            context.user_data["shortfall_mins"] = new_shortfall_mins
            context.user_data["shortfall_ks"]   = new_shortfall_ks
            context.user_data["cash_down_ks"]   = new_shortfall_ks
            context.user_data["game_amt"]        = new_shortfall_ks
            context.user_data["mins"]            = wallet_play_mins
            await update.message.reply_text(
                f"⚠️ Balance ဆက်မလောက်သေးပါ ({new_shortfall_mins} mins ≈ {new_shortfall_ks:,} Ks)\n"
                f"Cash Down အဖြစ် ဆက်သွားပါမည်...",
                reply_markup=ReplyKeyboardRemove(),
            )
        return await prompt_food_menu(update, context)

    return await show_main_menu(update, context)
