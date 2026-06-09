#!/usr/bin/env python3
"""Fix BS retained earnings: exclude topup/new member sales from ti."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    src = f.read()

# Fix: ti = SUM(net) FROM sales_daily WHERE net>0 AND exclude topup/new member notes
old_q = 'SELECT COALESCE(SUM(net),0) as t FROM sales_daily WHERE net>0'
new_q = "SELECT COALESCE(SUM(net),0) as t FROM sales_daily WHERE net>0 AND (notes IS NULL OR (notes NOT LIKE CONCAT('Topup', CHAR(37)) AND notes NOT LIKE CONCAT('New member', CHAR(37))))"

first = src.find(old_q)
if first > 0:
    src = src[:first] + new_q + src[first + len(old_q):]
    print('Fixed retained earnings ti query')
else:
    print('Pattern not found!')

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(src)

try:
    compile(src, '/root/psvibe_api_server/dashboard_routes.py', 'exec')
    print('Syntax OK')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
    lines = src.split('\n')
    for i in range(max(0, e.lineno - 3), min(len(lines), e.lineno + 2)):
        print(f'  {i+1}: {lines[i].rstrip()[:120]}')
