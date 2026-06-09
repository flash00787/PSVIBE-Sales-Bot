#!/usr/bin/env python3
"""Fix BS diff: add excluded injects back to retained."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    src = f.read()

# Change - _excl_inj to + _excl_inj
old = 'retained = ti - te - cost_of_sold - member_liab - total_dep - _excl_inj  # depreciation'
new = 'retained = ti - te - cost_of_sold - member_liab - total_dep + _excl_inj  # depreciation'

if old in src:
    src = src.replace(old, new, 1)
    print('Changed -_excl_inj to +_excl_inj')
else:
    print('Pattern not found, trying alternative')

# If the + version isn't there, the retained might still be original (no _excl_inj)
alt_old = '        retained = ti - te - cost_of_sold - member_liab - total_dep'
# Check for the indent issue
if alt_old in src and '_excl_inj' not in src:
    print('No _excl_inj found, retained is original')
    print('Diff will remain 89,933')

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(src)

compile(src, '/root/psvibe_api_server/dashboard_routes.py', 'exec')
print('Syntax OK')
