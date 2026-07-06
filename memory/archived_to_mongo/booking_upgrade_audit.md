# PS VIBE Booking System — Comprehensive Audit & Upgrade Plan

**Audit Date:** 2026-06-18
**Auditor:** Kora (Subagent)
**Scope:** Full booking codebase — API server, Sale Bot, Customer Bot, Discord Bot, DB schema, n8n webhooks

---

## System Overview

| Component | Path | States |
|-----------|------|--------|
| Customer Bot | `/root/psvibe-sales-bot/customer_bot/booking_handlers.py` | 16 states (BK_MEMBER_CHECK → BK_CONFIRM) |
| Staff Advance Booking | `/root/psvibe-sales-bot/bot/handlers/booking.py` | 7 states (SBK_DATE → SBK_CONFIRM) |
| Walk-in Session | `/root/psvibe-sales-bot/bot/handlers/booking.py` | 4 states (BOOK_LINK → BOOK_MINS) |
| Session Reminders | `/root/psvibe-sales-bot/bot/handlers/booking_flow.py` | Extend/End loop |
| API Server | `/root/psvibe_api_server/app.py` | 7 booking endpoints |
| Session Timer (API) | `/root/psvibe_api_server/session_timer.py` | Dead code duplicate |
| DB Tables | `console_booking`, `console_status` | MySQL (psvibe-mysql) |
| Discord Bot | `/root/psvibe-discord-bot/bot.js` | Direct MySQL bypass |

---

## 1. Issue List — Complete

### 🔴 CRITICAL (Data Integrity / Double-Booking)

---

#### C1: Discord Bot Bypasses ALL API Validation
- **File:** `/root/psvibe-discord-bot/bot.js:812`
- **Root Cause:** Discord bot performs direct `INSERT INTO console_booking` via `dbPool.execute()`, completely bypassing the API server's conflict checks, transactions, `FOR UPDATE` locking, and `_sync_console_status()`.
- **Impact:** Any Discord user can create bookings that double-book consoles, ignore time conflicts, and leave `console_status` out of sync. **This is the #1 double-booking vector.**
- **Severity:** CRITICAL

#### C2: Race Condition in Checkin Guard (Pre-Transaction Check)
- **File:** `/root/psvibe_api_server/app.py:1243-1255`
- **Root Cause:** `api_booking_checkin()` checks for existing Active bookings on the console **outside** the transaction block. Two concurrent checkins can both pass the guard, then both proceed into the transaction where only `FOR UPDATE` on their own row (not the existing one) protects them. The transaction only updates the booking being checked-in, and the console_status update doesn't have a unique constraint to fail.
- **Impact:** Two members can be checked into the same console simultaneously, creating two Active bookings on one console.
- **Severity:** CRITICAL

#### C3: `api_create_booking` (Deprecated) — No Transaction, No Conflict Check
- **File:** `/root/psvibe_api_server/app.py:1331-1377`
- **Root Cause:** The deprecated endpoint uses separate `_mysql_exec()` calls without wrapping in a transaction. No `FOR UPDATE`, no rollback capability. It inserts a booking, then tries to update `console_status` — if the second call fails, the booking row is orphaned with no rollback. It also never checks if the console is already Active, and uses no row-level locking to prevent races.
- **Impact:** Can create Active bookings on consoles already in use. Data corruption on partial failure.
- **Severity:** CRITICAL

#### C4: `console_booking.console_id` — Missing DB Index
- **Table:** `console_booking` — indexes exist for `booking_date`, `status`, `branch_id` — but NOT `console_id`.
- **Root Cause:** Every conflict check queries `WHERE console_id=%s AND status IN (...)` — without an index on `console_id`, these queries do full table scans.
- **Impact:** With 300+ bookings, conflict checks are progressively slower. Under concurrent load, full table scans hold locks longer and worsen race windows.
- **Severity:** HIGH → CRITICAL (amplifies all race conditions)

