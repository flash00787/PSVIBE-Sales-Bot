# PS VIBE Booking System — Feature Implementation Plan

> **Generated:** 2026-06-02 | **Analyst:** Subagent | **Method:** SSH into VPS + source reading

---

## Architect's Note: What This System Actually Does

PS VIBE has **TWO booking flows**, not one:

| Flow | Bot | States | Console Handling |
|------|-----|--------|------------------|
| **Customer Bot** | `psvibe_customer_bot` | 16-state `ConversationHandler` (BK_MEMBER_CHECK → ... → BK_CONFIRM) | User picks a **type** (PS5 / PS5 Pro / Any), NOT a specific unit |
| **Sale Bot (Staff)** | `psvibe-sale-bot` | 9-state `ConversationHandler` (SBK_CONSOLE → ... → SBK_CONFIRM) | Staff picks a **specific console unit** (C-01 through C-10) from a live-status keyboard |

**Critical insight:** The customer bot's console selection is a *type preference* (`bk_console` holds "PS5" or "PS5 Pro" or "Any"). The actual unit assignment happens when staff approves + later during session start. The `POST /api/bookings` from the customer bot always passes `console_id=""` (empty string) because no specific console has been chosen yet.

For Feature 1, we need to change this: let customers pick a specific console during booking, then pass it through to the API.

---

## 1. Current Flow Summary

### Customer Booking Flow (booking_handlers.py)

```
[Start] → BK_MEMBER_CHECK (Member card Yes/No)
           └→ Yes → BK_PHONE_VERIFY (last-3-digits match)
                    └→ Single match → BK_DATA_CONFIRM
                    └→ Multiple → BK_MEMBER_SELECT → BK_DATA_CONFIRM
                    └→ No match → BK_NAME (manual entry)
           └→ No → BK_NAME → BK_PHONE
                    └→ BK_DATE ← manual
                    └→ BK_DATE (from name/phone path or member path)
                          └→ BK_TIME (pick slot from available list)
                                └→ BK_CONSOLE (type: PS5 / PS5 Pro / Any)
                                      └→ BK_DURATION (mins)
                                            └→ BK_GAME (pick game)
                                                  └→ BK_CONFIRM
                                                        └→ BK_DUP_WARN (if duplicate)
                                                        └→ Submit via POST /api/bookings
```

### Sale Bot (Staff) Booking Flow (booking.py)

```
[Start] → cmd_staff_book_hub (Pending + Confirmed listings)
           └→ BTN_SBK_NEW → cmd_staff_booking
                               └→ SBK_CONSOLE (pick unit: C-01..C-10 with live icons)
                                     └→ SBK_CUST_NAME (member or type name)
                                           └→ SBK_DATE (pick date)
                                                 └→ SBK_TIME (pick time from hardcoded slots)
                                                       └→ SBK_DUR (duration in mins)
                                                             └→ SBK_GAME (pick game)
                                                                   └→ SBK_CONFIRM
                                                                         └→ Submit via POST /api/create_booking
```

### Key Functions

| Function | File | Line | Purpose |
|----------|------|------|---------|
| `_get_available_slots()` | `booking_handlers.py` | ~164 | Fetches bookings for a date, returns free time slots (9:00-21:00 minus booked) |
| `_submit_booking()` | `booking_handlers.py` | ~230 | Builds payload and POSTs to `/api/bookings` |
| `api_bookings_create()` | `app.py:968` | 968 | Handles customer POST — stores with `console_id=""` |
| `api_bookings_search()` | `patch_routes.py:520` | 520 | Search by date/status/chat_id |
| `_get_available_slots` → `_get_available_consoles` (NEW) | - | - | Will need to query `console_status` for free units |

---

## 2. MySQL Schema

### console_booking table
```sql
id             INT AUTO_INCREMENT PRIMARY KEY
console_id     VARCHAR(20)       -- "" for customer bot (will populate with Feature 1)
member_id      VARCHAR(50)
booking_date   DATE
start_time     DATETIME
end_time       DATETIME
status         VARCHAR(20)       -- pending, confirmed, Active, Done, cancelled, no_show
staff_name     VARCHAR(100)      -- For pending bookings: stores customerName
notes          TEXT
created_at     TIMESTAMP
telegram_chat_id VARCHAR(50)
duration_mins  INT
phone          VARCHAR(50)
game_name      VARCHAR(200)
```

