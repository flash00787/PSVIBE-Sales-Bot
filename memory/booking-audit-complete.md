# 🔍 PS VIBE Booking Flow — Complete Audit

> **Audited:** 2026-06-17 | **Auditor:** Kora (main agent, deep-review)
> **Files Audited:** 6 files, ~4,000 lines of code

---

## 📋 System Overview

PS VIBE has **THREE booking paths**:

| # | Path | Bot | Initiated By | Status on Create |
|---|------|-----|-------------|-----------------|
| 1 | Customer Booking | `psvibe_customer_bot` | Customer via Tele | `pending` (needs staff approve) |
| 2 | Staff Advance Booking | `psvibe-sale-bot` | Staff via Booking Hub | `confirmed` (auto) |
| 3 | Walk-in Session | `psvibe-sale-bot` | Staff via Console Menu | `Active` immediately |

---

## 🔄 Flow 1: Customer Bot Booking (16 states)

### States & Handlers

| State | Value | Handler | Keyboard |
|-------|-------|---------|----------|
| BK_MEMBER_CHECK | 0 | `bk_member_check_entry` | Yes/No |
| BK_MEMBER_SELECT | 1 | `bk_member_select` | Member list / text |
| BK_PHONE_VERIFY | 2 | `bk_phone_verify` | Text (last 3 digits) |
| BK_DATA_CONFIRM | 3 | `bk_data_confirm` | ✅ / ❌ |
| BK_NAME | 4 | `bk_name_entry` | Text |
| BK_PHONE | 5 | `bk_phone_entry` | Text |
| BK_DATE | 6 | `bk_date_select` | Today/Tomorrow/Day After |
| BK_TIME | 7 | `bk_time_select` | Slots + Custom Time |
| BK_CONSOLE | 8 | `bk_console_select` | PS5 / PS5 Pro / Any |
| BK_CONSOLE_PREF | 9 | `bk_console_pref` | Specific C-0X + Auto Assign |
| BK_DURATION | 10 | `bk_duration_select` | 30/60/90/120/180 |
| BK_GAME | 11 | `bk_game_select` | Game list (paginated) |
| BK_CONFIRM | 12 | `bk_confirm` | Confirm / Back |
| BK_DUP_WARN | 13 | `bk_dup_warn` | Continue / Go Back |
| BK_DISC_WARN | 14 | `bk_disc_warn` | Continue / Go Back |
| BK_CON_CONFLICT | 15 | `bk_con_conflict` | Continue/Change Time/Console |
| BK_END | -1 | `bk_end_handler` | Fallback (no keyboard) |

### Entry Points
- `/book`, `/booking` commands
- `📅 Booking` button text

### API Call: `POST /api/bookings`
```json
{
  "customerName": "...",
  "phone": "...",
  "date": "YYYY-MM-DD",
  "timeSlot": "HH:MM",
  "consoleType": "PS5/PS5 Pro/Any",
  "console_id": "C-01" or "",
  "durationMins": 60,
  "gameName": "...",
  "telegramChatId": "...",
  "username": "...",
  "status": "pending"
}
```

### ✅ Strengths
- Phone last-3-digit member matching with balance display
- `_get_available_slots()` uses time-range overlap detection (not just hourly)
- Past slots filtered for today with 30-min grace
- `_get_available_consoles()` two-level filter: real-time status + booking conflicts
- Auto-assign picks first free console matching type
- Duplicate booking warning before submit
- `_bk_state_stack` for proper back-button navigation
- Catch-all handler prevents text leaking to Gemini AI

### ⚠️ Issues Found

#### 🟡 MEDIUM: BK_SPECIFIC_CONSOLE state defined but NOT registered
- **File:** `customer_bot/handlers.py:30` — `BK_SPECIFIC_CONSOLE` constant defined
- **File:** `customer_bot/main.py` — NOT in ConversationHandler states
- **Impact:** State constant dead code; no functional issue since flow uses BK_CONSOLE_PREF instead
- **Recommendation:** Remove dead constant or implement if needed