#### C5: `_sync_console_status` Called AFTER Commit (Orphan Risk)
- **File:** `/root/psvibe_api_server/app.py:1956` (`api_bookings_create`)
- **Root Cause:** In `api_bookings_create`, the transaction commits first, THEN `_sync_console_status()` is called in a new connection. If the sync fails (network blip, DB error), the booking is committed but `console_status` is stale/dirty. This is also true at line 1694 (`api_end_booking`) and line 1849 (`api_booking_cancel`).
- **Impact:** `console_status` can drift out of sync, causing the console dashboard to show wrong status. Active sessions can appear Free and vice versa.
- **Severity:** HIGH

---

### 🟠 HIGH (Structural / Design)

---

#### H1: Two Overlapping Booking Endpoints
- **Files:**
  - `POST /api/bookings` — `/root/psvibe_api_server/app.py:1882` (customer bot + staff format, unified)
  - `POST /api/create_booking` — `/root/psvibe_api_server/app.py:1331` (deprecated, only staff format)
- **Root Cause:** The deprecated endpoint still exists and handles staff walk-in format differently (no transaction, no conflict check, skips customer bot logic). Both are active and routable.
- **Impact:** Future developers or API consumers may use the wrong endpoint. The deprecated endpoint has none of the safety fixes applied to the unified endpoint.
- **Severity:** HIGH

#### H2: Dual Parallel Timer Systems (Code Drift)
- **Files:**
  - API server: `/root/psvibe_api_server/session_timer.py` (single-fire, no extend, `_active_timers`)
  - Sale Bot: `/root/psvibe-sales-bot/bot/handlers/booking_flow.py` (repeat loop, extend support, `_REMIND_TASKS`)
- **Root Cause:** Two independent timer systems were built. `session_timer.py` schedules timers from API endpoints (`api_booking_checkin`), while `booking_flow.py` schedules from Sale Bot handlers (`_do_create_booking`). The API timer is a simpler, single-fire version without extend support. The Sale Bot timer handles repeats, extends, and persistence. Both can fire on the same session.
- **Impact:** Duplicate reminder messages in the admin group. Confusing state where extend on one system doesn't update the other.
- **Severity:** HIGH

#### H3: State Flow Logic Bug — `step_sbk_date` Back Button Wrong Target
- **File:** `/root/psvibe-sales-bot/bot/handlers/booking.py:351`
- **Root Cause:** In `step_sbk_date`, pressing Back goes to `SBK_PHONE` (asks for phone again), but the user was previously at `SBK_TIME` → `SBK_DATE`. The correct back target should be to time selection, not phone. The state isn't being popped correctly.
- **Impact:** Staff gets confused when Back doesn't return to the previous step but jumps several steps backward.
- **Severity:** HIGH

#### H4: `step_sbk_phone` Back Button Goes to Customer Name but Returns Wrong State
- **File:** `/root/psvibe-sales-bot/bot/handlers/booking.py:346-358`
- **Root Cause:** `step_sbk_phone` on Back shows customer name prompt text but returns `SBK_CUST_NAME` — this is actually correct for going back one step. But there's no state stack tracking; it relies on hardcoded routing.
- **Impact:** Brittle back navigation. If flow order changes, back buttons break silently.
- **Severity:** MEDIUM

#### H5: Hardcoded Time Slots — No API Conflict Check
- **File:** `/root/psvibe-sales-bot/bot/handlers/booking.py:528-529`, `step_sbk_time`
- **Root Cause:** `step_sbk_time` builds time slot availability from booking data fetched locally, not via a dedicated API endpoint. The data is queried across multiple statuses independently. If the booking list is stale (cached), availability can be wrong.
- **Impact:** Staff may schedule a booking at a slot that's already taken but not reflected in the cached data.
- **Severity:** HIGH

#### H6: Customer Bot Auto-Assign at Submit Time — Conflict Window
- **File:** `/root/psvibe-sales-bot/customer_bot/booking_handlers.py:_submit_booking()`
- **Root Cause:** Customer bot's `_submit_booking()` calls `_get_available_consoles()` at submit time and auto-assigns the first free console. Between the availability check and the actual booking submission (POST), another booking can take that console.
- **Impact:** Race condition — customer gets a booking confirmed for a console that's already taken. The API does catch this with its conflict check, returning an error, but the customer sees a confusing failure message.
- **Severity:** HIGH