### console_status table
```sql
console_id     VARCHAR(20) PRIMARY KEY  -- C - 01 .. C - 10
status         VARCHAR(50)              -- Free, Active, Reserved, Inactive
console_type   VARCHAR(50)              -- PS5, PS5 Pro
current_game   TEXT
current_member VARCHAR(100)
start_time     DATETIME
last_updated   DATETIME
```

---

## 3. Feature 1: Console Selection During Booking (တွဲချ)

### 3.1 What Changes

**Goal:** After customer picks time → show available physical consoles → customer picks one → submitted WITH that `console_id`.

### 3.2 Files to Change

#### A. `/root/psvibe-sales-bot/customer_bot/booking_handlers.py`

**Changes:**

1. **Add new constant** `BK_SPECIFIC_CONSOLE` (= 16, new state after BK_TIME, before BK_CONSOLE)

2. **Add keyboard builder**: `_make_specific_console_keyboard(free_consoles: list[dict])`
   - Fetches free consoles from API (`fetch_console_status`)
   - Filters to only those whose `status == "Free"` AND match the selected date/time (check `console_booking` for conflicts)
   - Shows each as `C - 01 (PS5) 🟢` etc.
   - Groups by type (PS5 first, PS5 Pro second)

3. **Add handler**: `bk_specific_console_select(update, context)`
   - Entry: Comes from BK_TIME (after time is selected)
   - Calls `_get_available_consoles(date, time, duration)` to find which units are free
   - Shows list via reply keyboard
   - On selection: stores `bk_specific_console_id` and `bk_console` (derived type)
   - Proceeds to BK_CONSOLE (for type display consistency) or directly to BK_DURATION

4. **Add helper**: `_get_available_consoles(date_str, time_str, duration_mins)`
   - Gets all console_status rows where status="Free"
   - For each free console, checks `console_booking` for conflicts at that [date, time, duration]
   - Returns list of available `{console_id, console_type}` dicts
   - If NONE available → warn customer (show all consoles with their statuses)

5. **Modify** `_submit_booking()`:
   - Add `bk_specific_console_id` to payload as `console_id` field
   - Final payload should include: `"console_id": context.user_data.get("bk_specific_console_id", "")`

6. **Modify** BK_DATE → BK_TIME flow:
   - After time selected, change transition from `return BK_CONSOLE` to `return BK_SPECIFIC_CONSOLE`

7. **Update** `_format_booking_summary()`:
   - Show `C - 01 (PS5)` instead of just "PS5" if specific console was picked

8. **Register the new state** in the ConversationHandler in `handlers.py` or `main.py`

**Estimated effort:** MEDIUM (~80-100 lines new code + 30 lines modifications)

---

#### B. `/root/psvibe-sales-bot/customer_bot/handlers.py`

**Changes:**

1. **Add** `BK_SPECIFIC_CONSOLE` to the state constants (range expanded from 16 to 17)

2. **Register** the new state handler in the conversation map (conversation_handler definition)

**Estimated effort:** SMALL (~5 lines)

---

#### C. `/root/psvibe_api_server/app.py`

**Changes to `api_bookings_create()` (line 968):**

1. **Accept `console_id` field** in the customer bot payload:
   ```python
   console_id = req.get("console_id", "")
   ```

2. **Use it in the INSERT** instead of empty string:
   ```python
   "INSERT INTO console_booking (console_id, member_id, booking_date, start_time, end_time, status, staff_name, notes, telegram_chat_id, duration_mins, phone, game_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
   (console_id, telegram_chat_id, booking_date_str, start_dt, end_dt, "pending", customer_name, notes, telegram_chat_id, duration_mins, phone, game_name)
   ```

**Estimated effort:** SMALL (~3 lines)

---

