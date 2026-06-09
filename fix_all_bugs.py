#!/usr/bin/env python3
"""Fix 3 sales bot bugs: console selection, double balance, large mins spam."""
import re, sys

# ──────────────────────────────────────────────────────────────
# BUG 1: Fix _replit_get_async to always return list of dicts
# ──────────────────────────────────────────────────────────────

init_path = '/root/psvibe-sales-bot/bot/__init__.py'
with open(init_path) as f:
    init = f.read()

# Fix the second _replit_get_async (line ~3058) to filter non-dicts from list results
old_get_async = '''        if is_list_path and isinstance(data, dict):
            # _api_call_async strips {success:, data:} envelope — check both cases
            if "data" in data:
                inner = data["data"]
                if isinstance(inner, list):
                    return inner
                if isinstance(inner, dict):
                    for _list_key in ("bookings", "items", "members", "consoles", "games", "waitlist"):
                        if _list_key in inner and isinstance(inner[_list_key], list):
                            return inner[_list_key]
                    return inner
            # Already-unwrapped: data itself may contain list-like keys
            for _list_key in ("bookings", "items", "members", "consoles", "games", "waitlist"):
                if _list_key in data and isinstance(data[_list_key], list):
                    return data[_list_key]
        return data'''

new_get_async = '''        if is_list_path and isinstance(data, dict):
            # _api_call_async strips {success:, data:} envelope — check both cases
            if "data" in data:
                inner = data["data"]
                if isinstance(inner, list):
                    return [x for x in inner if isinstance(x, dict)]
                if isinstance(inner, dict):
                    for _list_key in ("bookings", "items", "members", "consoles", "games", "waitlist"):
                        if _list_key in inner and isinstance(inner[_list_key], list):
                            return [x for x in inner[_list_key] if isinstance(x, dict)]
                    return inner
            # Already-unwrapped: data itself may contain list-like keys
            for _list_key in ("bookings", "items", "members", "consoles", "games", "waitlist"):
                if _list_key in data and isinstance(data[_list_key], list):
                    return [x for x in data[_list_key] if isinstance(x, dict)]
            # Dict without list-like keys — return empty list (not the dict itself)
            logging.warning("API GET /%s returned dict without list keys — returning []", path)
            return []
        # If data is a list, filter to only dicts for list_path safety
        if is_list_path and isinstance(data, list):
            filtered = [x for x in data if isinstance(x, dict)]
            if len(filtered) != len(data):
                logging.warning("API GET /%s list had %d non-dict elements filtered", path, len(data) - len(filtered))
            return filtered
        return data'''

# Count occurrences — should replace the SECOND one (line ~3058)
count = init.count(old_get_async)
print(f"Found {count} occurrences of old _replit_get_async block")

# Replace only the second occurrence
first_pos = init.find(old_get_async)
if first_pos >= 0:
    second_pos = init.find(old_get_async, first_pos + len(old_get_async))
    if second_pos >= 0:
        init = init[:second_pos] + new_get_async + init[second_pos + len(old_get_async):]
        print("Replaced SECOND _replit_get_async block")
        
        # Also fix the FIRST one (line ~2127) similarly
        old_first = '''        if is_list_path and isinstance(data, dict):
            # _api_call_async strips {success:, data:} envelope — check both cases
            if "data" in data:
                inner = data["data"]
                if isinstance(inner, list):
                    return inner
                if isinstance(inner, dict):
                    for _list_key in ("bookings", "items", "members", "consoles", "games", "waitlist"):
                        if _list_key in inner and isinstance(inner[_list_key], list):
                            return inner[_list_key]
                    return inner
            # Already-unwrapped: data itself may contain list-like keys
            for _list_key in ("bookings", "items", "members", "consoles", "games", "waitlist"):
                if _list_key in data and isinstance(data[_list_key], list):
                    return data[_list_key]
        return data'''
        
        if old_first in init:
            init = init.replace(old_first, new_get_async, 1)
            print("Replaced FIRST _replit_get_async block")
    else:
        print("ERROR: Could not find second occurrence")
else:
    print("ERROR: Could not find any occurrence")

# Also fix _check_console_in_session in sales.py — add safety filter
sales_path = '/root/psvibe-sales-bot/bot/handlers/sales.py'
with open(sales_path) as f:
    sales = f.read()

# Fix the _check_console_in_session function to filter non-dicts
old_check = '''    active = next(
        (c for c in consoles if c.get("id") == console_id
         and c.get("status") in ("Active", "Scheduled")),
        None,
    )'''

