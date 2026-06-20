# 🐛 Bug Patterns — PS VIBE Sales Bot

> ⏳ = Known but unsolved

## String-Based Editing Misses Comment-Annotated Lines (2026-06-20)

**Pattern:** When using Python scripts for batch string replacement, `str.strip()` or exact-match checks can miss lines with trailing comments.

**Example:**
```python
# Script checks: line.strip() == 'return 0'
# Fails on:       return 0  # Console is Active/Unavailable
# Because:        line.strip() produces 'return 0  # Console is Active/Unavailable'
```

**Symptom:** One function return value is wrong type → crashes downstream.

**Fix:** Always verify with `grep` after batch edits, or use regex that accounts for optional comments.

**Affected bugs:** #44 (return 0 tuple miss)

## Rejected Status Not Excluded from Active Filters (2026-06-20)

**Pattern:** Status filters that exclude cancelled/done bookings often forget `"rejected"` — rejected bookings are also inactive and should be excluded.

**Symptom:** Rejected bookings trigger duplicate warnings, conflict detection, or show up in active lists.

**Fix:** Always include `"rejected"` in inactive status lists alongside `("cancelled", "done")`.

**Affected bugs:** #45 (duplicate check on rejected bookings)

## UnboundLocalError: Variable Scope Across Branches (2026-06-20)

**Pattern:** Variable defined inside one `if` branch but accessed in another `if/else` branch.

**Example:**
```python
if action == "approve":
    bk_info = ...  # defined here only
# --- several blocks later ---
if action == "reject":  # or: else:
    customer_name = bk_info.get(...)  # ❌ UnboundLocalError!
```

**Fix:** Move variable definition BEFORE all conditional branches that use it.

**Affected bugs:** #38 (consoles_with_game), #39 (bk_info)

## ConversationHandler Interferes with context.user_data (2026-06-20)

**Pattern:** State stored in `context.user_data` between CallbackQueryHandler and MessageHandler gets lost/altered by ConversationHandler's internal state management.

**Symptom:** MessageHandler at group -1 fires but `context.user_data.get('key')` returns None.

**Fix:** Use `context.bot_data` keyed by `user_id` instead of `context.user_data`.

**Affected bugs:** #40 (reject reason flow)

## ValueError from API Treated as Crash (2026-06-20)

**Pattern:** `_validate_response()` raises `ValueError` for HTTP 4xx/5xx. If your `try/except` only has blanket `except Exception`, the API error gets treated as a crash (generic "ခဏနေ ပြန်ကြိုးစားပါ") instead of a booking failure (show specific error + max duration).

**Symptom:** Customer sees generic crash message instead of specific booking error.

**Fix:** Add `except ValueError` BEFORE `except Exception`. Handle ValueError as a booking failure (calculate max_dur, show specific message). Reserve `except Exception` for truly unexpected crashes.

**Affected bugs:** #42 (auto-assign duration v3)

## API Error vs Exception — Different User Experience (2026-06-20)

**Pattern:** When `_api._api_post` fails due to HTTP 409 Conflict (duration too long), it raises `ValueError`. The caller should interpret this as "booking not possible under current constraints" → show helpful guidance (max available duration). Only true network/unexpected errors should show generic "try again" message.

**Decision tree for `_submit_booking`:**
```
try _api_post("bookings")
  ✅ Success → show confirmation
  ❌ result error → check max_dur → show guidance
catch ValueError (API HTTP error) → check max_dur → show guidance  
catch Exception (network/crash) → generic "try again"
```

**Affected bugs:** #42 (auto-assign duration v3)

## Session Timer Drift on Bot Restart (FIXED — 2026-06-18)
- Bot restart → end-of-session timer drifts forward by 2h+
- **Root cause:** `_end_dt_iso = datetime.now() + planned_mins` — `now` = restart time, not original start
- **Fix:** Calculate end time from stored `end_t` (HH:MM format), not from current time
- **Pattern:** NEVER use `datetime.now()` in restore/boot code for time calculations. Always derive from stored absolute values.

## _sync_console_status() Overwrites Active start_time (FIXED — 2026-06-18)
- Booking operations (checkin, cancel, extend) → sync → `start_time=NOW()` resets already-running timers
- **Root cause:** `_sync_console_status()` unconditionally sets `start_time=NOW()`
- **Fix:** Check `already_active` before updating start_time — only set for newly activated consoles
- **Pattern:** Sync/utility functions that update state must check current state first (idempotency). Blind `SET col=NOW()` on every sync = timer reset bug.

## Payment Cash Calculation (FIXED)
- `d["cash"] = net - total_paid` → `d["cash"] = payments.get("Cash", 0)`

## Wallet Balance Column H (FIXED — 3 bugs)
- Sale flow, new registration, top-up — none wrote to Card_Wallet Column H
- Added `update_cell` / `batch_update` for Column H in all 3 paths

