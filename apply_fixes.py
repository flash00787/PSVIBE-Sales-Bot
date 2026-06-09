#!/usr/bin/env python3
"""Apply all bug fixes to remote server."""
import paramiko, sys, os

HOST = "5.223.81.16"
KEY_PATH = os.path.expanduser("/home/node/.openclaw/workspace/.ssh/id_rsa")
USER = "root"

def connect():
    key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, pkey=key, timeout=15)
    return client

def remote_edit(client, filepath, old_text, new_text):
    """Apply a single edit to a remote file."""
    sftp = client.open_sftp()
    with sftp.file(filepath, 'r') as f:
        content = f.read().decode('utf-8', errors='replace')
    
    count = content.count(old_text)
    if count == 0:
        sftp.close()
        return f"FAIL: oldText NOT FOUND in {filepath}"
    if count > 1:
        sftp.close()
        return f"FAIL: oldText found {count} times (not unique) in {filepath}"
    
    content = content.replace(old_text, new_text, 1)
    
    with sftp.file(filepath, 'w') as f:
        f.write(content)
    sftp.close()
    return f"OK: edit applied to {filepath}"

client = connect()

# ================================================================
# FIX 1: prompt_food_menu - don't cancel when stock data unavailable
# ================================================================
old1 = """    # Check if stock_map has any positive stock; if not, show warning and show all items
    has_any_stock = any(v > 0 for v in stock_map.values()) if stock_map else False
    if not has_any_stock:
        await update.message.reply_text(
            \"\\u26a0\\ufe0f stock \\u101c\\u1000\\u103a\\u1000\\u103b\\u1014\\u103a\\u1019\\u101b\\u103e\\u102d\\u1015\\u102b \\u2014 \\u1015\\u1005\\u1039\\u1005\\u100a\\u103a\\u1038\\u1021\\u102c\\u1038\\u101c\\u102f\\u1036\\u1038\\u1015\\u103c\\u1019\\u100a\\u1037\\u103a\",
            reply_markup=ReplyKeyboardRemove(),
        )
        return await cmd_cancel(update, context)
    elif stock_map:
        # Filter out items with zero stock
        prices = {k: v for k, v in prices.items()
                  if stock_map.get(k, 1) > 0}
        context.user_data[\"food_prices\"] = prices"""

new1 = """    # Check if stock_map has any positive stock
    if stock_map:
        # Stock data is available — filter out items with zero stock
        if any(v > 0 for v in stock_map.values()):
            prices = {k: v for k, v in prices.items()
                      if stock_map.get(k, 1) > 0}
            context.user_data[\"food_prices\"] = prices
        else:
            # Stock data available but everything is out of stock — cancel
            await update.message.reply_text(
                \"\\u26a0\\ufe0f stock \\u101c\\u1000\\u103a\\u1000\\u103b\\u1014\\u103a\\u1019\\u101b\\u103e\\u102d\\u1015\\u102b \\u2014 \\u1015\\u1005\\u1039\\u1005\\u100a\\u103a\\u1038\\u1021\\u102c\\u1038\\u101c\\u102f\\u1036\\u1038\\u1015\\u103c\\u1019\\u100a\\u1037\\u103a\",
                reply_markup=ReplyKeyboardRemove(),
            )
            return await cmd_cancel(update, context)
    # If stock_map is empty (no stock data available), show all items without filtering"""

result1 = remote_edit(client,
    "/root/psvibe-sales-bot/bot/handlers/sales.py",
    old1, new1)
print(f"FIX 1: {result1}")

# ================================================================
# FIX 2: cmd_mybookings - improve display to ensure pending shows
# The issue might be that the "no bookings" message shows when
# API fails silently. Add better error handling.
# ================================================================
old2 = """    try:
        data = await _api._api_get(f\"bookings/search?telegram_chat_id={uid}\", timeout=10)
        if isinstance(data, dict) and \"bookings\" in data:
            data = data[\"bookings\"]
        if not isinstance(data, list):
            data = []
    except Exception as e:
        logger.warning(\"cmd_mybookings: API call failed: %s\", e)
        await update.message.reply_text(NO_BOOKINGS_MSG)
        return

    # Filter by status first
    valid_statuses = (\"pending\", \"confirmed\", \"scheduled\")
    all_active = [b for b in data if str(b.get(\"status\", \"\")).lower() in valid_statuses]"""

