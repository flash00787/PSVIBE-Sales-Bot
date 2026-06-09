#!/usr/bin/env python3
"""Fix _do_extend: ext_delay wrong formula + planned_mins wrong value."""
FILE = "/root/psvibe-sales-bot/bot/handlers/booking_flow.py"
with open(FILE) as f:
    code = f.read()

old = (
    '    if has_remind:\n'
    '        ext_delay = (extra_mins - 5) * 60   # seconds until 5-min-before-end\n'
    '        # Bot loop: fire at "5 min before end", then every 5 min\n'
    '        task = asyncio.create_task(\n'
    '            _remind_loop(bot, chat_id, cid, member_id,\n'
    '                         extra_mins, new_end_t, ext_delay)\n'
    '        )\n'
    '        _REMIND_TASKS[_remind_key(cid, chat_id)] = task'
)

new = (
    '    if has_remind:\n'
    '        # BUG FIX: ext_delay must be based on TOTAL remaining time, not extra_mins\n'
    '        # Old: ext_delay = (extra_mins - 5) * 60 → wrong if passed time between start and extend\n'
    '        total_rem_secs = max(0, (new_end_dt - now).total_seconds())\n'
    '        ext_delay = max(0, total_rem_secs - 5 * 60)  # seconds until 5-min-before-end\n'
    '        # planned_mins = remaining minutes for display (at least 1)\n'
    '        rem_mins = max(1, int(total_rem_secs / 60))\n'
    '        # Bot loop: fire at "5 min before end", then every 5 min\n'
    '        task = asyncio.create_task(\n'
    '            _remind_loop(bot, chat_id, cid, member_id,\n'
    '                         rem_mins, new_end_t, ext_delay)\n'
    '        )\n'
    '        _REMIND_TASKS[_remind_key(cid, chat_id)] = task'
)

if old in code:
    code = code.replace(old, new, 1)
    with open(FILE, "w") as f:
        f.write(code)
    compile(code, FILE, "exec")
    print("✅ _do_extend: ext_delay + planned_mins fixed")
else:
    print("❌ Pattern not found")
