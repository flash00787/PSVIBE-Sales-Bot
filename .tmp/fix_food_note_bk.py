import ast

with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'r') as f:
    c = f.read()

old = '    # Check if in food note console picker mode\n    if context.user_data.pop("_food_note_pick", False):\n        from bot.handlers.sales import cmd_session_food_order\n        target = {"id": choice, "member": "", "staff": "", "booking_id": ""}\n        return await cmd_session_food_order(update, context, target)'

new = '    # Check if in food note console picker mode\n    if context.user_data.pop("_food_note_pick", False):\n        from bot.handlers.sales import cmd_session_food_order\n        from bot import _psvibe_get_async\n        # Find linked booking_id for this console\n        _bk_id = ""\n        try:\n            _bks = await _psvibe_get_async("bookings") or []\n            if not isinstance(_bks, list):\n                _bks = _bks.get("bookings", []) if isinstance(_bks, dict) else []\n            for _b in _bks:\n                if (_b.get("status") in ("confirmed", "arrived", "in_use")\n                        and (_b.get("consoleId") or "").strip() == choice):\n                    _bk_id = str(_b.get("id", ""))\n                    break\n        except Exception as e:\n            logger.error("food_note booking lookup: %s", e)\n        target = {"id": choice, "member": "", "staff": "", "booking_id": _bk_id}\n        return await cmd_session_food_order(update, context, target)'

c = c.replace(old, new)

with open('/root/psvibe-sales-bot/bot/handlers/console.py', 'w') as f:
    f.write(c)

ast.parse(c)
print('SYNTAX OK')