#### 🟡 MEDIUM: Duplicate check API call is text-search, not time-range
- **File:** `booking_handlers.py` — `bk_confirm()` lines ~1770-1820
- **Issue:** Uses `search-bookings?telegram_chat_id={uid}&date={date_str}` which returns ALL bookings for the user on that date, then does overlap detection IN the bot
- **API level** also has slot conflict check but only if `console_id` is set (line ~1830 in app.py)
- **Gap:** If user books without specific console (auto-assign), API slot check is bypassed
- **Risk:** LOW — auto-assign + `_get_available_consoles` already handles this

#### 🟢 LOW: `_submit_booking` console_id resolution logic
- **Lines:** ~355-380
- Auto-assign is called within `_submit_booking()` which is also called by `bk_confirm` → both also check dupes
- Redundant API calls for available consoles (called in `bk_console_select` then AGAIN in `_submit_booking`)
- Minor performance hit but ensures freshness

---

## 🔄 Flow 2: Sale Bot Staff Advance Booking (7 states)

### State → Actual Purpose Mapping

| State Name | Actual Purpose | State After |
|------------|---------------|-------------|
| `SBK_TIME` → `step_sbk_time` | **Select DATE** | → SBK_DUR |
| `SBK_DUR` → `step_sbk_dur` | **Select TIME** | → SBK_CONSOLE |
| `SBK_CONSOLE` → `step_sbk_console` | **Select CONSOLE** | → SBK_CUST_NAME |
| `SBK_CUST_NAME` → `step_sbk_cust_name` | **Select CUSTOMER** | → SBK_DATE |
| `SBK_DATE` → `step_sbk_date` | **Enter PHONE** | → SBK_GAME |
| `SBK_GAME` → `step_sbk_game` | **Select DURATION** | → SBK_CONFIRM |
| `SBK_CONFIRM` → `step_sbk_confirm` | **Select GAME + CONFIRM** | → SUBMIT |

### ⚠️ Issues Found

#### 🔴 HIGH: State names completely wrong — maintenance hazard
- **Files:** `bot/handlers/booking.py` + `bot/app.py`
- **Problem:** Every state name is wrong vs what it actually does:
  - `SBK_TIME` asks for DATE (not time)
  - `SBK_DUR` asks for TIME (not duration)
  - `SBK_GAME` asks for DURATION (not game)
  - `SBK_DATE` asks for PHONE (not date)
- **Risk:** Any developer working on this will be confused. Back-button logic depends on these names being mapped correctly in memory.
- **Impact:** Currently works because ConversationHandler maps handler→state correctly. But future modifications high risk.

#### 🟡 MEDIUM: Order is unconventional (Console → Customer → Duration → Game)
- Normal booking flow would be: Customer → Date → Time → Duration → Console → Game
- Current order: Date → Time → Console → Customer → Phone → Duration → Game
- Console is selected before knowing who the customer is
- **Impact:** Staff can't filter available consoles by customer game preference first

#### 🟡 MEDIUM: Time slots are hardcoded (10:00–22:00) — no API check
- **File:** `booking.py` — `step_sbk_time()`
- Unlike customer bot which uses `_get_available_slots()`, staff booking shows ALL hardcoded slots
- No conflict detection at staff booking time — only at API create
- **Gap:** Staff could try to book a slot that's already taken, gets error at confirm

#### 🟢 LOW: Back button in `step_sbk_cust_name` goes to date (should go to console)
- Line ~270: `BTN_BACK` calls `cmd_staff_booking(update, context)` which restarts the entire flow
- Instead of going back one step (to SBK_DUR = time selection), it restarts everything

### API Call: `POST /api/bookings`
```json
{
  "customerName": "...",
  "phone": "...",
  "date": "M/D/YYYY",
  "timeSlot": "HH:MM",
  "consoleType": "PS5",
  "console_id": "C-01",
  "durationMins": 60,
  "gameName": "...",
  "status": "confirmed",
  "source": "staff",
  "staffNote": "...",
  "telegramChatId": "..."
}
```

