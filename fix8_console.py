#!/usr/bin/env python3
"""Fix 8: Add BTN_SSD_MANAGE to console menu and handle it."""
path = '/root/psvibe-sales-bot/bot/handlers/console.py'
content = open(path).read()

# 1. Add BTN_SSD_MANAGE to imports
old_import = '''from bot import (
    BTN_BACK, BTN_BACK_MAIN, BTN_CANCEL, BTN_CHANGE_GAME,
    BTN_CONSOLE_INSTALL, BTN_END_SESSION, BTN_GAME_LIB_MENU, BTN_START_SESSION,
    BTN_STATUS_BOARD, CONSOLE_MENU, END_SESSION_SELECT, _delete_session_game,
    _replit_get, _replit_get_async, add_console_game, _replit_post_async,
    calc_duration, cmd_cancel, end_booking, end_booking_async, fetch_console_games,
    fetch_console_status, get_games_on_console, get_games_on_console_async, now_mmt,
    show_console_menu, show_game_menu, show_main_menu,
    prompt_book_console,
)'''

new_import = '''from bot import (
    BTN_BACK, BTN_BACK_MAIN, BTN_CANCEL, BTN_CHANGE_GAME,
    BTN_CONSOLE_INSTALL, BTN_END_SESSION, BTN_GAME_LIB_MENU, BTN_START_SESSION,
    BTN_SSD_MANAGE, BTN_STATUS_BOARD, CONSOLE_MENU, END_SESSION_SELECT,
    _delete_session_game,
    _replit_get, _replit_get_async, add_console_game, _replit_post_async,
    calc_duration, cmd_cancel, end_booking, end_booking_async, fetch_console_games,
    fetch_console_status, get_games_on_console, get_games_on_console_async, now_mmt,
    show_console_menu, show_game_menu, show_main_menu,
    prompt_book_console,
)'''

if old_import in content:
    content = content.replace(old_import, new_import)
    print('FIX 8a DONE: Added BTN_SSD_MANAGE to imports')
else:
    print('FIX 8a: Import pattern not found')
    idx = content.find('from bot import')
    if idx >= 0:
        print(f'  Found at position {idx}:')
        print(content[idx:idx+600])

# 2. Add BTN_SSD_MANAGE to the keyboard
old_kb = '''    kb = [
        [BTN_START_SESSION,  BTN_END_SESSION],
        [BTN_STATUS_BOARD,   BTN_GAME_LIB_MENU],
        [BTN_CONSOLE_INSTALL],
        [BTN_BACK_MAIN],
    ]'''

new_kb = '''    kb = [
        [BTN_START_SESSION,  BTN_END_SESSION],
        [BTN_STATUS_BOARD,   BTN_GAME_LIB_MENU],
        [BTN_CONSOLE_INSTALL, BTN_SSD_MANAGE],
        [BTN_BACK_MAIN],
    ]'''

if old_kb in content:
    content = content.replace(old_kb, new_kb)
    print('FIX 8b DONE: Added BTN_SSD_MANAGE to console menu keyboard')
else:
    print('FIX 8b: Keyboard pattern not found')
    idx = content.find('kb = [')
    if idx >= 0:
        print(f'  Found at position {idx}:')
        print(content[idx:idx+300])

# 3. Add handler for BTN_SSD_MANAGE in step_console_menu
old_step = '''    if choice == BTN_CONSOLE_INSTALL:
        return await show_ginst_menu(update, context)
    return await show_console_menu(update, context)'''

new_step = '''    if choice == BTN_CONSOLE_INSTALL:
        return await show_ginst_menu(update, context)
    if choice == BTN_SSD_MANAGE:
        from bot.handlers.ssd_disc import show_ssd_menu
        return await show_ssd_menu(update, context)
    return await show_console_menu(update, context)'''

if old_step in content:
    content = content.replace(old_step, new_step)
    print('FIX 8c DONE: Added BTN_SSD_MANAGE handler in step_console_menu')
else:
    print('FIX 8c: Step handler pattern not found')
    idx = content.find('if choice == BTN_CONSOLE_INSTALL')
    if idx >= 0:
        print(f'  Found at position {idx}:')
        print(content[idx:idx+200])

open(path, 'w').write(content)
print('console.py saved')
