# Archived Memory Entries
*Archived: 2026-06-09 05:49 UTC*

(dedup) psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅ | psvibe-dashboard ✅
  (dedup) - psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅
  (dedup) - 4. Checked coupon generation in `step_sale_confirm` → calls `api_post` from `bot/api_client.py`, which uses `?api_key=` query param (fails with 401)
  (dedup) - 1. **`api_client.py` `api_post()`** uses `?api_key=` query param → 401 response → coupon generation silently fails
  (dedup) - 2. **`api_client.py` `api_get()`** also uses `?api_key=` query param → would fail on any GET
  (dedup) - psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅
  (dedup) - psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅
  (dedup) - "book_value": float(a.get("book_value", 0) or 0) or (float(a.get("amount", 0) or 0) - float(...))
  (dedup) - psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅ | psvibe-dashboard ✅
  (dedup) - `net_position = assets_total - advances_pending - prepaid_total`
  (dedup) - ✅ Services: psvibe-api ✅, psvibe_customer_bot ✅, psvibe-sale-bot ✅
  (dedup) - psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅ | psvibe-dashboard ✅
  (dedup) - **Total Monthly Dep:** 4,029,826 Ks | **Total Acc. Dep:** 3,262,283 Ks

# Archived Memory Entries
*Archived: 2026-06-10 04:37 UTC*

(dedup) 9. **Python `.pyc` cache stale after edit:** Always `find -name '__pycache__' -exec rm -rf {} +` then restart

# Archived Memory Entries
*Archived: 2026-06-10 16:38 UTC*

(dedup) - psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅ | psvibe-dashboard ✅

# Archived Memory Entries
*Archived: 2026-06-11 15:31 UTC*

