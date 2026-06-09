#!/usr/bin/env python3
"""Fix move_console_game API to normalize console_id in SQL (space handling)."""
FILE = "/root/psvibe_api_server/app.py"

with open(FILE) as f:
    code = f.read()

old = (
    '        _mysql_exec("DELETE FROM console_games WHERE console_id=%s AND game_title=%s", (from_console, game_title))\n'
    '        _mysql_exec("DELETE FROM console_games WHERE console_id=%s AND game_title=%s AND install_type NOT IN (\'Session\')", (to_console, game_title))\n'
    '        _mysql_exec(\n'
    '            "INSERT INTO console_games (console_id, console_name, game_id, game_title, status, install_type, slot_position) VALUES (%s, %s, %s, %s, \'Installed\', \'Moved\', 0)",\n'
    '            (to_console, to_console, game_title, game_title))\n'
    '        has_installed = _mysql_query_one('
)

new = (
    '        # Normalize console_id by removing spaces for matching\n'
    '        norm = lambda cid: cid.replace(" ", "")\n'
    '        _mysql_exec("DELETE FROM console_games WHERE REPLACE(console_id, \' \', \'\')=%s AND game_title=%s", (norm(from_console), game_title))\n'
    '        _mysql_exec("DELETE FROM console_games WHERE REPLACE(console_id, \' \', \'\')=%s AND game_title=%s AND install_type NOT IN (\'Session\')", (norm(to_console), game_title))\n'
    '        _mysql_exec(\n'
    '            "INSERT INTO console_games (console_id, console_name, game_id, game_title, status, install_type, slot_position) VALUES (%s, %s, %s, %s, \'Installed\', \'Moved\', 0)",\n'
    '            (norm(to_console), norm(to_console), game_title, game_title))\n'
    '        has_installed = _mysql_query_one('
)

if old in code:
    code = code.replace(old, new, 1)
    with open(FILE, "w") as f:
        f.write(code)
    compile(code, FILE, "exec")
    print("OK")
else:
    print("NOT FOUND")
    idx = code.find("DELETE FROM console_games WHERE console_id")
    if idx >= 0:
        print("Found at", idx)
        print(code[idx:idx+400])
