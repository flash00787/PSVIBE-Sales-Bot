import asyncio
from bot import (
    fetch_console_status,
    get_consoles_from_setting, add_console_to_setting, remove_console_from_setting,
    BTN_BACK, BTN_CANCEL, BTN_ADD_CONSOLE, BTN_LIST_CONSOLE, BTN_DEL_CONSOLE,
    BTN_EDIT_MULT, BTN_MOVE_CONSOLE, BTN_SWAP_CONSOLE,
    CON_MGMT_MENU, CON_ADD_ID, CON_ADD_MULT, CON_ADD_TYPE,
    CON_DEL_SELECT, CON_EDIT_MULT_SELECT, CON_EDIT_MULT_VALUE,
    MOVECON_SOURCE, MOVECON_TARGET, MOVECON_CONFIRM,
    SWAP_SOURCE, SWAP_CONFIRM,
    show_console_menu,
)
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
    if name in ('__getattr__', '_bot_lazy_loaded', '__all__', '__path__', '__spec__', '__loader__', '__package__'):
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
        [BTN_EDIT_MULT,    BTN_DEL_CONSOLE],
        [BTN_MOVE_CONSOLE, BTN_SWAP_CONSOLE],
        [BTN_BACK],
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
    if choice == BTN_EDIT_MULT:
        cons = get_consoles_from_setting()
        if not cons:
            await update.message.reply_text("\u2139\ufe0f \u1015\u103c\u1004\u1039\u101b\u1031\u102c\u1000\u1039\u101b\u1014\u1039 Console \u1019\u103b\u101b\u102d\u101e\u101e\u1019\u1039\u1016\u102b")
            return await show_con_mgmt_menu(update, context)
        context.user_data["edit_mult_cons"] = cons
        kb = [[c["id"]] for c in cons] + [[BTN_BACK]]
        await update.message.reply_text(
            "\u2699\ufe0f *Mult \u1015\u103c\u1004\u1039\u1019\u102a*\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            "Mult \u1015\u103c\u1004\u1039\u1019\u102a Console \u101b\u103d\u1031\u1038\u1015\u102b:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
        )
        return CON_EDIT_MULT_SELECT
    if choice == BTN_MOVE_CONSOLE:
        return await prompt_move_session(update, context)
    if choice == BTN_SWAP_CONSOLE:
        return await prompt_swap_session(update, context)
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

