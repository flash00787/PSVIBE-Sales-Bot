#!/usr/bin/env python3
"""Revert cash_movements changes, keep sales/topup fixes."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    src = f.read()

# Find the exact pattern for the broken cash_rows line
import re

# Find the broken cash_rows
old = src.find("cash_rows = _mq(\"SELECT movement_type, account, COALESCE")
if old > 0:
    # Find the end of this line
    end = src.find('\n', old)
    old_line = src[old:end]
    print(f"Found broken cash_rows at pos {old}")
    print(f"Line: {old_line[:80]}...")
    
    # Replace with original
    new_line = '        cash_rows = _mq("SELECT movement_type, account, COALESCE(SUM(amount), 0) as total FROM cash_movements GROUP BY movement_type, account")'
    src = src[:old] + new_line + src[end:]
    print("Reverted ✅")

# Find and fix the BS inject filter line
old_inj = src.find("COALESCE(note,''")
if old_inj > 0:
    # Find the start of this line (inj = float)
    line_start = src.rfind('\n', 0, old_inj) + 1
    line_end = src.find('\n', old_inj)
    old_line = src[line_start:line_end]
    print(f"Found broken inject at line: {old_line[:80]}...")
    
    # Replace with original inject query
    new_line = '            inj = float(_mqo("SELECT COALESCE(SUM(amount),0) as t FROM cash_movements WHERE account=%s AND movement_type=\\'inject\\'", (db,))["t"] or 0)'
    src = src[:line_start] + new_line + src[line_end:]
    print("Fixed BS inject query ✅")

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(src)

try:
    compile(src, '/root/psvibe_api_server/dashboard_routes.py', 'exec')
    print("Syntax OK ✅")
except SyntaxError as e:
    print(f"Syntax error: {e}")
