import ast

with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'r') as f:
    c = f.read()

# ============ A. Timing instrumentation (from earlier fix) ============

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

# 7. Replace final return with timing
old_return = '    from bot.handlers.sales import launch_session_sale\n    return await launch_session_sale(update, context, cid, mbr, total_mins, session_staff,\n                                     booking_id=_linked_bk_id)'

new_return = '''    from bot.handlers.sales import launch_session_sale
    _t5 = time.monotonic()
    _pre_ms = (_t5 - _t0) * 1000
    _ls_result = await launch_session_sale(update, context, cid, mbr, total_mins, session_staff,
                                           booking_id=_linked_bk_id)
    _total_ms = (time.monotonic() - _t0) * 1000
    logger.warning("CONSOLE_TIME step_end_session: pre_sale=%dms sale=%dms total=%dms", _pre_ms, _total_ms - _pre_ms, _total_ms)
    return _ls_result'''

c = c.replace(old_return, new_return)

# ============ B. Add FOOD_NOTE button to Console Menu ============

# B1. Add import for BTN_FOOD_NOTE
c = c.replace(
    "from bot import BOT_VERSION, fetch_console_status, fetch_games, fetch_console_games,",
    "from bot import BOT_VERSION, BTN_FOOD_NOTE, fetch_console_status, fetch_games, fetch_console_games,"
)

# B2. Update show_console_menu keyboard - replace the old kb with food note
old_kb = '''    kb = [
        [BTN_START_SESSION,  BTN_END_SESSION],
        [BTN_STATUS_BOARD,   BTN_GAME_LIB_MENU],
        [BTN_CONSOLE_INSTALL, BTN_SSD_MANAGE],
        [BTN_BACK_MAIN],
    ]'''

new_kb = '''    kb = [
        [BTN_START_SESSION,  BTN_END_SESSION],
        [BTN_FOOD_NOTE,      BTN_STATUS_BOARD],
        [BTN_CONSOLE_INSTALL, BTN_SSD_MANAGE],
        [BTN_GAME_LIB_MENU,  BTN_BACK_MAIN],
    ]'''

c = c.replace(old_kb, new_kb)

# B3. Add Food Note handler in step_console_menu - before the final fallback
old_step_end = '''    if choice == BTN_SSD_MANAGE:
        from bot.handlers.ssd_disc import show_ssd_menu
        return await show_ssd_menu(update, context)
    return await show_console_menu(update, context)'''

new_step_end = '''    if choice == BTN_SSD_MANAGE:
        from bot.handlers.ssd_disc import show_ssd_menu
        return await show_ssd_menu(update, context)
    if choice == BTN_FOOD_NOTE:
        # Show active console list for food note
        try:
            cons = fetch_console_status()
        except Exception:
            cons = []
        active_consoles = [c for c in cons if c.get("id") and c.get("status", "").lower() in ("in use", "active")]
        if not active_consoles:
            await update.message.reply_text("❌ Active session ရှိသော Console မရှိပါ။")
            return await show_console_menu(update, context)
        msg = "📝 Food Note ထည့်ရန် Console ရွေးပါ:"
        kb = [[c["id"]] for c in active_consoles]
        kb.append([BTN_BACK])
        context.user_data["_food_note_pick"] = True
        await update.message.reply_text(
            msg,
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
        )
        return CONSOLE_MENU
    # Check if in food note console picker mode
    if context.user_data.pop("_food_note_pick", False):
        from bot.handlers.sales import cmd_session_food_order
        from bot import _psvibe_get_async
        # Find linked booking_id for this console
        _bk_id = ""
        try:
            _bks = await _psvibe_get_async("bookings") or []
            if not isinstance(_bks, list):
                _bks = _bks.get("bookings", []) if isinstance(_bks, dict) else []
            for _b in _bks:
                if (_b.get("status") in ("confirmed", "arrived", "in_use")
                        and (_b.get("consoleId") or "").strip() == choice):
                    _bk_id = str(_b.get("id", ""))
                    break
        except Exception as e:
            logger.error("food_note booking lookup: %s", e)
        target = {"id": choice, "member": "", "staff": "", "booking_id": _bk_id}
        return await cmd_session_food_order(update, context, target)
    return await show_console_menu(update, context)'''

c = c.replace(old_step_end, new_step_end)

with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'w') as f:
    f.write(c)

ast.parse(c)
print('SYNTAX OK')
