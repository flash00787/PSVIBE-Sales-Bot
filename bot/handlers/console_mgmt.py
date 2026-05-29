"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta
import sys as _sys

def __getattr__(name):
    """Lazy import from bot to break circular dependency at module load."""
    if name in ('__getattr__', '_bot_lazy_loaded'):
        raise AttributeError(name)
    _bot = _sys.modules.get('bot')
    if _bot is None:
        import bot as _bot
    val = getattr(_bot, name)
    # Cache in module dict for performance
    _sys.modules[__name__].__dict__[name] = val
    return val




async def show_con_mgmt_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cons  = get_consoles_from_setting()
    count = len(cons)
    kb    = [
        [BTN_LIST_CONSOLE, BTN_ADD_CONSOLE],
        [BTN_DEL_CONSOLE,  BTN_BACK],
    ]
    await update.message.reply_text(
        f"⚙️ *Console စီမံ* ({count} console)\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Action ရွေးပါ ↓",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return CON_MGMT_MENU

async def step_con_mgmt_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.handlers.console import show_console_menu
    choice = update.message.text.strip()
    if choice == BTN_BACK:
        return await show_console_menu(update, context)
    if choice == BTN_LIST_CONSOLE:
        cons = get_consoles_from_setting()
        if not cons:
            await update.message.reply_text("ℹ️ Console မရှိသေးပါ")
        else:
            lines = ["📋 <b>Console စာရင်း</b>\n━━━━━━━━━━━━━━━━━━"]
            for c in cons:
                mult = f"  ×{c['mult']}" if c.get("mult") else ""
                lines.append(f"🕹️ <b>{c['id']}</b> — {c.get('type','?')}{mult}")
            await update.message.reply_text("\n".join(lines), parse_mode="HTML")
        return await show_con_mgmt_menu(update, context)
    if choice == BTN_ADD_CONSOLE:
        context.user_data["new_con"] = {}
        await update.message.reply_text(
            "➕ *Console ထည့်*\n━━━━━━━━━━━━━━━━━━\n"
            "Console ID ရိုက်ပါ\n_(ဥပမာ: C - 11)_",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([[BTN_CANCEL]], resize_keyboard=True),
        )
        return CON_ADD_ID
    if choice == BTN_DEL_CONSOLE:
        cons = get_consoles_from_setting()
        if not cons:
            await update.message.reply_text("ℹ️ ဖျက်ရန် Console မရှိပါ")
            return await show_con_mgmt_menu(update, context)
        context.user_data["del_cons"] = cons
        kb = [[c["id"]] for c in cons] + [[BTN_BACK]]
        await update.message.reply_text(
            "🗑️ *Console ဖျက်မည်*\n━━━━━━━━━━━━━━━━━━\n"
            "ဖျက်မည့် Console ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
        )
        return CON_DEL_SELECT
    return await show_con_mgmt_menu(update, context)

async def step_con_add_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await show_con_mgmt_menu(update, context)
    # Check duplicate
    existing = {c["id"] for c in get_consoles_from_setting()}
    if text in existing:
        await update.message.reply_text(f"⚠️ <b>{text}</b> သည် ရှိပြီး ဖြစ်သည်", parse_mode="HTML")
        return CON_ADD_ID
    context.user_data["new_con"]["id"] = text
    kb = [["PS4", "PS5"], ["VR", BTN_CANCEL]]
    await update.message.reply_text(
        f"🕹️ <b>{text}</b>\n\nType ရွေးပါ:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return CON_ADD_TYPE

async def step_con_add_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await show_con_mgmt_menu(update, context)
    context.user_data["new_con"]["type"] = text
    kb = [["1.0", "1.5", "2.0"], [BTN_CANCEL]]
    await update.message.reply_text(
        "⚖️ Rate Multiplier ရွေးပါ\n_(Base rate ပေါ် မည်မျှ မြှောက်သည်)_\n\n"
        "1.0 = Normal · 1.5 = Premium · 2.0 = VR/Pro",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return CON_ADD_MULT

async def step_con_add_mult(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await show_con_mgmt_menu(update, context)
    try:
        mult = float(text)
    except ValueError:
        await update.message.reply_text("⚠️ ဂဏန်း ထည့်ပါ (ဥပမာ: 1.0)")
        return CON_ADD_MULT
    nc = context.user_data.get("new_con", {})
    ok = add_console_to_setting(nc.get("id",""), nc.get("type","PS4"), mult)
    if ok:
        # Update runtime VALID_CONSOLES set
        VALID_CONSOLES.add(nc.get("id",""))
        await update.message.reply_text(
            f"✅ <b>Console ထည့်ပြီ!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🕹️ ID   : <b>{nc.get('id','')}</b>\n"
            f"📱 Type : <b>{nc.get('type','')}</b>\n"
            f"⚖️ Mult : <b>×{mult}</b>",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("❌ Save မအောင်မြင်ပါ — GSheet စစ်ကြည့်ပါ")
    return await show_con_mgmt_menu(update, context)

async def step_con_del_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_con_mgmt_menu(update, context)
    cons = context.user_data.get("del_cons", [])
    target = next((c for c in cons if c["id"] == text), None)
    if not target:
        await update.message.reply_text("⚠️ Keyboard မှ ရွေးပေးပါ")
        return CON_DEL_SELECT
    ok = remove_console_from_setting(target["id"])
    if ok:
        VALID_CONSOLES.discard(target["id"])
        await update.message.reply_text(
            f"🗑️ <b>{target['id']}</b> ဖျက်ပြီ\n"
            f"<i>(Setting sheet မှ ဖယ်ထားသည်)</i>",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(f"❌ ဖျက်မရပါ — GSheet စစ်ကြည့်ပါ")
    return await show_con_mgmt_menu(update, context)
