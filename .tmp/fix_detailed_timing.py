with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'r') as f:
    c = f.read()

# Add detailed timing for each step in step_end_session, between _t0 and the launch call
# Find specific lines and add timing

# After _t0 is set, add _t_step marker
c = c.replace(
    '_t0 = time.monotonic()\n    text = update.message.text.strip()',
    '_t0 = time.monotonic()\n    _ts = [_t0]\n    text = update.message.text.strip()'
)

# After end_booking_async - add timing check
c = c.replace(
    'logger.warning("CONSOLE_TIME end_booking: %dms", (time.monotonic() - _t3) * 1000)',
    'logger.warning("CONSOLE_TIME end_booking: %dms step_sofar=%dms", (time.monotonic() - _t3) * 1000, (time.monotonic() - _t0) * 1000)'
)

# After Telegram message send - add timing for where we are
old_msg = 'f"📝 Sales Voucher ဖွင့်နေသည်..."'
new_msg = old_msg + '\n    logger.warning("CONSOLE_TIME after_voucher_msg: %dms", (time.monotonic() - _t0) * 1000)'
c = c.replace(old_msg, new_msg, 1)

# After _delete_session_game
c = c.replace(
    '_delete_session_game(cid)',
    '_delete_session_game(cid)\n    logger.warning("CONSOLE_TIME after_delete_session_game: %dms", (time.monotonic() - _t0) * 1000)'
)

# After bookings fetch
c = c.replace(
    'logger.warning("CONSOLE_TIME bookings_fetch: %dms", (time.monotonic() - _t4) * 1000)',
    'logger.warning("CONSOLE_TIME bookings_fetch: %dms step_sofar=%dms", (time.monotonic() - _t4) * 1000, (time.monotonic() - _t0) * 1000)'
)

with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'w') as f:
    f.write(c)
print('DETAILED TIMING ADDED')
