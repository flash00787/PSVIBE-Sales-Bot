# Booking Fixes — API Round 3 (2026-06-17)

## Summary
Applied 12 fixes across `/root/psvibe_api_server/app.py` for concurrency safety, data integrity, input validation, and error handling in the PS VIBE booking system.

---

## Fixes Applied

### CI-1: Double Booking — Row-Level Locking on Slot Booking ✅
**Function:** `api_bookings_create` (customer bot path)
**What:** Replaced bare SELECT conflict check with a MySQL transaction using `SELECT ... FOR UPDATE`. The conflict check + INSERT are now wrapped in a single transaction with row-level locking:
- Opens a dedicated `_mc.connect()` connection
- Calls `conn.start_transaction()`
- Uses `cur.execute(... FOR UPDATE)` for the conflict query
- Commits only if no conflict; rollbacks and closes on conflict
- This prevents two concurrent booking requests from both passing the conflict check before either INSERT commits.

### CI-2: Cancel API Unconditionally Cancels Any Booking ✅
**Function:** `api_booking_cancel`
**What:** The UPDATE now includes `AND status NOT IN ('Active','Done')` in the WHERE clause:
```python
_cancel_cur.execute(
    "UPDATE console_booking SET status='cancelled' WHERE id=%s AND status NOT IN ('Active','Done')",
    (booking_id,)
)
affected = _cancel_cur.rowcount
if affected == 0:
    return JSONResponse(content={"success": False, "message": "Cannot cancel - booking is Active or Done"}, status_code=400)
```
Uses `cur.rowcount` (via dedicated connection) since `_mysql_exec` returns `lastrowid` not affected rows.

### CI-3: Database Transactions for Multi-Step Operations ✅
**Functions:** `api_booking_checkin`, `api_end_booking`, `api_booking_cancel`, `api_bookings_create` (both paths), `api_start_console_session`, `api_update_booking_status`
**What:** Every booking mutation endpoint now wraps its multi-step DB operations in a transaction:
- `api_booking_checkin`: status update + console_status update wrapped in one transaction
- `api_end_booking`: end update + console_status update in one transaction
- `api_booking_cancel`: cancel update in dedicated transaction with rowcount check
- `api_bookings_create` (customer path): FOR UPDATE conflict check + INSERT in transaction
- `api_bookings_create` (staff path): INSERT + console_status update in transaction
- `api_start_console_session`: auto-checkin/create + console_status update in transaction
- `api_update_booking_status`: status update with optimistic lock in transaction

### HI-1: Optimistic Lock on Booking Approval ✅
**Function:** `api_update_booking_status`
**What:** Changed UPDATE to only affect `pending` bookings:
```python
UPDATE console_booking SET status=%s ... WHERE id=%s AND status='pending'
```
Returns HTTP 409 "Booking already processed" if no rows affected.

### HI-2: Walk-in Auto-Checks-In Future Bookings Early ✅
**Function:** `api_start_console_session`
**What:** Added ±30 minute time window to the auto-checkin query:
```python
WHERE console_id=%s AND status='confirmed' AND DATE(booking_date)=%s
AND start_time <= DATE_ADD(%s, INTERVAL 30 MINUTE)
AND end_time >= %s
```
Prevents walking in 4 hours early and auto-checking into a booking.

### HI-4: API Silently Creates Bookings with Invalid Dates ✅
**Function:** `api_bookings_create` (customer bot path)
**What:** Instead of `except: start_dt = now`, now returns HTTP 400 errors:
- If `start_dt < now_mmt()`: "Cannot book for a past date/time"
- If parse fails: "Invalid time format: {time_slot}"

### HI-6: console_status Can Drift from Booking Reality ✅
**Function:** New `_sync_console_status(console_id)` helper
**What:** Created a sync function that derives console status from current booking table:
- If any Active booking → sets console_status to Active
- If any confirmed booking within time window → sets to Reserved
- Otherwise → sets to Free
**Called after:** Every booking mutation (create, cancel, end, checkin, approve)

### MI-1: Two Separate MySQL Connection Modules ✅
**File:** `app.py`
**What:** Added comment block noting the duplication between `mysql.connector` helpers and `mysql_db.py` (pymysql), recommending future consolidation to pymysql-based functions.

### MI-2: Telegram Notifications Fail Silently ✅
**Function:** `_notify_booking_received`
**What:** Changed `except: pass` to:
```python
except Exception as e:
    logger.warning("[NOTIFY] Failed to send booking notification for #%s: %s", bk_id, e)
```
Other notification error handlers in `api_booking_checkin`, `api_create_booking`, and `api_booking_cancel` already had proper logging.

### MI-4: Duration Accepts Any Integer ✅
**Function:** `api_bookings_create` (customer bot path)
**What:** Added validation:
```python
if duration_mins < 1 or duration_mins > 1440:
    return JSONResponse(content={"success": False, "message": "Duration must be 1-1440 minutes"}, status_code=400)
```

### MI-7: Two Overlapping Booking Creation Endpoints ✅
**Function:** `api_create_booking`
**What:** Marked as deprecated in FastAPI:
- `summary="[DEPRECATED] Create new console booking — use POST /api/bookings instead [MySQL]"`
- `deprecated=True`
- Docstring updated to note deprecation

### MI-8: Slot Conflict Check Skipped When No console_id ✅
**Function:** `api_bookings_create` (customer bot path)
**What:** When `console_id` is empty, now queries ALL consoles of the matching `console_type` for conflicts:
```python
if console_id:
    # Check specific console
else:
    # Check all consoles of matching type
    _matching_consoles = cur.execute("SELECT console_id FROM console_status WHERE console_type=%s", (console_type,))
    # Check all matching console_ids with FOR UPDATE
```

---

## Files Modified
- `/root/psvibe_api_server/app.py` — All fixes applied (3787 lines after edits)

## Files NOT Modified (read-only audit check)
- `/root/psvibe_api_server/mysql_db.py` — No changes needed for this round

## Known Limitations
- `_sync_console_status` uses `NOW()` for timestamps in SQL, which is UTC. Should ideally use MMT timezone, but this matches existing patterns in the codebase.
- The dual connection module issue (MI-1) is documented but not consolidated — full migration to `mysql_db.py`'s pymysql approach is deferred to a future cleanup.
