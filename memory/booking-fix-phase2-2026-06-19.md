# Booking Flow Fixes — Phase 2 — 2026-06-19

## Fixes Applied to `/root/psvibe-sales-bot/customer_bot/booking_handlers.py`

### BUG 1: Race condition — Specific console not validated before submission

**Problem:** `_submit_booking()` only ran auto-assign when `console_id` was empty. When a
customer explicitly picked a console (e.g. "C-09"), that console_id was submitted
directly without a final availability check. Race condition: another customer could
book the same console between selection and submission.

**Fix:** Always run `_get_available_consoles()` when `date_str` and `time_str` are set:
- If `console_id` is already set → check it's in the available_ids set; if not,
  return error: `❌ Console {id} သည် ထိုအချိန်တွင် မရနိုင်တော့ပါ။ ပြန်ရွေးပါ။`
- If `console_id` is empty → auto-assign first available (existing behavior preserved)

### BUG 2: Silent fallthrough when all consoles are busy

**Problem:** When `_get_available_consoles()` returned empty after type filtering, the
code silently fell through to duration selection without telling the customer why.

**Fix:** Created `_get_next_available_times(consoles_raw, bookings, target_start_minutes, target_end_minutes)`:
- Builds per-console booking intervals (skipping cancelled/done/rejected)
- For each console, finds earliest free slot of `gap_mins` duration starting from target_start
- Returns sorted list of `{console_id, console_type, free_from, free_from_str}`

**Modified 3 call sites:**
1. `bk_console_select()` — CONSOLE_TYPES branch: shows next available times when filtered list is empty
2. `bk_console_select()` — BTN_NOT_SURE ("Any") branch: same
3. `bk_console_pref()` — shows next available times when filtered list is empty

Each shows a message like:
```
🎮 PS5 Pro စက်များ 13:00 တွင် မအားသေးပါ။
C-09 → 16:00 နောက်ပိုင်း ရနိုင်ပါမည်
C-10 → 14:00 နောက်ပိုင်း ရနိုင်ပါမည်
⏰ အခြားအချိန်ရွေးရန် Back နှိပ်ပါ
```
With Back + Cancel buttons to return to time selection.

### Verification
- Syntax check: ✅ passed
- Service restart: ✅ active (running) — PID 795776
- Backup: `booking_handlers.py.bak-20260619_*`
