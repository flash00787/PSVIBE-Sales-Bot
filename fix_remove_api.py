#!/usr/bin/env python3
"""Fix remove_console_game API DELETE to use REPLACE for space normalization."""
FILE = "/root/psvibe_api_server/app.py"
with open(FILE) as f:
    code = f.read()

old = ('_cid = req.get("console_id","").replace(" ", "")\n'
       '        _mysql_exec(\n'
       '            "DELETE FROM console_games WHERE console_id=%s AND game_title=%s",\n'
       '            (_cid, req.get("game_title","")))')

new = ('_cid = req.get("console_id","").replace(" ", "")\n'
       '        _mysql_exec(\n'
       '            "DELETE FROM console_games WHERE REPLACE(console_id, \' \', \'\')=%s AND game_title=%s",\n'
       '            (_cid, req.get("game_title","")))')

if old in code:
    code = code.replace(old, new, 1)
    with open(FILE, "w") as f:
        f.write(code)
    compile(code, FILE, "exec")
    print("OK")
else:
    print("NOT FOUND")
