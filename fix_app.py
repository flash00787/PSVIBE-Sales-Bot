with open('/root/psvibe_api_server/app.py') as f:
    content = f.read()

# 3a: Fix status_val from "false" to "Not Installed"
old_status = 'status_val = "Installed" if installed else "false"'
new_status = 'status_val = "Installed" if installed else "Not Installed"'
if old_status in content:
    content = content.replace(old_status, new_status)
    print('3a: status_val fixed')
else:
    print('3a: status_val pattern NOT FOUND')

# 3a: Add games_library.final_status update before the return ok in api_update_game_library_install
# Find the return ok line
old_return_line = '        return ok({"game_title": game_title, "console_id": console_id, "installed": installed})'
if old_return_line in content:
    final_status_block = """        # Update games_library.final_status based on console_games
        has_installed = _mysql_query_one(
            "SELECT COUNT(*) as cnt FROM console_games WHERE game_title=%s AND status='Installed'",
            (game_title,))
        new_final = "Installed" if (has_installed and has_installed.get("cnt", 0) > 0) else "Not Installed"
        _mysql_exec("UPDATE games_library SET final_status=%s WHERE game_title=%s", (new_final, game_title))
        
"""
    content = content.replace(old_return_line, final_status_block + old_return_line)
    print('3a: final_status update added')
else:
    print('3a: return ok line not found')

# 3b: Add move_console_game endpoint after api_delete_session_game
delete_func = '''@app.delete("/api/delete_session_game/{console_id}")
async def api_delete_session_game(console_id: str):
    try:
        _mysql_exec(
            "DELETE FROM console_games WHERE console_id=%s AND status='Session'",
            (console_id,))
        return ok({"console_id": console_id, "deleted": True})
    except Exception as e:
        return error_response(message=str(e))'''

if delete_func in content:
    move_endpoint = '''
@app.post("/api/move_console_game", response_model=GenericResponse, tags=["Games"], summary="Move game between console/SSD [MySQL]")
async def api_move_console_game(req: dict, auth=Depends(verify_api_key)):
    try:
        game_title = req.get("game_title", "").strip()
        from_console = req.get("from_console", "").strip()
        to_console = req.get("to_console", "").strip()
        if not game_title or not from_console or not to_console:
            return error_response(message="game_title, from_console, to_console required")
        if from_console == to_console:
            return error_response(message="source and destination must be different")
        _mysql_exec("DELETE FROM console_games WHERE console_id=%s AND game_title=%s", (from_console, game_title))
        _mysql_exec(
            "INSERT INTO console_games (console_id, console_name, game_id, game_title, status, install_type, slot_position) VALUES (%s, %s, %s, %s, 'Installed', 'Moved', 0)",
            (to_console, to_console, game_title, game_title))
        has_installed = _mysql_query_one(
            "SELECT COUNT(*) as cnt FROM console_games WHERE game_title=%s AND status='Installed'",
            (game_title,))
        new_final = "Installed" if (has_installed and has_installed.get("cnt", 0) > 0) else "Not Installed"
        _mysql_exec("UPDATE games_library SET final_status=%s WHERE game_title=%s", (new_final, game_title))
        return ok({"game_title": game_title, "from": from_console, "to": to_console, "moved": True})
    except Exception as e:
        return error_response(message=str(e))
'''
    content = content.replace(delete_func, delete_func + move_endpoint)
    print('3b: move_console_game endpoint added')
else:
    print('3b: delete_session_game pattern NOT FOUND')

# 3c: Fix api_add_console_game - ensure status is "Installed" and add install_type column
old_add = '''        _mysql_exec(
            "INSERT INTO console_games (console_id, console_name, game_id, game_title, genre, status, slot_position) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (req.get("console_id",""), req.get("console_name") or req.get("console_id",""), req.get("game_id") or req.get("game_title",""),
             req.get("game_title",""), req.get("genre",""), req.get("status") or req.get("install_type","Installed"),
             req.get("slot_position",1)))'''
new_add = '''        _mysql_exec(
            "INSERT INTO console_games (console_id, console_name, game_id, game_title, genre, status, install_type, slot_position) VALUES (%s, %s, %s, %s, %s, 'Installed', %s, %s)",
            (req.get("console_id",""), req.get("console_name") or req.get("console_id",""), req.get("game_id") or req.get("game_title",""),
             req.get("game_title",""), req.get("genre",""), req.get("install_type",""),
             req.get("slot_position",1)))'''
if old_add in content:
    content = content.replace(old_add, new_add)
    print('3c: api_add_console_game fixed')
else:
    print('3c: api_add_console_game pattern NOT FOUND')

with open('/root/psvibe_api_server/app.py', 'w') as f:
    f.write(content)
print('app.py updated successfully')
