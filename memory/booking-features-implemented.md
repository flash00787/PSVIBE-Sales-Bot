# Booking Features — Implementation Summary

> **Date:** 2026-06-02 | **Commits:** d53acb4 + 4582b6c

## Feature 1: Console Selection During Booking (တွဲချ) ✅
**Commit:** `d53acb4` on Sales Bot + API Server

### Changes:
| File | Change | Purpose |
|------|--------|---------|
| `customer_bot/booking_handlers.py` | +3 functions (~130 lines) | `_make_specific_console_keyboard()`, `_get_available_consoles()`, `bk_specific_console_select()` |
| | Modified `_submit_booking()` | Now sends `console_id` field |
| | Modified `bk_time_select()` | Shows available consoles after time selection |
| `customer_bot/handlers.py` | +1 constant | `BK_SPECIFIC_CONSOLE = 16` |
| `bot/handlers/booking.py` | +2 lines | Shows console ID in pending/confirmed bookings |
| `app.py` (API) | +1 line accept, 1 line use | Accepts `console_id` from customer, uses it in INSERT |

### New Flow:
1. Customer picks date → time
2. System checks available consoles (Free + no time conflict)
3. Shows inline keyboard: `C-01 (PS5)`, `C-03 (PS5)`, `C-09 (PS5 Pro)`
4. Customer picks specific console → continues to duration/game
5. Booking submitted WITH `console_id`

### Fallback:
- If no specific consoles available → falls back to type selection (PS5 / PS5 Pro / Any)
- Customer can always choose "Not sure" → type selection

## Feature 2: Time-Slot Restriction ✅
**Commit:** `4582b6c` on Sales Bot only

### Changes:
| File | Change | Purpose |
|------|--------|---------|
| `customer_bot/booking_handlers.py` | `_get_available_slots()` ~18 lines | Filters past slots for today (MMT) |

### Logic:
- Future dates: show ALL slots (9:00-21:00)
- Today: only show slots where `slot_start >= now_mmt + 30min`
- Time zone: UTC+6:30 (Myanmar Time)
- Grace buffer: 30 minutes
- If current time >= 21:00 → return empty list

### Example:
- It's 2:30 PM → available: 3 PM, 4 PM, 5 PM, 6 PM, 7 PM, 8 PM, 9 PM
- It's 8:50 PM → available: 9 PM (only if 9PM >= 8:50PM+30min=9:20PM... actually no, 9PM < 9:20PM → empty)

## Verification
- All 3 services restarted and `active`
- Git repos committed (Sales Bot: 2 new commits, API Server: 1 new commit)
- No database schema changes needed
