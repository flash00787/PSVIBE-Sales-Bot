#!/usr/bin/env python3
"""Add missing import to launch_session_sale in sales.py"""
FILE = "/root/psvibe-sales-bot/bot/handlers/sales.py"
with open(FILE) as f:
    data = f.read()

old = """    stock_map: dict = {}
    try:
        inv_data = await _replit_get_async("stock/current")"""

new = """    stock_map: dict = {}
    try:
        from bot.api_client import _replit_get_async
        inv_data = await _replit_get_async("stock/current")"""

if old in data:
    data = data.replace(old, new, 1)
    with open(FILE, "w") as f:
        f.write(data)
    compile(data, FILE, "exec")
    print("✅ sales.py: launch_session_sale import fixed")
else:
    print("❌ Pattern not found")
    idx = data.find('_replit_get_async("stock/current")')
    if idx >= 0:
        print(f"Found at {idx}: {repr(data[idx-80:idx+30])}")