## Double Multiplier in wallet_game_value (FIXED)
- `eff_mins` already × multiplier, then `wallet_val` applied mult again
- Removed mult from formula when `effective_cost_mins` already includes it

## Member Console Multiplier (FIXED)
- Members always got 1.0x. Added `fetch_console_multiplier()` for non-guest members.

## Console ID URL Encoding (⏳ KNOWN)
- Console IDs = "C - 01" (with spaces), `_api_call()` doesn't URL-encode
- Falls back to gspread (slow but works)

## Customer Bot — Menu Eaten by ConversationHandler (FIXED)
- All reply keyboard menu buttons consumed by booking text handlers
- Added `_bk_intercept_menu()` to all 7 text-accepting states
- **Lesson:** Check ALL related handlers, not just the reported one

## Git Push Blocked by SA JSON (FIXED)
- `git push` blocked because commit contained `kora_drive_sa.json` in cache files
- GitHub push protection — NEVER commit SA JSON

## API Server is SEPARATE from Bot (FIXED)
- Two repos! Sub-agents almost always miss the API server
- **Always check BOTH repos when investigating bugs**
- Include `PROJECT_STRUCTURE.md` in EVERY sub-agent spawn context

## Parallel Agent Collision — Same Function Overwrite (FIXED)
- Multiple fix agents modified the same function (`_fetch_games_from_mysql()`) in parallel
- Speed fix (76f203f) → Topup fix (ef9d733) → Game fix (c4ea16a) — chain of overwrites
- **Use Task Planner FIRST** to identify function-level conflicts

## Bot Crash Loop — KeyError: 0 → 703 Restarts (FIXED)
- `KeyError: 0` in asyncio task crashes bot with NO visible journal error
- systemd `Restart=always` silently restarts (703 lifetime!)
- **Fix:** Added `asyncio.get_event_loop().set_exception_handler()` in `bot/app.py`
- **Check:** `systemctl show <service> -p NRestarts`

## chr() Encoding Corruption in Auto-Fix (FIXED)
- Fix script replaced `d["nm_name"]` with `d[chr(39)+chr(110)+...]` → `d["'nm_name'"]`
- Quotes became part of key! `KeyError` because key is literal `'nm_name'`
- **Fix:** Always `ast.parse()` output before deploying auto-generated code

## MySQL-GSheet Sync Deletion Gap (KNOWN)
- Deleting from GSheet does NOT delete from MySQL `member_wallets`
- n8n handles INSERT/UPDATE only, not DELETE
- Stale rows cause wrong API data
- **Lesson:** Schema gaps include missing DELETE sync

## Missing Comma = API Crash Loop (FIXED 2026-06-02)
- Missing trailing comma in `patch_routes.py` → SyntaxError → API won't start
- systemd restart loop (65+), status shows "activating" forever
- **Fix:** Add comma. **Lesson:** Always `ast.parse()` after manual dict edits.

## MarkdownV2 `-` Character Escape (FIXED 2026-06-02)
- FAQ template `"Mon-Sun: 10AM-11PM"` — unescaped `-` causes `Can't parse entities`
- **Fix:** Use `_to_mdv2()` escape before any MarkdownV2 text

## API Key Mismatch After MySQL Migration (FIXED 2026-06-02)
- CallNames (36/36) & endpoint paths: 100% match
- But **Data keys** 12 mismatch (CRITICAL, HIGH, MED)
- **Fix:** API server dual key format accept + bot `__init__.py` key mapping
- **Lesson:** MySQL migration → check API response keys match bot handler expectations

## Coupon API Field Name Mismatch (FIXED — 2026-06-05)
- Bot checked `cd.get("coupon_code")`/`cd.get("coupon_mins")` but API returns `code`/`minutes`
- **Root cause:** Bot-side field names differed from API response schema — no shared type definition
- **Fix:** Changed to `cd.get("code")`/`cd.get("minutes")` in `sales.py`
- **Lesson:** When adding API calls, verify response field names match the actual API output, not assumed names

## Wallet Deduction Endpoint Missing Variable (FIXED — 2026-06-05)
- `api_member_wallet_update()` used `deduct_mins` without reading it from request → NameError
- **Fix:** Added `deduct_mins = req.get("deduct_mins")` before usage
- **Pattern:** Python NameError in API endpoints — variable used but never read from request body

## GSheet _LazyWorksheet .title Returns Bound Method (FIXED — 2026-06-05)
- `getattr(worksheet, 'title', '')` on `_LazyWorksheet` proxy returns a bound method, not a string
- **Fix:** Use `getattr(worksheet, '_name', None)` first, fallback to `getattr(worksheet, 'title', '')`
- **Pattern:** gspread proxy objects may have properties that look like attributes but are methods

