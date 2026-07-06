# Admin Group Notification Audit — Comprehensive Report

**Date:** 2026-07-01  
**Auditor:** Kora (DeepSeek V4 Pro subagent)  
**Scope:** Every notification sent to `STAFF_NOTIFY_CHAT` (-1003686032747) across all codebases  

---

## Executive Summary

**Found: 22 distinct notification paths** across 2 codebases + 3 cron scripts.

### Severity:

| Level | Count | Issue |
|-------|-------|-------|
| 🔴 CRITICAL | 3 | Duplicate notifications for same event (booking remind, session remind, session extend) |
| 🟠 HIGH | 1 | Infinite spam loop (_remind_loop fires every 5 min forever) |
| 🟡 MEDIUM | 3 | Missing dedup on customer cancel, dual report cron, deprecated endpoint |
| 🟢 LOW | 4 | Minor format inconsistencies, threading safety concerns |
| ⚪ INFO | 11 | Working as intended |

---

## Complete Notification Inventory

### 1. Booking Lifecycle

| # | Notification | Source (file:line) | Trigger | Message Preview | Sent By | Dedup? | Risk |
|---|-------------|-------------------|---------|-----------------|---------|--------|------|
| 1 | **New Booking Request** (customer) | `api_server/app.py:3170` | `POST /api/bookings` with customerName | `🆕 New Booking Request #BK-XXX` → name, phone, date, time, console, game | CUSTOMER_BOT_TOKEN | ✅ Yes — skipped if `admin_notify_msg_id` in payload | 🟢 LOW |
| 2 | **New Staff Booking** | `bot/handlers/booking.py:926` | `step_sbk_confirm` → BTN_SBK_CONFIRM_BOOK | `📅 New Staff Booking #BK-XXX` → console, name, phone, date, time, dur, game, staff | Sale Bot | ✅ Yes — deletes old msgs for same phone+date, stores msg_id | 🟢 LOW |
| 3 | **Booking Check-In** (API) | `api_server/app.py:1534-1557` | `PATCH /api/bookings/:id/status` → checkin | `✅ Customer Checked In!` → member, console, time | BOT_TOKEN | ❌ None | 🟢 LOW |
| 4 | **Booking Cancelled by Staff** | `bot/handlers/booking_flow.py:630-650` | `_do_cancel_booking` → staff cancel | `❌ Booking #BK-XXX Cancelled by Staff` → name, phone, date, console, reason, staff | Sale Bot | ❌ None | 🟢 LOW |
| 5 | **Booking Cancelled by Customer** (option 1) | `customer_bot/booking.py:225-240` | `/cancelbooking` command | `🚫 Booking #BK-XXX — Customer Cancelled` → name | Customer Bot | ❌ None | 🟡 MEDIUM |
| 6 | **Booking Cancelled by Customer** (option 2) | `customer_bot/handlers.py:1037-1048` | Inline cancel from booking list | `🚫 Booking #BK-XXX — Customer Cancelled` → name | Customer Bot | ❌ None | 🟡 MEDIUM |
| 7 | **Booking Auto-Cancelled (No-Show)** | `scripts/auto_cancel_no_shows.py:214-224` | Cron every 5 min → API → no-show detection | `🚫 Booking Auto-Cancelled (No-Show)` → name, phone, date, console | BOT_TOKEN | ✅ Yes — only fires when status transitions | 🟢 LOW |

### 2. Advance Booking Reminders

