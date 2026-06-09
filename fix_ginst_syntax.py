#!/usr/bin/env python3
"""Fix SyntaxError in ginst.py line 179 — unescaped double quotes in f-string."""
import sys

filepath = sys.argv[1]
with open(filepath, 'r') as f:
    lines = f.readlines()

# Line 179 (0-indexed: 178) currently has:
#   f"⚠️ <b>"{title}"</b> သည် <b>{cid}</b> မှာ ရှိပြီးသားပါ",
# Fix: use single quotes for f-string
old = lines[178]
lines[178] = "            f'⚠️ <b>\\\"{title}\\\"</b> သည် <b>{cid}</b> မှာ ရှိပြီးသားပါ',\n"

with open(filepath, 'w') as f:
    f.writelines(lines)

print(f"Fixed!")
print(f"OLD: {repr(old)}")
print(f"NEW: {repr(lines[178])}")