#### H7: `end_time` Not Set for Staff Walk-In Sessions
- **File:** `/root/psvibe_api_server/app.py:1331` (`api_create_booking` — deprecated)
- **Root Cause:** The deprecated endpoint (and the staff-format path in `/api/bookings`) doesn't compute or store `end_time`. This means session duration is only tracked by `duration_mins`, and elapsed-time calculations become unreliable.
- **Impact:** Session timer displays wrong remaining time; extend doesn't have a base end time to add to.
- **Severity:** HIGH

#### H8: `member_id` in `console_booking` Often Empty or Wrong
- **Files:** Multiple booking handlers
- **Root Cause:** 
  - Customer bot stores `telegram_chat_id` in the `telegram_chat_id` column but often leaves `member_id` empty if the phone→member lookup fails.
  - `_submit_booking` in customer bot does phone-based member lookup after calling `_api_post`, so the `member_id` is resolved server-side. If the lookup fails silently, `member_id` stays empty.
  - Staff walk-in sessions sometimes use `member_id="Guest"` which isn't a real member ID.
- **Impact:** Booking-to-member analytics/reporting is unreliable. Wallet deduction can't find the member.
- **Severity:** HIGH

---

### 🟡 MEDIUM (Bugs / UX)

---

#### M1: Staff Back Button in `step_sbk_console` Restarts Entire Flow
- **File:** `/root/psvibe-sales-bot/bot/handlers/booking.py:295-299`
- **Root Cause:** In `step_sbk_console`, BTN_BACK calls `cmd_staff_booking(update, context)` which clears ALL user_data and restarts from date selection. It should go back to time selection.
- **Impact:** If staff makes a mistake at console selection, they lose ALL previously entered data (date, time).
- **Severity:** MEDIUM

