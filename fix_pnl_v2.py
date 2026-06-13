# Fix PNL: Keep gross_profit as number for backward compat, add game_profit/food_profit as separate fields

with open('/root/psvibe_api_server/dashboard_routes.py', 'r') as f:
    content = f.read()

# The current problematic response block
old_response = '''            "gross_profit": {"game_profit": round(game_profit,0), "food_profit": round(food_profit,0), "total": round(total_gross_profit,0)},'''

# Fix: keep gross_profit as total number, add game_profit and food_profit as separate top-level fields
new_response = '''            "gross_profit": round(total_gross_profit,0), "game_profit": round(game_profit,0), "food_profit": round(food_profit,0),'''

content = content.replace(old_response, new_response)

# Also remove the duplicate stock_fifo block at line 2233-2236
old_dup = '''        import stock_fifo, pymysql
        _sfc = pymysql.connect(host='127.0.0.1', user='root', password='PsVibe@MySQL2024!', database='psvibe_api')
        _sfr = stock_fifo.calc_fifo(_sfc)
        _sfc.close()
        cogs = _sfr['cogs']'''

new_clean = '''        # cogs already computed above'''

content = content.replace(old_dup, new_clean)

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(content)

print("PNL fix v2 applied ✅")
print("  - gross_profit is now total number:", "✅" if 'gross_profit": round(total_gross_profit' in content else "❌")
print("  - game_profit as top-level field:", "✅" if 'game_profit": round(game_profit' in content else "❌")
print("  - food_profit as top-level field:", "✅" if 'food_profit": round(food_profit' in content else "❌")
print("  - duplicate stock_fifo removed:", "✅" if content.count('stock_fifo.calc_fifo(_sfc)') == 1 else "❌")
