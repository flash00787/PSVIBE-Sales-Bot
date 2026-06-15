import ast

with open('/root/psvibe_api_server/app.py', 'r') as f:
    c = f.read()

# Optimize api_get_bookings:
# 1. Add member_id filter support
# 2. Fix N+1 console_type query
# 3. Reduce to single query for console_type

old_func_start = '''async def api_get_bookings(status: str = "", auth=Depends(verify_api_key)):
    try:
        if status:
            rows = _mysql_query("SELECT id, console_id, member_id, booking_date, start_time, end_time, status, staff_name, notes, telegram_chat_id, duration_mins, phone, game_name FROM console_booking WHERE status=%s ORDER BY booking_date DESC, start_time DESC", (status,))
        else:
            rows = _mysql_query("SELECT id, console_id, member_id, booking_date, start_time, end_time, status, staff_name, notes, telegram_chat_id, duration_mins, phone, game_name FROM console_booking ORDER BY booking_date DESC, start_time DESC")
        from datetime import datetime as _dt
        normalized = []
        for r in rows:
            # Derive consoleType from console_id
            _cid = r.get("console_id", "")
            _ctype = _cid
            if _cid and not any(t in _cid.lower() for t in ("ps5", "ps4", "ps3", "xbox", "switch", "pc")):
                try:
                    _crows = _mysql_query("SELECT console_type FROM console_status WHERE console_id=%s LIMIT 1", (_cid,))
                    if _crows and _crows[0].get("console_type"):
                        _ctype = _crows[0]["console_type"]
                except Exception:
                    pass
            start = r.get("start_time")
            time_slot = ""
            if start:
                try:
                    start_dt = _dt.fromisoformat(start) if isinstance(start, str) else start
                    time_slot = start_dt.strftime("%H:%M")
                except:
                    time_slot = str(start)[:5] if start else ""
            bd = r.get("booking_date")
            if bd:
                try:
                    bd_o = _dt.fromisoformat(bd) if isinstance(bd, str) else bd
                    bd_str = bd_o.strftime("%Y-%m-%d")
                except:
                    bd_str = str(bd)[:10]
            else:
                bd_str = ""
            # Derive consoleType from console_id: if console_id is a specific ID (C-01, etc),
            # try to match against console_status; otherwise use console_id as the type name
            _cid = r.get("console_id", "")
            _ctype = _cid  # default: use console_id as display type (works for "PS5", "PS5 Pro")
            # If console_id looks like a specific console ID (e.g., "C - 01", "C-01"),
            # try to resolve to a type name from console_status
            if _cid and not any(t in _cid.lower() for t in ("ps5", "ps4", "ps3", "xbox", "switch", "pc")):
                try:'''

new_func_start = '''async def api_get_bookings(status: str = "", member_id: str = Query(""), auth=Depends(verify_api_key)):
    try:
        sql = "SELECT id, console_id, member_id, booking_date, start_time, end_time, status, staff_name, notes, telegram_chat_id, duration_mins, phone, game_name FROM console_booking"
        where = []
        params = []
        if status:
            where.append("status=%s")
            params.append(status)
        if member_id:
            where.append("member_id=%s")
            params.append(member_id)
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY booking_date DESC, start_time DESC"
        rows = _mysql_query(sql, tuple(params)) if params else _mysql_query(sql)
        
        if not rows:
            from datetime import datetime as _dt
            return {"ok": True, "data": []}
        
        # Batch resolve console types (N+1 fix)
        console_ids = set()
        for r in rows:
            _cid = r.get("console_id", "")
            if _cid and not any(t in _cid.lower() for t in ("ps5", "ps4", "ps3", "xbox", "switch", "pc")):
                console_ids.add(_cid)
        _ctype_map = {}
        if console_ids:
            _id_list = sorted(console_ids)
            _placeholders = ",".join("%s" for _ in _id_list)
            try:
                _crows = _mysql_query(f"SELECT console_id, console_type FROM console_status WHERE console_id IN ({_placeholders})", _id_list)
                for _cr in _crows or []:
                    _ctype_map[_cr.get("console_id")] = _cr.get("console_type", _cr.get("console_id"))
            except Exception:
                pass
        
        from datetime import datetime as _dt
        normalized = []
        for r in rows:
            _cid = r.get("console_id", "")
            _ctype = _ctype_map.get(_cid, _cid)
            start = r.get("start_time")
            time_slot = ""
            if start:
                try:
                    start_dt = _dt.fromisoformat(start) if isinstance(start, str) else start
                    time_slot = start_dt.strftime("%H:%M")
                except:
                    time_slot = str(start)[:5] if start else ""
            bd = r.get("booking_date")
            if bd:
                try:
                    bd_o = _dt.fromisoformat(bd) if isinstance(bd, str) else bd
                    bd_str = bd_o.strftime("%Y-%m-%d")
                except:
                    bd_str = str(bd)[:10]
            else:
                bd_str = ""
            _cid = r.get("console_id", "")
            _ctype = _ctype_map.get(_cid, _cid)
            if _cid and not any(t in _cid.lower() for t in ("ps5", "ps4", "ps3", "xbox", "switch", "pc")):'''

c = c.replace(old_func_start, new_func_start)

# Also need to import Query from fastapi
# Check if it's already imported
if 'from fastapi import Query' not in c:
    c = c.replace('from fastapi import APIRouter', 'from fastapi import APIRouter, Query')

with open('/root/psvibe_api_server/app.py', 'w') as f:
    f.write(c)

ast.parse(c)
print('FIXED AND SYNTAX OK')
