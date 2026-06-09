#!/usr/bin/env python3
"""Fix Bot account-balances to exclude Topup/New member injects."""
with open('/root/psvibe_api_server/patch_routes.py') as f:
    src = f.read()

# After cm_rows is fetched and before the for loop, add inject filter
# Find the for loop start
old = '        for r in cm_rows:\n            acct_key = r["account"].strip().lower()'

new = """        # Fetch inject entries that overlap with topup (notes start with Topup or New member)
        _bad_inject = _mysql_query("SELECT account, SUM(amount) as total FROM cash_movements WHERE movement_type = 'inject' AND (note IS NOT NULL AND (note LIKE CONCAT('Topup', CHAR(37)) OR note LIKE CONCAT('New member', CHAR(37)))) GROUP BY account")
        _bad_inject_map = {}
        for _r in _bad_inject:
            _bad_inject_map[_r['account'].strip().lower()] = float(_r['total'] or 0)
        for r in cm_rows:
            acct_key = r["account"].strip().lower()"""

src = src.replace(old, new, 1)

# Then modify the inject handling to subtract bad injects
old2 = '            if r["movement_type"] in ("inject", "transfer_in"):\n                income_by_acct[acct_key] += amt'
new2 = """            if r["movement_type"] in ("inject", "transfer_in"):
                amt_adj = amt
                if r["movement_type"] == "inject" and acct_key in _bad_inject_map:
                    amt_adj = amt - _bad_inject_map[acct_key]
                income_by_acct[acct_key] += amt_adj"""

src = src.replace(old2, new2, 1)

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
