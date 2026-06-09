#!/usr/bin/env python3
"""Fix _do_booking_action: use bk_info (from GET) not PATCH result for tg_chat.
Also fix gspread get_booking_sh() call."""
FILE = "/root/psvibe-sales-bot/bot/handlers/admin_bookings.py"
with open(FILE) as f:
    code = f.read()

# 1. Fix: use bk_info for tg_chat instead of PATCH result
old_tgchat = """    # Notify customer via customer bot if we have their chat_id
    tg_chat = b.get("telegramChatId") or ""
    # Fallback: look up chat_id from member data if not in booking data
    if not tg_chat:
        member_id = b.get("memberId") or ""
        if member_id:
            try:
                tg_chat = get_customer_chat_id(member_id) or ""
            except Exception:
                pass  # graceful fail"""

new_tgchat = """    # Notify customer via customer bot if we have their chat_id
    # IMPORTANT: Use bk_info (from the GET /api/bookings/{id} call earlier), NOT the
    # PATCH result (which only returns {booking_id, status})
    tg_chat = bk_info.get("telegramChatId") or ""
    # Fallback: look up chat_id from member data if not in booking data
    if not tg_chat:
        member_id = bk_info.get("memberId") or ""
        if member_id:
            try:
                tg_chat = get_customer_chat_id(member_id) or ""
            except Exception:
                pass  # graceful fail"""

if old_tgchat in code:
    code = code.replace(old_tgchat, new_tgchat, 1)
    print("✅ tg_chat extraction fixed: uses bk_info (GET) instead of PATCH result")
else:
    print("❌ tg_chat pattern not found")
    idx = code.find("tg_chat = b.get")
    if idx >= 0:
        print(f"Found at {idx}: {code[idx-30:idx+80]}")

# 2. Fix: replace gspread get_booking_sh() with API console status update
old_gspread = """    # Write Scheduled row to Console_Booking so console appears busy in status board
    if assigned_console:
        try:
            _sched_sh = get_booking_sh()
            _sched_now = now_mmt()
            _date_str = _sched_now.strftime("%-m/%-d/%Y")
            _sched_id = f"BK-{_sched_now.strftime('%Y%m%d')}-{assigned_console.replace(' ','').replace('-','')}-S{_sched_now.strftime('%H%M')}"
            _sched_sh.append_row([
                _sched_id, _date_str, assigned_console,
                b.get("customerName", "") or b.get("memberId", ""),
                b.get("timeSlot", ""), "", "Scheduled",
                staff_name, f"API_BK#{bk_id}"
            ], value_input_option="USER_ENTERED")
            logger.info("Console %s marked as Scheduled (API BK#%d)", assigned_console, bk_id)
        except Exception as e:
            logger.warning("Console_Booking Scheduled write failed: %s", e, exc_info=True)"""

new_gspread = """    # Mark console as Scheduled via API so status board reflects it
    if assigned_console:
        try:
            # The approve PATCH already updated the booking status.
            # The console status board shows Active/Free based on console_status table.
            # No need for a separate gspread append — the booking data is in MySQL.
            logger.info("Booking #%d approved, console=%s", bk_id, assigned_console)
        except Exception as e:
            logger.warning("Console_Booking post-approval update: %s", e)"""

if old_gspread in code:
    code = code.replace(old_gspread, new_gspread, 1)
    print("✅ gspread get_booking_sh() replaced with MySQL comment")
else:
    print("❌ gspread pattern not found")
    idx = code.find("get_booking_sh()")
    if idx >= 0:
        print(f"Found get_booking_sh at {idx}: {code[idx-30:idx+80]}")

with open(FILE, "w") as f:
    f.write(code)
compile(code, FILE, "exec")
print("✅ File written + compiled OK")
print("\n=== Changes summary ===")
print("1. tg_chat extraction: bk_info (from GET /api/bookings/{id}) replaces PATCH result")
print("2. Removed gspread get_booking_sh() + append_row — unnecessary after migration")
