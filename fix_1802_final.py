#!/usr/bin/env python3
"""Fix line 1802 of dashboard_routes.py (broken SQL string)."""
import sys

with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    lines = f.readlines()

# Replace line 1802 (index 1801)
new_line = '        rows = _mq("SELECT payment_method, net, notes FROM sales_daily WHERE payment_method IS NOT NULL AND payment_method != \'\'")\n'
lines[1801] = new_line

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.writelines(lines)

# Verify
src = ''.join(lines)
try:
    compile(src, '', 'exec')
    print("Syntax OK")
except SyntaxError as e:
    print(f"Syntax error at line {e.lineno}: {e.msg}")
    print(f"Content: {lines[e.lineno-1].rstrip()[:100]}")