## API Client Auto-Unwrap Confusion (FIXED — 2026-06-06)
- Customer Bot's `_api._api_get()` auto-unwraps `{"success":true,"data":{items}}` → `{items}` directly
- When code checks `resp.get("success")` on already-unwrapped data → key doesn't exist → always fails
- **Same pattern as Sales Bot's double-unwrap** (`__init__.py` line ~95, fixed 2026-06-03)
- **Fix:** Just check `if not resp:` and use `items = resp or {}`
- **Pattern:** Any `_api_get` / `_api_call` with "get" in name likely unwraps data. Audit ALL handlers if one mismatches.

## Unicode Escape Corruption in Auto-Fix Pipeline (FIXED — 2026-06-06)
- Burmese Unicode escapes (`\u1012\u103d\u102c...`) can be corrupted by auto-fix/auto-commit scripts
- Escaped sequences get re-escaped → garbled text displayed ("ဒွာသေါင္နေါဇွေနှင္းး")
- **Fix:** Use simple English text or direct Unicode chars, never double-escaped sequences
- **Pattern:** When bot shows garbled/nonsense Burmese text → check for corrupted Unicode escape sequences

## Python .pyc Cache Stale (FIXED — 2026-06-09)
- Edit .py file → restart service → `NameError: name 'X' is not defined` even though X is clearly in file
- **Root cause:** Python cached bytecode (`.pyc`/`__pycache__`) still has old code; `systemctl restart` doesn't clear it
- **Fix:** `find ... -name '*.pyc' -delete` AND `find ... -name '__pycache__' -type d -exec rm -rf {} +` THEN restart
- **Pattern:** Any backend edit that returns "not defined" error despite correct code

## String replace() Whitespace Mismatch (FIXED — 2026-06-09)
- Python patch script with `txt.replace(old, new)` silently does nothing — no error, no change
- **Root cause:** `old` string has different whitespace/newline count than actual file (e.g., `\n\n` vs `\n`)
- **Fix:** Use `repr(txt[idx:idx+N])` to verify exact whitespace before patching
- **Pattern:** After Python patch script says "done" but file hasn't changed

## Balance Sheet: Retained Earnings Missing Depreciation (FIXED — 2026-06-09)
- After adding Fixed Assets depreciation, BS shows Assets > L+E
- **Root cause:** `retained = ti - te - cost_of_sold - member_liab` — no `- total_dep`
- **Fix:** `retained = ti - te - cost_of_sold - member_liab - total_dep`
- **Pattern:** Any time accumulated depreciation is added to BS, retained earnings must subtract it too

## AYA Pay Missing After Restart/Apply Fixes (FIXED — 2026-06-16)
- AYA Pay disappears from payment options after bot restart or `apply_fixes.py` run
- **Root cause:** `PAY_METHODS` constant exists in BOTH `bot/constants.py` AND `apply_fixes.py`. Modifying only one leaves the other stale. `apply_fixes.py` overwrites constants.py on every run.
- **Fix:** Add "AYA Pay" to BOTH `bot/constants.py` (L35) AND `apply_fixes.py` PAY_METHODS injection list
- **Pattern:** Any shared constant/setting that's duplicated across a "source" file and a "fix/override" file — always check both

## Session Extended Reminder: Missing message_thread_id (FIXED — 2026-06-16)
- Extended sessions lose reminder notifications
- **Root cause:** `_do_extend()` calls `notify_update()` without passing `message_thread_id`. The reminder store persists `message_thread_id` during initial booking but the extend flow doesn't carry it forward.
- **Fix:** Add `message_thread_id` parameter through extend call chain (`booking_flow.py` → `console.py` → `sales.py`), use `kwargs.get("message_thread_id")` in `notify_update()`
- **Pattern:** When a feature has an "initial" flow and an "update/extend" flow, the update flow may drop parameters that the initial flow correctly passes

## Session Reminder: "Plan: 1 min" After Extend (FIXED — 2026-06-16)
- After session extension, reminder shows wrong remaining time ("Plan: 1 min")
- **Root cause:** `rem_mins = max(1, int(total_rem_secs / 60))` calculates remaining seconds from end time. When session is extended with only ~1 min left, rem_mins = 1. Missing `_SESSION_TOTAL_MINS` dict to track accumulated session duration.
- **Fix:** Added `_SESSION_TOTAL_MINS` dict that accumulates total minutes across extensions; display uses accumulated total instead of remaining time
- **Pattern:** Remaining time != total session time after an extension. Always track both.

