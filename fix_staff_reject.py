#!/usr/bin/env python3
with open("/root/psvibe_api_server/app.py", "r") as f:
    content = f.read()

# Find the end of the customer branch and add else clause
old = '''            threading.Thread(target=_notify_booking_received, args=(customer_name, booking_date_str, time_slot, console_type, duration_mins, game_name, phone, bk_id), daemon=True).start()

            return ok({"id": bk_id, "message": "Booking created"})
    except Exception as e:'''

new = '''            threading.Thread(target=_notify_booking_received, args=(customer_name, booking_date_str, time_slot, console_type, duration_mins, game_name, phone, bk_id), daemon=True).start()

            return ok({"id": bk_id, "message": "Booking created"})
        else:
            # No customerName — staff should use POST /api/sessions/start
            return JSONResponse(content={"success": False, "error": "Staff bookings must use POST /api/sessions/start"}, status_code=400)
    except Exception as e:'''

if old not in content:
    print("ERROR: old text not found")
    # Try to find nearby content
    idx = content.find('return ok({"id": bk_id, "message": "Booking created"})')
    print(f"Found at idx {idx}")
    print(repr(content[idx-50:idx+150]))
else:
    content = content.replace(old, new, 1)
    with open("/root/psvibe_api_server/app.py", "w") as f:
        f.write(content)
    print("Added else: block for staff format rejection")

import ast
ast.parse(content)
print("Syntax OK")
