#!/usr/bin/env python3
"""Fix two notification bugs:
1. Cancel notification — _do_cancel_booking uses PATCH result (no telegramChatId) instead of GET bk_info
2. 10-min booking reminder — add customer notification + telegramChatId to search response
"""
import re

# ── FIX 1: booking_flow.py — Cancel notification ──
FILE1 = '/root/psvibe-sales-bot/bot/handlers/booking_flow.py'
with open(FILE1) as f:
    t1 = f.read()

# Replace the notification block in _do_cancel_booking
# The bug: result.get("telegramChatId") returns "" because PATCH only returns {booking_id, status}
old_notify = """    # Notify customer if they have Telegram
    tg_chat = result.get("telegramChatId") or ""
    if tg_chat and CUSTOMER_BOT_TOKEN:
        cust_msg = (
            f"❌ <b>Booking #{bk_id} ကို ပယ်ဖျက်ပြီ</b>\\n"
            f"━━━━━━━━━━━━━━━━━━\\n"
            f"📅 {result.get('date','?')}  ⏰ {result.get('timeSlot','?')}\\n"
            f"🎮 {result.get('consoleType','?')}\\n"
            f"━━━━━━━━━━━━━━━━━━\\n"
            f"📝 အကြောင်းပြချက်: {reason}\\n"
            f"ကျေးဇူးပြု၍ ဆက်သွယ်ရန် @psvibeofficial"
        )
        await asyncio.to_thread(_notify_customer, tg_chat, cust_msg)"""

new_notify = """    # Notify customer if they have Telegram
    # Fetch full booking data via GET (PATCH result has no customer fields)
    _bk_info2 = await _replit_get_async(f"bookings/{bk_id}")
    if isinstance(_bk_info2, dict):
        if "booking" in _bk_info2:
            _bk_info2 = _bk_info2["booking"]
    tg_chat = _bk_info2.get("telegramChatId") or ""
    if tg_chat and CUSTOMER_BOT_TOKEN:
        cust_msg = (
            f"❌ <b>Booking #{bk_id} ကို ပယ်ဖျက်ပြီ</b>\\n"
            f"━━━━━━━━━━━━━━━━━━\\n"
            f"📅 {_bk_info2.get('date','?')}  ⏰ {_bk_info2.get('timeSlot','?')}\\n"
            f"🎮 {_bk_info2.get('consoleType','?')}\\n"
            f"━━━━━━━━━━━━━━━━━━\\n"
            f"📝 အကြောင်းပြချက်: {reason}\\n"
            f"ကျေးဇူးပြု၍ ဆက်သွယ်ရန် @psvibeofficial"
        )
        await asyncio.to_thread(_notify_customer, tg_chat, cust_msg)"""

if old_notify in t1:
    t1 = t1.replace(old_notify, new_notify, 1)
    print("1. Cancel notification FIXED — now fetches bk_info via GET")
else:
    print("1. SKIP — cancel notification pattern not found")

with open(FILE1, 'w') as f:
    f.write(t1)
compile(t1, FILE1, 'exec')
print("   booking_flow.py ✅")


# ── FIX 2: auto_cancel_no_shows.py — 10-min reminder: also notify customer ──
FILE2 = '/root/psvibe-sales-bot/scripts/auto_cancel_no_shows.py'
with open(FILE2) as f:
    t2 = f.read()

# Add telegramChatId to the search-bookings response (app.py)
# AND add customer notification in send_booking_reminders

# First, add customer notification after the staff notification in send_booking_reminders
old_reminder = """            if tg_send(STAFF_NOTIFY_CHAT, remind_msg, token=BOT_TOKEN, parse_mode="HTML"):
                reminded_ids.add(reminder_key)
                print(f"  \\u2713 Reminded staff about booking #{bk_id} ({customer}, {time_str})")"""

new_reminder = """            if tg_send(STAFF_NOTIFY_CHAT, remind_msg, token=BOT_TOKEN, parse_mode="HTML"):
                reminded_ids.add(reminder_key)
                print(f"  \\u2713 Reminded staff about booking #{bk_id} ({customer}, {time_str})")
            # Also notify customer via customer bot
            _cust_chat = b.get("telegram_chat_id") or b.get("telegramChatId") or ""
            if _cust_chat and CUSTOMER_BOT_TOKEN:
                _cust_remind = (
                    f"\\u23F0 <b>\\u203E\\u203E PS VIBE \\u203E\\u203E</b>\\n\\n"
                    f"\\u2705 <b>Booking Reminder</b>\\n"
                    f"Booking #{bk_id}\\n"
                    f"\\ud83d\\udcc5 {bk_date_clean}  \\ud83d\\udd50 {time_str}\\n"
                    f"\\ud83c\\udfae {console}  \\u23f1 {duration} mins\\n"
                )
                if game:
                    _cust_remind += f"\\ud83c\\udfae {game}\\n"
                _cust_remind += "\\n\\u23f0 \\u1014\\u102d\\u1029\\u101b\\u1031\\u101b\\u1000\\u1039\\u1018\\u102d\\u1019\\u1039\\u1019\\u1031\\u101c\\u102c\\u101b\\u1019\\u1039\\u1019"
                tg_send(_cust_chat, _cust_remind, token=CUSTOMER_BOT_TOKEN, parse_mode="HTML")
                print(f"  \\u2713 Reminded customer about booking #{bk_id}")"""

if old_reminder in t2:
    t2 = t2.replace(old_reminder, new_reminder, 1)
    print("2. 10-min reminder: customer notification ADDED")
else:
    print("2. SKIP — reminder pattern not found (might have different formatting)")

with open(FILE2, 'w') as f:
    f.write(t2)
compile(t2, FILE2, 'exec')
print("   auto_cancel_no_shows.py ✅")


# ── FIX 3: app.py — Add telegramChatId to search-bookings response ──
FILE3 = '/root/psvibe_api_server/app.py'
with open(FILE3) as f:
    t3 = f.read()

# The normalized list at line ~1341 doesn't include telegram_chat_id
old_search = """normalized.append({"id": r.get("id",""), "customerName": r.get("staff_name",""), "phone": r.get("phone","") or r.get("telegram_chat_id",""), "date": bd_str, "timeSlot": time_slot, "consoleType": _ctype, "durationMins": r.get("duration_mins",60), "gameName": r.get("game_name",""), "console_id": r.get("console_id",""), "consoleId": r.get("console_id",""), "member_id": r.get("member_id",""), "status": r.get("status","")})"""

new_search = """normalized.append({"id": r.get("id",""), "customerName": r.get("staff_name",""), "phone": r.get("phone","") or r.get("telegram_chat_id",""), "date": bd_str, "timeSlot": time_slot, "consoleType": _ctype, "durationMins": r.get("duration_mins",60), "gameName": r.get("game_name",""), "console_id": r.get("console_id",""), "consoleId": r.get("console_id",""), "member_id": r.get("member_id",""), "telegram_chat_id": r.get("telegram_chat_id",""), "status": r.get("status","")})"""

if old_search in t3:
    t3 = t3.replace(old_search, new_search, 1)
    print("3. search-bookings: telegram_chat_id ADDED to response")
else:
    print("3. SKIP — search response pattern not found")
    # Find nearby text
    idx = t3.find("normalized.append")
    if idx >= 0:
        print(f"   Found at {idx}: ...{t3[idx:idx+300]}...")

with open(FILE3, 'w') as f:
    f.write(t3)
compile(t3, FILE3, 'exec')
print("   app.py ✅")


print("\\n✅ All fixes applied!")
