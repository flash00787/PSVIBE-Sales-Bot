# 🔍 PS VIBE Booking Flow — Deep Audit Round 2

> **Audited:** 2026-06-17 | **Auditor:** Kora (Pro subagent, deep dive)
> **Files Audited:** 9 files | ~6,000+ lines | **Previous audit:** Round 1 found 9 issues

---

## 🎯 Executive Summary

The PS VIBE booking system has **no concurrency protection whatsoever**. Every multi-step database operation that should be atomic (slot booking, check-in, cancellation, approval) uses separate `SELECT`→`UPDATE` queries with **no transactions, no row-level locks, and no optimistic locking**. This means under concurrent load, **double bookings, data corruption, and session conflicts are guaranteed eventually**.

Additionally, the `auto_cancel_no_shows.py` script can **cancel Active (in-progress) sessions** because the cancel API doesn't check the booking's current status.

### Grades

| Category | Grade | Notes |
|----------|-------|-------|
| **Concurrency Safety** | **F** | Zero locking anywhere; all race conditions possible |
| **Data Consistency** | **D** | Multiple writers to console_status; no transactions |
| **Input Validation** | **C** | Parameterized queries prevent SQLi, but app-level validation weak |
| **Error Handling** | **C** | Silent failures on notifications; no retry queues |
| **Code Quality** | **D** | State name confusion, 2 MySQL modules, duplicate endpoints |
| **Overall** | **D+** | Works under low load but will fail under concurrency |

---

## 🔴 CRITICAL ISSUES (4) — Data Loss / Double Booking Risk

### CI-1: Double Booking — No Database-Level Slot Locking
- **File:** `/root/psvibe_api_server/app.py:1744-1865`
- **What's Wrong:** The booking creation endpoint (`POST /api/bookings`) performs:
  1. `SELECT ... WHERE console_id=X AND status IN (...) AND time-range-overlap` (conflict check)
  2. `INSERT INTO console_booking ...` (create booking)
  These are two separate queries with **no transaction, no `SELECT ... FOR UPDATE`, no MySQL lock**. Between step 1 and step 2, another concurrent request can pass the same conflict check and insert a booking for the same slot.
- **Reproduction:** Two customers submit bookings for the same console at the same time slot simultaneously.
- **Impact:** Two bookings for the same console at the same time. One customer gets bumped. Revenue risk.
- **Fix:**
  ```python
  # Option A: Use MySQL transaction with SELECT ... FOR UPDATE
  conn = _mc.connect(**_MYSQL_CFG)
  conn.start_transaction()
  cur = conn.cursor(dictionary=True)
  cur.execute("SELECT id FROM console_booking WHERE console_id=%s AND status IN (...) FOR UPDATE", (console_id,))
  # If conflict found → rollback
  # If no conflict → INSERT + COMMIT
  
  # Option B: Use INSERT ... ON DUPLICATE KEY with unique constraint
  # Option C: Use MySQL GET_LOCK() / RELEASE_LOCK() for slot-level locking
  ```

### CI-2: Cancel API Unconditionally Cancels ANY Booking (Including Active Sessions)
- **File:** `/root/psvibe_api_server/app.py:1675-1726` (`api_booking_cancel`)
- **What's Wrong:** `UPDATE console_booking SET status='cancelled' WHERE id=%s` — no status check at all. If a booking is Active (customer is playing), it still gets cancelled.
- **Reproduction:** 
  1. Customer checks in → booking becomes Active
  2. Staff accidentally clicks Cancel on wrong booking → Active session is cancelled
  3. OR: auto_cancel_no_shows.py runs while someone is being checked in → cancels Active session
- **Impact:** Active gaming sessions terminated mid-play. Data loss. Customer complaints.
- **Fix:**
  ```python
  # Add status guard
  affected = _mysql_exec(
      "UPDATE console_booking SET status='cancelled' WHERE id=%s AND status NOT IN ('Active','Done')",
      (booking_id,)
  )
  if affected == 0:
      return error_response(message="Cannot cancel - booking is already Active or Done")
  ```

