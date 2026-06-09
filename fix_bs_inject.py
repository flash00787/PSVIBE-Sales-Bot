#!/usr/bin/env python3
"""Fix Balance Sheet inject exclusion (FIX 2 for BS)."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    src = f.read()

# Find the BS inject query pattern
# Original: inj = float(_mqo("SELECT COALESCE(SUM(amount),0) as t FROM cash_movements WHERE account=%s AND movement_type='inject'", (db,))["t"] or 0)
# Need to add: AND (note IS NULL OR (note NOT LIKE CONCAT('Topup', CHAR(37)) AND note NOT LIKE CONCAT('New member', CHAR(37))))

old_part = "movement_type='inject'"
new_part = "movement_type='inject' AND (note IS NULL OR (note NOT LIKE CONCAT('Topup', CHAR(37)) AND note NOT LIKE CONCAT('New member', CHAR(37))))"

# Replace the SECOND occurrence (BS), not the first (FB which was already fixed)
count = 0
idx = src.find(old_part)
while idx >= 0:
    count += 1
    if count == 2:
        src = src[:idx] + new_part + src[idx + len(old_part):]
        print(f"Fixed BS inject query (occurrence #{count})")
        break
    idx = src.find(old_part, idx + 1)

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