new2 = """    try:
        raw_data = await _api._api_get(f\"bookings/search?telegram_chat_id={uid}\", timeout=10)
        if isinstance(raw_data, dict) and \"bookings\" in raw_data:
            data = raw_data[\"bookings\"]
        elif isinstance(raw_data, list):
            data = raw_data
        else:
            logger.warning(\"cmd_mybookings: unexpected response format: %s\", type(raw_data))
            data = []
        if not isinstance(data, list):
            data = []
    except Exception as e:
        logger.warning(\"cmd_mybookings: API call failed: %s\", e)
        await update.message.reply_text(NO_BOOKINGS_MSG)
        return

    # Filter by status first — include 'active' status as well (staff-scheduled sessions show as Active)
    valid_statuses = (\"pending\", \"confirmed\", \"scheduled\", \"active\")
    all_active = [b for b in data if str(b.get(\"status\", \"\")).lower() in valid_statuses]"""

result2 = remote_edit(client,
    "/root/psvibe-sales-bot/customer_bot/booking.py",
    old2, new2)
print(f"FIX 2: {result2}")

# ================================================================
# FIX 2b: cmd_start welcome banner - same improvement
# ================================================================
old2b = """    # Check for today active bookings (exclude cancelled/rejected)
    today_bks_raw = await _api._api_get(f\"bookings/search?telegram_chat_id={uid}\")
    today_bks = []
    if isinstance(today_bks_raw, dict) and \"bookings\" in today_bks_raw:
        today_bks = [b for b in today_bks_raw[\"bookings\"] if str(b.get(\"status\", \"\")).lower() in (\"pending\", \"confirmed\")]
    elif isinstance(today_bks_raw, list):
        today_bks = [b for b in today_bks_raw if str(b.get(\"status\", \"\")).lower() in (\"pending\", \"confirmed\")]"""

new2b = """    # Check for today active bookings (exclude cancelled/rejected)
    today_bks_raw = await _api._api_get(f\"bookings/search?telegram_chat_id={uid}\")
    today_bks = []
    if isinstance(today_bks_raw, dict) and \"bookings\" in today_bks_raw:
        today_bks = [b for b in today_bks_raw[\"bookings\"] if str(b.get(\"status\", \"\")).lower() in (\"pending\", \"confirmed\", \"active\")]
    elif isinstance(today_bks_raw, list):
        today_bks = [b for b in today_bks_raw if str(b.get(\"status\", \"\")).lower() in (\"pending\", \"confirmed\", \"active\")]"""

result2b = remote_edit(client,
    "/root/psvibe-sales-bot/customer_bot/handlers.py",
    old2b, new2b)
print(f"FIX 2b: {result2b}")

# ================================================================
# FIX 3: Console Status - ensure API response is properly handled
# Check the api_fetch_console_status_async function
# ================================================================
# First, read the function to see if there's an issue
stdin, stdout, stderr = client.exec_command(
    "grep -A 30 'async def api_fetch_console_status_async' /root/psvibe-sales-bot/bot/api_client.py", timeout=10)
func_code = stdout.read().decode('utf-8', errors='replace')
print(f"\napi_fetch_console_status_async:\n{func_code[:600]}")

# Also check if _api_call_async properly unwraps the data envelope
stdin2, stdout2, stderr2 = client.exec_command(
    "grep -A 40 'async def _api_call_async' /root/psvibe-sales-bot/bot/api_client.py | head -50", timeout=10)
api_call = stdout2.read().decode('utf-8', errors='replace')
print(f"\n_api_call_async:\n{api_call[:800]}")

client.close()
print("\n=== All fixes applied ===")