### CI-3: No Database Transactions — Multi-Step Operations Non-Atomic
- **File:** `/root/psvibe_api_server/app.py` — all booking endpoints
- **What's Wrong:** Every `_mysql_exec()` is a standalone auto-commit. Multi-step operations like:
  - Create booking (INSERT booking + UPDATE console_status) 
  - Check-in (UPDATE booking status + UPDATE console_status)
  - Cancel (UPDATE booking + UPDATE console_status)
  …can fail halfway through. If step 2 fails, step 1 is already committed with no rollback.
- **Reproduction:** Any transient error (connection drop, timeout) mid-operation.
- **Impact:** console_status drifts from actual booking state. Console shown as Active when no Active booking exists (or vice versa).
- **Fix:** Wrap multi-step operations in MySQL transactions:
  ```python
  conn = _mc.connect(**_MYSQL_CFG)
  conn.start_transaction()
  try:
      cur = conn.cursor()
      cur.execute("INSERT INTO console_booking ...")
      cur.execute("UPDATE console_status ...")
      conn.commit()
  except:
      conn.rollback()
      raise
  ```

### CI-4: Auto-Cancel No-Shows Can Cancel In-Progress Sessions
- **File:** `/root/psvibe-sales-bot/scripts/auto_cancel_no_shows.py:85-140`
- **What's Wrong:** The script:
  1. Fetches ALL pending/confirmed bookings via `GET /api/bookings`
  2. Iterates through them, checking time
  3. Calls `POST /api/bookings/cancel` for each expired one
  Between step 1 (fetch) and step 3 (cancel), the booking could have been checked in by staff. But `api_booking_cancel` (see CI-2) has no status guard — it cancels even Active bookings.
  Worse, the script processes bookings sequentially with API calls between each, giving a wide window for races.
- **Reproduction:** 
  1. Auto-cancel script starts at 14:16
  2. It fetches 50 bookings, including booking #42 set for 14:00
  3. While processing #1-41, staff checks in #42 (now 14:17)
  4. Script reaches #42, calls cancel API → cancels the now-Active session
- **Impact:** In-progress gaming sessions terminated. Customer data loss.
- **Fix:**
  1. Fix CI-2 first (add status guard to cancel API)
  2. In auto-cancel script, re-verify status before cancelling:
     ```python
     # Before canceling, re-fetch booking to check current status
     check = requests.get(f"{API_URL}/api/bookings/{bk_id}", headers=headers)
     current_status = check.json().get("booking", {}).get("status", "")
     if current_status.lower() in ("active", "done", "cancelled"):
         continue  # Skip - status changed since we fetched
     # Now proceed with cancel
     ```
  3. Run auto-cancel more frequently with smaller batches

---

## 🔴 HIGH ISSUES (6) — Booking Integrity / Business Logic

### HI-1: Two Staff Approving Same Pending Booking — No Optimistic Lock
- **Files:** `/root/psvibe_api_server/app.py:1336` + `/root/psvibe-sales-bot/bot/handlers/admin_bookings.py:125`
- **What's Wrong:** `PATCH /api/bookings/{id}/status` does:
  ```sql
  UPDATE console_booking SET status='confirmed' WHERE id=X
  ```
  No `WHERE status='pending'` guard. Two staff can click "Approve" on the same booking. Both succeed. The second one overwrites the first's console assignment.
- **Impact:** Console double-assigned or first assignment lost. Admin confusion.
- **Fix:**
  ```python
  affected = _mysql_exec(
      "UPDATE console_booking SET status=%s WHERE id=%s AND status='pending'",
      (new_status, booking_id)
  )
  if affected == 0:
      return error_response(message="Booking already processed by another staff")
  ```

