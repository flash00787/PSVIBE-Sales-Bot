"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import asyncio, logging, re, json
from datetime import datetime, timezone, timedelta




from bot import BTN_BACK, BTN_CANCEL, BTN_GINST_ADD, BTN_GINST_DISC, BTN_GINST_HDD, BTN_GINST_REMOVE, BTN_GINST_SSD, BTN_GINST_VIEW, GINST_ADD_CONS, GINST_ADD_GAME, GINST_ADD_TYPE, GINST_DEL_CONS, GINST_DEL_GAME, GINST_MENU, GINST_VIEW_CONS, add_console_game, fetch_console_games, fetch_games, get_consoles_from_setting, get_games_on_console, remove_console_game, update_game_library_install
async def show_ginst_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    records = fetch_console_games()
    count   = len(records)
    kb = [
        [BTN_GINST_VIEW],
        [BTN_GINST_ADD, BTN_GINST_REMOVE],
        [BTN_BACK],
    ]
    await update.message.reply_text(
        f"🖥️ *Console Install* ({count} မှတ်တမ်း)\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📋 ကြည့် — ဘယ် console မှာ ဘာ ရှိသလဲ\n"
        "➕ ထည့် — Game install မှတ်သား\n"
        "❌ ဖျက် — Install မှတ်တမ်း ဖျက်",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return GINST_MENU

async def step_ginst_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.handlers.games import show_game_menu
    text = update.message.text.strip()
    if text in (BTN_BACK, BTN_CANCEL):
        return await show_game_menu(update, context)
    if text == BTN_GINST_VIEW:
        return await _ginst_pick_console(update, context, next_state=GINST_VIEW_CONS, prompt="👁 ကြည့်မည့် Console ရွေးပါ:")
    if text == BTN_GINST_ADD:
        return await _ginst_pick_console(update, context, next_state=GINST_ADD_CONS, prompt="➕ Game ထည့်မည့် Console ရွေးပါ:")
    if text == BTN_GINST_REMOVE:
        return await _ginst_pick_console(update, context, next_state=GINST_DEL_CONS, prompt="❌ ဖျက်မည့် Console ရွေးပါ:")
    return await show_ginst_menu(update, context)

async def _ginst_pick_console(update, context, next_state, prompt):
    """Show console selection keyboard for a GINST operation."""
    cons = get_consoles_from_setting()
    if not cons:
        await update.message.reply_text("⚠️ Console မရှိသေးပါ\nConsole CRUD မှ ထည့်ပါ")
        return await show_ginst_menu(update, context)
    kb = [[c["id"]] for c in cons]
    kb.append([BTN_BACK])
    await update.message.reply_text(
        prompt,
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return next_state

async def step_ginst_view_cons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in (BTN_BACK, BTN_CANCEL):
        return await show_ginst_menu(update, context)
    console_id = text
    games = get_games_on_console(console_id)
    records = [r for r in fetch_console_games()
               if r["console_id"].upper() == console_id.upper()]
    if not records:
        await update.message.reply_text(
            f"ℹ️ <b>{console_id}</b> မှာ Install မှတ်တမ်း မရှိသေးပါ",
            parse_mode="HTML",
        )
    else:
        lines = [f"🖥️ <b>{console_id}</b> — Install ({len(records)} ဂိမ်း)\n━━━━━━━━━━━━━━━━━━"]
        for i, r in enumerate(records, 1):
            icon = "💾" if "HDD" in r["install_type"] else ("💿" if "Disc" in r["install_type"] else "🔌")
            lines.append(f"{i}. {icon} <b>{r['game_title']}</b>  <i>{r['install_type']}</i>  <code>{r['date']}</code>")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    return await show_ginst_menu(update, context)

async def step_ginst_add_cons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in (BTN_BACK, BTN_CANCEL):
        return await show_ginst_menu(update, context)
    context.user_data["ginst_console_id"] = text
    games = fetch_games()
    if not games:
        await update.message.reply_text(
            "⚠️ Game Library ဗလာ ဖြစ်နေသည်\nGame Library မှ ဂိမ်းထည့်ပါ"
        )
        return await show_ginst_menu(update, context)
    kb = []
    row = []
    for g in games:
        row.append(g["title"])
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([BTN_BACK])
    await update.message.reply_text(
        f"🖥️ <b>{text}</b>\n\n🎮 Install မည့် ဂိမ်းကို ရွေးပါ:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return GINST_ADD_GAME

async def step_ginst_add_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in (BTN_BACK, BTN_CANCEL):
        return await show_ginst_menu(update, context)
    cid   = context.user_data.get("ginst_console_id", "")
    title = text
    install_type = "HDD"

    # ── Duplicate check ───────────────────────────────────────────────────────
    existing = await asyncio.to_thread(fetch_console_games)
    already  = any(
        r["console_id"].strip().upper() == cid.upper()
        and r["game_title"].strip().lower() == title.strip().lower()
        for r in existing
    )
    if already:
        await update.message.reply_text(
            f"⚠️ <b>\"{title}\"</b> သည် <b>{cid}</b> မှာ ရှိပြီးသားပါ",
            parse_mode="HTML",
        )
        return await show_ginst_menu(update, context)

    ok, gl_ok = await asyncio.gather(
        asyncio.to_thread(add_console_game, cid, title, install_type),
        asyncio.to_thread(update_game_library_install, title, cid, True),
    )
    if ok:
        gl_note = "  📊 Game Library ✅" if gl_ok else "  📊 Game Library ⚠️ (manual update လို)"
        await update.message.reply_text(
            f"✅ <b>Install မှတ်သားပြီ!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🖥️ Console : <b>{cid}</b>\n"
            f"🎮 Game    : <b>{title}</b>\n"
            f"💾 Type    : <b>{install_type}</b>\n"
            f"{gl_note}",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            f"❌ မှတ်သားမရပါ — ထပ်ကြိုးစားပါ\n"
            f"(Console: {cid} | Game: {title})",
        )
    return await show_ginst_menu(update, context)

async def step_ginst_add_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in (BTN_BACK, BTN_CANCEL):
        return await show_ginst_menu(update, context)
    type_map = {BTN_GINST_HDD: "HDD", BTN_GINST_DISC: "Disc", BTN_GINST_SSD: "Portable SSD"}
    if text not in type_map:
        await update.message.reply_text("⚠️ Keyboard မှ ရွေးပေးပါ")
        return GINST_ADD_TYPE
    install_type = type_map[text]
    cid   = context.user_data.get("ginst_console_id", "")
    title = context.user_data.get("ginst_game_title", "")
    # Save to Console_Games sheet + sync Game_Library checkbox
    ok, gl_ok = await asyncio.gather(
        asyncio.to_thread(add_console_game, cid, title, install_type),
        asyncio.to_thread(update_game_library_install, title, cid, True),
    )
    if ok:
        icon = "💾" if install_type == "HDD" else ("💿" if install_type == "Disc" else "🔌")
        gl_note = "  📊 Game Library ✅" if gl_ok else "  📊 Game Library ⚠️ (manual update လို)"
        await update.message.reply_text(
            f"✅ <b>Install မှတ်သားပြီ!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🖥️ Console : <b>{cid}</b>\n"
            f"🎮 Game    : <b>{title}</b>\n"
            f"{icon} Type   : <b>{install_type}</b>\n"
            f"{gl_note}",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("❌ Save မအောင်မြင်ပါ — ထပ်ကြိုးစားပါ")
    return await show_ginst_menu(update, context)

async def step_ginst_del_cons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in (BTN_BACK, BTN_CANCEL):
        return await show_ginst_menu(update, context)
    console_id = text
    records = [r for r in fetch_console_games()
               if r["console_id"].upper() == console_id.upper()]
    if not records:
        await update.message.reply_text(
            f"ℹ️ <b>{console_id}</b> မှာ Install မှတ်တမ်း မရှိသေးပါ",
            parse_mode="HTML",
        )
        return await show_ginst_menu(update, context)
    context.user_data["ginst_console_id"]  = console_id
    context.user_data["ginst_del_records"] = records
    kb = [[f"{i}. {r['game_title']}"] for i, r in enumerate(records, 1)]
    kb.append([BTN_BACK])
    await update.message.reply_text(
        f"❌ <b>{console_id}</b> — ဖျက်မည့် ဂိမ်းရွေးပါ:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return GINST_DEL_GAME

async def step_ginst_del_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in (BTN_BACK, BTN_CANCEL):
        return await show_ginst_menu(update, context)
    records = context.user_data.get("ginst_del_records", [])
    cid     = context.user_data.get("ginst_console_id", "")
    target  = None
    for i, r in enumerate(records, 1):
        if text.startswith(f"{i}."):
            target = r
            break
    if not target:
        await update.message.reply_text("⚠️ Keyboard မှ ရွေးပေးပါ")
        return GINST_DEL_GAME
    # Remove from Console_Games + clear Game_Library checkbox
    ok, gl_ok = await asyncio.gather(
        asyncio.to_thread(remove_console_game, cid, target["game_title"]),
        asyncio.to_thread(update_game_library_install, target["game_title"], cid, False),
    )
    if ok:
        gl_note = "  📊 Game Library ✅" if gl_ok else "  📊 Game Library ⚠️ (manual update လို)"
        await update.message.reply_text(
            f"🗑️ <b>{cid}</b> မှ <b>\"{target['game_title']}\"</b> ဖျက်ပြီ\n{gl_note}",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("❌ ဖျက်မရပါ — ထပ်ကြိုးစားပါ")
    return await show_ginst_menu(update, context)
