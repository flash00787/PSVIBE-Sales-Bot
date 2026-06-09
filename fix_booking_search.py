#!/usr/bin/env python3
"""Add bookings/search endpoint to API server."""
import sys

filepath = sys.argv[1]

with open(filepath, 'r') as f:
    c = f.read()

# Find the location to insert (after the bookings list endpoint at ~line 1120)
# Look for @app.put("/api/end_booking/...")
marker = '@app.put("/api/end_booking/{booking_id}"'

new_endpoint = '''

@app.get("/api/bookings/search", response_model=GenericResponse, tags=["Bookings"], summary="Search bookings by telegram_chat_id [MySQL]")
async def api_search_bookings(telegram_chat_id: str = Query("", description="Telegram chat ID of customer"), auth=Depends(verify_api_key)):
    """Search bookings by telegram chat ID."""
    try:
        if telegram_chat_id:
            rows = _mysql_query(
                "SELECT id, console_id, member_id, booking_date, start_time, end_time, status, staff_name, notes, telegram_chat_id, duration_mins, phone, game_name FROM console_booking WHERE telegram_chat_id=%s ORDER BY booking_date DESC, start_time DESC",
                (telegram_chat_id,)
            )
        else:
            rows = _mysql_query(
                "SELECT id, console_id, member_id, booking_date, start_time, end_time, status, staff_name, notes, telegram_chat_id, duration_mins, phone, game_name FROM console_booking ORDER BY booking_date DESC, start_time DESC"
            )
        from datetime import datetime as _dt
        normalized = []
        for r in rows:
            start = r.get("start_time")
            time_slot = ""
            if start:
                try:
                    start_dt = _dt.fromisoformat(str(start)) if isinstance(start, str) else start
                    time_slot = start_dt.strftime("%H:%M")
                except (ValueError, TypeError):
                    time_slot = str(start)[:5] if start else ""
            duration = r.get("duration_mins") or ""
            game_name = r.get("game_name") or ""
            normalized.append({
                "id": r.get("id"),
                "console_id": r.get("console_id"),
                "member_id": r.get("member_id"),
                "booking_date": str(r.get("booking_date", "")),
                "timeSlot": time_slot,
                "startTime": str(r.get("start_time", "")),
                "endTime": str(r.get("end_time", "")),
                "status": r.get("status", "pending"),
                "staff_name": r.get("staff_name"),
                "notes": r.get("notes"),
                "telegram_chat_id": r.get("telegram_chat_id"),
                "durationMins": duration,
                "duration_mins": duration,
                "gameName": game_name,
                "game_name": game_name,
                "phone": r.get("phone"),
            })
        return JSONResponse(content={"success": True, "data": {"bookings": normalized, "total": len(normalized)}})
    except Exception as e:
        logger.error("api_search_bookings: %s", e, exc_info=True)
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

'''

if marker in c:
    c = c.replace(marker, new_endpoint + '\n' + marker)
    print("Added bookings/search endpoint")
else:
    print("WARNING: marker not found")
    # Try alternative
    if '@app.put("/api/end_booking/{booking_id}"' in c:
        c = c.replace('@app.put("/api/end_booking/{booking_id}"', new_endpoint + '\n@app.put("/api/end_booking/{booking_id}"')
        print("Added via alternative match")
    else:
        print("Could not find insertion point")

with open(filepath, 'w') as f:
    f.write(c)

print("Done!")