### HI-2: Walk-in Session Auto-Checks-In Confirmed Booking Regardless of Time
- **File:** `/root/psvibe_api_server/app.py:1580-1640` (`api_start_console_session`)
- **What's Wrong:** When starting a session:
  ```sql
  SELECT ... FROM console_booking 
  WHERE console_id=X AND status='confirmed' AND DATE(booking_date)=TODAY 
  ORDER BY created_at DESC LIMIT 1
  ```
  This auto-checks-in ANY confirmed booking for today, even if the booking time is **hours in the future**. A customer who booked for 18:00 could have their session started at 10:00 by a walk-in.
- **Reproduction:** 
  1. Customer books console C-01 for 18:00 → confirmed
  2. Staff starts a walk-in session on C-01 at 10:00
  3. The 18:00 booking is auto-checked-in early with the walk-in's member
- **Impact:** Customer's evening booking overwritten by morning walk-in. Wrong member assigned.
- **Fix:**
  ```python
  # Only auto-checkin if booking time is within a reasonable window (e.g., ±30 min)
  now_mmt = datetime.now(MMT)
  bk = _mysql_query_one(
      "SELECT ... FROM console_booking "
      "WHERE console_id=%s AND status='confirmed' AND DATE(booking_date)=%s "
      "AND start_time <= DATE_ADD(%s, INTERVAL 30 MINUTE) "
      "AND end_time >= %s "
      "ORDER BY created_at DESC LIMIT 1",
      (console_id, today, now_mmt, now_mmt)
  )
  ```

### HI-3: Staff Advance Booking — No Time Conflict Check in Bot
- **File:** `/root/psvibe-sales-bot/bot/handlers/booking.py:293-340` (`step_sbk_time`)
- **What's Wrong:** Staff booking shows hardcoded time slots (10:00, 11:00, ..., 22:00) with **no check against existing bookings**. Customer bot uses `_get_available_slots()` with overlap detection, but staff bot shows ALL slots regardless of availability. Conflict is only caught at API level after filling all 7 fields.
- **Reproduction:** Staff books at a slot that's already fully booked — fills name, phone, console, duration, game → gets error at final confirm.
- **Impact:** Terrible UX for staff. Time waste filling forms for unavailable slots.
- **Fix:** Add availability check when showing time slots:
  ```python
  # After selecting date, fetch existing bookings and filter slots
  try:
      bks = await _psvibe_get_async(f"search-bookings?date={date_str}")
      # Apply same overlap logic as customer bot
      ...
  except: pass
  ```

### HI-4: Booking Endpoint Accepts Invalid Dates/Times — Creates Garbage
- **File:** `/root/psvibe_api_server/app.py:1780-1800`
- **What's Wrong:** `POST /api/bookings` attempts to parse `date + time_slot`:
  ```python
  try:
      start_dt = datetime.strptime(f"{_parsed_date} {time_slot}", "%Y-%m-%d %H:%M")
  except:
      start_dt = now  # ← SILENTLY DEFAULTS TO NOW!
  ```
  If `time_slot` is "abc" or empty, the booking is created with the current time. No validation that date is in the future or that time is within operating hours.
- **Impact:** Bookings created with wrong times. Garbage data in database.
- **Fix:** Validate and reject with clear error:
  ```python
  try:
      start_dt = datetime.strptime(f"{_parsed_date} {time_slot}", "%Y-%m-%d %H:%M")
      if start_dt < now_mmt():
          return error_response(message="Cannot book for a past date/time")
  except:
      return error_response(message=f"Invalid time format: {time_slot}")
  ```

### HI-5: State Names Completely Wrong — Maintenance Disaster
- **Files:** `bot/handlers/booking.py` + `bot/app.py`
- **What's Wrong:** Every state name is the OPPOSITE of what it does:

| State Name | What It SAYS | What It ACTUALLY Does |
|------------|-------------|----------------------|
| `SBK_TIME` | Time selection | **Date** selection |
| `SBK_DUR` | Duration selection | **Time** selection |
| `SBK_CONSOLE` | Console selection | Console selection (correct!) |
| `SBK_CUST_NAME` | Customer name | Customer name (correct!) |
| `SBK_DATE` | Date selection | **Phone** entry |
| `SBK_GAME` | Game selection | **Duration** selection |
| `SBK_CONFIRM` | Confirmation | Game + Confirm (correct!) |

  Back-button handlers use these names. Any developer modifying this code WILL introduce bugs.
