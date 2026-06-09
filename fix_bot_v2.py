#!/usr/bin/env python3
"""Fix game library functions in sales bot to use API instead of GSheet."""

import py_compile

GAMES_PY = '/root/psvibe-sales-bot/bot/handlers/games.py'
INIT_PY = '/root/psvibe-sales-bot/bot/__init__.py'

# ===== GAMES.PY FIXES =====
with open(GAMES_PY, 'r') as f:
    content = f.read()

# Fix 1: Add _replit_post, _replit_put, _replit_delete to imports
old_import = "    fetch_console_games_async, fetch_games_async, get_game_lib_sh, show_game_menu,"
new_import = "    _replit_delete, _replit_post, _replit_put,\n    fetch_console_games_async, fetch_games_async, get_game_lib_sh, show_game_menu,"
content = content.replace(old_import, new_import)
print("Added API imports")

# Fix 2: Replace step_game_add_status GSheet write with API call
old_add = '    try:\n        sh = get_game_lib_sh()\n        # Determine next row number and next empty row\n        all_rows = sh.get_all_values()\n        existing_nos = [int(r[0]) for r in all_rows[1:] if r and r[0].strip().isdigit()]\n        next_no   = max(existing_nos, default=0) + 1\n        next_row  = len(all_rows) + 1  # append after last row\n        # Build full row (20 cols: A-T)'

# Try broader match - find the block from "try:" to "Invalidate cache" in add function
# Let me use line-by-line approach instead
lines = content.split('\n')
line_count_before = len(lines)

# Quick approach: find and replace specific patterns inline
# Pattern for add: line containing "sh = get_game_lib_sh()" followed by GSheet code
for i, line in enumerate(lines):
    if 'sh = get_game_lib_sh()' in line and i > 220 and i < 270:
        # Found in step_game_add_status. Find the try block for this section
        # Actually, let me check what follows
        if 'all_rows = sh.get_all_values()' in lines[i+1]:
            print(f"Found add_game GSheet at line {i+1}")
            # Find where the try block starts
            try_start = i
            for j in range(i, -1, -1):
                if lines[j].strip() == 'try:':
                    try_start = j
                    break
            # Find where _GAME_TS = 0 line ends (end of try block)
            try_end = i
            for j in range(i, min(i+30, len(lines))):
                if '_GAME_TS = 0' in lines[j]:
                    try_end = j
                    break
            
            if try_end > try_start:
                indent = '    '  # 4 spaces
                new_block = [
                    indent + 'try:',
                    indent + '    payload = {"title": title, "solo_multi": solo_multi, "genre": genre, "copies": copies}',
                    indent + '    result = _replit_post("add_game", payload)',
                    indent + '    if result is None or not result.get("success"):',
                    indent + '        raise Exception(result.get("error", "API call failed") if result else "API unavailable")',
                    indent + '    # Invalidate cache',
                    indent + '    import bot as _bot_mod',
                    indent + '    _bot_mod._GAME_ROWS = []',
                    indent + '    _bot_mod._GAME_TS = 0',
                ]
                lines[try_start:try_end+1] = new_block
                print(f"Replaced lines {try_start+1}-{try_end+1}")
            break

# Pattern for edit: find "sh.update_cell(row_num" around line 338-390
for i, line in enumerate(lines):
    if 'sh.update_cell(row_num, 21, meta)' in line:
        print(f"Found edit_game GSheet at line {i+1}")
        try_start = i - 1  # The "sh = get_game_lib_sh()" line
        try_end = i + 5    # Find _GAME_TS = 0
        for j in range(i, min(i+10, len(lines))):
            if '_GAME_TS = 0' in lines[j]:
                try_end = j
                break
        
        indent = '    '
        new_block = [
            indent + '    payload = {"title": title, "field": field, "value": text}',
            indent + '    result = _replit_put("edit_game", payload)',
            indent + '    if result is None or not result.get("success"):',
            indent + '        raise Exception(result.get("error", "API call failed") if result else "API unavailable")',
            indent + '    # Invalidate cache',
            indent + '    import bot as _bot_mod',
            indent + '    _bot_mod._GAME_ROWS = []',
            indent + '    _bot_mod._GAME_TS = 0',
        ]
        lines[try_start+1:try_end+1] = new_block
        print(f"Replaced lines {try_start+2}-{try_end+1}")
        break

# Pattern for delete: find "sh.delete_rows(target["row"])" 
for i, line in enumerate(lines):
    if 'sh.delete_rows(target["row"])' in line:
        print(f"Found delete_game GSheet at line {i+1}")
        # Replace the try-except block for delete
        # The line above should be "sh = get_game_lib_sh()"
        try_start = i - 1
        # Replace just these 2 lines
        indent = '        '
        lines[i-1] = indent + 'result = _replit_delete(f"delete_game/{game_name}")'
        lines[i] = indent + 'if result is None or not result.get("success"):'
        lines.insert(i+1, indent + '    raise Exception(result.get("error", "API call failed") if result else "API unavailable")')
        print(f"Replaced lines at {i+1}")
        break

# Remove the GSheet-specific "protected" error handling
# Replace the entire except block for delete
for i, line in enumerate(lines):
    if 'if "protected" in err_str.lower() or "400" in err_str:' in line:
        print(f"Found protected error handler at line {i+1}")
        # Find end of this if-else block that's in the except
        # This spans multiple lines. Let me find the end
        end = i
        for j in range(i, min(i+20, len(lines))):
            if 'return await show_game_menu(update, context)' in lines[j] and j > i+5:
                end = j
                break
        # Remove from line i to end
        # Replace with simple error message
        indent = '        '
        lines[i:end+1] = [
            indent + 'await update.message.reply_text(f"❌ ဖျက်မရပါ: {e}")'
        ]
        print(f"Removed protected handler lines {i+1}-{end+1}")
        break

content = '\n'.join(lines)

with open(GAMES_PY, 'w') as f:
    f.write(content)
print(f"Written games.py ({len(lines)} lines)")
py_compile.compile(GAMES_PY, doraise=True)
print("games.py syntax OK")

# ===== __INIT__.PY FIX: _delete_session_game =====
with open(INIT_PY, 'r') as f:
    init_lines = f.readlines()

# Find _delete_session_game and replace
in_func = False
func_start = -1
func_end = -1

for i, line in enumerate(init_lines):
    if line.strip() == 'def _delete_session_game(console_id: str) -> None:':
        func_start = i
        in_func = True
        continue
    if in_func:
        # Check if we've reached the end of the function (next def or significant dedent)
        if (line.strip().startswith('def ') and not line.strip().startswith('def _delete')) or \
           (line.strip().startswith('SSD_NAMES') and func_start > 0):
            func_end = i
            break

if func_start >= 0 and func_end > func_start:
    new_func = '''def _delete_session_game(console_id: str) -> None:
    """Remove any 'Session' type entry for a console via API."""
    try:
        result = _replit_delete(f"delete_session_game/{console_id}")
        if result and result.get("success"):
            global _CGAME_ROWS, _CGAME_TS
            _CGAME_TS = 0
    except Exception as e:
        logging.exception("_delete_session_game: %s", e)

'''
    init_lines[func_start:func_end] = new_func.splitlines(True)
    print(f"Replaced _delete_session_game at lines {func_start+1}-{func_end}")

with open(INIT_PY, 'w') as f:
    f.writelines(init_lines)
print(f"Written __init__.py ({len(init_lines)} lines)")
py_compile.compile(INIT_PY, doraise=True)
print("__init__.py syntax OK")

print("\n=== ALL BOT FIXES APPLIED ===")
