# Console Conflict Report
**Generated:** 2026-06-18 20:28 UTC (2026-06-19 02:58 MMT)
**Database:** MySQL `psvibe_api` (production) + SQLite `/root/psvibe-sales-bot/psvibe.db` (bot cache)

---

## Executive Summary

**3 confirmed booking conflicts found** across 3 different dates. All involve the same console double-booked at overlapping times. The recent bug fix (only mark consoles "Reserved" for bookings within 60 minutes) was applied correctly — all console_status rows now show "Free" — but **the conflicts in the booking table remain unresolved**.

Additionally, the SQLite bot DB has 2 orphaned "Active" bookings from May 28-29 with no console/customer info.

---

## Database Overview

| Database | Location | Tables Used |
|----------|----------|-------------|
| MySQL    | `psvibe_api` (localhost) | `console_booking` (544 rows), `console_status` (10 rows) |
| SQLite   | `/root/psvibe-sales-bot/psvibe.db` | `bookings`, `consoles` (empty), `v_active_bookings` |

**Booking Status Distribution (MySQL):**
| Status     | Count |
|------------|-------|
| Done       | 296   |
| cancelled  | 36    |
| confirmed  | 13    |
| rejected   | 5     |
| Waiting    | 1     |

---

## 🔥 CONFLICTS FOUND: Same Console + Same Date + Overlapping Time

### Conflict 1: 🟥 C-03 — June 19
| BK# | Console | Date | Time (MMT) | Dur | Status | Customer |
|-----|---------|------|------------|-----|--------|----------|
| 473 | C-03 | 2026-06-19 | 12:00 → 12:30 | 30m | confirmed | ZWE LIN HTET |
| 435 | C-03 | 2026-06-19 | 12:00 → 15:00 | 180m | confirmed | Aung Myo Thant |

> ⚠️ **Overlap: 12:00–12:30** — Both bookings occupy C-03 simultaneously. BK#435 (3 hours) completely engulfs BK#473 (30 min).

### Conflict 2: 🟥 C-01 — June 20
| BK# | Console | Date | Time (MMT) | Dur | Status | Customer |
|-----|---------|------|------------|-----|--------|----------|
| 488 | C-01 | 2026-06-20 | 12:00 → 14:00 | 120m | confirmed | SuperCatz |
| 484 | C-01 | 2026-06-20 | 13:00 → 14:00 | 60m | confirmed | Hsu Myat |

> ⚠️ **Overlap: 13:00–14:00** — Hsu Myat's hour is entirely inside SuperCatz's 2-hour block.

### Conflict 3: 🟥 C-10 — June 21
| BK# | Console | Date | Time (MMT) | Dur | Status | Customer |
|-----|---------|------|------------|-----|--------|----------|
| 531 | C-10 | 2026-06-21 | 11:00 → 14:00 | 180m | confirmed | Min Khant Zaw |
| 539 | C-10 | 2026-06-21 | 13:00 → 16:00 | 180m | confirmed | HtetMyatAung |

> ⚠️ **Overlap: 13:00–14:00** — One hour shared between both 3-hour bookings.

---

## All Non-Cancelled/Non-Rejected Bookings (Forward View)

### June 19 (all confirmed)
| BK# | Console | Time | Dur | Status | Customer | Game |
|-----|---------|------|-----|--------|----------|------|
| 435 | C-03 | 12:00–15:00 | 180m | confirmed | Aung Myo Thant | Mortal Kombat 1 |
| 473 | C-03 | 12:00–12:30 | 30m | confirmed | ZWE LIN HTET | Mortal Kombat 1 |
| 442 | C-10 | 12:00–15:00 | 180m | confirmed | Lolly | Split Fiction |
| 459 | C-02 | 15:00–16:00 | 60m | confirmed | Htet Aung Linn | Any |
| 540 | C-10 | 18:00–19:30 | 90m | confirmed | Si Thu | FC 26 |

