#!/usr/bin/env python3
"""Fix Bot account-balances: exclude Topup/New member sales from sales_daily."""
with open('/root/psvibe_api_server/patch_routes.py') as f:
    src = f.read()

# 1. Add notes to SELECT
old_sql = "SELECT payment_method\n            FROM sales_daily\n            WHERE sale_date >= '2026-01-01'"
new_sql = "SELECT payment_method, notes\n            FROM sales_daily\n            WHERE sale_date >= '2026-01-01'"
src = src.replace(old_sql, new_sql, 1)
print("Added notes to SELECT")

# 2. Add notes filter before parsing each row
old_loop = "        for r in sale_rows:\n            pm = r[\"payment_method\"] or \"\"\n\n            if \"|\" in pm:"
new_loop = """        for r in sale_rows:
            _note = (r.get("notes") or "").strip()
            if _note.startswith("Topup") or _note.startswith("New member"):
                continue
            pm = r["payment_method"] or ""

            if "|" in pm:"""
src = src.replace(old_loop, new_loop, 1)
print("Added notes filter")

with open('/root/psvibe_api_server/patch_routes.py', 'w') as f:
    f.write(src)

try:
    compile(src, '/root/psvibe_api_server/patch_routes.py', 'exec')
    print('Syntax OK')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
    lines = src.split('\n')
    for i in range(max(0, e.lineno - 3), min(len(lines), e.lineno + 2)):
        print(f'  {i+1}: {lines[i].rstrip()[:120]}')
