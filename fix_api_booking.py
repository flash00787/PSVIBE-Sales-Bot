#!/usr/bin/env python3
"""Add missing /api/bookings/search and /api/bookings POST endpoints to API server"""
import sys

with open('/root/psvibe_api_server/app.py', 'r') as f:
    content = f.read()

# New endpoints to inject
new_code = '''

# ═══════════════════════════════════════
#  SEARCH — bookings/search
# ═══════════════════════════════════════
@app.get("/api/bookings/search", tags=["Bookings"])
async def api_bookings_search(
    telegram_chat_id: str = Query(None, description="Search by Telegram chat ID"),
    date: str = Query(None, description="Search by date (YYYY-MM-DD or M/D/YYYY)"),
    auth=Depends(verify_api_key),
):
    """Search bookings by telegram_chat_id and/or date."""
    try:
        import json as _json
        bk = get_booking_rows()
        results = []
        for row in bk[1:]:
            if len(row) < 7:
                continue
            bk_id = row[0].strip()
            bk_date = row[1].strip()
            bk_console = row[2].strip()
            bk_member = row[3].strip() if len(row) > 3 else ""
            bk_time = row[4].strip() if len(row) > 4 else ""
            bk_endtime = row[5].strip() if len(row) > 5 else ""
            bk_status = row[6].strip() if len(row) > 6 else ""
            bk_staff = row[7].strip() if len(row) > 7 else ""
            bk_notes = row[8].strip() if len(row) > 8 else ""

            # Parse notes for extra data
            extra = {}
            if bk_notes:
                try:
                    extra = _json.loads(bk_notes)
                except Exception:
                    extra = {}

            # Date filter
            if date:
                date_match = False
                if date == bk_date:
                    date_match = True
                else:
                    try:
                        parts = date.split('-')
                        if len(parts) == 3:
                            converted = f"{int(parts[1])}/{int(parts[2])}/{parts[0]}"
                            if converted == bk_date:
                                date_match = True
                    except Exception:
                        pass
                if not date_match:
                    continue

            # Telegram chat_id filter
            if telegram_chat_id:
                tg_id = extra.get("telegramChatId", "")
                if str(tg_id) != str(telegram_chat_id):
                    continue

            entry = {
                "id": bk_id,
                "date": bk_date,
                "consoleId": bk_console,
                "memberId": bk_member,
                "timeSlot": bk_time,
                "endTime": bk_endtime,
                "status": bk_status,
                "staff": bk_staff,
                "createdAt": f"{bk_date} {bk_time}",
                "consoleType": extra.get("consoleType", ""),
                "gameName": extra.get("gameName", ""),
                "phone": extra.get("phone", ""),
                "customerName": extra.get("customerName", ""),
                "durationMins": extra.get("durationMins", 0),
                "telegramChatId": extra.get("telegramChatId", ""),
            }
            results.append(entry)

        return ok(results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════
#  CREATE/UPDATE — bookings (customer bot format)
# ═══════════════════════════════════════
@app.post("/api/bookings", tags=["Bookings"])
async def api_bookings(req: dict, auth=Depends(verify_api_key)):
    """Create a booking from customer bot payload."""
    try:
        import json as _json
        sh = get_worksheet(SHEET_CONSOLE_BOOKING)
        now = now_mmt()
        date_formatted = now.strftime("%-m/%-d/%Y")
        time_s = now.strftime("%H:%M")
        seq = now.strftime("%H%M")
        console_type = req.get("consoleType", "")
        console_id = console_type  # Store as-is

        notes_data = {
            "customerName": req.get("customerName", ""),
            "phone": req.get("phone", ""),
            "timeSlot": req.get("timeSlot", ""),
            "consoleType": req.get("consoleType", ""),
            "durationMins": req.get("durationMins", 0),
            "gameName": req.get("gameName", ""),
            "telegramChatId": req.get("telegramChatId", ""),
            "username": req.get("username", ""),
        }
        notes_json = _json.dumps(notes_data)
        bk_id = f"BK-{now.strftime('%Y%m%d')}-{console_id.replace(' ', '').replace('-', '')}-{seq}"
        sh.append_row([bk_id, date_formatted, console_id, "", time_s, "", "Pending", "", notes_json],
                      value_input_option="USER_ENTERED")
        invalidate_cache("bookings")
        return ok({"id": bk_id, "status": "Pending"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

'''

# Find insertion point: after cancel_booking endpoint
# Look for the section header before cancel_booking
markers = [
    '#  MUTATION — cancel_booking',
    '# MUTATION — cancel_booking',
]
found_at = -1
for marker in markers:
    found_at = content.find(marker)
    if found_at >= 0:
        break

if found_at < 0:
    print("FIX2_FAIL: cancel_booking marker not found")
    sys.exit(1)

# Find end of cancel_booking function (next endpoint or blank line before next section)
# Search for the next @app or next # ═══ section after cancel_booking
rest = content[found_at:]
# Find the end of cancel_booking function
# Look for the next @app. or # ═ marking a new section
import re
next_section = re.search(r'\n\s*(@app\.|# ═)', rest[100:])  # skip past the marker line
if next_section:
    insert_pos = found_at + 100 + next_section.start()
else:
    # Insert at end of file
    insert_pos = len(content)

new_content = content[:insert_pos] + new_code + content[insert_pos:]

with open('/root/psvibe_api_server/app.py', 'w') as f:
    f.write(new_content)

print("FIX2_OK: Added bookings/search and bookings POST endpoints")
