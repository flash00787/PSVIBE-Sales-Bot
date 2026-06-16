from bot import (
    BTN_BACK_MAIN, BTN_CONFIRM_SAVE, BTN_SI_ADD, BTN_SI_FINISH,
    BTN_SI_SPLIT, MAIN_MENU, SI_CART, SI_CONFIRM, SI_COST, SI_ITEM,
    SI_PAY, SI_PAY_SPLIT, SI_QTY, fetch_food_costs, fetch_food_prices,
    now_mmt, show_main_menu,
    fetch_food_prices_async,
    fetch_food_costs_async,
)

try:
    from bot.api_client import api_add_stock_in, api_post
except ImportError:
    def api_add_stock_in(data): return None
    api_post = None
"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta

# Explicit import for helper from stock module
# update_inv_total_k1 imported lazily in functions below




async def show_si_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show food item list for Stock In (restock) recording."""
    food_prices = await fetch_food_prices_async()
    context.user_data["si_food_prices"] = food_prices
    names = list(food_prices.keys())
    rows  = [names[i: i + 2] for i in range(0, len(names), 2)]
    kb    = rows + [[BTN_BACK_MAIN]]
    await update.message.reply_text(
        "📥 *Stock In — ဝယ်ယူသော ပစ္စည်းကို ရွေးပါ*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SI_ITEM

async def step_si_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    if choice == BTN_BACK_MAIN:
        return await show_main_menu(update, context)
    food_prices = context.user_data.get("si_food_prices", {})
    if choice not in food_prices:
        await update.message.reply_text("❌ ပစ္စည်း မရှိပါ။ ပြန်ရွေးပါ။")
        return SI_ITEM
    context.user_data["si_item"] = choice
    kb = [["1", "2", "3", "5", "10"], [BTN_BACK_MAIN]]
    await update.message.reply_text(
        f"📥 *{choice}*\n\nဝယ်ယူသော အရေအတွက် ထည့်ပါ (ဥပမာ: 10) -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SI_QTY

async def step_si_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK_MAIN:
        return await show_main_menu(update, context)
    try:
        qty = int(text)
    except ValueError:
        await update.message.reply_text("❌ ဂဏန်းသက်သက် ရိုက်ပေးပါ -")
        return SI_QTY
    if qty <= 0:
        await update.message.reply_text("❌ အရေအတွက် 1 နှင့်အထက် ဖြစ်ရမည် -")
        return SI_QTY
    context.user_data["si_qty"] = qty
    item = context.user_data.get("si_item", "")
    food_costs = await fetch_food_costs_async()
    default_cost = food_costs.get(item, 0)
    hint = f" (Default: {default_cost:,} Ks)" if default_cost else ""
    kb = [[BTN_BACK_MAIN]]
    await update.message.reply_text(
        f"📥 *{item}* × {qty}\n\nတစ်ခုစျေးနှုန်း (Unit Cost) ရိုက်ပါ{hint} -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SI_COST

async def step_si_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK_MAIN:
        return await show_main_menu(update, context)
    try:
        cost = int(text.replace(",", ""))
    except ValueError:
        await update.message.reply_text("❌ ဂဏန်းသက်သက် ရိုက်ပေးပါ (ဥပမာ: 2000) -")
        return SI_COST
    if cost < 0:
        await update.message.reply_text("❌ 0 နှင့်အထက် ဖြစ်ရမည် -")
        return SI_COST

    # Add this item to the cart
    item  = context.user_data.get("si_item", "")
    qty   = context.user_data.get("si_qty", 0)
    total = qty * cost
    cart  = context.user_data.setdefault("si_cart", [])
    cart.append({"item": item, "qty": qty, "cost": cost, "total": total})

    # Clear per-item temp data
    for k in ("si_item", "si_qty"):
        context.user_data.pop(k, None)

    return await show_si_cart(update, context)

async def show_si_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show running cart summary with options to add more or proceed to payment."""
    cart = context.user_data.get("si_cart", [])
    grand_total = sum(e["total"] for e in cart)
    lines = []
    for i, e in enumerate(cart, 1):
        lines.append(
            f"{i}. *{e['item']}*  ×{e['qty']}  @{e['cost']:,}  = *{e['total']:,} Ks*"
        )
    cart_text = "\n".join(lines)
    kb = [[BTN_SI_ADD], [BTN_SI_FINISH], [BTN_BACK_MAIN]]
    await update.message.reply_text(
        f"🛒 *Stock In Cart — {len(cart)} item(s)*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{cart_text}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Grand Total : *{grand_total:,} Ks*\n\n"
        f"➕ Item ထပ်ဝယ်မည်လား? ၀ယ်ပြီးလျှင် Payment ဆက်သွားပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SI_CART

async def step_si_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK_MAIN:
        context.user_data.pop("si_cart", None)
        return await show_main_menu(update, context)
    if text == BTN_SI_ADD:
        return await show_si_items(update, context)
    if text == BTN_SI_FINISH:
        cart        = context.user_data.get("si_cart", [])
        grand_total = sum(e["total"] for e in cart)
        kb = [["Cash", "KPay"], [BTN_SI_SPLIT], [BTN_BACK_MAIN]]
        await update.message.reply_text(
            f"💳 *{len(cart)} items — Grand Total: {grand_total:,} Ks*\n\n"
            f"ငွေပေးချေမှု နည်းလမ်း ရွေးပါ -\n"
            f"_(ငွေခွဲပေးမည်ဆိုရင် ္'ခွဲပေး' ကို နှိပ်ပါ)_",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return SI_PAY
    await update.message.reply_text("⬆️ ပေါ်ရှိ ခလုတ်များမှ ရွေးပါ -")
    return SI_CART

async def _show_si_review(update, context):
    """Shared review screen for Stock In — called from step_si_pay and step_si_pay_split."""
    d           = context.user_data
    cart        = d.get("si_cart", [])
    grand_total = sum(e["total"] for e in cart)
    lines = [
        f"• *{e['item']}*  ×{e['qty']}  @{e['cost']:,}/pc  = {e['total']:,} Ks"
        for e in cart
    ]
    # Build payment display
    if d.get("si_pay_cash") is not None:
        cash_amt  = d["si_pay_cash"]
        kpay_amt  = d["si_pay_kpay"]
        pay_line  = f"💵 Cash  : *{cash_amt:,} Ks*\n💙 KPay  : *{kpay_amt:,} Ks*"
    else:
        pay_line  = f"💳 Payment : *{d.get('si_pay', '')}*"
    kb = [[BTN_CONFIRM_SAVE], [BTN_BACK_MAIN]]
    await update.message.reply_text(
        f"📋 *Review — Stock In ({len(cart)} items)*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{chr(10).join(lines)}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Grand Total : *{grand_total:,} Ks*\n"
        f"{pay_line}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"မှန်ကန်ပါသလား? ✅ Confirm & Save နှိပ်ပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SI_CONFIRM

async def step_si_pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK_MAIN:
        return await show_si_cart(update, context)

    # Split payment option
    if text == BTN_SI_SPLIT:
        cart        = context.user_data.get("si_cart", [])
        grand_total = sum(e["total"] for e in cart)
        context.user_data.pop("si_pay", None)
        context.user_data.pop("si_pay_cash", None)
        context.user_data.pop("si_pay_kpay", None)
        kb = [[BTN_BACK_MAIN]]
        await update.message.reply_text(
            f"💵 *ခွဲပေး — Grand Total: {grand_total:,} Ks*\n\n"
            f"Cash ဘယ်လောက်ပေးမည်? (ဂဏန်းသက်သက် ရိုက်ပါ)\n"
            f"KPay = {grand_total:,} - Cash ဖြင့် အလိုအလျောက် တွက်မည်",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return SI_PAY_SPLIT

    if text not in ("Cash", "KPay"):
        await update.message.reply_text("❌ Cash / KPay / ခွဲပေး မှ ရွေးပါ -")
        return SI_PAY

    context.user_data["si_pay"]      = text
    context.user_data.pop("si_pay_cash", None)
    context.user_data.pop("si_pay_kpay", None)
    return await _show_si_review(update, context)

async def step_si_pay_split(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Collect Cash portion; KPay = Grand Total - Cash."""
    text = update.message.text.strip()
    if text == BTN_BACK_MAIN:
        return await show_si_cart(update, context)
    try:
        cash_amt = int(text.replace(",", ""))
    except ValueError:
        await update.message.reply_text("❌ ဂဏန်းသက်သက် ရိုက်ပေးပါ (ဥပမာ: 20000) -")
        return SI_PAY_SPLIT
    if cash_amt < 0:
        await update.message.reply_text("❌ 0 နှင့်အထက် ဖြစ်ရမည် -")
        return SI_PAY_SPLIT
    cart        = context.user_data.get("si_cart", [])
    grand_total = sum(e["total"] for e in cart)
    if cash_amt > grand_total:
        await update.message.reply_text(
            f"❌ Cash {cash_amt:,} Ks သည် Grand Total {grand_total:,} Ks ထက် မကျော်သင့်ပါ -"
        )
        return SI_PAY_SPLIT
    kpay_amt = grand_total - cash_amt
    context.user_data["si_pay_cash"] = cash_amt
    context.user_data["si_pay_kpay"] = kpay_amt
    context.user_data.pop("si_pay", None)
    return await _show_si_review(update, context)

async def step_si_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK_MAIN:
        return await show_si_cart(update, context)
    if text != BTN_CONFIRM_SAVE:
        return SI_CONFIRM
    d       = context.user_data
    cart      = d.get("si_cart", [])
    today     = now_mmt().strftime("%-m/%-d/%Y")
    # Build payment string for sheet
    if d.get("si_pay_cash") is not None:
        cash_amt  = d["si_pay_cash"]
        kpay_amt  = d["si_pay_kpay"]
        payment   = f"Cash {cash_amt:,} / KPay {kpay_amt:,}"
    else:
        payment   = d.get("si_pay", "")
    try:
        grand_total = sum(e["total"] for e in cart)
        is_split = d.get("si_pay_cash") is not None
        if is_split:
            cash_amt  = d["si_pay_cash"]
            kpay_amt  = d["si_pay_kpay"]
        for e in cart:
            # ── API write (primary) ──
            api_ok = False
            if api_post:
                try:
                    payload = {
                        "item_name": e["item"],
                        "quantity": e["qty"],
                        "unit_cost": e["cost"],
                        "payment_method": payment,  # composite for display / GSheet compat
                        "paid_by": "Bot",
                        "staff_name": "Bot",
                    }
                    if is_split:
                        # Split payment: compute this item's share of Cash and KPay
                        item_cash = round(cash_amt * e["total"] / grand_total)
                        item_kpay = e["total"] - item_cash
                        payload["cash_amount"] = item_cash
                        payload["kpay_amount"] = item_kpay
                    result = api_post("stock/in", payload)
                    if result and result.get("success"):
                        api_ok = True
                        logging.info("Stock-in API saved: %s x%d cost=%d payment=%s", e["item"], e["qty"], e["cost"], payment)
                    else:
                        logging.warning("Stock-in API returned success=False: %s", result)
                except Exception as ex:
                    logging.warning("Stock-in API write failed: %s", ex)
            # GSheet fallback removed — API is primary write path
            if not api_ok:
                logging.info("Stock in saved (GSheet only): %s x%d cost=%d", e["item"], e["qty"], e["cost"])
        grand_total = sum(e["total"] for e in cart)
        total_note  = ""
        lines = [
            f"• *{e['item']}*  ×{e['qty']}  = {e['total']:,} Ks"
            for e in cart
        ]
        # Payment display in success message
        if d.get("si_pay_cash") is not None:
            pay_display = f"💵 Cash {d['si_pay_cash']:,} Ks + 💙 KPay {d['si_pay_kpay']:,} Ks"
        else:
            pay_display = payment
        msg = (
            f"✅ *Stock In မှတ်တမ်းတင်ပြီး ({len(cart)} items)*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{chr(10).join(lines)}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 Grand Total : *{grand_total:,} Ks*\n"
            f"💳 Payment     : {pay_display}\n"
            f"📅 Date        : {today}"
            f"{total_note}"
        )
    except Exception as e:
        logging.error("Stock in failed: %s", e)
        msg = f"❌ မှတ်တမ်းတင်မှု မအောင်မြင်ပါ။\n{e}"

    for k in ("si_item", "si_qty", "si_cart", "si_pay", "si_pay_cash", "si_pay_kpay", "si_food_prices"):
        context.user_data.pop(k, None)
    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
    )
    return MAIN_MENU
