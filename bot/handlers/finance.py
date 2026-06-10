from bot import (
    log_duration,
    ACCT_TRF_AMT, ACCT_TRF_CONFIRM, ACCT_TRF_FROM, ACCT_TRF_NOTE,
    ACCT_TRF_TO, ADVPAY_ACCT, ADVPAY_AMT, ADVPAY_CONFIRM, ADVPAY_DESC,
    ADVPAY_DUE, ADVPAY_LIST, ADVPAY_NOTE, ADVPAY_PARTY,
    ADVPAY_SETTLE_CONFIRM, ASSET_CAT, ASSET_CONFIRM, ASSET_COST,
    ASSET_DATE, ASSET_DISPOSE_CONFIRM, ASSET_DISPOSE_DATE,
    ASSET_DISPOSE_PROCEEDS, ASSET_DISPOSE_QTY, ASSET_DISPOSE_SEL,
    ASSET_LIFE, ASSET_NAME, ASSET_PAY, ASSET_QTY, ASSET_SALVAGE,
    BTN_BACK, BTN_BACK_MAIN, BTN_CANCEL, BTN_CONFIRM_SAVE, BTN_FIN_ACCTS,
    BTN_FIN_ADVPAY, BTN_FIN_ASSET, BTN_FIN_ASSET_DISPOSE, BTN_FIN_BACK,
    BTN_FIN_BS, BTN_FIN_CAPITAL, BTN_FIN_DEPR, BTN_FIN_OPEX,
    BTN_FIN_PAYABLE, BTN_FIN_PNL, BTN_FIN_PREPAID, BTN_FIN_PROFIT_SHARE,
    BTN_FIN_RECEIVABLE, BTN_FIN_REPORT, BTN_FIN_SETTLE_ADVPAY,
    BTN_FIN_SETTLE_PAY, BTN_FIN_SETTLE_REC, BTN_FIN_SETUP,
    BTN_FIN_SHAREHOLDER, BTN_FIN_TRANSFER, CAP_ACCT, CAP_AMT,
    CAP_CONFIRM, FINANCE_MENU, FIN_REPORT_MENU, NAV_ROW, OPEX_ACCT,
    OPEX_AMT, OPEX_CAT, OPEX_CONFIRM, OPEX_DESC, OPEX_PAY, PAY_ACCT,
    PAY_AMT, PAY_CONFIRM, PAY_DESC, PAY_DUE, PAY_SETTLE_ACCT,
    PAY_SETTLE_CONFIRM, PAY_SETTLE_LIST, PAY_VENDOR, PREPAID_ACCT,
    PREPAID_AMT, PREPAID_CAT, PREPAID_CONFIRM, PREPAID_DESC, PREPAID_END,
    PREPAID_START, REC_ACCT, REC_AMT, REC_CONFIRM, REC_CUST, REC_DESC,
    REC_DUE, REC_SETTLE_ACCT, REC_SETTLE_CONFIRM, REC_SETTLE_LIST,
    SHARE_CAP, SHARE_CONFIRM, SHARE_NAME, SHARE_OWN, SHARE_ROLE,
    _pin_then,     cmd_cancel, now_mmt,
    show_main_menu, today_str,
    _psvibe_get_async, _psvibe_post_async,
)

try:
    from bot.api_client import api_add_opex
except ImportError:
    def api_add_opex(data): return None
import asyncio
"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta




# TODO: Migrate to MySQL via API -- direct gspread is fallback only
# These helper functions return gspread worksheet objects directly.
def get_opex_sh():
    try:
        result = api_fetch_finance_opex()
        if result is not None:
            return result
    except Exception:
        pass
    return wb.worksheet("OPEX_Log")
def get_assets_sh():
    try:
        result = api_fetch_finance_assets()
        if result is not None:
            return result
    except Exception:
        pass
    return wb.worksheet("Assets_Register")
def get_prepaid_fin_sh():
    try:
        result = api_fetch_finance_prepaid()
        if result is not None:
            return result
    except Exception:
        pass
    return wb.worksheet("Prepaid_Expenses")

def get_acct_trf_sh():
    return wb.worksheet("Account_Transfers")

def get_payables_sh():
    try:
        result = api_fetch_finance_payables()
        if result is not None:
            return result
    except Exception:
        pass
    return wb.worksheet("Payables")
def get_receivables_sh():
    try:
        result = api_fetch_finance_receivables()
        if result is not None:
            return result
    except Exception:
        pass
    return wb.worksheet("Receivables")
def get_advpay_sh():
    return wb.worksheet("Advance_Payments")

async def show_finance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Finance Management sub-menu."""
    kb = [
        # ── Capital & Equity ──
        [BTN_FIN_CAPITAL, BTN_FIN_SHAREHOLDER, BTN_FIN_TRANSFER],
        # ── Record Expenses / Assets ──
        [BTN_FIN_OPEX,    BTN_FIN_ASSET,       BTN_FIN_ASSET_DISPOSE],
        [BTN_FIN_PREPAID],
        # ── Payables / Receivables / Advances ──
        [BTN_FIN_PAYABLE, BTN_FIN_SETTLE_PAY],
        [BTN_FIN_RECEIVABLE, BTN_FIN_SETTLE_REC],
        [BTN_FIN_ADVPAY,  BTN_FIN_SETTLE_ADVPAY],
        # ── Reports ──
        [BTN_FIN_ACCTS,   BTN_FIN_REPORT],
        # ── Admin ──
        [BTN_FIN_SETUP,   BTN_BACK_MAIN],
    ]
    await update.message.reply_text(
        "💼 *Finance Management*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Action ရွေးပါ ↓",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return FINANCE_MENU

@log_duration("finance:step_finance_menu")
async def step_finance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route Finance menu choices."""
    choice = update.message.text.strip()
    if choice == BTN_BACK_MAIN:
        return await show_main_menu(update, context)
    if choice == BTN_FIN_CAPITAL:
        return await prompt_cap_acct(update, context)
    if choice == BTN_FIN_SHAREHOLDER:
        return await show_shareholder_menu(update, context)
    if choice == BTN_FIN_OPEX:
        return await prompt_opex_cat(update, context)
    if choice == BTN_FIN_ASSET:
        return await prompt_asset_name(update, context)
    if choice == BTN_FIN_ASSET_DISPOSE:
        return await prompt_asset_dispose_sel(update, context)
    if choice == BTN_FIN_PREPAID:
        return await prompt_prepaid_desc(update, context)
    if choice == BTN_FIN_TRANSFER:
        return await prompt_acct_trf_from(update, context)
    if choice == BTN_FIN_PAYABLE:
        return await prompt_pay_vendor(update, context)
    if choice == BTN_FIN_RECEIVABLE:
        return await prompt_rec_cust(update, context)
    if choice == BTN_FIN_SETTLE_PAY:
        return await show_settle_list(update, context, "payable")
    if choice == BTN_FIN_SETTLE_REC:
        return await show_settle_list(update, context, "receivable")
    if choice == BTN_FIN_ADVPAY:
        return await prompt_advpay_party(update, context)
    if choice == BTN_FIN_SETTLE_ADVPAY:
        return await show_advpay_settle(update, context)
    if choice == BTN_FIN_ACCTS:
        return await cmd_fin_accts(update, context)
    if choice == BTN_FIN_REPORT:
        return await show_fin_report_menu(update, context)
    if choice == BTN_FIN_SETUP:
        return await cmd_finance_setup(update, context)
    return await show_finance_menu(update, context)

