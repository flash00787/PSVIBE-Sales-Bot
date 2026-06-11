#!/usr/bin/env python3
"""Fix attendance handler positions in app.py"""
with open('/root/psvibe-sales-bot/bot/app.py', 'r') as f:
    lines = f.readlines()

# Find and remove misplaced attendance handlers
# They were inserted after line 143 (the first "newbooking" occurrence)
remove_start = None
remove_end = None
for i, line in enumerate(lines):
    if line.strip() == '("checkin",      cmd_checkin),' and remove_start is None:
        remove_start = i
    if remove_start is not None and line.strip() == '("staff_list",   cmd_staff_list),':
        remove_end = i + 1
        break

if remove_start is not None and remove_end is not None:
    print(f"Removing misplaced handlers at lines {remove_start+1}-{remove_end}")
    del lines[remove_start:remove_end]
else:
    print("Misplaced handlers not found, checking state...")
    for i, line in enumerate(lines):
        if 'checkin' in line and 'BotCommand' not in line and 'cb_checkin' not in line:
            print(f"  Line {i+1}: {line.rstrip()}")

# Now find the correct insertion point - after "newbooking" in the tuple list
# The tuple list starts with ("member" pattern and ends with "]:"
# Find the LAST "newbooking" entry
insert_pos = None
for i in range(len(lines) - 1, -1, -1):
    if '"newbooking"' in lines[i] and 'cmd_staff_booking' in lines[i]:
        insert_pos = i + 1  # Insert AFTER this line
        break

if insert_pos:
    to_insert = [
        '        ("checkin",      cmd_checkin),\n',
        '        ("checkout",     cmd_checkout),\n',
        '        ("attendance",   cmd_attendance),\n',
        '        ("salary",       cmd_salary),\n',
        '        ("staff_status", cmd_staff_status),\n',
        '        ("staff_list",   cmd_staff_list),\n',
    ]
    for j, line in enumerate(to_insert):
        lines.insert(insert_pos + j, line)
    print(f"Inserted handlers after line {insert_pos}")

# Write back
with open('/root/psvibe-sales-bot/bot/app.py', 'w') as f:
    f.writelines(lines)

print("Done. Verifying...")
# Verify syntax
import py_compile
try:
    py_compile.compile('/root/psvibe-sales-bot/bot/app.py', doraise=True)
    print("Python syntax: OK ✅")
except py_compile.PyCompileError as e:
    print(f"Python syntax ERROR: {e}")
