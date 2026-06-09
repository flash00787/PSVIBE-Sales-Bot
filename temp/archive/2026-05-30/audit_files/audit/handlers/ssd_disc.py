"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
from datetime import datetime, timezone, timedelta

from bot import (
    BTN_BACK, BTN_BACK_MAIN,
    BTN_GINST_DISC, BTN_GINST_HDD, BTN_GINST_SSD,
    BTN_SSD_ADD, BTN_SSD_BLUE, BTN_SSD_GREY,
    BTN_SSD_REMOVE, BTN_SSD_RETURN, BTN_SSD_T1,
    BTN_SSD_TRANSFER, BTN_SSD_VIEW,
    DISC_SELECT, DISC_SET_QTY,
    SSD_MENU, SSD_VIEW_SSD, SSD_ADD_SSD, SSD_ADD_GAME, SSD_ADD_TYPE,
    SSD_DEL_SSD, SSD_DEL_GAME,
    SSD_XFER_SSD, SSD_XFER_GAME, SSD_XFER_CONS,
    SSD_RET_CONS, SSD_RET_GAME,
    fetch_console_games, fetch_game_library,
    SSD_NAMES, SSD_BTN_TO_ID,
)
# Note: show_game_menu, show_console_menu imported lazily (circular import)


def _ssd_kb():
    """Keyboard with all 3 SSD names + Back."""
    return ReplyKeyboardMarkup(
        [[BTN_SSD_T1], [BTN_SSD_BLUE], [BTN_SSD_GREY], [BTN_BACK]],
        resize_keyboard=True,
    )

async def step_disc_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot import show_game_menu  # noqa: F811, F401
    """User picked a game from the disc record list (button label includes disc count)."""
    text  = update.message.text.strip()
    if text == BTN_BACK:
        return await show_game_menu(update, context)
    # Buttons are labelled "Title  💿Npc" or "Title  💿--"
    disc_map = context.user_data.get("disc_map", {})
    target   = disc_map.get(text)
    if not target:
        # Fallback: try matching by title portion (strip emoji suffix)
        clean = text.split("  💿")[0].strip() if "💿" in text else text.strip()
        target = disc_map.get(clean)
    if not target:
        # Last resort: case-insensitive partial match
        for k, v in disc_map.items():
            if clean.lower() in k.lower() or k.lower() in clean.lower():
                target = v
                break
    if not target:
        await update.message.reply_text("⚠️ ဂိမ်း မတွေ့ပါ — ထပ်ရွေးပါ")
        return DISC_SELECT
    context.user_data["disc_target"] = target
    current = target.get("discs", "").strip()
    cur_str = f"{current}pc" if current and current != "0" else "မမှတ်ထားရသေး"
    await update.message.reply_text(
        f"💿 <b>{target['title']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"လက်ရှိ disc: <b>{cur_str}</b>\n\n"
        f"ခွေဘယ်နှ့ ရှိသည် ရိုက်ထည့်ပါ (ဂဏန်းသာ):",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([[BTN_BACK]], resize_keyboard=True),
    )
    return DISC_SET_QTY

