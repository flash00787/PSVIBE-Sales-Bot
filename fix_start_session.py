with open('/root/psvibe_api_server/app.py', 'r') as f:
    lines = f.readlines()

# Find the confirmed-by-console endpoint location
insert_idx = None
for i, line in enumerate(lines):
    if '@app.get("/api/get-confirmed-booking"' in line:
        insert_idx = i
        break

print(f"Found at line {insert_idx+1}")

# Add new endpoint: start session with auto-checkin of confirmed booking
new_endpoint = [
    '\n',
    '@app.post("/api/consoles/start-session", response_model=GenericResponse, tags=["Consoles"], summary="Start session, auto-checkin confirmed booking [MySQL]")\n',
    'async def api_start_console_session(req: dict, auth=Depends(verify_api_key)):\n',
    '    """Start a session on a console. If there is a Confirmed booking, auto-checkin and link it."""\n',
    '    try:\n',
    "        console_id = (req.get('console_id') or '').strip()\n",
    "        member_id = req.get('member_id') or req.get('memberId') or 'Guest'\n",
    "        game_name = req.get('game_name') or req.get('gameName') or ''\n",
    "        duration_mins = req.get('duration_mins') or req.get('durationMins') or 60\n",
    '        if not console_id:\n',
    "            return error_response(message='console_id required')\n",
    '\n',
    "        # Check if console already Active\n",
    '        cs = _mysql_query_one("SELECT status FROM console_status WHERE console_id=%s", (console_id,))\n',
    "        if cs and cs['status'] == 'Active':\n",
    '            return error_response(message=f"Console {console_id} is already Active")\n',
    '\n',
    "        # Look for a Confirmed booking for this console today\n",
    "        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')\n",
    '        bk = _mysql_query_one(\n',
    '            "SELECT id, member_id, game_name, duration_mins, telegram_chat_id, staff_name FROM console_booking "\n',
    "            \"WHERE console_id=%s AND status='confirmed' AND DATE(booking_date)=%s ORDER BY created_at DESC LIMIT 1\",\n",
    '            (console_id, today)\n',
    '        )\n',
    '\n',
    '        booking_id = None\n',
    '        if bk:\n',
    "            # Use booking data (autofill)\n",
    "            member_id = bk['member_id'] or member_id\n",
    "            game_name = bk['game_name'] or game_name\n",
    "            duration_mins = bk['duration_mins'] or duration_mins\n",
    "            booking_id = bk['id']\n",
    '            # Check-in: update booking to Active\n',
    "            _mysql_exec(\"UPDATE console_booking SET status='Active', start_time=NOW() WHERE id=%s\", (booking_id,))\n",
    '            logger.info(f"Auto-checkin booking #{booking_id} for console {console_id}")\n',
    '        else:\n',
    "            # No confirmed booking — create a new Active booking record\n",
    '            _mysql_exec(\n',
    '                "INSERT INTO console_booking (console_id, member_id, status, booking_date, start_time, duration_mins, game_name) VALUES (%s,%s,\\'Active\\',%s,NOW(),%s,%s)",\n',
    '                (console_id, member_id, today, duration_mins, game_name)\n',
    '            )\n',
    '            booking_id = _mysql_query_one("SELECT LAST_INSERT_ID() as id")[\'id\']\n',
    '\n',
    '        # Set console to Active\n',
    '        _mysql_exec(\n',
    '            "UPDATE console_status SET status=\\'Active\\', current_member=%s, current_game=%s, start_time=NOW() WHERE console_id=%s",\n',
    '            (member_id, game_name, console_id)\n',
    '        )\n',
    '\n',
    '        return ok({\n',
    '            "booking_id": booking_id,\n',
    '            "console_id": console_id,\n',
    '            "member_id": member_id,\n',
    '            "status": "Active",\n',
    '            "linked_booking": True if bk else False,\n',
    '        })\n',
    '    except Exception as e:\n',
    '        logger.exception(f"start-session error: {e}")\n',
    '        return error_response(message=str(e))\n',
    '\n',
]

lines[insert_idx:insert_idx] = new_endpoint

with open('/root/psvibe_api_server/app.py', 'w') as f:
    f.writelines(lines)

print(f"Start-session endpoint added at line {insert_idx+1}")
