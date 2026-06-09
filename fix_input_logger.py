#!/usr/bin/env python3
"""Fix input_logger gspread None crash."""
FILE = "/root/psvibe-sales-bot/bot/handlers/input_logger.py"
with open(FILE) as f:
    data = f.read()

old = "                sh.append_rows(rows, value_input_option=\"USER_ENTERED\")"
new = "                if sh is not None:\n                    sh.append_rows(rows, value_input_option=\"USER_ENTERED\")"

if old in data:
    data = data.replace(old, new, 1)
    with open(FILE, "w") as f:
        f.write(data)
    compile(data, FILE, "exec")
    print("✅ input_logger: None check added")
else:
    print("❌ Pattern not found")