async def step_disc_set_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot import show_game_menu  # noqa: F811, F401
    """User entered the new disc count — save to sheet."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_game_menu(update, context)
    if not text.isdigit():
        await update.message.reply_text("⚠️ ဂဏန်းသာ ရိုက်ပါ (ဥပမာ: 2)")
        return DISC_SET_QTY
    count  = int(text)
    target = context.user_data.get("disc_target", {})
    row    = target.get("row", 0)
    title  = target.get("title", "?")
    if not row:
        await update.message.reply_text("❌ Error — ထပ်ကြိုးစားပါ")
        return await show_game_menu(update, context)
    ok = await asyncio.to_thread(set_game_disc_count, row, count)
    if ok:
        await update.message.reply_text(
            f"✅ <b>{title}</b>\n"
            f"💿 Disc count: <b>{count}pc</b> မှတ်သားပြီ",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("❌ Sheet ထဲ save မရပါ — ထပ်ကြိုးစားပါ")
    return await show_game_menu(update, context)

async def show_ssd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """SSD Management hub."""
    # Count games per SSD
    cgames = fetch_console_games()
    counts = {sid: sum(1 for r in cgames if r["console_id"] == sid) for sid in SSD_NAMES}
    count_str = "  |  ".join(f"{SSD_NAMES[s]}: {counts[s]}ဂိမ်း" for s in SSD_NAMES)
    kb = [
        [BTN_SSD_VIEW],
        [BTN_SSD_ADD,     BTN_SSD_REMOVE],
        [BTN_SSD_TRANSFER, BTN_SSD_RETURN],
        [BTN_BACK],
    ]
    await update.message.reply_text(
        f"📀 *External SSD Management*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{count_str}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 ကြည့် — SSD ထဲ ဘာ ရှိသလဲ\n"
        f"➕ ထည့် — SSD ထဲ ဂိမ်း မှတ်သား\n"
        f"❌ ဖျက် — SSD မှ ဂိမ်း ဖျက်\n"
        f"🔄 Transfer — SSD → Console (session အတွက်)\n"
        f"↩️ Return   — Console → SSD (session ပြီးပြီ)",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SSD_MENU

async def step_ssd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot import show_console_menu  # noqa: F811, F401
    text = update.message.text.strip()
    if text in (BTN_BACK, BTN_BACK_MAIN):
        return await show_console_menu(update, context)
    if text == BTN_SSD_VIEW:
        await update.message.reply_text("📀 ကြည့်မည့် SSD ရွေးပါ:", reply_markup=_ssd_kb())
        return SSD_VIEW_SSD
    if text == BTN_SSD_ADD:
        await update.message.reply_text("➕ ဂိမ်း ထည့်မည့် SSD ရွေးပါ:", reply_markup=_ssd_kb())
        return SSD_ADD_SSD
    if text == BTN_SSD_REMOVE:
        await update.message.reply_text("❌ ဂိမ်း ဖျက်မည့် SSD ရွေးပါ:", reply_markup=_ssd_kb())
        return SSD_DEL_SSD
    if text == BTN_SSD_TRANSFER:
        await update.message.reply_text(
            "🔄 *SSD → Console Transfer*\n\nSSD ကို ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=_ssd_kb(),
        )
        return SSD_XFER_SSD
    if text == BTN_SSD_RETURN:
        await update.message.reply_text(
            "↩️ *Console → SSD Return*\n\nConsole ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(
                [[c["id"]] for c in get_consoles_from_setting()] + [[BTN_BACK]],
                resize_keyboard=True,
            ),
        )
        return SSD_RET_CONS
    return await show_ssd_menu(update, context)

async def step_ssd_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all games stored on the chosen SSD."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    ssd_id = SSD_BTN_TO_ID.get(text)
    if not ssd_id:
        await update.message.reply_text("⚠️ မှန်သော SSD ရွေးပါ:", reply_markup=_ssd_kb())
        return SSD_VIEW_SSD
    rows = [r for r in fetch_console_games() if r["console_id"] == ssd_id]
    if not rows:
        await update.message.reply_text(
            f"📀 <b>{SSD_NAMES[ssd_id]}</b> — ဂိမ်း မရှိသေးပါ",
            parse_mode="HTML",
        )
    else:
        lines = [f"📀 <b>{SSD_NAMES[ssd_id]}</b> ({len(rows)} ဂိမ်း)\n━━━━━━━━━━━━━━━━━━"]
        for i, r in enumerate(rows, 1):
            install_t = r.get("install_type", "")
            note_str  = f"  [{r['notes']}]" if r.get("notes") else ""
            lines.append(f"{i}. 🎮 {r['game_title']}  ({install_t}){note_str}")
        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    return await show_ssd_menu(update, context)

async def step_ssd_add_ssd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose which SSD to add game to."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    ssd_id = SSD_BTN_TO_ID.get(text)
    if not ssd_id:
        await update.message.reply_text("⚠️ မှန်သော SSD ရွေးပါ:", reply_markup=_ssd_kb())
        return SSD_ADD_SSD
    context.user_data["ssd_target"] = ssd_id
    # Show Game Library as options
    games = fetch_game_library()
    titles = [g["title"] for g in games if g.get("title")]
    kb_rows = [[t] for t in titles] + [[BTN_BACK]]
    await update.message.reply_text(
        f"📀 <b>{SSD_NAMES[ssd_id]}</b> ထဲ ထည့်မည့် ဂိမ်း ရွေးပါ:\n"
        f"(Library မှ ရွေးပါ သို့ ဂိမ်းနာမည် ရိုက်ထည့်)",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return SSD_ADD_GAME

async def step_ssd_add_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User typed/chose the game name to add to SSD — save directly as SSD Copy."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    ssd_id    = context.user_data.get("ssd_target", "")
    game      = text
    inst_type = "SSD Copy"

    # ── Duplicate check ───────────────────────────────────────────────────────
    existing = await asyncio.to_thread(fetch_console_games)
    already  = any(
        r["console_id"].strip().upper() == ssd_id.upper()
        and r["game_title"].strip().lower() == game.strip().lower()
        for r in existing
    )
    if already:
        await update.message.reply_text(
            f"⚠️ <b>\"{game}\"</b> သည် <b>{SSD_NAMES.get(ssd_id, ssd_id)}</b> မှာ ရှိပြီးသားပါ",
            parse_mode="HTML",
        )
        return await show_ssd_menu(update, context)

    ok = await asyncio.to_thread(write_console_game, ssd_id, game, inst_type)
    if ok:
        await update.message.reply_text(
            f"✅ <b>{SSD_NAMES.get(ssd_id, ssd_id)}</b> ထဲ <b>\"{game}\"</b> ထည့်ပြီ",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("❌ မှတ်သားမရပါ — ထပ်ကြိုးစားပါ")
    return await show_ssd_menu(update, context)

async def step_ssd_add_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store selected install type for SSD game."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    valid = {BTN_GINST_HDD: "HDD", BTN_GINST_DISC: "Disc", BTN_GINST_SSD: "SSD Copy"}
    if text not in valid:
        await update.message.reply_text("⚠️ မှန်သော type ရွေးပါ")
        return SSD_ADD_TYPE
    ssd_id   = context.user_data.get("ssd_target", "")
    game     = context.user_data.get("ssd_game", "")
    inst_type = valid[text]
    ok = write_console_game(ssd_id, game, inst_type, "")
    if ok:
        await update.message.reply_text(
            f"✅ <b>{SSD_NAMES.get(ssd_id, ssd_id)}</b> ထဲ <b>\"{game}\"</b> ထည့်ပြီ",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("❌ မှတ်သားမရပါ — ထပ်ကြိုးစားပါ")
    return await show_ssd_menu(update, context)

async def step_ssd_del_ssd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose which SSD to remove a game from."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    ssd_id = SSD_BTN_TO_ID.get(text)
    if not ssd_id:
        await update.message.reply_text("⚠️ မှန်သော SSD ရွေးပါ:", reply_markup=_ssd_kb())
        return SSD_DEL_SSD
    rows = [r for r in fetch_console_games() if r["console_id"] == ssd_id]
    if not rows:
        await update.message.reply_text(
            f"📀 <b>{SSD_NAMES[ssd_id]}</b> — ဂိမ်း မရှိသေးပါ",
            parse_mode="HTML",
        )
        return await show_ssd_menu(update, context)
    context.user_data["ssd_target"] = ssd_id
    titles = [r["game_title"] for r in rows]
    kb_rows = [[t] for t in titles] + [[BTN_BACK]]
    await update.message.reply_text(
        f"📀 <b>{SSD_NAMES[ssd_id]}</b> မှ ဖျက်မည့် ဂိမ်း ရွေးပါ:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return SSD_DEL_GAME

async def step_ssd_del_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete chosen game from SSD."""
    text = update.message.text.strip()
    ssd_id = context.user_data.get("ssd_target", "")
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    rows = [r for r in fetch_console_games() if r["console_id"] == ssd_id]
    target = next((r for r in rows if r["game_title"] == text), None)
    if not target:
        await update.message.reply_text("⚠️ ဂိမ်း မတွေ့ပါ — ထပ်ရွေးပါ")
        return SSD_DEL_GAME
    ok = delete_console_game(ssd_id, text)
    if ok:
        await update.message.reply_text(
            f"🗑️ <b>{SSD_NAMES.get(ssd_id, ssd_id)}</b> မှ <b>\"{text}\"</b> ဖျက်ပြီ",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("❌ ဖျက်မရပါ — ထပ်ကြိုးစားပါ")
    return await show_ssd_menu(update, context)

async def step_ssd_xfer_ssd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose source SSD for transfer."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    ssd_id = SSD_BTN_TO_ID.get(text)
    if not ssd_id:
        await update.message.reply_text("⚠️ မှန်သော SSD ရွေးပါ:", reply_markup=_ssd_kb())
        return SSD_XFER_SSD
    rows = [r for r in fetch_console_games() if r["console_id"] == ssd_id]
    if not rows:
        await update.message.reply_text(
            f"📀 <b>{SSD_NAMES[ssd_id]}</b> — ဂိမ်း မရှိသေးပါ",
            parse_mode="HTML",
        )
        return await show_ssd_menu(update, context)
    context.user_data["ssd_xfer_src"] = ssd_id
    titles = [r["game_title"] for r in rows]
    kb_rows = [[t] for t in titles] + [[BTN_BACK]]
    await update.message.reply_text(
        f"🔄 <b>{SSD_NAMES[ssd_id]}</b> မှ Transfer မည့် ဂိမ်း ရွေးပါ:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return SSD_XFER_GAME

async def step_ssd_xfer_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose game to transfer."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        # If came from session start, go back to game prompt
        if context.user_data.pop("ssd_return_to_session", False):
            context.user_data.pop("ssd_xfer_target_cons", None)
            return await prompt_book_game(update, context)
        return await show_ssd_menu(update, context)
    ssd_id = context.user_data.get("ssd_xfer_src", "")
    rows = [r for r in fetch_console_games() if r["console_id"] == ssd_id]
    target = next((r for r in rows if r["game_title"] == text), None)
    if not target:
        await update.message.reply_text("⚠️ ဂိမ်း မတွေ့ပါ — ထပ်ရွေးပါ")
        return SSD_XFER_GAME
    context.user_data["ssd_xfer_game"] = text

    # ── Session-start shortcut: console already known, skip console picker ──
    if context.user_data.get("ssd_return_to_session"):
        target_cid = context.user_data.get("ssd_xfer_target_cons", "")
        src_lbl    = SSD_NAMES.get(ssd_id, ssd_id)
        existing   = await asyncio.to_thread(fetch_console_games)
        already    = any(
            r["console_id"].strip().upper() == target_cid.upper()
            and r["game_title"].strip().lower() == text.strip().lower()
            for r in existing
        )
        if already:
            await update.message.reply_text(
                f"⚠️ <b>\"{text}\"</b> သည် <b>{target_cid}</b> မှာ ရှိပြီးသားပါ\n"
                f"ထပ် transfer မလိုပါ",
                parse_mode="HTML",
            )
        else:
            ok = write_console_game(target_cid, text, "SSD Transfer", f"From {src_lbl}")
            if ok:
                await asyncio.to_thread(remove_console_game, ssd_id, text)
                await update.message.reply_text(
                    f"✅ <b>\"{text}\"</b> Transfer ပြီးပါပြီ\n"
                    f"📀 {src_lbl} → 🕹️ <b>{target_cid}</b>\n"
                    f"(session ပြီးရင် ↩️ Return ဖြင့် SSD ပြန်ထည့်ပါ)",
                    parse_mode="HTML",
                )
            else:
                await update.message.reply_text("❌ Transfer မှတ်မရပါ — ထပ်ကြိုးစားပါ")
        context.user_data.pop("ssd_return_to_session", None)
        context.user_data.pop("ssd_xfer_target_cons", None)
        return await prompt_book_game(update, context)
    # ── Normal flow: ask which console ──────────────────────────────────────
    consoles = get_consoles_from_setting()
    kb_rows = [[c["id"]] for c in consoles] + [[BTN_BACK]]
    await update.message.reply_text(
        f"🔄 <b>\"{text}\"</b> ကို ဘယ် Console ထဲ ထည့်မည်နည်း?",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return SSD_XFER_CONS

async def step_ssd_xfer_cons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Record transfer: add game to console with 'SSD Transfer' type, with duplicate check."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    ssd_id  = context.user_data.get("ssd_xfer_src", "")
    game    = context.user_data.get("ssd_xfer_game", "")
    cid     = text
    src_lbl = SSD_NAMES.get(ssd_id, ssd_id)

    # ── Duplicate check: game already on target console? ──────────────────────
    existing = await asyncio.to_thread(fetch_console_games)
    already  = any(
        r["console_id"].strip().upper() == cid.upper()
        and r["game_title"].strip().lower() == game.strip().lower()
        for r in existing
    )
    if already:
        await update.message.reply_text(
            f"⚠️ <b>\"{game}\"</b> သည် <b>{cid}</b> မှာ ရှိပြီးသားပါ\n"
            f"ထပ် transfer မလိုပါ",
            parse_mode="HTML",
        )
        return await show_ssd_menu(update, context)

    ok = write_console_game(cid, game, "SSD Transfer", f"From {src_lbl}")
    if ok:
        # ── Move: remove from SSD after writing to console ────────────────────
        await asyncio.to_thread(remove_console_game, ssd_id, game)
        await update.message.reply_text(
            f"✅ <b>\"{game}\"</b>\n"
            f"📀 {src_lbl} → 🕹️ <b>{cid}</b>\n"
            f"(SSD မှ ဖယ်ရှားပြီ — session ဆုံးသည်နှင့် Return ဖြင့် ပြန်ထည့်ပါ)",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("❌ Transfer မှတ်မရပါ — ထပ်ကြိုးစားပါ")
    return await show_ssd_menu(update, context)

async def step_ssd_ret_cons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose console to return SSD games from."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    cid  = text
    rows = [
        r for r in fetch_console_games()
        if r["console_id"].upper() == cid.upper()
        and "SSD Transfer" in r.get("install_type", "")
    ]
    if not rows:
        await update.message.reply_text(
            f"🕹️ <b>{cid}</b> — SSD Transfer ဂိမ်း မရှိပါ",
            parse_mode="HTML",
        )
        return await show_ssd_menu(update, context)
    context.user_data["ssd_ret_cons"] = cid
    titles = [r["game_title"] for r in rows]
    kb_rows = [[t] for t in titles] + [[BTN_BACK]]
    await update.message.reply_text(
        f"↩️ <b>{cid}</b> မှ SSD ပြန်ရွေ့မည့် ဂိမ်း ရွေးပါ:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return SSD_RET_GAME

async def step_ssd_ret_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove 'SSD Transfer' entry from console (game returned to SSD)."""
    text = update.message.text.strip()
    cid  = context.user_data.get("ssd_ret_cons", "")
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    ok = delete_console_game(cid, text)
    if ok:
        await update.message.reply_text(
            f"✅ <b>\"{text}\"</b> — 🕹️ <b>{cid}</b> မှ SSD ပြန်ရွေ့ပြီ ✔️",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("❌ မရပါ — ထပ်ကြိုးစားပါ")
    return await show_ssd_menu(update, context)