### June 20 (all confirmed + 1 Waiting)
| BK# | Console | Time | Dur | Status | Customer | Game |
|-----|---------|------|-----|--------|----------|------|
| 488 | C-01 | 12:00–14:00 | 120m | confirmed | SuperCatz | It Takes Two |
| 484 | C-01 | 13:00–14:00 | 60m | confirmed | Hsu Myat | Resident Evil 9 |
| 487 | C-01 | 14:00–16:00 | 120m | confirmed | Wai Yan | FC 26 |
| 513 | C-01 | 16:00–17:00 | 60m | confirmed | Nay linn | It Takes Two |
| 536 | C-01 | (see note) | 0m | Waiting | Test C-01 Customer | — |

> ⚠️ **BK#536**: booking_date=2026-06-20 but start_time=2026-06-18 16:00:36. Start time is in the past. Status is "Waiting". Likely a test/abandoned entry — no end_time, duration=0, console=C-01. **Recommend: cancel or delete.**

### June 21
| BK# | Console | Time | Dur | Status | Customer | Game |
|-----|---------|------|-----|--------|----------|------|
| 531 | C-10 | 11:00–14:00 | 180m | confirmed | Min Khant Zaw | FC 26 |
| 539 | C-10 | 13:00–16:00 | 180m | confirmed | HtetMyatAung | FC 26 |

### June 22
| BK# | Console | Time | Dur | Status | Customer | Game |
|-----|---------|------|-----|--------|----------|------|
| 471 | C-01 | 10:00–11:00 | 60m | confirmed | Aung Myat Htet | — |

### June 24
| BK# | Console | Time | Dur | Status | Customer | Game |
|-----|---------|------|-----|--------|----------|------|
| 542 | C-09 | 13:00–15:00 | 120m | confirmed | Nyan Swan Htet | Any |

---

## Console State Analysis

### Current `console_status` Table
All 10 consoles show **"Free"** — no stale reservations:

| Console | Status | Type | Current Game | Current Member | Start Time |
|---------|--------|------|-------------|----------------|------------|
| C-01 | Free | PS5 | NULL | NULL | NULL |
| C-02 | Free | PS5 | NULL | NULL | NULL |
| C-03 | Free | PS5 | NULL | NULL | NULL |
| C-04 | Free | PS5 | NULL | NULL | NULL |
| C-05 | Free | PS5 | NULL | NULL | NULL |
| C-06 | Free | PS5 | NULL | NULL | NULL |
| C-07 | Free | PS5 | NULL | NULL | NULL |
| C-08 | Free | PS5 | NULL | NULL | NULL |
| C-09 | Free | PS5 Pro | NULL | NULL | NULL |
| C-10 | Free | PS5 Pro | NULL | NULL | NULL |

✅ **Console state is clean.** The recent bug fix (restrict "Reserved" to bookings within 60 minutes) is working correctly. No stale "Reserved" states remain.

### June 18 Walk-In Audit (Done bookings)
✅ **Zero conflicts.** All 30+ "Done" bookings on June 18 were clean — no console had overlapping active sessions. The floor staff managed walk-ins correctly.

---

## SQLite Bot DB: Orphaned "Active" Bookings

2 stale records in `/root/psvibe-sales-bot/psvibe.db`:

| Booking ID | Date | Status | Console | Start Time |
|-----------|------|--------|---------|------------|
| BK-20260528--1831 | 5/28/2026 | Active | *(empty)* | 18:31 |
| BK-20260529--0009 | 5/29/2026 | Active | *(empty)* | 00:09 |

> These have no console_id, no member_id, no end_time. They are 3 weeks old and should be cleaned up.

---

## Root Cause Analysis

The booking approval system (`app.py`, booking confirmation around line 1395) lacks an **overlap check** before confirming a booking. The flow is:

1. Customer requests booking → "Waiting" status
2. Staff approves → status set to "confirmed"  
3. **No check**: "Is this console already booked at this time?"

The same is true for the booking creation endpoint (line 1328) which inserts directly with no overlap validation.

### The Bug That Was Fixed
Previous behavior: ALL confirmed bookings (regardless of date) set `console_status.status = 'Reserved'`.  
Fix applied: Only bookings starting within 60 minutes set "Reserved"; all others leave console "Free" for walk-ins.

**What was NOT fixed:** The existing conflicts in the `console_booking` table created before the fix.

---

## Recommended Fixes

### Immediate (Manual SQL)

