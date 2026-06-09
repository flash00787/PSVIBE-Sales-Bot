#!/usr/bin/env python3
"""Fix approve flow: consoles_with_game returns dicts, not strings."""
import re

FILE = '/root/psvibe-sales-bot/bot/handlers/admin_bookings.py'

with open(FILE) as f:
    t = f.read()

# Bug: consoles_with_game returns list[dict], code calls .upper() on dicts
# The API returns [{"console_id": "C-06", "console_name": "C-06"}]
# Fix: extract console_id from each dict
old = '            consoles_with_game = await get_consoles_with_game_async(game_name)\n                cw_upper  = {c.upper() for c in consoles_with_game}'
new = '            consoles_with_game = await get_consoles_with_game_async(game_name)\n                cw_upper  = {c.get("console_id","").upper() for c in consoles_with_game if isinstance(c, dict)}'

if old in t:
    t = t.replace(old, new, 1)
    print("1. consoles_with_game fix applied")
else:
    print("1. SKIP - pattern not found")
    for m in re.finditer('consoles_with_game', t):
        pos = m.start()
        print(f"  Found at {pos}: ...{t[pos-40:pos+80]}...")

# Revert any wrong console_type change from previous script
old2 = 'consoles = [{"id":c["id"],"type":c.get("console_type",""),"liveStatus":c.get("status","Free")} for c in consoles_tmp]'
new2 = 'consoles = [{"id":c["id"],"type":c.get("type",""),"liveStatus":c.get("status","Free")} for c in consoles_tmp]'

if old2 in t:
    t = t.replace(old2, new2, 1)
    print("2. Reverted console_type (fetch_console_status maps to 'type' key)")

with open(FILE, 'w') as f:
    f.write(t)
compile(t, FILE, 'exec')
print("✅ OK")
