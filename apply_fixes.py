import sys

path = '/root/psvibe-sales-bot/bot/__init__.py'
with open(path) as f:
    content = f.read()
    lines = content.split('\n')

# ── FIX 1: Add BTN_ATTEND_DONE and BTN_ATTEND_SKIP after BTN_NO_MORE ──
# Line after 'BTN_NO_MORE   = No More Payments' (approx line 1297 in original)
for i, line in enumerate(lines):
    if line.strip().startswith('BTN_NO_MORE'):
        # Insert after this line
        insert_pos = i + 1
        break

attendance_btns = [
    '',
    '# Attendance flow buttons',
    'BTN_ATTEND_DONE = ✅ ပြီးပါပြီ',
    'BTN_ATTEND_SKIP = ⏭ Skip',
]

for btn_line in reversed(attendance_btns):
    lines.insert(insert_pos, btn_line)

print(f'FIX 1: Added BTN_ATTEND_DONE and BTN_ATTEND_SKIP after line {insert_pos}')

# ── FIX 2: Add category constants after NAV_ROW ──
# Find NAV_ROW line
for i, line in enumerate(lines):
    if line.strip().startswith('NAV_ROW'):
        nav_pos = i + 1
        break

category_constants = [
    '',
    '# ── Finance Category Lists ──',
    'OPEX_CATEGORIES = [',
    '    လစာ, ငှားရမ်းခ, မီတာခ, အင်တာနက်,',
    '    ပြုပြင်စရိတ်, ရုံးသုံးစရိတ်, အခြား,',
    ']',
    'PAY_METHODS = [Cash, KPay, WavePay, Bank Transfer]',
    'ASSET_CATEGORIES = [Furniture, Equipment, Electronics, Vehicle, Gaming Console, Other]',
    'PREPAID_CATEGORIES = [Rent, Insurance, Subscription, Software License, Other]',
    'FINANCE_ACCOUNTS = [Cash, KPay, WavePay, CB Bank, AYA Bank, Other]',
    'CAPITAL_ACCOUNTS = [Cash, KPay, WavePay, CB Bank, AYA Bank, Other]',
    '_SHARE_ROLES = [Owner, Partner, Investor, Staff]',
    '',
    '# Business start date for depreciation calculations',
    'from datetime import datetime as _dt',
    '_BIZ_START = _dt(2023, 1, 1)',
]

for cat_line in reversed(category_constants):
    lines.insert(nav_pos, cat_line)

print(f'FIX 2: Added category constants after line {nav_pos}')

# ── FIX 3: Add _pin_then and fetch_payment_methods before import handlers ──
# Find the last import line or the 'from bot.handlers import *' line
for i in range(len(lines) - 1, -1, -1):
    if 'from bot.handlers import *' in lines[i]:
        import_pos = i
        break

new_funcs = [
    '',
    '',
    '# ── PIN-then-action wrapper ──',
    'async def _pin_then(after: str, label: str, update, context):',
    '    Store target action, prompt for PIN, return ADMIN_PIN state.',
    '    context.user_data[_after_pin] = after',
    '    await update.message.reply_text(',
    '        f🔐 *{label}* PIN ရိုက်ထည့်ပါ -,',
    '        parse_mode=Markdown,',
    '        reply_markup=ReplyKeyboardRemove(),',
    '    )',
    '    return ADMIN_PIN',
    '',
    '',
    '# ── Payment Methods Fetcher ──',
    'def fetch_payment_methods():',
    '    Return list of payment method options, with API-backed fallback.',
    '    try:',
    '        data = _replit_get(sheets/payment-methods)',
    '        if isinstance(data, dict) and methods in data:',
    '            return data[methods]',
    '        if isinstance(data, list):',
    '            return data',
    '    except Exception:',
    '        pass',
    '    return list(PAY_METHODS)',
]

for func_line in reversed(new_funcs):
    lines.insert(import_pos, func_line)

print(f'FIX 3: Added _pin_then and fetch_payment_methods before line {import_pos}')

# Write back
with open(path, 'w') as f:
    f.write('\n'.join(lines))

print(f'Done. File now has {len(lines)} lines.')
