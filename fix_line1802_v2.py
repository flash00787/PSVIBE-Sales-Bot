#!/usr/bin/env python3
"""Fix broken line 1802."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    src = f.read()

# The broken line has: != ."" ."
# Replace with proper: != ''
src = src.replace(
    'AND payment_method != .' + chr(34) + chr(34) + ' .' + chr(34),
    "AND payment_method != " + chr(39) + chr(39)
)

# Also verify line 2146 (BS query)
src = src.replace(
    "' SELECT payment_method, net, notes FROM sales_daily'",
    ''
)

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(src)

try:
    compile(src, '/root/psvibe_api_server/dashboard_routes.py', 'exec')
    print("Syntax OK")
except SyntaxError as e:
    print(f"Error: {e}")
    # Show the problematic area
    print(f"Line {e.lineno}: {src.split(chr(10))[e.lineno-1][:100]}")