| # | Notification | Source (file:line) | Trigger | Message Preview | Sent By | Dedup? | Risk |
|---|-------------|-------------------|---------|-----------------|---------|--------|------|
| 8 | **30-min Advance Reminder** (Sales Bot) | `bot/handlers/booking.py:680-762` | `_sbk_advance_reminder` — scheduled after confirm | `⏰ Booking #BK-XXX Reminder! 30 မိနစ်ခန့်အလို` → name, phone, date, time, dur, game, staff | Sale Bot | ✅ Yes — `_ADVANCE_REMIND_TASKS` dict by key | 🟢 LOW |
| 9 | **30-min Advance Reminder** (API Server) | `api_server/booking_reminder.py:126-196` | Webhook `POST /webhook/booking-reminder` from Sale Bot | `⏰ Booking #BK-XXX Reminder! 30 မိနစ်ခန့်အလို` → name, phone, console, date, time, dur | BOT_TOKEN | ✅ Yes — key-based dedup in `_pending_reminders` | 🔴 DUPLICATE with #8 |
| 10 | **Near-Start Reminder** (5-12 min before) | `scripts/auto_cancel_no_shows.py:330-355` | Cron every 5 min → scans for bookings 5-12 min before start | `⏰ Booking Reminder • Booking #BK-XXX` → name, date, time, console, dur, /checkin /cancel commands | BOT_TOKEN | ✅ Yes — `TRACK_FILE` prevents re-remind same day | 🟢 LOW |

### 3. Session/Console Timer

| # | Notification | Source (file:line) | Trigger | Message Preview | Sent By | Dedup? | Risk |
|---|-------------|-------------------|---------|-----------------|---------|--------|------|
| 11 | **Session Reminder Loop** (Sales Bot) | `bot/handlers/booking_flow.py:145-220` | `_remind_loop` — starts 5 min before end, repeats every 5 min FOREVER | `⏰ Session Reminder!` → console, member, plan mins, end time, warning (5min→0min→overdue), with Extend/End buttons | Sale Bot | ✅ Yes — task key `{cid}\|{chat_id}`, cancelled on end/extend | 🟠 HIGH — infinite repeat |
| 12 | **Session Timer Alert** (API Server) | `api_server/session_timer.py:173-175` | `_session_timer_task` — 5 min before session end (single fire) | `⏰ Timer Alert — Session ဆုံးခါနီး!` → console, member, remaining mins | BOT_TOKEN | ✅ Yes — checks `_bot_has_persistent_reminder()` before firing | 🔴 DUPLICATE with #11 |
| 13 | **Session Extended** (Sales Bot) | `bot/handlers/booking_flow.py:696-712` | `_do_extend` → extend callback | `⏰ Session Extended!` → console, member, +mins, new end | Sale Bot | ✅ Yes — only fires on explicit extend action | 🔴 DUPLICATE with #14 |
| 14 | **Session Extended** (API Server) | `api_server/session_timer.py:245-249` | `extend_session` → callback handler | `✅ Session Extended!` → console, member, +mins, new total | BOT_TOKEN | ❌ None | 🔴 DUPLICATE with #13 |
| 15 | **Session Ended** (API Server) | `api_server/session_timer.py:295-299` | `end_session_now` → callback handler | `⏹️ Session Ended` → console, member | BOT_TOKEN | ❌ None | 🟢 LOW (rarely triggered) |
| 16 | **Session End → Waitlist Notify** | `bot/handlers/sales.py:1643-1655` | Session end → POST `/api/waitlist/notify` | (No direct message — updates DB status to "Notified") | - | N/A | 🟢 LOW |

### 4. Finance & Sales

| # | Notification | Source (file:line) | Trigger | Message Preview | Sent By | Dedup? | Risk |
|---|-------------|-------------------|---------|-----------------|---------|--------|------|
| 17 | **Auto Top-Up Receipt** | `bot/handlers/members.py:1444-1500` | `auto_generate_receipt` after top-up complete | `🧾 PS VIBE Gaming Center Top-Up Receipt` → voucher, member, rank, date, amounts, balance | Sale Bot | ✅ Yes — per top-up | 🟢 LOW |

### 5. Daily Reports

| # | Notification | Source (file:line) | Trigger | Message Preview | Sent By | Dedup? | Risk |
|---|-------------|-------------------|---------|-----------------|---------|--------|------|
| 18 | **EOD Report** | `scripts/eod_report.py:30` | Cron: 20:00 MMT daily | Full Burmese daily summary: sales, members, top consoles, topup stats | BOT_TOKEN | ✅ Yes — once daily | 🟢 LOW |
| 19 | **Daily Report** (legacy?) | `send_daily_report.py:35` | Cron: 22:00 MMT daily | Generated daily report from `report_generator` | BOT_TOKEN | ✅ Yes — once daily | 🟡 MEDIUM |

