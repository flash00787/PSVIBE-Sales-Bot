#!/usr/bin/env python3
"""Fix booking detail unwrap in _do_booking_action."""
FILE = "/root/psvibe-sales-bot/bot/handlers/admin_bookings.py"
with open(FILE) as f:
    code = f.read()

old = (
    '        bk_data      = await _replit_get_async(f"bookings/{bk_id}")\n'
    '        bk_info      = bk_data or {}\n'
    '        # Unwrap {"data": {"booking": {...}}} envelope\n'
    '        if isinstance(bk_info, dict) and bk_info.get("data") and isinstance(bk_info["data"], dict):\n'
    '            inner = bk_info["data"]\n'
    '            if "booking" in inner:\n'
    '                bk_info = inner["booking"]\n'
    '            else:\n'
    '                bk_info = inner\n'
    '        console_type = bk_info.get("consoleType", "")'
)

new = (
    '        bk_data      = await _replit_get_async(f"bookings/{bk_id}")\n'
    '        bk_info      = bk_data or {}\n'
    '        # Unwrap {"booking": {...}} or {"data": {"booking": {...}}} envelope\n'
    '        if isinstance(bk_info, dict):\n'
    '            if "booking" in bk_info:\n'
    '                bk_info = bk_info["booking"]\n'
    '            elif bk_info.get("data") and isinstance(bk_info["data"], dict):\n'
    '                inner = bk_info["data"]\n'
    '                if "booking" in inner:\n'
    '                    bk_info = inner["booking"]\n'
    '                else:\n'
    '                    bk_info = inner\n'
    '        console_type = bk_info.get("consoleType", "")'
)

if old in code:
    code = code.replace(old, new, 1)
    with open(FILE, "w") as f:
        f.write(code)
    compile(code, FILE, "exec")
    print("✅ Booking detail unwrap fixed")
else:
    print("❌ Pattern not found")
    idx = code.find('_replit_get_async(f"bookings/"')
    if idx >= 0:
        print(f"Found at {idx}")
        print(code[idx:idx+300])
