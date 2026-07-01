# PS VIBE Customer Bot — Booking Notification Audit

**Date:** 2026-07-01  
**Auditor:** Kora (sub-agent)  
**Scope:** All 7 notification paths when a customer creates a booking  

---

## Summary

| Path | Notifies Customer? | Notifies Admin? | Reminder Scheduled? | Gaps |
|------|--------------------|--------------------|----------------------|------|
| 1. Customer Creates Booking | ❌ No immediate confirmation | ✅ Yes (`_notify_booking_received`) | ❌ No | Customer sees no confirmation until staff approves |
| 2. Staff Approves | ✅ Yes | ✅ Yes (via original card edit) | ✅ Yes (n8n + bot fallback) | — |
| 3. Staff Rejects | ✅ Yes | ✅ Yes (via card edit) | — | — |
| 4. Staff Cancels | ✅ Yes | ❌ No (only card edit in staff chat) | ✅ Cancels reminders | Admin group not notified of cancellation |
| 5. Customer Self-Cancels (`_text_cancel_booking`) | ✅ Yes | ✅ Yes (via `_tg_send`) | ❌ No | Only one handler path notifies admin; the other doesn't |
| 6. Auto-Cancel (API/PATCH) | ✅ Yes (if `telegram_chat_id` exists) | ❌ No | ✅ Cancels reminders | No proactive no-show auto-cancel job exists |
| 7. Checkin | ✅ Yes (`_send_checkin_notification`) | ✅ Yes (via BOT_TOKEN) | — | No auto-cancel for no-show after checkin window |

---

## Path 1: Customer Creates Booking (via Customer Bot)

### Where does booking creation happen?
- **Customer Bot booking form:** `/root/psvibe-sales-bot/customer_bot/handlers.py` — conversation states BK_MEMBER_CHECK → BK_CONFIRM. The final submission calls the API.
- **API endpoint:** `POST /api/bookings` in `/root/psvibe_api_server/app.py` lines 2960–3125

### Does it capture telegramChatId?
✅ **Yes.** The customer bot passes `update.effective_user.id` through the booking form as `telegramChatId` (or `telegram_chat_id`). The API stores it in `console_booking.telegram_chat_id`.

### Does customer receive confirmation after booking creation?
❌ **NO.** There is no "သင်၏ Booking ကို အတည်ပြုပြီးပါပြီ" message sent to the customer after they submit their booking via the customer bot. The customer only sees a message from the conversation handler ending, but no explicit confirmation that their booking was received and is pending.

The `step_sbk_confirm` function in `/root/psvibe-sales-bot/bot/handlers/booking.py` (line ~570) sends a customer confirmation, but ONLY for staff-created bookings (`sbk_*` flow), NOT for customer-bot-created bookings.

### Does admin group get notified?
✅ **Yes.** `_notify_booking_received()` in `/root/psvibe_api_server/app.py` line 3148 sends a Telegram message to hardcoded chat ID `-1003686032747` using `CUSTOMER_BOT_TOKEN` (or `BOT_TOKEN` as fallback).

### GAP: Customer receives NO acknowledgment
The customer submits a booking and hears nothing until/unless staff approves or rejects. This can cause confusion — customer may think their booking didn't go through. Staff bookings (`step_sbk_confirm`) get immediate confirmation; customer-bot bookings should too.

---

## Path 2: Staff Approves → Customer Notified

### Code location
`_do_booking_action()` in `/root/psvibe-sales-bot/bot/handlers/admin_bookings.py` lines 213–390

### Customer notification
✅ **YES.** After successful PATCH (line ~340), if `tg_chat` is found and `CUSTOMER_BOT_TOKEN` is set, the customer receives:
```
မင်္ဂလာပါ 🙏
သင်၏ Booking (#{bk_id}) ကို အတည်ပြုပြီးပါပြီ။
📅 {date}  🕐 {time}
🎮 {console_type}  ⏱️ {duration} mins
🖥️ Console: {assigned_console}
PS Vibe မှ ကြိုဆိုပါသည်! ✨
```

### Admin notification
✅ **YES.** The inline card is edited to show "Confirmed!" with details.

