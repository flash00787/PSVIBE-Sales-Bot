#!/usr/bin/env python3
"""Fix remaining b.get() refs in _do_booking_action (rejection msg + n8n call)."""
FILE = "/root/psvibe-sales-bot/bot/handlers/admin_bookings.py"
with open(FILE) as f:
    data = f.read()

# Replace the n8n reminder call block (all b.get -> bk_info.get)
old_block = """    if action == "approve":
        asyncio.create_task(_post_n8n_booking_reminder(
            bk_id=bk_id,
            customer_name=b.get("customerName", ""),
            phone=b.get("phone", ""),
            console_id=b.get("consoleId") or "",
            console_type=b.get("consoleType", ""),
            date_str=b.get("date", ""),
            time_slot=b.get("timeSlot", ""),
            duration_mins=int(b.get("durationMins") or 60),
            tg_chat=tg_chat,
        ))"""

new_block = """    if action == "approve":
        asyncio.create_task(_post_n8n_booking_reminder(
            bk_id=bk_id,
            customer_name=bk_info.get("customerName", ""),
            phone=bk_info.get("phone", ""),
            console_id=bk_info.get("consoleId") or bk_info.get("console_id", ""),
            console_type=bk_info.get("consoleType", ""),
            date_str=bk_info.get("date", ""),
            time_slot=bk_info.get("timeSlot", ""),
            duration_mins=int(bk_info.get("durationMins") or 60),
            tg_chat=tg_chat,
        ))"""

if old_block in data:
    data = data.replace(old_block, new_block, 1)
    print("✅ n8n reminder: b.get -> bk_info.get")
else:
    print("❌ n8n block not found")

# Replace the rejection message
old_rej = """        else:
            cust_msg = (
                f"😔 <b>Booking #{bk_id} Rejected</b>\\n\\n"
                f"📅 {b.get('date', '?')}  🕐 {b.get('timeSlot', '?')}\\n\\n"
                f"အဆင်မပြေသဖြင့် တောင်းပန်ပါသည်။ နောက်ထပ် booking ထပ်မံလုပ်နိုင်ပါသည်။\\n"
                f"📞 ဆက်သွယ်ရန် @psvibeofficial"
            )"""

new_rej = """        else:
            cust_msg = (
                f"😔 <b>Booking #{bk_id} Rejected</b>\\n\\n"
                f"📅 {bk_info.get('date', '?')}  🕐 {bk_info.get('timeSlot', '?')}\\n\\n"
                f"အဆင်မပြေသဖြင့် တောင်းပန်ပါသည်။ နောက်ထပ် booking ထပ်မံလုပ်နိုင်ပါသည်။\\n"
                f"📞 ဆက်သွယ်ရန် @psvibeofficial"
            )"""

if old_rej in data:
    data = data.replace(old_rej, new_rej, 1)
    print("✅ rejection msg: b.get -> bk_info.get")
else:
    print("❌ rejection block not found")
    idx = data.find("Booking #{bk_id} Rejected")
    if idx >= 0:
        print(f"Found at {idx}: {repr(data[idx:idx+200])}")

with open(FILE, "w") as f:
    f.write(data)
compile(data, FILE, "exec")
print("✅ File written + compiled OK")
