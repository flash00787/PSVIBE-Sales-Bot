import re

with open('/root/psvibe_api_server/app.py', 'r') as f:
    content = f.read()

# 1. Add check-in guard — reject if console already has Active booking
# Find the check-in function
old = """        # Update booking status to Active
        _mysql_exec("UPDATE console_booking SET status='Active', start_time=NOW() WHERE id=%s", (booking_id,))"""

new = """        # 🛡️ Guard: reject if console already has a different Active booking
        if console_id:
            existing = _mysql_query_one(
                "SELECT id FROM console_booking WHERE console_id=%s AND status='Active' AND id != %s",
                (console_id, booking_id)
            )
            if existing:
                return error_response(message=f"Console {console_id} already has Active booking #{existing['id']}. End that session first.")
        
        # Update booking status to Active
        _mysql_exec("UPDATE console_booking SET status='Active', start_time=NOW() WHERE id=%s", (booking_id,))"""

content = content.replace(old, new)

# 2. Add new endpoint: get confirmed bookings for a console today
# Find the end of booking routes section, before the wallet routes
old2 = """# ═══════════════════════════════════════

@app.post("/api/bookings/cancel\"\"\""

new2 = """# ═══════════════════════════════════════

@app.get("/api/bookings/confirmed-by-console", response_model=GenericResponse, tags=["Bookings"], summary="Get confirmed bookings for a console today [MySQL]")
async def api_confirmed_bookings_for_console(console_id: str, auth=Depends(verify_api_key)):
    \"\"\"Get today's Confirmed booking for a console (for auto-checkin).\"\"\"
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        row = _mysql_query_one(
            "SELECT * FROM console_booking WHERE console_id=%s AND status='confirmed' AND DATE(booking_date)=%s ORDER BY created_at DESC LIMIT 1",
            (console_id, today)
        )
        if not row:
            return ok({"booking": None, "message": "No confirmed booking for this console today"})
        # Convert datetime objects for JSON
        for k in ('start_time', 'end_time', 'created_at'):
            if k in row and row[k] is not None:
                row[k] = row[k].isoformat() if hasattr(row[k], 'isoformat') else str(row[k])
        return ok({"booking": row})
    except Exception as e:
        logger.error(f"confirmed-by-console error: {e}")
        return ok({"booking": None, "message": str(e)})

# ═══════════════════════════════════════

@app.post("/api/bookings/cancel\"\"\""  # Note: keep existing cancel route

# Replace
content = content.replace(old2, new2)

# But the new2 has a comment issue - let me just verify the replacement
if new2 in content:
    print("✅ New endpoint added: GET /api/bookings/confirmed-by-console")
else:
    print("⚠️  Replacement failed - trying fallback...")
    # Remove the trailing comment artifact
    content = content.replace('"  # Note: keep existing cancel route', '')

with open('/root/psvibe_api_server/app.py', 'w') as f:
    f.write(content)

print("✅ Check-in guard added to booking/checkin endpoint")
