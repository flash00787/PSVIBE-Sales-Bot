members_path = '/root/psvibe-sales-bot/bot/handlers/members.py'
with open(members_path) as f:
    members = f.read()

# Bug 2: Remove duplicate api_add_topup call that doubles new member balance
old_topup = '            # \u2500\u2500 API write (best-effort) \u2500\u2500\n            try:\n                api_add_topup({\n                    "date": today,\n                    "member_id": nm_id,\n                    "type": "New Member",\n                    "amount": nm_amt,\n                    "kpay": nm_kpay,\n                    "cash": nm_cash,\n                    "mins_added": _nm_added_mins,\n                    "staff": nm_staff,\n                })\n            except Exception as e:\n                logging.warning("Topup API write failed (GSheet fallback OK): %s", e)\n            topup_sh.batch_update'

new_topup = '            # NOTE: api_add_member (members/register) already creates wallet + topup_log entry.\n            # No separate api_add_topup call here to avoid double-balance bug.\n            topup_sh.batch_update'

if old_topup in members:
    members = members.replace(old_topup, new_topup)
    print("Fixed Bug 2: Removed duplicate api_add_topup in new member flow")
else:
    # Try finding with different indentation
    print("Trying to find the block by searching for api_add_topup...")
    import re
    # Find the block containing api_add_topup in the _nm_bg function
    lines = members.split('\n')
    for i, line in enumerate(lines):
        if 'api_add_topup' in line and 'nm_id' in lines[i+1] if i+1 < len(lines) else False:
            print(f"  Found api_add_topup at line {i+1}: {line.strip()}")
        elif 'api_add_topup' in line:
            print(f"  Found api_add_topup at line {i+1}: {line.strip()}")
    
    # Alternative: search for the exact string
    pos = members.find('api_add_topup({\n                    "date": today,')
    if pos >= 0:
        print(f"  Found api_add_topup block at position {pos}")
        # Show context
        ctx_start = max(0, pos - 200)
        ctx_end = min(len(members), pos + 600)
        print(repr(members[ctx_start:ctx_end]))
    else:
        print("  Could not find the exact api_add_topup block pattern")

with open(members_path, 'w') as f:
    f.write(members)
print("Wrote members.py - check output for success")
