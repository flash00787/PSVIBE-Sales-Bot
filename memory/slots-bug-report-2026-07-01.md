# /slots Bug Debug Report — July 1, 2026 11:30 AM MMT

## Summary
The Discord bot `/slots` command showed **0/10 consoles available** because:
1. All 10 consoles had either Active sessions (2) or upcoming confirmed bookings (8) at 11:30 AM
2. BUT 2 of those statuses were **wrong** due to bugs in console_status sync logic

## Root Cause Chain

### Timeline (UTC → MMT+6:30)
| UTC Time | MMT Time | Event |
|----------|----------|-------|
| Jun 30 11:35 | Jun 30 18:05 | Booking #1181 created for C-07 (Active, 10:41-11:41) |
| Jul 01 03:23 | Jul 01 09:53 | Dashboard PUT #1181: status→confirmed, console→**C-08** (staff error) |
| Jul 01 04:11 | Jul 01 10:41 | Session started → timer scheduled for **C-08**, console_status C-08→Active |
| Jul 01 04:26–04:40 | Jul 01 10:56–11:10 | API server crashed/restarted **5 times**; each startup synced C-08 as Active |
| Jul 01 05:06 | Jul 01 11:36 | Timer crashed (MMT scope bug) — 5 min before end |
| Jul 01 05:12 | Jul 01 11:42 | Dashboard PUT #1181: console→**C-07** (fixed back, but too late!) |

## Bugs Found

### 🔴 BUG 1: dashboard_update_booking doesn't sync console_status on console_id change
- **File:** `/root/psvibe_api_server/dashboard_routes.py`, line ~295 (`dashboard_update_booking`)
- **Impact:** When booking #1181 was moved from C-08 to C-07 at 11:42 MMT, the old console C-08 was NOT freed and C-07 was NOT activated
- **Result:** C-08 console_status stayed "Active" (phantom), C-07 stayed "Free" (even though booking was Active)

### 🔴 BUG 2: session_timer.py MMT variable scope error
- **File:** `/root/psvibe_api_server/session_timer.py`, line ~110–147
- **Bug:** `MMT = timezone(timedelta(hours=6, minutes=30))` is defined inside `if start_time.tzinfo is None:` block, but `MMT` is used on line 147 outside that block in `actual_end.replace(tzinfo=MMT)`. When `start_time.tzinfo is not None`, MMT is never defined → `UnboundLocalError`
- **Impact:** Session timer for booking #1181 crashed at exactly 5-min-before-end (11:36 MMT), failing to send reminder
- **Also affected:** Booking #1201 timer crashed earlier at 04:03 UTC

### 🟡 BUG 3: fetch_console_status trusts console_status table blindly
- **File:** `/root/psvibe_api_server/app.py`, line ~609 (`api_fetch_console_status`)
- **Bug:** The endpoint queries console_status.status directly and only uses the LEFT JOIN for booking metadata. It does not cross-validate: if a console has an Active booking JOIN result but console_status says "Free", it should still show "Active". Conversely, if console_status says "Active" but no Active booking JOIN exists, it should not show "Active"
- **Fix needed:** Derive status from the booking JOIN, not from console_status

### 🟡 BUG 4: API server instability — 5 restarts in 15 minutes
- Between 04:26–04:40 UTC (10:56–11:10 MMT), the server restarted 5 times
- Each restart called `resume_active_timers()` → `_sync_console_status()` for Active bookings
- Since booking #1181 was on C-08 at that time, C-08 kept getting re-synced as Active

## Data State at 11:30 MMT

### console_status table (PERSISTED - has stale data):
```
C-01: Free     C-02: Reserved  C-03: Reserved  C-04: Free     C-05: Free
C-06: Active   C-07: Free      C-08: Active    C-09: Free     C-10: Free
```

### API response (what /slots sees):
```
C-01: Reserved  C-02: Reserved  C-03: Reserved  C-04: Reserved  C-05: Reserved
C-06: Active    C-07: Reserved  C-08: Active    C-09: Reserved  C-10: Reserved
```
→ 0 Free, 2 Active, 8 Reserved

### ACTUAL correct state at 11:30 MMT:
```
C-06: Active (Zay paing, 10:57-12:57) ✓
C-07: Active (Eaindray's fri, 10:41-11:41) — WRONGLY showing as Reserved!
C-08: Reserved (Heinlin, upcoming 12:00-15:00) — WRONGLY showing as Active!
C-01..C-05, C-09, C-10: Reserved (upcoming 12:00 bookings) ✓
```
→ Same 0/10 count, but C-07 and C-08 statuses are swapped

## Fixes Applied
See below.
