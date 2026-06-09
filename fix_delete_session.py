#!/usr/bin/env python3
"""Fix delete_session_game API to normalize console_id spaces."""
FILE = "/root/psvibe_api_server/app.py"
with open(FILE) as f:
    code = f.read()

old = (
    '@app.delete("/api/delete_session_game/{console_id}")\n'
    'async def api_delete_session_game(console_id: str):\n'
    '    try:\n'
    '        _mysql_exec(\n'
    '            "DELETE FROM console_games WHERE console_id=%s AND status=\'Session\'",\n'
    '            (console_id,))\n'
    '        return ok({"console_id": console_id, "deleted": True})\n'
    '    except Exception as e:\n'
    '        return error_response(message=str(e))'
)

new = (
    '@app.delete("/api/delete_session_game/{console_id}")\n'
    'async def api_delete_session_game(console_id: str):\n'
    '    try:\n'
    '        _cid = console_id.replace(" ", "")\n'
    '        _mysql_exec(\n'
    '            "DELETE FROM console_games WHERE REPLACE(console_id, \' \', \'\')=%s AND status=\'Session\'",\n'
    '            (_cid,))\n'
    '        return ok({"console_id": console_id, "deleted": True})\n'
    '    except Exception as e:\n'
    '        return error_response(message=str(e))'
)

if old in code:
    code = code.replace(old, new, 1)
    with open(FILE, "w") as f:
        f.write(code)
    compile(code, FILE, "exec")
    print("OK")
else:
    print("NOT FOUND")
    idx = code.find("delete_session_game")
    if idx >= 0:
        print("Found at", idx)
        print(code[idx:idx+200])
