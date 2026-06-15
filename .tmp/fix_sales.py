import sys

with open('/root/psvibe-sales-bot/bot/handlers/sales.py', 'r') as f:
    content = f.read()

old = '''    is_guest = member_id in ("Guest", "0 (Guest)", "")

    base_rate  = await fetch_base_rate_async()
    # For combined cids (e.g. "C-09+C-10") multiplier lookup returns 1.0 — that's fine
    # because pre_effective_mins already encodes the per-console multipliers.
    multiplier = await fetch_console_multiplier_async(cid) if "+" not in cid else 1.0

    # Fetch food prices filtered by stock
    food_prices = await fetch_food_prices_async()
    stock_map: dict = {}
    try:
        from bot import _psvibe_get_async
        inv_data = await _psvibe_get_async("stock/current")
        if inv_data and isinstance(inv_data, dict):
            stock_map = {i.get("item_name", ""): max(0, i.get("quantity", 0))
                         for i in inv_data.get("stock", []) if isinstance(i, dict) and i.get("item_name")}
            # Only filter if there is actually some stock available
            if any(v > 0 for v in stock_map.values()):
                food_prices = {k: v for k, v in food_prices.items()
                               if stock_map.get(k, 0) > 0}
    except Exception as e:
        logger.warning("launch_session_sale: stock fetch failed, showing all items: %s", e)'''

new = '''    is_guest = member_id in ("Guest", "0 (Guest)", "")

    # Parallelize independent API calls for speed
    from bot import _psvibe_get_async
    if "+" not in cid:
        base_rate, multiplier, food_prices = await asyncio.gather(
            fetch_base_rate_async(),
            fetch_console_multiplier_async(cid),
            fetch_food_prices_async(),
        )
    else:
        base_rate, food_prices = await asyncio.gather(
            fetch_base_rate_async(),
            fetch_food_prices_async(),
        )
        multiplier = 1.0

    # Fetch stock (separate try/except for graceful degradation)
    stock_map: dict = {}
    try:
        inv_data = await _psvibe_get_async("stock/current")
        if inv_data and isinstance(inv_data, dict):
            stock_map = {i.get("item_name", ""): max(0, i.get("quantity", 0))
                         for i in inv_data.get("stock", []) if isinstance(i, dict) and i.get("item_name")}
            # Only filter if there is actually some stock available
            if any(v > 0 for v in stock_map.values()):
                food_prices = {k: v for k, v in food_prices.items()
                               if stock_map.get(k, 0) > 0}
    except Exception as e:
        logger.warning("launch_session_sale: stock fetch failed, showing all items: %s", e)'''

if old in content:
    content = content.replace(old, new, 1)
    with open('/root/psvibe-sales-bot/bot/handlers/sales.py', 'w') as f:
        f.write(content)
    print('REPLACED OK')
else:
    print('OLD TEXT NOT FOUND')
    # debug
    idx = content.find('base_rate  = await fetch_base_rate_async()')
    if idx >= 0:
        print(f'Found at {idx}')
        print(repr(content[idx:idx+300]))
    else:
        print('Not found anywhere')
        # Show context around 'is_guest'
        idx2 = content.find('is_guest = member_id in')
        if idx2 >= 0:
            print(f'is_guest at {idx2}:')
            print(repr(content[idx2:idx2+500]))
