#!/usr/bin/env python3
with open("/root/psvibe-sales-bot/bot/handlers/booking.py", "r") as f:
    content = f.read()

# Update endpoint from consoles/start-session to sessions/start
old = '        # Use unified start-session endpoint (auto-checkin confirmed booking + guard)\n        payload = {\n            "console_id": cid,\n            "member_id": member_id,\n            "game_name": game,\n            "duration_mins": planned_mins if planned_mins > 0 else 0,\n        }\n        result = await _psvibe_post_async("consoles/start-session", payload)'

new = '        # FIX 2.4: Use dedicated sessions/start endpoint\n        payload = {\n            "console_id": cid,\n            "member_id": member_id,\n            "game_name": game,\n            "duration_mins": planned_mins if planned_mins > 0 else 0,\n            "booking_date": now_mmt().strftime("%Y-%m-%d"),\n        }\n        result = await _psvibe_post_async("sessions/start", payload)'

if old not in content:
    print("ERROR: old text not found")
    idx = content.find("consoles/start-session")
    print(f"Found consoles/start-session at idx {idx}")
    print(content[idx-300:idx+300])
else:
    content = content.replace(old, new, 1)
    with open("/root/psvibe-sales-bot/bot/handlers/booking.py", "w") as f:
        f.write(content)
    print("Sale Bot _do_create_booking updated to use POST /api/sessions/start")

import ast
ast.parse(content)
print("Syntax OK")
