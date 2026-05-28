"""PS VIBE Bot — Game Library handlers.
Auto-refactored from monolithic handlers.py (Phase 6).
"""
# ═══════ Imports from bot package ═══════
import bot as _bot_module  # for globals that need mutation  # noqa: F401
from bot import *  # noqa: F401,F403


async def show_game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [BTN_VIEW_GAMES,      BTN_ADD_GAME],
        [BTN_CONSOLE_INSTALL, BTN_DEL_GAME],
        [BTN_EDIT_GAME,       BTN_DISC_RECORD],
        [BTN_SSD_MANAGE],
        [BTN_BACK_MAIN],
    ]
    games = fetch_games()
    count = len(games)
    await update.message.reply_text(
        f"🎮 *Game Library* ({count} ဂိမ်း)\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Action ရွေးပါ ↓",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return GAME_MENU

async def step_game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    if choice in (BTN_BACK, BTN_BACK_MAIN):
        return await show_main_menu(update, context)
    if choice == BTN_VIEW_GAMES:
        games       = fetch_games()
        cgames      = fetch_console_games()  # Console_Games sheet records
        if not games:
            await update.message.reply_text("ℹ️ Game Library ဗလာ ဖြစ်နေသည်\nဂိမ်းထည့်ပါ")
        else:
            # Build a map: game_title_lower → [console_ids]
            install_map: dict[str, list[str]] = {}
            for r in cgames:
                gt = r.get("game_title", "").strip()
                cid = r.get("console_id", "").strip()
                if gt and cid:
                    install_map.setdefault(gt.lower(), []).append(cid)

            lines = [f"🎮 <b>Game Library</b> ({len(games)} ဂိမ်း)\n━━━━━━━━━━━━━━━━━━"]
            for i, g in enumerate(games, 1):
                name  = g.get("title", "").strip()
                if not name:
                    continue
                # Installed consoles
                cons_list  = install_map.get(name.lower(), [])
                discs      = g.get("discs", "").strip()
                solo_multi = g.get("solo_multi", "").strip()
                genre      = g.get("genre", "").strip()
                discs_str   = f" 💿<b>{discs}pc</b>" if discs and discs not in ("", "0") else ""
                install_str = f"🖥️ {', '.join(cons_list)}" if cons_list else "🖥️ <i>Not installed</i>"
                sm_icon = "🧑" if solo_multi == "Solo" else ("👥" if solo_multi == "Multiplayer" else ("🧑👥" if solo_multi else ""))
                tags = ""
                if sm_icon and solo_multi:
                    tags += f" {sm_icon}{solo_multi}"
                if genre:
                    tags += f" · {genre}"
                lines.append(f"{i}. <b>{name}</b>{discs_str}{tags}\n   {install_str}")
            chunk = ""
            for ln in lines:
                if len(chunk) + len(ln) + 2 > 3800:
                    await update.message.reply_text(chunk, parse_mode="HTML")
                    chunk = ln
                else:
                    chunk = chunk + "\n" + ln if chunk else ln
            if chunk:
                await update.message.reply_text(chunk, parse_mode="HTML")
        return await show_game_menu(update, context)
    if choice == BTN_ADD_GAME:
        context.user_data.pop("new_game", None)
        context.user_data["new_game"] = {}
        await update.message.reply_text(
            "➕ *ဂိမ်းအသစ် ထည့်*\n━━━━━━━━━━━━━━━━━━\n"
            "🎮 ဂိမ်းနာမည် ရိုက်ပါ:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([[BTN_CANCEL]], resize_keyboard=True),
        )
        return GAME_ADD_TITLE
    if choice == BTN_CONSOLE_INSTALL:
        return await show_ginst_menu(update, context)
    if choice == BTN_SSD_MANAGE:
        return await show_ssd_menu(update, context)
    if choice == BTN_DISC_RECORD:
        games = fetch_games()
        if not games:
            await update.message.reply_text("ℹ️ Game Library ဗလာ ဖြစ်နေသည်")
            return await show_game_menu(update, context)
        context.user_data["disc_games"] = games
        # Build label→game mapping; store by BOTH label and title for robust lookup
        disc_map = {}
        kb_rows  = []
        for g in games:
            d   = g.get("discs", "").strip()
            lbl = f"{g['title']}  💿{d}pc" if d and d != "0" else f"{g['title']}  💿--"
            disc_map[lbl]          = g   # exact label key
            disc_map[g["title"]]   = g   # title-only fallback key
            kb_rows.append([lbl])
        kb_rows.append([BTN_BACK])
        context.user_data["disc_map"] = disc_map
        await update.message.reply_text(
            "💿 <b>Game Discs Record</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "ပြင်မည့် ဂိမ်း ရွေးပါ:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
        )
        return DISC_SELECT
    if choice == BTN_EDIT_GAME:
        games = fetch_games()
        if not games:
            await update.message.reply_text("ℹ️ ဂိမ်း မရှိပါ")
            return await show_game_menu(update, context)
        context.user_data["edit_games"] = games
        kb = [[f"{i}. {g['title']}"] for i, g in enumerate(games, 1)]
        kb.append([BTN_BACK])
        await update.message.reply_text(
            "✏️ <b>Edit Game</b>\n━━━━━━━━━━━━━━━━━━\nပြင်မည့် ဂိမ်း ရွေးပါ:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return GAME_EDIT_SELECT
    if choice == BTN_DEL_GAME:
        games = fetch_games()
        if not games:
            await update.message.reply_text("ℹ️ ဖျက်ရန် ဂိမ်းမရှိပါ")
            return await show_game_menu(update, context)
        kb = [[f"{i}. {g['title']}" ] for i, g in enumerate(games, 1)]
        kb.append([BTN_BACK])
        context.user_data["del_games"] = games
        await update.message.reply_text(
            "🗑️ *ဂိမ်းဖျက်မည်*\n━━━━━━━━━━━━━━━━━━\n"
            "ဖျက်မည့် ဂိမ်းကို ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
        )
        return GAME_DEL_SELECT
    return await show_game_menu(update, context)

async def step_game_add_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await show_game_menu(update, context)
    context.user_data["new_game"]["title"] = text
    await update.message.reply_text(
        f"🎮 <b>{text}</b>\n\n"
        "👥 Solo / Multiplayer ရွေးပါ:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            [["Solo", "Multiplayer"], ["Solo & Multi"], [BTN_CANCEL]],
            resize_keyboard=True,
        ),
    )
    return GAME_ADD_PLATFORM

async def step_game_add_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Repurposed as Solo/Multiplayer selection step."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await show_game_menu(update, context)
    valid = ("Solo", "Multiplayer", "Solo & Multi")
    if text not in valid:
        await update.message.reply_text(
            "⚠️ Solo / Multiplayer / Solo & Multi မှ ရွေးပါ",
            reply_markup=ReplyKeyboardMarkup(
                [["Solo", "Multiplayer"], ["Solo & Multi"], [BTN_CANCEL]],
                resize_keyboard=True,
            ),
        )
        return GAME_ADD_PLATFORM
    context.user_data["new_game"]["solo_multi"] = text
    await update.message.reply_text(
        "🎯 Genre ရွေးပါ (သို့) ရိုက်ထည့်ပါ:",
        reply_markup=ReplyKeyboardMarkup(
            [["Action", "Sports"], ["Racing", "Fighting"],
             ["Adventure", "RPG"], ["Horror", "Simulation"],
             ["Puzzle", "Other"], [BTN_CANCEL]],
            resize_keyboard=True,
        ),
    )
    return GAME_ADD_GENRE

async def step_game_add_genre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genre selection step — then ask for copies count."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await show_game_menu(update, context)
    if not text:
        await update.message.reply_text("⚠️ Genre ရိုက်ပါ:")
        return GAME_ADD_GENRE
    context.user_data["new_game"]["genre"] = text
    await update.message.reply_text(
        f"🎯 Genre: <b>{text}</b>\n\n"
        "💿 Disc/Copy ဘယ်နှစ်ခု ရှိသလဲ?",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            [["1", "2", "3"], [BTN_CANCEL]],
            resize_keyboard=True,
        ),
    )
    return GAME_ADD_STATUS

