with open('/root/psvibe_api_server/app.py', 'r') as f:
    lines = f.readlines()

# Find line indices
guard_idx = None
cancel_idx = None
for i, line in enumerate(lines):
    if '# Update booking status to Active' in line:
        guard_idx = i
    if '@app.post("/api/bookings/cancel"' in line:
        cancel_idx = i

if guard_idx is None:
    print("ERROR: Could not find guard insertion point")
    exit(1)
if cancel_idx is None:
    print("ERROR: Could not find cancel endpoint")
    exit(1)

print(f"Guard at line {guard_idx+1}, cancel at line {cancel_idx+1}")

# 1. Insert check-in guard before "Update booking status to Active"
guard_code = [
    "        # 🛡️ Guard: reject if console already has a different Active booking\n",
    "        if console_id:\n",
    "            existing = _mysql_query_one(\n",
    '                "SELECT id FROM console_booking WHERE console_id=%s AND status=\'Active\' AND id != %s",\n',
    "                (console_id, booking_id)\n",
    "            )\n",
    "            if existing:\n",
    f'                return error_response(message=f"Console {{console_id}} already has Active booking #{{existing[\'id\']}}. End that session first.")\n',
    "\n",
]

# Insert before guard_idx
lines[guard_idx:guard_idx] = guard_code
# Adjust cancel_idx since we inserted 8 lines
cancel_idx += 8

# 2. Add new endpoint before the cancel endpoint
new_endpoint = [
    '\n',
    '@app.get("/api/bookings/confirmed-by-console", response_model=GenericResponse, tags=["Bookings"], summary="Get confirmed bookings for a console [MySQL]")\n',
    'async def api_confirmed_bookings_for_console(console_id: str, auth=Depends(verify_api_key)):\n',
    '    """Get today\'s Confirmed booking for a console (for auto-checkin)."""\n',
    "    try:\n",
    "        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')\n",
    "        row = _mysql_query_one(\n",
    "            \"SELECT id, console_id, member_id, booking_date, start_time, end_time, status, staff_name, notes, telegram_chat_id, duration_mins, phone, game_name FROM console_booking \"\n",
    "            \"WHERE console_id=%s AND status='confirmed' AND DATE(booking_date)=%s ORDER BY created_at DESC LIMIT 1\",\n",
    "            (console_id, today)\n",
    "        )\n",
    "        if not row:\n",
    '            return ok({"booking": None})\n',
    "        for k in ('start_time', 'end_time', 'created_at'):\n",
    "            if k in row and row[k] is not None:\n",
    "                row[k] = row[k].isoformat() if hasattr(row[k], 'isoformat') else str(row[k])\n",
    '        return ok({"booking": row})\n',
    "    except Exception as e:\n",
    "        logger.exception(f\"confirmed-by-console error: {e}\")\n",
    '        return ok({"booking": None})\n',
]

lines[cancel_idx:cancel_idx] = new_endpoint
cancel_idx += len(new_endpoint)
print(f"Inserted new endpoint at line {cancel_idx - len(new_endpoint) + 1}")

with open('/root/psvibe_api_server/app.py', 'w') as f:
    f.writelines(lines)

print("✅ Done!")