- **Impact:** High risk of future bugs during maintenance. Code is unreadable.
- **Fix:** Rename constants and handlers to match actual purpose. Example:
  ```python
  SBK_DATE → SBK_DATE    # Actually select date
  SBK_TIME → SBK_TIME    # Actually select time  
  SBK_CONSOLE → SBK_CONSOLE
  SBK_CUST_NAME → SBK_CUST_NAME
  SBK_PHONE → SBK_PHONE  # Actually enter phone
  SBK_DURATION → SBK_DURATION  # Actually select duration
  SBK_CONFIRM → SBK_CONFIRM
  ```

### HI-6: console_status Can Drift from Booking Reality
- **Files:** Multiple app.py endpoints (`api_create_booking`, `api_start_console_session`, `api_booking_checkin`, `api_end_booking`, `api_booking_cancel`)
- **What's Wrong:** `console_status` table is updated as a side effect in **5 different endpoints**. Each one writes directly to console_status with no coordination. If a check-in fails after updating console_status, or a cancel is processed while a session is being started, console_status and booking status diverge.
- **Impact:** Dashboard shows wrong status. Staff makes wrong decisions. Customer sees incorrect availability.
- **Fix:** Make console_status a **derived view** computed from the booking table, not independently maintained. Or at minimum, use a single function/trigger that updates console_status based on current bookings.

---

## 🟡 MEDIUM ISSUES (10) — Code Quality / Operational Risk

### MI-1: Two Separate MySQL Connection Modules in Same Project
- **Files:** `/root/psvibe_api_server/app.py:45-100` + `/root/psvibe_api_server/mysql_db.py`
- `app.py` has `_mysql_query()`, `_mysql_query_one()`, `_mysql_exec()` using **mysql.connector** (new connection per call)
- `mysql_db.py` has `query()`, `query_one()`, `execute()` using **pymysql** (single shared connection)
- Both are used in the same codebase. `_mysql_exec` is used in app.py endpoints, `mysql_execute` is used elsewhere.
- Two different libraries, two connection strategies, no pooling.
- **Fix:** Consolidate to ONE MySQL module. Use connection pooling.

### MI-2: Telegram Notification Failures Silently Ignored
- **Files:** `app.py:_notify_booking_received()`, `app.py:api_booking_checkin`, `app.py:api_booking_cancel`
- **What's Wrong:** All Telegram notifications are fire-and-forget with bare `except: pass`. If Telegram is down, admin notification for a new booking is lost. No retry, no dead letter queue, not even a log.
- **Impact:** New customer bookings silently go unnoticed by staff if Telegram has a transient error.
- **Fix:** At minimum, log failures. Better: add to a notification queue table for async retry.

### MI-3: No Conversation Timeout in Customer Bot
- **File:** `/root/psvibe-sales-bot/customer_bot/booking_handlers.py` + `main.py`
- **What's Wrong:** `ConversationHandler` has no `conversation_timeout` set. If a customer starts booking then abandons, `context.user_data` stays in memory indefinitely with partially-filled booking data. No cleanup.
- **Impact:** Memory leak over time. Stale data in user_data.
- **Fix:**
  ```python
  ConversationHandler(
      ...,
      conversation_timeout=timedelta(minutes=30),
      ...
  )
  ```

### MI-4: Duration Accepts Any Integer — No Maximum Cap
- **Files:** `customer_bot/booking_handlers.py:bk_duration_select` + `bot/handlers/booking.py:step_sbk_game` + `app.py:api_bookings_create`
- **What's Wrong:** 
  - Customer bot: Only allows 30/60/90/120/180 from keyboard (safe ✓)
  - Staff booking: Free text input, `int(text)` → accepts 0, -1, 9999999
  - API level: `int(req.get("durationMins", 60))` → accepts any integer
