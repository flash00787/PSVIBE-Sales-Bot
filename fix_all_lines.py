#!/usr/bin/env python3
"""Fix all broken lines in dashboard_routes.py."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    src = f.read()

# Line 1802: incomplete sales_daily query
src = src.replace(
    'rows = _mq("SELECT payment_method, net, notes FROM sales_daily WHERE payment_method IS NOT NULL")',
    '        rows = _mq("SELECT payment_method, net, notes FROM sales_daily WHERE payment_method IS NOT NULL AND payment_method != ' + "''" + '")'
)

# Line 2146: wrong indentation, use correct query
src = src.replace(
    '            rows = _mq("SELECT payment_method, net, notes FROM sales_daily WHERE payment_method IS NOT NULL AND payment_method != ' + "''" + '")',
    '        rows = _mq("SELECT payment_method, net, notes FROM sales_daily WHERE payment_method IS NOT NULL AND payment_method != ' + "''" + '")'
)

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(src)

compile(src, '/root/psvibe_api_server/dashboard_routes.py', 'exec')
print("Syntax OK")