#### D. `/root/psvibe-sales-bot/bot/handlers/booking.py`

**Changes to `step_sbk_console()` and `step_sbk_confirm()`:**

1. **When staff approves a pending booking** that already has a `console_id`:
   - Display a note saying "Customer selected console: C-03"
   - Offer option to keep or change it
   - This is OPTIONAL — staff can always override

**Estimated effort:** SMALL (~15 lines)

---

#### E. Customer Bot — `customer_bot/api.py`

**Changes:**

1. **Add** `_fetch_console_status()` is already implemented — returns console list with `id`, `type`, `status`

2. **The `_get_available_consoles` helper** in `booking_handlers.py` will use this function

**Estimated effort:** NONE (already exists)

---

### 3.3 Flow After Feature 1

```
[Start] → BK_MEMBER_CHECK → ... → BK_DATE → BK_TIME
                                              ↓
                               BK_SPECIFIC_CONSOLE (NEW!)
                                  "Available consoles for {date} {time}:"
                                  [C-01 (PS5) 🟢] [C-03 (PS5) 🟢]
                                  [C-09 (PS5 Pro) 🟢]
                                  ↓ picks one
                               BK_CONSOLE (type selection, may auto-fill from unit)
                               → BK_DURATION → BK_GAME → BK_CONFIRM
                                                       ↓
                                        Submit with console_id="C-03"
```

---

## 4. Feature 2: Smart Time Slot Filtering (Past Slots Blocked)

### 4.1 What Changes

**Goal:** When customer picks today's date, only show time slots where `current_time + 30min_grace < slot_start_time`. For future dates, show ALL slots.

### 4.2 Files to Change

#### A. `/root/psvibe-sales-bot/customer_bot/booking_handlers.py`

**Changes to `_get_available_slots()` (line ~164):**

**Current code:**
```python
async def _get_available_slots(date_str: str) -> list[str]:
    """Get available time slots for a given date."""
    try:
        bks = await _api._api_get(f"bookings/search?date={date_str}")
    except Exception:
        bks = []
    bks = bks if isinstance(bks, list) else []
    if isinstance(bks, dict) and "bookings" in bks:
        bks = bks["bookings"]
    booked_slots = {b.get("timeSlot", "") for b in bks if b.get("status", "").lower() not in ("cancelled", "done")}
    all_slots = [f"{h:02d}:00" for h in range(OPEN_HOUR, CLOSE_HOUR)]
    return [s for s in all_slots if s not in booked_slots]
```

**New code (changes marked):**
```python
async def _get_available_slots(date_str: str) -> list[str]:
    """Get available time slots for a given date.
    
    - For future dates: return all unbooked slots (9:00-21:00).
    - For today: only return slots where start_time > current_time + 30min buffer.
    """
    try:
        bks = await _api._api_get(f"bookings/search?date={date_str}")
    except Exception:
        bks = []
    bks = bks if isinstance(bks, list) else []
    if isinstance(bks, dict) and "bookings" in bks:
        bks = bks["bookings"]
    booked_slots = {b.get("timeSlot", "") for b in bks if b.get("status", "").lower() not in ("cancelled", "done")}
    all_slots = [f"{h:02d}:00" for h in range(OPEN_HOUR, CLOSE_HOUR)]
    
    # NEW: Filter past slots for today
    available = [s for s in all_slots if s not in booked_slots]
    
    if date_str == today_mmt():
        now = now_mmt()
        # Add 30-minute buffer (grace period)
        grace_time = now + timedelta(minutes=30)
        grace_hour = grace_time.hour
        grace_min = grace_time.minute
        
        # Only keep slots whose hour is strictly > grace_hour
        # or equal hour but > grace minute (only for partial hours like 14:30 which isn't in all_slots but keep future-proof)
        available = [
            s for s in available
            if int(s.split(":")[0]) > grace_hour or (
                int(s.split(":")[0]) == grace_hour and grace_min == 0
            )
        ]
        
        # Edge case: if grace_hour >= CLOSE_HOUR, return empty
        if grace_hour >= CLOSE_HOUR:
            return []
    
    return available
```

