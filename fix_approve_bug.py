#!/usr/bin/env python3
"""Fix approve flow bugs in admin_bookings.py"""
FILE = '/root/psvibe-sales-bot/bot/handlers/admin_bookings.py'

with open(FILE) as f:
    t = f.read()

# Bug 1: consoles_with_game returns list[dict] but code expects list[str]
# Fix: extract console_id from dict
old_cw = """            consoles_with_game = await get_consoles_with_game_async(game_name)
                cw_upper  = {c.upper() for c in consoles_with_game}"""

new_cw = """            consoles_with_game = await get_consoles_with_game_async(game_name)
                cw_upper  = {c.get("console_id","").upper() for c in consoles_with_game if isinstance(c, dict)}"""

t = t.replace(old_cw, new_cw, 1)
print("1. consoles_with_game fix applied")

# Bug 2: API returns 'console_type' not 'type' - fix the comprehension
old_type = """            consoles = [{"id":c["id"],"type":c.get("type",""),"liveStatus":c.get("status","Free")} for c in consoles_tmp]"""

new_type = """            consoles = [{"id":c["id"],"type":c.get("console_type",""),"liveStatus":c.get("status","Free")} for c in consoles_tmp]"""

t = t.replace(old_type, new_type, 1)
print("2. console_type field fix applied")

with open(FILE, 'w') as f:
    f.write(t)

compile(t, FILE, 'exec')
print("✅ File compiles OK!")
