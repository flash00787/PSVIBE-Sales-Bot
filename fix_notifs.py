#!/usr/bin/env python3
"""Fix notification bugs - cancel + 10-min reminder customer notification"""
import re, ast

# ── FIX 1: booking_flow.py – Cancel uses GET not PATCH ──
f1 = '/root/psvibe-sales-bot/bot/handlers/booking_flow.py'
with open(f1) as f:
    t = f.read()

old1 = '''    # Notify customer if they have Telegram
    tg_chat = result.get("telegramChatId") or ""'''
new1 = '''    # Notify customer if they have Telegram
    # Fetch full booking data via GET (PATCH result has no customer fields)
    _bk_full = await _replit_get_async(f"bookings/{bk_id}")
    if isinstance(_bk_full, dict) and "booking" in _bk_full:
        _bk_full = _bk_full["booking"]
    tg_chat = _bk_full.get("telegramChatId") or ""'''

t = t.replace(old1, new1, 1)
t = t.replace('result.get("date","?")','_bk_full.get("date","?")')
t = t.replace('result.get("timeSlot","?")','_bk_full.get("timeSlot","?")')
t = t.replace('result.get("consoleType","?")','_bk_full.get("consoleType","?")')

with open(f1, 'w') as f:
    f.write(t)
compile(t, f1, 'exec')
print("1. booking_flow.py OK")

# ── FIX 2: API – Add telegram_chat_id to search-bookings ──
f3 = '/root/psvibe_api_server/app.py'
with open(f3) as f:
    t3 = f.read()

old3 = '''normalized.append({"id": r.get("id",""), "customerName": r.get("staff_name",""), "phone": r.get("phone","") or r.get("telegram_chat_id",""), "date": bd_str, "timeSlot": time_slot, "consoleType": _ctype, "durationMins": r.get("duration_mins",60), "gameName": r.get("game_name",""), "console_id": r.get("console_id",""), "consoleId": r.get("console_id",""), "member_id": r.get("member_id",""), "status": r.get("status","")})'''
new3 = '''normalized.append({"id": r.get("id",""), "customerName": r.get("staff_name",""), "phone": r.get("phone","") or r.get("telegram_chat_id",""), "date": bd_str, "timeSlot": time_slot, "consoleType": _ctype, "durationMins": r.get("duration_mins",60), "gameName": r.get("game_name",""), "console_id": r.get("console_id",""), "consoleId": r.get("console_id",""), "member_id": r.get("member_id",""), "telegram_chat_id": r.get("telegram_chat_id",""), "telegramChatId": r.get("telegram_chat_id",""), "status": r.get("status","")})'''

if old3 in t3:
    t3 = t3.replace(old3, new3, 1)
    print("2. API search-bookings: telegramChatId added")
else:
    # Try with slight variation
    for m in re.finditer(r'normalized\.append', t3):
        start = m.start()
        chunk = t3[start:start+450]
        print(f"Found at {start}: {chunk[:200]}...")

with open(f3, 'w') as f:
    f.write(t3)
compile(t3, f3, 'exec')
print("   app.py OK")

# ── FIX 3: auto_cancel_no_shows.py – send customer notification ──
f2 = '/root/psvibe-sales-bot/scripts/auto_cancel_no_shows.py'
with open(f2) as f:
    lines = f.readlines()

new_lines = []
patched = False
for i, line in enumerate(lines):
    new_lines.append(line)
    if 'Reminded staff about booking' in line and not patched:
        indent = ' ' * (len(line) - len(line.lstrip()))
        # Add customer notification block
        new_lines.append(
            f'{indent}# Also notify customer via customer bot\n'
            f'{indent}_cust_chat = b.get("telegram_chat_id") or b.get("telegramChatId") or ""\n'
            f'{indent}if _cust_chat and CUSTOMER_BOT_TOKEN:\n'
            f'{indent}    _cust_remind = f"\\u23F0 <b>PS VIBE Booking Reminder</b>\\nBooking #{bk_id}\\n\\U0001F4C5 {bk_date_clean}  \\U0001F550 {time_str}\\n\\U0001F3AE {console}  \\u23F1 {duration} mins"\n'
            f'{indent}    if game:\n'
            f'{indent}        _cust_remind += f"\\n\\U0001F579 {game}"\n'
            f'{indent}    _cust_remind += "\\n\\n\\u23F0 \\u1014\\u102d\\u1029\\u101b\\u1031\\u101b\\u1000\\u1039\\u101b\\u102e\\u1019\\u1031\\u101c\\u102c\\u1031\\u101b\\u1019\\u1039\\u1019"\n'
            f'{indent}    tg_send(_cust_chat, _cust_remind, token=CUSTOMER_BOT_TOKEN, parse_mode="HTML")\n'
            f'{indent}    print(f"  \\u2713 Reminded customer #{bk_id}")\n'
        )
        patched = True

with open(f2, 'w') as f:
    f.writelines(new_lines)

try:
    ast.parse(''.join(new_lines))
    print(f"3. auto_cancel_no_shows.py OK {'(patched)' if patched else '(no match)'}")
except SyntaxError as e:
    print(f"3. SYNTAX ERROR: {e}")
    # Revert
    with open(f2, 'w') as f:
        f.writelines(lines)
    print("   REVERTED")

print("All done!")