**Also need to import:**
```python
from datetime import datetime, timedelta
from .data.prompts import today_mmt, OPEN_HOUR, CLOSE_HOUR, now_mmt
```

**Note:** `now_mmt` is already available in `prompts.py` (confirmed from reading the file).

**Estimated effort:** SMALL (~20 lines changed)

---

#### B. `/root/psvibe-sales-bot/customer_bot/handlers.py`

**Changes to `cmd_today()` (the "Today Overview" command):**

The `open_slots` generation at ~line already filters past slots:
```python
open_slots = [f"{h:02d}:00" for h in range(9, 21) if f"{h:02d}:00" > now_str]
```
This is already correct. No change needed.

**Estimated effort:** NONE

---

#### C. `/root/psvibe-sales-bot/bot/handlers/booking_flow.py`

The Sale Bot's `step_sbk_time()` uses **hardcoded** slots (10:00, 11:00, ..., 22:00). These are NOT filtered. However, staff bookings may intentionally want past slots (for creating back-dated entries). **Recommendation:** keep as-is for staff booking — staff are trusted operators.

**Estimated effort:** NONE

---

### 4.3 Edge Cases Covered

| Scenario | Behavior |
|----------|----------|
| Today, 9:00 AM | Shows 9:00-21:00 (now + 30min = 9:30 → 9:00 before grace → but 9:00 == 9:00 so kept if 0 grace_min; rounded) |
| Today, 2:30 PM | Shows 15:00-21:00 (grace = 15:00) |
| Today, 8:50 PM | Shows empty (grace = 21:20, no valid slots) |
| Tomorrow | Shows all 9:00-21:00 |
| Day after tomorrow | Shows all 9:00-21:00 |
| Any past date | Not possible in current UI (only Today/Tomorrow/Day After shown) |

---

## 5. Risk Assessment

### Feature 1 Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| **No available consoles** at the selected time → customer confused | MEDIUM | Add "All consoles busy at this time" message + offer alternative time or waitlist |
| **Race condition**: two customers see same console available and both book it | LOW | The booking creates a "pending" entry. Staff approval resolves conflicts. Also, checking `console_booking` for that slot before inserting provides first-line defense. |
| **Performance**: fetching consoles + checking conflicts adds 2 API calls per time selection | LOW | Cache can be added (30s TTL for console_status). API calls are fast (<200ms). |
| **Customer picks a console, then staff changes it during approval** | LOW | This is EXISTING behavior. Feature 1 just lets customer PREFER a console. Staff always has final say. |
| **State machine complexity**: adding state 16 means updating all back-button navigation | MEDIUM | Each handler's back-button logic peeks/pops state stack. Need to ensure `_pop_state` and `_push_state` are correctly handled for the new BK_SPECIFIC_CONSOLE state. |

### Feature 2 Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Time zone confusion**: server time vs MMT | LOW | Already using `now_mmt()` from `prompts.py` which adds `MMT_HOURS=6, MMT_MINUTES=30` offset |
| **Grace period rounding**: showing a slot that just passed | LOW (UX only) | 30 min buffer is generous. If someone picks 10:00 at 10:02, they get blocked — that's intentional. |
| **Staff booking inconsistency**: staff see different results than customer | MEDIUM (intentional) | Doc says: staff booking uses hardcoded slots intentionally. Staff may need to book for future dates. |
| **Performance** | NONE | Simple time comparison — no database impact |

---

## 6. Implementation Order

### Phase 1: Feature 2 (Foundation — easier, lower risk)

1. Modify `_get_available_slots()` in `booking_handlers.py` (~20 lines)
2. Test: Today at various times shows correct remaining slots
3. Test: Future dates show all slots

**Estimated time:** 30 minutes

### Phase 2: Feature 1 (Core — bigger change)

1. Add BK_SPECIFIC_CONSOLE state constant in `handlers.py`
2. Add keyboard builder `_make_specific_console_keyboard()` in `booking_handlers.py`
3. Add `_get_available_consoles()` helper in `booking_handlers.py`
4. Add `bk_specific_console_select()` handler in `booking_handlers.py`
5. Wire it into BK_TIME → BK_CONSOLE flow (change transition)
6. Update `_submit_booking()` to pass `console_id`
7. Update `api_bookings_create()` in `app.py` to accept `console_id`
8. Register handler in conversation map
9. Test the full flow

