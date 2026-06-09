#!/usr/bin/env python3
"""Add move functionality to ssd_disc.py"""

with open('/root/psvibe-sales-bot/bot/handlers/ssd_disc.py') as f:
    content = f.read()

# 1. Update imports
old_import_start = 'from bot import ('
old_import_end = ')'
# Find the import block
import_start = content.find('from bot import (')
import_end = content.find('\n)', import_start)

if import_start >= 0 and import_end >= 0:
    old_import_block = content[import_start:import_end+2]
    new_import_block = '''from bot import (
    BTN_BACK, BTN_BACK_MAIN, BTN_GINST_DISC, BTN_GINST_HDD,
    BTN_GINST_SSD, BTN_SSD_ADD, BTN_SSD_BLUE, BTN_SSD_GREY,
    BTN_SSD_MOVE_TO_CONSOLE, BTN_SSD_MOVE_TO_SSD,
    BTN_SSD_REMOVE, BTN_SSD_RETURN, BTN_SSD_T1, BTN_SSD_TRANSFER,
    BTN_SSD_VIEW, DISC_SELECT, DISC_SET_QTY, SSD_ADD_GAME, SSD_ADD_SSD,
    SSD_ADD_TYPE, SSD_DEL_GAME, SSD_DEL_SSD, SSD_MENU, SSD_RET_CONS,
    SSD_RET_GAME, SSD_VIEW_SSD, SSD_XFER_CONS, SSD_XFER_GAME,
    SSD_XFER_SSD, SSD_BTN_TO_ID, SSD_NAMES, delete_console_game,
    fetch_console_games, fetch_console_games_async, fetch_game_library,
    get_consoles_from_setting, remove_console_game, remove_console_game_async,
    set_game_disc_count, set_game_disc_count_async, show_console_menu,
    show_game_menu, write_console_game,
    SSD_MOVE_SSD, SSD_MOVE_GAME, SSD_MOVE_CONS,
    SSD_MOVE_FROM_CONS, SSD_MOVE_FROM_GAME, SSD_MOVE_TO_SSD,
)'''
    content = content[:import_start] + new_import_block + content[import_end+2:]
    print('ssd_disc: imports updated')
else:
    print('ssd_disc: import block NOT FOUND')

# 2. Add move_console_game_async import after asyncio
content = content.replace(
    'import asyncio\nlogger = logging.getLogger(__name__)',
    'import asyncio\nfrom bot.api_client import move_console_game_async\nlogger = logging.getLogger(__name__)'
)

# 3. Add move buttons to show_ssd_menu kb
content = content.replace(
    '        [BTN_SSD_TRANSFER, BTN_SSD_RETURN],\n        [BTN_BACK],',
    '        [BTN_SSD_TRANSFER, BTN_SSD_RETURN],\n        [BTN_SSD_MOVE_TO_CONSOLE, BTN_SSD_MOVE_TO_SSD],\n        [BTN_BACK],'
)

# 4. Add move handlers in step_ssd_menu (before the BTN_SSD_RETURN block)
old_return_block = '''    if text == BTN_SSD_RETURN:
        await update.message.reply_text(
            "\\u21a9\\ufe0f *Console \\u2192 SSD Return*\\n\\nConsole \\u101b\\u103d\\u1031\\u1038\\u1015\\u102b:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(
                [[c["id"]] for c in get_consoles_from_setting()] + [[BTN_BACK]],
                resize_keyboard=True,
            ),
        )
        return SSD_RET_CONS'''

move_block = '''    if text == BTN_SSD_MOVE_TO_CONSOLE:
        await update.message.reply_text(
            "\\U0001f504 *SSD\\u2192Console Move*\\n\\nSSD \\u101b\\u103d\\u1031\\u1038\\u1015\\u102b:",
            parse_mode="Markdown",
            reply_markup=_ssd_kb(),
        )
        return SSD_MOVE_SSD
    if text == BTN_SSD_MOVE_TO_SSD:
        await update.message.reply_text(
            "\\U0001f504 *Console\\u2192SSD Move*\\n\\nConsole \\u101b\\u103d\\u1031\\u1038\\u1015\\u102b:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(
                [[c["id"]] for c in get_consoles_from_setting()] + [[BTN_BACK]],
                resize_keyboard=True,
            ),
        )
        return SSD_MOVE_FROM_CONS
''' + old_return_block

if old_return_block in content:
    content = content.replace(old_return_block, move_block)
    print('ssd_disc: move handlers added to step_ssd_menu')
else:
    print('ssd_disc: BTN_SSD_RETURN block NOT FOUND')