async def step_con_edit_mult_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_con_mgmt_menu(update, context)
    cons = context.user_data.get("edit_mult_cons", [])
    target = next((c for c in cons if c["id"] == text), None)
    if not target:
        await update.message.reply_text("\u26a0\ufe0f Keyboard \u1019\u103e \u101b\u103d\u1031\u1038\u1015\u1034\u1015\u102b")
        return CON_EDIT_MULT_SELECT
    context.user_data["edit_mult_console"] = target
    current_mult = target.get("mult", "1.0")
    kb = [["1.0", "1.5", "2.0"], [BTN_CANCEL]]
    await update.message.reply_text(
        f"\u2699\ufe0f *Mult \u1015\u103c\u1004\u1039\u1019\u102a*\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"\U0001f579\ufe0f <b>{target['id']}</b>\n"
        f"\u26b2\ufe0f \u2039\u101c\u103d\u1010\u1039\u1038 Mult: <b>{current_mult}</b>\n\n"
        "Mult \u1010\u1014\u1039\u1016\u102c\u101b\u102d\u1019\u1039 \u101b\u102d\u1021\u1039\u1015\u102b\u1004\u1039\u1019\u103c\u1031\u1018\u102b:\n"
        "_(\u1014\u103d\u1019\u1039\u1019\u104a 1.0 > Normal \u00b7 1.5 > Premium \u00b7 2.0 > VR/Pro)_",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return CON_EDIT_MULT_VALUE


async def step_con_edit_mult_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await show_con_mgmt_menu(update, context)
    try:
        mult = float(text)
    except ValueError:
        await update.message.reply_text("\u26a0\ufe0f \u1002\u1012\u1014\u1039\u1038 \u1011\u102d\u1034\u1000\u1039\u1015\u102b (\u1025\u1019\u1039\u1019\u104a: 1.0)")
        return CON_EDIT_MULT_VALUE
    target = context.user_data.get("edit_mult_console", {})
    cid = target.get("id", "")
    if not cid:
        return await show_con_mgmt_menu(update, context)
    ok = update_console_multiplier(cid, mult)
    if ok:
        await update.message.reply_text(
            f"\u2705 <b>Mult \u1015\u103c\u1004\u1039\u1014\u1010\u1039!</b>\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"\U0001f579\ufe0f <b>{cid}</b>\n"
            f"\u26b2\ufe0f New Mult: <b>\u00d7{mult:g}</b>",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("\u274c Save \u1019\u1021\u1031\u102c\u1004\u1039\u1019\u1000\u1039\u1015\u102b\u1019\u1039\u101e\u1031\u1019\u102c\u1021\u101b\u103e\u1014\u1039\u1005\u1005\u1039\u1000\u103c\u1019\u1039\u1015\u102b")
    context.user_data.pop("edit_mult_console", None)
    context.user_data.pop("edit_mult_cons", None)
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


# ═══════════════════════════════════════
#  Move Active Session to Another Console
# ═══════════════════════════════════════

async def prompt_move_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show active sessions to move."""
    try:
        cons = fetch_console_status()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await show_con_mgmt_menu(update, context)

    active = [c for c in cons if c.get("status") == "Active"]
    if not active:
        await update.message.reply_text(
            "ℹ️ Move လုပ်ရန် Active session မရှိပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK]], resize_keyboard=True),
        )
        return CON_MGMT_MENU

    free = [c for c in cons if c.get("status") == "Free"]
    if len(free) < 1:
        await update.message.reply_text(
            "⚠️ ရွှေ့ရန် Free console မရှိပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK]], resize_keyboard=True),
        )
        return CON_MGMT_MENU

    context.user_data["_move_free_consoles"] = free

    lines = ["🔄 <b>Session ရွှေ့မည် — Console ရွေးပါ</b>", "━━━━━━━━━━━━━━━━━━"]
    kb = []
    for c in active:
        mbr = c.get("member") or "Guest"
        st = c.get("start", "?")
        lines.append(f"🔴 <b>{c['id']}</b>  |  👤 {mbr}  |  🕐 {st}")
        kb.append([c["id"]])
    kb.append([BTN_BACK])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return MOVECON_SOURCE


async def step_move_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User picked source console — show free targets."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_con_mgmt_menu(update, context)

    try:
        cons = fetch_console_status()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await show_con_mgmt_menu(update, context)

    source = next((c for c in cons if c.get("id") == text and c.get("status") == "Active"), None)
    if not source:
        await update.message.reply_text(f"⚠️ <b>{text}</b> သည် Active မဟုတ်ပါ", parse_mode="HTML")
        return await prompt_move_session(update, context)

    context.user_data["_move_source"] = source
    free = [c for c in cons if c.get("status") == "Free" and c.get("id") != text]

    if not free:
        await update.message.reply_text("⚠️ ရွှေ့ရန် Free console မရှိပါ")
        return await show_con_mgmt_menu(update, context)

    lines = [
        f"🔄 <b>{text}</b> → ?",
        "━━━━━━━━━━━━━━━━━━",
        f"👤 {source.get('member') or 'Guest'}",
        f"🕐 {source.get('start', '?')}",
        "",
        "Target Console ရွေးပါ:",
    ]
    kb = [[c["id"]] for c in free]
    kb.append([BTN_BACK])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return MOVECON_TARGET


async def step_move_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User picked target console — confirm and execute."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await prompt_move_session(update, context)

    source = context.user_data.get("_move_source", {})
    if not source:
        return await show_con_mgmt_menu(update, context)

    src_id = source.get("id", "")
    src_bk = source.get("booking_id", "")

    try:
        cons = fetch_console_status()
    except Exception:
        cons = []

    free_ids = {c["id"] for c in cons if c.get("status") == "Free"}
    if text not in free_ids:
        await update.message.reply_text(
            f"⚠️ <b>{text}</b> သည် Free မဟုတ်တော့ပါ — ပြန်ရွေးပါ",
            parse_mode="HTML",
        )
        return await step_move_source(update, context)

    # Execute move via API
    try:
        from bot.api_client import api_post
        result = await asyncio.to_thread(
            api_post, "sessions/move",
            {"booking_id": int(src_bk), "to_console_id": text}
        )
    except Exception as e:
        logger.exception("move_session api error")
        await update.message.reply_text(f"❌ API Error: {e}")
        return await show_con_mgmt_menu(update, context)

    if result and result.get("success"):
        await update.message.reply_text(
            f"✅ <b>Session ရွှေ့ပြီ!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🕹️ {src_id} → <b>{text}</b>\n"
            f"👤 {source.get('member') or 'Guest'}\n\n"
            f"<i>Timer အလိုအလျောက် ပြန်ချိန်ထားပါတယ်</i>",
            parse_mode="HTML",
        )
    else:
        err = (result or {}).get("error", "Unknown error")
        await update.message.reply_text(
            f"❌ <b>မအောင်မြင်ပါ</b>\n━━━━━━━━━━━━━━━━━━\n{err}",
            parse_mode="HTML",
        )

    context.user_data.pop("_move_source", None)
    context.user_data.pop("_move_free_consoles", None)
    return await show_console_menu(update, context)


# ═══════════════════════════════════════
#  Swap Two Active Sessions
# ═══════════════════════════════════════

async def prompt_swap_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Active sessions to pick first console for swap."""
    try:
        cons = fetch_console_status()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await show_con_mgmt_menu(update, context)

    active = [c for c in cons if c.get("status") == "Active"]
    if len(active) < 2:
        await update.message.reply_text(
            "⚠️ Swap လုပ်ရန် Active session အနည်းဆုံး ၂ ခုရှိရမည်",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK]], resize_keyboard=True),
        )
        return CON_MGMT_MENU

    context.user_data["_swap_active"] = active

    lines = ["↔️ <b>Console Swap — ပထမ Console ရွေးပါ</b>", "━━━━━━━━━━━━━━━━━━"]
    kb = []
    for c in active:
        mbr = c.get("member") or "Guest"
        st = c.get("start", "?")
        game = c.get("current_game", "") or ""
        lines.append(f"🔴 <b>{c['id']}</b>  |  👤 {mbr}  |  🎮 {game}  |  🕐 {st}")
        kb.append([c["id"]])
    kb.append([BTN_BACK])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return SWAP_SOURCE


