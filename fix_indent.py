#!/usr/bin/env python3
"""Fix indentation of _excl_inj line."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '_excl_inj' in line and not line.startswith('        _excl_inj'):
        # Fix indentation to exactly 8 spaces
        indent = '        '
        content = line.strip()
        if content.startswith('_excl_inj'):
            lines[i] = indent + content + '\n'
            print(f'Fixed line {i+1}')
            break

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.writelines(lines)

src = ''.join(lines)
compile(src, '/root/psvibe_api_server/dashboard_routes.py', 'exec')
print('Syntax OK')
