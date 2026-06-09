with open('/root/psvibe_api_server/app.py', 'r') as f:
    lines = f.readlines()

# Find insertion point
insert_idx = None
for i, line in enumerate(lines):
    if '@app.get("/api/get-confirmed-booking"' in line:
        insert_idx = i
        break

print(f"Found at line {insert_idx+1}")

# Add start-session endpoint - use simple string concatenation to avoid escape issues
endpoint = r'''
@app.post("/api/consoles/start-session", response_model=GenericResponse, tags=["Consoles"], summary="Start session, auto-checkin confirmed booking [MySQL]")
async def api_start_console_session(req: dict, auth=Depends(verify_api_key)):
    """Start a session on a console. If there is a Confirmed booking, auto-checkin and link it."""
    try:
        console_id = (req.get('console_id') or '').strip()
        member_id = req.get('member_id') or req.get('memberId') or 'Guest'
        game_name = req.get('game_name') or req.get('gameName') or ''
        duration_mins = req.get('duration_mins') or req.get('durationMins') or 60
        if not console_id:
            return error_response(message='console_id required')

        # Check if console already Active
        cs = _mysql_query_one("SELECT status FROM console_status WHERE console_id=%s", (console_id,))
        if cs and cs['status'] == 'Active':
            return error_response(message=f"Console {console_id} is already Active")

        # Look for a Confirmed booking for this console today
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        bk = _mysql_query_one(
            "SELECT id, member_id, game_name, duration_mins, telegram_chat_id, staff_name FROM console_booking "
            "WHERE console_id=%s AND status='confirmed' AND DATE(booking_date)=%s ORDER BY created_at DESC LIMIT 1",
            (console_id, today)
        )

        booking_id = None
        if bk:
            # Use booking data (autofill)
            member_id = bk['member_id'] or member_id
            game_name = bk['game_name'] or game_name
            duration_mins = bk['duration_mins'] or duration_mins
            booking_id = bk['id']
            # Check-in: update booking to Active
            _mysql_exec("UPDATE console_booking SET status='Active', start_time=NOW() WHERE id=%s", (booking_id,))
            logger.info(f"Auto-checkin booking #{booking_id} for console {console_id}")
        else:
            # No confirmed booking - create a new Active booking record
            _mysql_exec(
                "INSERT INTO console_booking (console_id, member_id, status, booking_date, start_time, duration_mins, game_name) VALUES (%s,%s,'Active',%s,NOW(),%s,%s)",
                (console_id, member_id, today, duration_mins, game_name)
            )
            booking_id = _mysql_query_one("SELECT LAST_INSERT_ID() as id")['id']

        # Set console to Active
        _mysql_exec(
            "UPDATE console_status SET status='Active', current_member=%s, current_game=%s, start_time=NOW() WHERE console_id=%s",
            (member_id, game_name, console_id)
        )

        return ok({
            "booking_id": booking_id,
            "console_id": console_id,
            "member_id": member_id,
            "status": "Active",
            "linked_booking": True if bk else False,
        })
    except Exception as e:
        logger.exception(f"start-session error: {e}")
        return error_response(message=str(e))

'''

lines.insert(insert_idx, endpoint)

with open('/root/psvibe_api_server/app.py', 'w') as f:
    f.writelines(lines)

print(f"Start-session endpoint inserted at line {insert_idx+1}")
