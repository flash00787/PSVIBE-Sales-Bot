const { Client } = require('ssh2');
const fs = require('fs');

// Read local fix protocol script
const fixes = `
echo "=== START FIX PROTOCOL ==="
date

# 1. Fix _format_booking_line in booking.py - better console display for pending bookings
cat > /tmp/booking_fix.py << 'PYEOF'
import re

with open('/root/psvibe-sales-bot/customer_bot/booking.py', 'r') as f:
    content = f.read()

# Fix _format_booking_line: better field handling
# Change console display to prefer consoleType over console_id and handle empty values
old_format = '''    bk_id = b.get("id", "?")
    status = str(b.get("status", "")).lower()
    date = b.get("booking_date", b.get("date", "?"))
    time_str = b.get("booking_time", b.get("timeSlot", b.get("startTime", "?")))
    if "T" in str(time_str):
        time_str = str(time_str).split("T")[1][:5]
    console_type = b.get("console_id", b.get("consoleType", "?"))
    duration = b.get("duration_mins", b.get("durationMins", ""))
    game = b.get("game_name", b.get("gameName", ""))
    phone = b.get("phone", "")'''

new_format = '''    bk_id = b.get("id", "?")
    status = str(b.get("status", "")).lower()
    date = b.get("booking_date") or b.get("date") or "?"
    time_str = b.get("booking_time") or b.get("timeSlot") or b.get("startTime") or "?"
    if "T" in str(time_str):
        time_str = str(time_str).split("T")[1][:5]
    # For pending bookings, console_id may store the type (e.g. "PS5", "PS5 Pro")
    # For confirmed bookings, console_id is the specific console (e.g. "C - 01")
    # Prefer consoleType (user-friendly), fall back to console_id, then "PS5" as default
    raw_console = b.get("consoleType") or b.get("console_id") or ""
    if not raw_console.strip():
        raw_console = "PS5"
    console_type = raw_console
    duration = b.get("duration_mins") or b.get("durationMins") or ""
    game = b.get("game_name") or b.get("gameName") or ""
    phone = b.get("phone") or ""'''

if old_format in content:
    content = content.replace(old_format, new_format)
    print("PATCH 1: _format_booking_line updated")
else:
    print("PATCH 1: old_format NOT FOUND - checking content")
    if "b.get(\\"console_id\\", b.get(\\"consoleType\\"" in content:
        print("  -> Found console_id pattern, attempting line-by-line patch")

# Fix _parse_booking_datetime_mmt: handle booking_date objects/datetime
old_parse = '''    bk_date = booking.get("date") or booking.get("booking_date") or ""
    time_slot = booking.get("timeSlot") or booking.get("startTime") or ""
    
    if not bk_date or not time_slot:
        return None
    
    # Clean date (remove time part if present)
    bk_date_clean = str(bk_date).split(" ")[0]'''

new_parse = '''    bk_date = booking.get("date") or booking.get("booking_date") or ""
    time_slot = booking.get("timeSlot") or booking.get("startTime") or ""
    
    if not bk_date or not time_slot:
        return None
    
    # Clean date: handle datetime objects, strings, etc.
    bk_date_str = str(bk_date)
    # If it's a datetime or date object, extract date part
    if hasattr(bk_date, 'strftime'):
        bk_date_clean = bk_date.strftime("%Y-%m-%d")
    else:
        bk_date_clean = bk_date_str.split(" ")[0]'''

if old_parse in content:
    content = content.replace(old_parse, new_parse)
    print("PATCH 2: _parse_booking_datetime_mmt updated")
else:
    print("PATCH 2: old_parse NOT FOUND")

with open('/root/psvibe-sales-bot/customer_bot/booking.py', 'w') as f:
    f.write(content)

print("booking.py written")

# Verify syntax
import subprocess
result = subprocess.run(['python3', '-m', 'py_compile', '/root/psvibe-sales-bot/customer_bot/booking.py'], 
                       capture_output=True, text=True)
if result.returncode == 0:
    print("PY_COMPILE: PASS")
else:
    print("PY_COMPILE: FAIL")
    print(result.stderr)
PYEOF

python3 /tmp/booking_fix.py

echo "=== FIX DONE ==="