### Reminders scheduled
✅ **YES.** Two mechanisms:
1. **n8n webhook:** `_post_n8n_booking_reminder()` → `POST /webhook/booking-reminder` → `add_booking_reminder()` in `booking_reminder.py` — 30-min advance reminder to admin + customer
2. **Bot fallback:** `_sbk_advance_reminder()` in `booking.py` — also sends 30-min advance reminder to admin + customer

### Chat ID resolution
- Primary: `bk_info.get("telegramChatId")` from the booking GET response
- Fallback: Looks up via `get_customer_chat_id(member_id)` from booking history

---

## Path 3: Staff Rejects → Customer Notified

### Code location
Same `_do_booking_action()` in `/root/psvibe-sales-bot/bot/handlers/admin_bookings.py` lines 213–390

### Customer notification
✅ **YES.** Sends via `_notify_customer()`:
```
😔 Booking #{bk_id} Rejected
📅 {date}  🕐 {time}
📝 Reason: {reject_reason}  (optional)
အဆင်မပြေသဖြင့် တောင်းပန်ပါသည်။ နောက်ထပ် booking ထပ်မံလုပ်နိုင်ပါသည်။
📞 ဆက်သွယ်ရန် @psvibeofficial
```

### Reminders cancelled
✅ **YES.** `POST /webhook/booking-reminder/cancel` is called.

---

## Path 4: Staff Cancels → Customer Notified

### Code location
- Cancel button appears in `cmd_confirmed_bookings()` in `/root/psvibe-sales-bot/bot/handlers/booking.py` line 289
- Handler: `cb_cancel_booking()` → `cb_cancel_with_reason()` → `_do_cancel_booking()` in `/root/psvibe-sales-bot/bot/handlers/booking_flow.py` lines 423–625

### Customer notification
✅ **YES.** After cancel PATCH succeeds, sends via `_notify_customer()`:
```
❌ Booking #{bk_id} ကို ပယ်ဖျက်ပြီ
📅 {date}  ⏰ {time}
🎮 {console}  🕹 {game}
📝 အကြောင်းပြချက်: {reason}
ကျေးဇူးပြု၍ ဆက်သွယ်ရန် @psvibeofficial
```

### Admin notification
❌ **NO separate admin group notification.** The inline card in the staff chat is edited to show "Cancelled" but no new message is sent to `STAFF_NOTIFY_CHAT` group. Other staff members not looking at the confirmed bookings list won't know.

### Reminders cancelled
✅ **YES.** Both `webhook/booking-reminder/cancel` AND `_cancel_advance_reminder` called.

---

## Path 5: Customer Self-Cancels → Customer Notified

### Two different handlers exist:

#### Path 5a: `_text_cancel_booking()` (handlers.py line ~415)
- **Trigger:** Customer types `cancel #42` in chat
- **Customer notification:** ✅ **YES** — `"🚫 Booking #{booking_id} ပယ်ဖျက်လိုက်ပြီ"`
- **Admin notification:** ✅ **YES** — sends to `_api.STAFF_NOTIFY_CHAT` via `_api._tg_send()`:
  ```
  🚫 Booking #{booking_id} — Customer Cancelled
  👤 {cust_name} မှ ပယ်ဖျက်သည်
  ```
- **Method:** Uses `PUT /api/cancel_booking/{booking_id}`
- **Reminders cancelled:** ❌ **NO** — no call to `webhook/booking-reminder/cancel`

#### Path 5b: `cmd_cancel_booking()` (booking.py line ~152)
- **Trigger:** Customer types `/cancelbooking 131`
- **Customer notification:** ✅ **YES** — `"✅ Booking #{bk_id} ကို ပယ်ဖျက်လိုက်ပါပြီ။"`
- **Admin notification:** ❌ **NO** — no staff notification sent
- **Method:** Uses `PATCH /api/bookings/{bk_id}/status` with `status: "cancelled"`
- **Reminders cancelled:** ✅ **YES** — the PATCH handler in app.py line 1705 sends customer notification and cancels reminders

### GAP: Inconsistent admin notification
- `_text_cancel_booking` notifies admin, `cmd_cancel_booking` does NOT
- Neither path cancels pending booking reminders at the call site (`_text_cancel_booking` uses a different endpoint)

