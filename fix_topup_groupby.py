#!/usr/bin/env python3
"""Fix: topup_log query in patch_routes.py uses GROUP BY payment_method collapsing duplicate PMs.

Bug: Two topup records with same payment_method 'KPay:90000/Cash:0' get GROUPed into ONE row.
The code then parses the payment_method string to extract amounts (90000 each).
The per-segment amount is 90000 (from the string), but there are TWO records (180,000 total).
Result: 90,000 Ks missing from KPay balance.

Fix: Remove GROUP BY, iterate individual rows instead.
"""
FILE = "/root/psvibe_api_server/patch_routes.py"
with open(FILE) as f:
    code = f.read()

old_q = """        topup_rows = _mysql_query("""
            SELECT payment_method, SUM(amount) as total
            FROM topup_log
            WHERE topup_date >= '2026-01-01'
            GROUP BY payment_method
        """)"""

new_q = """        topup_rows = _mysql_query("""
            SELECT payment_method, amount
            FROM topup_log
            WHERE topup_date >= '2026-01-01'
        """)"""

if old_q in code:
    code = code.replace(old_q, new_q, 1)
    print("✅ topup_log query: removed GROUP BY, removed SUM(amount)")
else:
    print("❌ Pattern 1 not found")

# Also fix the for loop — the variable name changes from r["total"] to r["amount"]
# Actually the code doesn't use r["total"] at all, it parses from payment_method string
# So no loop change needed

with open(FILE, "w") as f:
    f.write(code)
compile(code, FILE, "exec")
print("✅ File written + compiled OK")
