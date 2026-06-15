import re

with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'r') as f:
    content = f.read()

# Add timing import at top
if 'import time' not in content:
    content = content.replace(
        'import asyncio, logging, re, json',
        'import asyncio, logging, re, json, time'
    )

# Add _t0 after docstring
old = 'text = update.message.text.strip()'
new = '_t0 = time.monotonic()\n    text = update.message.text.strip()'
content = content.replace(old, new, 1)

# Add timing before end_booking
old3 = 'ok = await end_booking_async(bk_id) if bk_id else False'
new3 = '_t_endbk = time.monotonic()\n    ok = await end_booking_async(bk_id) if bk_id else False\n    logger.warning("TIMING end_booking: %dms", (time.monotonic() - _t_endbk) * 1000)'
content = content.replace(old3, new3, 1)

# Add timing to bookings fetch
old4 = '_bks = await _psvibe_get_async(f"bookings?memberId={mbr}") or []'
new4 = '_t_bk = time.monotonic()\n        _bks = await _psvibe_get_async(f"bookings?memberId={mbr}") or []\n        logger.warning("TIMING bookings_fetch: %dms", (time.monotonic() - _t_bk) * 1000)'
content = content.replace(old4, new4, 1)

# Add timing before launch_session_sale + total timing
old5 = '''    from bot.handlers.sales import launch_session_sale
    return await launch_session_sale(update, context, cid, mbr, total_mins, session_staff,
                                     booking_id=_linked_bk_id)'''

new5 = '''    _t_launch = time.monotonic()
    _t_pre = (_t_launch - _t0) * 1000
    from bot.handlers.sales import launch_session_sale
    _result = await launch_session_sale(update, context, cid, mbr, total_mins, session_staff, booking_id=_linked_bk_id)
    _t_total = (time.monotonic() - _t0) * 1000
    logger.warning("TIMING TOTAL step_end_session: pre_sale=%dms sale=%dms total=%dms", _t_pre, _t_total - _t_pre, _t_total)
    return _result'''

content = content.replace(old5, new5, 1)

with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'w') as f:
    f.write(content)
print('INSTRUMENTED OK')
