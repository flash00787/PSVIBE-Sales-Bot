import ast

with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'r') as f:
    c = f.read()

# 1. Add time import
c = c.replace('import asyncio, logging, re, json', 'import asyncio, logging, re, json, time')

# 2. Add _t0 in step_end_session
c = c.replace(
    '    """User picked a console to end \u2014 find its booking and end it."""\n    text = update.message.text.strip()',
    '    """User picked a console to end \u2014 find its booking and end it."""\n    _t0 = time.monotonic()\n    text = update.message.text.strip()'
)

# 3. Add timing after end_booking
c = c.replace(
    '    ok = await end_booking_async(bk_id) if bk_id else False\n    if not ok:',
    '    ok = await end_booking_async(bk_id) if bk_id else False\n    logger.warning("step_t end_booking: %dms", (time.monotonic() - _t0) * 1000)\n    if not ok:'
)

# 4. Add timing after voucher message send
c = c.replace(
    'f"{ssd_warn}",\n        parse_mode="HTML",\n    )',
    'f"{ssd_warn}",\n        parse_mode="HTML",\n    )\n    logger.warning("step_t after_voucher_msg: %dms", (time.monotonic() - _t0) * 1000)'
)

# 5. Add timing after _delete_session_game
c = c.replace(
    '_delete_session_game(cid)\n    # Try to find linked booking_id',
    '_delete_session_game(cid)\n    logger.warning("step_t after_delete_game: %dms", (time.monotonic() - _t0) * 1000)\n    # Try to find linked booking_id'
)

# 6. Add timing after bookings fetch
c = c.replace(
    '    # \u2500\u2500 CashBack Coupon: Auto-generate via MySQL API \u2500\u2500',
    '    logger.warning("step_t after_bookings_fetch: %dms", (time.monotonic() - _t0) * 1000)\n    # \u2500\u2500 CashBack Coupon: Auto-generate via MySQL API \u2500\u2500'
)

# 7. Add timing before launch and total timing at end
# Replace the final return
old_return = '    from bot.handlers.sales import launch_session_sale\n    return await launch_session_sale(update, context, cid, mbr, total_mins, session_staff,\n                                     booking_id=_linked_bk_id)'

new_return = '    from bot.handlers.sales import launch_session_sale\n    _t5 = time.monotonic()\n    _pre_ms = (_t5 - _t0) * 1000\n    _ls_result = await launch_session_sale(update, context, cid, mbr, total_mins, session_staff, booking_id=_linked_bk_id)\n    _total_ms = (time.monotonic() - _t0) * 1000\n    logger.warning("CONSOLE_TIME step_end_session: pre_sale=%dms sale=%dms total=%dms", _pre_ms, _total_ms - _pre_ms, _total_ms)\n    return _ls_result'

c = c.replace(old_return, new_return)

with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'w') as f:
    f.write(c)

ast.parse(c)
print('SYNTAX OK')
