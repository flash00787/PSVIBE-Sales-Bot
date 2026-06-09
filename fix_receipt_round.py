#!/usr/bin/env python3
"""Add nearest-50 rounding for all receipt amount displays."""
with open('/root/psvibe-sales-bot/bot/handlers/sales.py') as f:
    src = f.read()

# Find the section where receipt is built - right before # ── Build discount/bonus lines
# Insert rounding for all display amounts before the discount lines
old_marker = '    # ── Build discount/bonus lines for receipt ───────────────────────────────'

# Add a rounding block before this marker
round_block = """    # Round all display amounts to nearest 50 (voucher format --50/--00)
    def _r50(x): return round(x / 50) * 50 if x else 0
    game_amt = _r50(d.get("game_amt", game_amt))
    food_total = _r50(d.get("food_total", food_total))
    d_gross = _r50(d.get("gross_total", d_gross))
    discount = _r50(d.get("discount", discount))
    net_total = _r50(d.get("net_total", net_total))
    kpay = _r50(d.get("kpay", kpay))
    cash = _r50(d.get("cash", cash))

"""

src = src.replace(old_marker, round_block + old_marker, 1)

with open('/root/psvibe-sales-bot/bot/handlers/sales.py', 'w') as f:
    f.write(src)

try:
    compile(src, '/root/psvibe-sales-bot/bot/handlers/sales.py', 'exec')
    print('Syntax OK')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
    lines = src.split('\n')
    for i in range(max(0, e.lineno - 3), min(len(lines), e.lineno + 2)):
        print(f'  {i+1}: {lines[i].rstrip()[:120]}')