**Estimated time:** 2-3 hours

---

## 7. Files Modified Summary

| File | Feature 1 | Feature 2 | Effort |
|------|-----------|-----------|--------|
| `customer_bot/booking_handlers.py` | ~100 new lines + 30 mod | ~20 new lines | MEDIUM |
| `customer_bot/handlers.py` | ~5 lines | 0 | SMALL |
| `bot/handlers/booking.py` | ~15 lines | 0 | SMALL |
| `psvibe_api_server/app.py` | ~3 lines | 0 | SMALL |
| `psvibe_api_server/patch_routes.py` | 0 | 0 | NONE |
| MySQL schema | 0 | 0 | **NONE** (existing tables suffice) |

**Total estimated effort:** ~3-5 hours for implementation, ~2 hours for testing

---

## 8. File-by-File Changes (Detailed)

### 8.1 booking_handlers.py — Feature 1

**Constants to add** (near line 44):
```python
BK_SPECIFIC_CONSOLE = 16  # New state: pick specific console unit
```

**New keyboard builder** (near line 100):
```python
def _make_specific_console_keyboard(consoles: list[dict]) -> ReplyKeyboardMarkup:
    """Build console selection keyboard from available units.
    consoles: list of {"console_id": str, "console_type": str}
    """
    rows = []
    row = []
    # Group by type: PS5 first, PS5 Pro second
    ps5 = [c for c in consoles if c["console_type"] == "PS5"]
    ps5pro = [c for c in consoles if c["console_type"] == "PS5 Pro"]
    
    for c_list, icon in [(ps5, "🎮"), (ps5pro, "⭐")]:
        for c in c_list:
            label = f"{icon} {c['console_id']} ({c['console_type']})"
            row.append(label)
            if len(row) == 2:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
            row = []
    
    if not rows:
        rows.append(["⚠️ အားလုံးအလုပ်ရှုပ်နေပါသည်"])
    
    rows.append(["🤷 ကိစ္စမရှိပါ (Auto)"])
    rows.append([BTN_BACK, BTN_CANCEL])
    return _rp_kb(rows)
```

**New helper** (near line 180):
```python
async def _get_available_consoles(date_str: str, time_str: str, duration_mins: int = 60) -> list[dict]:
    """Get list of available specific console units for a given date+time.
    Returns: list of {"console_id": str, "console_type": str}
    """
    # Fetch all console statuses
    consoles = await _api._fetch_consoles()
    
    # Fetch bookings for that date to check conflicts
    try:
        bks = await _api._api_get(f"bookings/search?date={date_str}")
    except Exception:
        bks = []
    bks = bks if isinstance(bks, list) else []
    if isinstance(bks, dict) and "bookings" in bks:
        bks = bks["bookings"]
    
    # Parse the requested time as integer minutes from midnight
    h, m = map(int, time_str.split(":"))
    req_start = h * 60 + m
    req_end = req_start + duration_mins
    
    available = []
    for c in consoles:
        cid = c.get("id", "")
        ctype = c.get("type", "")
        status = c.get("status", "").lower()
        
        # Skip if not free (this is a basic check; a more thorough one checks bookings)
        if status != "free":
            continue
        
        # Check console_booking for time conflict
        conflicted = False
        for b in bks:
            if b.get("console_id", "").strip() != cid:
                continue
            bs = b.get("status", "").lower()
            if bs in ("cancelled", "done", "no_show"):
                continue
            # Extract timeSlot from booking
            b_start_str = b.get("timeSlot", "")
            if not b_start_str:
                continue
            try:
                bh, bm = map(int, b_start_str.split(":"))
                b_start = bh * 60 + bm
                b_dur = b.get("durationMins", 60)
                b_end = b_start + b_dur
                # Check overlap: [req_start, req_end) vs [b_start, b_end)
                if req_start < b_end and req_end > b_start:
                    conflicted = True
                    break
            except (ValueError, TypeError):
                continue
        
        if not conflicted:
            available.append({"console_id": cid, "console_type": ctype})
    
    return available
```