## Session Extend — Console Status Not Updating (FIXED — 2026-06-17)
- Staff extends session via reminder → "Extended!" message shown ✅
- But `/status` / Console Status Board still shows OLD duration ❌
- **Root cause:** `_do_extend()` in `booking_flow.py` used `asyncio.ensure_future(_psvibe_post_async(...))` — fire-and-forget!
  - API call runs in background without await
  - If API call fails silently (network blip, server error), ONLY the error is logged
  - `_SESSION_END_TIMES` / `_SESSION_TOTAL_MINS` updated in-memory ✅ (so End Session shows correct total)
  - But `console_booking.duration_mins` in MySQL NOT updated ❌ → `/status` reads from DB → shows old duration
- **Fix:** Changed `asyncio.ensure_future(...)` to `await _psvibe_post_async(...)`
  - DB sync now happens BEFORE function returns
  - Added error message to staff if DB sync fails (instead of silent swallow)
- **Secondary issue:** 3 orphaned Active bookings found (id=434,444,463) where session ended but console_booking.status never set to 'Done'. Fixed.
- **Pattern:** `asyncio.ensure_future()` with fire-and-forget = silent failure risk. If the result matters (like DB sync), always `await`.

## Customer Booking Slot — Date Filter Ignored by API (FIXED — 2026-06-16)
- Customer Bot slot availability shows "No consoles available" even when consoles are free
- **Root cause:** `GET /api/search-bookings` endpoint had no `date` query parameter. Client sends `date=2026-06-17` but API ignores it — SQL query returns ALL bookings across all dates → slot logic marks everything unavailable
- **Fix:** Added `date: str = Query("")` parameter to endpoint; built dynamic WHERE clause with date normalization (supports 5 date formats)
  ```python
  sql = "SELECT ... FROM console_booking WHERE 1=1"
  if date:
      sql += " AND booking_date=%s"
      params.append(cleaned_date)
  ```
- **Pattern:** When an API endpoint has a `date`/`filter` parameter in the client call but NOT in the server's function signature or SQL query, it becomes a silent no-op — the code works but returns wrong data. Always cross-check: (1) endpoint function parameters, (2) SQL WHERE clause, (3) client call parameters.

## In-Memory State Lost on Bot Restart (FIXED)
- `_SESSION_TOTAL_MINS` dict က in-memory-only → bot restart တိုင်း extend အတွက် total mins တန်ဖိုးတွေ ပျောက်သွားပြီး "Plan: 1 min" ပြတယ်
- **Fix:** `session_reminder_store.py` persist/restore logic ထဲမှာ `total_plan_mins` ကို JSON နဲ့ serialise လုပ်
- **Lesson:** Any in-memory state that should survive restart must be explicitly persisted to a file. `_SESSION_TOTAL_MINS` is a dict living in the bot process — gone on restart. Pair with `session_reminders.json` (or equivalent) for restart survival.

## Food Cart Lost in Voucher After Session End — booking_id Lookup After Booking Ended (FIXED)
- Food Note → food_cart table ထဲမှာ items တွေကို booking_id နဲ့ သိမ်းတယ်
- Session End → `step_end_session()` က console_status ကနေ `bk_id` ကို ရှာတယ် ✅
- `end_booking_async(bk_id)` → booking status → 'Done' ✅
- ပြီးမှ `_linked_bk_id` ကို `bookings?memberId={mbr}` API နဲ့ ထပ်ရှာတယ် ❌
- Filter: status IN ('confirmed','arrived','in_use','Active') — 'Done' က exclude
- Result: `_linked_bk_id` က empty → `launch_session_sale()` မှာ `booking_id=''` → food cart items က ဘယ်တော့မှ load မလုပ်ခံရဘူး
- **Fix:** `_linked_bk_id = bk_id` (console_status ကနေရတဲ့ ID ကိုတန်းသုံး) — fallback အနေနဲ့ member lookup ကို bk_id empty မှသာလုပ်မယ်
- **Lesson:** After ending a booking, never try to find it again by status filter. Use the ID you already had from the pre-end console status lookup.

## Plan Display Wrong After Session Extend (FIXED — 2026-06-17)
- **Symptom:** After extending a session, the reminder shows wrong "Plan: X mins" value. First extension loses the original plan minutes entirely (e.g., 240 min + 30 min extend shows "30 mins" instead of "270 mins").
- **Root cause:** `_SESSION_TOTAL_MINS` dict is never initialized when `_remind_loop()` starts (line 102-104 in `booking_flow.py`). When `_do_extend()` calls `.get(_session_key, 0)`, it returns 0, so `_SESSION_TOTAL_MINS[_session_key] = 0 + extra_mins` — losing the original plan.
- **Fix:** Added `if key not in _SESSION_TOTAL_MINS: _SESSION_TOTAL_MINS[key] = planned_mins` in `_remind_loop()` right after `_SESSION_END_TIMES[key] = end_t`.
- **Pattern:** Any module-level dict that tracks session state across functions must be initialized at the FIRST entry point (`_remind_loop`), not only at mutation points (`_do_extend`).
