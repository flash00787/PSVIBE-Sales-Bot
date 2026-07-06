# Booking Time & Slot System — Production Deep Audit

**Date:** 2026-06-17  
**Auditor:** Subagent (Pro)  
**Files Audited:**
1. `/root/psvibe-sales-bot/bot/handlers/booking.py` — Staff booking flow
2. `/root/psvibe-sales-bot/customer_bot/booking_handlers.py` — Customer booking flow
3. `/root/psvibe_api_server/app.py` — API endpoints (booking focus)
4. `/root/psvibe_api_server/session_timer.py` — Session timer module

---

## 🔴 CRITICAL BUGS (Will Cause Double Bookings or Wrong Availability)

### C1. `api_start_console_session` — Booking Date Set to UTC, Not MMT

**File:** `app.py` line ~1758  
**Severity:** HIGH (API safety net exists, but UI shows wrong availability)

```python
today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
```

The `booking_date` column is set to UTC date, but `start_time` (stored via `now_mmt()`) is MMT. During the window from 17:30-23:59 UTC (00:00-06:29 MMT next day), the booking gets yesterday's UTC date. This means:

- **Customer bot `_get_available_consoles()`** and **`_get_available_slots()`** query by `search-bookings?date=<MMT_date>` — they won't find this session, showing the console as available when it's actually Active
- **Staff bot `_sbk_console_kb()`** fetches all bookings and filters by date string — won't see this session for the correct MMT date
- **The API conflict check in `api_bookings_create`** uses `start_time`/`end_time` datetime columns (not `booking_date`), so a double-booking IS caught at the API level → user sees "booking failed" after selecting a console that appeared free

**Same bug in `api_booking_checkin`** (app.py line ~1687) — the auto-checkin query uses UTC date, so during the crossover window confirmed bookings won't auto-checkin.

**Same bug in `api_confirmed_bookings_for_console`** (app.py line ~1758).

**Impact:** Console shows as available in UI when it's actually in use. Customer proceeds through booking flow, hits API conflict rejection. Bad UX but no actual double-booking.

**Fix:** Replace `datetime.now(timezone.utc)` with `now_mmt()` for the date portion:
```python
today = now_mmt().strftime('%Y-%m-%d')
```

---

### C2. Staff Booking — Duration Blocking Algorithm Overly Aggressive