- **Impact:** Staff could accidentally create a 10,000-hour booking. Database stores huge values.
- **Fix:** Add validation:
  ```python
  if duration_mins < 1 or duration_mins > 1440:  # max 24 hours
      return error_response(message="Duration must be 1-1440 minutes")
  ```

### MI-5: Phone Validation Too Weak
- **File:** `customer_bot/booking_handlers.py:bk_phone_entry`
- **What's Wrong:** Only checks `len(cleaned) < 7`. Accepts "1234567" (fake), "0000000000" (invalid MM number). No Myanmar format validation (09...).
- **Impact:** Wrong phone numbers in database. Can't contact customer.
- **Fix:** Validate Myanmar phone format: starts with 09, 9-11 digits.

### MI-6: Game Name Not Validated Against Game Library
- **File:** `customer_bot/booking_handlers.py:bk_game_select`
- **What's Wrong:** Any text input becomes the game name. Matches against game list but falls back to `text[:50]` if no match. User can type "asdf" and it's accepted.
- **Impact:** Junk data in game_name column. Staff sees meaningless game names.
- **Fix:** If user types free text that doesn't match any game, ask them to select from the list.

### MI-7: Booking Creation Endpoints — Two Overlapping Implementations
- **Files:** `app.py:api_bookings_create` (POST /api/bookings) + `app.py:api_create_booking` (POST /api/create_booking)
- **What's Wrong:** Two endpoints do very similar things with different payload formats. `/api/create_booking` creates Active bookings directly with no validation. `/api/bookings` handles both customer and staff formats but is more complex.
- **Impact:** Confusion about which to use. Legacy endpoint bypasses all validation.
- **Fix:** Deprecate `/api/create_booking`. Route everything through `/api/bookings`.

### MI-8: Slot Conflict Check Skipped When console_id Is Empty
- **File:** `app.py:1826-1835` (in `api_bookings_create`)
- **What's Wrong:** `if console_id:` guard means bookings without a specific console bypass conflict detection. Customer bot now auto-assigns before API call (mitigation), but staff bookings or direct API calls don't get this protection.
- **Impact:** Potential overbooking when console_id is resolved later.
- **Fix:** If no console_id, check ALL consoles of the matching type for conflicts.

### MI-9: Auto-Cancel Reminder File Growth
- **File:** `scripts/auto_cancel_no_shows.py:20` (TRACK_FILE)
- **What's Wrong:** `booking_reminders.json` tracks reminded booking IDs. Only today's entries are cleaned. If the script runs once, the file contains only today's entries (fine). But no mechanism to prevent growth if multiple runs per day.
- **Impact:** Minor — file grows slowly over time if script runs multiple times/day.
- **Fix:** Periodically truncate file. Or use a TTL-based cleanup.

### MI-10: `_bk_state_stack` Trims Oldest Entries — Can Lose Back History
- **File:** `customer_bot/booking_handlers.py:45-48`
- **What's Wrong:** `if len(stack) > 20: stack.pop(0)` — removes the OLDEST state. If user goes deep into the flow and then wants to go back all the way, they can't because oldest states are trimmed.
- **Impact:** User can't go back beyond 20 states (practically impossible in a 16-state flow, but the bug logic is inverted — should pop most recent duplicate, not oldest entry).

---

## 🟢 LOW ISSUES (6) — Minor / Cosmetic

### LI-1: `scheduled` Status Doesn't Exist — Wasted API Call
- **File:** `scripts/auto_cancel_no_shows.py:80` + `:175`
- **What's Wrong:** Both `auto_cancel()` and `send_booking_reminders()` query for `status="scheduled"` which is not a valid booking status (valid: pending, confirmed, Active, Done, cancelled, no_show).
- **Impact:** Wastes one API call per run. No functional impact.

### LI-2: No HTML Escaping on Customer Names
- **File:** Multiple places where names are shown via `parse_mode="HTML"`
- **What's Wrong:** Customer names with `<` or `>` characters would break HTML rendering in Telegram messages.
- **Impact:** Malformed Telegram messages if someone enters `<script>` as their name.
- **Fix:** Sanitize or use `parse_mode="MarkdownV2"` with escaping.

