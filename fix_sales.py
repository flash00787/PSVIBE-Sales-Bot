sales_path = '/root/psvibe-sales-bot/bot/handlers/sales.py'
with open(sales_path) as f:
    sales = f.read()

# Fix _check_console_in_session
old_check = '    active = next(\n        (c for c in consoles if c.get("id") == console_id\n         and c.get("status") in ("Active", "Scheduled")),\n        None,\n    )'

new_check = '    # Filter to only dicts (safety against API returning strings in list)\n    consoles_dicts = [c for c in consoles if isinstance(c, dict)]\n    if len(consoles_dicts) != len(consoles):\n        logging.warning("_check_console_in_session: filtered %d non-dict elements from consoles",\n                        len(consoles) - len(consoles_dicts))\n    active = next(\n        (c for c in consoles_dicts if c.get("id") == console_id\n         and c.get("status") in ("Active", "Scheduled")),\n        None,\n    )'

if old_check in sales:
    sales = sales.replace(old_check, new_check)
    print("Fixed _check_console_in_session")
else:
    print("WARNING: Could not find _check_console_in_session pattern")

# Fix prompt_console  
old_prompt = '    try:\n        _cons = [c["id"] for c in await fetch_console_status_async()]\n    except Exception as e:\n        logging.warning("Failed to fetch console status for booking keyboard: %s", e)\n        _cons = sorted(VALID_CONSOLES)'

new_prompt = '    try:\n        raw_cons = await fetch_console_status_async()\n        _cons = [c["id"] for c in raw_cons if isinstance(c, dict) and c.get("id")]\n        if not _cons:\n            _cons = sorted(VALID_CONSOLES)\n    except Exception as e:\n        logging.warning("Failed to fetch console status for booking keyboard: %s", e)\n        _cons = sorted(VALID_CONSOLES)'

if old_prompt in sales:
    sales = sales.replace(old_prompt, new_prompt)
    print("Fixed prompt_console")
else:
    print("WARNING: Could not find prompt_console pattern")

# Fix step_mins - add max limit (Bug 3)
old_mins_line = '    if mins <= 0:'
pos = sales.find(old_mins_line)
if pos >= 0:
    # Find the end of this block (next 'return MINS')
    block_end = sales.find('return MINS', pos)
    if block_end >= 0:
        block_end = sales.find('\n', block_end) + 1
        old_mins_block = sales[pos:block_end]
        
        new_mins_block = '''    if mins <= 0:
        await update.message.reply_text("\u26a0\ufe0f \u1019\u102d\u1014\u1005\u1039 1 \u1014\u103e\u1004\u1037\u103a\u1021\u1011\u1000\u1039 \u1011\u100a\u1037\u103a\u1015\u1031\u1038\u1015\u102b -")
        return MINS

    # Anti-spam guard: max 1440 mins (24 hours) per session
    MAX_SESSION_MINS = 1440
    if mins > MAX_SESSION_MINS:
        await update.message.reply_text(
            f"\u26a0\ufe0f \u1010\u1005\u103a\u1001\u102b\u1010\u100a\u103a\u1038 {MAX_SESSION_MINS:,} \u1019\u102d\u1014\u1005\u1039 (24 \u1014\u102c\u101b\u102e) \u1021\u1011\u102d\u101e\u102c \u1011\u100a\u1037\u103a\u101c\u102d\u102f\u1037\u101b\u1015\u102b\u101e\u100a\u103a -\\n"
            f"\u1015\u103c\u1031\u1038\u1007\u1030\u1038\u1015\u103c\u102f\u102d\u1037\u104a {MAX_SESSION_MINS:,} \u1021\u1031\u102c\u1000\u103a \u1002\u100f\u1014\u103a\u1038\u101b\u102d\u102f\u1000\u103a\u1015\u102b -",
        )
        return MINS
'''
        sales = sales[:pos] + new_mins_block + sales[block_end:]
        print("Fixed step_mins (Bug 3: max mins limit)")
    else:
        print("WARNING: Could not find end of step_mins block")
else:
    print("WARNING: Could not find step_mins validation pattern")

with open(sales_path, 'w') as f:
    f.write(sales)
print("Wrote sales.py")
