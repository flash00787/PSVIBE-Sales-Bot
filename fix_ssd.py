#!/usr/bin/env python3
"""Add move functions to ssd_disc.py and update bot app.py"""

# ─── Update ssd_disc.py imports ──────────────────────────────────
with open('/root/psvibe-sales-bot/bot/handlers/ssd_disc.py') as f:
    content = f.read()

# Update imports to include new constants and move_console_game_async
old_imports = 'from bot import (\n    BTN_BACK, BTN_BACK_MAIN, BTN_GINST_DISC, BTN_GINST_HDD,\n    BTN_GINST_SSD, BTN_SSD_ADD, BTN_SSD_BLUE, BTN_SSD_GREY,\n    BTN_SSD_REMOVE, BTN_SSD_RETURN, BTN_SSD_T1, BTN_SSD_TRANSFER,\n    BTN_SSD_VIEW, DISC_SELECT, DISC_SET_QTY, SSD_ADD_GAME, SSD_ADD_SSD,\n    SSD_ADD_TYPE, SSD_DEL_GAME, SSD_DEL_SSD, SSD_MENU, SSD_RET_CONS,\n    SSD_RET_GAME, SSD_VIEW_SSD, SSD_XFER_CONS, SSD_XFER_GAME,\n    SSD_XFER_SSD, SSD_BTN_TO_ID, SSD_NAMES, delete_console_game,\n    fetch_console_games, fetch_console_games_async, fetch_game_library,\n    get_consoles_from_setting, remove_console_game, remove_console_game_async,\n    set_game_disc_count, set_game_disc_count_async, show_console_menu,\n    show_game_menu, write_console_game,\n)'

new_imports = 'from bot import (\n    BTN_BACK, BTN_BACK_MAIN, BTN_GINST_DISC, BTN_GINST_HDD,\n    BTN_GINST_SSD, BTN_SSD_ADD, BTN_SSD_BLUE, BTN_SSD_GREY,\n    BTN_SSD_REMOVE, BTN_SSD_RETURN, BTN_SSD_T1, BTN_SSD_TRANSFER,\n    BTN_SSD_VIEW, BTN_SSD_MOVE_TO_CONSOLE, BTN_SSD_MOVE_TO_SSD,\n    DISC_SELECT, DISC_SET_QTY, SSD_ADD_GAME, SSD_ADD_SSD,\n    SSD_ADD_TYPE, SSD_DEL_GAME, SSD_DEL_SSD, SSD_MENU, SSD_RET_CONS,\n    SSD_RET_GAME, SSD_VIEW_SSD, SSD_XFER_CONS, SSD_XFER_GAME,\n    SSD_XFER_SSD, SSD_BTN_TO_ID, SSD_NAMES, delete_console_game,\n    fetch_console_games, fetch_console_games_async, fetch_game_library,\n    get_consoles_from_setting, remove_console_game, remove_console_game_async,\n    set_game_disc_count, set_game_disc_count_async, show_console_menu,\n    show_game_menu, write_console_game, SSD_MOVE_SSD, SSD_MOVE_GAME,\n    SSD_MOVE_CONS, SSD_MOVE_FROM_CONS, SSD_MOVE_FROM_GAME, SSD_MOVE_TO_SSD,\n)'

if old_imports in content:
    content = content.replace(old_imports, new_imports)
    print('ssd_disc: imports updated')
else:
    print('ssd_disc: import pattern NOT FOUND')

# Add move_console_game_async import
old_import_line = 'from bot.api_client import move_console_game_async'
if old_import_line not in content:
    # Add after the asyncio import
    content = content.replace(
        'import asyncio\nlogger',
        'import asyncio\nfrom bot.api_client import move_console_game_async\nlogger'
    )
    print('ssd_disc: move_console_game_async imported')
else:
    print('ssd_disc: import already present')

# Update show_ssd_menu to add Move buttons
old_menu_kb = '    kb = [\n        [BTN_SSD_VIEW],\n        [BTN_SSD_ADD,     BTN_SSD_REMOVE],\n        [BTN_SSD_TRANSFER, BTN_SSD_RETURN],\n        [BTN_BACK],\n    ]'
new_menu_kb = '    kb = [\n        [BTN_SSD_VIEW],\n        [BTN_SSD_ADD,     BTN_SSD_REMOVE],\n        [BTN_SSD_TRANSFER, BTN_SSD_RETURN],\n        [BTN_SSD_MOVE_TO_CONSOLE, BTN_SSD_MOVE_TO_SSD],\n        [BTN_BACK],\n    ]'
if old_menu_kb in content:
    content = content.replace(old_menu_kb, new_menu_kb)
    print('ssd_disc: move buttons added to menu')
else:
    print('ssd_disc: menu kb pattern NOT FOUND')

# Update step_ssd_menu to handle move buttons
old_step_menu = """    if text == BTN_SSD_RETURN:
        await update.message.reply_text(
            "\\u21a9\\ufe0f *Console \\u2192 SSD Return*\\n\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole"""

# The actual step_ssd_menu has:
# if text == BTN_SSD_RETURN:
#     await update.message.reply_text("↩️ *Console → SSD Return*\n\nConsole ရွေးပါ:", ...)
#     return SSD_RET_CONS
# return await show_ssd_menu(update, context)

# Let me find and replace the BTN_SSD_RETURN handling to add move buttons
old_return_block = """    if text == BTN_SSD_RETURN:
        await update.message.reply_text(
            "\\u21a9\\ufe0f *Console \\u2192 SSD Return*\\n\\nConsole \\u21a9\\ufe0f:\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole \\u21a9\\ufe0f *Console \\u2192 SSD Return*\\nConsole"""

# Actually, let me just search for the exact text in the file
print("Searching for BTN_SSD_RETURN block...")
# Find the line with BTN_SSD_RETURN
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'BTN_SSD_RETURN' in line and 'if text' in line:
        print(f'  Found at line {i+1}: {line.strip()[:80]}')
        # Print surrounding context
        for j in range(max(0,i-1), min(len(lines), i+15)):
            print(f'  {j+1}: {lines[j][:100]}')
        break
'''
    # Let me just search and replace with a simpler approach
    # Find the BTN_SSD_RETURN block and add move handling before the final return
    return_pattern = '    return await show_ssd_menu(update, context)'
    # This is the last line of step_ssd_menu - find its position
    idx = content.rfind(return_pattern)
    if idx != -1:
        # Find the position of "if text == BTN_SSD_RETURN:" before it
        ret_idx = content.rfind('if text == BTN_SSD_RETURN:', 0, idx)
        if ret_idx != -1:
            # Insert move handling before the SSD_RETURN block
            move_handling = '''    if text == BTN_SSD_MOVE_TO_CONSOLE:
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

'''
            content = content[:ret_idx] + move_handling + content[ret_idx:]
            print('ssd_disc: move handlers added to step_ssd_menu')
        else:
            print('ssd_disc: BTN_SSD_RETURN not found')
    else:
        print('ssd_disc: return pattern not found')
'''

with open('/root/psvibe-sales-bot/bot/handlers/ssd_disc.py', 'w') as f:
    f.write(content)
