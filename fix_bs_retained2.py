#!/usr/bin/env python3
"""Fix BS retained: subtract excluded injects from retained earnings."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    src = f.read()

old = 'retained = ti - te - cost_of_sold - member_liab - total_dep  # depreciation'
new = """        _excl_inj = float(_mqo("SELECT COALESCE(SUM(amount),0) as t FROM cash_movements WHERE movement_type = 'inject' AND (note IS NOT NULL AND (note LIKE CONCAT('Topup', CHAR(37)) OR note LIKE CONCAT('New member', CHAR(37))))")["t"] or 0)
        retained = ti - te - cost_of_sold - member_liab - total_dep - _excl_inj  # depreciation"""

src = src.replace(old, new, 1)

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(src)

try:
    compile(src, '/root/psvibe_api_server/dashboard_routes.py', 'exec')
    print('Syntax OK')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
