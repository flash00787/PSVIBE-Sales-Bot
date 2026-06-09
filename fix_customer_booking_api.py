#!/usr/bin/env python3
"""Fix Customer Booking: missing API endpoints + broken sheets/consoles call."""

# ===== FIX 1: API Server — Add PATCH + GET booking endpoints =====
APP_FILE = "/root/psvibe_api_server/app.py"
with open(APP_FILE) as f:
    code = f.read()

insert_marker = "#  GET /api/bookings - list bookings by status"

patch_endpoint = '''

# ── PATCH /api/bookings/{booking_id}/status ──
@app.patch("/api/bookings/{booking_id}/status", response_model=GenericResponse, tags=["Bookings"], summary="Update booking status (approve/reject) [MySQL]")
async def api_update_booking_status(booking_id: int, req: dict, auth=Depends(verify_api_key)):
    """Update a booking's status and optionally assign a console."""
    try:
        status = req.get("status", "")
        if status not in ("pending", "confirmed", "rejected", "pending_check_in", "Active", "cancelled", "Done"):
            return error_response(message=f"Invalid status: {status}")
        _mysql_exec(
            "UPDATE console_booking SET status=%s, staff_name=COALESCE(%s, staff_name), notes=COALESCE(%s, notes) WHERE id=%s",
            (status, req.get("staffName", ""), req.get("staffNote", ""), booking_id))
        if req.get("consoleId"):
            _mysql_exec("UPDATE console_booking SET console_id=%s WHERE id=%s", (req["consoleId"], booking_id))
        invalidate_cache("bookings")
        return ok({"booking_id": booking_id, "status": status})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /api/bookings/{booking_id} ──
@app.get("/api/bookings/{booking_id}", response_model=GenericResponse, tags=["Bookings"], summary="Get single booking by ID [MySQL]")
async def api_get_booking(booking_id: int, auth=Depends(verify_api_key)):
    """Fetch a single booking's full details."""
    try:
        row = _mysql_query_one(
            "SELECT id, console_id, member_id, booking_date, start_time, end_time, status, staff_name, notes, telegram_chat_id, duration_mins, phone, game_name FROM console_booking WHERE id=%s",
            (booking_id,))
        if not row:
            raise HTTPException(status_code=404, detail="Booking not found")
        start = row.get("start_time")
        time_slot = ""
        if start:
            try:
                from datetime import datetime as _dt
                start_dt = _dt.fromisoformat(start) if isinstance(start, str) else start
                time_slot = start_dt.strftime("%H:%M")
            except:
                time_slot = str(start)[:5] if start else ""
        bd = row.get("booking_date")
        bd_str = str(bd)[:10] if bd else ""
        _cid = row.get("console_id", "")
        _ctype = _cid
        if _cid and not any(t in _cid.lower() for t in ("ps5", "ps4", "ps3", "xbox", "switch", "pc")):
            try:
                _crows = _mysql_query("SELECT console_type FROM console_status WHERE console_id=%s LIMIT 1", (_cid,))
                if _crows and _crows[0].get("console_type"):
                    _ctype = _crows[0]["console_type"]
            except Exception:
                pass
        return ok({
            "booking": {
                "id": row.get("id"),
                "customerName": row.get("staff_name", ""),
                "phone": row.get("phone", ""),
                "date": bd_str,
                "timeSlot": time_slot,
                "consoleType": _ctype,
                "durationMins": row.get("duration_mins", 60),
                "gameName": row.get("game_name", ""),
                "console_id": row.get("console_id", ""),
                "status": row.get("status", ""),
                "notes": row.get("notes", ""),
                "telegramChatId": row.get("telegram_chat_id", ""),
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

'''

if insert_marker in code:
    code = code.replace(insert_marker, patch_endpoint + "\n" + insert_marker, 1)
    with open(APP_FILE, "w") as f:
        f.write(code)
    compile(code, APP_FILE, "exec")
    print("✅ API Server: PATCH + GET booking endpoints added")
else:
    print("❌ API marker not found")

# ===== FIX 2: Bot — Replace sheets/consoles with fetch_console_status =====
BOT_FILE = "/root/psvibe-sales-bot/bot/handlers/admin_bookings.py"
with open(BOT_FILE) as f:
    bot_code = f.read()

old_consoles = '            consoles_data = await _replit_get_async("sheets/consoles")\n            consoles      = (consoles_data or {}).get("consoles", []) if consoles_data else []'

new_consoles = '            from bot import fetch_console_status\n            consoles_tmp = fetch_console_status()\n            consoles = [{"id":c["id"],"type":c.get("type",""),"liveStatus":c.get("status","Free")} for c in consoles_tmp]'

if old_consoles in bot_code:
    bot_code = bot_code.replace(old_consoles, new_consoles, 1)
    with open(BOT_FILE, "w") as f:
        f.write(bot_code)
    compile(bot_code, BOT_FILE, "exec")
    print("✅ Bot: sheets/consoles → fetch_console_status replaced")
else:
    print("❌ Bot pattern not found at line", bot_code.find("sheets/consoles"))
    idx = bot_code.find("sheets/consoles")
    if idx >= 0:
        print(f"  Context: {bot_code[idx:idx+150]}")