```sql
-- 1. Resolve C-03 June 19 conflict: Keep BK#435 (180m, approved by PS VIBE), cancel BK#473
UPDATE console_booking SET status = 'cancelled', notes = CONCAT(COALESCE(notes,''), ' | Auto-cancelled: console conflict with BK#435') WHERE id = 473;

-- 2. Resolve C-01 June 20 conflict: Keep BK#488 (120m, approved by PS VIBE), cancel BK#484
UPDATE console_booking SET status = 'cancelled', notes = CONCAT(COALESCE(notes,''), ' | Auto-cancelled: console conflict with BK#488') WHERE id = 484;

-- 3. Resolve C-10 June 21 conflict: Keep BK#531 (180m, approved first), cancel BK#539
UPDATE console_booking SET status = 'cancelled', notes = CONCAT(COALESCE(notes,''), ' | Auto-cancelled: console conflict with BK#531') WHERE id = 539;

-- 4. Clean up abandoned test booking
UPDATE console_booking SET status = 'cancelled', notes = 'Auto-cancelled: abandoned test booking' WHERE id = 536;

-- 5. Clean up orphaned SQLite Active bookings
-- Run in SQLite: DELETE FROM bookings WHERE id IN ('BK-20260528--1831', 'BK-20260529--0009');
```

### Code Fix: Add Overlap Check

Add this check in `app.py` before confirming a booking (around line 1395):

```python
# Check for console time conflicts before confirming
_overlap_check = _mysql_query_one("""
    SELECT COUNT(*) as cnt FROM console_booking 
    WHERE console_id = %s 
    AND booking_date = %s 
    AND status IN ('confirmed', 'checked_in', 'Active')
    AND id != %s
    AND start_time < %s 
    AND end_time > %s
""", (_console_id, _booking_date, booking_id, _end_time, _start_time))

if _overlap_check and _overlap_check.get('cnt', 0) > 0:
    raise HTTPException(status_code=409, detail="Time slot conflict: console already booked for this time")
```

This same check should also be applied in the booking creation endpoint (around line 1328).

### Optional: Add UNIQUE Constraint (Defense in Depth)

```sql
-- Requires MySQL 8.0.13+ for functional indexes
-- This prevents future conflicts at the database level
-- NOTE: requires cleaning existing conflicts first!
ALTER TABLE console_booking 
ADD CONSTRAINT no_console_overlap 
CHECK (NOT EXISTS (
    SELECT 1 FROM console_booking cb2 
    WHERE cb2.console_id = console_booking.console_id 
    AND cb2.booking_date = console_booking.booking_date 
    AND cb2.id != console_booking.id 
    AND cb2.status IN ('confirmed', 'checked_in', 'Active')
    AND cb2.start_time < console_booking.end_time 
    AND cb2.end_time > console_booking.start_time
));
```

> ⚠️ MySQL CHECK constraints with subqueries may not be enforced in all versions. A trigger-based approach or application-level validation is more reliable.

---

## Verification After Fix

After applying the manual SQL fixes above, verify with:

```sql
-- Should return 0 rows (no conflicts)
SELECT a.id, a.console_id, a.booking_date, a.start_time, a.end_time, a.status,
       b.id as conflict_id, b.start_time as conflict_start, b.end_time as conflict_end
FROM console_booking a
JOIN console_booking b ON a.console_id = b.console_id 
    AND a.booking_date = b.booking_date 
    AND a.id < b.id
    AND a.status IN ('confirmed', 'checked_in', 'Active')
    AND b.status IN ('confirmed', 'checked_in', 'Active')
    AND a.start_time < b.end_time 
    AND b.start_time < a.end_time
ORDER BY a.booking_date, a.console_id;
```

---

## Summary

| Item | Status |
|------|--------|
| Confirmed booking conflicts | 🔴 3 found (C-03 Jun 19, C-01 Jun 20, C-10 Jun 21) |
| Console state (console_status) | 🟢 All "Free" — no stale reservations |
| June 18 walk-in overlaps | 🟢 None — clean operations |
| "Reserved"/"Active" statuses | 🟢 None in MySQL; 2 orphans in SQLite |
| Bug fix (60-min window) | 🟢 Working correctly |
| Overlap prevention code | 🔴 MISSING — needs to be added |
| BK#536 (test entry) | 🟡 Suspicious — recommend cancel |