---

## Path 6: Auto-Cancel / Expired / No-Show

### `POST /api/bookings/cancel` (app.py line 2420)
- **Customer notification:** ✅ **YES** — if `telegram_chat_id` exists, sends via `CUSTOMER_BOT_TOKEN`:
  ```
  ❌ Booking #{id} Cancelled
  📅 {date}  🕐 {time}
  🎮 {console}  ⏱️ {duration} mins
  🕹️ {game}
  ဆက်သွယ်ရန်: @psvibeofficial
  ```
- **Admin notification:** ❌ **NO** — only waitlist auto-notify is triggered
- **Reminders cancelled:** ✅ **YES** — cancels via `_sync_console_status` and booking_reminder cancel

### `PATCH /api/bookings/{id}/status` with status="cancelled" (app.py line 1605)
- **Customer notification:** ✅ **YES** — threaded notification sent:
  ```
  ❌ Booking #{id} Cancelled
  Slot မအားတာ သို့မဟုတ် အကြောင်းတစ်စုံတစ်ရာကြောင့် Booking ကို cancel လုပ်လိုက်ပါတယ်။
  📲 နောက်ထပ် Booking အသစ် တင်ပေးပါ။
  ```
- **Admin notification:** ❌ **NO**

### `POST /webhook/booking-reminder/cancel` (app.py line 727)
- **Customer notification:** ❌ **NO** — only cancels the timer
- **Admin notification:** ❌ **NO**

### `_sbk_advance_reminder()` (booking.py)
- **What it does:** Sleeps until 30 min before booking, then checks if booking is still confirmed/pending. If status changed to something else (cancelled, rejected), it silently skips. Does NOT proactively cancel the booking.
- **Customer notification:** ✅ Sends 30-min reminder if booking still active
- **Auto-cancel:** ❌ Does NOT auto-cancel expired bookings

### `session_timer.py` — `resume_active_timers()`
- **Auto-cancel:** ❌ **Explicitly DISABLED** — line comment says "NOT auto-ending (manual-only policy)". Staff must manually end sessions.

### CRITICAL GAP: No Proactive No-Show Auto-Cancel
There is **no background job or cron** that automatically cancels bookings where the customer hasn't shown up by the booking time + grace period. The system depends entirely on:
1. Staff manually noticing no-shows and cancelling
2. Expired bookings showing with ❌ icon in customer's "My Bookings" view (customer_bot/booking.py line ~65, `_is_booking_expired` with 15-min grace)
3. No notification is sent to either customer or admin when a booking time passes without check-in

---

## Path 7: Booking Checkin

### `POST /api/bookings/checkin` (app.py line 1465)
- **Booking status:** `confirmed` → `checked_in`
- **Admin notification:** ✅ **YES** — sends via `BOT_TOKEN` to `STAFF_NOTIFY_CHAT`:
  ```
  ✅ Customer Checked In!
  👤 Member: {member_id}
  🎮 Console: {console_id}
  ⏱ Time: {time} MMT
  📋 Status: Checked In (Session မစသေးပါ)
  ```
- **Customer notification:** ✅ **YES** — `_send_checkin_notification()` in admin_bookings.py line ~167 sends via `CUSTOMER_BOT_TOKEN`:
  ```
  🎉 Welcome to PS VIBE! 🎮
  ✅ Booking #{id} — Checked In!
  Staff will start your session shortly. Enjoy! 🎉
  ```

### `cb_checkin_booking()` in admin_bookings.py (line ~170)
- **Admin notification:** ✅ Inline card edited to "Checked In"
- **Customer notification:** ✅ **YES** — calls `_send_checkin_notification()`

### No-Show Auto-Cancel
❌ **No auto-cancel mechanism exists.** When a confirmed booking's time passes without check-in, the booking remains "confirmed" indefinitely. The only visual indicator is in the customer's My Bookings view where it shows as ❌ Expired.

### `POST /api/consoles/start-session` (app.py line 2192)
- Auto-checkin is triggered if booking time is within ±30 minutes
- Links the checked-in booking to the active session
- Does NOT notify customer (neither auto-checkin nor session start)

