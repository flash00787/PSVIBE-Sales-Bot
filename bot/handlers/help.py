"""PS VIBE Bot — Help, Version & Error Handler.
"""
from bot.handlers import *

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta


async def cmd_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the running bot version and build date."""
    import platform
    py_ver = platform.python_version()
    built  = now_mmt().strftime("%Y-%m-%d %H:%M MMT")
    await update.message.reply_text(
        f"🤖 *PS Vibe Sales Bot*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 Version   : `{BOT_VERSION}`\n"
        f"🐍 Python    : `{py_ver}`\n"
        f"🕐 Server time: `{built}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ *Latest features:*\n"
        f"  • Admin CMD PIN (/payroll /kpi /setattend)\n"
        f"  • Payroll target display in hrs (not mins)\n"
        f"  • Session repeat reminder loop (5-min cycle)\n"
        f"  • Inventory cache bust after stock update\n"
        f"  • Staff breakdown + low-wallet API endpoints\n"
        f"  • Payroll business-wide play\\_mins total\n"
        f"  • Per-member exact effective rate\n"
        f"  • P&L / Cash Flow / Liability reports",
        parse_mode="Markdown",
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all available commands."""
    await update.message.reply_text(
        "📖 *PS Vibe Bot — Commands*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🏠 *Navigation*\n"
        "/start        — Main Menu ပြမည်\n"
        "/menu         — Main Menu ပြမည်\n"
        "/cancel       — လက်ရှိ action ဖျက်သိမ်း\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎮 *Sales*\n"
        "/sales        — 📝 New Sale _(shortcut)_\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💳 *Members*\n"
        "/member       — Member Management menu\n"
        "/newmember    — 🆕 New Member Register\n"
        "/topup        — 💰 Top Up _(shortcut)_\n"
        "/check        — 🔍 Check Member Info\n"
        "/ranks        — 📋 View Rank Tier Table\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📊 *Reports*\n"
        "/report       — 📊 Today's Report\n"
        "/kpi          — 📈 Staff KPI (ဒီနေ့)\n"
        "/payroll      — 💰 Monthly Payroll\n"
        "/setattend    — 📅 ခွင့်ယူ / နောက်ကျ မှတ်တမ်း\n"
        "/admin        — 🔧 Admin Panel (Stock/Attend/Payroll/KPI)\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📦 *Stock*\n"
        "/stock        — Stock Update menu\n"
        "/stockin      — 📥 Stock In (Restock)\n"
        "/stockout     — 📦 Stock Out\n"
        "/inventory    — 🗂 Inventory Status\n"
        "/stocktoday   — 🛒 Items sold today\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "/help         — ဤ command list",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log all Telegram errors without crashing the bot."""
    from telegram.error import NetworkError, TimedOut, Conflict
    err = context.error
    if isinstance(err, (NetworkError, TimedOut)):
        logging.warning("Network issue (will auto-retry): %s", err)
    elif isinstance(err, Conflict):
        logging.warning("Conflict: another instance is running — will resolve automatically.")
    else:
        logging.error("Unhandled error: %s", err, exc_info=err)