**New handler** (near line 900, after bk_time_select):
```python
async def bk_specific_console_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle specific console selection — new state between BK_TIME and BK_CONSOLE."""
    text = (update.message.text or "").strip() if update.message else ""
    
    if not update.callback_query and text:
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result
        
        if text == BTN_CANCEL:
            return await _cleanup_and_end(update, context)
        
        if text == BTN_BACK:
            _pop_state(context)
            date_str = context.user_data.get("bk_date", "")
            free_slots = await _get_available_slots(date_str) if date_str else []
            await update.message.reply_text(
                f"📅 *{date_str}* — အချိန်ရွေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_time_keyboard(free_slots) if free_slots else _make_date_keyboard(),
            )
            return BK_TIME
        
        # "ကိစ္စမရှိပါ (Auto)" → skip to BK_CONSOLE type selection
        if text == "🤷 ကိစ္စမရှိပါ (Auto)":
            context.user_data["bk_specific_console_id"] = ""
            _push_state(context, BK_SPECIFIC_CONSOLE)
            await update.message.reply_text(
                "🎮 Console အမျိုးအစား ရွေးပါ:",
                reply_markup=_make_console_keyboard(),
            )
            return BK_CONSOLE
        
        # Parse console label like "🎮 C - 01 (PS5)"
        import re
        m = re.match(r"[🎮⭐]\s*(C\s*-\s*\d+)\s*\(([^)]+)\)", text)
        if m:
            cid = m.group(1).strip()
            ctype = m.group(2).strip()
            context.user_data["bk_specific_console_id"] = cid
            context.user_data["bk_console"] = ctype  # auto-set type
            _push_state(context, BK_SPECIFIC_CONSOLE)
            await update.message.reply_text(
                f"🖥️ Console: *{cid} ({ctype})*\n\n⏱️ ကြာချိန် ရွေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_duration_keyboard(),
            )
            return BK_DURATION
        
        # Invalid selection — re-show
        date_str = context.user_data.get("bk_date", "")
        time_str = context.user_data.get("bk_time", "")
        dur = context.user_data.get("bk_duration_mins", 60)
        free_consoles = await _get_available_consoles(date_str, time_str, dur)
        await update.message.reply_text(
            "⚠️ ကျေးဇူးပြုပြီး console ရွေးချယ်ပါ:",
            reply_markup=_make_specific_console_keyboard(free_consoles),
        )
        return BK_SPECIFIC_CONSOLE
    
    return BK_SPECIFIC_CONSOLE
```

**Modify `_submit_booking()`** (near line 228):
```python
payload = {
    ...
    "console_id": context.user_data.get("bk_specific_console_id", ""),
    ...
}
```

**Modify transition in `bk_time_select()`** — change line where it returns `BK_CONSOLE` to return `BK_SPECIFIC_CONSOLE` instead, and show available consoles:
```python
# Instead of:
#     return BK_CONSOLE
# Do:
date_str = context.user_data.get("bk_date", "")
time_str = text
dur = context.user_data.get("bk_duration_mins", 60)
free_consoles = await _get_available_consoles(date_str, time_str, dur)

await update.message.reply_text(
    f"⏰ အချိန်: *{text}*\n\n"
    f"🖥️ *{date_str}* တွင် {time_str} အချိန်အတွက် ရနိုင်သော Console များ:\n"
    f"(ရနိုင်သော — *{len(free_consoles)}* ခု)",
    parse_mode="Markdown",
    reply_markup=_make_specific_console_keyboard(free_consoles),
)
return BK_SPECIFIC_CONSOLE
```

### 8.2 booking_handlers.py — Feature 2

**Add import** at top:
```python
from datetime import datetime, timedelta
```