async def prompt_opex_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("fin", {})["flow"] = "opex"
    kb = [[c] for c in OPEX_CATEGORIES] + [NAV_ROW]
    await update.message.reply_text(
        "📝 *OPEX ထည့် — အမျိုးအစား*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "လည်ပတ်ကုန်ကျစရိတ် အမျိုးအစား ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return OPEX_CAT

@log_duration("finance:step_opex_cat")
async def step_opex_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_finance_menu(update, context)
    if text not in OPEX_CATEGORIES:
        await update.message.reply_text("⚠️ အောက်မှ ရွေးပါ")
        return OPEX_CAT
    context.user_data["fin"]["opex_cat"] = text
    kb = [["⏩ Skip"], NAV_ROW]
    await update.message.reply_text(
        f"📝 *{text}* — အသေးစိတ်ဖော်ပြချက်\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ဖော်ပြချက် ရိုက်ပါ (သို့) Skip:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return OPEX_DESC

@log_duration("finance:step_opex_desc")
async def step_opex_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_opex_cat(update, context)
    context.user_data["fin"]["opex_desc"] = "" if text == "⏩ Skip" else text
    await update.message.reply_text(
        "💰 *ကုန်ကျစရိတ် ပမာဏ (Ks)*\n\nAmount ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return OPEX_AMT

@log_duration("finance:step_opex_amt")
async def step_opex_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_opex_cat(update, context)
    try:
        amt = int(text.replace(",", ""))
        if amt <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ မှန်ကန်သော ပမာဏ ရိုက်ပါ")
        return OPEX_AMT
    context.user_data["fin"]["opex_amt"] = amt
    kb = [[a] for a in FINANCE_ACCOUNTS] + [NAV_ROW]
    await update.message.reply_text(
        f"💰 *{amt:,} Ks* — ငွေ Account ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return OPEX_ACCT

@log_duration("finance:step_opex_acct")
async def step_opex_acct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        await update.message.reply_text(
            "ပမာဏ ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return OPEX_AMT
    if text not in FINANCE_ACCOUNTS:
        await update.message.reply_text("⚠️ Account ရွေးပါ")
        return OPEX_ACCT
    d = context.user_data["fin"]
    d["opex_acct"] = text
    # Auto-derive pay method from account
    _pay_map = {"Cash Box": "Cash", "MMQR": "KPay", "KBZ Bank": "Bank Transfer", "AYA Bank": "Bank Transfer"}
    d["opex_pay"] = _pay_map.get(text, "Cash")
    kb = [[BTN_CONFIRM_SAVE], NAV_ROW]
    await update.message.reply_text(
        "📝 <b>OPEX မှတ်တမ်း — အတည်ပြုချက်</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📌 Category : <b>{d['opex_cat']}</b>\n"
        f"📋 Note     : <b>{d.get('opex_desc','') or '—'}</b>\n"
        f"💰 Amount   : <b>{d['opex_amt']:,} Ks</b>\n"
        f"🏦 Account  : <b>{d['opex_acct']}</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "မှန်ကန်ပါသလား? ✅ Confirm &amp; Save နှိပ်ပါ",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return OPEX_CONFIRM

@log_duration("finance:step_opex_pay")
async def step_opex_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [[a] for a in FINANCE_ACCOUNTS] + [NAV_ROW]
        await update.message.reply_text(
            "Account ပြန်ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return OPEX_ACCT
    if text not in PAY_METHODS:
        await update.message.reply_text("⚠️ ငွေပေးပုံ ရွေးပါ")
        return OPEX_PAY
    d = context.user_data["fin"]
    d["opex_pay"] = text
    kb = [[BTN_CONFIRM_SAVE], NAV_ROW]
    await update.message.reply_text(
        "📝 *OPEX မှတ်တမ်း — အတည်ပြုချက်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📌 Category : *{d['opex_cat']}*\n"
        f"📋 Note     : *{d.get('opex_desc','') or '—'}*\n"
        f"💰 Amount   : *{d['opex_amt']:,} Ks*\n"
        f"🏦 Account  : *{d['opex_acct']}*\n"
        f"💳 Payment  : *{d['opex_pay']}*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "မှန်ကန်ပါသလား? ✅ Confirm & Save နှိပ်ပါ",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return OPEX_CONFIRM

@log_duration("finance:step_opex_confirm")
async def step_opex_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [[a] for a in FINANCE_ACCOUNTS] + [NAV_ROW]
        await update.message.reply_text(
            "Account ပြန်ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return OPEX_ACCT
    if text != BTN_CONFIRM_SAVE:
        await update.message.reply_text("✅ Confirm & Save နှိပ်ပါ")
        return OPEX_CONFIRM
    d = context.user_data["fin"]
    await update.message.reply_text("⏳ သိမ်းဆည်းနေသည်...")
    try:
        def _do():
            sh = get_opex_sh()
            sh.append_row(
                [today_str(), d["opex_cat"], d.get("opex_desc", ""),
                 d["opex_amt"], d["opex_acct"], d["opex_pay"]],
                value_input_option="USER_ENTERED",
            )
        await asyncio.to_thread(_do)

        # ── API write (non-blocking, best-effort) ──
        async def _api_write():
            try:
                api_add_opex({
                    "date": today_str(),
                    "category": d["opex_cat"],
                    "description": d.get("opex_desc", ""),
                    "amount": d["opex_amt"],
                    "account": d["opex_acct"],
                    "payment": d["opex_pay"],
                })
            except Exception as e:
                logging.warning("OPEX API write failed (GSheet fallback OK): %s", e)
        asyncio.create_task(_api_write())
        await update.message.reply_text(
            f"✅ *OPEX မှတ်တမ်း သိမ်းဆည်းပြီး!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📌 {d['opex_cat']}  |  💰 {d['opex_amt']:,} Ks\n"
            f"🏦 {d['opex_acct']}  |  💳 {d['opex_pay']}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    return await show_finance_menu(update, context)

async def prompt_asset_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("fin", {})["flow"] = "asset"
    await update.message.reply_text(
        "🏢 *Asset မှတ်တမ်း — Asset အမည်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Asset အမည် ရိုက်ပါ\n(ဥပမာ: PS5 Console #3):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return ASSET_NAME

@log_duration("finance:step_asset_name")
async def step_asset_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_finance_menu(update, context)
    if not text:
        await update.message.reply_text("⚠️ Asset အမည် ထည့်ပါ")
        return ASSET_NAME
    context.user_data["fin"]["asset_name"] = text
    kb = [[c] for c in ASSET_CATEGORIES] + [NAV_ROW]
    await update.message.reply_text(
        f"🏢 *{text}* — အမျိုးအစား ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ASSET_CAT

@log_duration("finance:step_asset_cat")
async def step_asset_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_asset_name(update, context)
    if text not in ASSET_CATEGORIES:
        await update.message.reply_text("⚠️ Category ရွေးပါ")
        return ASSET_CAT
    context.user_data["fin"]["asset_cat"] = text
    today = now_mmt().strftime("%-m/%-d/%Y")
    kb = [[today], NAV_ROW]
    await update.message.reply_text(
        "📅 *ဝယ်ယူသည့် ရက်စွဲ (M/D/YYYY)*\n"
        f"ဥပမာ: {today}",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ASSET_DATE

@log_duration("finance:step_asset_date")
async def step_asset_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [[c] for c in ASSET_CATEGORIES] + [NAV_ROW]
        await update.message.reply_text(
            "Category ပြန်ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return ASSET_CAT
    context.user_data["fin"]["asset_date"] = text
    await update.message.reply_text(
        "💰 *Asset ဝယ်ယူစျေး (Ks)*\n\nAmount ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return ASSET_COST

@log_duration("finance:step_asset_cost")
async def step_asset_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        today = now_mmt().strftime("%-m/%-d/%Y")
        await update.message.reply_text(
            "ရက်စွဲ ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([[today], NAV_ROW], resize_keyboard=True),
        )
        return ASSET_DATE
    try:
        cost = int(text.replace(",", ""))
        if cost <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ ပမာဏ မှန်ကန်စွာ ရိုက်ပါ")
        return ASSET_COST
    context.user_data["fin"]["asset_unit_cost"] = cost
    kb = [["1"], ["2"], ["3"], ["5"], ["10"], NAV_ROW]
    await update.message.reply_text(
        "🔢 *Qty (အရေအတွက်)*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"Unit Cost: *{cost:,} Ks*\n\n"
        "မည်သည့် အရေအတွက် ဝယ်ယူသည်?\n(ဥပမာ — PS5 ၃ လုံး → 3):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ASSET_QTY

@log_duration("finance:step_asset_qty")
async def step_asset_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        await update.message.reply_text(
            "Unit Cost ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return ASSET_COST
    try:
        qty = int(text.replace(",", ""))
        if qty <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ အရေအတွက် (ကိန်းဂဏန်း) ရိုက်ပါ")
        return ASSET_QTY
    context.user_data["fin"]["asset_qty"] = qty
    kb = [["3"], ["5"], ["10"], NAV_ROW]
    await update.message.reply_text(
        "📅 *Useful Life (နှစ်)*\n"
        "သုံးစွဲမည့် သက်တမ်း နှစ်အရေအတွက် ရိုက်ပါ\n(ဥပမာ: 3, 5, 10):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ASSET_LIFE

@log_duration("finance:step_asset_life")
async def step_asset_life(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        unit_cost = context.user_data["fin"].get("asset_unit_cost", 0)
        kb = [["1"], ["2"], ["3"], ["5"], ["10"], NAV_ROW]
        await update.message.reply_text(
            f"Qty ပြန်ရိုက်ပါ (Unit Cost: {unit_cost:,} Ks):",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return ASSET_QTY
    try:
        life = int(text)
        if life <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ နှစ် (ကိန်းဂဏန်း) ရိုက်ပါ")
        return ASSET_LIFE
    context.user_data["fin"]["asset_life"] = life
    cost = context.user_data["fin"].get("asset_unit_cost", 0)
    salvage_hint = int(cost * 0.1)
    kb = [[str(salvage_hint)], ["0"], NAV_ROW]
    await update.message.reply_text(
        "♻️ *Salvage Value (Ks)*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ပျက်စီးပြီးနောက် ရောင်းချနိုင်မည့် တန်ဖိုး\n"
        f"မသိပါက *0* ရိုက်ပါ\n"
        f"(အကြံ 10%: {salvage_hint:,} Ks)",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ASSET_SALVAGE

@log_duration("finance:step_asset_salvage")
async def step_asset_salvage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [["3"], ["5"], ["10"], NAV_ROW]
        await update.message.reply_text(
            "Useful Life ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return ASSET_LIFE
    try:
        salvage = int(text.replace(",", ""))
    except ValueError:
        await update.message.reply_text("⚠️ ဂဏန်း ရိုက်ပါ")
        return ASSET_SALVAGE
    d = context.user_data["fin"]
    d["asset_salvage"] = salvage
    kb = [[a] for a in FINANCE_ACCOUNTS] + [NAV_ROW]
    await update.message.reply_text(
        "🏦 ငွေပေးသော Account ရွေးပါ:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ASSET_PAY

@log_duration("finance:step_asset_pay")
async def step_asset_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        unit_cost = context.user_data["fin"].get("asset_unit_cost", 0)
        salvage_hint = int(unit_cost * 0.1)
        kb = [[str(salvage_hint)], ["0"], NAV_ROW]
        await update.message.reply_text(
            "Salvage Value/Unit ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return ASSET_SALVAGE
    if text not in FINANCE_ACCOUNTS:
        kb = [[a] for a in FINANCE_ACCOUNTS] + [NAV_ROW]
        await update.message.reply_text(
            "⚠️ Account ရွေးပါ",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return ASSET_PAY
    d = context.user_data["fin"]
    d["asset_pay"] = text  # account name e.g. "KBZ Bank", "MMQR", "Cash Box"
    life      = d["asset_life"]
    unit_cost = d["asset_unit_cost"]
    qty       = d.get("asset_qty", 1)
    salvage   = d["asset_salvage"]
    total_cost = unit_cost * qty
    total_salvage = salvage * qty
    annual_total = int((total_cost - total_salvage) / life) if life > 0 else 0
    annual_per_unit = int((unit_cost - salvage) / life) if life > 0 else 0
    kb = [[BTN_CONFIRM_SAVE], NAV_ROW]
    qty_line = f"🔢 Qty           : <b>{qty} ခု</b>\n" if qty > 1 else ""
    qty_note = f" ({annual_per_unit:,} × {qty})" if qty > 1 else ""
    await update.message.reply_text(
        "🏢 <b>Asset မှတ်တမ်း — အတည်ပြုချက်</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ Name         : <b>{d['asset_name']}</b>\n"
        f"📁 Category     : <b>{d['asset_cat']}</b>\n"
        f"📅 Purchase Date: <b>{d['asset_date']}</b>\n"
        f"💰 Unit Cost    : <b>{unit_cost:,} Ks</b>\n"
        f"{qty_line}"
        f"💵 Total Cost   : <b>{total_cost:,} Ks</b>\n"
        f"📅 Useful Life  : <b>{life} နှစ်</b>\n"
        f"♻️ Salvage/Unit : <b>{salvage:,} Ks</b>\n"
        f"📉 Annual Depr  : <b>{annual_total:,} Ks/year</b>{qty_note}\n"
        f"🏦 Account      : <b>{d['asset_pay']}</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "မှန်ကန်ပါသလား? ✅ Confirm &amp; Save နှိပ်ပါ",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ASSET_CONFIRM

@log_duration("finance:step_asset_confirm")
async def step_asset_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [[a] for a in FINANCE_ACCOUNTS] + [NAV_ROW]
        await update.message.reply_text(
            "🏦 ငွေပေးသော Account ပြန်ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return ASSET_PAY
    if text != BTN_CONFIRM_SAVE:
        await update.message.reply_text("✅ Confirm & Save နှိပ်ပါ")
        return ASSET_CONFIRM
    d = context.user_data["fin"]
    unit_cost = d["asset_unit_cost"]
    qty       = d.get("asset_qty", 1)
    pay       = d.get("asset_pay", "")
    await update.message.reply_text("⏳ သိမ်းဆည်းနေသည်...")
    try:
        def _do():
            sh = get_assets_sh()
            sh.append_row(
                [d["asset_name"], d["asset_cat"], d["asset_date"],
                 unit_cost, qty, d["asset_life"], d["asset_salvage"],
                 "Active", "", "", "", "", pay],
                value_input_option="USER_ENTERED",
            )
        await asyncio.to_thread(_do)
        total_cost = unit_cost * qty
        await update.message.reply_text(
            f"✅ <b>Asset မှတ်တမ်း သိမ်းပြီး!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ {d['asset_name']}  |  {d['asset_cat']}\n"
            f"💰 {unit_cost:,} Ks × {qty} = {total_cost:,} Ks  |  {d['asset_life']} နှစ်\n"
            f"🏦 {pay}",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    return await show_finance_menu(update, context)

def _calc_nbv_per_unit(asset: dict, as_of: datetime) -> int:
    """Net Book Value per unit at as_of date (straight-line from BUSINESS_START)."""
    unit_cost = asset["unit_cost"]
    salvage   = asset["salvage"]
    life      = asset["life"]
    date_str  = asset["date"]
    if not life or life <= 0:
        return unit_cost
    try:
        parts = date_str.split("/")
        purchase = datetime(int(parts[2]), int(parts[0]), int(parts[1])) if len(parts) == 3 else datetime.fromisoformat(date_str)
    except Exception as e:
        logger.error("_calc_nbv_per_unit: %s", e, exc_info=True)
        return unit_cost
    start = max(purchase, _BIZ_START)
    elapsed = (as_of.year - start.year) * 12 + (as_of.month - start.month) + 1
    total_months = int(life * 12)
    months = max(0, min(elapsed, total_months))
    acc_dep = round(((unit_cost - salvage) / total_months) * months) if total_months > 0 else 0
    return max(salvage, unit_cost - acc_dep)

async def prompt_asset_dispose_sel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("fin", {})["flow"] = "asset_dispose"
    await update.message.reply_text("⏳ Asset list ဖတ်နေသည်...")
    try:
        def _read():
            sh = get_assets_sh()
            rows = sh.get_all_values()
            assets = []
            for i, r in enumerate(rows[1:], start=2):
                name = (r[0] if len(r) > 0 else "").strip()
                if not name:
                    continue
                status = (r[7] if len(r) > 7 else "Active").strip()
                if status == "Disposed":
                    continue
                try:
                    qty = int((r[4] if len(r) > 4 else "1").replace(",", "") or "1")
                except Exception as e:
                    logger.error("_read: %s", e, exc_info=True)
                    qty = 1
                try:
                    disp_qty = int((r[9] if len(r) > 9 else "0").replace(",", "") or "0")
                except Exception as e:
                    logger.error("_read: %s", e, exc_info=True)
                    disp_qty = 0
                remaining = qty - disp_qty
                if remaining <= 0:
                    continue
                try:
                    unit_cost = int((r[3] if len(r) > 3 else "0").replace(",", "") or "0")
                except Exception as e:
                    logger.error("_read: %s", e, exc_info=True)
                    unit_cost = 0
                try:
                    life = float((r[5] if len(r) > 5 else "0").replace(",", "") or "0")
                except Exception as e:
                    logger.error("_read: %s", e, exc_info=True)
                    life = 0
                try:
                    salvage = int((r[6] if len(r) > 6 else "0").replace(",", "") or "0")
                except Exception as e:
                    logger.error("_read: %s", e, exc_info=True)
                    salvage = 0
                assets.append({
                    "row": i,
                    "name": name,
                    "cat": (r[1] if len(r) > 1 else "").strip(),
                    "date": (r[2] if len(r) > 2 else "").strip(),
                    "unit_cost": unit_cost,
                    "qty": qty,
                    "life": life,
                    "salvage": salvage,
                    "status": status,
                    "disp_qty": disp_qty,
                    "remaining": remaining,
                })
            return assets
        assets = await asyncio.to_thread(_read)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await show_finance_menu(update, context)

    if not assets:
        await update.message.reply_text("⚠️ Active asset မရှိပါ")
        return await show_finance_menu(update, context)

    context.user_data["fin"]["dispose_assets"] = assets
    kb = [[f"{a['name']} (x{a['remaining']})"] for a in assets] + [NAV_ROW]
    await update.message.reply_text(
        "🔄 *Asset ထုတ်ရောင်းမည်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ထုတ်ရောင်းမည့် Asset ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ASSET_DISPOSE_SEL

@log_duration("finance:step_asset_dispose_sel")
async def step_asset_dispose_sel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_finance_menu(update, context)

    assets = context.user_data.get("fin", {}).get("dispose_assets", [])
    selected = next((a for a in assets if text == f"{a['name']} (x{a['remaining']})"), None)
    if not selected:
        await update.message.reply_text("⚠️ List မှ ရွေးပါ")
        return ASSET_DISPOSE_SEL

    context.user_data["fin"]["dispose_asset"] = selected
    nbv_pu = _calc_nbv_per_unit(selected, now_mmt())
    total_nbv = nbv_pu * selected["remaining"]
    today = now_mmt().strftime("%-m/%-d/%Y")
    await update.message.reply_text(
        f"🔄 *{selected['name']}* ထုတ်ရောင်းမည်\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 Qty ကျန်     : *{selected['remaining']}* ခု\n"
        f"📉 NBV/unit     : *{nbv_pu:,} Ks*\n"
        f"💰 Total NBV    : *{total_nbv:,} Ks*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        "📅 ထုတ်ရောင်းသည့် ရက်စွဲ (M/D/YYYY):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[today], NAV_ROW], resize_keyboard=True),
    )
    return ASSET_DISPOSE_DATE

@log_duration("finance:step_asset_dispose_date")
async def step_asset_dispose_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        assets = context.user_data.get("fin", {}).get("dispose_assets", [])
        kb = [[f"{a['name']} (x{a['remaining']})"] for a in assets] + [NAV_ROW]
        await update.message.reply_text("Asset ပြန်ရွေးပါ:",
                                         reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return ASSET_DISPOSE_SEL

    context.user_data["fin"]["dispose_date"] = text
    asset = context.user_data["fin"]["dispose_asset"]
    remaining = asset["remaining"]
    quick = [str(i) for i in range(1, min(remaining + 1, 7))]
    kb = [quick] + [NAV_ROW] if remaining <= 6 else [[str(i)] for i in range(1, min(remaining + 1, 7))] + [NAV_ROW]
    await update.message.reply_text(
        f"📦 *ထုတ်ရောင်းမည့် Qty*\n\n"
        f"ကျန်ရှိ: *{remaining}* ခု\n"
        "ထုတ်ရောင်းမည့် အရေအတွက် ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[str(i)] for i in range(1, min(remaining + 1, 7))] + [NAV_ROW],
                                          resize_keyboard=True),
    )
    return ASSET_DISPOSE_QTY

@log_duration("finance:step_asset_dispose_qty")
async def step_asset_dispose_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        today = now_mmt().strftime("%-m/%-d/%Y")
        await update.message.reply_text("ရက်စွဲ ပြန်ရိုက်ပါ:",
                                         reply_markup=ReplyKeyboardMarkup([[today], NAV_ROW], resize_keyboard=True))
        return ASSET_DISPOSE_DATE

    asset = context.user_data["fin"]["dispose_asset"]
    try:
        qty = int(text.replace(",", ""))
        if qty <= 0 or qty > asset["remaining"]:
            raise ValueError
    except ValueError:
        await update.message.reply_text(f"⚠️ 1 မှ {asset['remaining']} ကြားဖြင့် ရိုက်ပါ")
        return ASSET_DISPOSE_QTY

    context.user_data["fin"]["dispose_qty"] = qty
    await update.message.reply_text(
        f"💰 *ရောင်းရငွေ (Ks)*\n\n"
        f"Qty: {qty} ခု ထုတ်ရောင်း — ရောင်းရငွေ စုစုပေါင်း ရိုက်ပါ\n"
        "(ရောင်းမဲ့မဟုတ်/ပစ်ပယ်ရင် 0 ရိုက်ပါ):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["0"], NAV_ROW], resize_keyboard=True),
    )
    return ASSET_DISPOSE_PROCEEDS

@log_duration("finance:step_asset_dispose_proceeds")
async def step_asset_dispose_proceeds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        asset = context.user_data["fin"]["dispose_asset"]
        remaining = asset["remaining"]
        await update.message.reply_text("Qty ပြန်ရိုက်ပါ:",
                                         reply_markup=ReplyKeyboardMarkup([[str(i)] for i in range(1, min(remaining + 1, 7))] + [NAV_ROW], resize_keyboard=True))
        return ASSET_DISPOSE_QTY

    try:
        proceeds = int(text.replace(",", ""))
        if proceeds < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ ပမာဏ ရိုက်ပါ (0 ရိုက်ပါ ရောင်းငွေ မရှိရင်)")
        return ASSET_DISPOSE_PROCEEDS

    d   = context.user_data["fin"]
    asset = d["dispose_asset"]
    qty   = d["dispose_qty"]
    dispose_date_str = d["dispose_date"]

    try:
        parts = dispose_date_str.split("/")
        as_of = datetime(int(parts[2]), int(parts[0]), int(parts[1])) if len(parts) == 3 else now_mmt()
    except Exception as e:
        logger.error("step_asset_dispose_proceeds: %s", e, exc_info=True)
        as_of = now_mmt()

    nbv_pu      = _calc_nbv_per_unit(asset, as_of)
    nbv_disposed = nbv_pu * qty
    gain_loss    = proceeds - nbv_disposed
    gl_icon = "💚" if gain_loss >= 0 else "🔴"
    gl_word = "Gain" if gain_loss >= 0 else "Loss"

    d["dispose_proceeds"]  = proceeds
    d["dispose_nbv"]       = nbv_disposed
    d["dispose_gain_loss"] = gain_loss

    kb = [[BTN_CONFIRM_SAVE], NAV_ROW]
    await update.message.reply_text(
        f"🔄 *Dispose အတည်ပြုချက်*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ Asset        : *{asset['name']}*\n"
        f"📅 Dispose Date : *{dispose_date_str}*\n"
        f"📦 Qty          : *{qty}* ခု (ကျန် {asset['remaining'] - qty})\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📉 NBV @ dispose : *{nbv_disposed:,} Ks*\n"
        f"💵 ရောင်းရငွေ    : *{proceeds:,} Ks*\n"
        f"{gl_icon} {gl_word}         : *{abs(gain_loss):,} Ks*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        "✅ Confirm & Save နှိပ်ပါ",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ASSET_DISPOSE_CONFIRM

@log_duration("finance:step_asset_dispose_confirm")
async def step_asset_dispose_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        await update.message.reply_text("ရောင်းငွေ ပြန်ရိုက်ပါ:",
                                         reply_markup=ReplyKeyboardMarkup([["0"], NAV_ROW], resize_keyboard=True))
        return ASSET_DISPOSE_PROCEEDS
    if text != BTN_CONFIRM_SAVE:
        await update.message.reply_text("✅ Confirm & Save နှိပ်ပါ")
        return ASSET_DISPOSE_CONFIRM

    d     = context.user_data["fin"]
    asset = d["dispose_asset"]
    qty   = d["dispose_qty"]
    proceeds = d["dispose_proceeds"]
    dispose_date = d["dispose_date"]
    await update.message.reply_text("⏳ သိမ်းဆည်းနေသည်...")

    try:
        def _write():
            sh = get_assets_sh()
            row_idx = asset["row"]
            prev_disp_qty = asset["disp_qty"]
            new_disp_qty  = prev_disp_qty + qty
            new_remaining = asset["qty"] - new_disp_qty
            new_status    = "Disposed" if new_remaining <= 0 else "Partially Disposed"
            try:
                prev_proc = int(str(sh.cell(row_idx, 11).value or "0").replace(",", ""))
            except Exception as e:
                logger.error("_write: %s", e, exc_info=True)
                prev_proc = 0
            sh.update_cell(row_idx, 8,  new_status)
            sh.update_cell(row_idx, 9,  dispose_date)
            sh.update_cell(row_idx, 10, new_disp_qty)
            sh.update_cell(row_idx, 11, prev_proc + proceeds)
        await asyncio.to_thread(_write)

        gain_loss = d["dispose_gain_loss"]
        gl_icon = "💚" if gain_loss >= 0 else "🔴"
        gl_word = "Gain" if gain_loss >= 0 else "Loss"
        await update.message.reply_text(
            f"✅ *Dispose မှတ်တမ်း သိမ်းပြီး!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ {asset['name']}  |  Qty: {qty} ခု\n"
            f"{gl_icon} {gl_word}: {abs(gain_loss):,} Ks",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    return await show_finance_menu(update, context)

async def prompt_prepaid_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("fin", {})["flow"] = "prepaid"
    await update.message.reply_text(
        "📅 *Prepaid ထည့် — ဖော်ပြချက်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ကြိုပေးငွေ ဖော်ပြချက် ရိုက်ပါ\n"
        "(ဥပမာ: မြေငှားရမ်းခ 6 လ):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return PREPAID_DESC

@log_duration("finance:step_prepaid_desc")
async def step_prepaid_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_finance_menu(update, context)
    context.user_data["fin"]["prepaid_desc"] = text
    kb = [[c] for c in PREPAID_CATEGORIES] + [NAV_ROW]
    await update.message.reply_text(
        "📁 *Prepaid Category ရွေးပါ:*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return PREPAID_CAT

@log_duration("finance:step_prepaid_cat")
async def step_prepaid_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_prepaid_desc(update, context)
    if text not in PREPAID_CATEGORIES:
        await update.message.reply_text("⚠️ Category ရွေးပါ")
        return PREPAID_CAT
    context.user_data["fin"]["prepaid_cat"] = text
    await update.message.reply_text(
        "💰 *ကြိုပေးငွေ စုစုပေါင်း (Ks)*\n\nAmount ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return PREPAID_AMT

@log_duration("finance:step_prepaid_amt")
async def step_prepaid_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [[c] for c in PREPAID_CATEGORIES] + [NAV_ROW]
        await update.message.reply_text(
            "Category ပြန်ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return PREPAID_CAT
    try:
        amt = int(text.replace(",", ""))
        if amt <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ ပမာဏ မှန်ကန်စွာ ရိုက်ပါ")
        return PREPAID_AMT
    context.user_data["fin"]["prepaid_amt"] = amt
    kb = [[a] for a in FINANCE_ACCOUNTS] + [NAV_ROW]
    await update.message.reply_text(
        f"💰 *{amt:,} Ks* — ငွေ ထုတ်မည့် Account ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return PREPAID_ACCT

@log_duration("finance:step_prepaid_acct")
async def step_prepaid_acct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        await update.message.reply_text(
            "Amount ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return PREPAID_AMT
    if text not in FINANCE_ACCOUNTS:
        kb = [[a] for a in FINANCE_ACCOUNTS] + [NAV_ROW]
        await update.message.reply_text(
            "⚠️ Account ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return PREPAID_ACCT
    context.user_data["fin"]["prepaid_acct"] = text
    today = now_mmt().strftime("%-m/%-d/%Y")
    kb = [[today], NAV_ROW]
    await update.message.reply_text(
        "📅 *Start Date (M/D/YYYY)*\n\nစတင်ရက်စွဲ ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return PREPAID_START

def _prepaid_add_months(date_str: str, months: int) -> str:
    """Parse M/D/YYYY or YYYY-MM-DD, add months, return M/D/YYYY."""
    import calendar as _cal
    from datetime import date as _date
    s = date_str.strip()
    try:
        if "-" in s and len(s) == 10:
            d = _date.fromisoformat(s)
        else:
            parts = s.split("/")
            d = _date(int(parts[2]), int(parts[0]), int(parts[1]))
    except Exception as e:
        logger.error("_prepaid_add_months: %s", e, exc_info=True)
        return s  # fallback
    m = d.month - 1 + months
    yr = d.year + m // 12
    mo = m % 12 + 1
    day = min(d.day, _cal.monthrange(yr, mo)[1])
    return f"{mo}/{day}/{yr}"

@log_duration("finance:step_prepaid_start")
async def step_prepaid_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [[a] for a in FINANCE_ACCOUNTS] + [NAV_ROW]
        await update.message.reply_text(
            "Account ပြန်ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return PREPAID_ACCT
    context.user_data["fin"]["prepaid_start"] = text
    kb = [["1"], ["3"], ["6"], ["12"], NAV_ROW]
    await update.message.reply_text(
        "📅 *Period — လပေါင်း ဘယ်လောက်?*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ကြိုပေးငွေ သက်တမ်း (လပေါင်း) ရိုက်ပါ\n"
        "(ဥပမာ — 6 လ Rent ဆိုရင် 6):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return PREPAID_END

@log_duration("finance:step_prepaid_end")
async def step_prepaid_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle period months input; auto-calculate end date."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        today = now_mmt().strftime("%-m/%-d/%Y")
        await update.message.reply_text(
            "Start Date ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([[today], NAV_ROW], resize_keyboard=True),
        )
        return PREPAID_START
    try:
        period = int(text)
        if period <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ လပေါင်း ဂဏန်း ရိုက်ပါ (ဥပမာ: 6)")
        return PREPAID_END
    d = context.user_data["fin"]
    d["prepaid_period"] = period
    end_date = _prepaid_add_months(d["prepaid_start"], period)
    d["prepaid_end"] = end_date
    kb = [[BTN_CONFIRM_SAVE], NAV_ROW]
    monthly = d["prepaid_amt"] // period if period else 0
    await update.message.reply_text(
        "📅 *Prepaid မှတ်တမ်း — အတည်ပြုချက်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📋 ဖော်ပြ     : *{d['prepaid_desc']}*\n"
        f"📁 Category  : *{d['prepaid_cat']}*\n"
        f"💰 Total Paid: *{d['prepaid_amt']:,} Ks*\n"
        f"🏦 Account    : *{d.get('prepaid_acct','—')}*\n"
        f"📅 Start     : *{d['prepaid_start']}*\n"
        f"⏱ Period    : *{period} လ*\n"
        f"📅 End       : *{end_date}* (auto)\n"
        f"📊 Monthly   : *{monthly:,} Ks/လ*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ Confirm & Save နှိပ်ပါ",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return PREPAID_CONFIRM

@log_duration("finance:step_prepaid_confirm")
async def step_prepaid_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [["1"], ["3"], ["6"], ["12"], NAV_ROW]
        await update.message.reply_text(
            "Period (လပေါင်း) ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return PREPAID_END
    if text != BTN_CONFIRM_SAVE:
        await update.message.reply_text("✅ Confirm & Save နှိပ်ပါ")
        return PREPAID_CONFIRM
    d = context.user_data["fin"]
    await update.message.reply_text("⏳ သိမ်းဆည်းနေသည်...")
    try:
        def _do():
            sh = get_prepaid_fin_sh()
            sh.append_row(
                [d["prepaid_desc"], d["prepaid_cat"], d["prepaid_amt"],
                 d["prepaid_start"], d["prepaid_end"], d.get("prepaid_acct", "")],
                value_input_option="USER_ENTERED",
            )
        await asyncio.to_thread(_do)
        await update.message.reply_text(
            f"✅ *Prepaid မှတ်တမ်း သိမ်းပြီး!*\n"
            f"📋 {d['prepaid_desc']}  |  {d['prepaid_cat']}\n"
            f"💰 {d['prepaid_amt']:,} Ks  |  {d['prepaid_start']} → {d['prepaid_end']}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    return await show_finance_menu(update, context)

async def prompt_acct_trf_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("fin", {})["flow"] = "transfer"
    kb = [[a] for a in FINANCE_ACCOUNTS] + [NAV_ROW]
    await update.message.reply_text(
        "💸 *Account Transfer — ငွေလွှဲမည်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ငွေထုတ်မည့် Account (From) ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ACCT_TRF_FROM

@log_duration("finance:step_acct_trf_from")
async def step_acct_trf_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_finance_menu(update, context)
    if text not in FINANCE_ACCOUNTS:
        await update.message.reply_text("⚠️ Account ရွေးပါ")
        return ACCT_TRF_FROM
    context.user_data["fin"]["trf_from"] = text
    to_accts = [a for a in FINANCE_ACCOUNTS if a != text]
    kb = [[a] for a in to_accts] + [NAV_ROW]
    await update.message.reply_text(
        f"💸 *From: {text}*\nTo Account ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ACCT_TRF_TO

@log_duration("finance:step_acct_trf_to")
async def step_acct_trf_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_acct_trf_from(update, context)
    if text not in FINANCE_ACCOUNTS:
        await update.message.reply_text("⚠️ Account ရွေးပါ")
        return ACCT_TRF_TO
    context.user_data["fin"]["trf_to"] = text
    await update.message.reply_text(
        "💰 *ငွေပမာဏ (Ks)*\n\nAmount ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return ACCT_TRF_AMT

@log_duration("finance:step_acct_trf_amt")
async def step_acct_trf_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        to_accts = [a for a in FINANCE_ACCOUNTS if a != context.user_data["fin"].get("trf_from", "")]
        kb = [[a] for a in to_accts] + [NAV_ROW]
        await update.message.reply_text(
            "To Account ပြန်ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return ACCT_TRF_TO
    try:
        amt = int(text.replace(",", ""))
        if amt <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ ပမာဏ မှန်ကန်စွာ ရိုက်ပါ")
        return ACCT_TRF_AMT
    context.user_data["fin"]["trf_amt"] = amt
    kb = [["⏩ Skip"], NAV_ROW]
    await update.message.reply_text(
        "📝 *မှတ်ချက် (Notes)*\n\nမှတ်ချက် ရိုက်ပါ သို့ Skip:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ACCT_TRF_NOTE

@log_duration("finance:step_acct_trf_note")
async def step_acct_trf_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        await update.message.reply_text(
            "Amount ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return ACCT_TRF_AMT
    d = context.user_data["fin"]
    d["trf_note"] = "" if text == "⏩ Skip" else text
    kb = [[BTN_CONFIRM_SAVE], NAV_ROW]
    await update.message.reply_text(
        "💸 *Account Transfer — အတည်ပြုချက်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🏦 From   : *{d['trf_from']}*\n"
        f"🏦 To     : *{d['trf_to']}*\n"
        f"💰 Amount : *{d['trf_amt']:,} Ks*\n"
        f"📝 Note   : *{d.get('trf_note','') or '—'}*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ Confirm & Save နှိပ်ပါ",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ACCT_TRF_CONFIRM

@log_duration("finance:step_acct_trf_confirm")
async def step_acct_trf_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [["⏩ Skip"], NAV_ROW]
        await update.message.reply_text(
            "မှတ်ချက် ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return ACCT_TRF_NOTE
    if text != BTN_CONFIRM_SAVE:
        await update.message.reply_text("✅ Confirm & Save နှိပ်ပါ")
        return ACCT_TRF_CONFIRM
    d = context.user_data["fin"]
    await update.message.reply_text("⏳ သိမ်းဆည်းနေသည်...")
    try:
        def _do():
            sh = get_acct_trf_sh()
            sh.append_row(
                [today_str(), d["trf_from"], d["trf_to"],
                 d["trf_amt"], d.get("trf_note", "")],
                value_input_option="USER_ENTERED",
            )
        await asyncio.to_thread(_do)
        await update.message.reply_text(
            f"✅ *Transfer မှတ်တမ်း သိမ်းပြီး!*\n"
            f"💸 {d['trf_from']} → {d['trf_to']}\n"
            f"💰 {d['trf_amt']:,} Ks",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    return await show_finance_menu(update, context)

async def prompt_pay_vendor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("fin", {})["flow"] = "payable"
    await update.message.reply_text(
        "📤 *Payable ထည့် — Vendor*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ပေးရမည့် ဆရာ/ကုမ္ပဏီ အမည် ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return PAY_VENDOR

@log_duration("finance:step_pay_vendor")
async def step_pay_vendor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_finance_menu(update, context)
    context.user_data["fin"]["pay_vendor"] = text
    await update.message.reply_text(
        "📝 *ဖော်ပြချက်*\n\nဘာအတွက် ပေးရသည် ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return PAY_DESC

@log_duration("finance:step_pay_desc")
async def step_pay_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_pay_vendor(update, context)
    context.user_data["fin"]["pay_desc"] = text
    await update.message.reply_text(
        "💰 *ပေးရမည့် ပမာဏ (Ks)*\n\nAmount ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return PAY_AMT

@log_duration("finance:step_pay_amt")
async def step_pay_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        await update.message.reply_text(
            "ဖော်ပြချက် ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return PAY_DESC
    try:
        amt = int(text.replace(",", ""))
        if amt <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ ပမာဏ မှန်ကန်စွာ ရိုက်ပါ")
        return PAY_AMT
    context.user_data["fin"]["pay_amt"] = amt
    today = now_mmt().strftime("%-m/%-d/%Y")
    kb = [[today], NAV_ROW]
    await update.message.reply_text(
        "📅 *Due Date (M/D/YYYY)*\n\nပေးဆပ်ရမည့် ရက်စွဲ ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return PAY_DUE

@log_duration("finance:step_pay_due")
async def step_pay_due(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        await update.message.reply_text(
            "Amount ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return PAY_AMT
    context.user_data["fin"]["pay_due"] = text
    kb = [[a] for a in FINANCE_ACCOUNTS] + [["⏩ Skip"], NAV_ROW]
    await update.message.reply_text(
        "🏦 *ပေးမည့် Account ရွေးပါ:*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return PAY_ACCT

@log_duration("finance:step_pay_acct")
async def step_pay_acct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        today = now_mmt().strftime("%-m/%-d/%Y")
        await update.message.reply_text(
            "Due Date ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([[today], NAV_ROW], resize_keyboard=True),
        )
        return PAY_DUE
    d = context.user_data["fin"]
    d["pay_acct"] = "" if text == "⏩ Skip" else text
    kb = [[BTN_CONFIRM_SAVE], NAV_ROW]
    await update.message.reply_text(
        "📤 *Payable — အတည်ပြုချက်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🏪 Vendor  : *{d['pay_vendor']}*\n"
        f"📝 Desc    : *{d['pay_desc']}*\n"
        f"💰 Amount  : *{d['pay_amt']:,} Ks*\n"
        f"📅 Due     : *{d['pay_due']}*\n"
        f"🏦 Account : *{d.get('pay_acct','') or '—'}*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ Confirm & Save နှိပ်ပါ",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return PAY_CONFIRM

@log_duration("finance:step_pay_confirm")
async def step_pay_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [[a] for a in FINANCE_ACCOUNTS] + [["⏩ Skip"], NAV_ROW]
        await update.message.reply_text(
            "Account ပြန်ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return PAY_ACCT
    if text != BTN_CONFIRM_SAVE:
        await update.message.reply_text("✅ Confirm & Save နှိပ်ပါ")
        return PAY_CONFIRM
    d = context.user_data["fin"]
    await update.message.reply_text("⏳ သိမ်းဆည်းနေသည်...")
    try:
        def _do():
            sh = get_payables_sh()
            sh.append_row(
                [today_str(), d["pay_vendor"], d["pay_desc"],
                 d["pay_amt"], d["pay_due"], "Pending", "", d.get("pay_acct", ""), ""],
                value_input_option="USER_ENTERED",
            )
        await asyncio.to_thread(_do)
        # ── API write ──
        async def _api_write():
            try:
                api_add_payable({
                    "date": today_str(),
                    "vendor": d["pay_vendor"],
                    "description": d["pay_desc"],
                    "amount": d["pay_amt"],
                    "due_date": d["pay_due"],
                    "status": "Pending",
                    "account": d.get("pay_acct", ""),
                })
            except Exception:
                pass
        asyncio.ensure_future(_api_write())
        await update.message.reply_text(
            f"✅ *Payable မှတ်တမ်း သိမ်းပြီး!*\n"
            f"📤 {d['pay_vendor']} — {d['pay_desc']}\n"
            f"💰 {d['pay_amt']:,} Ks  |  Due: {d['pay_due']}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    return await show_finance_menu(update, context)

async def prompt_rec_cust(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("fin", {})["flow"] = "receivable"
    await update.message.reply_text(
        "📥 *Receivable ထည့် — Customer*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ရမည့် ဆရာ/ကုမ္ပဏီ အမည် ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return REC_CUST

@log_duration("finance:step_rec_cust")
async def step_rec_cust(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_finance_menu(update, context)
    context.user_data["fin"]["rec_cust"] = text
    await update.message.reply_text(
        "📝 *ဖော်ပြချက်*\n\nဘာအတွက် ရမည် ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return REC_DESC

@log_duration("finance:step_rec_desc")
async def step_rec_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_rec_cust(update, context)
    context.user_data["fin"]["rec_desc"] = text
    await update.message.reply_text(
        "💰 *ရမည့် ပမာဏ (Ks)*\n\nAmount ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return REC_AMT

@log_duration("finance:step_rec_amt")
async def step_rec_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        await update.message.reply_text(
            "ဖော်ပြချက် ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return REC_DESC
    try:
        amt = int(text.replace(",", ""))
        if amt <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ ပမာဏ မှန်ကန်စွာ ရိုက်ပါ")
        return REC_AMT
    context.user_data["fin"]["rec_amt"] = amt
    today = now_mmt().strftime("%-m/%-d/%Y")
    kb = [[today], NAV_ROW]
    await update.message.reply_text(
        "📅 *Expected Date (M/D/YYYY)*\n\nရမည့် ရက်စွဲ ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return REC_DUE

@log_duration("finance:step_rec_due")
async def step_rec_due(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        await update.message.reply_text(
            "Amount ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return REC_AMT
    context.user_data["fin"]["rec_due"] = text
    kb = [[a] for a in FINANCE_ACCOUNTS] + [["⏩ Skip"], NAV_ROW]
    await update.message.reply_text(
        "🏦 *ရမည့် Account ရွေးပါ:*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return REC_ACCT

@log_duration("finance:step_rec_acct")
async def step_rec_acct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        today = now_mmt().strftime("%-m/%-d/%Y")
        await update.message.reply_text(
            "Expected Date ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([[today], NAV_ROW], resize_keyboard=True),
        )
        return REC_DUE
    d = context.user_data["fin"]
    d["rec_acct"] = "" if text == "⏩ Skip" else text
    kb = [[BTN_CONFIRM_SAVE], NAV_ROW]
    await update.message.reply_text(
        "📥 *Receivable — အတည်ပြုချက်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 Customer : *{d['rec_cust']}*\n"
        f"📝 Desc     : *{d['rec_desc']}*\n"
        f"💰 Amount   : *{d['rec_amt']:,} Ks*\n"
        f"📅 Expected : *{d['rec_due']}*\n"
        f"🏦 Account  : *{d.get('rec_acct','') or '—'}*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ Confirm & Save နှိပ်ပါ",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return REC_CONFIRM

@log_duration("finance:step_rec_confirm")
async def step_rec_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [[a] for a in FINANCE_ACCOUNTS] + [["⏩ Skip"], NAV_ROW]
        await update.message.reply_text(
            "Account ပြန်ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return REC_ACCT
    if text != BTN_CONFIRM_SAVE:
        await update.message.reply_text("✅ Confirm & Save နှိပ်ပါ")
        return REC_CONFIRM
    d = context.user_data["fin"]
    await update.message.reply_text("⏳ သိမ်းဆည်းနေသည်...")
    try:
        def _do():
            sh = get_receivables_sh()
            sh.append_row(
                [today_str(), d["rec_cust"], d["rec_desc"],
                 d["rec_amt"], d["rec_due"], "Pending", "", d.get("rec_acct", ""), ""],
                value_input_option="USER_ENTERED",
            )
        await asyncio.to_thread(_do)
        await update.message.reply_text(
            f"✅ *Receivable မှတ်တမ်း သိမ်းပြီး!*\n"
            f"📥 {d['rec_cust']} — {d['rec_desc']}\n"
            f"💰 {d['rec_amt']:,} Ks  |  Expected: {d['rec_due']}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    return await show_finance_menu(update, context)

async def show_settle_list(update: Update, context: ContextTypes.DEFAULT_TYPE, kind: str):
    """Show list of Pending payables or receivables for settling."""
    is_pay = kind == "payable"
    label  = "Payable" if is_pay else "Receivable"
    icon   = "📤" if is_pay else "📥"
    await update.message.reply_text(f"⏳ Pending {label} ဆွဲယူနေသည်...")
    try:
        def _read():
            sh = get_payables_sh() if is_pay else get_receivables_sh()
            return sh.get_all_values()
        rows = await asyncio.to_thread(_read)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await show_finance_menu(update, context)

    # Payables/Receivables cols: A=Date B=Vendor/Cust C=Desc D=Amt E=Due F=Status G=PaidDate H=Acct
    pending = [(i + 2, r) for i, r in enumerate(rows[1:])
               if r and (r[5] if len(r) > 5 else "").strip().lower() in ("pending", "")]
    context.user_data.setdefault("fin", {})["settle_kind"]    = kind
    context.user_data["fin"]["settle_pending"] = pending   # list of (sheet_row, row_data)

    if not pending:
        await update.message.reply_text(
            f"✅ Pending {label} မရှိပါ — အားလုံး Settle ပြီးပြီ!"
        )
        return await show_finance_menu(update, context)

    lines = [f"{icon} *Pending {label} စာရင်း*", "━━━━━━━━━━━━━━━━━━"]
    for idx, (_, r) in enumerate(pending, 1):
        party = (r[1] if len(r) > 1 else "?").strip()
        desc  = (r[2] if len(r) > 2 else "").strip()
        amt   = (r[3] if len(r) > 3 else "0").strip()
        due   = (r[4] if len(r) > 4 else "").strip()
        try:
            amt_fmt = f"{int(str(amt).replace(',','').replace('.','').split('.')[0]):,}"
        except Exception as e:
            logger.error("_read: %s", e, exc_info=True)
            amt_fmt = amt
        lines.append(f"{idx}. *{party}*\n   {desc}\n   💰 {amt_fmt} Ks  |  📅 Due: {due}")
    lines += ["━━━━━━━━━━━━━━━━━━", "ဘယ် ဂဏန်းကို Settle မည်? (ဥပမာ: 1)"]

    num_kb = [[str(i)] for i in range(1, len(pending) + 1)]
    num_kb.append([BTN_FIN_BACK, BTN_CANCEL])
    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(num_kb, resize_keyboard=True),
    )
    return PAY_SETTLE_LIST if is_pay else REC_SETTLE_LIST

async def _handle_settle_list(update: Update, context: ContextTypes.DEFAULT_TYPE, kind: str):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_FIN_BACK:
        return await show_finance_menu(update, context)
    d = context.user_data.get("fin", {})
    pending = d.get("settle_pending", [])
    try:
        idx = int(text) - 1
        assert 0 <= idx < len(pending)
    except (ValueError, AssertionError):
        await update.message.reply_text("⚠️ မှန်ကန်သော ဂဏန်း ရိုက်ပါ")
        return PAY_SETTLE_LIST if kind == "payable" else REC_SETTLE_LIST

    sheet_row, r = pending[idx]
    d["settle_row"]  = sheet_row
    d["settle_data"] = r
    acct = (r[7] if len(r) > 7 else "").strip()
    # If account not set, ask user which account to pay from/into
    if not acct:
        is_pay = kind == "payable"
        party  = (r[1] if len(r) > 1 else "?").strip()
        amt    = (r[3] if len(r) > 3 else "0").strip()
        try:
            amt_fmt = f"{int(str(amt).replace(',','').split('.')[0]):,}"
        except Exception as e:
            logger.error("_handle_settle_list: %s", e, exc_info=True)
            amt_fmt = amt
        verb = "ပေးမည့်" if is_pay else "လက်ခံမည့်"
        kb = [[a] for a in FINANCE_ACCOUNTS] + [[BTN_BACK, BTN_CANCEL]]
        await update.message.reply_text(
            f"🏦 *{party} — {amt_fmt} Ks*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"ငွေ {verb} Account ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return PAY_SETTLE_ACCT if is_pay else REC_SETTLE_ACCT
    # Account already set — go straight to confirm
    return await _show_settle_confirm(update, context, kind)

async def _show_settle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, kind: str):
    """Render the settle confirmation screen (account already in d['settle_acct'] or settle_data)."""
    d = context.user_data.get("fin", {})
    r      = d.get("settle_data", [])
    is_pay = kind == "payable"
    party  = (r[1] if len(r) > 1 else "?").strip()
    desc   = (r[2] if len(r) > 2 else "").strip()
    amt    = (r[3] if len(r) > 3 else "0").strip()
    due    = (r[4] if len(r) > 4 else "").strip()
    acct   = d.get("settle_acct") or (r[7] if len(r) > 7 else "").strip()
    try:
        amt_fmt = f"{int(str(amt).replace(',','').split('.')[0]):,}"
    except Exception as e:
        logger.error("_show_settle_confirm: %s", e, exc_info=True)
        amt_fmt = amt
    status_new = "Paid" if is_pay else "Received"
    label = "Payable" if is_pay else "Receivable"
    icon  = "📤" if is_pay else "📥"
    await update.message.reply_text(
        f"{icon} *Settle {label} — အတည်ပြုချက်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 {'Vendor' if is_pay else 'Customer'} : *{party}*\n"
        f"📋 Description      : {desc}\n"
        f"💰 Amount           : *{amt_fmt} Ks*\n"
        f"📅 Due Date         : {due}\n"
        f"🏦 Account          : *{acct or '—'}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ Confirm နှိပ်ရင် Status → *{status_new}*, Date → *{today_str()}*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[BTN_CONFIRM_SAVE], [BTN_BACK, BTN_CANCEL]], resize_keyboard=True),
    )
    return PAY_SETTLE_CONFIRM if is_pay else REC_SETTLE_CONFIRM

async def _handle_settle_acct(update: Update, context: ContextTypes.DEFAULT_TYPE, kind: str):
    """Handle account selection step during settle."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_settle_list(update, context, kind)
    if text not in FINANCE_ACCOUNTS:
        kb = [[a] for a in FINANCE_ACCOUNTS] + [[BTN_BACK, BTN_CANCEL]]
        await update.message.reply_text(
            "⚠️ Account ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return PAY_SETTLE_ACCT if kind == "payable" else REC_SETTLE_ACCT
    context.user_data["fin"]["settle_acct"] = text
    return await _show_settle_confirm(update, context, kind)

async def prompt_advpay_party(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("fin", {})["flow"] = "advpay"
    kb = [["⬅️ Finance Menu", BTN_CANCEL]]
    await update.message.reply_text(
        "💵 *Advance Payment ထည့်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Vendor/Party အမည် ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ADVPAY_PARTY

@log_duration("finance:step_advpay_party")
async def step_advpay_party(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_FIN_BACK or text == "⬅️ Finance Menu":
        return await show_finance_menu(update, context)
    context.user_data["fin"]["advpay_party"] = text
    await update.message.reply_text(
        "📝 ဘာအတွက် ကြိုပေးသလဲ? (Description):",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return ADVPAY_DESC

@log_duration("finance:step_advpay_desc")
async def step_advpay_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        await update.message.reply_text(
            "Party/Vendor ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([["⬅️ Finance Menu", BTN_CANCEL]], resize_keyboard=True),
        )
        return ADVPAY_PARTY
    context.user_data["fin"]["advpay_desc"] = text
    await update.message.reply_text(
        "💰 Amount (Ks) ရိုက်ပါ:",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return ADVPAY_AMT

@log_duration("finance:step_advpay_amt")
async def step_advpay_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        await update.message.reply_text(
            "Description ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return ADVPAY_DESC
    try:
        amt = int(text.replace(",", "").replace(".", ""))
        if amt <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ ပမာဏ မှန်ကန်စွာ ရိုက်ပါ")
        return ADVPAY_AMT
    context.user_data["fin"]["advpay_amt"] = amt
    kb = [[a] for a in FINANCE_ACCOUNTS] + [NAV_ROW]
    await update.message.reply_text(
        f"💰 *{amt:,} Ks* — ထုတ်မည့် Account ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ADVPAY_ACCT

@log_duration("finance:step_advpay_acct")
async def step_advpay_acct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        await update.message.reply_text(
            "Amount ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return ADVPAY_AMT
    if text not in FINANCE_ACCOUNTS:
        kb = [[a] for a in FINANCE_ACCOUNTS] + [NAV_ROW]
        await update.message.reply_text("⚠️ Account ရွေးပါ:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return ADVPAY_ACCT
    context.user_data["fin"]["advpay_acct"] = text
    today = now_mmt().strftime("%-m/%-d/%Y")
    kb = [[today], NAV_ROW]
    await update.message.reply_text(
        "📅 Expected Return/Settle Date (M/D/YYYY):",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ADVPAY_DUE

@log_duration("finance:step_advpay_due")
async def step_advpay_due(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [[a] for a in FINANCE_ACCOUNTS] + [NAV_ROW]
        await update.message.reply_text("Account ပြန်ရွေးပါ:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return ADVPAY_ACCT
    context.user_data["fin"]["advpay_due"] = text
    kb = [["⏩ Skip"], NAV_ROW]
    await update.message.reply_text(
        "📝 Notes (မလိုလျှင် Skip နှိပ်ပါ):",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ADVPAY_NOTE

@log_duration("finance:step_advpay_note")
async def step_advpay_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        today = now_mmt().strftime("%-m/%-d/%Y")
        await update.message.reply_text(
            "Expected Date ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([[today], NAV_ROW], resize_keyboard=True),
        )
        return ADVPAY_DUE
    d = context.user_data["fin"]
    d["advpay_note"] = "" if text == "⏩ Skip" else text
    kb = [[BTN_CONFIRM_SAVE], NAV_ROW]
    await update.message.reply_text(
        "💵 *Advance Payment — အတည်ပြုချက်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 Party      : *{d['advpay_party']}*\n"
        f"📝 Desc       : *{d['advpay_desc']}*\n"
        f"💰 Amount     : *{d['advpay_amt']:,} Ks*\n"
        f"🏦 Account    : *{d['advpay_acct']}*\n"
        f"📅 Expect Date: *{d['advpay_due']}*\n"
        f"📋 Notes      : {d.get('advpay_note') or '—'}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ Confirm & Save နှိပ်ပါ",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ADVPAY_CONFIRM

@log_duration("finance:step_advpay_confirm")
async def step_advpay_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [["⏩ Skip"], NAV_ROW]
        await update.message.reply_text("Notes ပြန်ရိုက်ပါ:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return ADVPAY_NOTE
    if text != BTN_CONFIRM_SAVE:
        await update.message.reply_text("✅ Confirm & Save နှိပ်ပါ")
        return ADVPAY_CONFIRM
    d = context.user_data["fin"]
    await update.message.reply_text("⏳ သိမ်းဆည်းနေသည်...")
    try:
        def _do():
            sh = get_advpay_sh()
            sh.append_row(
                [today_str(), d["advpay_party"], d["advpay_desc"],
                 d["advpay_amt"], d["advpay_acct"], d["advpay_due"],
                 "Pending", d.get("advpay_note", "")],
                value_input_option="USER_ENTERED",
            )
        await asyncio.to_thread(_do)
        # ── API write ──
        async def _api_write():
            try:
                api_add_advance({
                    "advance_date": today_str(),
                    "party": d["advpay_party"],
                    "description": d["advpay_desc"],
                    "amount": d["advpay_amt"],
                    "account": d["advpay_acct"],
                    "due_date": d["advpay_due"],
                    "status": "Pending",
                    "notes": d.get("advpay_note", ""),
                })
            except Exception:
                pass
        asyncio.ensure_future(_api_write())
        await update.message.reply_text(
            f"✅ *Advance Payment မှတ်ပြီး!*\n"
            f"👤 {d['advpay_party']}  |  💰 {d['advpay_amt']:,} Ks\n"
            f"🏦 {d['advpay_acct']}  |  📅 {d['advpay_due']}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    return await show_finance_menu(update, context)

async def show_advpay_settle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all Pending advance payments for settlement."""
    context.user_data.setdefault("fin", {})
    try:
        def _fetch():
            sh = get_advpay_sh()
            return sh.get_all_values()
        rows = await asyncio.to_thread(_fetch)
    except Exception as e:
        await update.message.reply_text(f"❌ Sheet error: {e}")
        return await show_finance_menu(update, context)

    pending = [(i + 2, r) for i, r in enumerate(rows[1:]) if len(r) >= 7 and (r[6] or "").strip().lower() == "pending"]
    if not pending:
        await update.message.reply_text("ℹ️ Pending Advance Payment မရှိပါ")
        return await show_finance_menu(update, context)

    context.user_data["fin"]["advpay_pending"] = pending
    lines = ["💵 *Pending Advance Payments*\n━━━━━━━━━━━━━━━━━━"]
    num_kb = []
    for idx, (_, r) in enumerate(pending):
        party = (r[1] if len(r) > 1 else "?").strip()
        amt   = (r[3] if len(r) > 3 else "0").strip()
        due   = (r[5] if len(r) > 5 else "").strip()
        try:
            amt_fmt = f"{int(str(amt).replace(',','').split('.')[0]):,}"
        except Exception as e:
            logger.error("_fetch: %s", e, exc_info=True)
            amt_fmt = amt
        lines.append(f"{idx+1}. {party}  |  {amt_fmt} Ks  |  {due}")
        num_kb.append([str(idx + 1)])
    num_kb.append([BTN_FIN_BACK, BTN_CANCEL])
    await update.message.reply_text(
        "\n".join(lines) + "\n\nဂဏန်း ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(num_kb, resize_keyboard=True),
    )
    return ADVPAY_LIST

@log_duration("finance:step_advpay_list")
async def step_advpay_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_FIN_BACK:
        return await show_finance_menu(update, context)
    d = context.user_data.get("fin", {})
    pending = d.get("advpay_pending", [])
    try:
        idx = int(text) - 1
        assert 0 <= idx < len(pending)
    except (ValueError, AssertionError):
        await update.message.reply_text("⚠️ မှန်ကန်သော ဂဏန်း ရိုက်ပါ")
        return ADVPAY_LIST
    sheet_row, r = pending[idx]
    d["advpay_settle_row"]  = sheet_row
    d["advpay_settle_data"] = r
    party = (r[1] if len(r) > 1 else "?").strip()
    desc  = (r[2] if len(r) > 2 else "").strip()
    amt   = (r[3] if len(r) > 3 else "0").strip()
    acct  = (r[4] if len(r) > 4 else "").strip()
    due   = (r[5] if len(r) > 5 else "").strip()
    try:
        amt_fmt = f"{int(str(amt).replace(',','').split('.')[0]):,}"
    except Exception as e:
        logger.error("step_advpay_list: %s", e, exc_info=True)
        amt_fmt = amt
    await update.message.reply_text(
        "💵 *Advance Settle — အတည်ပြုချက်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 Party     : *{party}*\n"
        f"📝 Desc      : {desc}\n"
        f"💰 Amount    : *{amt_fmt} Ks*\n"
        f"🏦 Account   : *{acct}*\n"
        f"📅 Due       : {due}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"✅ Confirm → Status *Settled*, Date → *{today_str()}*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[BTN_CONFIRM_SAVE], [BTN_BACK, BTN_CANCEL]], resize_keyboard=True),
    )
    return ADVPAY_SETTLE_CONFIRM

@log_duration("finance:step_advpay_settle_confirm")
async def step_advpay_settle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_advpay_settle(update, context)
    if text != BTN_CONFIRM_SAVE:
        await update.message.reply_text("✅ Confirm & Save နှိပ်ပါ")
        return ADVPAY_SETTLE_CONFIRM
    d = context.user_data.get("fin", {})
    sheet_row = d.get("advpay_settle_row")
    r = d.get("advpay_settle_data", [])
    await update.message.reply_text("⏳ သိမ်းဆည်းနေသည်...")
    try:
        def _do():
            sh = get_advpay_sh()
            # ── API update ──
            api_update_finance_advance(sheet_row, {
                "status": "Settled",
                "settle_date": today_str(),
                "notes": d.get("advpay_note", ""),
            })
            # ── GSheet fallback ──
            sh.update_cell(sheet_row, 7, "Settled")
            sh.update_cell(sheet_row, 8, today_str())
        await asyncio.to_thread(_do)
        party = (r[1] if len(r) > 1 else "?").strip()
        amt   = (r[3] if len(r) > 3 else "0").strip()
        try:
            amt_fmt = f"{int(str(amt).replace(',','').split('.')[0]):,}"
        except Exception as e:
            logger.error("_do: %s", e, exc_info=True)
            amt_fmt = amt
        await update.message.reply_text(
            f"✅ *Advance Settled!*\n"
            f"👤 {party}  |  💰 {amt_fmt} Ks\n"
            f"📅 {today_str()}  |  Status: *Settled*",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    return await show_finance_menu(update, context)

@log_duration("finance:step_pay_settle_list")
async def step_pay_settle_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _handle_settle_list(update, context, "payable")

@log_duration("finance:step_rec_settle_list")
async def step_rec_settle_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _handle_settle_list(update, context, "receivable")

@log_duration("finance:step_pay_settle_acct")
async def step_pay_settle_acct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _handle_settle_acct(update, context, "payable")

@log_duration("finance:step_rec_settle_acct")
async def step_rec_settle_acct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _handle_settle_acct(update, context, "receivable")

async def _handle_settle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, kind: str):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_settle_list(update, context, kind)
    if text != BTN_CONFIRM_SAVE:
        await update.message.reply_text("✅ Confirm & Save နှိပ်ပါ")
        return PAY_SETTLE_CONFIRM if kind == "payable" else REC_SETTLE_CONFIRM
    d = context.user_data.get("fin", {})
    sheet_row = d.get("settle_row")
    is_pay    = kind == "payable"
    status_new = "Paid" if is_pay else "Received"
    await update.message.reply_text("⏳ သိမ်းဆည်းနေသည်...")
    settle_acct = d.get("settle_acct", "")
    try:
        def _do():
            sh = get_payables_sh() if is_pay else get_receivables_sh()
            # ── API update ──
            update_data = {
                "status": status_new,
                "paid_date": today_str(),
                "settle_account": settle_acct,
            }
            if is_pay:
                api_update_finance_payable(sheet_row, update_data)
            else:
                api_update_finance_receivable(sheet_row, update_data)
            # ── GSheet fallback ──
            sh.update_cell(sheet_row, 6, status_new)
            sh.update_cell(sheet_row, 7, today_str())
            if settle_acct:
                sh.update_cell(sheet_row, 8, settle_acct)
        await asyncio.to_thread(_do)
        r     = d.get("settle_data", [])
        party = (r[1] if len(r) > 1 else "?").strip()
        amt   = (r[3] if len(r) > 3 else "0").strip()
        acct_used = settle_acct or (r[7] if len(r) > 7 else "").strip()
        try:
            amt_fmt = f"{int(str(amt).replace(',','').split('.')[0]):,}"
        except Exception as e:
            logger.error("_do: %s", e, exc_info=True)
            amt_fmt = amt
        label = "Payable" if is_pay else "Receivable"
        await update.message.reply_text(
            f"✅ *{label} Settled!*\n"
            f"👤 {party}\n"
            f"💰 {amt_fmt} Ks  |  🏦 {acct_used or '—'}\n"
            f"📅 {today_str()}  |  Status: *{status_new}*",
            parse_mode="Markdown",
        )
        d.pop("settle_acct", None)   # clear for next settle
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    return await show_finance_menu(update, context)

@log_duration("finance:step_pay_settle_confirm")
async def step_pay_settle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _handle_settle_confirm(update, context, "payable")

@log_duration("finance:step_rec_settle_confirm")
async def step_rec_settle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _handle_settle_confirm(update, context, "receivable")

# TODO: Migrate to MySQL via API -- direct gspread is fallback only
def get_capital_sh():
    try:
        result = api_fetch_finance_accounts()
        if result is not None:
            return result
    except Exception:
        pass
    return wb.worksheet("Capital_Setup")
async def show_shareholder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show shareholders list (A=Name, B=Role, C=Capital, D=Ownership%) + Add button."""
    await update.message.reply_text("⏳ Shareholders ဆွဲယူနေသည်...")
    try:
        def _read():
            return get_capital_sh().get_all_values()
        rows = await asyncio.to_thread(_read)
        # Capital_Setup: A=Shareholder, B=Role, C=Capital(Ks), D=Ownership%
        shareholders = [r for r in rows[1:] if r and (r[0] if r else "").strip()]
        lines = ["👥 *Shareholders & Capital*", "━━━━━━━━━━━━━━━━━━"]
        total = 0
        if shareholders:
            for i, r in enumerate(shareholders, 1):
                name  = (r[0] if len(r) > 0 else "?").strip()
                role  = (r[1] if len(r) > 1 else "").strip() or "Partner"
                try:
                    cap = int(str(r[2] if len(r) > 2 else "0").replace(",", ""))
                except ValueError:
                    cap = 0
                try:
                    own = float(str(r[3] if len(r) > 3 else "0").replace(",", "").replace("%", ""))
                except ValueError:
                    own = 0.0
                total += cap
                role_icon = "🔑" if "operation" in role.lower() else "🤝"
                lines.append(
                    f"{i}. 👤 *{name}*\n"
                    f"   {role_icon} {role}  |  📊 {own:.0f}%\n"
                    f"   💰 {cap:,} Ks"
                )
            lines += ["━━━━━━━━━━━━━━━━━━", f"💼 *Total Capital : {total:,} Ks*"]
        else:
            lines.append("_(Shareholders မရှိသေးပါ)_")
    except Exception as e:
        lines = [f"❌ Error: {e}\n💡 ⚙️ Sheet Setup ဖြင့် Finance Sheets ဆောက်ပါ"]

    kb = [["➕ Shareholder ထည့်"], [BTN_FIN_BACK], [BTN_BACK_MAIN]]
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SHARE_NAME

async def step_shareholder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK_MAIN:
        return await show_main_menu(update, context)
    if text == BTN_FIN_BACK:
        return await show_finance_menu(update, context)
    if text == "➕ Shareholder ထည့်":
        return await prompt_share_name(update, context)
    return await show_shareholder_menu(update, context)

async def prompt_share_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("fin", {})["flow"] = "shareholder"
    await update.message.reply_text(
        "👤 *Shareholder အသစ် — (1/4) နာမည်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Shareholder နာမည် ရိုက်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[BTN_BACK, BTN_CANCEL]], resize_keyboard=True),
    )
    return SHARE_NAME

@log_duration("finance:step_share_name")
async def step_share_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK_MAIN:
        return await show_main_menu(update, context)
    if text == BTN_FIN_BACK:
        return await show_finance_menu(update, context)
    if text in (BTN_BACK, "➕ Shareholder ထည့်"):
        return await show_shareholder_menu(update, context)
    if not text:
        await update.message.reply_text("⚠️ နာမည် ရိုက်ပါ")
        return SHARE_NAME
    context.user_data["fin"]["share_name"] = text
    kb = [[r] for r in _SHARE_ROLES] + [[BTN_BACK, BTN_CANCEL]]
    await update.message.reply_text(
        f"👤 *{text}* — (2/4) Role ရွေးပါ",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SHARE_ROLE

@log_duration("finance:step_share_role")
async def step_share_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_share_name(update, context)
    if text not in _SHARE_ROLES:
        await update.message.reply_text("⚠️ Role ရွေးပါ")
        return SHARE_ROLE
    context.user_data["fin"]["share_role"] = text
    await update.message.reply_text(
        f"💼 *{text}* — (3/4) Capital ပမာဏ\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ထည့်ဝင်သော ငွေပမာဏ (Ks) ရိုက်ပါ\n(ဥပမာ: 150000000):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[BTN_BACK, BTN_CANCEL]], resize_keyboard=True),
    )
    return SHARE_CAP

@log_duration("finance:step_share_cap")
async def step_share_cap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [[r] for r in _SHARE_ROLES] + [[BTN_BACK, BTN_CANCEL]]
        await update.message.reply_text(
            "Role ပြန်ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return SHARE_ROLE
    try:
        cap = int(text.replace(",", ""))
        if cap <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ မှန်ကန်သော ပမာဏ ရိုက်ပါ")
        return SHARE_CAP
    context.user_data["fin"]["share_cap"] = cap
    kb = [["33"], ["34"], ["50"], ["100"], [BTN_BACK, BTN_CANCEL]]
    await update.message.reply_text(
        f"💰 *{cap:,} Ks* — (4/4) Ownership %\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ပိုင်ဆိုင်မှု ရာခိုင်နှုန်း ရိုက်ပါ (ဥပမာ: 33):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SHARE_OWN

@log_duration("finance:step_share_own")
async def step_share_own(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        await update.message.reply_text(
            "Capital ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK, BTN_CANCEL]], resize_keyboard=True),
        )
        return SHARE_CAP
    try:
        own = float(text.replace("%", ""))
        if own < 0 or own > 100:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ 0–100 ကြား ဂဏန်း ရိုက်ပါ")
        return SHARE_OWN
    d = context.user_data["fin"]
    d["share_own"] = own
    kb = [[BTN_CONFIRM_SAVE], [BTN_BACK, BTN_CANCEL]]
    await update.message.reply_text(
        "👥 *Shareholder — အတည်ပြုချက်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 နာမည်    : *{d['share_name']}*\n"
        f"💼 Role     : *{d['share_role']}*\n"
        f"💰 Capital  : *{d['share_cap']:,} Ks*\n"
        f"📊 Ownership: *{own:.0f}%*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ Confirm & Save နှိပ်ပါ",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SHARE_CONFIRM

@log_duration("finance:step_share_confirm")
async def step_share_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [["33"], ["34"], ["50"], ["100"], [BTN_BACK, BTN_CANCEL]]
        await update.message.reply_text(
            "Ownership % ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return SHARE_OWN
    if text != BTN_CONFIRM_SAVE:
        await update.message.reply_text("✅ Confirm & Save နှိပ်ပါ")
        return SHARE_CONFIRM
    d = context.user_data["fin"]
    name = d["share_name"]
    role = d["share_role"]
    cap  = d["share_cap"]
    own  = d["share_own"]
    await update.message.reply_text("⏳ သိမ်းဆည်းနေသည်...")
    try:
        def _do():
            # Capital_Setup: A=Shareholder, B=Role, C=Capital(Ks), D=Ownership%
            sh = get_capital_sh()
            sh.append_row([name, role, cap, own], value_input_option="USER_ENTERED")
        await asyncio.to_thread(_do)
        # ── API write ──
        async def _api_write():
            try:
                api_add_advance({
                    "advance_date": today_str(),
                    "staff": name,
                    "amount": cap,
                    "description": f"Share capital: {role} ({own:.0f}%)",
                    "status": "active"
                })
            except Exception:
                pass
        asyncio.ensure_future(_api_write())
        await update.message.reply_text(
            f"✅ *Shareholder မှတ်တမ်း သိမ်းပြီး!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 {name}  |  💼 {role}\n"
            f"💰 {cap:,} Ks  |  📊 {own:.0f}%",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {e}\n💡 ⚙️ Sheet Setup ဖြင့် Capital_Setup sheet ဆောက်ပါ"
        )
    return await show_shareholder_menu(update, context)

async def prompt_cap_acct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("fin", {})["flow"] = "capital"
    kb = [[a] for a in CAPITAL_ACCOUNTS] + [NAV_ROW]
    await update.message.reply_text(
        "🏦 *Initial Capital — Account ရွေးပါ*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ငွေ ထည့်မည့် Account ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return CAP_ACCT

@log_duration("finance:step_cap_acct")
async def step_cap_acct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await show_finance_menu(update, context)
    if text not in CAPITAL_ACCOUNTS:
        await update.message.reply_text("⚠️ Account ရွေးပါ")
        return CAP_ACCT
    context.user_data["fin"]["cap_acct"] = text
    await update.message.reply_text(
        f"🏦 *{text}* — Initial Capital ပမာဏ\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ငွေပမာဏ ရိုက်ပါ (ဥပမာ: 300000000):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return CAP_AMT

@log_duration("finance:step_cap_amt")
async def step_cap_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        kb = [[a] for a in CAPITAL_ACCOUNTS] + [NAV_ROW]
        await update.message.reply_text(
            "Account ပြန်ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return CAP_ACCT
    try:
        amt = int(text.replace(",", ""))
        if amt <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("⚠️ မှန်ကန်သော ပမာဏ ရိုက်ပါ")
        return CAP_AMT
    context.user_data["fin"]["cap_amt"] = amt
    d = context.user_data["fin"]
    kb = [[BTN_CONFIRM_SAVE], NAV_ROW]
    await update.message.reply_text(
        "🏦 *Initial Capital — အတည်ပြုချက်*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🏦 Account  : *{d['cap_acct']}*\n"
        f"💰 Amount   : *{amt:,} Ks*\n"
        f"📅 Date     : *{today_str()}*\n"
        f"📋 Type     : *Opening Balance*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ Confirm & Save နှိပ်ပါ",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return CAP_CONFIRM

@log_duration("finance:step_cap_confirm")
async def step_cap_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        await update.message.reply_text(
            "Amount ပြန်ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return CAP_AMT
    if text != BTN_CONFIRM_SAVE:
        await update.message.reply_text("✅ Confirm & Save နှိပ်ပါ")
        return CAP_CONFIRM
    d = context.user_data["fin"]
    acct = d["cap_acct"]
    amt  = d["cap_amt"]
    await update.message.reply_text("⏳ သိမ်းဆည်းနေသည်...")
    try:
        def _do():
            # ── API write (MySQL) ──
            try:
                existing = api_fetch_finance_accounts()
                if existing and isinstance(existing, dict) and existing.get("success"):
                    data = existing.get("data", [])
                    found = False
                    for item in data:
                        if isinstance(item, dict) and str(item.get("name", "")).strip() == acct:
                            # Update existing
                            api_update_finance_opex(item.get("id", 0), {"amount": amt})
                            found = True
                            return "updated"
                    if not found:
                        # Append new
                        api_add_opex({
                            "date": today_str(),
                            "category": "Capital",
                            "description": f"{acct} - Initial Capital",
                            "amount": amt,
                            "account": acct,
                            "payment": "Cash"
                        })
                        return "added"
            except Exception:
                pass
            # ── GSheet fallback ──
            sh = wb.worksheet("Accounts")
            rows = sh.get_all_values()
            for i, row in enumerate(rows[1:], start=2):
                if (row[0] if row else "").strip() == acct:
                    sh.update_cell(i, 3, amt)
                    return "updated"
            acct_type = "Bank" if ("bank" in acct.lower() or "kbz" in acct.lower() or "aya" in acct.lower()) else ("Digital" if "mmqr" in acct.lower() else "Cash")
            sh.append_row([acct, acct_type, amt, "Initial Capital"], value_input_option="USER_ENTERED")
            return "added"
        result = await asyncio.to_thread(_do)
        action = "အပ်ဒိတ်" if result == "updated" else "ထည့်သွင်း"
        await update.message.reply_text(
            f"✅ *Initial Capital {action}ပြီး!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🏦 {acct}\n"
            f"💰 {amt:,} Ks\n\n"
            f"💡 Account Balances တွင် ယခု ပြသမည်",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {e}\n\n"
            f"💡 ⚙️ Sheet Setup ကို ဦးစွာ လုပ်ဆောင်ပြီး Accounts sheet ဆောက်ပါ"
        )
    return await show_finance_menu(update, context)

async def show_fin_report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [BTN_FIN_PNL,          BTN_FIN_BS],
        [BTN_FIN_DEPR,         BTN_FIN_PROFIT_SHARE],
        [BTN_FIN_BACK],
        [BTN_BACK_MAIN],
    ]
    await update.message.reply_text(
        "📊 *Finance Reports*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "ကြည့်လိုသော Report ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return FIN_REPORT_MENU

@log_duration("finance:step_fin_report_menu")
async def step_fin_report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    if choice == BTN_FIN_BACK:
        return await show_finance_menu(update, context)
    if choice == BTN_BACK_MAIN:
        return await show_main_menu(update, context)
    if choice == BTN_FIN_PNL:
        return await cmd_fin_pnl(update, context)
    if choice == BTN_FIN_BS:
        return await cmd_fin_bs(update, context)
    if choice == BTN_FIN_DEPR:
        return await cmd_fin_depr(update, context)
    if choice == BTN_FIN_PROFIT_SHARE:
        return await cmd_fin_profit_share(update, context)
    return await show_fin_report_menu(update, context)

async def cmd_fin_pnl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch P&L from VPS API."""
    await update.message.reply_text("⏳ P&L ဆွဲယူနေသည်...")
    now = now_mmt()
    m   = now.strftime("%Y-%m")
    data = await _psvibe_get_async(f"finance/pnl?m={m}")
    if not data:
        await update.message.reply_text("❌ P&L API ချိတ်မရပါ — VPS စစ်ပါ")
        return await show_fin_report_menu(update, context)
    rev          = data.get("revenue", {})
    topup        = data.get("topup", {})
    opex_cats    = data.get("opex", {})
    total_opex   = data.get("total_opex", 0)
    depr         = data.get("depreciation", 0)
    disp_gl      = data.get("disposal_gain_loss", 0)
    ebit         = data.get("ebit", 0)
    om_bonus     = data.get("om_bonus", 0)
    net          = data.get("net_profit", 0)
    payroll      = opex_cats.get("Payroll", 0)
    other_opex   = total_opex - payroll
    total_costs  = total_opex + depr
    game_rev     = rev.get("game", 0)
    food_rev     = rev.get("food", 0)
    discounts    = rev.get("discounts", 0)
    topup_rev    = topup.get("total", 0)
    total_rev    = rev.get("total", 0)        # excludes topup — topup is liability, not revenue
    month_label  = now.strftime("%B %Y")
    lines = [
        f"📊 *P&L Report — {month_label}*",
        "━━━━━━━━━━━━━━━━━━",
        "💰 *Revenue*",
        f"  Game Play    : {game_rev:>12,} Ks",
        f"  Food & Drink : {food_rev:>12,} Ks",
    ]
    if discounts:
        lines.append(f"  Discount     :({discounts:>11,} Ks)")
    lines += [
        f"  ─────────────────────────",
        f"  Total Revenue: {total_rev:>12,} Ks",
        f"  TopUp (Liab) : {topup_rev:>12,} Ks",
        "━━━━━━━━━━━━━━━━━━",
        "📤 *Operating Costs*",
        f"  Payroll      : {payroll:>12,} Ks",
        f"  OPEX         : {other_opex:>12,} Ks",
        f"  Depreciation : {depr:>12,} Ks",
        f"  ─────────────────────────",
        f"  Total Costs  : {total_costs:>12,} Ks",
    ]
    if disp_gl != 0:
        label = "Disposal Gain" if disp_gl > 0 else "Disposal Loss"
        sign  = "+" if disp_gl > 0 else ""
        lines += [
            "━━━━━━━━━━━━━━━━━━",
            f"🔄 *Other Items*",
            f"  {label:<13}: {sign}{disp_gl:>10,} Ks",
        ]
    lines += [
        "━━━━━━━━━━━━━━━━━━",
        f"  EBIT         : {ebit:>12,} Ks",
    ]
    if om_bonus:
        lines.append(f"  OM Bonus(10%):({om_bonus:>11,} Ks)")
    lines += [
        f"{'✅' if net >= 0 else '🔴'} *Net Profit : {net:,} Ks*",
    ]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    return await show_fin_report_menu(update, context)

async def cmd_fin_bs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch Balance Sheet from VPS API."""
    await update.message.reply_text("⏳ Balance Sheet ဆွဲယူနေသည်...")
    data = await _psvibe_get_async("finance/balance-sheet")
    if not data:
        await update.message.reply_text("❌ Balance Sheet API ချိတ်မရပါ")
        return await show_fin_report_menu(update, context)
    assets     = data.get("assets", {})
    liab       = data.get("liabilities", {})
    equity     = data.get("equity", {})
    assets_tot = assets.get("total", 0)
    liab_tot   = liab.get("total", 0)
    equity_tot = equity.get("total", 0)
    cash_net   = assets.get("current_total", 0)
    fixed_tot  = assets.get("fixed_total", 0)
    receivables = assets.get("receivables", 0)
    advances_pending = assets.get("advances_pending", 0)
    member_liab = liab.get("member_liability", 0)
    payables    = liab.get("payables", 0)
    lines = [
        "🏦 *Balance Sheet*",
        "━━━━━━━━━━━━━━━━━━",
        "📦 *Assets*",
        f"  Cash (Net)    : {cash_net:>12,} Ks",
        f"  Fixed Assets  : {fixed_tot:>12,} Ks",
        f"  Receivables   : {receivables:>12,} Ks",
    ]
    if advances_pending:
        lines.append(f"  Adv. Pending  : {advances_pending:>12,} Ks")
    lines += [
        f"  ─────────────────────────",
        f"  Total Assets  : {assets_tot:>12,} Ks",
        "━━━━━━━━━━━━━━━━━━",
        "📤 *Liabilities*",
        f"  Member Liab   : {member_liab:>12,} Ks",
        f"  Payables      : {payables:>12,} Ks",
        f"  ─────────────────────────",
        f"  Total Liab    : {liab_tot:>12,} Ks",
        "━━━━━━━━━━━━━━━━━━",
        f"💼 *Equity : {equity_tot:,} Ks*",
    ]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    return await show_fin_report_menu(update, context)

async def cmd_fin_accts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch account balances from VPS API. Always returns to Finance main menu."""
    await update.message.reply_text("⏳ Account Balances ဆွဲယူနေသည်...")
    data = await _psvibe_get_async("finance/account-balances")
    if not data:
        await update.message.reply_text(
            "❌ Account Balances API ချိတ်မရပါ\n"
            "💡 ခဏစောင့်ပြီး ပြန်ကြိုးစားပါ"
        )
        return await show_finance_menu(update, context)
    operating = data.get("operating", [])
    capital = data.get("capital", [])
    all_accounts = operating + capital
    store_total = data.get("store_total", 0)
    acm_total = data.get("acm_total", 0)
    grand_total = data.get("grand_total", 0)
    lines = ["💰 *Account Balances*", "━━━━━━━━━━━━━━━━━━"]
    for a in all_accounts:
        name = a.get("name", "?")
        bal = int(a.get("balance", 0))
        low = name.lower()
        if "kbz" in low:
            icon = "🏦"
        elif "acm" in low:
            icon = "🏦"
        elif "kpay" in low:
            icon = "📱"
        elif "wave" in low:
            icon = "📱"
        elif "aya" in low:
            icon = "💳"
        elif "cash" in low:
            icon = "💵"
        else:
            icon = "💵"
        lines.append(f"{icon} {name:<16}: {bal:>10,} Ks")
    lines += ["", f"🏪 ဆိုင်ငွေ : {int(store_total):,} Ks"]
    lines += [f"🏦 ACM's Acc: {int(acm_total):,} Ks"]
    lines += ["━━━━━━━━━━━━━━━━━━", f"  *Grand Total : {int(grand_total):,} Ks*"]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    return await show_finance_menu(update, context)

async def cmd_fin_depr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show depreciation summary from VPS API."""
    await update.message.reply_text("⏳ Depreciation ဆွဲယူနေသည်...")
    now_yr = now_mmt().year
    data = await _psvibe_get_async(f"finance/depreciation?year={now_yr}")
    if not data:
        await update.message.reply_text("❌ Depreciation API ချိတ်မရပါ")
        return await show_fin_report_menu(update, context)
    schedule   = data.get("schedule", [])
    year_total = data.get("year_total", 0)
    if not schedule:
        await update.message.reply_text("📉 Assets_Register တွင် မှတ်တမ်းမရှိပါ")
        return await show_fin_report_menu(update, context)
    lines = [f"📉 *Depreciation — {now_yr}*", "━━━━━━━━━━━━━━━━━━"]
    for a in schedule[:10]:
        name    = a.get("name", "?")[:20]
        annual  = a.get("year_total", 0)
        bv_end  = a.get("book_value_end", 0)
        dep_mo  = round(annual / 12) if annual else 0
        lines.append(f"🏷️ *{name}*\n   📉 {dep_mo:,}/mo  |  Annual: {annual:,} Ks\n   📘 Book Value (yr-end): {bv_end:,} Ks")
    lines += ["━━━━━━━━━━━━━━━━━━", f"📊 *Total Dep {now_yr}: {year_total:,} Ks*"]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    return await show_fin_report_menu(update, context)

async def cmd_fin_profit_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show profit sharing distribution."""
    await update.message.reply_text("⏳ Profit Sharing ဆွဲယူနေသည်...")
    now  = now_mmt()
    m    = now.strftime("%Y-%m")
    data = await _psvibe_get_async(f"finance/profit-sharing?m={m}")
    if not data:
        await update.message.reply_text("❌ Profit Sharing API ချိတ်မရပါ")
        return await show_fin_report_menu(update, context)
    ebit         = data.get("ebit", 0)
    om_bonus     = data.get("om_bonus", 0)
    distributable = data.get("distributable_profit", 0)
    shareholders = data.get("shareholders", [])
    month_label  = now.strftime("%B %Y")
    lines = [
        f"💸 *Profit Sharing — {month_label}*",
        "━━━━━━━━━━━━━━━━━━",
        f"💰 Net Profit   : *{ebit:,} Ks*",
        f"🎯 OM Bonus     : *{om_bonus:,} Ks*",
        f"📊 Distributable: *{distributable:,} Ks*",
        "━━━━━━━━━━━━━━━━━━",
    ]
    for s in shareholders:
        name      = s.get("name", "?")
        pct       = s.get("ownership", 0)
        dividend  = s.get("dividend", 0)
        s_bonus   = s.get("om_bonus", 0)
        total_inc = s.get("total_income", 0)
        if s_bonus:
            lines.append(f"👤 {name} ({pct}%) : {dividend:,} + {s_bonus:,} bonus = *{total_inc:,} Ks*")
        else:
            lines.append(f"👤 {name} ({pct}%) : {total_inc:,} Ks")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    return await show_fin_report_menu(update, context)

async def cmd_finance_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create all Finance sheets via VPS API."""
    await update.message.reply_text(
        "⚙️ Finance Sheets ဆောက်နေသည်...\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Capital Setup | Assets Register | OPEX Log\n"
        "Accounts | Account Transfers\n"
        "Payables | Receivables | Advance Staff\n"
        "Prepaid Expenses | Advance Payments",
    )
    result = await _psvibe_post_async("finance/setup-sheets", {})
    if result and result.get("ok"):
        created = result.get("created", [])
        skipped = result.get("skipped", [])
        created_str = ", ".join(created) if created else "None"
        skipped_str = ", ".join(skipped) if skipped else "None"
        await update.message.reply_text(
            f"✅ Finance Sheets ပြင်ဆင်ပြီး!\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ Created : {len(created)} sheets\n"
            f"⏩ Skipped : {len(skipped)} (ရှိပြီးသား)\n\n"
            f"Created: {created_str}\n"
            f"Skipped: {skipped_str}",
        )
    else:
        err = result.get("error", "unknown") if result else "API ချိတ်မရ"
        await update.message.reply_text(f"❌ Setup မအောင်မြင်ပါ: {err}")
    return await show_finance_menu(update, context)

async def cmd_finance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /finance — PIN then Finance menu."""
    return await _pin_then("finance", "Finance", update, context)