### ✅ Strengths
- n8n reminder webhook integration after booking
- 10-min advance reminder to admin group
- SSD transfer warning when game not on console
- Disc session conflict check
- tg_chat_id auto-resolve from phone number

---

## 🔄 Flow 3: Walk-in Session (BOOK_* states)

### States
- `BOOK_CONSOLE` → `BOOK_MEMBER` → `BOOK_GAME` → `BOOK_MINS` → Create
- Optional: `BOOK_LINK` (link to confirmed booking) → `BOOK_DUP_WARN`

### API Call: `POST /api/consoles/start-session`
```json
{
  "console_id": "C-01",
  "member_id": "PSV_A",
  "game_name": "FIFA",
  "duration_mins": 60
}
```
This auto-creates a booking with status="Active" directly.

### ✅ Strengths
- Confirmed booking linking: autofills member/console/game
- Duplicate session detection (member already active on another console)
- 5-min reminder timer with extend/done buttons
- SSD transfer integration

---

## 🔌 API Server Endpoints

### `POST /api/bookings` (Customer Bot + Staff Booking)
- **Line:** ~1744
- Supports TWO formats: customer bot (has `customerName`) vs staff (legacy)
- Multi-format date parsing (5 formats)
- Slot conflict check ONLY when `console_id` is provided
- Auto-confirm for `source == "staff"`
- Member_id auto-resolve from phone
- Admin notification via Telegram (fire-and-forget thread)

### `POST /api/create_booking` (Legacy, still active)
- **Line:** ~1276
- Creates booking with status="Active" immediately
- Used by walk-in sessions
- Also marks console_status as Active
- ⚠️ **NOTE:** Both `/api/bookings` (staff format) and `/api/create_booking` exist with similar functionality

### `POST /api/bookings/checkin`
- **Line:** ~1180
- Changes booking status to "Active"
- Updates console_status to Active with member + game
- Optional console override at checkin time
- Guard against same console having another Active booking
- Schedules session timer
- Sends Telegram notification to admin group

### `POST /api/bookings/cancel`
- **Line:** ~1675
- Sets booking to "cancelled"
- Frees console (console_status → "Free")
- Notifies customer via Telegram (Customer Bot)

### `PATCH /api/bookings/{id}/status` (Approve/Reject)
- **Line:** ~1336
- Sets status + optional console assignment
- Used by admin_bookings.py approve/reject buttons

### `GET /api/bookings` (List)
- **Line:** ~1412
- Query params: `status`, `date`, `telegram_chat_id`

### `GET /api/bookings/{id}` (Get single)
- **Line:** ~1355
- Returns full booking details

### `GET /api/search-bookings` (Search by chat_id)
- **Line:** ~1492
- Used by customer bot for duplicate detection

### `GET /api/get-confirmed-booking`
- **Line:** ~1656
- Get confirmed bookings for a specific console

### `PUT /api/end_booking/{id}`
- **Line:** ~1564
- End booking, mark as Done

### `POST /api/bookings/extend-duration`
- **Line:** ~493
- Extend active booking duration

### ✅ Strengths
- Comprehensive endpoint coverage
- Multi-format date parsing
- Conflict detection
- Auto member_id resolution

### ⚠️ Issues Found

#### 🟡 MEDIUM: Two overlapping booking creation endpoints
- `/api/bookings` (POST) — primary for customer+staff
- `/api/create_booking` (POST) — creates "Active" booking directly
- Both do similar things with different payload formats
- **Risk:** Confusion about which to use; `/api/create_booking` bypasses all validation

#### 🟡 MEDIUM: Slot conflict check only runs when console_id present
- **Line:** ~1826 in `api_bookings_create()`
- `if console_id:` guard means bookings without specific console bypass conflict detection
- Customer bot auto-assign happens in bot, not API — so API sees `console_id=""` initially
- **Mitigation:** Bot's `_submit_booking` now auto-assigns before calling API

---

## 📋 Admin Booking Management

### Pending Bookings List
- Shows 20 most recent pending bookings
- Each card has ✅ Approve / ❌ Reject buttons
- On approve: auto-assigns matching console type (prefers console with game installed)
- Game install warning if assigned console doesn't have the game