---

## Detailed Code Location Table

| # | Flow | Code Location | Line(s) | Customer Notified? | Admin Notified? |
|---|------|---------------|---------|--------------------|-----------------|
| 1 | Customer creates booking (API) | `app.py` `POST /api/bookings` | ~2960-3125 | ❌ | ✅ `_notify_booking_received` |
| 1 | Customer creates booking (bot form) | `customer_bot/handlers.py` conversation states | BK_MEMBER_CHECK→BK_CONFIRM | ❌ | — |
| 2 | Staff approves | `admin_bookings.py` `_do_booking_action` | 213-390 | ✅ `_notify_customer()` | ✅ card edit |
| 3 | Staff rejects | `admin_bookings.py` `_do_booking_action` | 213-390 | ✅ `_notify_customer()` | ✅ card edit |
| 4 | Staff cancels | `booking_flow.py` `_do_cancel_booking` | 534-625 | ✅ `_notify_customer()` | ❌ (card edit only) |
| 5a | Customer self-cancels (text) | `customer_bot/handlers.py` `_text_cancel_booking` | ~415-460 | ✅ | ✅ `_api._tg_send()` |
| 5b | Customer self-cancels (/cancelbooking) | `customer_bot/booking.py` `cmd_cancel_booking` | ~152-185 | ✅ | ❌ |
| 6 | API cancel (POST) | `app.py` `POST /api/bookings/cancel` | 2420-2500 | ✅ (if tg_chat_id) | ❌ |
| 6 | PATCH cancel | `app.py` `PATCH /api/bookings/{id}/status` | 1605-1729 | ✅ (threaded) | ❌ |
| 6 | No-show auto-cancel | **DOES NOT EXIST** | — | ❌ | ❌ |
| 7 | Checkin (API) | `app.py` `POST /api/bookings/checkin` | 1465-1560 | ✅ `_send_checkin_notification` | ✅ via `BOT_TOKEN` |
| 7 | Checkin (bot button) | `admin_bookings.py` `cb_checkin_booking` | ~170-230 | ✅ `_send_checkin_notification` | ✅ card edit |

---

## Reminder System Overview

| Mechanism | Trigger | Who Gets Notified | Timing |
|-----------|---------|--------------------|--------|
| n8n webhook | Staff approves booking | Admin group + Customer | 30 min before |
| `_sbk_advance_reminder` (bot) | Staff approves booking | Admin group + Customer | 30 min before |
| `booking_reminder.py` (API) | `POST /webhook/booking-reminder` | Admin group + Customer | 30 min before |
| `session_timer.py` (API) | Session starts (walk-in) | Admin group only | 5 min before session end |
| `_remind_loop` (bot) | Session starts (bot) | Admin group | 5 min before session end, repeats |

---

## Critical Gaps Summary

1. **❌ Customer receives NO confirmation after booking creation** — Customer bot does not send "သင်၏ Booking ကို လက်ခံပြီးပါပြီ" after form submission. Staff-created bookings get immediate confirmation but customer-bot bookings don't.

2. **❌ No proactive no-show auto-cancel** — No background job automatically cancels bookings when the booking time passes without check-in. The session_timer explicitly says "manual-only policy."

3. **❌ Inconsistent admin notifications on cancel** — `cmd_cancel_booking` (Path 5b) and `_do_cancel_booking` (Path 4 from staff) don't notify the admin group, only edit the inline card.

4. **❌ `_text_cancel_booking` doesn't cancel reminders** — Uses a different endpoint (`PUT /api/cancel_booking/{id}`) that doesn't trigger the reminder cancellation webhook.

5. **⚠️ `_sbk_advance_reminder` sends reminders at 30 min, not 10 min** — The docstring says 10 min but code shows `timedelta(minutes=30)`.

6. **⚠️ Hardcoded admin chat ID** — `_notify_booking_received` uses hardcoded `-1003686032747` instead of `STAFF_NOTIFY_CHAT` env var.

7. **⚠️ Double reminder on approve** — Both n8n webhook AND `_sbk_advance_reminder` schedule 30-min reminders, potentially sending duplicate notifications.
