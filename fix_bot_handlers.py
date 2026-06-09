#!/usr/bin/env python3
"""Fix game library functions in sales bot to use API instead of GSheet."""

# ----- Fix 1: games.py import -----
GAMES_PY = '/root/psvibe-sales-bot/bot/handlers/games.py'
INIT_PY = '/root/psvibe-sales-bot/bot/__init__.py'

# ===== GAMES.PY FIXES =====
with open(GAMES_PY, 'r') as f:
    content = f.read()

# Fix 1a: Add _replit_post, _replit_put, _replit_delete to imports
old_import = "    fetch_console_games_async, fetch_games_async, get_game_lib_sh, show_game_menu,"
new_import = "    _replit_delete, _replit_post, _replit_put,\n    fetch_console_games_async, fetch_games_async, get_game_lib_sh, show_game_menu,"
content = content.replace(old_import, new_import)

# Fix 1b: Replace step_game_add_status GSheet write with API call
old_add = """    try:
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
        _bot_mod._GAME_TS = 0"""

new_add = """    try:
        payload = {"title": title, "solo_multi": solo_multi, "genre": genre, "copies": copies}
        result = _replit_post("add_game", payload)
        if result is None or not result.get("success"):
            raise Exception(result.get("error", "API call failed") if result else "API unavailable")
        # Invalidate cache
        import bot as _bot_mod
        _bot_mod._GAME_ROWS = []
        _bot_mod._GAME_TS = 0"""

if old_add in content:
    content = content.replace(old_add, new_add)
    print("Fixed: step_game_add_status")
else:
    print("WARNING: step_game_add_status pattern not found")

# Fix 1c: Replace step_game_edit_value GSheet write with API call
old_edit = """    try:
        sh = get_game_lib_sh()
        sh.update_cell(row_num, 21, meta)   # col U = index 21
        # Invalidate cache
        import bot as _bot_mod
        _bot_mod._GAME_ROWS = []
        _bot_mod._GAME_TS = 0"""

new_edit = """    try:
        payload = {"title": title, "field": field, "value": text}
        result = _replit_put("edit_game", payload)
        if result is None or not result.get("success"):
            raise Exception(result.get("error", "API call failed") if result else "API unavailable")
        # Invalidate cache
        import bot as _bot_mod
        _bot_mod._GAME_ROWS = []
        _bot_mod._GAME_TS = 0"""

if old_edit in content:
    content = content.replace(old_edit, new_edit)
    print("Fixed: step_game_edit_value")
else:
    print("WARNING: step_game_edit_value pattern not found")

# Fix 1d: Replace step_game_del_select GSheet delete with API call
old_del = """    try:
        sh = get_game_lib_sh()
        sh.delete_rows(target["row"])"""

new_del = """    try:
        result = _replit_delete(f"delete_game/{game_name}")
        if result is None or not result.get("success"):
            raise Exception(result.get("error", "API call failed") if result else "API unavailable")"""

if old_del in content:
    content = content.replace(old_del, new_del)
    print("Fixed: step_game_del_select")
else:
    print("WARNING: step_game_del_select pattern not found")

# Now remove the special "protected" error handling since we no longer use GSheet
# The except block after delete had special handling for GSheet protection errors
old_except_protected = """    except Exception as e:
        err_str = str(e)
        if "protected" in err_str.lower() or "400" in err_str:
            await update.message.reply_text(
                f"⚠️ <b>Game Library sheet protected</b> ဖြစ်သောကြောင့်\\n"
                f"bot မှ row ဖျက်ခြင်း မပြုနိုင်ပါ\\n\\n"
                f"📋 Google Sheet ကို directly ဝင်ပြီး\\n"
                f"<b>\\"{game_name}\\"</b> row ကို ဖျက်ပေးပါ",
                parse_mode="HTML",
            )
        else:
            await update.message.reply_text(f"❌ ဖျက်မရပါ: {err_str}")"""

new_except = "$REPLACE$"  # We'll handle this differently

if old_except_protected in content:
    content = content.replace(old_except_protected, new_except)
    print("Removed: GSheet protected error handling")
else:
    print("WARNING: Protected error handling pattern not found")

with open(GAMES_PY, 'w') as f:
    f.write(content)

print(f"Written games.py ({len(content.split(chr(10)))} lines)")

# ===== __INIT__.PY FIX: _delete_session_game =====
with open(INIT_PY, 'r') as f:
    init_content = f.read()

old_session_del = """def _delete_session_game(console_id: str) -> None:
    \"""Remove any 'Session' type entry for a console from Console_Games.\"""
    try:
        sh   = get_console_games_sh()
        rows = sh.get("A:C")  # OPT: range-restricted read (A=console_id, C=install_type)
        for i, row in enumerate(rows[1:], start=2):
            if (len(row) >= 3
                    and row[0].strip().upper() == console_id.strip().upper()
                    and row[2].strip() == "Session"):
                sh.delete_rows(i)
                # Invalidate cache
                global _CGAME_ROWS, _CGAME_TS
                _CGAME_TS = 0
                return
    except Exception as e:
        logging.exception("_delete_session_game: %s", e)"""

new_session_del = """def _delete_session_game(console_id: str) -> None:
    \"""Remove any 'Session' type entry for a console via API.\"""
    try:
        result = _replit_delete(f"delete_session_game/{console_id}")
        if result and result.get("success"):
            global _CGAME_ROWS, _CGAME_TS
            _CGAME_TS = 0
    except Exception as e:
        logging.exception("_delete_session_game: %s", e)"""

if old_session_del in init_content:
    init_content = init_content.replace(old_session_del, new_session_del)
    print("Fixed: _delete_session_game in __init__.py")
else:
    print("WARNING: _delete_session_game pattern not found")

with open(INIT_PY, 'w') as f:
    f.write(init_content)

print(f"Written __init__.py ({len(init_content.split(chr(10)))} lines)")

# Validate both files with Python syntax check
import py_compile
py_compile.compile(GAMES_PY, doraise=True)
print("games.py syntax OK")
py_compile.compile(INIT_PY, doraise=True)
print("__init__.py syntax OK")
print("ALL DONE")
