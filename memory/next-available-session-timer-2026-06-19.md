# Next Available Times — Live Session Enhancement
**Date:** 2026-06-19  
**File:** `/root/psvibe-sales-bot/customer_bot/booking_handlers.py`

## Changes Made

### 1. Function Signature Updated
Added optional `target_date=""` parameter to `_get_next_available_times()`:
```python
def _get_next_available_times(consoles_raw, bookings, target_start_minutes, target_end_minutes, target_date=""):
```

### 2. Live Session Detection (TODAY only)
After building booking intervals, the function checks if `target_date` equals today (MMT, UTC+6:30). If so:
- Iterates consoles with `status` = "Active" or "Reserved"
- Parses `start_time` (handles both "YYYY-MM-DDTHH:MM:SS" and "YYYY-MM-DD HH:MM:SS" formats)
- Converts to Myanmar time and calculates `session_start` in minutes since midnight
- Looks for matching booking in `console_bookings[console_id]` with overlapping time
- If found: uses booking's `duration_mins` to calculate `expected_end`
- If NOT found (walk-in): uses default 60-minute duration
- Skips sessions whose `expected_end` ≤ `now_minutes` (already over)
- Adds non-duplicate `(session_start, expected_end)` interval to `console_bookings`

### 3. All 3 Call Sites Updated
Passing `date_str` as `target_date`:
- `bk_console_select` (specific type): line ~1489
- `bk_console_select` ("Any"): line ~1540
- `bk_console_pref`: line ~1951

### 4. Overlap Resolution
The existing overlap-resolution loops (two-pass scan pushing `free_from` past conflicting bookings) naturally handle the added live-session intervals, since they're merged into the same `console_bookings` dict and sorted.

## Verification
- ✅ Syntax check: `python3 -m py_compile` — passed
- ✅ Service restart: `systemctl restart psvibe_customer_bot.service` — active
- ✅ Logs show clean startup: "Application started" with no errors
- ✅ Backup created: `booking_handlers.py.bak-session-20260619_*`

## Notes
- The live session check is skipped entirely for future dates (only TODAY)
- Duplicate intervals (when booking already covered the session) are detected and skipped
- Logging added at INFO level for detected live sessions, WARNING for parse errors