# 5. Add move flow handler functions before the last line
move_handlers = '''
async def step_ssd_move_ssd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose SSD to move from (SSD->Console flow)."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    ssd_id = SSD_BTN_TO_ID.get(text)
    if not ssd_id:
        await update.message.reply_text("\\u26a0\\ufe0f \\u1019\\u103e\\u1014\\u103a\\u101e\\u1031\\u102c SSD \\u101b\\u103d\\u1031\\u1038\\u1015\\u102b:", reply_markup=_ssd_kb())
        return SSD_MOVE_SSD
    rows = [r for r in await fetch_console_games_async() if r["console_id"] == ssd_id]
    if not rows:
        await update.message.reply_text(
            f"\\U0001f4c0 <b>{SSD_NAMES[ssd_id]}</b> \\u2014 \\u1002\\u102d\\u1019\\u103a\\u1038 \\u1019\\u101b\\u103e\\u102d\\u101e\\u1031\\u1038\\u1015\\u102b",
            parse_mode="HTML",
        )
        return await show_ssd_menu(update, context)
    context.user_data["ssd_move_src"] = ssd_id
    titles = [r["game_title"] for r in rows]
    kb_rows = [[t] for t in titles] + [[BTN_BACK]]
    await update.message.reply_text(
        f"\\U0001f504 <b>{SSD_NAMES[ssd_id]}</b> \\u1019\\u103e Move \\u1019\\u100a\\u1037\\u103a \\u1002\\u102d\\u1019\\u103a\\u1038 \\u101b\\u103d\\u1031\\u1038\\u1015\\u102b:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return SSD_MOVE_GAME

async def step_ssd_move_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose game to move from SSD -> pick destination console."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    ssd_id = context.user_data.get("ssd_move_src", "")
    context.user_data["ssd_move_game"] = text
    consoles = get_consoles_from_setting()
    kb_rows = [[c["id"]] for c in consoles] + [[BTN_BACK]]
    await update.message.reply_text(
        f"\\U0001f504 <b>\\"{text}\\"</b> \\u1000\\u102d\\u102f \\u1018\\u101a\\u103a Console \\u1011\\u1032 \\u1011\\u100a\\u1037\\u103a\\u1019\\u100a\\u103a\\u1014\\u100a\\u103a\\u1038?",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return SSD_MOVE_CONS

async def step_ssd_move_cons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute SSD->Console move."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    ssd_id = context.user_data.get("ssd_move_src", "")
    game = context.user_data.get("ssd_move_game", "")
    to_console = text
    ok = await move_console_game_async(ssd_id, game, to_console)
    if ok:
        await update.message.reply_text(
            f"\\u2705 <b>\\"{game}\\"</b>\\n\\U0001f4c0 {SSD_NAMES.get(ssd_id, ssd_id)} \\u2192 \\U0001f579\\ufe0f <b>{to_console}</b>\\nMove \\u1015\\u103c\\u102e\\u1038\\u1015\\u102b\\u1015\\u103c\\u102e",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("\\u274c Move \\u1019\\u101b\\u1015\\u102b \\u2014 \\u1011\\u1015\\u103a\\u1000\\u103c\\u102d\\u102f\\u1038\\u1005\\u102c\\u1038\\u1015\\u102b")
    return await show_ssd_menu(update, context)

async def step_ssd_move_from_cons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose source console for Console->SSD move."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    cid = text
    rows = [r for r in await fetch_console_games_async()
            if r["console_id"].upper() == cid.upper()
            and r.get("status", "") == "Installed"]
    if not rows:
        await update.message.reply_text(
            f"\\U0001f579\\ufe0f <b>{cid}</b> \\u2014 Installed \\u1002\\u102d\\u1019\\u103a\\u1038 \\u1019\\u101b\\u103e\\u102d\\u1015\\u102b",
            parse_mode="HTML",
        )
        return await show_ssd_menu(update, context)
    context.user_data["ssd_move_from_cons"] = cid
    titles = [r["game_title"] for r in rows]
    kb_rows = [[t] for t in titles] + [[BTN_BACK]]
    await update.message.reply_text(
        f"\\U0001f504 <b>{cid}</b> \\u1019\\u103e Move \\u1019\\u100a\\u1037\\u103a \\u1002\\u102d\\u1019\\u103a\\u1038 \\u101b\\u103d\\u1031\\u1038\\u1015\\u102b:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return SSD_MOVE_FROM_GAME

async def step_ssd_move_from_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User chose game to move from console -> pick destination SSD."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    context.user_data["ssd_move_from_game"] = text
    await update.message.reply_text(
        f"\\U0001f504 <b>\\"{text}\\"</b> \\u1000\\u102d\\u102f \\u1018\\u101a\\u103a SSD \\u1011\\u1032 \\u1011\\u100a\\u1037\\u103a\\u1019\\u100a\\u103a\\u1014\\u100a\\u103a\\u1038?",
        parse_mode="HTML",
        reply_markup=_ssd_kb(),
    )
    return SSD_MOVE_TO_SSD

async def step_ssd_move_to_ssd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute Console->SSD move."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_ssd_menu(update, context)
    ssd_id = SSD_BTN_TO_ID.get(text)
    if not ssd_id:
        await update.message.reply_text("\\u26a0\\ufe0f \\u1019\\u103e\\u1014\\u103a\\u101e\\u1031\\u102c SSD \\u101b\\u103d\\u1031\\u1038\\u1015\\u102b:", reply_markup=_ssd_kb())
        return SSD_MOVE_TO_SSD
    from_cons = context.user_data.get("ssd_move_from_cons", "")
    game = context.user_data.get("ssd_move_from_game", "")
    ok = await move_console_game_async(from_cons, game, ssd_id)
    if ok:
        await update.message.reply_text(
            f"\\u2705 <b>\\"{game}\\"</b>\\n\\U0001f579\\ufe0f <b>{from_cons}</b> \\u2192 \\U0001f4c0 {SSD_NAMES.get(ssd_id, ssd_id)}\\nMove \\u1015\\u103c\\u102e\\u1038\\u1015\\u102b\\u1015\\u103c\\u102e",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("\\u274c Move \\u1019\\u101b\\u1015\\u102b \\u2014 \\u1011\\u1015\\u103a\\u1000\\u103c\\u102d\\u102f\\u1038\\u1005\\u102c\\u1038\\u1015\\u102b")
    return await show_ssd_menu(update, context)
'''

# Add before the last async function
content += move_handlers

with open('/root/psvibe-sales-bot/bot/handlers/ssd_disc.py', 'w') as f:
    f.write(content)
print('ssd_disc.py updated with move functionality')