async def step_swap_source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User picked first console — show remaining Active consoles for second."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_con_mgmt_menu(update, context)

    active = context.user_data.get("_swap_active", [])
    source = next((c for c in active if c.get("id") == text), None)
    if not source:
        await update.message.reply_text("⚠️ ပထမ Console ပြန်ရွေးပါ")
        return await prompt_swap_session(update, context)

    context.user_data["_swap_source"] = source
    others = [c for c in active if c.get("id") != text]

    lines = [
        f"↔️ <b>{text}</b> ↔ ?",
        "━━━━━━━━━━━━━━━━━━",
        f"👤 {source.get('member') or 'Guest'}",
        f"🕐 {source.get('start', '?')}",
        "",
        "ဒုတိယ Console ရွေးပါ:",
    ]
    kb = []
    for c in others:
        mbr = c.get("member") or "Guest"
        st = c.get("start", "?")
        kb.append([f"{c['id']}  |  👤 {mbr}  |  🕐 {st}"])
    kb.append([BTN_BACK])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return SWAP_CONFIRM


async def step_swap_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User picked second console — execute swap."""
    text = (update.message.text or "").strip()
    if text == BTN_BACK:
        return await prompt_swap_session(update, context)

    # Extract console_id from the label (format: "C-04  |  👤 Guest  |  🕐 12:25")
    target_cid = text.split("  |")[0].strip() if "  |" in text else text

    source = context.user_data.get("_swap_source", {})
    active = context.user_data.get("_swap_active", [])

    target = next((c for c in active if c.get("id") == target_cid and c.get("id") != source.get("id")), None)
    if not target:
        await update.message.reply_text("⚠️ ဒုတိယ Console ပြန်ရွေးပါ")
        return await step_swap_source(update, context)

    src_bk = source.get("booking_id")
    tgt_bk = target.get("booking_id")

    if not src_bk or not tgt_bk:
        await update.message.reply_text("❌ Booking data missing — မရွှေ့နိုင်ပါ")
        return await show_con_mgmt_menu(update, context)

    # Execute swap via API
    try:
        from bot.api_client import api_post
        result = await asyncio.to_thread(
            api_post, "sessions/swap",
            {"booking_id_1": int(src_bk), "booking_id_2": int(tgt_bk)}
        )
    except Exception as e:
        logger.exception("swap_sessions api error")
        await update.message.reply_text(f"❌ API Error: {e}")
        return await show_con_mgmt_menu(update, context)

    if result and result.get("success"):
        await update.message.reply_text(
            f"✅ Swap အောင်မြင်ပါသည်!\n\n"
            f"🔄 <b>{source['id']}</b> ↔ <b>{target['id']}</b>",
            parse_mode="HTML",
        )
    else:
        err = (result or {}).get("error") or (result or {}).get("message", "Unknown")
        await update.message.reply_text(f"❌ Swap မအောင်မြင်ပါ: {err}")

    context.user_data.pop("_swap_source", None)
    context.user_data.pop("_swap_active", None)
    return await show_con_mgmt_menu(update, context)