### Confirmed Bookings List
- Shows upcoming confirmed bookings (sorted by date)
- Each card has ✅ Check In / 🚫 Cancel buttons
- Today's bookings marked with 🔵 Today tag

### Check-In Flow
1. Staff clicks ✅ Check In
2. Console selection: shows free consoles + current booking console + skip option
3. API check-in: marks booking Active + console Active
4. Sends welcome notification to customer

### Approve Flow
1. Staff clicks ✅ Approve on pending booking
2. Auto-assigns matching console type (with game install preference)
3. PATCH /api/bookings/{id}/status → status="confirmed"
4. Notifies customer via Customer Bot
5. Fires n8n reminder webhook

### Reject Flow
1. Staff clicks ❌ Reject
2. PATCH /api/bookings/{id}/status → status="rejected"
3. Notifies customer

### ✅ Strengths
- Complete approve/reject/checkin/cancel lifecycle
- Console auto-assignment
- Customer notifications
- n8n reminder integration

---

## ⏰ Auto Cancel No-Shows (`auto_cancel_no_shows.py`)

### How it works
1. Fetches bookings with status: confirmed, pending, scheduled
2. Checks if `now_mmt > booking_time + 15 min grace`
3. If passed → cancels via `POST /api/bookings/cancel`
4. Notifies customer + staff via Telegram

### ✅ Strengths
- Multi-status coverage (confirmed, pending, scheduled)
- De-duplication by ID
- Both customer and staff notifications
- Proper MMT timezone handling
- Grace period (15 min)

### ⚠️ Issues Found

#### 🟢 LOW: `scheduled` status may not exist
- Script queries for "scheduled" but MySQL booking statuses are: pending, confirmed, Active, Done, cancelled, no_show
- "scheduled" is not a valid booking status → wasted API call
- **Impact:** None (gracefully handled, just an extra API call)

---

## 📊 Summary: All Issues

| # | Severity | Location | Issue |
|---|----------|----------|-------|
| 1 | 🔴 HIGH | `booking.py` | State names completely wrong (SBK_TIME=DATE, SBK_DUR=TIME, SBK_GAME=DURATION) |
| 2 | 🟡 MEDIUM | `handlers.py` + `main.py` | BK_SPECIFIC_CONSOLE defined but not registered |
| 3 | 🟡 MEDIUM | `booking.py` | Staff time slots hardcoded, no API conflict check |
| 4 | 🟡 MEDIUM | `app.py` | Slot conflict check skipped when console_id="" |
| 5 | 🟡 MEDIUM | `app.py` | Two overlapping booking creation endpoints |
| 6 | 🟡 MEDIUM | `booking.py` | Back button in customer name step restarts entire flow |
| 7 | 🟢 LOW | `booking.py` | Unconventional flow order (console before customer) |
| 8 | 🟢 LOW | `auto_cancel_no_shows.py` | Queries non-existent "scheduled" status |
| 9 | 🟢 LOW | `booking_handlers.py` | Redundant console availability check in _submit_booking |

---

## 🎯 Overall Verdict

### ✅ What's Working Well
- All three booking paths functional end-to-end
- Phone-based member matching works
- Auto-assign console logic is solid
- Conflict detection at multiple levels
- Complete admin lifecycle (approve → checkin → end)
- Customer notifications on all state changes
- Auto-cancel no-shows with 15-min grace
- Reminder system (Telegram + n8n)

### ⚠️ Main Risks
1. **Maintenance hazard:** State name confusion in staff booking flow (#1)
2. **Slot double-booking:** When console_id not assigned at API level (#4)
3. **Endpoint confusion:** Two create-booking endpoints with different semantics (#5)

### 🔧 Recommended Fixes (Priority Order)
1. Rename SBK_* state constants + handler functions to match actual purpose
2. Add slot conflict check in API even when console_id not yet assigned (check by type)
3. Consolidate `/api/bookings` and `/api/create_booking` — deprecate the legacy one
4. Remove dead BK_SPECIFIC_CONSOLE code or implement it properly
5. Fix back-button in staff booking customer name step