#### M2: Customer Bot DuplicateBooking Check Parses Time Range But API Also Checks
- **File:** `/root/psvibe-sales-bot/customer_bot/booking_handlers.py:bk_confirm()`
- **Root Cause:** The customer bot does a duplicate-booking overlap check client-side, then the API also does one server-side in `api_bookings_create`. This double-check is redundant but uses different logic (client uses `search-bookings?telegram_chat_id`, API uses `FOR UPDATE` with console_id matching).
- **Impact:** False positive duplicate warnings (client warns about user's own bookings on any console, server checks actual console-level conflicts). Confusing UX.
- **Severity:** MEDIUM

#### M3: n8n Webhook Env Vars Empty
- **Files:** `/root/psvibe-sales-bot/bot/__init__.py:1438-1439`
- **Root Cause:** `N8N_SESSION_WEBHOOK` and `N8N_BOOKING_WEBHOOK` default to `""` (empty string). The n8n integration (`_post_n8n_booking_reminder`, `_post_n8n_session_reminder`) checks for non-empty before firing. If n8n is expected to handle restart-proof timers or booking reminders, it's currently inactive.
- **Impact:** Staff booking reminders (10-min-before, auto-cancel) won't fire via n8n. Restart-proof timers won't work.
- **Severity:** MEDIUM

#### M4: No Error Recovery in Customer Bot When API Fails Mid-Flow
- **File:** `/root/psvibe-sales-bot/customer_bot/booking_handlers.py`
- **Root Cause:** If `_api_get("fetch_console_status")` or `_api_get("search-bookings")` fails (timeout, 500), the customer bot shows "⚠️ Game list မရဘူး" or returns empty slots. There's no retry logic and no way for the user to retry without restarting the booking flow.
- **Impact:** Customer booking flow aborts silently; user has to restart from the beginning.
- **Severity:** MEDIUM

#### M5: `fetch_console_status` Returns Empty List on API Failure — Silent Data Loss
- **File:** `/root/psvibe-sales-bot/bot/__init__.py:348-385`
- **Root Cause:** On API failure, `fetch_console_status()` logs a warning and returns `[]`. This causes the console selection keyboards to be empty, showing "⚠️ Free console မရှိပါ" to the staff.
- **Impact:** Staff can't book sessions during API downtime. No graceful degradation.
- **Severity:** MEDIUM

#### M6: `member_wallets` Staleness Window (10-15 min) During Booking
- **File:** `/root/psvibe_api_server/app.py` — `_fetch_wallet_mins_from_mysql` (10 min), `_fetch_member_data_from_mysql` (15 min)
- **Root Cause:** Wallet balance reads have a 10-15 minute staleness window. If a member tops up between being cached and booking, the customer bot shows stale balance (or wrong "insufficient balance" warning). The actual wallet deduction at sale time uses live balance, but the booking-time warning is misleading.
- **Impact:** Customer may be told they can't book (low balance) when they just topped up. Or vice versa — told they have balance but wallet was drained by another concurrent session.
- **Severity:** MEDIUM

#### M7: `_SESSION_TOTAL_MINS` Persistence Gap
- **File:** `/root/psvibe-sales-bot/bot/handlers/booking_flow.py` + `/root/psvibe-sales-bot/bot/session_reminder_store.py`
- **Root Cause:** `_SESSION_TOTAL_MINS` is saved to disk via `persist_reminder()`, but the weekly cleanup task in `cleanup_stale_reminders_async` can purge entries while sessions are still active (if `_is_session_active` returns False due to API blip).
- **Impact:** On session recovery after restart, accumulated total_plan_mins may be lost, showing wrong "Plan: X min" in reminder messages.
- **Severity:** MEDIUM

---

### 🟢 LOW (Quality / Maintenance)

---

#### L1: Dead GSheet Fallback Code Everywhere
- **Files:** `/root/psvibe-sales-bot/bot/__init__.py` — `create_booking()`, `end_booking()`, `fetch_console_status()`, etc.
- **Root Cause:** Every function has `if _HAS_API: ... else: GSheet fallback`. The fallback code references GSheet functions (`get_booking_sh()`, `sh.append_row()`) that are no longer the primary data store. This creates maintenance burden and risk of accidentally writing to old sheets.
- **Severity:** LOW

#### L2: `api_bookings_create` Handles Two Incompatible Formats
- **File:** `/root/psvibe_api_server/app.py:1882-2028`
- **Root Cause:** One endpoint handles both customer bot format (with `customerName`, `date`, `timeSlot`) and staff format (with `console_id`, `member_id`). The format detection is brittle — it checks for `customerName` presence. If a staff call accidentally includes `customerName`, it routes through the wrong code path.
- **Severity:** LOW

#### L3: `_post_n8n_session_reminder` — Dead/Unused Function
- **File:** `/root/psvibe-sales-bot/bot/handlers/booking_flow.py:247`
- **Root Cause:** This function posts to n8n but is never called from any handler. `_remind_loop` handles all reminders directly. The function exists as dead code.
- **Severity:** LOW

#### L4: No Input Validation on `duration_mins` in Staff Walk-In Path
- **File:** `/root/psvibe-sales-bot/bot/handlers/booking.py:step_book_mins()`
- **Root Cause:** `step_book_mins` allows free-text minutes entry. `_do_create_booking` sends the value to `api_start_console_session` which accepts any integer. A typo like `99999` could create a session with absurd duration.
- **Severity:** LOW

#### L5: Inconsistent Key Names (`console_id` vs `consoleId`)
- **Files:** Throughout all bot handlers and API responses
- **Root Cause:** API returns `console_id` in DB rows but the API response mapping code creates BOTH `console_id` and `consoleId` fields. Bot handlers sometimes use one, sometimes the other. This works due to both keys being present, but is fragile.
- **Severity:** LOW

#### L6: `_delete_session_game` Not Exported as Async
- **File:** `/root/psvibe-sales-bot/bot/handlers/booking.py` importing `_delete_session_game` from `bot`
- **Root Cause:** `_delete_session_game` is a sync function that calls `api_delete_session_game` via the API. It's called from `_do_create_booking` (async) without `asyncio.to_thread`, potentially blocking the event loop.
- **Severity:** LOW

---

## 2. Upgrade Plan — Prioritized Phases

### Phase 1: Critical Fixes (Data Integrity & Race Conditions)

| # | Fix | Files | Effort |
|---|-----|-------|--------|
| 1.1 | **Add `console_id` index to `console_booking`** | DB migration | 5 min |
| 1.2 | **Fix Discord bot to route through API** — Replace direct `INSERT` with `POST /api/bookings` call, or at minimum add conflict check + console_status sync | `bot.js:812` | 1h |
| 1.3 | **Move checkin guard INSIDE transaction** — In `api_booking_checkin`, move the `existing = _mysql_query_one(...)` check into the transaction block with `FOR UPDATE` on ALL Active rows for that console | `app.py:1260-1290` | 30 min |
| 1.4 | **Remove or hard-disable `POST /api/create_booking`** — Either delete the endpoint or make it unconditionally return a deprecation error. All callers should use `POST /api/bookings` or `POST /api/consoles/start-session` | `app.py:1331` | 15 min |
| 1.5 | **Move `_sync_console_status` into transaction blocks** — In `api_bookings_create`, `api_booking_cancel`, `api_end_booking`, include the console_status update in the same transaction (not after commit) | `app.py:1956, 1849, 1694` | 45 min |

### Phase 2: Structural Improvements

| # | Fix | Files | Effort |
|---|-----|-------|--------|
| 2.1 | **Unify timer systems** — Remove `session_timer.py` → have `api_booking_checkin` call the Sale Bot's timer via API or shared module. Single source of truth for session timers | `session_timer.py`, `booking_flow.py` | 2h |
| 2.2 | **Add state stack for staff booking back navigation** — Implement a proper `_bk_state_stack` (like customer bot) so Back always returns exactly one step | `booking.py` | 1.5h |
| 2.3 | **Add dedicated `GET /api/available-slots?date=&console_type=`** endpoint that returns availability with conflict resolution done server-side (not on the bot) | `app.py` (new endpoint) + `booking.py` | 2h |
| 2.4 | **Split `POST /api/bookings` into two endpoints**: `POST /api/bookings` (customer format) and `POST /api/sessions/start` (staff walk-in). Clear separation, no format sniffing | `app.py` | 1h |
| 2.5 | **Fix `step_sbk_console` back button** — `BTN_BACK` should return to `SBK_TIME` (time selection), not restart the flow | `booking.py:295-299` | 10 min |
| 2.6 | **Add retry + graceful degradation for API calls in customer bot** — Wrap `_api_get`/`_api_post` calls with retry (3x) and show "ခဏစောင့်ပါ — ပြန်ကြိုးစားနေသည်" instead of silent failures | `customer_bot/booking_handlers.py` | 1h |
| 2.7 | **Add MAX_SESSION_MINS validation to ALL booking paths** — 1440 min cap should be enforced in `api_bookings_create` (server-side), not just in bot handlers | `app.py:1882` | 15 min |

### Phase 3: Feature Upgrades & Polish

| # | Fix | Files | Effort |
|---|-----|-------|--------|
| 3.1 | **Live wallet balance at booking time** — Add `GET /api/wallet/live/{member_id}` that bypasses the 10-min cache for booking-critical reads | `app.py` (new endpoint) | 30 min |
| 3.2 | **Auto-cancel expired pending bookings** — Add background task that cancels `pending` bookings older than 24h (or with past start_time) | `app.py` (startup task) | 1h |
| 3.3 | **Add booking conflict API** — `POST /api/booking-conflicts` endpoint that accepts `{date, time, duration_mins, console_id}` and returns conflicting bookings. Use this from ALL bots before submission | `app.py` (new endpoint) | 1h |
| 3.4 | **Add booking history view for customers** — Customer bot: "📋 My Bookings" button showing upcoming + past bookings from `search-bookings?telegram_chat_id=` | `customer_bot/` | 1.5h |
| 3.5 | **Email/SMS booking confirmation** — Post-booking hook to send confirmation via customer's registered phone/email | n8n workflow or new endpoint | 2h |
| 3.6 | **Console availability heatmap** — Dashboard view showing hourly availability for next 7 days, color-coded by # free consoles | Dashboard SPA | 3h |
| 3.7 | **Waitlist auto-notify on cancel** — When a booking is cancelled, automatically notify the next waitlisted customer for that date/time/console-type | `app.py` + `waitlist.py` | 2h |

---

## 3. Recommendations for Error-Free Operation

### Architecture
1. **Single Booking API Gateway**: ALL booking mutations (create, checkin, cancel, end) must go through the API server. Block direct DB access from bots/discord. Add DB user permission restrictions (read-only for bot DB users, write-only for API user).

2. **Idempotency Keys**: Add `idempotency_key` to all booking mutation endpoints. Clients generate a UUID; server stores it in a new `idempotency_keys` table with TTL. Prevents double-submit from retry storms.

3. **Booking State Machine in DB**: Instead of scattered status transitions across 3 bots and 7 endpoints, implement booking status transitions as a state machine in the API layer with allowed transitions:
   ```
   pending → confirmed | rejected | cancelled
   confirmed → Active | cancelled | pending_check_in
   Active → Done | cancelled
   ```
   Reject invalid transitions at the API level.

### Monitoring
4. **Booking Anomaly Alerts**: Add alerts for:
   - Two Active bookings on same console (scan every 5 min)
   - Booking created but console_status not updated within 10s
   - Booking with duration > 480 min (8 hours — likely typo)
   - Multiple bookings from same `telegram_chat_id` within 1 minute (double-click)

5. **Health Check Endpoint**: `GET /api/bookings/health` that verifies:
   - `console_booking` ↔ `console_status` consistency (Active bookings have Active consoles)
   - No duplicate Active consoles
   - No bookings with `start_time` in the future but status=Active

### Testing
6. **Concurrency Test Suite**: Write tests that:
   - Fire 5 simultaneous `POST /api/bookings/checkin` for the same console
   - Create bookings at the exact same datetime for the same console type
   - Extend session while another process ends it
   
7. **DB Index Review**: Before deployment, review all query patterns against `console_booking` and ensure covering indexes:
   ```sql
   ALTER TABLE console_booking ADD INDEX idx_console_status (console_id, status);
   ALTER TABLE console_booking ADD INDEX idx_date_console (booking_date, console_id, status);
   ```

### Process
8. **Code Review Checklist for Booking Changes**: Any PR touching booking logic must verify:
   - Transaction wrapping for all multi-statement operations
   - `FOR UPDATE` on rows that will be modified
   - `_sync_console_status` called within transaction
   - Input validation (duration 1-1440, date not in past, etc.)
   - Backward compatibility for bot format changes

---

## 4. Summary by Severity

| Severity | Count | Key Issues |
|----------|-------|------------|
| CRITICAL | 5 | Discord bypass, checkin race, deprecated endpoint, missing index, sync-after-commit |
| HIGH | 8 | Overlapping endpoints, dual timers, back button wrong target, hardcoded slots, auto-assign race, missing end_time, empty member_id, state flow bug |
| MEDIUM | 7 | n8n inactive, API failure handling, wallet staleness, duplicate check double-counting, timer persistence gap |
| LOW | 6 | Dead GSheet code, format sniffing, dead n8n function, missing validation, inconsistent keys, sync-in-async |

**Total Issues Found:** 26

**Immediate Action Items (this week):**
1. Add `console_id` DB index (5 min, no downtime)
2. Fix Discord bot to use API (1h)
3. Fix checkin race condition (30 min)
4. Remove deprecated endpoint or hard-disable it (15 min)
5. Move `_sync_console_status` into transactions (45 min)
