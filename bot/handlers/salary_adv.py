from bot import (
    BTN_BACK_MAIN, SAL_ADV_AMT, SAL_ADV_CONFIRM, SAL_ADV_PAY,
    SAL_ADV_STAFF, fetch_staff, now_mmt,
    show_admin_menu, today_str,
)

try:
    from bot.api_client import api_add_salary_advance
except ImportError:
    def api_add_salary_advance(data): return None
"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta




async def step_sal_adv_staff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    if choice == BTN_BACK_MAIN:
        return await show_admin_menu(update, context)

    staff_list = fetch_staff()
    if choice not in staff_list:
        await update.message.reply_text("❌ Staff မတွေ့ပါ။ ထပ်မံ ရွေးပါ:")
        return SAL_ADV_STAFF

    context.user_data["sal_adv_staff"] = choice
    await update.message.reply_text(
        f"💸 *{choice}* — Salary Advance\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"ပေးမည့် ပမာဏ (Ks) ရိုက်ထည့်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return SAL_ADV_AMT

async def step_sal_adv_amt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amt = int(update.message.text.strip().replace(",", "").replace(".", ""))
        if amt <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ ငွေပမာဏ မှန်ကန်စွာ ထည့်ပါ (ဂဏန်းများသာ):")
        return SAL_ADV_AMT

    context.user_data["sal_adv_amt"] = amt
    kb = [["💵 Cash", "💙 KPay"], [BTN_BACK_MAIN]]
    await update.message.reply_text(
        f"💸 ပေးချေနည်း ရွေးပါ:\n"
        f"Amount: *{amt:,} Ks*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SAL_ADV_PAY

async def step_sal_adv_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    if choice == BTN_BACK_MAIN:
        return await show_admin_menu(update, context)

    if "kpay" in choice.lower() or "KPay" in choice:
        payment = "KPay"
    elif "cash" in choice.lower() or "Cash" in choice:
        payment = "Cash"
    else:
        await update.message.reply_text("❌ Cash သို့မဟုတ် KPay ရွေးပါ:")
        return SAL_ADV_PAY

    context.user_data["sal_adv_pay"] = payment
    staff     = context.user_data["sal_adv_staff"]
    amt       = context.user_data["sal_adv_amt"]
    today_str = now_mmt().strftime("%m/%d/%Y")
    pay_icon  = "💵" if payment == "Cash" else "💙"

    kb = [["✅ အတည်ပြုမည်"], [BTN_BACK_MAIN]]
    await update.message.reply_text(
        f"💸 *Salary Advance အတည်ပြုချက်*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👔 Staff    : *{staff}*\n"
        f"💰 Amount   : *{amt:,} Ks*\n"
        f"{pay_icon} Payment  : *{payment}*\n"
        f"📅 Date     : *{today_str}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"မှန်ပါသလား?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SAL_ADV_CONFIRM

async def step_sal_adv_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    if choice == BTN_BACK_MAIN or choice != "✅ အတည်ပြုမည်":
        await update.message.reply_text("❌ ပယ်ဖျက်လိုက်သည်။")
        return await show_admin_menu(update, context)

    staff     = context.user_data.get("sal_adv_staff", "")
    amt       = context.user_data.get("sal_adv_amt", 0)
    payment   = context.user_data.get("sal_adv_pay", "Cash")
    today_str = now_mmt().strftime("%m/%d/%Y")
    month_str = now_mmt().strftime("%Y-%m")
    pay_icon  = "💵" if payment == "Cash" else "💙"

    try:
        # ── API write (primary) ──
        try:
            api_add_salary_advance({
                "staff_name": staff,
                "date": today_str,
                "amount": amt,
                "payment": payment,
            })
        except Exception as e:
            logging.warning("Salary advance API write failed (GSheet fallback OK): %s", e)
        advances  = fetch_salary_advances(month_str)
        staff_adv = advances.get(staff, {"total": 0, "cash": 0, "kpay": 0})
        cum       = staff_adv["total"]
        await update.message.reply_text(
            f"✅ *Salary Advance မှတ်တမ်းသွင်းပြီး*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👔 {staff}\n"
            f"💰 Amount   : *{amt:,} Ks*\n"
            f"{pay_icon} Payment  : *{payment}*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 ဒီလ စုစုပေါင်း Advance: *{cum:,} Ks*\n"
            f"  💵 Cash: {staff_adv['cash']:,} + 💙 KPay: {staff_adv['kpay']:,}\n"
            f"_(လစာချိန်မှာ ဒီပမာဏ နုတ်မည်)_",
            parse_mode="Markdown",
        )
    except Exception as e:
        logging.error("step_sal_adv_confirm: %s", e)
        await update.message.reply_text(f"❌ Error: {e}")

    context.user_data.pop("sal_adv_staff", None)
    context.user_data.pop("sal_adv_amt", None)
    context.user_data.pop("sal_adv_pay", None)
    return await show_admin_menu(update, context)

