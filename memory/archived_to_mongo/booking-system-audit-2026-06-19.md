# PS VIBE Booking System — Full Audit Report
**Date:** 2026-06-19  
**Auditor:** Kora (Subagent, DeepSeek V4 Pro)  
**Scope:** Every booking creation, approval, checkin, session start, and cancel path across API server + both bots

---

## 1. All Booking Paths (Numbered)

### Path 1 — Customer Bot Booking (Customer → API)
**Flow:** Customer Bot `bk_confirm()` → `_submit_booking()` → `POST /api/bookings`
- Customer selects date, time, console type, duration, game
- `_get_available_consoles()` filters busy consoles (client-side)
- `_submit_booking()` auto-assigns first free matching console
- Final availability re-check before submission
- Duplicate booking check (same user, same date, overlapping time)
- API endpoint does FOR UPDATE conflict check + INSERT in transaction

**File:** `customer_bot/booking_handlers.py:2073-2473` + `app.py:2278-2420`

### Path 2 — Staff Bot Booking (Staff → API)
**Flow:** Staff Bot `step_sbk_confirm()` → `POST /api/bookings`
- Staff fills all booking details including explicit console_id
- Pre-submit: calls `POST /api/booking-conflicts` for overlap check
- Submits with `source: "staff"`, `status: "confirmed"` (auto-confirmed)
- API endpoint does FOR UPDATE conflict check + INSERT

**File:** `bot/handlers/booking.py:703-933` + `app.py:2278-2420`

### Path 3 — Admin Approve Booking (Staff Bot → PATCH API)
**Flow:** `_do_booking_action()` → `PATCH /api/bookings/{id}/status`
- Auto-assign: queries free consoles, pre-checks each via `/api/booking-conflicts`
- Sends PATCH with `status: "confirmed"` + optional `consoleId`
- API: optimistic lock (WHERE status IN ('pending')) + overlap check inside transaction
- Conflict check: `status IN ('confirmed','pending','pending_check_in','Active')`

**File:** `bot/handlers/admin_bookings.py:257-465` + `app.py:1378-1448`

### Path 4 — Console Start-Session (Staff → API)
**Flow:** `POST /api/consoles/start-session`
- Pre-check: console_status not Active (NO lock)
- Auto-links confirmed bookings within ±30 min
- Creates or transitions booking to Active
- Console_status set to Active inside transaction

**File:** `app.py:1848-1940`

### Path 5 — Walk-In Session Start (Staff → API)
**Flow:** `POST /api/sessions/start`
- Checks console_status not Active (pre-check, no lock)
- FOR UPDATE lock on console_status inside transaction
- Checks for existing Active booking on same console
- Links checked_in bookings or creates new Active booking

**File:** `app.py:2140-2278`

### Path 6 — Booking Checkin (Staff → API)
**Flow:** `POST /api/bookings/checkin`
- Marks booking status → `checked_in`
- Optional: overrides console_id
- No conflict check (by design — only marks arrival)

**File:** `app.py:1232-1315`

### Path 7 — Booking Cancel (Staff → API)
**Flow:** `POST /api/bookings/cancel`
- Cancels only non-Active/non-Done bookings
- Frees console_status inside transaction
- Notifies customer via Telegram

**File:** `app.py:2031-2100`

### Path 8 — Disc-Game Conflict Check (Bot-side utility)
**Flow:** `check_disc_session_conflict()` 
- Checks Google Sheets (now returns None — Sheets removed)
- Effectively a no-op in current deployment

**File:** `bot/__init__.py:537-610`

### Path 9 — Booking Conflict Check (Dedicated endpoint)
**Flow:** `POST /api/booking-conflicts`
- Queries: `status IN ('pending','confirmed','pending_check_in','Active')`
- Time-range overlap: `NOT (end_time <= %s OR start_time >= %s)`
- No locking (read-only endpoint)

**File:** `app.py:4197-4265`

### Path 10 — Legacy create_booking (DEPRECATED — hard-disabled)
**Flow:** `POST /api/create_booking` → returns 410 Gone
- No longer executable. Safely dead.

**File:** `app.py:1316-1377`

---

## 2. Protection Status for Each Path

