# Overlap Fix — Root Cause & Prevention
**Date:** 2026-06-19 | **By:** Kora (Boss request)

## Root Cause
- Booking approval endpoint (`PATCH /api/bookings/{id}/status`) had **NO overlap check**
- Customer flow (`booking.py`) checked conflicts, but staff approval bypassed it
- Multiple staff could approve pending bookings for same console/time simultaneously

## What Was Fixed
- Found 8 overlaps across June 20-21 (C-01, C-09)
- Cancelled 2 duplicates (#578, #600)
- Moved 3 bookings to free consoles (#606→C-02, #607→C-02, #577→C-05)
- Final: 19 confirmed bookings, 0 overlaps ✅

## Prevention (permanent fix)
- **File:** `/root/psvibe_api_server/app.py` — `api_update_booking_status()`
- **Added:** Overlap check at lines 1403-1426
- When status="confirmed", queries existing bookings on same console at same time
- If conflict found → 409 error + conflict_id returned, approval blocked
- No DB schema changes needed

## How It Works
```
Staff clicks "Approve" →
  API checks: "Console X already booked at Y time?" →
    YES → ❌ Blocked: "Console C-01 already has confirmed booking (BK#608)"
    NO  → ✅ Approved
```
