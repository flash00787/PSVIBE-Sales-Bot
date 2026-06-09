#!/usr/bin/env python3
"""Fix _do_booking_action: use bk_info (from GET) for response msg + customer fields."""
FILE = "/root/psvibe-sales-bot/bot/handlers/admin_bookings.py"
with open(FILE) as f:
    code = f.read()

# Fix: replace ALL b.get(...) in response messages with bk_info.get(...)
# The PATCH response only returns {booking_id, status} — no customer fields!

# Replace the response message section
old_resp = """    # Unwrap {"data": {"booking": {...}}} envelope
    if isinstance(result, dict):
        data_outer = result.get("data") or {}
        if isinstance(data_outer, dict) and "booking" in data_outer:
            b = data_outer["booking"]
        elif isinstance(data_outer, dict) and "bookings" in data_outer:
            b = data_outer["bookings"][0] if data_outer["bookings"] else result
        else:
            b = result
    else:
        b = result
    if action == "approve":
        console_line = f"\\n🖥️ Console: <b>{assigned_console}</b>" if assigned_console else ""
        game_line    = f"\\n🕹️ Game: <b>{b.get('gameName') or '—'}</b>" if b.get("gameName") else ""
        msg = (
            f"✅ <b>Booking #{bk_id} Confirmed!</b>\\n"
            f"👤 {b.get('customerName', 'Unknown')}  📞 {b.get('phone', '-')}\\n"
            f"📅 {b.get('date', '?')}  🕐 {b.get('timeSlot', '?')}\\n"
            f"🎮 {b.get('consoleType', '-')}  ⏱️ {b.get('durationMins', '?')} mins"
            f"{game_line}{console_line}\\n"
            f"<i>Approved by {staff_name}</i>"
            f"{install_warn}"
        )
    else:
        msg = (
            f"❌ <b>Booking #{bk_id} Rejected</b>\\n"
            f"👤 {b.get('customerName', 'Unknown')}  📅 {b.get('date', '?')}  🕐 {b.get('timeSlot', '?')}\\n"
            f"<i>Rejected by {staff_name}</i>"
        )"""

new_resp = """    # Use bk_info (from GET /api/bookings/{id}) for all customer fields.
    # PATCH result only returns {booking_id, status} — no customer data.
    if action == "approve":
        console_line = f"\\n🖥️ Console: <b>{assigned_console}</b>" if assigned_console else ""
        game_line    = f"\\n🕹️ Game: <b>{bk_info.get('gameName') or '—'}</b>" if bk_info.get("gameName") else ""
        msg = (
            f"✅ <b>Booking #{bk_id} Confirmed!</b>\\n"
            f"👤 {bk_info.get('customerName', 'Unknown')}  📞 {bk_info.get('phone', '-')}\\n"
            f"📅 {bk_info.get('date', '?')}  🕐 {bk_info.get('timeSlot', '?')}\\n"
            f"🎮 {bk_info.get('consoleType', '-')}  ⏱️ {bk_info.get('durationMins', '?')} mins"
            f"{game_line}{console_line}\\n"
            f"<i>Approved by {staff_name}</i>"
            f"{install_warn}"
        )
    else:
        msg = (
            f"❌ <b>Booking #{bk_id} Rejected</b>\\n"
            f"👤 {bk_info.get('customerName', 'Unknown')}  📅 {bk_info.get('date', '?')}  🕐 {bk_info.get('timeSlot', '?')}\\n"
            f"<i>Rejected by {staff_name}</i>"
        )"""

if old_resp in code:
    code = code.replace(old_resp, new_resp, 1)
    print("✅ Response message now uses bk_info (not PATCH result)")
else:
    print("❌ Response pattern not found")
    idx = code.find("Unwrap {\"data\": {\"booking\":")
    if idx >= 0:
        print(f"Found at {idx}")

# Also fix the customer notification cust_msg to use bk_info
old_cust = """            console_line = f"\\n🖥️ Console: <b>{assigned_console}</b>" if assigned_console else ""
            cust_msg = (
                "မင်္ဂလာပါ 🙏\\n\\n"
                f"သင်၏ Booking (#{bk_id}) ကို အတည်ပြုပြီးပါပြီ။\\n"
                f"━━━━━━━━━━━━━━━━━━━\\n"
                f"📅 {b.get('date', '?')}  🕐 {b.get('timeSlot', '?')}\\n"
                f"🎮 {b.get('consoleType', '')}  ⏱️ {b.get('durationMins', '?')} mins{console_line}\\n"
                f"━━━━━━━━━━━━━━━━━━━\\n"
                f"PS Vibe မှ ကြိုဆိုပါသည်! ✨\\n"
                f"ကျေးဇူးတင်ပါတယ်"
            )"""

new_cust = """            console_line = f"\\n🖥️ Console: <b>{assigned_console}</b>" if assigned_console else ""
            cust_msg = (
                "မင်္ဂလာပါ 🙏\\n\\n"
                f"သင်၏ Booking (#{bk_id}) ကို အတည်ပြုပြီးပါပြီ။\\n"
                f"━━━━━━━━━━━━━━━━━━━\\n"
                f"📅 {bk_info.get('date', '?')}  🕐 {bk_info.get('timeSlot', '?')}\\n"
                f"🎮 {bk_info.get('consoleType', '')}  ⏱️ {bk_info.get('durationMins', '?')} mins{console_line}\\n"
                f"━━━━━━━━━━━━━━━━━━━\\n"
                f"PS Vibe မှ ကြိုဆိုပါသည်! ✨\\n"
                f"ကျေးဇူးတင်ပါတယ်"
            )"""

if old_cust in code:
    code = code.replace(old_cust, new_cust, 1)
    print("✅ Customer notify message now uses bk_info")
else:
    print("❌ Customer notify pattern not found")
    idx2 = code.find("သင်၏ Booking")
    if idx2 >= 0:
        print(f"Found cust_msg at {idx2}")

with open(FILE, "w") as f:
    f.write(code)
compile(code, FILE, "exec")
print("✅ File written + compiled OK")
