import sys
path = '/root/Sales-Tele-Bot_refactored/bot/handlers/booking_flow.py'
with open(path) as f:
    lines = f.readlines()
insert = [
    'from typing import Dict, Optional\n',
    'import asyncio\n',
    '\n',
    '# Module-level state\n',
    '_pending_cancel_note: Dict[int, dict] = {}\n',
    '_REMIND_TASKS: dict[str, "asyncio.Task[None]"] = {}\n',
    '_SESSION_END_TIMES: dict[str, str] = {}\n',
    '\n',
]
for i, line in enumerate(insert):
    lines.insert(8 + i, line)
with open(path, 'w') as f:
    f.writelines(lines)
print('DONE: vars added after line 8')
