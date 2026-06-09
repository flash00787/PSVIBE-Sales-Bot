#!/usr/bin/env python3
"""Fix _check_member_in_session: move actives comprehension inside try/except block."""

with open("/root/psvibe-sales-bot/bot/handlers/sales.py", "r") as f:
    content = f.read()

old_block = (
    "    try:\n"
    "        consoles = await fetch_console_status_async()\n"
    "    except Exception as e:\n"
    '        logging.warning("Failed to fetch console status for member session check: %s", e)\n'
    "        return await prompt_console(update, context)\n"
    "\n"
    "    actives = [\n"
    "        c for c in consoles\n"
    '        if c.get("member") == member_id and c.get("status") in ("Active", "Scheduled")\n'
    "    ]"
)

new_block = (
    "    try:\n"
    "        consoles = await fetch_console_status_async()\n"
    "        actives = [\n"
    "            c for c in consoles\n"
    '            if c.get("member") == member_id and c.get("status") in ("Active", "Scheduled")\n'
    "        ]\n"
    "    except Exception as e:\n"
    '        logging.warning("Failed to fetch console status for member session check: %s", e)\n'
    "        return await prompt_console(update, context)"
)

if old_block in content:
    content = content.replace(old_block, new_block, 1)
    with open("/root/psvibe-sales-bot/bot/handlers/sales.py", "w") as f:
        f.write(content)
    print("OK - actives block moved inside try/except")
else:
    print("ERROR: Old block not found!")
    # Find the function to help debug
    idx = content.find("async def _check_member_in_session")
    if idx >= 0:
        print("Found function at index", idx)
        print("Context:")
        print(repr(content[idx:idx+600]))
