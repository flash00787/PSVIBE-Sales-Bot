#!/usr/bin/env python3
"""Fix booking.py: missing imports + sheets/consoles old path."""
FILE = "/root/psvibe-sales-bot/bot/handlers/booking.py"
with open(FILE) as f:
    code = f.read()

# 1. Add _replit_get_async + _replit_patch_async to imports
# Find the closing paren of the from bot import block
old_import_block = (
    'from bot import (\n'
    '    BOOK_CONSOLE, BOOK_DUP_WARN, BOOK_GAME, BOOK_LINK, BOOK_MEMBER,\n'
    '    BOOK_MINS, BTN_BACK, BTN_BACK_MAIN, BTN_BOOK_PROCEED, BTN_CANCEL,\n'
    '    BTN_NO_RESELECT, BTN_SBK_CONFIRMED, BTN_SBK_CONFIRM_BOOK,\n'
    '    BTN_SBK_CUSTOM, BTN_SBK_NEW, BTN_SBK_SKIP_GAME, BTN_SBK_SKIP_PHONE,\n'
    '    BTN_SBK_WAITLIST, BTN_SKIP_GAME, BTN_SKIP_TIMER, BTN_SSD_TRANSFER,\n'
    '    CONSOLE_MENU, MAIN_MENU, N8N_BOOKING_WEBHOOK, SBK_CONFIRM,\n'
    '    SBK_CONSOLE, SBK_CUST_NAME, SBK_DATE, SBK_DUR, SBK_GAME, SBK_TIME,\n'
    '    SSD_XFER_SSD, STAFF_NOTIFY_CHAT, VALID_CONSOLES,\n'
    '    add_console_game, add_console_game_async, _delete_session_game,     calc_duration,\n'
    '    check_disc_session_conflict, cmd_cancel, create_booking, create_booking_async,\n'
    '    fetch_console_games, fetch_console_games_async, fetch_console_status, fetch_games, fetch_games_async,\n'
    '    fetch_members, fetch_staff, get_consoles_with_game, get_consoles_with_game_async,\n'
    '    get_games_on_console, get_games_on_console_async, now_mmt, show_admin_menu, show_console_menu,\n'
    '    show_main_menu, today_str,\n'
    '    fetch_members_async,\n'
    ')'
)

new_import_block = (
    'from bot import (\n'
    '    BOOK_CONSOLE, BOOK_DUP_WARN, BOOK_GAME, BOOK_LINK, BOOK_MEMBER,\n'
    '    BOOK_MINS, BTN_BACK, BTN_BACK_MAIN, BTN_BOOK_PROCEED, BTN_CANCEL,\n'
    '    BTN_NO_RESELECT, BTN_SBK_CONFIRMED, BTN_SBK_CONFIRM_BOOK,\n'
    '    BTN_SBK_CUSTOM, BTN_SBK_NEW, BTN_SBK_SKIP_GAME, BTN_SBK_SKIP_PHONE,\n'
    '    BTN_SBK_WAITLIST, BTN_SKIP_GAME, BTN_SKIP_TIMER, BTN_SSD_TRANSFER,\n'
    '    CONSOLE_MENU, MAIN_MENU, N8N_BOOKING_WEBHOOK, SBK_CONFIRM,\n'
    '    SBK_CONSOLE, SBK_CUST_NAME, SBK_DATE, SBK_DUR, SBK_GAME, SBK_TIME,\n'
    '    SSD_XFER_SSD, STAFF_NOTIFY_CHAT, VALID_CONSOLES,\n'
    '    _replit_get_async, _replit_patch_async,\n'
    '    add_console_game, add_console_game_async, _delete_session_game,     calc_duration,\n'
    '    check_disc_session_conflict, cmd_cancel, create_booking, create_booking_async,\n'
    '    fetch_console_games, fetch_console_games_async, fetch_console_status, fetch_games, fetch_games_async,\n'
    '    fetch_members, fetch_staff, get_consoles_with_game, get_consoles_with_game_async,\n'
    '    get_games_on_console, get_games_on_console_async, now_mmt, show_admin_menu, show_console_menu,\n'
    '    show_main_menu, today_str,\n'
    '    fetch_members_async,\n'
    ')'
)

if old_import_block in code:
    code = code.replace(old_import_block, new_import_block, 1)
    print("✅ booking.py: _replit_get_async/_replit_patch_async added to imports")
else:
    print("❌ Import block pattern not found, trying alt...")
    # The actual file might have different spacing
    idx = code.find("BOOK_CONSOLE")
    if idx >= 0:
        # Find the block from 'from bot' to the closing paren
        start = code.rfind("from bot", 0, idx)
        end = code.find(")", start) + 1
        block = code[start:end]
        print(f"Found import block: {repr(block[:200])}...")
        # Just add the import after STAFF_NOTIFY_CHAT
        old_line = "    SSD_XFER_SSD, STAFF_NOTIFY_CHAT, VALID_CONSOLES,"
        if old_line in block:
            code = code.replace(old_line + "\n", old_line + "\n    _replit_get_async, _replit_patch_async,\n", 1)
            print("✅ Added imports via inline fix")

# 2. Replace sheets/consoles with fetch_console_status()
old_sheets = 'data = await _replit_get_async("sheets/consoles") or {}'
new_sheets = 'data = {"consoles": [{"id": c["id"], "type": c.get("type",""), "liveStatus": c.get("status","Free")} for c in fetch_console_status()]}'

if old_sheets in code:
    code = code.replace(old_sheets, new_sheets, 1)
    print("✅ booking.py: sheets/consoles → fetch_console_status()")
else:
    print("❌ sheets/consoles pattern not found")

with open(FILE, "w") as f:
    f.write(code)
compile(code, FILE, "exec")
print("✅ booking.py: File written + compiled OK")

# ===== FIX 3: sales.py launch_session_sale missing _replit_get_async import =====
SALES_FILE = "/root/psvibe-sales-bot/bot/handlers/sales.py"
with open(SALES_FILE) as f:
    sales_code = f.read()

old_sales = '    stock_map: dict = {}\n    try:\n        inv_data = await _replit_get_async("stock/current")'
new_sales = '    stock_map: dict = {}\n    try:\n        from bot.api_client import _replit_get_async\n        inv_data = await _replit_get_async("stock/current")'

if old_sales in sales_code:
    sales_code = sales_code.replace(old_sales, new_sales, 1)
    with open(SALES_FILE, "w") as f:
        f.write(sales_code)
    compile(sales_code, SALES_FILE, "exec")
    print("✅ sales.py: launch_session_sale import fixed")
else:
    print("❌ sales.py: pattern not found")
    idx = sales_code.find('inv_data = await _replit_get_async("stock/current")')
    if idx >= 0:
        print(f"  Found at {idx}: {sales_code[idx-100:idx+100]}")
