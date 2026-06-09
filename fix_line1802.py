#!/usr/bin/env python3
"""Fix line 1802 - broken SQL syntax."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    lines = f.readlines()

# Fix line 1802
lines[1801] = '        rows = _mq("SELECT payment_method, net, notes FROM sales_daily WHERE payment_method IS NOT NULL AND payment_method != \\'\\'\\'\\'\\'\\'}")\n'

# Write back
with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.writelines(lines)

print("Line 1802 fixed")