**Modify `_get_available_slots()`** (line ~164):
```python
async def _get_available_slots(date_str: str) -> list[str]:
    """Get available time slots for a given date.
    
    - For future dates: return all unbooked slots (9:00-21:00).
    - For today: only return slots where start_time > current_time + 30min buffer.
    """
    try:
        bks = await _api._api_get(f"bookings/search?date={date_str}")
    except Exception:
        bks = []
    bks = bks if isinstance(bks, list) else []
    if isinstance(bks, dict) and "bookings" in bks:
        bks = bks["bookings"]
    booked_slots = {b.get("timeSlot", "") for b in bks if b.get("status", "").lower() not in ("cancelled", "done")}
    all_slots = [f"{h:02d}:00" for h in range(OPEN_HOUR, CLOSE_HOUR)]
    
    available = [s for s in all_slots if s not in booked_slots]
    
    # NEW: For today, filter out past time slots with 30-minute grace buffer
    if date_str == today_mmt():
        now = now_mmt()
        grace = now + timedelta(minutes=30)
        grace_hour = grace.hour
        grace_min = grace.minute
        
        available = [
            s for s in available
            if int(s.split(":")[0]) > grace_hour or (
                int(s.split(":")[0]) == grace_hour and grace_min == 0
            )
        ]
        
        # Edge: if grace_hour >= CLOSE_HOUR, no more slots today
        if grace_hour >= CLOSE_HOUR:
            return []
    
    return available
```

### 8.3 app.py — Feature 1 **only**

**In `api_bookings_create()` (line 968),** add `console_id` field:
```python
# Near line where other fields are extracted:
console_id = req.get("console_id", "")

# In the INSERT statement, change "" to console_id:
"INSERT INTO console_booking (console_id, member_id, booking_date, start_time, end_time, status, staff_name, notes, telegram_chat_id, duration_mins, phone, game_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
(console_id, telegram_chat_id, booking_date_str, start_dt, end_dt, "pending", customer_name, notes, telegram_chat_id, duration_mins, phone, game_name)
```

---

## 9. Testing Checklist

### Feature 2 Tests
- [ ] Today 9:00 AM → slots 9:00-21:00 shown (all available)
- [ ] Today 2:30 PM → only slots 15:00-21:00 shown
- [ ] Today 8:50 PM → no slots shown ("အားလုံးပိတ်ပါပြီ")
- [ ] Tomorrow → all slots 9:00-21:00
- [ ] Day after → all slots 9:00-21:00
- [ ] A booked slot at a future time is still hidden (existing behavior preserved)
- [ ] Custom time entry also respects the filter

### Feature 1 Tests
- [ ] After time selection → shows available console list
- [ ] Each console shows type and free/available status
- [ ] Picking a console → auto-fills console type, proceeds to duration
- [ ] "ကိစ္စမရှိပါ (Auto)" → skips to type selection (existing behavior)
- [ ] Back button works (goes back to time selection)
- [ ] No available consoles → friendly message + suggestion to change time
- [ ] Submitted booking includes `console_id` in database
- [ ] Staff approval flow shows customer's console selection
- [ ] Race condition: two customers pick same console at same time → both get "pending" → staff resolves

---

## 10. Implementation Notes

1. **Back-button stack is fragile.** The `_bk_state_stack` in `booking_handlers.py` tracks navigation history. Adding BK_SPECIFIC_CONSOLE means every handler's `BTN_BACK` logic that previously targeted BK_TIME needs verification. The `_pop_state()` approach in the code is already sound — just ensure it's called correctly.

2. **No MySQL schema changes needed.** Both `console_booking.console_id` (VARCHAR(20)) and `console_booking` already exist. The console_id field is already in the table schema. Customer bot just currently passes empty string.

3. **The `now_mmt()` function** is already imported in `booking_handlers.py` via `from .data.prompts import today_mmt, OPEN_HOUR, CLOSE_HOUR`. We just need to add `now_mmt` to that import.

4. **Cache consideration:** `_fetch_consoles()` has a 300s cache. For real-time console selection, we may want to invalidate or use a shorter TTL. However, since the booking creates a "pending" status (not immediate), 300s cache is acceptable.

---

*End of Implementation Plan*
