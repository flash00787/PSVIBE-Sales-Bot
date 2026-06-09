#!/usr/bin/env python3
"""Revert retained earnings ti change — topup backfill should remain in retained."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    src = f.read()

# Revert: put back original ti query
old_q = "SELECT COALESCE(SUM(net),0) as t FROM sales_daily WHERE net>0 AND (notes IS NULL OR (notes NOT LIKE CONCAT('Topup', CHAR(37)) AND notes NOT LIKE CONCAT('New member', CHAR(37))))"
new_q = "SELECT COALESCE(SUM(net),0) as t FROM sales_daily WHERE net>0"

if old_q in src:
    src = src.replace(old_q, new_q, 1)
    print('Reverted retained earnings ti query')
else:
    print('Pattern not found (may already be reverted)')

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(src)

try:
    compile(src, '/root/psvibe_api_server/dashboard_routes.py', 'exec')
    print('Syntax OK')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
