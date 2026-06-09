"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
from datetime import datetime, timezone, timedelta




async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ ဖျက်သိမ်းလိုက်ပါပြီ။", reply_markup=ReplyKeyboardRemove()
    )
    return await show_main_menu(update, context)

async def cmd_topup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /topup — jump to Top Up member selection."""
    context.user_data.clear()
    return await prompt_tu_member(update, context)

async def cmd_member_mgmt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /member — Member Management menu."""
    context.user_data.clear()
    return await show_mm_menu(update, context)

async def cmd_check_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /check — jump straight to member lookup."""
    context.user_data.clear()
    return await prompt_mm_lookup(update, context)

async def cmd_newmember(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /newmember — jump straight to new member registration."""
    context.user_data.clear()
    context.user_data["nm_staff"] = ""
    return await prompt_nm_name(update, context)

async def cmd_ranks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /ranks — show rank tier info."""
    context.user_data.clear()
    return await show_rank_info(update, context)