new_check = '''    # Filter to only dicts (safety against API returning strings in list)
    consoles_dicts = [c for c in consoles if isinstance(c, dict)]
    if len(consoles_dicts) != len(consoles):
        logging.warning("_check_console_in_session: filtered %d non-dict elements from consoles",
                        len(consoles) - len(consoles_dicts))
    active = next(
        (c for c in consoles_dicts if c.get("id") == console_id
         and c.get("status") in ("Active", "Scheduled")),
        None,
    )'''

if old_check in sales:
    sales = sales.replace(old_check, new_check)
    print("Fixed _check_console_in_session in sales.py")
else:
    print("WARNING: Could not find _check_console_in_session pattern in sales.py")

# Also fix prompt_console — add dict filter before iterating
old_prompt = '''    try:
        _cons = [c["id"] for c in await fetch_console_status_async()]
    except Exception as e:
        logging.warning("Failed to fetch console status for booking keyboard: %s", e)
        _cons = sorted(VALID_CONSOLES)'''

new_prompt = '''    try:
        raw_cons = await fetch_console_status_async()
        _cons = [c["id"] for c in raw_cons if isinstance(c, dict) and c.get("id")]
        if not _cons:
            _cons = sorted(VALID_CONSOLES)
    except Exception as e:
        logging.warning("Failed to fetch console status for booking keyboard: %s", e)
        _cons = sorted(VALID_CONSOLES)'''

if old_prompt in sales:
    sales = sales.replace(old_prompt, new_prompt)
    print("Fixed prompt_console in sales.py")
else:
    print("WARNING: Could not find prompt_console pattern in sales.py")

# ──────────────────────────────────────────────────────────────
# BUG 2: Remove double topup API call in new member creation
# ──────────────────────────────────────────────────────────────

members_path = '/root/psvibe-sales-bot/bot/handlers/members.py'
with open(members_path) as f:
    members = f.read()

# Remove the api_add_topup call in the new member background writer
old_topup = '''            # ── API write (best-effort) ──
            try:
                api_add_topup({
                    "date": today,
                    "member_id": nm_id,
                    "type": "New Member",
                    "amount": nm_amt,
                    "kpay": nm_kpay,
                    "cash": nm_cash,
                    "mins_added": _nm_added_mins,
                    "staff": nm_staff,
                })
            except Exception as e:
                logging.warning("Topup API write failed (GSheet fallback OK): %s", e)
            topup_sh.batch_update'''

new_topup = '''            # NOTE: api_add_member (members/register) already creates wallet + topup_log entry.
            # No separate api_add_topup call here to avoid double-balance bug.
            topup_sh.batch_update'''

if old_topup in members:
    members = members.replace(old_topup, new_topup)
    print("Fixed Bug 2: Removed duplicate api_add_topup in new member flow")
else:
    print("WARNING: Could not find api_add_topup pattern in members.py")

# ──────────────────────────────────────────────────────────────
# BUG 3: Add max limit on play mins to prevent spam/large-number issues
# ──────────────────────────────────────────────────────────────

old_mins = '''    if mins <= 0:
        await update.message.reply_text("⚠️ မိနစ် 1 နှင့်အထက် ထည့်ပေးပါ -")
        return MINS'''

new_mins = '''    if mins <= 0:
        await update.message.reply_text("⚠️ မိနစ် 1 နှင့်အထက် ထည့်ပေးပါ -")
        return MINS

    # Anti-spam guard: max 1440 mins (24 hours) per session
    MAX_SESSION_MINS = 1440
    if mins > MAX_SESSION_MINS:
        await update.message.reply_text(
            f"⚠️ တစ်ခါတည်း {MAX_SESSION_MINS:,} မိနစ် (24 နာရီ) အထိသာ ထည့်လို့ရပါသည် -\n"
            f"ကျေးဇူးပြု၍ {MAX_SESSION_MINS:,} အောက် ဂဏန်းရိုက်ပါ -",
        )
        return MINS'''

if old_mins in sales:
    sales = sales.replace(old_mins, new_mins)
    print("Fixed Bug 3: Added max 1440 mins limit to step_mins")
else:
    print("WARNING: Could not find step_mins validation pattern in sales.py")

# ──────────────────────────────────────────────────────────────
# Write all files
# ──────────────────────────────────────────────────────────────

with open(init_path, 'w') as f:
    f.write(init)
print("Wrote __init__.py")

with open(sales_path, 'w') as f:
    f.write(sales)
print("Wrote sales.py")

with open(members_path, 'w') as f:
    f.write(members)
print("Wrote members.py")

print("\nAll 3 bugs fixed!")
