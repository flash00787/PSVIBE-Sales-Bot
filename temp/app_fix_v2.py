#!/usr/bin/env python3
"""Properly add attendance handlers to app.py and __init__.py"""

import sys

# Step 1: Fix __init__.py if needed
with open('/root/psvibe-sales-bot/bot/handlers/__init__.py', 'r') as f:
    init_content = f.read()

if '.staff_attendance_handler' not in init_content:
    init_content += "\nfrom .staff_attendance_handler import *  # noqa: F401,F403\n"
    with open('/root/psvibe-sales-bot/bot/handlers/__init__.py', 'w') as f:
        f.write(init_content)
    print("__init__.py: Updated ✅")
else:
    print("__init__.py: Already has import ✅")

# Step 2: Fix app.py
with open('/root/psvibe-sales-bot/bot/app.py', 'r') as f:
    lines = f.readlines()

# Find the tuple list end marker: "    ]:"  (after all handler tuples)
tuple_end_idx = None
for i in range(len(lines) - 1, -1, -1):
    if lines[i].strip() == ']:' and i > 10:
        tuple_end_idx = i
        break

if tuple_end_idx is None:
    print("ERROR: Could not find tuple list end!")
    sys.exit(1)

# Insert attendance handlers before the closing "]:"
# First check if already exists
already_there = any('checkin' in line and 'cmd_checkin' in line for line in lines)

if not already_there:
    attendance_entries = [
        '        ("checkin",      cmd_checkin),\n',
        '        ("checkout",     cmd_checkout),\n',
        '        ("attendance",   cmd_attendance),\n',
        '        ("salary",       cmd_salary),\n',
        '        ("staff_status", cmd_staff_status),\n',
        '        ("staff_list",   cmd_staff_list),\n',
    ]
    for entry in reversed(attendance_entries):
        lines.insert(tuple_end_idx, entry)
    print(f"app.py: Added {len(attendance_entries)} handler entries ✅")
else:
    print("app.py: Handlers already exist ✅")

# Step 3: Add BotCommands
# Find the end of the BotCommand list
botcmd_end = None
for i in range(len(lines) - 1, -1, -1):
    if 'BotCommand' in lines[i] and 'console' in lines[i] and 'status' in lines[i]:
        botcmd_end = i + 1
        break

if botcmd_end and not any('checkin' in l and 'BotCommand' in l for l in lines):
    botcmd_entries = [
        '            BotCommand("checkin",     "\\u2705 Staff Check-in"),\n',
        '            BotCommand("checkout",    "\\u274c Staff Check-out"),\n',
        '            BotCommand("attendance",  "\\U0001f4cb Daily Attendance"),\n',
        '            BotCommand("salary",      "\\U0001f4b0 Staff Salary"),\n',
        '            BotCommand("staff_status","\\U0001f465 Staff Status"),\n',
        '            BotCommand("staff_list",  "\\U0001f4dd Staff List"),\n',
    ]
    for entry in reversed(botcmd_entries):
        lines.insert(botcmd_end, entry)
    print("app.py: Added BotCommands ✅")
else:
    print("app.py: BotCommands already exist or not found ✅")

# Write back
with open('/root/psvibe-sales-bot/bot/app.py', 'w') as f:
    f.writelines(lines)

# Verify syntax
try:
    py_compile = __import__('py_compile')
    py_compile.compile('/root/psvibe-sales-bot/bot/app.py', doraise=True)
    print("Python syntax: OK ✅")
except Exception as e:
    print(f"Syntax error: {e}")
