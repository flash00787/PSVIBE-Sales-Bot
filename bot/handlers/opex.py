
"""
PS VIBE Sale Bot — OPEX / Operating Expenses handler.
Boss-only commands to record and view expenses.
"""
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler, MessageHandler, filters, ConversationHandler,
    CallbackContext,
)
from bot.constants import BTN_OPEX, BTN_OPEX_LIST, OPEX_CATEGORIES
from bot.api_client import api_post, api_get

logger = logging.getLogger(__name__)

# ── States ────────────────────────────────────────────────────────────────────
CATEGORY, DESCRIPTION, AMOUNT, PAYMENT = range(4)

def _is_boss(user_id: int) -> bool:
    from bot.constants import ADMIN_IDS
    return user_id in ADMIN_IDS

async def cmd_opex(update: Update, context: CallbackContext):
    """Start OPEX recording flow."""
    if not _is_boss(update.effective_user.id):
        await update.message.reply_text("Boss only command")
        return ConversationHandler.END

    keyboard = [[c] for c in OPEX_CATEGORIES] + [["\u274c Cancel"]]
    await update.message.reply_text(
        "\U0001f4b0 OPEX — Select category:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CATEGORY

async def step_category(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if text == "\u274c Cancel":
        await update.message.reply_text("Cancelled", reply_markup=ReplyKeyboardMarkup.remove())
        return ConversationHandler.END
    if text not in OPEX_CATEGORIES:
        await update.message.reply_text("Invalid category, try again")
        return CATEGORY
    context.user_data["opex_cat"] = text
    await update.message.reply_text(
        f"Category: {text}\n\nEnter description (or /skip for none):",
        reply_markup=ReplyKeyboardMarkup.remove(),
    )
    return DESCRIPTION

async def step_description(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if text == "/skip":
        context.user_data["opex_desc"] = ""
    else:
        context.user_data["opex_desc"] = text
    await update.message.reply_text("Enter amount (Ks):")
    return AMOUNT

async def step_amount(update: Update, context: CallbackContext):
    try:
        amount = int(update.message.text.strip().replace(",", ""))
    except ValueError:
        await update.message.reply_text("Invalid amount. Enter number:")
        return AMOUNT
    if amount <= 0:
        await update.message.reply_text("Amount must be positive:")
        return AMOUNT
    context.user_data["opex_amount"] = amount
    keyboard = [["Cash", "WavePay", "AYA Pay", "Bank"]] + [["\u274c Cancel"]]
    await update.message.reply_text(
        f"Amount: {amount:,} Ks\n\nSelect payment method:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return PAYMENT

async def step_payment(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if text == "\u274c Cancel":
        await update.message.reply_text("Cancelled", reply_markup=ReplyKeyboardMarkup.remove())
        return ConversationHandler.END

    cat = context.user_data["opex_cat"]
    desc = context.user_data["opex_desc"]
    amt = context.user_data["opex_amount"]
    user = update.effective_user
    name = user.full_name or user.username or "Staff"

    result = await api_post("opex/add", {
        "category": cat,
        "description": desc,
        "amount": amt,
        "payment_method": text,
        "recorded_by": name,
    })

    if isinstance(result, dict) and result.get("success"):
        await update.message.reply_text(
            f"\u2705 OPEX Recorded:\n"
            f"  \U0001f4a1 {cat}: {amt:,} Ks\n"
            f"  \U0001f4b3 {text}\n"
            f"  \U0001f4c5 {desc if desc else '-'}",
            reply_markup=ReplyKeyboardMarkup.remove(),
        )
    else:
        await update.message.reply_text(
            f"\u274c Failed: {result.get('error', 'Unknown')}",
            reply_markup=ReplyKeyboardMarkup.remove(),
        )

    context.user_data.clear()
    return ConversationHandler.END

async def cmd_opex_list(update: Update, context: CallbackContext):
    """Show recent OPEX entries."""
    if not _is_boss(update.effective_user.id):
        return
    data = await api_get("opex/list?limit=10")
    if isinstance(data, dict) and data.get("success"):
        items = data.get("data", [])
        if not items:
            await update.message.reply_text("No OPEX entries yet")
            return
        msg = "\U0001f4cb Recent OPEX:\n"
        for i in items:
            msg += f"\n  {i['expense_date']} | {i['category']}: {i['amount']:,} Ks"
            if i.get("description"):
                msg += f" ({i['description']})"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("Failed to fetch OPEX list")

OPEX_CONV_HANDLER = ConversationHandler(
    entry_points=[MessageHandler(filters.Text(BTN_OPEX), cmd_opex)],
    states={
        CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_category)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_description)],
        AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_amount)],
        PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_payment)],
    },
    fallbacks=[],
    name="opex_conv",
    persistent=False,
)

HANDLERS = [
    OPEX_CONV_HANDLER,
    CommandHandler("opex_list", cmd_opex_list),
    MessageHandler(filters.Text(BTN_OPEX_LIST), cmd_opex_list),
]
