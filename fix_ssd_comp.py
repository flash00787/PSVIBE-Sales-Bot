#!/usr/bin/env python3
"""Fix SSD comparisons to normalize console_id spaces."""
FILE = "/root/psvibe-sales-bot/bot/handlers/ssd_disc.py"

with open(FILE) as f:
    code = f.read()

# Fix: all console_id comparisons should normalize spaces
code = code.replace(
    'r["console_id"].strip().upper() == cid.upper()',
    'r["console_id"].replace(" ", "").upper() == cid.replace(" ", "").upper()',
)

code = code.replace(
    'r["console_id"].upper() == cid.upper()',
    'r["console_id"].replace(" ", "").upper() == cid.replace(" ", "").upper()',
)

code = code.replace(
    'r["console_id"].upper().replace(" ", "") == cid.upper().replace(" ", "")',
    'r["console_id"].replace(" ", "").upper() == cid.replace(" ", "").upper()',
)

with open(FILE, "w") as f:
    f.write(code)

import py_compile
py_compile.compile(FILE, doraise=True)
print("OK")