async def step_game_add_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Copies count step — then save to sheet."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await show_game_menu(update, context)
    try:
        copies = int(text)
        if copies < 1 or copies > 20:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "⚠️ ဂဏန်း (1-20) ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([["1", "2", "3"], [BTN_CANCEL]], resize_keyboard=True),
        )
        return GAME_ADD_STATUS
    g = context.user_data.get("new_game", {})
    g["copies"] = copies
    title      = g.get("title", "")
    solo_multi = g.get("solo_multi", "")
    genre      = g.get("genre", "")
    # Metadata stored in col U (Installed_On) as "solo_multi|genre"
    meta = f"{solo_multi}|{genre}"
    try:
        sh = get_game_lib_sh()
        # Determine next row number and next empty row
        all_rows = sh.get_all_values()
        existing_nos = [int(r[0]) for r in all_rows[1:] if r and r[0].strip().isdigit()]
        next_no   = max(existing_nos, default=0) + 1
        next_row  = len(all_rows) + 1  # append after last row
        # Build full row (20 cols: A-T) — Col E was Total Copies (removed)
        new_row = [next_no, title, "Not Installed",
                   copies, 0,
                   False, False, False, False, False,
                   False, False, False, False, False,
                   False, False, False, "", meta]
        # Use update() on specific row to avoid SSD-section column-offset bug
        sh.update(f"A{next_row}:T{next_row}", [new_row], value_input_option="USER_ENTERED")
        # Invalidate cache
        import bot as _bot_mod
        _bot_mod._GAME_ROWS = []
        _bot_mod._GAME_TS = 0
        # Solo/Multi emoji
        sm_icon = "🧑" if solo_multi == "Solo" else ("👥" if solo_multi == "Multiplayer" else "🧑👥")
        await update.message.reply_text(
            f"✅ <b>ဂိမ်းထည့်ပြီ!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎮 Game     : <b>{title}</b>\n"
            f"{sm_icon} Mode     : <b>{solo_multi}</b>\n"
            f"🎯 Genre    : <b>{genre}</b>\n"
            f"💿 Copies   : <b>{copies}</b>\n"
            f"📊 Status   : <b>Not Installed</b>\n\n"
            f"ℹ️ Console Install မှ console ထဲ ထည့်နိုင်သည်",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Save မအောင်မြင်ပါ: {e}")
    return await show_game_menu(update, context)

async def step_game_edit_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User picked a game to edit — ask which field to edit."""
    text  = update.message.text.strip()
    if text == BTN_BACK:
        return await show_game_menu(update, context)
    games  = context.user_data.get("edit_games", [])
    target = None
    for i, g in enumerate(games, 1):
        if text.startswith(f"{i}."):
            target = g
            break
    if not target:
        await update.message.reply_text("⚠️ Keyboard မှ ရွေးပေးပါ")
        return GAME_EDIT_SELECT
    context.user_data["edit_target"] = target
    sm  = target.get("solo_multi", "") or "မသတ်မှတ်ရသေး"
    gen = target.get("genre", "")      or "မသတ်မှတ်ရသေး"
    await update.message.reply_text(
        f"✏️ <b>{target['title']}</b>\n━━━━━━━━━━━━━━━━━━\n👥 Solo/Multi : <b>{sm}</b>\n🎯 Genre      : <b>{gen}</b>\n"
        f"ဘာပြင်မလဲ?",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            [["👥 Solo/Multi", "🎯 Genre"], [BTN_BACK]],
            resize_keyboard=True,
        ),
    )
    return GAME_EDIT_FIELD

async def step_game_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User picked which field to edit — ask for new value."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_game_menu(update, context)
    if text == "👥 Solo/Multi":
        context.user_data["edit_field"] = "solo_multi"
        await update.message.reply_text(
            "👥 Solo/Multi ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(
                [["Solo", "Multiplayer"], ["Solo & Multi"], [BTN_BACK]],
                resize_keyboard=True,
            ),
        )
    elif text == "🎯 Genre":
        context.user_data["edit_field"] = "genre"
        await update.message.reply_text(
            "🎯 Genre ရွေးပါ (သို့) ရိုက်ထည့်ပါ:",
            reply_markup=ReplyKeyboardMarkup(
                [["Action", "Sports"], ["Racing", "Fighting"],
                 ["Adventure", "RPG"], ["Horror", "Simulation"],
                 ["Puzzle", "Other"], [BTN_BACK]],
                resize_keyboard=True,
            ),
        )
    else:
        await update.message.reply_text("⚠️ Solo/Multi သို့မဟုတ် Genre ရွေးပါ")
        return GAME_EDIT_FIELD
    return GAME_EDIT_VALUE

async def step_game_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User entered new value — save to col U of Game_Library sheet."""
    text  = update.message.text.strip()
    if text == BTN_BACK:
        return await show_game_menu(update, context)
    field  = context.user_data.get("edit_field", "")
    target = context.user_data.get("edit_target", {})
    if not field or not target:
        return await show_game_menu(update, context)
    # Validate solo_multi
    if field == "solo_multi" and text not in ("Solo", "Multiplayer", "Solo & Multi"):
        await update.message.reply_text(
            "⚠️ Solo / Multiplayer / Solo & Multi မှ ရွေးပါ",
            reply_markup=ReplyKeyboardMarkup(
                [["Solo", "Multiplayer"], ["Solo & Multi"], [BTN_BACK]],
                resize_keyboard=True,
            ),
        )
        return GAME_EDIT_VALUE
    # Build updated metadata string for col U
    cur_sm  = target.get("solo_multi", "")
    cur_gen = target.get("genre", "")
    if field == "solo_multi":
        new_sm  = text
        new_gen = cur_gen
    else:
        new_sm  = cur_sm
        new_gen = text
    meta    = f"{new_sm}|{new_gen}"
    row_num = target.get("row", 0)
    title   = target.get("title", "?")
    try:
        sh = get_game_lib_sh()
        sh.update_cell(row_num, 21, meta)   # col U = index 21
        # Invalidate cache
        import bot as _bot_mod
        _bot_mod._GAME_ROWS = []
        _bot_mod._GAME_TS = 0
        field_label = "Solo/Multi" if field == "solo_multi" else "Genre"
        await update.message.reply_text(
            f"✅ <b>{title}</b>\n━━━━━━━━━━━━━━━━━━\n✏️ {field_label}: <b>{text}</b> မှတ်သားပြီ",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Save မအောင်မြင်ပါ: {e}")
    return await show_game_menu(update, context)

async def step_game_del_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_game_menu(update, context)
    games = context.user_data.get("del_games", [])
    target = None
    for i, g in enumerate(games, 1):
        if text.startswith(f"{i}."):
            target = g
            break
    if not target:
        await update.message.reply_text("⚠️ Keyboard မှ ရွေးပေးပါ")
        return GAME_DEL_SELECT
    game_name = target.get("title", "")
    try:
        sh = get_game_lib_sh()
        sh.delete_rows(target["row"])
        await update.message.reply_text(
            f"🗑️ <b>\"{game_name}\"</b> ဂိမ်း ဖျက်ပြီ",
            parse_mode="HTML",
        )
    except Exception as e:
        err_str = str(e)
        if "protected" in err_str.lower() or "400" in err_str:
            await update.message.reply_text(
                f"⚠️ <b>Game Library sheet protected</b> ဖြစ်သောကြောင့်\n"
                f"bot မှ row ဖျက်ခြင်း မပြုနိုင်ပါ\n\n"
                f"📋 Google Sheet ကို directly ဝင်ပြီး\n"
                f"<b>\"{game_name}\"</b> row ကို ဖျက်ပေးပါ",
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(f"❌ ဖျက်မရပါ: {err_str}")
    return await show_game_menu(update, context)
