#!/usr/bin/env python3
"""Fix KPay balance: exclude Topup/New member injects from balance calculations (both FB and BS)."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    src = f.read()

# === FIX 1: Finance Balances - cash_map inject filtering ===
old1 = '        key_to_name = {"cash": "Cash", "wave": "Wave", "kpay": "KPay", "aya_pay": "AYA Pay", "kbz_bank": "KBZ Bank", "acm_acc": "ACM\'s Acc"}'
new1 = """        # Subtract inject entries that overlap with topup (notes start with Topup or New member)
        _bad_inject_rows = _mq("SELECT account, COALESCE(SUM(amount), 0) as total FROM cash_movements WHERE movement_type = 'inject' AND (note IS NOT NULL AND (note LIKE CONCAT('Topup', CHAR(37)) OR note LIKE CONCAT('New member', CHAR(37)))) GROUP BY account")
        for _r in _bad_inject_rows:
            _k = "inject|" + _r["account"]
            if _k in cash_map:
                cash_map[_k] -= float(_r["total"] or 0)
        key_to_name = {"cash": "Cash", "wave": "Wave", "kpay": "KPay", "aya_pay": "AYA Pay", "kbz_bank": "KBZ Bank", "acm_acc": "ACM's Acc"}"""
src = src.replace(old1, new1, 1)
print('FIX 1: FB inject filtering applied')

# === FIX 2: Balance Sheet - inject query with note exclusion ===
old2 = '            inj = float(_mqo("SELECT COALESCE(SUM(amount),0) as t FROM cash_movements WHERE account=%s AND movement_type=' + "'" + "inject'" + '", (db,))["t"] or 0)'
new2 = '            inj = float(_mqo("SELECT COALESCE(SUM(amount),0) as t FROM cash_movements WHERE account=%s AND movement_type=' + "'" + "inject' AND (note IS NULL OR (note NOT LIKE CONCAT('Topup', CHAR(37)) AND note NOT LIKE CONCAT('New member', CHAR(37))))" + '", (db,))["t"] or 0)'
src = src.replace(old2, new2, 1)
print('FIX 2: BS inject filtering applied')

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(src)

try:
    compile(src, '/root/psvibe_api_server/dashboard_routes.py', 'exec')
    print('Syntax OK')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
    lines = src.split('\n')
    for i in range(max(0, e.lineno - 3), min(len(lines), e.lineno + 2)):
        nearby = lines[i].rstrip()
        print(f'  {i+1}: {nearby[:120]}')
