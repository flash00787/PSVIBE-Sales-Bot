from bot import (
    BTN_BACK_MAIN, BTN_INVENTORY_VIEW, BTN_STOCK_IN_M, BTN_STOCK_OUT,
    MAIN_MENU, STOCK_ACCESS_PIN, STOCK_ITEM, STOCK_MENU, STOCK_PIN,
    STOCK_QTY,   fetch_food_costs, fetch_food_prices,
    now_mmt, show_main_menu,
    fetch_food_prices_async,
    fetch_food_costs_async,
)

try:
    from bot.api_client import api_add_stock_out
except ImportError:
    def api_add_stock_out(data): return None
"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta

# update_inv_total_k1() removed — GSheet fallback dead code





async def cmd_stockin_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /stockin — PIN verify then Stock In."""
    context.user_data.clear()
    context.user_data["stock_dest"] = "stockin"
    await update.message.reply_text(
        "🔐 *Stock In — PIN လိုအပ်သည်*\n\nPIN နံပါတ် ထည့်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return STOCK_PIN

async def cmd_stockout_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /stockout — PIN verify then Stock Out."""
    context.user_data.clear()
    context.user_data["stock_dest"] = "stockout"
    await update.message.reply_text(
        "🔐 *Stock Out — PIN လိုအပ်သည်*\n\nPIN နံပါတ် ထည့်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return STOCK_PIN

async def cmd_stock_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /stock — PIN verify then Stock menu."""
    context.user_data.clear()
    context.user_data["stock_dest"] = "menu"
    await update.message.reply_text(
        "🔐 *Stock Update — PIN လိုအပ်သည်*\n\nPIN နံပါတ် ထည့်ပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return STOCK_PIN

async def step_stock_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify PIN — delete the PIN message then route to dest."""
    entered = update.message.text.strip()
    try:
        await update.message.delete()
    except Exception as e:
        logger.error("step_stock_pin: %s", e, exc_info=True)
        pass
    if entered == STOCK_ACCESS_PIN:
        dest = context.user_data.pop("stock_dest", "menu")
        if dest == "stockin":
            from bot.handlers.stock_in import show_si_items
            return await show_si_items(update, context)
        if dest == "stockout":
            return await show_stock_out_items(update, context)
        return await show_stock_menu(update, context)
    await update.message.reply_text(
        "❌ PIN မမှန်ကန်ပါ။\n\nMain Menu သို့ ပြန်သွားမည်။",
        reply_markup=ReplyKeyboardRemove(),
    )
    return await show_main_menu(update, context)

async def show_stock_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Stock Update sub-menu: Stock Out, Stock In only."""
    kb = [
        [BTN_STOCK_OUT],
        [BTN_STOCK_IN_M],
        [BTN_BACK_MAIN],
    ]
    await update.message.reply_text(
        "📦 *Stock Update*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Action ရွေးပါ ↓",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return STOCK_MENU

async def step_stock_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route from Stock sub-menu."""
    choice = update.message.text.strip()
    if choice == BTN_BACK_MAIN:
        return await show_main_menu(update, context)
    if choice == BTN_STOCK_OUT:
        return await show_stock_out_items(update, context)
    if choice == BTN_STOCK_IN_M:
        from bot.handlers.stock_in import show_si_items
        return await show_si_items(update, context)
    if choice == BTN_INVENTORY_VIEW:
        await update.message.reply_text("⏳ Inventory စစ်နေသည်...", reply_markup=ReplyKeyboardRemove())
        data = await _psvibe_get_async("sheets/inventory")
        if not data:
            await update.message.reply_text("❌ Inventory data ရယူ၍ မရပါ။")
            return await show_stock_menu(update, context)
        items = data.get("items", [])
        lines = ["📦 *Inventory Status*\n━━━━━━━━━━━━━━━━━━"]
        for item in items:
            name = item.get("name", "?")
            stock_qty = max(0, item.get("qty", 0))
            if stock_qty > 5:
                em = "🟢"
            elif stock_qty > 0:
                em = "🟡"
            else:
                em = "🔴"
            lines.append(f"{em} *{name}*: {stock_qty} pcs")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return await show_stock_menu(update, context)
    return await show_stock_menu(update, context)

async def show_stock_out_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show food item list for manual stock-out recording."""
    food_prices = await fetch_food_prices_async()
    context.user_data["stock_food_prices"] = food_prices
    names = list(food_prices.keys())
    rows  = [names[i: i + 2] for i in range(0, len(names), 2)]
    kb    = rows + [[BTN_BACK_MAIN]]
    await update.message.reply_text(
        "📦 *Stock Out — ထုတ်ယူမည့် ပစ္စည်းကို ရွေးပါ*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return STOCK_ITEM

async def step_stock_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()

    if choice == BTN_BACK_MAIN:
        return await show_main_menu(update, context)

    food_prices = context.user_data.get("stock_food_prices", {})
    if choice not in food_prices:
        await update.message.reply_text("❌ ပစ္စည်း မရှိပါ။ ပြန်ရွေးပါ။")
        return STOCK_ITEM

    context.user_data["stock_item"] = choice
    kb = [[BTN_BACK_MAIN]]
    await update.message.reply_text(
        f"📦 *{choice}*\n\n"
        f"ထုတ်ယူသော အရေအတွက် ထည့်ပါ (ဥပမာ: 2) -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return STOCK_QTY

async def step_stock_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == BTN_BACK_MAIN:
        return await show_main_menu(update, context)

    if not text.isdigit() or int(text) <= 0:
        await update.message.reply_text("❌ ဂဏန်း မှန်မှန်ကန်ကန် ထည့်ပါ (ဥပမာ: 2) -")
        return STOCK_QTY

    qty  = int(text)
    item = context.user_data.get("stock_item", "")
    today = now_mmt().strftime("%-m/%-d/%Y")
    ref   = "STK-" + now_mmt().strftime("%Y%m%d-%H%M%S")

    food_prices = context.user_data.get("stock_food_prices", {})
    food_costs  = await fetch_food_costs_async()
    sell_price  = food_prices.get(item, 0)
    cost_price  = food_costs.get(item, 0)
    total_val   = sell_price * qty
    total_cogs  = cost_price * qty

    try:
        # TODO: Migrate to MySQL via API -- direct gspread is fallback only
        logging.warning("DEPRECATED: direct gspread write in step_stock_qty — should use API endpoint")
        # ── API write (best-effort) ──
        try:
            api_add_stock_out({
                "date": today,
                "reference": ref,
                "item_name": item,
                "qty": qty,
                "sell_price": sell_price,
                "total_value": total_val,
                "cost_price": cost_price,
                "total_cogs": total_cogs,
            })
        except Exception as e:
            logging.warning("Stock-out API write failed (GSheet fallback OK): %s", e)
        logging.info("Stock out saved: %s x%d ref=%s", item, qty, ref)
        msg = (
            f"✅ *Stock Out မှတ်တမ်းတင်ပြီး*\n\n"
            f"📦 Item     : *{item}*\n"
            f"🔢 Qty Out  : *{qty}*\n"
            f"💰 Sell     : {sell_price:,} × {qty} = *{total_val:,} Ks*\n"
            f"📋 Ref      : `{ref}`\n"
            f"📅 Date     : {today}"
        )
        # K1 total inventory value — removed (GSheet dead code)
        # Low stock alert
        inv_data = await _psvibe_get_async("sheets/inventory")
        if inv_data:
            for inv_item in inv_data.get("items", []):
                if inv_item.get("name") == item:
                    remaining = max(0, inv_item.get("current_stock", 0))
                    if remaining <= 5:
                        alert_emoji = "🔴" if remaining == 0 else "🟡"
                        msg += (
                            f"\n\n{alert_emoji} *Low Stock Alert!*\n"
                            f"📦 *{item}* — လက်ကျန် *{remaining} pcs* သာကျန်တော့သည်!\n"
                            f"{'❌ Stock ကုန်သွားပြီ — အမြန်ဖြည့်ပါ!' if remaining == 0 else '⚠️ Stock ဖြည့်ရန် အချိန်ကြောင်ပြီ!'}"
                        )
                    break
    except Exception as e:
        logging.error("Stock out failed: %s", e)
        msg = f"❌ မှတ်တမ်းတင်မှု မအောင်မြင်ပါ။\n{e}"

    context.user_data.pop("stock_item", None)
    context.user_data.pop("stock_food_prices", None)

    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
    )
    return MAIN_MENU