(dedup) - Knowledge graph: ✅ 54 nodes, 1418 edges
  (dedup) - Knowledge graph: ✅ 54 nodes, 1418 edges
  (dedup) - Stale lock cleanup: ✅ 0 cleaned
  (dedup) - 1. 📅 Real Booking Schedule (9AM-9PM timeline, color-coded)
  (dedup) - 2. 💰 Real Sales Chart (7-day Canvas bar chart)
  (dedup) - 3. 🔍 Member Quick Lookup (search + wallet balance)
  (dedup) - 4. ⚠️ Smart Alerts Panel (health alerts)
  (dedup) - 5. 📦 Food Stock Status (menu + stock levels)
  (dedup) - 6. 📊 End-of-Day Summary (today's panel)
  (dedup) - 9. ⚡ Quick Commands (Health, Docker, Uptime, Backups)
  (dedup) - **MEMORY.md truncation:** Session context loads ~11KB of ~40KB file. Keep MEMORY.md ≤20KB — use module files for details

# Archived Memory Entries
*Archived: 2026-06-12 20:07 UTC*

(dedup) 5. **GitHub Deploy failing** — PSVIBE-API-Server master branch
  (dedup) 10. disc_count values are intentional — never "fix" without Boss confirmation

# Archived Memory Entries
*Archived: 2026-06-13 17:07 UTC*

(dedup) 1. **n8n Payment (€25.68)** — 2nd notice received, subscription may expire
  (dedup) 2. **GitHub Deploy Failing** — PSVIBE-API-Server master branch deploy workflow failing

# Archived Memory Entries
*Archived: 2026-06-15 16:07 UTC*

(dedup) 1. **n8n payment (€25.68)** — 2nd notice, subscription may expire
  (dedup) 2. **GitHub Deploy failing** — psvibe-api-server master branch

# Archived Memory Entries
*Archived: 2026-06-16 15:37 UTC*

(dedup) - **Root cause:** Added coupon API call but used `cd.get("coupon_code")` and `cd.get("coupon_mins")` — API response uses `code` and `minutes`
  (dedup) - **Fix:** Changed to `cd.get("code")` and `cd.get("minutes")`
  (dedup) - **Files:** `bot/handlers/sales.py` — both `step_sale_confirm()` and `launch_session_sale()`
  (dedup) - **Status:** ✅ Boss confirmed coupon is showing
  (dedup) - **Root cause:** API server's `api_member_wallet_update()` endpoint was missing `deduct_mins = req.get("deduct_mins")` — variable undefined, NameError caught, returned `success=false`
  (dedup) - **Fix:** Added `deduct_mins = req.get("deduct_mins")` to the endpoint
  (dedup) - **File:** `/root/psvibe_api_server/app.py` line 2097
  (dedup) - **Status:** ✅ Verified working (600→540 mins deducted)
  (dedup) - **Root cause:** FastAPI's `response_model=GenericResponse` only had `success`, `message`, `data` — when `error_response()` returned `{"success":false,"error":"...","code":500}`, FastAPI STRIPPED the `error` field
  (dedup) - **Result:** Bot always saw `{"success":false,"message":null,"data":null}` with `error=unknown`
  (dedup) - **Fix:** Added `error: Optional[str] = None` to `GenericResponse` in `models.py`
  (dedup) - **File:** `/root/psvibe_api_server/models.py`
  (dedup) - **Impact:** Now error messages from API will be visible in bot logs
  (dedup) - **Root cause:** `getattr(worksheet, 'title', '')` on `_LazyWorksheet` proxy returns bound method instead of string in some cases
  (dedup) - **Fix:** Changed to `getattr(worksheet, '_name', None) or getattr(worksheet, 'title', '')`
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/__init__.py` — `next_write_row` function
  (dedup) - `psvibe-api` — ✅ active (restarted multiple times)
  (dedup) - `psvibe-sale-bot` — ✅ active (restarted)
  (dedup) - `psvibe_customer_bot` — ✅ active
  (dedup) - `/root/psvibe_api_server/app.py` — added `deduct_mins = req.get("deduct_mins")`
  (dedup) - `/root/psvibe_api_server/models.py` — added `error: Optional[str]` to GenericResponse
  (dedup) - `/root/psvibe-sales-bot/bot/__init__.py` — fixed `next_write_row` title lookup
  (dedup) - **Root cause:** Added coupon API call but used `cd.get("coupon_code")` and `cd.get("coupon_mins")` — API response uses `code` and `minutes`
  (dedup) - **Fix:** Changed to `cd.get("code")` and `cd.get("minutes")`
  (dedup) - **Files:** `bot/handlers/sales.py` — both `step_sale_confirm()` and `launch_session_sale()`
  (dedup) - **Status:** ✅ Boss confirmed coupon is showing
  (dedup) - **Root cause:** API server's `api_member_wallet_update()` endpoint was missing `deduct_mins = req.get("deduct_mins")` — variable undefined, NameError caught, returned `success=false`
  (dedup) - **Fix:** Added `deduct_mins = req.get("deduct_mins")` to the endpoint
  (dedup) - **File:** `/root/psvibe_api_server/app.py` line 2097
  (dedup) - **Status:** ✅ Verified working (600→540 mins deducted)
  (dedup) - **Root cause:** FastAPI's `response_model=GenericResponse` only had `success`, `message`, `data` — when `error_response()` returned `{"success":false,"error":"...","code":500}`, FastAPI STRIPPED the `error` field
  (dedup) - **Result:** Bot always saw `{"success":false,"message":null,"data":null}` with `error=unknown`
  (dedup) - **Fix:** Added `error: Optional[str] = None` to `GenericResponse` in `models.py`
  (dedup) - **File:** `/root/psvibe_api_server/models.py`
  (dedup) - **Impact:** Now error messages from API will be visible in bot logs
  (dedup) - **Root cause:** `getattr(worksheet, 'title', '')` on `_LazyWorksheet` proxy returns bound method instead of string in some cases
  (dedup) - **Fix:** Changed to `getattr(worksheet, '_name', None) or getattr(worksheet, 'title', '')`
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/__init__.py` — `next_write_row` function
  (dedup) - **Root cause:** Line 1301 in `bot/handlers/sales.py`:
  (dedup) - `_disc = discount if discount else ""` → when `discount=0`, converts to `""`
  (dedup) - API endpoint does `float(req.get("discount", 0))` → `float("")` → `ValueError`
  (dedup) - FastAPI catches error → returns `success=false: internal error`
  (dedup) - GenericResponse bug (#3) silently stripped the actual error message
  (dedup) - **Fix:** Changed to `_disc = discount if discount else 0`
  (dedup) - **Impact:** Both API path (MySQL) AND GSheet fallback were broken — double fail masked the root cause
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
  (dedup) - **Symptom:** Sale bot stuck at booking menu after restart — "New Booking" button visible but does nothing
  (dedup) - **Root cause:** `_sbk_console_kb()` function was made `async` in a previous fix, but the calling code still used `rows = _sbk_console_kb()` WITHOUT `await`
  (dedup) - **Result:** `rows` gets a coroutine object instead of the keyboard layout → `InjectedKeyboard` silently fails
  (dedup) - **Fix:** Changed to `rows = await _sbk_console_kb()`
  (dedup) - **File:** `bot/handlers/sales.py` (around booking conversation handler)
  (dedup) - **Status:** ✅ Fixed, bot restarted
  (dedup) - **Status:** ✅ Fixed, Boss confirmed booking is working
  (dedup) - **File:** `/root/psvibe_api_server/app.py` — `api_bookings_create()` endpoint
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
  (dedup) 1. **FastAPI response_model silently strips undeclared fields** — always audit response models against actual return shapes
  (dedup) 2. **`bool(0) == False`** — `"x if x else default"` pattern breaks on `0`; use `"x if x is not None else default"` instead
  (dedup) 3. **`async def` + missing `await`** — coroutine objects silently pass type checks at runtime, cause confusing failures. Always use proper type hints to catch this.
  (dedup) 4. **Double fail masking** — Both API (MySQL) and GSheet fallback were broken simultaneously → masked the true root cause. Monitor both paths independently.
  (dedup) - `psvibe_customer_bot` — ✅ active
  (dedup) - `/root/psvibe_api_server/models.py` — `error: Optional[str]` added to GenericResponse
  (dedup) - `/root/psvibe-sales-bot/bot/__init__.py` — `next_write_row` title lookup fix
  (dedup) - `/root/psvibe-sales-bot/bot/handlers/sales.py` — coupon field names, `_disc` fix, console normalization, booking `await`, `_notify_customer` import
  (dedup) - **All critical path bugs fixed:**
  (dedup) - ✅ Console normalization (spaces in console IDs)
  (dedup) - ✅ Error messages now visible from API
  (dedup) - **Root cause:** Added coupon API call but used `cd.get("coupon_code")` and `cd.get("coupon_mins")` — API response uses `code` and `minutes`
  (dedup) - **Fix:** Changed to `cd.get("code")` and `cd.get("minutes")`
  (dedup) - **Files:** `bot/handlers/sales.py` — both `step_sale_confirm()` and `launch_session_sale()`
  (dedup) - **Status:** ✅ Boss confirmed coupon is showing
  (dedup) - **Root cause:** API server's `api_member_wallet_update()` endpoint was missing `deduct_mins = req.get("deduct_mins")` — variable undefined, NameError caught, returned `success=false`
  (dedup) - **Fix:** Added `deduct_mins = req.get("deduct_mins")` to the endpoint
  (dedup) - **File:** `/root/psvibe_api_server/app.py` line 2097
  (dedup) - **Status:** ✅ Verified working (600→540 mins deducted)
  (dedup) - **Root cause:** FastAPI's `response_model=GenericResponse` only had `success`, `message`, `data` — when `error_response()` returned `{"success":false,"error":"...","code":500}`, FastAPI STRIPPED the `error` field
  (dedup) - **Result:** Bot always saw `{"success":false,"message":null,"data":null}` with `error=unknown`
  (dedup) - **Fix:** Added `error: Optional[str] = None` to `GenericResponse` in `models.py`
  (dedup) - **File:** `/root/psvibe_api_server/models.py`
  (dedup) - **Impact:** Now error messages from API will be visible in bot logs
  (dedup) - **Root cause:** `getattr(worksheet, 'title', '')` on `_LazyWorksheet` proxy returns bound method instead of string in some cases
  (dedup) - **Fix:** Changed to `getattr(worksheet, '_name', None) or getattr(worksheet, 'title', '')`
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/__init__.py` — `next_write_row` function
  (dedup) - **Root cause:** Line 1301 in `bot/handlers/sales.py`:
  (dedup) - `_disc = discount if discount else ""` → when `discount=0`, converts to `""`
  (dedup) - API endpoint does `float(req.get("discount", 0))` → `float("")` → `ValueError`
  (dedup) - FastAPI catches error → returns `success=false: internal error`
  (dedup) - GenericResponse bug (#3) silently stripped the actual error message
  (dedup) - **Fix:** Changed to `_disc = discount if discount else 0`
  (dedup) - **Impact:** Both API path (MySQL) AND GSheet fallback were broken — double fail masked the root cause
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
  (dedup) - **Status:** ✅ Fixed, Boss confirmed working
  (dedup) - **Symptom:** Sale bot stuck at booking menu after restart — "New Booking" button visible but does nothing
  (dedup) - **Root cause:** `_sbk_console_kb()` function was made `async` in a previous fix, but the calling code still used `rows = _sbk_console_kb()` WITHOUT `await`
  (dedup) - **Result:** `rows` gets a coroutine object instead of the keyboard layout → `InjectedKeyboard` silently fails
  (dedup) - **Fix:** Changed to `rows = await _sbk_console_kb()`
  (dedup) - **File:** `bot/handlers/sales.py` (around booking conversation handler)
  (dedup) - **Status:** ✅ Fixed, bot restarted
  (dedup) - **Symptom:** Sale Bot creates booking → API returns HTTP 500
  (dedup) - **Root cause:** Bot sends date as `6/6/2026` (M/D/YYYY) but API endpoint `api_bookings_create()` expects `%Y-%m-%d` (YYYY-MM-DD). `strptime` parse fails gracefully (falls back to `now`), but the raw `booking_date_str` (`6/6/2026`) was passed directly to MySQL INSERT → `Incorrect date value` error → HTTP 500
  (dedup) - **Fix:** Added multi-format date parsing in `api_bookings_create()` supporting: `%Y-%m-%d`, `%m/%d/%Y`, `%m-%d-%Y`, `%d/%m/%Y`, `%Y/%m/%d`. Uses the parsed `_parsed_date` (YYYY-MM-DD string) in the INSERT statement.
  (dedup) - **File:** `/root/psvibe_api_server/app.py` — `api_bookings_create()` endpoint
  (dedup) - **Status:** ✅ Fixed, Boss confirmed booking is working
  (dedup) - **Request:** Staff-created bookings (via Sale Bot) should auto-confirm without manual "Accept" step
  (dedup) - **Fix:** API endpoint now checks for `source == "staff"` OR presence of `staffNote` field in the booking payload. If staff booking → sets `status = "confirmed"` instead of `"pending"`. Customer-submitted bookings remain `pending → accept flow`.
  (dedup) - **File:** `/root/psvibe_api_server/app.py` — `api_bookings_create()` endpoint (status assignment logic)
  (dedup) - **Symptom:** Same console, same time could be double-booked
  (dedup) - **Fix:** Added slot conflict check in `api_bookings_create()`: before INSERT, check if any existing booking for the same `console_id` on the same `booking_date` at the same `start_time` has `status IN ('confirmed', 'pending_check_in')`. If conflict → return error with message "⏰ Console {console_id} သည် {booking_date} {start_time} တွင် ကြိုတင်စာရင်းရှိပြီးဖြစ်ပါသည်"
  (dedup) - **Note:** API-level check protects both dashboard and bot paths
  (dedup) - **File:** `/root/psvibe_api_server/app.py` — `api_bookings_create()` endpoint
  (dedup) - **Symptom:** Cancel booking doesn't work — `NameError: name '_notify_customer' is not defined`
  (dedup) - **Root cause:** `_notify_customer` function was referenced in `booking.py` but not imported
  (dedup) - **Fix:** Added `from bot.handlers.booking import _notify_customer` import in the cancel handler
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
  (dedup) - **Status:** ✅ Done, bot restarted
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/booking.py`
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py` or similar
  (dedup) - **Status:** ✅ Done (per Kora's claim; need Boss to verify)
  (dedup) 1. **FastAPI response_model silently strips undeclared fields** — always audit response models against actual return shapes
  (dedup) 2. **`bool(0) == False`** — `"x if x else default"` pattern breaks on `0`; use `"x if x is not None else default"` instead
  (dedup) 4. **Double fail masking** — Both API (MySQL) and GSheet fallback broken simultaneously → masked the true root cause
  (dedup) 5. **Date format inconsistency between bot and API** — Bot sends locale-dependent format; always normalize to YYYY-MM-DD at the API boundary
  (dedup) - `psvibe-sale-bot` — ✅ active
  (dedup) - `psvibe_customer_bot` — ✅ active
  (dedup) - ✅ Daily Sale recording to API/MySQL
  (dedup) - ✅ Auto-confirm for staff bookings
  (dedup) - psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅
  (dedup) 1. Browser lazy-loads `SaleDaily-DXRSp17u.js` ✅
  (dedup) 2. SaleDaily tries to import from `./index-DDJXoolO.js` ❌
  (dedup) 3. Cloudflare serves CACHED n8n content for this URL
  (dedup) 4. JavaScript fails → button does nothing
  (dedup) - Updated ALL 22 lazy-loaded chunks to import from `./index-DDJXoolO.v2.js` instead
  (dedup) - Also overwrote the original `index-DDJXoolO.js` with correct content (for safety)
  (dedup) - Main JS: `index-DDJXoolO.v2.js` (HTML ref)
  (dedup) - All lazy chunks: import from `./index-DDJXoolO.v2.js`
  (dedup) - Original file: `index-DDJXoolO.js` (overwritten with correct content)
  (dedup) - Auto-resolve: if `member_id` is provided but `phone` isn't → lookup `member_wallets` by member_id
  (dedup) - **Error:** `Can't parse keyboard button: can't find field 'text'` when selecting console
  (dedup) - Layer 1: `fetch_members_async()` wrapper (line 1491) needed `[m["id"] for m in result if ...]` mapping — ✅ fixed
  (dedup) - Layer 2: Alias at line 2541 (`fetch_members_async = api_fetch_members_async`) overrode the wrapper — **removed**
  (dedup) - **Result:** Booking flow now works for Guest (walk-in) ✅
  (dedup) - **Root cause:** `app.py` line 1517 had `@app.post("/api/consoles/start-session")` orphaned — decorated `api_session_end_notify` instead of `api_start_console_session`
  (dedup) - **Fix:** Moved decorator to line 1601 (before correct function)
  (dedup) - **Error:** `name '_psvibe_get_async' is not defined`
  (dedup) - **Root cause:** Function never existed in `api_client.py` — was imported in 3 places in `sales.py` but never defined
  (dedup) - **Fix:** Added `async def _psvibe_get_async(path)` to `api_client.py`
  (dedup) - **File:** `bot/handlers/booking_flow.py`
  (dedup) - **Root cause:** `_do_extend()` called `persist_reminder(..., message_thread_id)` but `message_thread_id` wasn't a parameter
  (dedup) - **Fix:** Added `message_thread_id: int = 0` parameter, updated both callers to extract from `query.message` / `update.message`
  (dedup) - **File:** `bot/handlers/notify.py`
  (dedup) - **Root cause:** `_check_low_balance_alert` used `os` module but never imported it
  (dedup) - **Fix:** Added `import os` (initially placed wrong — broke multi-line import — fixed in second attempt)
  (dedup) - **`inv_sh` = None** — K1 inventory Google Sheets update always fails silently (try/except catches it)
  (dedup) - **`fetch_balance_mins/-` 404** — Empty member_id when checking Guest wallet
  (dedup) - **Error:** `Can't parse keyboard button: can't find field 'text'` when selecting console
  (dedup) - Layer 1: `fetch_members_async()` wrapper (line 1491) needed `[m["id"] for m in result if ...]` mapping — ✅ fixed
  (dedup) - Layer 2: Alias at line 2541 (`fetch_members_async = api_fetch_members_async`) overrode the wrapper — **removed**
  (dedup) - **Result:** Booking flow now works for Guest (walk-in) ✅
  (dedup) - **Root cause:** `app.py` line 1517 had `@app.post("/api/consoles/start-session")` orphaned — decorated `api_session_end_notify` instead of `api_start_console_session`
  (dedup) - **Fix:** Moved decorator to line 1601 (before correct function)
  (dedup) - **Error:** `name '_psvibe_get_async' is not defined`
  (dedup) - **Root cause:** Function never existed in `api_client.py` — was imported in 3 places in `sales.py` but never defined
  (dedup) - **Fix:** Added `async def _psvibe_get_async(path)` to `api_client.py`
  (dedup) - **File:** `bot/handlers/booking_flow.py`
  (dedup) - **Root cause:** `_do_extend()` called `persist_reminder(..., message_thread_id)` but `message_thread_id` wasn't a parameter
  (dedup) - **Fix:** Added `message_thread_id: int = 0` parameter, updated both callers to extract from `query.message` / `update.message`
  (dedup) - **File:** `bot/handlers/notify.py`
  (dedup) - **Root cause:** `_check_low_balance_alert` used `os` module but never imported it
  (dedup) - **Fix:** Added `import os` (initially placed wrong — broke multi-line import — fixed in second attempt)
  (dedup) - **Error:** "Ovaltine cookies" (lowercase) chosen from food menu but `if choice not in prices:` failed because database has "Ovaltine Cookies" (capital C)
  (dedup) - **Root cause:** `step_food_menu` used exact/raw dictionary key lookup — case mismatch caused item to appear not found
  (dedup) - **Fix:** Added case-insensitive matching in `step_food_menu` and `step_food_qty` — uses `matched_key` to find correct-case key from `prices` dict, stores in `last_food_key` for quantity step
  (dedup) - **Files modified:** `bot/handlers/sales.py` — `step_food_menu()` + `step_food_qty()` functions
  (dedup) - **Result:** Ovaltine cookies, Ovaltine Cookies, or any case variant now matches ✅
  (dedup) - **Status:** Investigated but not fixed. Root cause inconclusive.
  (dedup) - Logs confirm `_remind_loop` task is created via `load_and_restore()` but **never executes** `_extend_timer_kb()` or `sendMessage`
  (dedup) 1. `asyncio.sleep(initial_delay)` silently never completes (event loop issue with `asyncio.get_event_loop().create_task`)
  (dedup) 2. Task is cancelled before sleep completes
  (dedup) 3. `initial_delay` is negative (if `next_remind_at` is in the past) → sleep never fires
  (dedup) - **Mitigation:** Staff using "No Timer" (`mins=0`) for recent sessions, so reminders not needed currently
  (dedup) - **Deferred:** Needs debug logging added inside `_remind_loop` to confirm reason
  (dedup) - **`inv_sh` = None** — K1 inventory Google Sheets update always fails silently (try/except catches it)
  (dedup) - **`fetch_balance_mins/-` 404** — Empty member_id when checking Guest wallet
  (dedup) - New button `BTN_FOOD_SALE` added to Console Management keyboard
  (dedup) - When clicked → shows list of active sessions → staff picks one via `/_console_session_food_pick`
  (dedup) - Calls `cmd_session_food_order(target)` which:
  (dedup) - Pre-fills member/console from session data
  (dedup) - Sets `session_food_order=True` flag
  (dedup) - Opens `prompt_food_menu`
  (dedup) - New function `cmd_session_food_order(update, context, target)` — sets up user_data with session info
  (dedup) - New function `_save_food_cart(update, context)` — intercepts `BTN_DONE` when flag is set:
  (dedup) - Saves items to food_cart via `POST /api/food-cart`
  (dedup) - Returns to Console Menu (no payment)
  (dedup) - Modified `step_food_menu`: checks `session_food_order` flag at `BTN_DONE`
  (dedup) - After `context.user_data.update({...})`, fetches `GET /api/food-cart/{booking_id}`
  (dedup) - Adds all cart items to `context.user_data["food_items"]` automatically
  (dedup) - Items appear in Daily Sales form when voucher opens
  (dedup) - psvibe-api ✅ (food-cart routes)
  (dedup) - psvibe-sale-bot ✅ (new handler functions)
  (dedup) - POST /api/food-cart: CREATE ✅
  (dedup) - GET /api/food-cart/B001: SELECT (unfulfilled only) ✅
  (dedup) - DELETE /api/food-cart/B001: UPDATE fulfilled_at ✅
  (dedup) - Python syntax: console.py ✅ sales.py ✅
  (dedup) - POST → GET → DELETE cycle verified on all food_cart API endpoints
  (dedup) - SQL query verified both create and fulfill timestamps correct
  (dedup) - Python compile check on both modified bot files
  (dedup) - Customer Bot direct ordering (customers order from their own chat)
  (dedup) - Customer Notifications when food arrives
  (dedup) - Multiple-food-order UI improvements (edit/remove items before Done)
  (dedup) - **Bot restarted:** psvibe-sale-bot ✅
  (dedup) 1. **n8n Payment (€25.68)** — 2nd notice, subscription may expire
  (dedup) 2. **GitHub Deploy Failing** — PSVIBE-API-Server master branch deploy workflow failing
  (dedup) - `fetch_balance_mins/-` 404 — Empty member_id when checking Guest wallet

# Archived Memory Entries
*Archived: 2026-06-16 17:37 UTC*

(dedup) ### 🧠 Critical Lessons Archive (continued)

# Archived Memory Entries
*Archived: 2026-06-16 18:46 UTC*

(dedup) - 22. **PAY_METHODS sync** — must update BOTH `constants.py` AND `apply_fixes.py`
  (dedup) - 23. **Reminder thread_id** — `message_thread_id` must carry through EVERY extend point
  (dedup) - 24. **Session total tracking** — `_SESSION_TOTAL_MINS` for proper remaining-time after extend
  (dedup) - 25. **API date filter** — endpoint signature, SQL WHERE clause, AND client call must all agree; missing any one = silent no-op

# Archived Memory Entries
*Archived: 2026-06-19 13:36 UTC*

(dedup) - **Status:** ✅ Fixed, Boss confirmed booking is working
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
  (dedup) - 1. **FastAPI response_model silently strips undeclared fields** — always audit response models against actual return shapes
  (dedup) - 2. **`bool(0) == False`** — `"x if x else default"` pattern breaks on `0`; use `"x if x is not None else default"` instead
  (dedup) - 3. **`async def` + missing `await`** — coroutine objects silently pass type checks at runtime, cause confusing failures. Always use proper type hints to catch this.
  (dedup) - 4. **Double fail masking** — Both API (MySQL) and GSheet fallback were broken simultaneously → masked the true root cause. Monitor both paths independently.
  (dedup) - `psvibe_customer_bot` — ✅ active
  (dedup) - `/root/psvibe_api_server/models.py` — `error: Optional[str]` added to GenericResponse
  (dedup) - `/root/psvibe-sales-bot/bot/__init__.py` — `next_write_row` title lookup fix
  (dedup) - `/root/psvibe-sales-bot/bot/handlers/sales.py` — coupon field names, `_disc` fix, console normalization, booking `await`, `_notify_customer` import
  (dedup) - **All critical path bugs fixed:**
  (dedup) - ✅ Console normalization (spaces in console IDs)
  (dedup) - ✅ Auto-confirm for staff bookings
  (dedup) - ✅ Error messages now visible from API
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/booking.py`
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py` or similar
  (dedup) - **Status:** ✅ Done (per Kora's claim; need Boss to verify)
  (dedup) - 1. **FastAPI response_model silently strips undeclared fields** — always audit response models against actual return shapes
  (dedup) - 2. **`bool(0) == False`** — `"x if x else default"` pattern breaks on `0`; use `"x if x is not None else default"` instead
  (dedup) - 4. **Double fail masking** — Both API (MySQL) and GSheet fallback broken simultaneously → masked the true root cause
  (dedup) - 5. **Date format inconsistency between bot and API** — Bot sends locale-dependent format; always normalize to YYYY-MM-DD at the API boundary
  (dedup) - `psvibe-sale-bot` — ✅ active
  (dedup) - `psvibe_customer_bot` — ✅ active
  (dedup) - ✅ Daily Sale recording to API/MySQL
  (dedup) - ✅ Auto-confirm for staff bookings
  (dedup) - const { execSync } = require('child_process');
  (dedup) - const out = execSync(`ssh -i /home/node/.openclaw/workspace/.ssh/id_rsa -o StrictHostKeyChecking=no root@5.223.81.16 "grep -n 'def.*pnl\\|def.*profit_loss\\|financial/pnl' /root/psvibe_api_server/dashboard_routes.py 2>/dev/null"`, { timeout: 15000 });
  (dedup) - **4/41 empty** (all unreleased: Basketball 2026, Expedition 33, FIFA 2026, Little Nightmare 3)
  (dedup) - Auto-resolve: if `member_id` is provided but `phone` isn't → lookup `member_wallets` by member_id
  (dedup) - **Bot restarted:** psvibe-sale-bot ✅
  (dedup) - `/root/psvibe_api_server/app.py`
  (dedup) - `/root/.openclaw/workspace/kora_dashboard/index.html`
  (dedup) - **`/root/psvibe_api_server/app.py`:**
  (dedup) - **`/root/psvibe_api_server/patch_routes.py`:**

## [P3] Memory (2026-06-18)

### Heartbeat Checks (14:37 MMT)
- Health monitor: overall 53.5 (false positives on path mismatches for AGENTS.md/SOUL.md, VPS unreachable)
- Heartbeat routine: 12 tasks OK, 0 pending, 0 stuck
- Stale notifier: 2 old yyo-personal-wallet alerts (Jun 11, Jun 14) — service likely restored
- Check alerts: ✅ All services healthy
- Dead letter queue: empty
- Stale locks: 0 cleaned
- Memory index rebuilt: 1339 topics
- Knowledge graph rebuilt: 54 nodes, 1419 edges
- Git backup: committed 7 files
- Digest: 2026-06-18-digest.md (2 sections)
- Memory pruner: nothing to prune

### Cancel Confirmed Booking Fix + Display Data Fix (16:46-16:56 UTC / 23:16-23:26 MMT)

### Bug 1: Cancel မရတာ
- **Root Cause:** `PATCH /api/bookings/{id}/status` (app.py L1400) - `WHERE status='pending'` hardcoded.
- Confirmed bookings ကို cancel လုပ်ချင်ရင် row affected=0 → "Booking already processed" 409 error.
- **Fix:** Cancel → `WHERE status IN ('pending','confirmed','pending_check_in')`.
- **Test:** #539, #513 ✅ cancel, double-cancel → 409 ✅, all restored ✅

### Bug 2: Cancel လုပ်ရင် Data "?" ပဲပြတာ
- **Root Cause:** `_do_cancel_booking()` (booking_flow.py) က PATCH response (`{booking_id, status}` only) ကို display + customer notification အတွက်သုံး → fields အားလုံး ? ဖြစ်.
- **Fix:** Cancel မလုပ်ခင် GET `/api/bookings/{id}` နဲ့ booking data အပြည့် pre-fetch လုပ်။ Staff display + customer notification နှစ်ခုလုံး pre-fetched data သုံး.
- **Files:**
- `/root/psvibe_api_server/app.py` (L1397-1404)
- `/root/psvibe-sales-bot/bot/handlers/booking_flow.py` (L492-572)

### Broadcast System Fix + Customer Bot Broadcast (17:22 UTC / 23:52 MMT)
- **Request:** Customer Bot ကနေ bot user အားလုံးကို broadcast ပို့လို့ရမလား
- **Found:** Sale Bot မှာ `/broadcast` ရှိပြီးသားဒါပေမယ့် bug 3 ခုကြောင့် အလုပ်မလုပ်:
- 1. API endpoint `bookings/broadcast-targets` က `member_id` ပြန်နေ (bot က `telegram_ids` ရှာ)
- 2. Route order — broadcast-targets က `{booking_id}` catch-all အောက်မှာ → 422
- 3. Customer Bot မှာ broadcast command မရှိ
- **Fixes:**
- 1. API endpoint: `DISTINCT telegram_chat_id WHERE telegram_chat_id IS NOT NULL AND != ''`
- 2. Route order: broadcast-targets ကို `{booking_id}` အရှေ့ကိုရွှေ့ (app.py L1440)
- 3. Customer Bot `/admin_broadcast` အသစ် (`customer_bot/broadcast.py`)
- 4. `ADMIN_USER_IDS=6296803251` secrets.env ထဲထည့်
- **Test:** API returns 44 targets ✅, Boss (6296803251) included ✅
- **Files:**
- `/root/psvibe_api_server/app.py` (L1440-1453)
- `/root/psvibe_api_server/patch_routes.py` (removed duplicate)
- `/root/psvibe-sales-bot/customer_bot/broadcast.py` (new)
- `/root/psvibe-sales-bot/customer_bot/main.py` (register handler)
- `/etc/psvibe/secrets.env` (ADMIN_USER_IDS)

# Archived Memory Entries
*Archived: 2026-06-28 17:33 UTC*

(dedup) - See `memory/2026-06-27.md` for full details
  (dedup) - **#37: JS Date(YYYY-MM-DDTHH:MM:SS) is LOCAL time** — without Z/timezone suffix, interpreted in browser timezone. Always append Z for UTC DB timestamps.
  (dedup) - **#38: Server-side filter > client-side** — for time-based filtering, MySQL NOW() - INTERVAL is more reliable than browser JS Date parsing.

# Archived Memory Entries
*Archived: 2026-06-29 18:34 UTC*

(dedup) - Buy#1: 10,000B @ 125.00 + 300 chg = 125.03/B (first buy)
  (dedup) - Buy#2: 20,000B @ 122.00 + 0 chg = 122.00/B (second buy)
  (dedup) - **`/root/psvibe-sales-bot/customer_bot/handlers.py`**:
  (dedup) - **`/root/psvibe-sales-bot/scripts/eod_report.py`**:
  (dedup) - New API endpoints in dashboard_routes.py (6 new routes)
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
  (dedup) - **Status:** ✅ Fixed, Boss confirmed booking is working
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
  (dedup) - 1. **FastAPI response_model silently strips undeclared fields** — always audit response models against actual return shapes
  (dedup) - 2. **`bool(0) == False`** — `"x if x else default"` pattern breaks on `0`; use `"x if x is not None else default"` instead
  (dedup) - 3. **`async def` + missing `await`** — coroutine objects silently pass type checks at runtime, cause confusing failures. Always use proper type hints to catch this.
  (dedup) - 4. **Double fail masking** — Both API (MySQL) and GSheet fallback were broken simultaneously → masked the true root cause. Monitor both paths independently.
  (dedup) - `psvibe_customer_bot` — ✅ active
  (dedup) - `/root/psvibe_api_server/models.py` — `error: Optional[str]` added to GenericResponse
  (dedup) - `/root/psvibe-sales-bot/bot/__init__.py` — `next_write_row` title lookup fix
  (dedup) - `/root/psvibe-sales-bot/bot/handlers/sales.py` — coupon field names, `_disc` fix, console normalization, booking `await`, `_notify_customer` import
  (dedup) - **All critical path bugs fixed:**
  (dedup) - ✅ Console normalization (spaces in console IDs)
  (dedup) - ✅ Auto-confirm for staff bookings
  (dedup) - ✅ Error messages now visible from API
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/booking.py`
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
  (dedup) - **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py` or similar
  (dedup) - **Status:** ✅ Done (per Kora's claim; need Boss to verify)
  (dedup) - 1. **FastAPI response_model silently strips undeclared fields** — always audit response models against actual return shapes
  (dedup) - 2. **`bool(0) == False`** — `"x if x else default"` pattern breaks on `0`; use `"x if x is not None else default"` instead
  (dedup) - 4. **Double fail masking** — Both API (MySQL) and GSheet fallback broken simultaneously → masked the true root cause
  (dedup) - 5. **Date format inconsistency between bot and API** — Bot sends locale-dependent format; always normalize to YYYY-MM-DD at the API boundary
  (dedup) - `psvibe-sale-bot` — ✅ active
  (dedup) - `psvibe_customer_bot` — ✅ active
  (dedup) - ✅ Daily Sale recording to API/MySQL
  (dedup) - ✅ Auto-confirm for staff bookings
  (dedup) - const { execSync } = require('child_process');
  (dedup) - const out = execSync(`ssh -i /home/node/.openclaw/workspace/.ssh/id_rsa -o StrictHostKeyChecking=no root@5.223.81.16 "grep -n 'def.*pnl\\|def.*profit_loss\\|financial/pnl' /root/psvibe_api_server/dashboard_routes.py 2>/dev/null"`, { timeout: 15000 });
  (dedup) - **4/41 empty** (all unreleased: Basketball 2026, Expedition 33, FIFA 2026, Little Nightmare 3)
  (dedup) - Auto-resolve: if `member_id` is provided but `phone` isn't → lookup `member_wallets` by member_id
  (dedup) - **Bot restarted:** psvibe-sale-bot ✅
  (dedup) - `/root/psvibe_api_server/app.py`
  (dedup) - `/root/.openclaw/workspace/kora_dashboard/index.html`
  (dedup) - **`/root/psvibe_api_server/app.py`:**
  (dedup) - **`/root/psvibe_api_server/patch_routes.py`:**

## [P3] Memory (2026-06-18)

### Heartbeat Checks (14:37 MMT)
- Health monitor: overall 53.5 (false positives on path mismatches for AGENTS.md/SOUL.md, VPS unreachable)
- Heartbeat routine: 12 tasks OK, 0 pending, 0 stuck
- Stale notifier: 2 old yyo-personal-wallet alerts (Jun 11, Jun 14) — service likely restored
- Check alerts: ✅ All services healthy
- Dead letter queue: empty
- Stale locks: 0 cleaned
- Memory index rebuilt: 1339 topics
- Knowledge graph rebuilt: 54 nodes, 1419 edges
- Git backup: committed 7 files
- Digest: 2026-06-18-digest.md (2 sections)
- Memory pruner: nothing to prune

### Cancel Confirmed Booking Fix + Display Data Fix (16:46-16:56 UTC / 23:16-23:26 MMT)

### Bug 1: Cancel မရတာ
- **Root Cause:** `PATCH /api/bookings/{id}/status` (app.py L1400) - `WHERE status='pending'` hardcoded.
- Confirmed bookings ကို cancel လုပ်ချင်ရင် row affected=0 → "Booking already processed" 409 error.
- **Fix:** Cancel → `WHERE status IN ('pending','confirmed','pending_check_in')`.
- **Test:** #539, #513 ✅ cancel, double-cancel → 409 ✅, all restored ✅

### Bug 2: Cancel လုပ်ရင် Data "?" ပဲပြတာ
- **Root Cause:** `_do_cancel_booking()` (booking_flow.py) က PATCH response (`{booking_id, status}` only) ကို display + customer notification အတွက်သုံး → fields အားလုံး ? ဖြစ်.
- **Fix:** Cancel မလုပ်ခင် GET `/api/bookings/{id}` နဲ့ booking data အပြည့် pre-fetch လုပ်။ Staff display + customer notification နှစ်ခုလုံး pre-fetched data သုံး.
- **Files:**
- `/root/psvibe_api_server/app.py` (L1397-1404)
- `/root/psvibe-sales-bot/bot/handlers/booking_flow.py` (L492-572)

### Broadcast System Fix + Customer Bot Broadcast (17:22 UTC / 23:52 MMT)
- **Request:** Customer Bot ကနေ bot user အားလုံးကို broadcast ပို့လို့ရမလား
- **Found:** Sale Bot မှာ `/broadcast` ရှိပြီးသားဒါပေမယ့် bug 3 ခုကြောင့် အလုပ်မလုပ်:
- 1. API endpoint `bookings/broadcast-targets` က `member_id` ပြန်နေ (bot က `telegram_ids` ရှာ)
- 2. Route order — broadcast-targets က `{booking_id}` catch-all အောက်မှာ → 422
- 3. Customer Bot မှာ broadcast command မရှိ
- **Fixes:**
- 1. API endpoint: `DISTINCT telegram_chat_id WHERE telegram_chat_id IS NOT NULL AND != ''`
- 2. Route order: broadcast-targets ကို `{booking_id}` အရှေ့ကိုရွှေ့ (app.py L1440)
- 3. Customer Bot `/admin_broadcast` အသစ် (`customer_bot/broadcast.py`)
- 4. `ADMIN_USER_IDS=6296803251` secrets.env ထဲထည့်
- **Test:** API returns 44 targets ✅, Boss (6296803251) included ✅
- **Files:**
- `/root/psvibe_api_server/app.py` (L1440-1453)
- `/root/psvibe_api_server/patch_routes.py` (removed duplicate)
- `/root/psvibe-sales-bot/customer_bot/broadcast.py` (new)
- `/root/psvibe-sales-bot/customer_bot/main.py` (register handler)
- `/etc/psvibe/secrets.env` (ADMIN_USER_IDS)
  (dedup) - Mgmt Fee = Net Profit × 10% → Aung Chan Myint
  (dedup) - if (a.status !== 'Active' && b.status === 'Active') return 1;
  (dedup) - **#28: Never edit minified Vue build output directly** — Always edit the source `.vue` files and rebuild. Single-character name conflicts can break the entire component. The project is at `/root/psvibe-dashboard/`.
  (dedup) - **#30: JS object key sorting trap** — String keys that look like integers (e.g., "848") are sorted numerically by V8, not by insertion order. Using `.reverse()` on `Object.values()` doesn't reverse insertion order when keys are numeric strings.
  (dedup) - Built: `cd /root/psvibe-dashboard && npx vite build`
  (dedup) - **#32: `window` object not available in Vue `<template>`** — Must use computed properties or method-returned style objects instead of inline `window.innerWidth` references.
  (dedup) - `/root/psvibe-dashboard/src/components/AppLayout.vue` — Reconciliation sidebar item added
  (dedup) - `/root/psvibe-dashboard/src/router/index.ts` — Reconciliation route added
  (dedup) ### Payment Method Parsing Bug (CRITICAL)
  (dedup) - Status badge: 🟢 Open / ⚫ Closed / 🟡 Not Opened
  (dedup) ### API: `GET /api/dashboard/reconciliation?date=YYYY-MM-DD`
  (dedup) - **Orphan filter:** Excludes food-only sales (notes without "Mins:")
  (dedup) - `staffOnlyPaths` in AppLayout.vue: added `/till`, `/reconciliation`, `/members`
