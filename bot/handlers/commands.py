"""PS VIBE Bot — Command shortcut handlers (/cancel, /topup, /member, /check, /newmember, /ranks).
"""
# Using bot.* namespace instead of direct handler imports to avoid circular deps

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Release any held food cart stock for this session
    bk_id = context.user_data.get("booking_id", "")
    if bk_id and context.user_data.get("_stock_held"):
        try:
            from bot.api_client import api_post
            import asyncio
            asyncio.create_task(asyncio.to_thread(api_post, "food-cart/cancel-release", {"booking_id": str(bk_id)}))
        except Exception:
            pass
    await update.message.reply_text(
        "❌ ဖျက်သိမ်းလိုက်ပါပြီ။", reply_markup=ReplyKeyboardRemove()
    )
    from bot.handlers.main_menu import show_main_menu
    return await show_main_menu(update, context)

async def cmd_topup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /topup — jump to Top Up member selection."""
    context.user_data.clear()
    from bot.handlers.members import prompt_tu_member
    return await prompt_tu_member(update, context)

async def cmd_member_mgmt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /member — Member Management menu."""
    context.user_data.clear()
    from bot.handlers.members import show_mm_menu
    return await show_mm_menu(update, context)

async def cmd_check_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /check — jump straight to member lookup."""
    context.user_data.clear()
    from bot.handlers.members import prompt_mm_lookup
    return await prompt_mm_lookup(update, context)

async def cmd_newmember(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /newmember — jump straight to new member registration."""
    context.user_data.clear()
    context.user_data["nm_staff"] = ""
    from bot.handlers.members import prompt_nm_name
    return await prompt_nm_name(update, context)

async def cmd_ranks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /ranks — show rank tier info."""
    context.user_data.clear()
    from bot.handlers.members import show_rank_info
    return await show_rank_info(update, context)
