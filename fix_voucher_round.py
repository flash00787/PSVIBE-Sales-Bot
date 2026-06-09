#!/usr/bin/env python3
"""Add nearest-50 rounding to receipt amounts."""
with open('/root/psvibe-sales-bot/bot/handlers/sales.py') as f:
    src = f.read()

# 1. Add _round_50 helper function before _build_payment_receipt_lines
old_fn = 'def _build_payment_receipt_lines(kpay: int, cash: int, payments: dict) -> str:'
new_fn = 'def _round_50(amt): return round(amt / 50) * 50\n\n\n' + old_fn
src = src.replace(old_fn, new_fn, 1)
print('Added _round_50 helper')

# 2. Replace amount display in the for loop
old_amt = 'lines.append(f"  {ico} {method}: *{int(amt):,} Ks*")'
new_amt = 'lines.append(f"  {ico} {method}: *{_round_50(int(amt)):,} Ks*")'
src = src.replace(old_amt, new_amt, 1)
print('Applied _round_50 to payment lines')

# 3. Also round the default fallback amounts
old_def = 'return f"' + chr(128) + ' Kpay: *{kpay:,} Ks*  |  ' + chr(128) + ' Cash: *{cash:,} Ks*"'
# Find and replace the default return
if old_def in src:
    new_def = 'return f"' + chr(128) + ' Kpay: *{_round_50(kpay):,} Ks*  |  ' + chr(128) + ' Cash: *{_round_50(cash):,} Ks*"'
    src = src.replace(old_def, new_def, 1)
    print('Applied _round_50 to default line')

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
