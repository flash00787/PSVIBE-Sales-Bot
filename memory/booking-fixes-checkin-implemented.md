# Booking Fixes & Check-In Implementation

## Date: 2026-06-02
## Implemented by: Subagent

## 1. Bug Fix: Console Selection Stuck

**Root Cause:** BK_SPECIFIC_CONSOLE state (16) was not registered in the `customer_bot/main.py` ConversationHandler states dict, but `bk_time_select` returns this state when available consoles exist. The bot gets stuck because no handler is defined for the state.

### Changes Made:

**a) `customer_bot/booking_handlers.py`:**
- Changed `_make_specific_console_keyboard` from InlineKeyboardMarkup to ReplyKeyboardMarkup with `_rp_kb()` helper
- Removed unused `date_str` and `time_str` parameters from the function signature
- Changed `bk_specific_console_select` to handle TEXT input from ReplyKeyboard instead of callback_query:
  - BTN_CANCEL → cleanup and end
  - BTN_BACK → return to time selection
  - BTN_NOT_SURE → go to console type selection
  - Parses "C-01 (PS5)" format to extract console ID and type
  - Falls back to direct console ID matching

**b) `customer_bot/main.py`:**
- Added BK_SPECIFIC_CONSOLE state to ConversationHandler states dict with:
  ```python
  BK_SPECIFIC_CONSOLE: [
      MessageHandler(filters.TEXT & ~filters.COMMAND, bk_specific_console_select),
  ],
  ```

## 2. Feature: Staff Check-In

**Goal:** Staff can mark a confirmed booking as "Checked In" when customer arrives.

### Changes Made:

**a) `bot/handlers/admin_bookings.py`:**
- Added `cb_checkin_booking` callback handler for `bkm:checkin:<id>` pattern
- Added `_send_checkin_notification` helper to notify customer via customer bot
- Check-In flow:
  1. Staff clicks "✅ Check In" button on confirmed booking card
  2. Calls `POST /api/bookings/checkin` API
  3. Updates booking status to "Active" and sets console to Active
  4. Sends success message to staff
  5. Notifies customer: "Welcome to PS VIBE! Your session has started. Enjoy! 🎮"

**b) `bot/handlers/booking.py`:**
- Added "✅ Check In" button to `cmd_confirmed_bookings` alongside existing Cancel button

**c) `bot/app.py`:**
- Registered `cb_checkin_booking` as separate CallbackQueryHandler with pattern `^bkm:checkin:\d+$`

## 3. Feature: Auto-Cancel No-Show

**Goal:** Auto-cancel bookings if customer doesn't check in within 15 minutes of booking time.

### Changes Made:

**a) Created `/root/psvibe-sales-bot/scripts/auto_cancel_no_shows.py`:**
- Runs as cron job every 5 minutes
- Fetches today's confirmed bookings via API
- Checks if current MMT time > booking time + 15 minutes
- Cancels via `POST /api/bookings/cancel` API endpoint
- Does NOT store bot tokens - notifications handled by Sale Bot

**b) Added endpoint in `app.py`:**
- `POST /api/bookings/checkin` - Check in a customer (booking → Active, console → Active)
- `POST /api/bookings/cancel` - Cancel a booking by ID (booking → cancelled, console → Free)

**c) Cron job added (every 5 minutes):**
```
*/5 * * * * cd /root/psvibe-sales-bot && /usr/bin/python3 /root/psvibe-sales-bot/scripts/auto_cancel_no_shows.py >> /var/log/auto_cancel.log 2>&1
```

## Files Modified
- `/root/psvibe-sales-bot/customer_bot/booking_handlers.py`
- `/root/psvibe-sales-bot/customer_bot/main.py`
- `/root/psvibe-sales-bot/bot/handlers/admin_bookings.py`
- `/root/psvibe-sales-bot/bot/handlers/booking.py`
- `/root/psvibe-sales-bot/bot/app.py`
- `/root/psvibe_api_server/app.py`

## Files Created
- `/root/psvibe-sales-bot/scripts/auto_cancel_no_shows.py`

## Services Restarted
- psvibe-sale-bot.service ✅
- psvibe_customer_bot.service ✅
- psvibe-api.service ✅