### LI-3: 0 Balance Not Warned
- **File:** `customer_bot/booking_handlers.py:bk_phone_verify`
- **What's Wrong:** When a member has 0 balance, it's shown but no warning is displayed. The member can still book (need to pay).
- **Impact:** Minor UX issue — member may expect to use wallet balance.

### LI-4: BK_SPECIFIC_CONSOLE State Defined But Not Used
- **File:** `customer_bot/handlers.py:30` — constant defined but not in ConversationHandler states
- **Impact:** Dead code. No functional impact.

### LI-5: Redundant Console Availability Check in `_submit_booking`
- **File:** `customer_bot/booking_handlers.py:355-380`
- **What's Wrong:** `_get_available_consoles()` is called in `bk_console_select()` AND again in `_submit_booking()`. Redundant but ensures freshness.
- **Impact:** Extra API call. Minimal performance impact.

### LI-6: `sync_service.py` Is a Complete No-Op Stub
- **File:** `/root/psvibe_api_server/sync_service.py`
- **What's Wrong:** All functions are stubs (`pass`). GSheet sync is intentionally disabled.
- **Impact:** By design — MySQL is the single source of truth. Not a bug.

---

## 📊 Complete Issue Inventory

| # | Severity | Category | Issue | Files |
|---|----------|----------|-------|-------|
| CI-1 | 🔴 CRITICAL | Concurrency | No DB lock on slot booking → double booking possible | `app.py:1744-1865` |
| CI-2 | 🔴 CRITICAL | Data Integrity | Cancel API cancels even Active sessions | `app.py:1675-1726` |
| CI-3 | 🔴 CRITICAL | Data Integrity | No transactions for multi-step DB operations | `app.py` (all booking endpoints) |
| CI-4 | 🔴 CRITICAL | Concurrency | auto_cancel can cancel checked-in sessions | `auto_cancel_no_shows.py:85-140` |
| HI-1 | 🔴 HIGH | Concurrency | No optimistic lock on booking approval | `admin_bookings.py:125`, `app.py:1336` |
| HI-2 | 🔴 HIGH | Business Logic | Walk-in auto-checks-in future bookings early | `app.py:1580-1640` |
| HI-3 | 🔴 HIGH | UX | Staff booking shows all slots as available | `bot/booking.py:293-340` |
| HI-4 | 🔴 HIGH | Validation | API silently creates bookings with invalid dates | `app.py:1780-1800` |
| HI-5 | 🔴 HIGH | Code Quality | State names completely wrong (SBK_TIME=Date, etc.) | `bot/booking.py` + `bot/app.py` |
| HI-6 | 🔴 HIGH | Data Integrity | console_status independently written by 5 endpoints | `app.py` (multiple) |
| MI-1 | 🟡 MEDIUM | Code Quality | Two separate MySQL connection modules | `app.py`, `mysql_db.py` |
| MI-2 | 🟡 MEDIUM | Reliability | Telegram notifications fail silently | `app.py` (multiple) |
| MI-3 | 🟡 MEDIUM | Memory | No conversation timeout → memory leak | `booking_handlers.py` |
| MI-4 | 🟡 MEDIUM | Validation | Duration accepts any integer (no max) | `booking.py`, `app.py` |
| MI-5 | 🟡 MEDIUM | Validation | Phone validation too weak (no MM format) | `booking_handlers.py` |
| MI-6 | 🟡 MEDIUM | Validation | Game name not validated against library | `booking_handlers.py` |
| MI-7 | 🟡 MEDIUM | Code Quality | Two overlapping booking creation endpoints | `app.py` |
| MI-8 | 🟡 MEDIUM | Business Logic | Slot conflict check skipped when no console_id | `app.py:1826` |
| MI-9 | 🟡 MEDIUM | Maintenance | Reminder file could grow unbounded | `auto_cancel_no_shows.py:20` |
| MI-10 | 🟡 MEDIUM | UX | State stack trims wrong end (pops oldest) | `booking_handlers.py:45` |
| LI-1 | 🟢 LOW | Efficiency | "scheduled" status queried but doesn't exist | `auto_cancel_no_shows.py` |
| LI-2 | 🟢 LOW | Rendering | No HTML escaping on customer names | Multiple files |
| LI-3 | 🟢 LOW | UX | 0 balance shown but not warned | `booking_handlers.py` |
| LI-4 | 🟢 LOW | Dead Code | BK_SPECIFIC_CONSOLE defined but unused | `handlers.py:30` |
| LI-5 | 🟢 LOW | Performance | Redundant console availability check | `booking_handlers.py:355` |
| LI-6 | 🟢 LOW | Design | sync_service.py is complete no-op | `sync_service.py` |

