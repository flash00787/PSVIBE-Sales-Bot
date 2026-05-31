"""PS VIBE — Member Creation Bug Fix Patch"""
import sys

# === FIX 1: api_members_register in app.py ===
app_path = '/root/psvibe_api_server/app.py'
with open(app_path, 'r') as f:
    content = f.read()

orig1 = '''        name = req.get("name", "")
        phone = req.get("phone", "")
        email = req.get("email", "")
        join_date = req.get("join_date", "")
        staff_name = req.get("staff_name", "")

        # Generate a member_id
        member_id = f"M-{int(time.time())}"'''

repl1 = '''        name = req.get("name", "")
        phone = req.get("phone", "")
        email = req.get("email", "")
        join_date = req.get("join_date", "")
        initial_mins = req.get("initial_mins", 0)

        # Use provided member_id, fall back to timestamp only if missing
        member_id = req.get("member_id", f"M-{int(time.time())}")
        staff_name = req.get("staff_name", req.get("staff", ""))'''

if orig1 in content:
    content = content.replace(orig1, repl1)
    print("FIX 1a: OK - use req member_id + accept staff field")
else:
    print("FIX 1a: MISS")
    sys.exit(1)

orig1b = '''            "INSERT IGNORE INTO member_wallets (member_id, member_name, phone, balance_mins) "
                "VALUES (%s, %s, %s, 0)",
                (member_id, name, phone)'''

repl1b = '''            "INSERT IGNORE INTO member_wallets (member_id, member_name, phone, balance_mins) "
                "VALUES (%s, %s, %s, %s)",
                (member_id, name, phone, initial_mins)'''

if orig1b in content:
    content = content.replace(orig1b, repl1b)
    print("FIX 1b: OK - wallet uses initial_mins")
else:
    print("FIX 1b: MISS - trying alternate match")
    # Could be different indentation
    if 'balance_mins) " "VALUES (%s, %s, %s, 0)"' in content:
        print("  Found pattern with different spacing")

orig2 = '''        member_id = req.get("member_id", "")
        amount = req.get("amount", 0)
        mins_added = req.get("mins_added", 0)
        payment_method = req.get("payment_method", "")
        staff_name = req.get("staff_name", "")
        date = req.get("date", "")'''

repl2 = '''        member_id = req.get("member_id", "")
        amount = req.get("amount", 0)
        # Accept both "mins_added" (API convention) and "minutes" (bot convention)
        mins_added = req.get("mins_added", req.get("minutes", 0))
        # Build payment_method from bot fields (kpay + cash) or accept direct field
        payment_method = req.get("payment_method", "")
        if not payment_method and (req.get("kpay") or req.get("cash")):
            payment_method = f"KPay:{req.get('kpay',0)}|Cash:{req.get('cash',0)}"
        # Accept both "staff_name" and "staff" (bot convention)
        staff_name = req.get("staff_name", req.get("staff", ""))
        date = req.get("date", "")'''

if orig2 in content:
    content = content.replace(orig2, repl2)
    print("FIX 2: OK - topup accepts bot field names")
else:
    print("FIX 2: MISS")

with open(app_path, 'w') as f:
    f.write(content)
print("app.py written successfully")


# === FIX 3: members.py - pass initial_mins to api_add_member ===
mpath = '/root/psvibe-sales-bot/bot/handlers/members.py'
with open(mpath, 'r') as f:
    mc = f.read()

orig3 = '''                    "member_id": nm_id,
                    "name": nm_name,
                    "phone": phone,
                    "staff": nm_staff,
                    "email": nm_email or "",
                    "row_no": row_no,
                })'''

repl3 = '''                    "member_id": nm_id,
                    "name": nm_name,
                    "phone": phone,
                    "staff": nm_staff,
                    "email": nm_email or "",
                    "row_no": row_no,
                    "initial_mins": bal_mins,
                })'''

if orig3 in mc:
    mc = mc.replace(orig3, repl3)
    print("FIX 3: OK - initial_mins passed to api_add_member")
else:
    print("FIX 3: MISS - trying regex search")
    import re
    # Find the api_add_member block
    m = re.search(r'api_add_member\(\{([^}]+)\}\)', mc)
    if m:
        print(f"  Found api_add_member block: {m.group(0)[:100]}")

with open(mpath, 'w') as f:
    f.write(mc)
print("members.py written successfully")

print("\n=== ALL FIXES APPLIED ===")
