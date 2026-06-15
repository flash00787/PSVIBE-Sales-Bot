# Fix api_get_bookings:
# 1. Add member_id filter
# 2. Batch console_type queries (N+1 fix)
# 3. Remove duplicate console_type resolution

with open('/root/psvibe_api_server/app.py', 'r') as f:
    lines = f.readlines()

# Find the function
func_start = -1
func_end = -1
for i, line in enumerate(lines):
    if 'async def api_get_bookings(status: str = ""' in line:
        func_start = i
    if func_start >= 0 and i > func_start and line.strip().startswith('@app.get("/api/search-bookings"'):
        func_end = i
        break

print(f'Function: lines {func_start+1} to {func_end}')

if func_start < 0 or func_end < 0:
    print('ERROR: function not found')
    exit(1)

# Extract function text
old_func = ''.join(lines[func_start:func_end])
print(f'Function length: {len(old_func)} chars')

# Build new function
new_func = '''@app.get("/api/bookings", response_model=GenericResponse, tags=["Bookings"], summary="List bookings by status [MySQL]")
async def api_get_bookings(status: str = "", member_id: str = Query(""), auth=Depends(verify_api_key)):
    """List bookings with optional status and member_id filters."""
    try:
        sql = "SELECT id, console_id, member_id, booking_date, start_time, end_time, status, staff_name, notes, telegram_chat_id, duration_mins, phone, game_name FROM console_booking"
        where_clauses = []
        params = []
        if status:
            where_clauses.append("status=%s")
            params.append(status)
        if member_id:
            where_clauses.append("member_id=%s")
            params.append(member_id)
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " ORDER BY booking_date DESC, start_time DESC"
        rows = _mysql_query(sql, tuple(params)) if params else _mysql_query(sql)
        if not rows:
            return ok({"bookings": []})
        # Batch resolve console_types (N+1 fix)
        all_cids = set()
        for r in rows:
            _cid = r.get("console_id", "")
            if _cid and not any(t in _cid.lower() for t in ("ps5", "ps4", "ps3", "xbox", "switch", "pc")):
                all_cids.add(_cid)
        ctype_map = {}
        if all_cids:
            cid_list = sorted(all_cids)
            placeholders = ",".join("%s" for _ in cid_list)
            try:
                crows = _mysql_query(f"SELECT console_id, console_type FROM console_status WHERE console_id IN ({placeholders})", cid_list)
                for cr in crows or []:
                    ctype_map[cr.get("console_id")] = cr.get("console_type", cr.get("console_id"))
            except Exception:
                pass
        from datetime import datetime as _dt
        normalized = []
        for r in rows:
            _cid = r.get("console_id", "")
            _ctype = ctype_map.get(_cid, _cid)
            start = r.get("start_time")
            time_slot = ""
            if start:
                try:
                    start_dt = _dt.fromisoformat(start) if isinstance(start, str) else start
                    time_slot = start_dt.strftime("%H:%M")
                except Exception:
                    time_slot = str(start)[:5] if start else ""
            bd = r.get("booking_date")
            bd_str = ""
            if bd:
                try:
                    bd_o = _dt.fromisoformat(bd) if isinstance(bd, str) else bd
                    bd_str = bd_o.strftime("%Y-%m-%d")
                except Exception:
                    bd_str = str(bd)[:10]
            normalized.append({
                "id": r.get("id",""),
                "customerName": r.get("staff_name",""),
                "phone": r.get("phone","") or r.get("telegram_chat_id",""),
                "date": bd_str,
                "timeSlot": time_slot,
                "consoleType": _ctype,
                "durationMins": r.get("duration_mins",60),
                "gameName": r.get("game_name",""),
                "console_id": r.get("console_id",""),
                "consoleId": r.get("console_id",""),
                "member_id": r.get("member_id",""),
                "telegram_chat_id": r.get("telegram_chat_id",""),
                "telegramChatId": r.get("telegram_chat_id",""),
                "status": r.get("status","")
            })
        return ok({"bookings": normalized})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

'''

lines[func_start:func_end] = new_func.splitlines(keepends=True)

with open('/root/psvibe_api_server/app.py', 'w') as f:
    f.writelines(lines)

import ast
ast.parse(open('/root/psvibe_api_server/app.py').read())
print('SYNTAX OK')