| # | Path | Conflict Check | FOR UPDATE | Status |
|---|------|---------------|------------|--------|
| 1 | Customer Bot → POST /api/bookings | ✅ Server-side FOR UPDATE + overlap check | ✅ | ✅ Protected |
| 2 | Staff Bot → POST /api/bookings | ✅ Pre-check + server-side FOR UPDATE | ✅ | ✅ Protected |
| 3 | Admin Approve → PATCH /api/bookings/{id}/status | ✅ Optimistic lock + overlap check | ⚠️ No FOR UPDATE | ⚠️ Partial |
| 4 | Console Start-Session | ❌ No overlap check against pending/confirmed | ❌ No FOR UPDATE | ❌ Unprotected |
| 5 | Walk-In Session Start | ⚠️ Only checks Active (misses pending/confirmed) | ✅ FOR UPDATE on console_status | ⚠️ Partial |
| 6 | Booking Checkin | N/A (read-only status change) | N/A | ✅ Protected |
| 7 | Booking Cancel | ✅ Only cancels non-Active/Done | ❌ No FOR UPDATE | ⚠️ Partial |
| 8 | Disc-Game Conflict | N/A (returns empty — Sheets removed) | N/A | N/A |
| 9 | Booking Conflicts API | N/A (read-only) | N/A | N/A |
| 10 | Legacy create_booking | N/A (hard-disabled, returns 410) | N/A | ✅ Protected |

---

## 3. Race Condition Analysis

### R1: Double Approval Race (PATCH endpoint)
**Risk:** Two staff members approve the same pending booking simultaneously.  
**Mitigation:** Optimistic lock — `WHERE status IN ('pending')`. One wins, the other gets `affected=0`.  
**Verdict:** ✅ SAFE

### R2: Auto-Assign TOCTOU (Admin approve)
**Risk:** Staff bot pre-checks `/api/booking-conflicts` for candidate consoles, then sends `consoleId` in PATCH. Between pre-check and PATCH, another booking can claim the same console.  
**Mitigation:** The PATCH endpoint re-checks overlap (line 1406-1428), so if a conflict exists by the time the PATCH runs, it will reject. However, the check uses NO FOR UPDATE, so two concurrent approves targeting different bookings could both see "no conflict" and both succeed.  
**Verdict:** ⚠️ PARTIALLY MITIGATED — No FOR UPDATE on the overlap check means simultaneous transactions could both pass

### R3: Console Start-Session No-Lock Race
**Risk:** Two staff members start sessions on the same console concurrently.  
- Pre-check: `console_status != Active` (no lock, line 1862)  
- Both pass → both enter transaction  
- One updates console_status to Active, the other also updates → one session overwrites the other silently  
**Mitigation:** NONE. The transaction does NOT re-check console_status with FOR UPDATE.  
**Verdict:** ❌ CRITICAL — Two simultaneous start-session calls on same console will both succeed

### R4: Customer Booking Concurrent Submissions
**Risk:** Two customers book the same console at the same time.  
**Mitigation:** FOR UPDATE on the conflict query locks the row until INSERT commits.  
**Verdict:** ✅ SAFE

### R5: Walk-In Session Bypasses Pending Bookings
**Risk:** Staff starts a walk-in session (`POST /api/sessions/start`) that overlaps with a pending customer booking. The endpoint only checks `status='Active'` (line 2180+), not pending/confirmed.  
**Mitigation:** NONE — Only Active bookings are checked.  
**Verdict:** ❌ HIGH — Staff walk-in can preempt customer bookings

### R6: Start-Session Bypasses Pending/Confirmed Bookings
**Risk:** Same as R5 but for `consoles/start-session`. Only looks for confirmed bookings to auto-link (line 1871), but doesn't check if another pending/confirmed booking exists on the same console.  
**Mitigation:** NONE.  
**Verdict:** ❌ HIGH

---

## 4. Conflict Check Implementation Comparison

All critical paths that DO check conflicts use the same status filter:

| Location | Status Filter |
|----------|--------------|
| `api_bookings_create` (line 2352) | `IN ('pending','confirmed','pending_check_in','Active')` |
| `api_update_booking_status` (line 1412) | `IN ('confirmed','pending','pending_check_in','Active')` |
| `api_booking_conflicts` (line 4239) | `IN ('pending','confirmed','pending_check_in','Active')` |
| `api_sessions_start` (line 2180) | `= 'Active'` ← **INCONSISTENT!** |
| `api_consoles/start-session` | **NO CHECK** ← **MISSING!** |
| Customer Bot `_get_available_consoles` | Excludes 'cancelled','done','rejected' ← equivalent |
| Customer Bot `_get_available_slots` | Excludes 'cancelled','done','rejected' ← equivalent |

