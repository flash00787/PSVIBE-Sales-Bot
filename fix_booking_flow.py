#!/usr/bin/env python3
"""Fix booking_flow.py: add missing module-level variables and fix import."""
import re

path = '/root/Sales-Tele-Bot_refactored/bot/handlers/booking_flow.py'

with open(path, 'r') as f:
    content = f.read()

modified = False

# Fix 1: Change explicit import to from bot import *
if 'from bot import' in content and 'from bot import *' not in content:
    content = content.replace('from bot import now_mmt', 'from bot import *')
    content = content.replace('from bot import fetch_allowed_staff_ids, now_mmt', 'from bot import *')
    modified = True
    print('Fix 1: import changed')

# Fix 2: Find last import line and insert module-level vars
lines = content.split('\n')
last_import_idx = -1
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('from ') or stripped.startswith('import '):
        last_import_idx = i

if last_import_idx >= 0 and '_pending_cancel_note' not in content:
    insert_lines = [
        '',
        'from typing import Dict, Optional',
        'import asyncio',
        '',
        '# Module-level state',
        '_pending_cancel_note: Dict[int, dict] = {}',
        '_REMIND_TASKS: dict[str, "asyncio.Task[None]"] = {}',
        '_SESSION_END_TIMES: dict[str, str] = {}',
    ]
    for j, ins in enumerate(insert_lines):
        lines.insert(last_import_idx + 1 + j, ins)
    content = '\n'.join(lines)
    modified = True
    print('Fix 2: module-level vars added')

if modified:
    with open(path, 'w') as f:
        f.write(content)
    print('DONE')
else:
    print('Nothing to fix')
