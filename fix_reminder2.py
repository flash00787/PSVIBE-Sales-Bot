#!/usr/bin/env python3
"""Fix auto_cancel_no_shows.py - add customer notification to 10-min reminder.
Note: {{ and }} are literal braces in f-strings to produce {bk_id} in generated code.
Note: \\n produces \n in generated code."""
import sys

f2 = '/root/psvibe-sales-bot/scripts/auto_cancel_no_shows.py'
with open(f2) as f:
    lines = f.readlines()

new_lines = []
patched = False
for i, line in enumerate(lines):
    new_lines.append(line)
    if 'Reminded staff about booking' in line and not patched:
        indent = ' ' * (len(line) - len(line.lstrip()))
        new_lines.append(
            f'{indent}# Also notify customer\n'
            f'{indent}_cust_chat = b.get("telegram_chat_id") or b.get("telegramChatId") or ""\n'
            f'{indent}if _cust_chat and CUSTOMER_BOT_TOKEN:\n'
            f'{indent}    _cust_remind = f"\\U0001F514 <b>PS VIBE Booking Reminder</b>\\nBooking #{{bk_id}}\\n\\U0001F4C5 {{bk_date_clean}}  \\U0001F550 {{time_str}}\\n\\U0001F3AE {{console}}  \\u23F1 {{duration}} mins"\n'
            f'{indent}    if game:\n'
            f'{indent}        _cust_remind += f"\\n\\U0001F579 {{game}}"\n'
            f'{indent}    _cust_remind += "\\n\\n\\u23F0 \\u1014\\u102d\\u1029\\u101b\\u1031\\u101b\\u1000\\u1039\\u101b\\u102e\\u1019\\u1031\\u101c\\u102c\\u1031\\u101b\\u1019\\u1039\\u1019"\n'
            f'{indent}    tg_send(_cust_chat, _cust_remind, token=CUSTOMER_BOT_TOKEN, parse_mode="HTML")\n'
            f'{indent}    print(f"  \\u2713 Reminded customer #{{bk_id}}")\n'
        )
        patched = True

if not patched:
    print("ERROR: 'Reminded staff' line not found")
    sys.exit(1)

with open(f2, 'w') as f:
    f.writelines(new_lines)

try:
    compile(''.join(new_lines), f2, 'exec')
    print(f"OK - patched")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
    with open(f2, 'w') as f:
        f.writelines(lines)
