# Booking Fixes — Bots Round 3 (2026-06-17)

## Issues Fixed

### CI-4: Auto-Cancel Can Cancel In-Progress Sessions ✅
**File:** `/root/psvibe-sales-bot/scripts/auto_cancel_no_shows.py`
- Added re-fetch of booking status before canceling
- Skips bookings with status "active", "done", or "cancelled"
- Catches exceptions gracefully if status check fails

### HI-1: Handle Approval Conflict in Admin Bookings ✅
**File:** `/root/psvibe-sales-bot/bot/handlers/admin_bookings.py`
- After PATCH, checks for `conflict` field or 409 status code
- Shows staff a message that another staff already processed the booking

### HI-3: Staff Booking Shows All Slots Without Availability ✅
**File:** `/root/psvibe-sales-bot/bot/handlers/booking.py`
- `step_sbk_date`: Fetches existing bookings for selected date via API
- Marks unavailable hourly slots with 🔴, available with 🟢
- Shows count of available slots
- `step_sbk_time`: Strips icon prefix from selected slot text before validation

### HI-5: State Names Completely Wrong — RENAMED ✅
**Files:** `bot/__init__.py`, `bot/app.py`, `bot/handlers/booking.py`
- SBK_DATE (74, was phone step) → **SBK_PHONE** (74)
- SBK_TIME (75, was date step) → **SBK_DATE** (75)
- SBK_DUR (76, was time step) → **SBK_TIME** (76)
- SBK_GAME (77, was duration step) → **SBK_DURATION** (77)
- Handler functions renamed: step_sbk_time→step_sbk_date, step_sbk_dur→step_sbk_time, step_sbk_date→step_sbk_phone, step_sbk_game→step_sbk_duration
- All references updated in __init__.py (BotState, __all__, module-level), app.py (imports, state mappings), booking.py (imports, returns)

### MI-3: No Conversation Timeout in Customer Bot ✅
**File:** `/root/psvibe-sales-bot/customer_bot/main.py`
- Added `conversation_timeout=timedelta(minutes=30)` to booking ConversationHandler

### MI-4: Duration Validation in Staff Booking ✅
**File:** `/root/psvibe-sales-bot/bot/handlers/booking.py`
- In `step_sbk_duration`, validates duration is 1-1440 minutes

### MI-5: Phone Validation Too Weak ✅
**File:** `/root/psvibe-sales-bot/customer_bot/booking_handlers.py`
- Added Myanmar phone format validation in `bk_phone_entry`
- Supports both `09xxxxxxxxx` and `+959xxxxxxxx` formats
- Requires 9-11 digits after country code

### MI-6: Game Name Not Validated ✅
**File:** `/root/psvibe-sales-bot/customer_bot/booking_handlers.py`
- In `bk_game_select`, free text not matching any known game now shows error
- Asks user to select from the provided list instead of accepting arbitrary text

### MI-9: Reminder File Growth ✅
**File:** `/root/psvibe-sales-bot/scripts/auto_cancel_no_shows.py`
- Changed `booking_reminders.json` cleanup from "today only" to "7-day window"
- Uses cutoff_date computed as 7 days before now_MMT

### MI-10: State Stack Trims Wrong End ✅
**File:** `/root/psvibe-sales-bot/customer_bot/booking_handlers.py`
- Changed `stack.pop(0)` to `stack.pop()` in `_push_state`
- Now removes oldest (front) entries instead of newest (back) — corrected to remove from end

### LI-1: "scheduled" Status Doesn't Exist ✅
**File:** `/root/psvibe-sales-bot/scripts/auto_cancel_no_shows.py`
- Removed "scheduled" from status filters (both auto_cancel and send_reminders)
- Now only queries "confirmed" and "pending"

### LI-2: HTML Escaping on Customer Names ✅
**File:** `/root/psvibe-sales-bot/bot/handlers/admin_bookings.py`
- Added `import html`
- Uses `html.escape()` on customer names and phone before inserting into HTML parse_mode messages

### LI-3: 0 Balance Warning ✅
**File:** `/root/psvibe-sales-bot/customer_bot/booking_handlers.py`
- Added balance_warn variable when member balance is 0 or N/A
- Shows ⚠️ warning in both member found messages

### LI-4: BK_SPECIFIC_CONSOLE Unused ✅
**Files:** `customer_bot/handlers.py`, `customer_bot/booking_handlers.py`, `customer_bot/__init__.py`
- Removed BK_SPECIFIC_CONSOLE from all imports and state definitions
- Changed `range(17)` to `range(16)` in both definitions
- Added comment note about removal

## Verification
- All 9 affected files pass Python syntax check (`py_compile`)
- State numeric values verified: SBK_CONSOLE=72, SBK_CUST_NAME=73, SBK_PHONE=74, SBK_DATE=75, SBK_TIME=76, SBK_DURATION=77, SBK_CONFIRM=78
- All handler function names verified to match app.py state mappings
