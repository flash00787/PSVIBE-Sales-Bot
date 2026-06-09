#!/usr/bin/env python3
"""Fix console_booking.console_id normalization + update SQL join in API."""
APP_FILE = "/root/psvibe_api_server/app.py"

# Step 1: Normalize DB
import subprocess
cmd = [
    "docker", "exec", "psvibe-mysql", "mysql",
    "-u", "psvibe_user", "-pPsVibe@2026_Rotated!", "psvibe_api",
    "-e", "UPDATE console_booking SET console_id = REPLACE(console_id, ' ', '') WHERE console_id LIKE '% %';"
]
r = subprocess.run(cmd, capture_output=True, text=True)
print("DB UPDATE:", r.stdout, r.stderr)

# Verify
cmd_v = [
    "docker", "exec", "psvibe-mysql", "mysql",
    "-u", "psvibe_user", "-pPsVibe@2026_Rotated!", "psvibe_api",
    "-e", "SELECT id, console_id, status FROM console_booking ORDER BY id;"
]
r2 = subprocess.run(cmd_v, capture_output=True, text=True)
print("After normalization:")
print(r2.stdout)

# Step 2: Update SQL in app.py to use REPLACE on console_id in the booking subquery JOIN
with open(APP_FILE) as f:
    code = f.read()

# Find the end_booking endpoint
old = (
    '            row = _mysql_query_one("SELECT console_id FROM console_booking WHERE id=%s", (booking_id,))\n'
    '        if row:\n'
    '            _mysql_exec("UPDATE console_status SET status=\'Free\', current_member=NULL, current_game=NULL, start_time=NULL WHERE console_id=%s", (row["console_id"],))'
)

new = (
    '            row = _mysql_query_one("SELECT console_id FROM console_booking WHERE id=%s", (booking_id,))\n'
    '        if row:\n'
    '            _cid = row["console_id"].replace(" ", "")\n'
    '            _mysql_exec("UPDATE console_status SET status=\'Free\', current_member=NULL, current_game=NULL, start_time=NULL WHERE REPLACE(console_id, \' \', \'\')=%s", (_cid,))'
)

if old in code:
    code = code.replace(old, new, 1)
    with open(APP_FILE, "w") as f:
        f.write(code)
    compile(code, APP_FILE, "exec")
    print("end_booking SQL fixed")
else:
    print("end_booking SQL NOT FOUND")
    idx = code.find("console_id FROM console_booking WHERE id")
    if idx >= 0:
        print(code[idx-20:idx+120])

# Also fix the fetch_console_status LEFT JOIN to use REPLACE
old2 = (
    ') cb ON cb.console_id LIKE CONCAT(cs.console_id, \'%\')'
)

new2 = (
    ') cb ON REPLACE(cb.console_id, \' \', \'\') LIKE CONCAT(REPLACE(cs.console_id, \' \', \'\'), \'%\')'
)

if old2 in code:
    code = code.replace(old2, new2, 1)
    with open(APP_FILE, "w") as f:
        f.write(code)
    compile(code, APP_FILE, "exec")
    print("fetch_console_status JOIN fixed")
else:
    print("fetch_console_status JOIN NOT FOUND")
    print("Checking for alternatives...")
    # Try shorter match
    idx = code.find("cb.console_id LIKE CONCAT(cs.console_id")
    if idx >= 0:
        print(f"Found at {idx}: {code[idx:idx+60]}")
