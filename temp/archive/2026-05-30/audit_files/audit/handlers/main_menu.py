from bot import fetch_allowed_staff_ids, now_mmt, MAIN_MENU, ADMIN_PIN, BTN_DAILY_SALES, BTN_MEMBER_MGMT, BTN_CONSOLES, BTN_TODAY_REPORT, BTN_STAFF_BOOK, BTN_INVENTORY_VIEW, BTN_FINANCIAL_REPORT, BTN_ADMIN, BTN_NEW_SALE, BTN_SBK_WAITLIST, BTN_SBK_NEW, BTN_SBK_CONFIRMED, BTN_GAME_LIB_MENU, BTN_BACK_MAIN, next_voucher
from .console import show_console_menu
from .reports import cmd_inventory, cmd_today_report, cmd_financial_report
from .booking import cmd_staff_book_hub, cmd_staff_booking, cmd_confirmed_bookings
from .waitlist import cmd_waitlist_mgmt
from .members import show_mm_menu
from .sales import prompt_member
from .games import show_game_menu
"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
from datetime import datetime, timezone, timedelta




async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Authorization check — only whitelisted users can access staff bot
    user = update.effective_user
    if not user or user.id not in fetch_allowed_staff_ids():
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
        [BTN_CONSOLES,         BTN_TODAY_REPORT],
        [BTN_STAFF_BOOK,       BTN_INVENTORY_VIEW],
        [BTN_FINANCIAL_REPORT, BTN_ADMIN],
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
    choice = update.message.text

    if choice in (BTN_DAILY_SALES, BTN_NEW_SALE):
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

    if choice == BTN_ADMIN:
        await update.message.reply_text(
            "🔐 *Admin Panel — PIN လိုအပ်သည်*\n\nPIN နံပါတ် ထည့်ပါ:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ADMIN_PIN

    # Any back from sub-states that lands here
    if choice == BTN_BACK_MAIN:
        return await show_main_menu(update, context)

    return await show_main_menu(update, context)