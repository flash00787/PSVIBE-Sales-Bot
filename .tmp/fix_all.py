import re

# Read ALL three files
files = {}

for path in ['/root/psvibe-sales-bot/bot/handlers/console.py',
             '/root/psvibe-sales-bot/bot/handlers/sales.py',
             '/root/psvibe-sales-bot/bot/app.py',
             '/root/psvibe-sales-bot/bot/__init__.py']:
    with open(path, 'r') as f:
        files[path] = f.read()

# ========== FILE 1: console.py ==========
c = files['/root/psvibe-sales-bot/bot/handlers/console.py']

# 1a: BTN_FOOD_SALE -> BTN_FOOD_NOTE
c = c.replace('BTN_FOOD_SALE', 'BTN_FOOD_NOTE')

# 1b: Add time import
if 'import time' not in c:
    c = c.replace('import asyncio, logging, re, json', 'import asyncio, logging, re, json, time')

# 1c: Fix coupon generation to use create_task (was reverted by git)
old_coupon_block = '''    # \u2500\u2500 CashBack Coupon: Auto-generate via MySQL API \u2500\u2500
    try:
        from bot.api_client import api_post
        member_id_for_coupon = mbr if mbr not in ("Guest", "0 (Guest)", "") else ""
        if member_id_for_coupon and total_mins > 0:
            gen_result = await asyncio.to_thread(
                api_post, "coupons/generate",
                {"member_id": member_id_for_coupon, "session_minutes": total_mins}
            )
            if gen_result and isinstance(gen_result, dict):
                cd = gen_result.get("coupon") or (gen_result.get("data") or {}).get("coupon")
                if cd and cd.get("code"):
                    context.user_data["_cashback_coupon"] = cd["code"]
                    context.user_data["_cashback_coupon_mins"] = cd.get("minutes", total_mins)
                    logger.warning("COUPON GEN OK: code=%s mins=%s member=%s", cd["code"], cd.get("minutes", total_mins), member_id_for_coupon)
                else:
                    logger.warning("COUPON GEN: no coupon in response: gen_result=%s", gen_result)
    except Exception as cb_e:
        logger.warning("Cashback coupon generation failed (non-critical): %s", cb_e)'''

new_coupon_block = '''    # \u2500\u2500 CashBack Coupon: Auto-generate via MySQL API \u2500\u2500
    try:
        from bot.api_client import api_post
        member_id_for_coupon = mbr if mbr not in ("Guest", "0 (Guest)", "") else ""
        if member_id_for_coupon and total_mins > 0:
            async def _gen_coupon_async():
                try:
                    gen_result = await asyncio.to_thread(
                        api_post, "coupons/generate",
                        {"member_id": member_id_for_coupon, "session_minutes": total_mins}
                    )
                    if gen_result and isinstance(gen_result, dict):
                        cd = gen_result.get("coupon") or (gen_result.get("data") or {}).get("coupon")
                        if cd and cd.get("code"):
                            context.user_data["_cashback_coupon"] = cd["code"]
                            context.user_data["_cashback_coupon_mins"] = cd.get("minutes", total_mins)
                            logger.warning("COUPON GEN OK: code=%s mins=%s member=%s", cd["code"], cd.get("minutes", total_mins), member_id_for_coupon)
                        else:
                            logger.warning("COUPON GEN: no coupon in response: gen_result=%s", gen_result)
                except Exception as e:
                    logger.warning("Cashback coupon generation failed: %s", e)
            asyncio.create_task(_gen_coupon_async())
    except Exception as cb_e:
        logger.warning("Cashback coupon generation failed (non-critical): %s", cb_e)'''

if old_coupon_block in c:
    c = c.replace(old_coupon_block, new_coupon_block)
    print('console: coupon create_task FIXED')
else:
    print('console: WARNING - old_coupon_block NOT found')
    idx = c.find('CashBack Coupon: Auto-generate')
    if idx >= 0:
        print(f'  Found at {idx}')
        print(f'  Context: {repr(c[idx:idx+300])}')

# 1d: Add timing instrumentation to step_end_session
# Find the step_end_session function and insert _t0
if '_t0 = time.monotonic()' not in c:
    c = c.replace(
        '    """User picked a console to end \\u2014 find its booking and end it."""\n    text = update.message.text.strip()',
        '    """User picked a console to end \\u2014 find its booking and end it."""\n    _t0 = time.monotonic()\n    _clog_start = time.monotonic()\n    text = update.message.text.strip()'
    )
    print('console: timing _t0 added')
else:
    print('console: timing _t0 already present')

# Replace the launch_session_sale line with timing
old_launch = '    from bot.handlers.sales import launch_session_sale\n    return await launch_session_sale(update, context, cid, mbr, total_mins, session_staff,\n                                     booking_id=_linked_bk_id)'
new_launch = '    from bot.handlers.sales import launch_session_sale\n    _t5 = time.monotonic()\n    _pre_ms = (_t5 - _t0) * 1000\n    _ls_result = await launch_session_sale(update, context, cid, mbr, total_mins, session_staff, booking_id=_linked_bk_id)\n    _total_ms = (time.monotonic() - _t0) * 1000\n    logger.warning("CONSOLE_TIME step_end_session: pre_sale=%dms sale=%dms total=%dms", _pre_ms, _total_ms - _pre_ms, _total_ms)\n    return _ls_result'
if old_launch in c:
    c = c.replace(old_launch, new_launch, 1)
    print('console: launch timing added')
else:
    print('console: launch timing NOT FOUND - trying alt')
    # Maybe indentation differs
    old_launch2 = '    from bot.handlers.sales import launch_session_sale\n    return await launch_session_sale(update, context, cid, mbr, total_mins, session_staff,\n        booking_id=_linked_bk_id)'
    if old_launch2 in c:
        c = c.replace(old_launch2, new_launch, 1)
        print('console: launch timing added (alt)')

files['/root/psvibe-sales-bot/bot/handlers/console.py'] = c

# ========== FILE 2: sales.py ==========
s = files['/root/psvibe-sales-bot/bot/handlers/sales.py']
# Verify parallel fix is in place
if 'asyncio.gather' in s:
    print('sales: parallel fix already present')
else:
    print('sales: WARNING - parallel fix missing!')

# ========== FILE 3: __init__.py ==========
i = files['/root/psvibe-sales-bot/bot/__init__.py']

# Check BTN_FOOD_SALE and BTN_FOOD_NOTE
if 'BTN_FOOD_NOTE' in i and 'BTN_FOOD_SALE' in i:
    print('init: BTN_FOOD already fixed')
else:
    print('init: WARNING - BTN_FOOD fix missing!')

# ========== FILE 4: app.py ==========
a = files['/root/psvibe-sales-bot/bot/app.py']
if 'BTN_FOOD_NOTE' in a:
    print('app: BTN_FOOD_NOTE handled')
else:
    print('app: WARNING - BTN_FOOD_NOTE missing')

# Write all files
for path, content in files.items():
    with open(path, 'w') as f:
        f.write(content)
print('ALL FILES WRITTEN')

# Verify syntax
import ast
for path in files:
    try:
        ast.parse(files[path])
        print(f'{path.split("/")[-1]}: syntax OK')
    except SyntaxError as e:
        print(f'{path.split("/")[-1]}: SYNTAX ERROR: {e}')