**Total:** 26 issues (4 CRITICAL, 6 HIGH, 10 MEDIUM, 6 LOW)
**Carried from Round 1:** All 9 previous issues confirmed, most integrated into new findings

---

## 🔧 Top 3 CRITICAL Fixes (Do These First)

### 1. Add Row-Level Locking to Slot Booking (CI-1)
**Risk if unfixed:** Customers WILL get double-booked under concurrent load.
**Time to fix:** 2-4 hours
**Approach:** 
- Add `SELECT ... FOR UPDATE` inside a transaction in `POST /api/bookings`
- OR: Create a composite unique index on `(console_id, start_time)` and catch duplicate key errors

### 2. Add Status Guard to Cancel API (CI-2)
**Risk if unfixed:** Active gaming sessions can be terminated by accident.
**Time to fix:** 30 minutes
**Approach:** Add `AND status NOT IN ('Active','Done')` to the UPDATE query. Reject with clear error if no rows affected.

### 3. Add Transaction Wrappers to Multi-Step Operations (CI-3)
**Risk if unfixed:** console_status drifts from booking state; dashboard shows wrong data.
**Time to fix:** 4-6 hours
**Approach:** Wrap all booking mutations (create, checkin, cancel, end) in `START TRANSACTION` / `COMMIT` / `ROLLBACK`.

---

## 📋 Pre-Existing Issues (Round 1) — Status Update

| Round 1 Issue | Status |
|---------------|--------|
| State names completely wrong | ✅ Confirmed (now HI-5) |
| BK_SPECIFIC_CONSOLE defined but not registered | ✅ Confirmed (now LI-4) |
| Staff time slots hardcoded, no API check | ✅ Confirmed (now HI-3) |
| Slot conflict skipped when console_id empty | ✅ Confirmed (now MI-8) |
| Two overlapping booking creation endpoints | ✅ Confirmed (now MI-7) |
| Back button restarts entire flow (staff booking) | ✅ Confirmed, not re-flagged separately |
| Unconventional flow order | ⚠️ Design choice, not re-flagged |
| "scheduled" status queried but doesn't exist | ✅ Confirmed (now LI-1) |
| Redundant console availability check | ✅ Confirmed (now LI-5) |

---

## 🏁 Overall Verdict

The PS VIBE booking system **works correctly under single-user load** but has **zero concurrency safety**. The four critical issues (CI-1 through CI-4) mean that under any concurrent usage scenario (which is normal for a gaming lounge), **data corruption, double bookings, and session disruption are inevitable**.

The good news: all fixes are straightforward. The bad news: they require database-level changes (transactions, locking, constraints) that need careful implementation and testing.

### Strengths (Preserved from Round 1)
- All three booking paths functional end-to-end
- Phone-based member matching is solid
- Auto-assign console logic works
- Conflict detection at multiple levels (though not atomic)
- Complete admin lifecycle (approve → checkin → end)
- Customer notifications work
- Reminder system in place

### Weaknesses (New Findings This Round)
- **Zero concurrency protection** — the biggest finding
- **Cancel without status check** — can destroy active sessions
- **No database transactions** — data can become inconsistent
- **Worst-case race:** auto_cancel + checkin + cancel could cause triple failure

---

*Audit completed 2026-06-17. All file paths verified. All line numbers approximate — code may shift.*