### 6. Session Start (creates timer, not direct notification)

| # | Notification | Source (file:line) | Trigger | Message Preview | Sent By | Dedup? | Risk |
|---|-------------|-------------------|---------|-----------------|---------|--------|------|
| 20 | **Session Start → reminder scheduled** | `bot/handlers/booking.py:1691-1697` | `step_book_confirm` after session start | (No direct message — creates `_remind_loop` task → #11) | - | N/A | 🟢 LOW |
| 21 | **Session Start → reminder scheduled** | `bot/handlers/sales.py:1689-1697` | Sales confirmation flow | (No direct message — creates `_remind_loop` task → #11) | - | N/A | 🟢 LOW |

### 7. DEPRECATED (code exists but disabled)

| # | Notification | Source (file:line) | Trigger | Message Preview | Status |
|---|-------------|-------------------|---------|-----------------|--------|
| 22 | **New Booking Created** (deprecated) | `api_server/app.py:1595-1620` | `POST /api/create_booking` | `📅 New Booking Created!` → member, console, time | 🔴 **HARD-DISABLED** — returns HTTP 410 |

---

## 🔴 CRITICAL: Duplicate Notification Pairs

### Duplicate #1: 30-min Advance Booking Reminder
- **Path A:** `booking.py:_sbk_advance_reminder` (Sales Bot, scheduled locally)
- **Path B:** `booking_reminder.py:_reminder_thread` (API Server, triggered by webhook from Sale Bot)

**Flow:**
1. Booking confirmed → `step_sbk_confirm` → schedules `_sbk_advance_reminder` to fire in 30 min
2. Booking confirmed → `step_sbk_confirm` → calls `POST /webhook/booking-reminder` → `add_booking_reminder` → schedules `_reminder_thread` to fire in 30 min

**Result:** Both fire simultaneously at T-30 min → **duplicate admin notification AND duplicate customer notification.**

**Dedup status:** Both use `bk_id` as dedup key but operate INDEPENDENTLY. No cross-system dedup.

**Fix:** Disable one. The webhook path (B) was meant to replace the in-bot path (A), but both are active. Remove `_sbk_advance_reminder` call or remove the webhook call.

---

### Duplicate #2: Session Reminder (5-min before end)
- **Path A:** `booking_flow.py:_remind_loop` (Sales Bot, repeating every 5 min)
- **Path B:** `session_timer.py:_session_timer_task` (API Server, single fire)

**Flow:**
1. Session starts → `_remind_loop` created → fires at T-5min, T, T+5, T+10, ... (loops forever)
2. Session starts → `schedule_session_timer` called → `_session_timer_task` fires at T-5min

**Dedup status:** API Server (#B) checks `_bot_has_persistent_reminder(console_id, tg_id)` before firing. If Sales Bot ran `persist_reminder()` → API skips. **This works IF persistence is always written before API fires.**

**Risk:** Race condition — if API fires before persistence completes, both fire. Also, the API timer is scheduled at checkin while `_remind_loop` is scheduled at session start — these may be different times.

**Fix:** The API-side check should be sufficient. Monitor for any occurrences of both firing.

---

### Duplicate #3: Session Extended
- **Path A:** `booking_flow.py:_do_extend` (Sales Bot, fires on inline button → callback handler)
- **Path B:** `session_timer.py:extend_session` (API Server, fires on callback handler)

**Flow:**
1. User clicks Extend button → Sale Bot's `CallbackQueryHandler` → `_do_extend` → sends admin notification
2. User clicks Extend button → API's `handle_callback` → `extend_session` → sends admin notification

**Dedup status:** ❌ NONE. Both code paths process the same callback.

**Fix:** 
- If Sale Bot's callback handler processes the extend → only Sale Bot should notify
- If API's callback handler processes the extend → only API should notify
- Determine which handler is actually bound to Extend button callbacks

---

## 🟠 HIGH: Infinite Spam Risk — `_remind_loop`

**File:** `bot/handlers/booking_flow.py:145-220`

**Problem:** `_remind_loop` fires a notification every 5 minutes FOREVER until the session ends. There is NO auto-end mechanism. If staff forgets to manually end a session:

| Time Elapsed | Messages Sent | Cumulative |
|--------------|--------------|------------|
| 30 min overdue | 6 messages | 6 |
| 1 hour overdue | 12 messages | 12 |
| 3 hours overdue | 36 messages | 36 |
| Overnight (8h) | 96 messages | 96 |

**Each message includes inline buttons (Extend/End)**, which creates additional Telegram API load.

**Mitigation:** The loop checks `_is_session_active()` before each fire, which queries console_status. If console is freed, the loop breaks. But if there's a bug where console_status stays "Active", this loops forever.

**Recommendation:** Add a max-fire-count limit (e.g., 10 fires = 50 min overdue = auto-stop with final warning).

---

## 🟡 MEDIUM: Other Issues

### 5. Dual Customer Cancel Notifications
`customer_bot/booking.py:225` and `customer_bot/handlers.py:1037` both send "Customer Cancelled" to admin. A single cancel action could trigger both if not guarded. Check if both handlers can fire for the same cancel event.

### 6. Dual Daily Reports
- `eod_report.py` runs at 20:00 MMT via cron
- `send_daily_report.py` runs at 22:00 MMT via cron

Both send to STAFF_CHAT_ID. If both are enabled, staff gets two daily reports (2 hours apart). Verify if `send_daily_report.py` is still needed or was replaced by `eod_report.py`.

### 7. Checkin Notification Uses `BOT_TOKEN` Not `CUSTOMER_BOT_TOKEN`
`app.py:1534` uses `BOT_TOKEN` (Sale Bot token) for checkin notification. All other customer-facing notifications use `CUSTOMER_BOT_TOKEN`. Since this goes to admin, using BOT_TOKEN is correct, but the inconsistency could cause confusion.

---

## 🟢 LOW: Minor Issues

### 8. Session End: No Admin Notification
Session end (via sales flow or admin bookings) does NOT directly send a notification to admin group — it sends a customer notification (`session-end-notify`) and a waitlist notification, but no "Session Ended" to admin. The admin only sees session end via the conversation flow in the chat where they started the session. This is probably intentional but worth noting.

### 9. Hardcoded Chat ID in `_notify_booking_received`
`app.py:3175` uses hardcoded `"-1003686032747"` instead of reading from environment. Already the same value, but should be updated to use env var for consistency.

### 10. Race Condition in Dual Reminder Scheduling
When a booking is confirmed, `step_sbk_confirm` calls BOTH:
- `_sbk_advance_reminder()` (local to Sales Bot)
- `POST /webhook/booking-reminder` (triggers API-side reminder)

These are both `asyncio.create_task()` calls with no error handling. If one fails, the other still fires — which is actually good for reliability but bad for duplicate prevention.

---

## Notification Flow Diagram

```
BOOKING LIFECYCLE:
┌─────────────────────────────────────────────────────────────────┐
│ Customer creates booking (Customer Bot)                        │
│   → POST /api/bookings                                         │
│   → _notify_booking_received → Admin: "New Booking Request"   │
│                                                                │
│ Staff creates booking (Sale Bot)                               │
│   → step_sbk_confirm                                           │
│   → send_message → Admin: "New Staff Booking"                  │
│   → POST /webhook/booking-reminder (triggers API reminder)     │
│   → _sbk_advance_reminder (local reminder)                     │
│   → notify customer via Customer Bot                           │
│                                                                │
│ Approve/Reject:                                                │
│   → Notify customer only (not admin)                           │
│                                                                │
│ Cancel:                                                        │
│   → Staff cancel → _do_cancel_booking → Admin: "Cancelled"     │
│   → Customer cancel → Admin: "Customer Cancelled"              │
│                                                                │
│ Auto-Cancel (No-Show):                                         │
│   → Cron every 5 min → Admin: "Auto-Cancelled"                 │
└─────────────────────────────────────────────────────────────────┘

SESSION LIFECYCLE:
┌─────────────────────────────────────────────────────────────────┐
│ Check-In:                                                      │
│   → Admin: "Customer Checked In!"                              │
│   → Customer: "Welcome to PS VIBE!"                            │
│                                                                │
│ Session Start:                                                 │
│   → _remind_loop scheduled → Admin gets reminders every 5 min │
│   → API timer scheduled (may skip if bot reminder exists)      │
│                                                                │
│ 5-min Warning:                                                 │
│   → Admin: "Session Reminder! 5 min" + Extend/End buttons      │
│   → Customer: "5 မိနစ် ကျန်တော့သည်"                           │
│                                                                │
│ Every 5 min after (until ended):                               │
│   → Admin: "Session Reminder! 0 min / N min overdue"           │
│   → Customer: "ဆုံးချိန်ရောက်ပြီ / N min ကျော်ပြီ"            │
│                                                                │
│ Extend:                                                        │
│   → Admin: "Session Extended! +N min" (Sales Bot)              │
│   → Admin: "Session Extended! +N min" (API — DUPLICATE)        │
│   → New _remind_loop started                                   │
│                                                                │
│ Session End:                                                   │
│   → No direct admin notification (only in chat flow)           │
│   → Waitlist notified if applicable                            │
│   → Customer: session-end-notify                               │
└─────────────────────────────────────────────────────────────────┘

DAILY CRON:
┌─────────────────────────────────────────────────────────────────┐
│ 20:00 MMT → eod_report.py → Admin + Boss: Burmese daily report │
│ 22:00 MMT → send_daily_report.py → Admin: Generated report     │
│ */5 min  → auto_cancel cron → No-show checks + near-start alert │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cron Jobs That Send to Admin

```
# EOD Report: Daily at 20:00 MMT (13:30 UTC)
30 15 * * * python3 /root/psvibe-sales-bot/scripts/eod_report.py

# Auto-cancel no-shows + near-start reminders: every 5 min
*/5 * * * * curl ... POST /api/bookings/auto-cancel-no-show

# DISABLED — was sending auto-cancel notifications
#DISABLED_OBSOLETE */5 * * * * python3 scripts/auto_cancel_no_shows.py

# Reminder Health Monitor: every 10 min (no admin messages)
*/10 * * * * python3 /root/psvibe-sales-bot/scripts/reminder_health.py
```

---

## Fix Priority Matrix

| Priority | # | Issue | Fix |
|----------|---|-------|-----|
| 🔴 P0 | D1 | Double 30-min advance reminder | Disable one path: remove either `_sbk_advance_reminder` call OR the webhook call in `step_sbk_confirm` |
| 🔴 P0 | D3 | Double session-extend notification | Remove notification from one handler; determine which handles extend callbacks |
| 🔴 P1 | D2 | Double session reminder (race) | Already partially mitigated; add retry/confirmation on `persist_reminder` before scheduling |
| 🟠 P1 | #11 | Infinite _remind_loop | Add max-fire limit (10 fires = auto-stop) |
| 🟡 P2 | #5/#6 | Dual customer cancel notif | Verify single cancel action triggers only one handler |
| 🟡 P2 | #18/#19 | Dual daily reports | Disable `send_daily_report.py` cron if `eod_report.py` is the canonical one |
| 🟢 P3 | #9 | Hardcoded chat ID | Change to `os.environ.get("STAFF_NOTIFY_CHAT")` |
| 🟢 P3 | #15 | No session-end admin notif | Add explicit session-end notification to admin group |

---

## Notification Count Estimate (Typical Day)

| Notification Type | Est. Daily Count | Notes |
|-------------------|-----------------|-------|
| New Booking Request | 5-15 | Customer bookings |
| New Staff Booking | 3-10 | Staff-created bookings |
| Booking Confirmed (admin visible only via chat flow) | 0 | Not directly sent |
| Booking Cancelled | 1-5 | Staff/customer cancellations |
| Booking Auto-Cancelled | 0-3 | No-shows |
| 30-min Advance Reminder | 8-25 | **DUPLICATED** → actually 16-50 |
| Check-In | 8-25 | One per session |
| Session Reminder (5-min loop) | 30-100+ | **HEAVIEST TRAFFIC** — depends on overdue sessions |
| Session Extended | 5-15 | **DUPLICATED** → actually 10-30 |
| Top-Up Receipt | 5-20 | Auto-generated |
| EOD Report | 1-2 | **DUPLICATED daily reports** |
| Near-Start Reminder (cron) | 5-15 | 5-12 min before |
| **TOTAL** | **~70-250+** | Heavy load from session reminders |

---

## Key Files Audited

| File | Lines Checked | Notifications Found |
|------|--------------|-------------------|
| `/root/psvibe-sales-bot/bot/handlers/booking.py` | All | 3 (advance remind, staff booking, session-start reminder) |
| `/root/psvibe-sales-bot/bot/handlers/booking_flow.py` | All | 4 (cancel, remind-loop, extend, legacy remind) |
| `/root/psvibe-sales-bot/bot/handlers/admin_bookings.py` | All | 0 (customer-facing only) |
| `/root/psvibe-sales-bot/bot/handlers/sales.py` | All | 2 (remind-loop start, waitlist notify) |
| `/root/psvibe-sales-bot/bot/handlers/members.py` | All | 1 (auto-receipt) |
| `/root/psvibe-sales-bot/bot/handlers/notify.py` | All | 0 (customer-facing utility) |
| `/root/psvibe-sales-bot/customer_bot/booking.py` | All | 1 (customer cancel) |
| `/root/psvibe-sales-bot/customer_bot/handlers.py` | All | 1 (customer cancel) |
| `/root/psvibe_api_server/app.py` | All | 4 (checkin, deprecated create, new booking request, booking confirmed/cancelled) |
| `/root/psvibe_api_server/session_timer.py` | All | 3 (timer alert, extend, end) |
| `/root/psvibe_api_server/booking_reminder.py` | All | 1 (30-min advance) |
| `/root/psvibe_api_server/dashboard_routes.py` | All | 1 (customer notification from dashboard — not admin) |
| `/root/psvibe_api_server/patch_routes.py` | All | 1 (waitlist notify — not admin) |
| `/root/psvibe-sales-bot/send_daily_report.py` | All | 1 (daily report) |
| `/root/psvibe-sales-bot/scripts/eod_report.py` | All | 1 (EOD report) |
| `/root/psvibe-sales-bot/scripts/auto_cancel_no_shows.py` | All | 2 (auto-cancel, near-start remind) |
| `/root/psvibe-sales-bot/scripts/reminder_health.py` | All | 0 (monitoring only) |

---

## Conclusions

1. **The _remind_loop is the #1 source of admin group noise.** It fires every 5 minutes per active session. With 5+ active consoles, that's 5+ messages every 5 minutes = 60+ messages per hour just from reminders. With overdue sessions, this compounds.

2. **Three duplicate paths** send the same notification twice. The 30-min advance reminder and session-extend notifications are the most reliable duplicates.

3. **The old python auto-cancel script is DISABLED** in cron but the code still exists in `scripts/auto_cancel_no_shows.py`. Its near-start reminder logic has been replaced by the API endpoint approach.

4. **No session-end admin notification exists.** Staff only knows a session ended if they're in the chat where they started it.

5. **The daily report is sent twice** (20:00 and 22:00 MMT) via two different scripts. Likely one is legacy.

6. **Overall architecture is solid** but suffers from the "two systems" problem — Sales Bot and API Server both manage reminders, creating natural duplication risk.