**Overlap logic comparison:**
- `api_bookings_create` uses: `(start_time <= %s AND end_time > %s) OR (start_time < %s AND end_time >= %s) OR (start_time >= %s AND end_time <= %s)` — 3-condition overlap
- `api_update_booking_status` uses: `NOT (end_time <= %s OR start_time >= %s)` — 2-condition overlap (De Morgan's equivalent)
- `api_booking_conflicts` uses: `NOT (end_time <= %s OR start_time >= %s)` — same as above
- Customer bot uses: `b_start < target_end AND b_end > target_start` — standard overlap

All overlap logics are mathematically equivalent. ✅ No disagreement.

---

## 5. Edge Case Analysis

### Empty/NULL console_id
- `api_bookings_create`: When console_id is empty, checks ALL consoles of matching type. Auto-assign NOT done at API layer — left empty in INSERT. ✅ Handled (no conflict check needed since no specific console claimed)
- `api_update_booking_status` (approve): If no consoleId in req, stall assigns none. Auto-assign done in bot layer before PATCH. ⚠️ If bot fails to auto-assign, booking stays confirmed without console
- `api_sessions/start`: Requires console_id (returns 400 if missing). ✅ Enforced

### Past Dates
- `api_bookings_create`: Validates `start_dt < now_mmt()` → returns 400. ✅
- `api_sessions/start`: No date validation. ⚠️ Could create session with past date
- `api_update_booking_status`: No date validation. ⚠️ Could approve past-dated bookings
- Customer bot: Date keyboard only shows future dates. ✅

### Simultaneous Bookings on Different Consoles
- Conflict checks are console-id-scoped. Two bookings on different consoles at the same time are allowed. ✅ Correct behavior.

### Console Status Drift
- `_sync_console_status()` called after every mutation. ✅
- Active session resume on startup. ✅
- Edge case: if `_sync_console_status()` fails silently, console may show wrong status until next mutation.

---

## 6. MySQL Transaction Isolation & Locking

### mysql_db.py (pymysql, used by some queries)
- **Pool:** Single persistent connection
- **Auto-commit:** Every query is followed by `conn.commit()` — effectively READ UNCOMMITTED between queries
- **Isolation level:** Default pymysql (REPEATABLE READ, but irrelevant with per-query auto-commit)
- **FOR UPDATE:** NEVER used in mysql_db.py queries

### app.py (mysql.connector, used by mutation endpoints)
- **Connection:** Fresh connection per request via `_mc.connect()`
- **Transactions:** Explicit `conn.start_transaction()` with `conn.commit()`/`conn.rollback()`
- **Isolation level:** MySQL default REPEATABLE READ (not explicitly set)
- **FOR UPDATE:** Used in:
  - `api_bookings_create` (line 2352, 2366) ✅
  - `api_sessions_start` (line 2180, 2202) ✅
  - NOT in `api_update_booking_status` ❌
  - NOT in `api_consoles/start-session` ❌
  - NOT in `api_bookings/cancel` ❌
  - NOT in `api_bookings/checkin` ❌

---

## 7. Recommendations — Ranked by Severity

### 🔴 CRITICAL

**C1: Add FOR UPDATE to `consoles/start-session` endpoint**
- File: `app.py:1862-1925`
- Problem: No lock on console_status check; two concurrent starts on same console both succeed
- Fix: Move the console_status Active check inside the transaction with FOR UPDATE (mirror `sessions/start` pattern)
- **Immediate fix needed**

**C2: Add overlap/conflict check to `consoles/start-session`**
- File: `app.py:1871-1920`
- Problem: Auto-links confirmed bookings but never checks if another pending/confirmed booking exists for the same console at the same time
- Fix: Add a conflict check query inside the transaction, similar to `api_bookings_create` pattern:
  ```python
  cur.execute(
      "SELECT id FROM console_booking WHERE console_id=%s"
      " AND status IN ('pending','confirmed','pending_check_in','Active')"
      " AND id != %s"
      " AND NOT (end_time <= %s OR start_time >= %s) LIMIT 1 FOR UPDATE",
      (console_id, booking_id, _now_ref, _now_ref)
  )
  ```
- **Immediate fix needed**

### 🔴 HIGH

**H1: Add FOR UPDATE to `api_update_booking_status` overlap check**
- File: `app.py:1406-1428`
- Problem: Overlap check on approval runs inside a transaction but WITHOUT row-level locking. Two concurrent approvals for different bookings on the same console could both pass.
- Fix: Add `FOR UPDATE` to the conflict detection SELECT query (line 1411)
- **Before next release**

**H2: Add pending/confirmed conflict check to `sessions/start`**
- File: `app.py:2180-2202`
- Problem: Only checks `status='Active'` on the console. A staff walk-in can preempt a pending customer booking.
- Fix: Change the Active-only check to cover all active statuses:
  ```python
  cur.execute(
      "SELECT id FROM console_booking WHERE console_id=%s"
      " AND status IN ('pending','confirmed','pending_check_in','Active')"
      " AND NOT (end_time <= %s OR start_time >= %s) LIMIT 1 FOR UPDATE",
      (console_id, _now_ref, _now_ref)
  )
  ```
- **Before next release**

### 🟡 MEDIUM

**M1: Add FOR UPDATE to `api_bookings/cancel`**
- File: `app.py:2053`
- Problem: Cancel uses a WHERE clause with status check but no row lock. In theory, a session could be started between the SELECT and UPDATE.
- Fix: Add FOR UPDATE to the SELECT at line 2039
- **Next sprint**

**M2: Close auto-assign TOCTOU window in admin_bookings.py**
- File: `bot/handlers/admin_bookings.py:316-330`
- Problem: Pre-checks each candidate console via `/api/booking-conflicts` (separate HTTP call), then sends `consoleId` in PATCH. Between calls, another booking could claim the console.
- Fix: Already partially protected by the PATCH endpoint's overlap check (H1 above). If H1 is fixed, this is safe.
- **Depends on H1**

**M3: Add date validation to `sessions/start`**
- File: `app.py:2140`
- Problem: No validation of `booking_date` — could be past or future
- Fix: Add date validation similar to `api_bookings_create`
- **Next sprint**

### 🟢 LOW

**L1: Standardize conflict check to a shared helper function**
- All three implementations (create, approve, conflicts) use slightly different overlap queries
- Extract to `_check_booking_conflicts(console_id, start_dt, end_dt, exclude_id)` in app.py
- **Tech debt — whenever convenient**

**L2: Migrate mysql_db.py from auto-commit to proper connection pooling**
- Current: single connection with per-query auto-commit — no isolation guarantees
- Impact: Used for read queries mostly, so low immediate risk
- **Architecture improvement — future**

**L3: Remove dead Google Sheets code from `check_disc_session_conflict`**
- File: `bot/__init__.py:537-610`
- `get_booking_sh()` returns `None` so this function always returns `""` (no conflict)
- Either fix to use MySQL or remove the function
- **Cleanup — whenever**

**L4: Console status may drift after `_sync_console_status()` failure**
- If sync fails silently (caught by broad except), console may show wrong status
- Add alert/monitoring for sync failures
- **Monitoring improvement**

---

## 8. Code Needing Immediate Fix

### FIX 1: `consoles/start-session` — Missing locking + conflict check
**File:** `app.py`, lines 1860-1925
**Issue:** The pre-check on console_status (line 1862) happens OUTSIDE the transaction without FOR UPDATE. Two concurrent calls will both pass and both create sessions. Also, no overlap check against other pending/confirmed bookings.
```python
# CURRENT (broken):
cs = _mysql_query_one("SELECT status FROM console_status WHERE console_id=%s", (console_id,))
# ... later in transaction, no re-check with FOR UPDATE

# FIX: Move console_status check INSIDE transaction with FOR UPDATE,
# and add overlap conflict check
```

### FIX 2: `sessions/start` — Missing pending/confirmed conflict check
**File:** `app.py`, lines 2180-2202
**Issue:** Only checks `status='Active'`. A staff walk-in can overlap with a pending customer booking.
```python
# CURRENT (incomplete):
cur.execute(
    "SELECT id FROM console_booking WHERE console_id=%s AND status='Active' LIMIT 1 FOR UPDATE",
    (console_id,)
)

# FIX: Check all active statuses
cur.execute(
    "SELECT id FROM console_booking WHERE console_id=%s"
    " AND status IN ('pending','confirmed','pending_check_in','Active')"
    " AND NOT (end_time <= %s OR start_time >= %s) LIMIT 1 FOR UPDATE",
    (console_id, _now_ref, _now_ref)
)
```

### FIX 3: `api_update_booking_status` — Missing FOR UPDATE on overlap check
**File:** `app.py`, lines 1410-1428
**Issue:** Overlap check runs inside transaction but without row lock. Two concurrent approvals could both pass.
```python
# CURRENT (missing FOR UPDATE):
_app_cur.execute(
    "SELECT id FROM console_booking WHERE console_id=%s"
    " AND status IN ('confirmed','pending','pending_check_in','Active')"
    " AND id != %s"
    " AND NOT (end_time <= %s OR start_time >= %s)"
    " LIMIT 1",
    (_bk["console_id"], booking_id, _bk["start_time"], _bk["end_time"])
)

# FIX: Add FOR UPDATE
```

---

## 9. Summary

| Metric | Count |
|--------|-------|
| Total booking paths | 10 |
| ✅ Fully protected | 5 |
| ⚠️ Partially protected | 2 |
| ❌ Unprotected | 1 |
| N/A (read-only/dead) | 2 |
| CRITICAL issues | 2 |
| HIGH issues | 2 |
| MEDIUM issues | 3 |
| LOW issues | 4 |

**Bottom line:** The primary customer booking path (Path 1) and staff booking path (Path 2) are well-protected with FOR UPDATE locking. The critical gaps are in the session-start paths (Paths 4 and 5) which lack proper conflict checking and row locking. The approval path (Path 3) has a missing FOR UPDATE that creates a small-but-real race window. Fixing the 3 CRITICAL+HIGH items will close the remaining gaps.
