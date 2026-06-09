#!/usr/bin/env python3
"""Fix missing _replit_get_async/_replit_patch_async import in admin_bookings.py.

These functions are used in the cmd_admin_bookings and _do_booking_action paths
but were never imported — causes NameError silently stuck.
"""
FILE = "/root/psvibe-sales-bot/bot/handlers/admin_bookings.py"
with open(FILE) as f:
    code = f.read()

# The current import block from bot
# Need to add _replit_get_async and _replit_patch_async to the from bot import
old_block = "from bot import (\n    CUSTOMER_BOT_TOKEN,     \n    check_disc_session_conflict,  get_consoles_with_game, get_consoles_with_game_async,\n    now_mmt, show_admin_menu,\n)"
new_block = "from bot import (\n    CUSTOMER_BOT_TOKEN,     \n    _replit_get_async, _replit_patch_async,\n    check_disc_session_conflict,  get_consoles_with_game, get_consoles_with_game_async,\n    now_mmt, show_admin_menu,\n)"

if old_block in code:
    code = code.replace(old_block, new_block, 1)
    with open(FILE, "w") as f:
        f.write(code)
    compile(code, FILE, "exec")
    print("✅ admin_bookings.py: _replit_get_async + _replit_patch_async imported")
else:
    print("❌ Pattern 1 not found, trying alternative...")
    # Try the raw text without formatting
    import textwrap
    alt_old = textwrap.dedent("""\
        from bot import (
            CUSTOMER_BOT_TOKEN,     
            check_disc_session_conflict,  get_consoles_with_game, get_consoles_with_game_async,
            now_mmt, show_admin_menu,
        )""")
    alt_new = textwrap.dedent("""\
        from bot import (
            CUSTOMER_BOT_TOKEN,     
            _replit_get_async, _replit_patch_async,
            check_disc_session_conflict,  get_consoles_with_game, get_consoles_with_game_async,
            now_mmt, show_admin_menu,
        )""")
    if alt_old in code:
        code = code.replace(alt_old, alt_new, 1)
        with open(FILE, "w") as f:
            f.write(code)
        compile(code, FILE, "exec")
        print("✅ admin_bookings.py: fixed (alt pattern)")
    else:
        # Direct edit approach
        idx = code.find("CUSTOMER_BOT_TOKEN,")
        if idx >= 0:
            print(f"Found CUSTOMER_BOT_TOKEN at {idx}")
            # Find the closing parenthesis of the import block
            end_idx = code.find(")", idx)
            block = code[idx:end_idx]
            print(f"Block: {repr(block)}")