**File:** `booking.py` lines 435-445  
**Severity:** HIGH (Shows many slots as unavailable when they're actually free)

```python
total_mins = start_h * 60 + start_m + b_dur
end_h = min(total_mins // 60, 23)
# Mark all hourly slots from start_h to end_h (inclusive)
for h in range(start_h, end_h + 1):
    unavailable.add(f"{h:02d}:00")
```

This uses **integer division** on total minutes + duration and marks EVERY full hour in the range as `🔴` blocked. The problem:

| Booking | start_h | total_mins | end_h (capped) | Blocked slots | Actually blocks |
|---------|---------|------------|----------------|---------------|-----------------|
| 10:30, 30min | 10 | 660 | 11 | 10:00, 11:00 | Only 10:00-11:00 |
| 10:00, 120min | 10 | 720 | 12 | 10:00, 11:00, 12:00 | 10:00-12:00 ✓ |
| 14:30, 30min | 14 | 900 | 15 | 14:00, 15:00 | Only 14:30-15:00 |
| 11:30, 90min | 11 | 780 | 13 | 11:00, 12:00, 13:00 | 11:30-13:00 |

**Example of false unavailability:**
- Booking at 10:30 for 30 mins → blocks slot 11:00 with 🔴
- But 11:00-12:00 does NOT overlap with 10:30-11:00
- A customer wanting to book 11:00-12:00 would see it as blocked

**Trigger:** ANY booking that doesn't start exactly on the hour gets aggressive blocking. With custom time slots in the customer bot, this happens frequently.

**Impact:** Staff sees false unavailability; may reject booking requests unnecessarily. The API would accept them, but staff won't offer them.

**Fix:** Use actual time-range overlap check instead of hourly bucket blocking:
```python
# Instead of:
for h in range(start_h, end_h + 1):
    unavailable.add(f"{h:02d}:00")

# Use actual overlap:
for slot in all_hours:
    sh, sm = map(int, slot.split(":"))
    slot_start = sh * 60 + sm
    slot_end = slot_start + 60
    if start_total < slot_end and end_total > slot_start:
        unavailable.add(slot)
```

---

### C3. `_get_available_slots` — UTC Date Used for "Today" Comparison

**File:** `customer_bot/booking_handlers.py` lines 160-170  
**Severity:** LOW (shop is closed during mismatch window)

```python
today_str = datetime.utcnow().strftime("%Y-%m-%d")
if date_str == today_str:
    # past-slot filtering
```

`date_str` comes from the user's date selection which uses MMT `today_str()`. During 17:30-23:59 UTC (00:00-06:29 MMT), UTC date != MMT date, so the past-slot filter is skipped for "Today" bookings.

**Impact:** Very low — shop opens at 09:00 MMT (02:30 UTC), by which time UTC and MMT dates are already aligned. Past-slot filtering works correctly during all open hours.

**Fix:** Use MMT-based today:
```python
from .data.prompts import today_mmt
today_str = today_mmt()  # returns "2026-06-17" in MMT
```

---

### C4. Console Availability Check Uses Wrong Duration (Default 60 Min)

**File:** `customer_bot/booking_handlers.py` lines ~720-740  
**Severity:** HIGH (False console availability)

In `bk_console_select()`, when checking available consoles:
```python
dur = context.user_data.get("bk_duration_mins", 60)  # DEFAULT 60!
available = await _get_available_consoles(date_str, time_str, dur)
```

The customer selects **console type BEFORE duration**. At this point, `bk_duration_mins` is always the default 60 (since duration hasn't been set yet). This means:

- **Scenario:** Customer wants to book 120 mins at 10:00. Console-A has a booking at 11:00 (just 60 mins away).
  - Availability check: 10:00+60min window doesn't conflict with 11:00 booking → Console-A shown as available ✅
  - But actual booking: 10:00+120min window DOES overlap 11:00 booking → Conflict! ❌
  - Customer proceeds, hits API rejection at final submission

**The same issue exists in `bk_time_select`** (line ~1078):
```python
dur = context.user_data.get("bk_duration_mins", 60)  # DEFAULT!
```

**Impact:** Customer sees consoles as available, goes through entire booking flow, only to be rejected at submission. Frustrating UX.

**Fix:** Move duration selection BEFORE console selection, OR use a conservative default like 240 (4 hours, the typical max for the UI keyboard).

---

## 🟡 HIGH ISSUES (Misleading UI or Incorrect Filtering)

### H1. Staff `_sbk_console_kb` Missing "arrived" Status

**File:** `booking.py` lines ~55-70  
**Severity:** MEDIUM

```python
for st in ("Active", "confirmed", "pending", "pending_check_in"):
```

Status "arrived" is missing from the conflict check. A booking marked as "arrived" (customer present but session not yet started) won't be detected as a conflict. However, the customer bot's `_get_available_consoles` excludes only "cancelled" and "done", which DOES include "arrived" — so this is only a staff-booking-side issue.

---

### H2. Customer Bot `_get_available_slots` — Active Sessions May Not Be Caught

**File:** `customer_bot/booking_handlers.py` lines 130-150  
**Severity:** MEDIUM

The function queries `search-bookings?date=<date>` which searches by `booking_date`. Due to **C1** (UTC date in `api_start_console_session`), Active sessions started during the UTC/MMT date crossover window have the wrong `booking_date` and won't appear in the search. This makes slots appear free when they shouldn't.

---

### H3. Staff Booking Time Slots Start at 10:00, Customer Bot at 09:00

**File:** `booking.py` line 444 vs `customer_bot/data/prompts.py` line 14  
**Severity:** MEDIUM

- **Staff bot:** `all_hours = ["10:00", "11:00", ...]` — starts at 10:00
- **Customer bot:** `OPEN_HOUR = 9` — slots from 09:00 to 21:00

Customer can book 09:00 slots that staff can't see/create in the booking flow. Staff booking doesn't show 09:00 as an option at all.

---

### H4. Staff Booking `step_sbk_duration` Back Button Goes to Wrong Step

**File:** `booking.py` lines ~470-480  
**Severity:** LOW

```python
if text == BTN_BACK:
    # re-ask time
    slots = [
        ["10:00", "11:00", "12:00"],
        ...
    ]
    await update.message.reply_text(
        "⏰ Time Slot ရွေးပါ:",
        reply_markup=ReplyKeyboardMarkup(slots + [[BTN_BACK, BTN_CANCEL]], resize_keyboard=True),
    )
    return SBK_TIME
```

The back button from duration goes to time selection, but it uses hardcoded time slots **without availability indicators** (no 🟢/🔴). The user sees all slots as equally available, losing the filtering. If back is pressed, then time is re-selected, the availability indicators won't show.

---

### H5. `_get_available_slots` Grace Period Hardcoded at 30 Min

**File:** `customer_bot/booking_handlers.py` line ~165  
**Severity:** LOW

```python
grace = now_mmt + timedelta(minutes=30)
```

The 30-minute grace period is hardcoded. If the business changes policy (e.g., allow booking 15 min before), this needs a code change. Consider making it configurable.

---

## 🟢 LOW ISSUES (Cosmetic / Unlikely)

### L1. `datetime.utcnow()` Deprecated in Python 3.12+

**Files:** `customer_bot/booking_handlers.py`, multiple locations  
**Severity:** COSMETIC

Python 3.12+ deprecates `datetime.utcnow()` in favor of `datetime.now(timezone.utc)`. Both are functionally identical, but this will cause deprecation warnings.

---

### L2. Customer Bot Uses Two Different MMT Implementations

**Files:** `customer_bot/data/prompts.py` and `customer_bot/data/time_utils.py`  
**Severity:** COSMETIC

- `prompts.py` imports from `time_utils.py` → `now_mmt()` returns `datetime.now(MMT)` (proper timezone-aware)
- `booking_handlers.py` manually computes MMT as `datetime.utcnow() + timedelta(hours=6, minutes=30)` (naive datetime)

Two different MMT implementations increase maintenance risk. The manual computation also doesn't handle `MMT` timezone object, making cross-timezone comparisons fragile.

---

### L3. `_get_available_consoles`—Redundant Live Status Check for Future Dates

**File:** `customer_bot/booking_handlers.py` line ~245  
**Severity:** COSMETIC

```python
is_today = (date_str == today_str)
...
if is_today and cstatus in ("active", "reserved"):
    continue
```

For future dates, the live console status is correctly skipped. But the code structure implies live status is checked first and booking overlap second — for today, both checks apply, which is correct but slightly redundant for Active consoles that already have a booking record.

---

### L4. Hardcoded Staff-Notify Chat ID in Session Timer

**File:** `session_timer.py` line ~30  
**Severity:** COSMETIC

```python
STAFF_NOTIFY_CHAT = os.environ.get("STAFF_NOTIFY_CHAT", "-1003686032747")
```

The default value is hardcoded. If the env var is not set, it falls back silently rather than raising a clear error.

---

### L5. Deprecated `create_booking` Endpoint Uses MMT — Inconsistent

**File:** `app.py` line ~1478  
**Severity:** COSMETIC

The deprecated `api_create_booking` endpoint correctly uses `now_mmt()` and `now.date()` (MMT). But the live `api_start_console_session` uses UTC. This inconsistency between "old correct" and "new wrong" is confusing.

---

### L6. `_sbk_advance_reminder` — Datetime Parsing Assumes M/D/YYYY

**File:** `booking.py` lines ~510-530  
**Severity:** LOW

```python
m = _re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", date_str)
mo, da, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
booking_dt = datetime(yr, mo, da, hr, mi, 0, tzinfo=timezone(timedelta(hours=6, minutes=30)))
```

This only supports M/D/YYYY format. If the date arrives in YYYY-MM-DD format, the regex won't match and the reminder silently fails. The API normalizes to YYYY-MM-DD in responses, so there's a format mismatch risk depending on the data flow.

---

## ✅ VERIFIED CORRECT

| Area | Verdict |
|------|---------|
| API conflict check (overlap query) | ✅ Correct — covers all overlap cases with 3 conditions |
| FOR UPDATE lock in `api_bookings_create` | ✅ Correct — prevents race conditions |
| Transaction wrapping in checkin/start/create | ✅ Correct — atomic operations |
| `_sync_console_status()` | ✅ Correct — called after each booking mutation |
| `now_mmt()` in API server | ✅ Correct — uses proper `timezone(timedelta(hours=6, minutes=30))` |
| Status filtering in API conflict query | ✅ Correct — includes `pending, confirmed, pending_check_in, Active` |
| Cross-midnight handling | ✅ Handled — datetime columns store full timestamps |
| `_get_available_slots` overlap detection | ✅ Correct — uses standard `bk_start < slot_end AND bk_end > slot_start` |
| `_get_available_consoles` overlap detection | ✅ Correct — same standard overlap check |
| `api_fetch_console_status` Reserved marking | ✅ Correct — marks Free consoles as Reserved when within booking window |
| Session timer resume on startup | ✅ Correct — `resume_active_timers()` re-queries DB on boot |

---

## 📊 SUMMARY TABLE

| # | ID | Category | Severity | File | Description |
|---|----|----------|----------|------|-------------|
| 1 | C1 | Timezone | 🔴 HIGH | `app.py:1758` | `api_start_console_session` sets `booking_date` to UTC date, not MMT — wrong date during crossover window (17:30-23:59 UTC) |
| 2 | C1b | Timezone | 🔴 HIGH | `app.py:1687` | `api_booking_checkin` auto-checkin query uses UTC date — may miss confirmed bookings during crossover |
| 3 | C2 | Availability Display | 🔴 HIGH | `booking.py:435-445` | Staff booking hourly slot blocking is overly aggressive — marks many slots 🔴 that are actually free |
| 4 | C3 | Timezone | 🟢 LOW | `booking_handlers.py:160` | `_get_available_slots` uses UTC date string for today comparison — only broken when shop closed |
| 5 | C4 | Availability Display | 🔴 HIGH | `booking_handlers.py:720` | Console availability check uses default 60-min duration before user selects actual duration |
| 6 | H1 | Availability Display | 🟡 MEDIUM | `booking.py:57` | Staff `_sbk_console_kb` missing "arrived" status in conflict check |
| 7 | H2 | Availability Display | 🟡 MEDIUM | `booking_handlers.py` | Sessions with wrong booking_date (from C1) missing from availability queries |
| 8 | H3 | Inconsistency | 🟡 MEDIUM | `booking.py:444` | Staff slots start at 10:00, customer bot opens at 09:00 |
| 9 | H4 | UI Flow | 🟢 LOW | `booking.py:470` | Back from duration to time loses availability indicators |
| 10 | H5 | Configuration | 🟢 LOW | `booking_handlers.py:165` | 30-min grace period hardcoded |
| 11 | L1 | Deprecation | 🟢 COSMETIC | Multiple | `datetime.utcnow()` deprecated in Python 3.12+ |
| 12 | L2 | Code Quality | 🟢 COSMETIC | Multiple | Two different MMT implementations in customer bot |
| 13 | L3 | Code Quality | 🟢 COSMETIC | `booking_handlers.py:245` | Redundant live status check for future dates |
| 14 | L4 | Configuration | 🟢 COSMETIC | `session_timer.py:30` | Hardcoded default STAFF_NOTIFY_CHAT |
| 15 | L5 | Consistency | 🟢 COSMETIC | `app.py:1478` | Deprecated endpoint uses MMT, live endpoint uses UTC |
| 16 | L6 | Parsing | 🟢 LOW | `booking.py:510` | `_sbk_advance_reminder` only parses M/D/YYYY date format |

---

## 🎯 PRIORITY FIX ORDER

1. **C2** — Fix slot blocking algorithm (aggressive false 🔴 — staff rejecting bookings unnecessarily)
2. **C4** — Fix console availability duration (customers getting rejected after full flow)
3. **C1** — Fix `booking_date` UTC→MMT in `api_start_console_session` and `api_booking_checkin`
4. **H1** — Add "arrived" status to staff conflict check
5. **H3** — Align staff booking hours with customer bot (add 09:00 slot)

