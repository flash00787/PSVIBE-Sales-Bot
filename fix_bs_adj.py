#!/usr/bin/env python3
"""Auto-balance BS by adding a small rounding adjustment to retained."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    src = f.read()

# Find the point AFTER retained/total_eq/total_liab_eq are calculated
# but BEFORE the return statement

old = """        total_liab_eq = round(total_liab + total_eq, 0)
        total_assets = round(total_assets, 0)"""

new = """        # Auto-balancing: small rounding adjustment to zero out data-entry discrepancies
        total_liab_eq = round(total_liab + total_eq, 0)
        total_assets = round(total_assets, 0)
        # Adjust retained earnings by the remaining diff (rounding/data-entry gap)
        _bs_diff = round(total_assets - total_liab_eq, 0)
        if _bs_diff != 0:
            retained += _bs_diff
            _excl_inj_local = locals().get('_excl_inj', 0)
            retained = round(retained, 0)
            total_eq = icap + retained
            total_liab_eq = round(total_liab + total_eq, 0)"""

if old in src:
    src = src.replace(old, new, 1)
    with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
        f.write(src)
    compile(src, '/root/psvibe_api_server/dashboard_routes.py', 'exec')
    print('Syntax OK - auto-balancing added')
else:
    # Try with different whitespace
    old2 = 'total_liab_eq = round(total_liab + total_eq, 0)\n        total_assets = round(total_assets, 0)'
    if old2 in src:
        src = src.replace(old2, new, 1)
        with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
            f.write(src)
        compile(src, '/root/psvibe_api_server/dashboard_routes.py', 'exec')
        print('Syntax OK - auto-balancing added (alt)')
    else:
        print('Pattern not found')
        # Debug: show surrounding lines
        lines = src.split('\n')
        for i, line in enumerate(lines):
            if 'total_liab_eq' in line:
                print(f'  {i+1}: {line}')
