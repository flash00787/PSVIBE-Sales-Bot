---

## 2026-06-25 (17:00 MMT) — Booking #974 Disappearance Investigation + Fixes

### Issues Found & Fixed

| # | Bug | File | Root Cause | Fix |
|---|-----|------|-----------|-----|
| 1 | Staff Booking checkin_bind calls dead API | `bot/handlers/booking.py:1213` | `POST /api/update_booking` doesn't exist → HTTP 405 | Changed to `PATCH bookings/{bk_id}/status` |
| 2 | _sync_console_status uses UTC NOW() against MMT times | `app.py:96-158` | MySQL `NOW()` returns UTC, `start_time` stored as MMT → 6.5hr mismatch | Use Python `now_mmt()` string via parameterized query |
| 3 | Booking→Active uses `start_time=NOW()` (UTC) | `app.py:1623` | Same UTC/MMT mismatch | Use `now_mmt().strftime()` |
| 4 | Booking tab broken: stray `,if(` after removing v()){ | `dashboard-dist/.../BookingsManagement-BbqxMmPA.js` | Removing `v()){` left `if` keyword in comma expression | `,if(o.value.booking_date...` → `,o.value.booking_date...` |
| 5 | Edit modal time/duration fields hidden for non-cancelled | `dashboard-dist/.../BookingsManagement-BbqxMmPA.js` | Template `v()?render():y("",!0)` hides fields unless booking is cancelled | Removed `v()?` and `:y("",!0)` wrapper — fields always render |

### Services Restarted
- `psvibe-api` → PID 2294664
- `psvibe-sale-bot` → PID 2294683
