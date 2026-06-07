# Local imports to avoid circular dependency with handlers/__init__.py
# (functions from bot.handlers.* are available via bot.*)

# ========== Main Menu Handler ==========

# Import canonical button labels from bot (defined before circular import triggers)
from typing import Set

# from bot.handlers.console import show_console_menu
# from bot.handlers.booking import cmd_staff_book_hub, cmd_staff_booking, cmd_confirmed_bookings
# from bot.handlers.games import show_game_menu
from bot.handlers.sales import next_voucher, prompt_member

from bot import (
    ADMIN_PIN, BTN_ADMIN, BTN_HELP, BTN_BACK_MAIN, BTN_CONSOLES, BTN_DAILY_SALES,
    BTN_FINANCIAL_REPORT, BTN_BALANCE, BTN_GAME_LIB_MENU, BTN_INVENTORY_VIEW,
    BTN_MEMBER_MGMT, BTN_SBK_CONFIRMED, BTN_SBK_NEW, BTN_SBK_WAITLIST,
    BTN_STAFF_BOOK, BTN_TODAY_REPORT, MAIN_MENU, fetch_allowed_staff_ids,
    next_voucher, now_mmt, show_console_menu, show_game_menu,
    show_main_menu,
    fetch_allowed_staff_ids_async, _replit_get_async,
)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta


async def cmd_balance(update, context):
    """Show account balances for staff (no PIN needed)."""
    await update.message.reply_text(
        "\U0001f4b0 *Account Balance — ရှာဖွေနေပါသည်...*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    data = await _replit_get_async("finance/accounts")
    if not data:
        await update.message.reply_text(
            "\u274c Account Balances API ချိတ်မရပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
        )
        return MAIN_MENU
    accounts = data.get("accounts", [])
    total_bal = data.get("total_balance", 0)
    if not accounts:
        await update.message.reply_text(
            "\u26a0\ufe0f Account မှတ်တမ်း မရှိသေးပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
        )
        return MAIN_MENU
    lines = ["\U0001f4b0 *Account Balances*", "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"]
    for a in accounts:
        name = a.get("name", "?")
        bal = a.get("balance", a.get("opening", 0))
        low = name.lower()
        icon = "\U0001f3e6" if ("bank" in low or "kbz" in low or "aya" in low or "cb" in low) else ("\U0001f4f1" if ("mmqr" in low or "kpay" in low or "wave" in low) else "\U0001f4b5")
        lines.append(f"{icon} {name:<16}: {int(bal):>10,} Ks")
    lines += ["\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501", f"\U0001f4b5 *Total : {int(total_bal):,} Ks*"]
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
    )
    return MAIN_MENU

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Authorization check — only whitelisted users can access staff bot
    user = update.effective_user
    if not user or user.id not in await fetch_allowed_staff_ids_async():
        await update.message.reply_text(
            "🚫 *Access Denied*\n"
            "ဒီ bot ကို authorized staff တွေသာ သုံးနိုင်ပါတယ်။",
            parse_mode="Markdown",
        )
        return ConversationHandler.END
    context.user_data.clear()
    now      = now_mmt()
    date_str = now.strftime("%-d %b %Y")
    hour     = now.hour
    if hour < 12:
        greet = "🌅 မင်္ဂလာနံနက်ခင်း"
    elif hour < 18:
        greet = "☀️ မင်္ဂလာနေ့လည်"
    else:
        greet = "🌙 မင်္ဂလာညနေ"
    kb = [
        [BTN_DAILY_SALES,      BTN_MEMBER_MGMT],
        [BTN_CONSOLES,         BTN_BALANCE],
        [BTN_TODAY_REPORT,     BTN_INVENTORY_VIEW],
        [BTN_STAFF_BOOK,       BTN_ADMIN],
    ]
    await update.message.reply_text(
        f"🎮 *PS Vibe — Staff Bot*\n"
        f"{greet} | _{date_str}_\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Menu ရွေးပါ ↓",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return MAIN_MENU

async def step_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.handlers.sales import prompt_member
    from bot.handlers.sales import next_voucher
    from bot.handlers.games import show_game_menu
    from bot.handlers.booking import cmd_confirmed_bookings
    from bot.handlers.booking import cmd_staff_booking
    from bot.handlers.booking import cmd_staff_book_hub
    from bot.handlers.console import show_console_menu
    from bot.handlers.members import show_mm_menu
    from bot.handlers.reports import cmd_inventory, cmd_today_report, cmd_financial_report
    from bot.handlers.waitlist import cmd_waitlist_mgmt
    from bot.handlers.help import cmd_help
    choice = update.message.text

    if choice in (BTN_DAILY_SALES,):
        context.user_data["v_no"]  = next_voucher()
        context.user_data["staff"] = ""
        return await prompt_member(update, context)

    if choice == BTN_MEMBER_MGMT:
        return await show_mm_menu(update, context)

    if choice == BTN_INVENTORY_VIEW:
        return await cmd_inventory(update, context)

    if choice == BTN_TODAY_REPORT:
        return await cmd_today_report(update, context)

    if choice == BTN_CONSOLES:
        return await show_console_menu(update, context)

    if choice == BTN_STAFF_BOOK:
        return await cmd_staff_book_hub(update, context)

    if choice == BTN_SBK_WAITLIST:
        return await cmd_waitlist_mgmt(update, context)
    if choice == BTN_SBK_NEW:
        return await cmd_staff_booking(update, context)

    if choice == BTN_SBK_CONFIRMED:
        return await cmd_confirmed_bookings(update, context)

    if choice == BTN_GAME_LIB_MENU:
        return await show_game_menu(update, context)

    if choice == BTN_FINANCIAL_REPORT:
        return await cmd_financial_report(update, context)

    if choice == BTN_BALANCE:
        return await cmd_balance(update, context)

    if choice == BTN_ADMIN:
        await update.message.reply_text(
            "🔐 *Admin Panel — PIN လိုအပ်သည်*\n\nPIN နံပါတ် ထည့်ပါ:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ADMIN_PIN

    if choice == BTN_HELP:
        return await cmd_help(update, context)

    # Any back from sub-states that lands here
    if choice == BTN_BACK_MAIN:
        return await show_main_menu(update, context)

    return await show_main_menu(update, context)
