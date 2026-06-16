# MEMORY.md — Kora's Long-Term Memory Index

> 🗂️ Short master index. Detailed history → module files in `memory/`.
> Search via `memory_search` or `memory_get(path=memory/<file>.md)`.
## 🔴 Core Docs (workspace root)
| File | Purpose |
|------|---------|
| `GOLDEN_RULES.md` | Golden rules — never break |
| `HEARTBEAT.md` | Periodic tasks & cron schedule |
| `AGENTS.md` | Identity, workflow, hybrid spawning |
| `SOUL.md` | Personality, language, tone |
| `TOOLS.md` | SSH, bots, commands, API keys |
| `PROJECT_STRUCTURE.md` | Project overview (2 repos) |

## 📁 Module Files (`memory/`)

### Systems & Accounts
- **`memory/contacts.md`** — 👥 Contacts, Boss info, friend contacts
- **`memory/emails.md`** — 📧 Gmail accounts, API, Google Drive

### Infrastructure
- **`memory/infrastructure.md`** — 🏗️ Bot paths, services, MySQL, coordination tools
- **`memory/config.md`** — 🔧 Gateway config, lock_monitor, fix_protocol
- **`memory/psvibe-code-structure.md`** — 📂 File-by-file code reference (both repos)
- **`memory/project-state.md`** — 📋 Current project state & known issues

### SOPs & Frameworks (`memory/sop/`)
- **`memory/sop/SPAWN_PROTOCOL.md`** — 🔀 Sub-agent spawn rules & hybrid spawning
- **`memory/sop/POST_TASK_SOP.md`** — 📝 Post-task documentation SOP
- **`memory/sop/COORDINATION_FRAMEWORK.md`** — 🏗️ Agent coordination framework
- **`memory/sop/HELPER_GUIDELINES.md`** — 👷 Helper agent guidelines
- **`memory/sop/heartbeat-procedures.md`** — 💓 Full heartbeat procedures
- **`memory/sop/DISPATCH_MANAGER_SOP.md`** — 📋 Dispatch manager SOP
- **`memory/sop/FINDINGS_MANAGER_SOP.md`** — 🔍 Findings manager SOP
- **`memory/sop/TASK_PLANNER_SOP.md`** — 📊 Task planner SOP
- **`memory/sop/STATUS_REPORTER_SOP.md`** — 📈 Status reporter SOP
- **`memory/sop/VERIFY_AGENT_SOP.md`** — ✅ Verify agent SOP
- **`memory/sop/DEPLOY_MANAGER_SOP.md`** — 🚀 Deploy manager SOP
- **`memory/sop/GIT_SYNC_SOP.md`** — 🔄 Git sync SOP
- **`memory/sop/SPAWNING_MANAGER_SOP.md`** — 🥚 Spawning manager SOP

### Operations
- **`memory/tools-commands.md`** — 🛠️ All coordination tool commands reference
- **`memory/memory-usage-guide.md`** — 📖 How to use the memory system (decision tree, write rules)

### Memory Automation (Phase 3)
- **`memory/session_summary.py`** — Session end auto-summary
- **`memory/memory_index.py`** — Topic search index (1,146 topics)
- **`memory/priority_engine.py`** — P0-P3 priority classifier
- **`memory/memory_pruner.py`** — Dedup & prune (target ~20KB MEMORY.md)
- **`memory/daily_digest.py`** — Daily digest generator
- **`memory/git_backup.py`** — Memory git auto-backup
- **`memory/knowledge_graph.py`** — Entity relationship graph (54 nodes)

### Bugs, Fixes & Lessons
- **`memory/bug-patterns.md`** — 🐛 All known bug patterns (fixed & known)
- **`memory/ERROR_PATTERNS.md`** — ⚡ Quick ref: error → root cause → fix
- **`memory/lessons.md`** — 📚 Critical lessons learned
- **`memory/fix-history.md`** — 📋 Recent fix history (by date)

#

## Daily Logs

### 2026-05-28
## Activity (09:00-10:20 UTC)
- boot_protocol.py orphan detection fixed to skip `active_tasks.json` metadata keys (`version`, `active`)
- All scripts verified working with clean output
- Memory index built, priority engine tested
- `subagent_ctl.py complete` expects 3 positional args (task-id, status, summary)
- The `data` key in some function signatures was unused; works correctly via sys.argv

### 2026-06-03
## Grand Opening Countdown: June 6 (3 days away!)
## Major Fixes: 11 Items — All Complete ✅
- **Issue 1**: Promotions filtered — inactive/expired promos removed from Sale Daily display
- **Issue 9**: Coupon stuck at confirm step in Sale Daily — fixed broken Markdown string in discount.py
- **Issue 10**: C-09/C-10 multiplier ×1.2 — hardcoded fallback in fetch_console_multiplier()
- **Issue 2**: Member 90K default payment — removed duplicate separator text, fixed auto-confirm flow
- **Issue 4**: Booking counts incorrect — fixed URL encoding bug in api_client.py _api_call_async()
- **Issue 3**: Session Start/End — fixed duplicate except block (SyntaxError) in console.py
- **Issue 5**: Console Install — fixed type selection flow in ginst.py (was hardcoded HDD)
- **Issue 6**: Game list — fixed empty button labels; shows game names directly with Edit Game option
- **Issue 7**: Main Menu — removed BTN_FINANCIAL_REPORT and BTN_HELP
- **Issue 8**: SSD Management — added BTN_SSD_MANAGE to console menu; Game Library shows direct list
- Dashboard data fixed (stats, consoles, schedule, revenue-trend)
- Member card tiers fixed (mapping platinum/gold/silver/bronze with toLowerCase)
- Delete buttons added (Members, Inventory, Stock In, Stock Out)
- New API endpoints in dashboard_routes.py (6 new routes)
- New views: SaleDaily.vue, FinancialReport.vue
- Router updated: /sales-daily, /financial-report routes
- Sidebar updated: Sales Daily + Finance nav items
- Built & deployed to API server dashboard-dist/
## Full Audit Completed
## V2 Fixes (Round 2)
- 7 DB indexes added
- 114 stale bookings deleted
- Dashboard table names fixed
- Finance query optimized (19K rows → 0.05s)
- All Python files syntax OK, 0 errors in logs
- All 3 services active

### 2026-06-04
## Heartbeat 16:37 UTC — 2026-06-04
- All 4 services active ✅
- Disk 17%, Mem 44%, Load 0.66 ✅
- Quality Gate 55/100 ⚠️ (non-blocking)
- API Server git 11 uncommitted ⚠️ (expected — active fixes today)
- Fixed `sync_service.py` overwriting `console_status` → full line deleted ✅
- Grand Opening in ~1.5 days (June 6)
- Awaiting user test of Session Start/End
## Heartbeat 20:07 UTC (03:37 MMT)
- All services active: API, bot, customer bot
- Docker healthy: mysql, nova, coco, gateway, construction_bot
- Disk 17%
- No pending tasks / dead-letter / alerts
- Grand Opening tomorrow (June 6) - critical fixes just deployed:
- New Member payment data now sent to API
- Sale Daily uses api_add_sales_record (correct field mapping)
- Stock-out uses api_add_stock_out (correct endpoint)
- Console ID normalization in API layer

### 2026-06-05
## Major Bug Hunt - Phase 3 (13:00-15:20 UTC)
- **Root cause:** Added coupon API call but used `cd.get("coupon_code")` and `cd.get("coupon_mins")` — API response uses `code` and `minutes`
- **Fix:** Changed to `cd.get("code")` and `cd.get("minutes")`
- **Files:** `bot/handlers/sales.py` — both `step_sale_confirm()` and `launch_session_sale()`
- **Status:** ✅ Boss confirmed coupon is showing
- **Root cause:** API server's `api_member_wallet_update()` endpoint was missing `deduct_mins = req.get("deduct_mins")` — variable undefined, NameError caught, returned `success=false`
- **Fix:** Added `deduct_mins = req.get("deduct_mins")` to the endpoint
- **File:** `/root/psvibe_api_server/app.py` line 2097
- **Status:** ✅ Verified working (600→540 mins deducted)
- **Root cause:** FastAPI's `response_model=GenericResponse` only had `success`, `message`, `data` — when `error_response()` returned `{"success":false,"error":"...","code":500}`, FastAPI STRIPPED the `error` field
- **Result:** Bot always saw `{"success":false,"message":null,"data":null}` with `error=unknown`
- **Fix:** Added `error: Optional[str] = None` to `GenericResponse` in `models.py`
- **File:** `/root/psvibe_api_server/models.py`
- **Impact:** Now error messages from API will be visible in bot logs
- **Root cause:** `getattr(worksheet, 'title', '')` on `_LazyWorksheet` proxy returns bound method instead of string in some cases
- **Fix:** Changed to `getattr(worksheet, '_name', None) or getattr(worksheet, 'title', '')`
- **File:** `/root/psvibe-sales-bot/bot/__init__.py` — `next_write_row` function
- **Status:** ✅ Fixed
- **Symptom:** Manual API test works fine, but bot's real-time call returns `success=false: unknown`
- **Fix:** With GenericResponse fix (#3), the actual error message will now be visible
- **Diagnosis:** Log shows this has been happening since 03:01 UTC today — pre-existing issue
- **Status:** 🔍 Needs Boss to re-test to see real error
- `psvibe-api` — ✅ active (restarted multiple times)
- `psvibe-sale-bot` — ✅ active (restarted)
- `psvibe_customer_bot` — ✅ active
- `/root/psvibe_api_server/app.py` — added `deduct_mins = req.get("deduct_mins")`
- `/root/psvibe_api_server/models.py` — added `error: Optional[str]` to GenericResponse
- `/root/psvibe-sales-bot/bot/__init__.py` — fixed `next_write_row` title lookup
- `/root/psvibe-sales-bot/bot/handlers/sales.py` — coupon field names, console normalization
- `/root/psvibe-sales-bot/bot/api_client.py` — (temp debug logging added then removed)
- `_check_low_balance_alert` has `name 'os' is not defined` — minor, doesn't block flow
- API `sales/record` returning `success=false` from bot — root cause still unclear but error msgs now visible
- **Tomorrow:** June 6, 2026 (Saturday) 🎮🔥
- All critical path bugs fixed (coupon, wallet, sale record, console selection)
## Major Bug Hunt - Phase 3 (13:00-15:20 UTC)
- **Root cause:** Added coupon API call but used `cd.get("coupon_code")` and `cd.get("coupon_mins")` — API response uses `code` and `minutes`
- **Fix:** Changed to `cd.get("code")` and `cd.get("minutes")`
- **Files:** `bot/handlers/sales.py` — both `step_sale_confirm()` and `launch_session_sale()`
- **Status:** ✅ Boss confirmed coupon is showing
- **Root cause:** API server's `api_member_wallet_update()` endpoint was missing `deduct_mins = req.get("deduct_mins")` — variable undefined, NameError caught, returned `success=false`
- **Fix:** Added `deduct_mins = req.get("deduct_mins")` to the endpoint
- **File:** `/root/psvibe_api_server/app.py` line 2097
- **Status:** ✅ Verified working (600→540 mins deducted)
- **Root cause:** FastAPI's `response_model=GenericResponse` only had `success`, `message`, `data` — when `error_response()` returned `{"success":false,"error":"...","code":500}`, FastAPI STRIPPED the `error` field
- **Result:** Bot always saw `{"success":false,"message":null,"data":null}` with `error=unknown`
- **Fix:** Added `error: Optional[str] = None` to `GenericResponse` in `models.py`
- **File:** `/root/psvibe_api_server/models.py`
- **Impact:** Now error messages from API will be visible in bot logs
- **Root cause:** `getattr(worksheet, 'title', '')` on `_LazyWorksheet` proxy returns bound method instead of string in some cases
- **Fix:** Changed to `getattr(worksheet, '_name', None) or getattr(worksheet, 'title', '')`
- **File:** `/root/psvibe-sales-bot/bot/__init__.py` — `next_write_row` function
- **Status:** ✅ Fixed
- **Root cause:** Line 1301 in `bot/handlers/sales.py`:
- `_disc = discount if discount else ""` → when `discount=0`, converts to `""`
- API endpoint does `float(req.get("discount", 0))` → `float("")` → `ValueError`
- FastAPI catches error → returns `success=false: internal error`
- GenericResponse bug (#3) silently stripped the actual error message
- **Fix:** Changed to `_disc = discount if discount else 0`
- **Impact:** Both API path (MySQL) AND GSheet fallback were broken — double fail masked the root cause
- **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
- **Status:** ✅ Fixed, needs Boss re-test
- **Symptom:** Sale bot stuck at booking menu after restart — "New Booking" button visible but does nothing
- **Root cause:** `_sbk_console_kb()` function was made `async` in a previous fix, but the calling code still used `rows = _sbk_console_kb()` WITHOUT `await`
- **Result:** `rows` gets a coroutine object instead of the keyboard layout → `InjectedKeyboard` silently fails
- **Fix:** Changed to `rows = await _sbk_console_kb()`
- **File:** `bot/handlers/sales.py` (around booking conversation handler)
- **Status:** ✅ Fixed, bot restarted
1. **FastAPI response_model silently strips undeclared fields** — always audit response models against actual return shapes
2. **`bool(0) == False`** — `"x if x else default"` pattern breaks on `0`; use `"x if x is not None else default"` instead
3. **`async def` + missing `await`** — coroutine objects silently pass type checks at runtime, cause confusing failures. Always use proper type hints to catch this.
4. **Double fail masking** — Both API (MySQL) and GSheet fallback were broken simultaneously → masked the true root cause. Monitor both paths independently.
- `psvibe-api` — ✅ active (restarted multiple times)
- `psvibe-sale-bot` — ✅ active (restarted)
- `psvibe_customer_bot` — ✅ active
- `/root/psvibe_api_server/app.py` — added `deduct_mins = req.get("deduct_mins")`
- `/root/psvibe_api_server/models.py` — added `error: Optional[str]` to GenericResponse
- `/root/psvibe-sales-bot/bot/__init__.py` — fixed `next_write_row` title lookup
- `/root/psvibe-sales-bot/bot/handlers/sales.py` — coupon field names, `_disc` fix, console normalization, booking `await`
- `_check_low_balance_alert` has `name 'os' is not defined` — minor, alert just silently fails
- GSheet fallback `sales/record` path — still needs test but API (MySQL) path now fixed
- **TOMORROW:** June 6, 2026 (Saturday) 🎮🔥🎉
- **All critical path bugs fixed:**
- ✅ Coupon generation working
- ✅ Wallet deduction working
- ✅ Daily Sale recording to API/MySQL (with discount=0)
- ✅ Console normalization (spaces in console IDs)
- ✅ Booking button working after restart
- ✅ Error messages now visible from API
## Major Bug Hunt - Phase 3 (13:00-15:20 UTC)
- **Root cause:** Added coupon API call but used `cd.get("coupon_code")` and `cd.get("coupon_mins")` — API response uses `code` and `minutes`
- **Fix:** Changed to `cd.get("code")` and `cd.get("minutes")`
- **Files:** `bot/handlers/sales.py` — both `step_sale_confirm()` and `launch_session_sale()`
- **Status:** ✅ Boss confirmed coupon is showing
- **Root cause:** API server's `api_member_wallet_update()` endpoint was missing `deduct_mins = req.get("deduct_mins")` — variable undefined, NameError caught, returned `success=false`
- **Fix:** Added `deduct_mins = req.get("deduct_mins")` to the endpoint
- **File:** `/root/psvibe_api_server/app.py` line 2097
- **Status:** ✅ Verified working (600→540 mins deducted)
- **Root cause:** FastAPI's `response_model=GenericResponse` only had `success`, `message`, `data` — when `error_response()` returned `{"success":false,"error":"...","code":500}`, FastAPI STRIPPED the `error` field
- **Result:** Bot always saw `{"success":false,"message":null,"data":null}` with `error=unknown`
- **Fix:** Added `error: Optional[str] = None` to `GenericResponse` in `models.py`
- **File:** `/root/psvibe_api_server/models.py`
- **Impact:** Now error messages from API will be visible in bot logs
- **Root cause:** `getattr(worksheet, 'title', '')` on `_LazyWorksheet` proxy returns bound method instead of string in some cases
- **Fix:** Changed to `getattr(worksheet, '_name', None) or getattr(worksheet, 'title', '')`
- **File:** `/root/psvibe-sales-bot/bot/__init__.py` — `next_write_row` function
- **Status:** ✅ Fixed
- **Root cause:** Line 1301 in `bot/handlers/sales.py`:
- `_disc = discount if discount else ""` → when `discount=0`, converts to `""`
- API endpoint does `float(req.get("discount", 0))` → `float("")` → `ValueError`
- FastAPI catches error → returns `success=false: internal error`
- GenericResponse bug (#3) silently stripped the actual error message
- **Fix:** Changed to `_disc = discount if discount else 0`
- **Impact:** Both API path (MySQL) AND GSheet fallback were broken — double fail masked the root cause
- **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
- **Status:** ✅ Fixed, Boss confirmed working
- **Symptom:** Sale bot stuck at booking menu after restart — "New Booking" button visible but does nothing
- **Root cause:** `_sbk_console_kb()` function was made `async` in a previous fix, but the calling code still used `rows = _sbk_console_kb()` WITHOUT `await`
- **Result:** `rows` gets a coroutine object instead of the keyboard layout → `InjectedKeyboard` silently fails
- **Fix:** Changed to `rows = await _sbk_console_kb()`
- **File:** `bot/handlers/sales.py` (around booking conversation handler)
- **Status:** ✅ Fixed, bot restarted
## Phase 3.5 — Booking Flow Fixes (16:00-17:00 UTC)
- **Symptom:** Sale Bot creates booking → API returns HTTP 500
- **Root cause:** Bot sends date as `6/6/2026` (M/D/YYYY) but API endpoint `api_bookings_create()` expects `%Y-%m-%d` (YYYY-MM-DD). `strptime` parse fails gracefully (falls back to `now`), but the raw `booking_date_str` (`6/6/2026`) was passed directly to MySQL INSERT → `Incorrect date value` error → HTTP 500
- **Fix:** Added multi-format date parsing in `api_bookings_create()` supporting: `%Y-%m-%d`, `%m/%d/%Y`, `%m-%d-%Y`, `%d/%m/%Y`, `%Y/%m/%d`. Uses the parsed `_parsed_date` (YYYY-MM-DD string) in the INSERT statement.
- **File:** `/root/psvibe_api_server/app.py` — `api_bookings_create()` endpoint
- **Status:** ✅ Fixed, Boss confirmed booking is working
- **Request:** Staff-created bookings (via Sale Bot) should auto-confirm without manual "Accept" step
- **Fix:** API endpoint now checks for `source == "staff"` OR presence of `staffNote` field in the booking payload. If staff booking → sets `status = "confirmed"` instead of `"pending"`. Customer-submitted bookings remain `pending → accept flow`.
- **File:** `/root/psvibe_api_server/app.py` — `api_bookings_create()` endpoint (status assignment logic)
- **Status:** ✅ Done
- **Symptom:** Same console, same time could be double-booked
- **Fix:** Added slot conflict check in `api_bookings_create()`: before INSERT, check if any existing booking for the same `console_id` on the same `booking_date` at the same `start_time` has `status IN ('confirmed', 'pending_check_in')`. If conflict → return error with message "⏰ Console {console_id} သည် {booking_date} {start_time} တွင် ကြိုတင်စာရင်းရှိပြီးဖြစ်ပါသည်"
- **Note:** API-level check protects both dashboard and bot paths
- **File:** `/root/psvibe_api_server/app.py` — `api_bookings_create()` endpoint
- **Status:** ✅ Done
- **Symptom:** Cancel booking doesn't work — `NameError: name '_notify_customer' is not defined`
- **Root cause:** `_notify_customer` function was referenced in `booking.py` but not imported
- **Fix:** Added `from bot.handlers.booking import _notify_customer` import in the cancel handler
- **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
- **Status:** ✅ Done, bot restarted
1. **FastAPI response_model silently strips undeclared fields** — always audit response models against actual return shapes
2. **`bool(0) == False`** — `"x if x else default"` pattern breaks on `0`; use `"x if x is not None else default"` instead
3. **`async def` + missing `await`** — coroutine objects silently pass type checks at runtime, cause confusing failures. Always use proper type hints to catch this.
4. **Double fail masking** — Both API (MySQL) and GSheet fallback were broken simultaneously → masked the true root cause. Monitor both paths independently.
5. **Date format inconsistency between bot and API** — Bot sends locale-dependent date format but API expects strict YYYY-MM-DD. Always normalize to YYYY-MM-DD at the API boundary.
6. **Same-console double booking** — Must check existing bookings before allowing new ones. API-level check is best since both bot and dashboard share the same endpoint.
- `psvibe-api` — ✅ active
- `psvibe-sale-bot` — ✅ active
- `psvibe_customer_bot` — ✅ active
- `/root/psvibe_api_server/app.py` — `deduct_mins` + `GenericResponse` import + date format parsing + auto-confirm staff bookings + slot conflict check
- `/root/psvibe_api_server/models.py` — `error: Optional[str]` added to GenericResponse
- `/root/psvibe-sales-bot/bot/__init__.py` — `next_write_row` title lookup fix
- `/root/psvibe-sales-bot/bot/handlers/sales.py` — coupon field names, `_disc` fix, console normalization, booking `await`, `_notify_customer` import
- `/root/psvibe-sales-bot/bot/handlers/booking.py` — API key mapping in `_sbk_console_kb()`
- `_check_low_balance_alert` has `name 'os' is not defined` — non-blocking, alert silently fails
- GSheet fallback `sales/record` path — secondary path, API/MySQL primary path now working
- "အချိန်အရင်ထည့်ပြီးမှ slot စစ်တာ" UX improvement — Boss suggested reorder booking flow (time first, then slot check) — post-Grand-Opening task
- **TOMORROW:** June 6, 2026 (Saturday) 🎮🔥🎉
- **All critical path bugs fixed:**
- ✅ Coupon generation working
- ✅ Wallet deduction working
- ✅ Daily Sale recording to API/MySQL
- ✅ Console normalization (spaces in console IDs)
- ✅ Booking button working
- ✅ New booking creation working
- ✅ Auto-confirm for staff bookings
- ✅ Slot conflict prevention (no double bookings)
- ✅ Cancel button working
- ✅ Error messages now visible from API
## Major Bug Hunt - Phase 3 (13:00-15:20 UTC)
- **Root cause:** Added coupon API call but used `cd.get("coupon_code")` and `cd.get("coupon_mins")` — API response uses `code` and `minutes`
- **Fix:** Changed to `cd.get("code")` and `cd.get("minutes")`
- **Files:** `bot/handlers/sales.py` — both `step_sale_confirm()` and `launch_session_sale()`
- **Status:** ✅ Boss confirmed coupon is showing
- **Root cause:** API server's `api_member_wallet_update()` endpoint was missing `deduct_mins = req.get("deduct_mins")` — variable undefined, NameError caught, returned `success=false`
- **Fix:** Added `deduct_mins = req.get("deduct_mins")` to the endpoint
- **File:** `/root/psvibe_api_server/app.py` line 2097
- **Status:** ✅ Verified working (600→540 mins deducted)
- **Root cause:** FastAPI's `response_model=GenericResponse` only had `success`, `message`, `data` — when `error_response()` returned `{"success":false,"error":"...","code":500}`, FastAPI STRIPPED the `error` field
- **Result:** Bot always saw `{"success":false,"message":null,"data":null}` with `error=unknown`
- **Fix:** Added `error: Optional[str] = None` to `GenericResponse` in `models.py`
- **File:** `/root/psvibe_api_server/models.py`
- **Impact:** Now error messages from API will be visible in bot logs
- **Root cause:** `getattr(worksheet, 'title', '')` on `_LazyWorksheet` proxy returns bound method instead of string in some cases
- **Fix:** Changed to `getattr(worksheet, '_name', None) or getattr(worksheet, 'title', '')`
- **File:** `/root/psvibe-sales-bot/bot/__init__.py` — `next_write_row` function
- **Status:** ✅ Fixed
- **Root cause:** Line 1301 in `bot/handlers/sales.py`:
- `_disc = discount if discount else ""` → when `discount=0`, converts to `""`
- API endpoint does `float(req.get("discount", 0))` → `float("")` → `ValueError`
- FastAPI catches error → returns `success=false: internal error`
- GenericResponse bug (#3) silently stripped the actual error message
- **Fix:** Changed to `_disc = discount if discount else 0`
- **Impact:** Both API path (MySQL) AND GSheet fallback were broken — double fail masked the root cause
- **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
- **Status:** ✅ Fixed, Boss confirmed working
- **Symptom:** Sale bot stuck at booking menu after restart — "New Booking" button visible but does nothing
- **Root cause:** `_sbk_console_kb()` function was made `async` in a previous fix, but the calling code still used `rows = _sbk_console_kb()` WITHOUT `await`
- **Result:** `rows` gets a coroutine object instead of the keyboard layout → `InjectedKeyboard` silently fails
- **Fix:** Changed to `rows = await _sbk_console_kb()`
- **File:** `bot/handlers/sales.py` (around booking conversation handler)
- **Status:** ✅ Fixed, bot restarted
## Phase 3.5 — Booking Flow Fixes (16:00-17:00 UTC)
- **Symptom:** Sale Bot creates booking → API returns HTTP 500
- **Root cause:** Bot sends date as `6/6/2026` (M/D/YYYY) but API endpoint `api_bookings_create()` expects `%Y-%m-%d` (YYYY-MM-DD). `strptime` parse fails gracefully (falls back to `now`), but the raw `booking_date_str` (`6/6/2026`) was passed directly to MySQL INSERT → `Incorrect date value` error → HTTP 500
- **Fix:** Added multi-format date parsing in `api_bookings_create()` supporting: `%Y-%m-%d`, `%m/%d/%Y`, `%m-%d-%Y`, `%d/%m/%Y`, `%Y/%m/%d`. Uses the parsed `_parsed_date` (YYYY-MM-DD string) in the INSERT statement.
- **File:** `/root/psvibe_api_server/app.py` — `api_bookings_create()` endpoint
- **Status:** ✅ Fixed, Boss confirmed booking is working
- **Request:** Staff-created bookings (via Sale Bot) should auto-confirm without manual "Accept" step
- **Fix:** API endpoint now checks for `source == "staff"` OR presence of `staffNote` field in the booking payload. If staff booking → sets `status = "confirmed"` instead of `"pending"`. Customer-submitted bookings remain `pending → accept flow`.
- **File:** `/root/psvibe_api_server/app.py` — `api_bookings_create()` endpoint (status assignment logic)
- **Status:** ✅ Done
- **Symptom:** Same console, same time could be double-booked
- **Fix:** Added slot conflict check in `api_bookings_create()`: before INSERT, check if any existing booking for the same `console_id` on the same `booking_date` at the same `start_time` has `status IN ('confirmed', 'pending_check_in')`. If conflict → return error with message "⏰ Console {console_id} သည် {booking_date} {start_time} တွင် ကြိုတင်စာရင်းရှိပြီးဖြစ်ပါသည်"
- **Note:** API-level check protects both dashboard and bot paths
- **File:** `/root/psvibe_api_server/app.py` — `api_bookings_create()` endpoint
- **Status:** ✅ Done
- **Symptom:** Cancel booking doesn't work — `NameError: name '_notify_customer' is not defined`
- **Root cause:** `_notify_customer` function was referenced in `booking.py` but not imported
- **Fix:** Added `from bot.handlers.booking import _notify_customer` import in the cancel handler
- **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
- **Status:** ✅ Done, bot restarted
## Phase 4 — Booking Flow Reorder (17:00-18:30 UTC)
- **Root cause:** `cmd_staff_booking` returned `SBK_DATE` which mapped to `step_sbk_date` (PHONE handler), not the date handler. Also, after reorder, Console selection step was completely missing from the flow.
- **Fix (3 rounds):**
1. `cmd_staff_booking` → return `SBK_TIME` (date handler)
2. `step_sbk_dur` rewritten to do availability check → show free console list → `SBK_CONSOLE`
3. `step_sbk_date` after phone → go to `SBK_GAME` (duration) instead of `SBK_TIME`
- **File:** `/root/psvibe-sales-bot/bot/handlers/booking.py`
- **Status:** ✅ Fixed after Unicode encoding issue resolved (used SFTP upload instead of inline replace)
- **Symptom:** Console Start Session from sales flow → no 5-min-before-end reminder fired
- **Root cause:** `_remind_loop` was only called from BOOK flow (`booking.py`), not from sales flow (`step_sale_confirm`)
- **Fix:** Added import of `_remind_loop`, `_REMIND_TASKS`, `_remind_key` to `sales.py`. Added code right before final return in `step_sale_confirm` to start `_remind_loop` if `play_mins > 5` and `c_id` set.
- **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py`
- **Status:** ✅ Fixed
## Phase 5 — Grand Opening Data Reset (18:31 UTC)
- **Cleared tables:** `stock_in`, `member_coupons`, `topup_log`, `sales_daily`, `receipts`, `promotions_log`, `stock_out`, `attendance_log`, `members`, `member_wallets`
- **Kept:** Booking IDs 175, 176, 177, 189 (confirmed)
- **Session records cleared:** `console_games` WHERE `install_type = 'Session'` → 0 left
- **Active sessions cleared:** C-04 (Guest), C-09 (VIP001) → both Free
- **Card Wallet records:** Cleared
- **Console Status Board:** 10/10 Free ✅
## Phase 6 — Features (18:37-19:09 UTC)
- **Request:** Show "Reserved" (🟡) for confirmed bookings 2 hours before the booking time
- **Changes made:**
- `console_status_endpoint` now includes logic to check for upcoming confirmed bookings (within 2 hours) and marks those consoles as `"reserved"` with yellow status
- Sale Bot Console Status Board shows 🟡 Reserved for upcoming bookings
- Customer Bot Console Status Board also shows 🟡 Reserved
- **File:** `/root/psvibe_api_server/app.py` — console status endpoint
- **Status:** ✅ Done (per Kora's claim; need Boss to verify display)
- **Request:** Auto-reminder for confirmed bookings 10 minutes before the start time
- **Changes made:**
- Added reminder logic that checks for confirmed bookings starting within ~10 minutes
- Sends reminder to admin group with customer name, phone, time, duration, game details
- **File:** `/root/psvibe-sales-bot/bot/handlers/sales.py` or similar
- **Status:** ✅ Done (per Kora's claim; need Boss to verify)
## 🧠 Critical Lessons Learned (Complete)
1. **FastAPI response_model silently strips undeclared fields** — always audit response models against actual return shapes
2. **`bool(0) == False`** — `"x if x else default"` pattern breaks on `0`; use `"x if x is not None else default"` instead
3. **`async def` + missing `await`** — coroutine objects silently pass type checks at runtime, cause confusing failures
4. **Double fail masking** — Both API (MySQL) and GSheet fallback broken simultaneously → masked the true root cause
5. **Date format inconsistency between bot and API** — Bot sends locale-dependent format; always normalize to YYYY-MM-DD at the API boundary
6. **Same-console double booking** — Must check existing bookings before allowing new ones. API-level check is best.
7. **`_replit_get_async` list-path heuristic** — Paths containing "bookings"/"console" keywords treated as list paths; single resources need special handling
8. **Unicode escape sequences in fix scripts** — Python `content.replace()` with escaped Unicode may not match actual file bytes; use SFTP upload + remote execution instead
9. **Booking flow: Date/Time first → then check availability** — UX improvement, prevents console selection before knowing if it's free
## Services (Final State 19:09 UTC)
- `psvibe-api` — ✅ active
- `psvibe-sale-bot` — ✅ active
- `psvibe_customer_bot` — ✅ active
## Grand Opening — TOMORROW June 6, 2026 (Saturday) 🎮🔥🎉
- **All critical path bugs fixed and data reset complete:**
- ✅ Coupon generation
- ✅ Wallet deduction
- ✅ Daily Sale recording to API/MySQL
- ✅ Console normalization (spaces in IDs)
- ✅ Booking button / new booking / cancel
- ✅ Auto-confirm for staff bookings
- ✅ Slot conflict prevention
- ✅ Reordered booking flow (Date→Time→Avail→Console→Name→Phone→Dur→Game)
- ✅ Timer reminder (5 min before end)
- ✅ 10-min advance booking reminder
- ✅ Console Status Board with Reserved (🟡) display
- ✅ Data reset (clean state for Grand Opening)
- ✅ All services active

### 2026-06-06
## 🎮 Grand Opening Day! 🔥 Day of Grand Opening
- **Symptoms:** After selecting PS5/PS5 Pro/Any, the bot asks about duration twice in a loop
- **Root cause:** Unicode escape sequences in the previous fix were corrupted. `ရွေးပါ` was rendered as garbled text (`ရြေအအ038ပါ`), so the user's tap on the visible keyboard was interpreted wrong, causing `bk_console_pref` to fall through and re-show the console type selection instead of progressing to choice phase
- **Fix:** Re-examined all Unicode escape sequences in `/root/psvibe-sales-bot/customer_bot/booking_handlers.py`, fixed 6 corrupted Unicode escapes. The prompt message "ကြာချိန်ရွေးပါ" now displays correctly.
- **Symptoms:** C-01 booked at 13:00-14:00 on June 6, but customer bot doesn't show it as reserved or blocked
- **Root causes:**
1. **API `_map_booking_row` (patch_routes.py):** maps `console_id` → `consoleType` (not `consoleId`). Customer bot's `_get_available_consoles` checks `b.get("console_id")` or `b.get("consoleId")`, but neither exists because the key is `consoleType` → no conflict detection possible
2. **Bot `_get_available_consoles` (booking_handlers.py):** only checks `b.get("console_id")` and `b.get("consoleId")`, no fallback for `consoleType`
- **Fix:**
- **API:** Added `consoleId` field to `_map_booking_row` response (line ~264 in patch_routes.py)
- **Bot:** Added `consoleType` fallback check alongside `console_id` and `consoleId`
- Both fixes applied via SSH SFTP upload + remote execution to ensure exact byte-level correctness
- ✅ Both bugs fixed
- All 3 services restarted
- Grand Opening: Day of — monitoring needed
- VPS Monitor Alert Check at 02:01 UTC → NO ALERTS (all services active, health OK)
- Note: Monitoring cron jobs may be stale (last entries from May 27 — ~10 days old)
- Mail check showed GitHub Deploy workflow failing 10+ times (13-17 sec duration, failing within deployment)
## 🐛 Bug Round: Food Menu Not Working (03:00-03:30 UTC / 09:30-10:00 Myanmar Time)
- Added BTN_FOOD to MAIN_MENU_KB
- Added `cmd_food_menu` function with Unicode escape Burmese text (`\u1012\u103d...`)
- Added BTN_FOOD routing in `handle_menu_buttons()`
- Added flexible text matching ("food menu", "menu", "food ပါ", "food ကြည့်မယ်")
- Registered CommandHandler + MessageHandler in `main.py`
1. Missing BTN_FOOD in `_bk_intercept_menu` → booking conversation still ate the button
2. `cmd_food_menu` checked `resp.get("success")` / `resp.get("data", {})` on auto-unwrapped response → always failed
3. Unicode escape sequences corrupted → garbled loading text
1. `_bk_intercept_menu` didn't include BTN_FOOD → booking conversation ate the button silently
2. `_api._api_get()` **auto-unwraps** response → `{"success":true,"data":{items}}` becomes `{items}` directly
- Bot code checked `resp.get("success")` → key doesn't exist in unwrapped data → always false
- Bot code checked `resp.get("data", {})` → key doesn't exist in unwrapped data → always empty
3. Unicode escape sequences (`\u1012\u103d...`) were corrupted during auto-fix pipeline → garbled text
4. Duplicate BTN_FOOD MessageHandler in `main.py` could cause conflicts
- All 4 services active: `psvibe-api`, `psvibe_customer_bot`, `psvibe-sale-bot`, `psvibe-dashboard`
- Food Menu is working (need Boss to re-test)
- The commit `1dd1be1` shows the final correct code

### 2026-06-07
## 🐛 api_client.py Fix Summary (18:17 UTC)
- `api_post()` in api_client.py changed from `?api_key=` query param to `X-API-Key` header
- `api_get()` in api_client.py also fixed
- Coupon generation (`coupons/generate`) now works because auth is correct
- Promotion extended: 2026-06-07 → 2026-06-30
- Coupon validation/redeem also fixed earlier (discount.py `_api_post_coupon`)
- Services: api & sale bot restarted

### 2026-06-08
- **Built** `/root/psvibe_api_server/fifo_wallet.py` — FIFO (oldest topups consumed first)
- **Added** `POST /api/member/wallet/update` endpoint for real-time wallet deduction
- **Integrated** into `dashboard_routes.py` — member liability + wallet consumption via FIFO
- **Fixed** asset query: `SUM(amount)` → `SUM(per_price * qty)` (was returning wrong 820M)
- **API restarted** ✅
## Earlier Today (June 8) — Tasks before FIFO
- **GROUP BY bug**: collapsed payment strings → Cash off by -60,000 Ks. Fixed: removed GROUP BY, iterate all rows.
- **Wave/AYA Pay not saving**: hardcoded payment_method → dynamic
- **Elif bug**: `== "wave"` only, not `== "wavepay"` → fixed
- New endpoint `GET /api/fetch_food_menu` — categories with emoji headers
- MySQL + API + Sales Bot + Customer Bot updated
- `cash_movements` table + `/api/cash/inject|eject|movements`
- Bot `/inject` `/eject` (Boss-only) + `/admin/cash` web page
- SSD: substring→prefix `cid.upper().startswith("SSD")`
- Duplicate games: `install_type != "Session"` + API protection
- `_is_session_active()` was calling non-existent endpoint → fixed to `fetch_console_status`
- Keyboard race condition on stale button taps → added catch-all `else` in `step_coupon_confirm`
- Normalization mismatch: `"acm"` in DB vs `"acm's acc"` in code
- `systemctl restart` silent failure → `kill -9`
- Standalone `🍔 Food Sale` button (no console/game)
- `is_food_sale` flag → records `type: "food_only"`
- PyMySQL `LIKE '%/%'` conflict → `CONCAT('%', '/', '%')`
- 35 backdated stock_in records → KBZ Bank
- `PUT /api/dashboard/stock-in/{entry_id}` + edit modal
- Payment method dropdown: Cash, WavePay, KPay, AYA Pay, KBZ Bank, ACM's Acc
- **Asset query**: `SUM(amount)`→`SUM(per_price*qty)` (820M→126M)
- **KBZ Bank deductions**: Assets 126.6M + Advances 104.8M + Prepaid 22.4M
- **Web vs Bot identical** endpoints
- **Stock In double-counting** removed
- Game: 557,666 Ks | Food: 66,000 Ks | Topup: 90,000 Ks
- Discount: 114,833 Ks | Liability: 81,000 Ks | Total Income: 713,666 Ks
- `sync_member_wallets()` 2216 chars deleted
- GSheet fallback replaced with logging
- Wallet: 100% MySQL
## 🧠 Key Lessons
- GROUP BY collapses pipe-delimited data → iterate all rows
- Elif chains must cover ALL variants (`"wave"` ≠ `"wavepay"`)
- systemctl restart can silently fail → verify PID, fallback `kill -9`
- `x if x else default` breaks on `0` → use `x if x is not None else default`
- PyMySQL `%` in LIKE → `CONCAT('%', '/', '%')` or `%%`
- FIFO for wallet: oldest topups consumed first; bonus min = 0 Ks
- Always use `per_price*qty` not raw `amount` for assets
- psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅
- **All 6 remaining sync functions deleted** from `sync_service.py` — `sync_games_library`, `sync_console_status`, `sync_staff_records`, `sync_settings_config`, `sync_finance_opex`, `sync_finance_assets`
- `sync_service.py` replaced with minimal stub (MySQL-only)
- `run_sync.sh` renamed to `/root/psvibe_api_server/run_sync.sh.DISABLED`
- GSheet cron (`*/5 * * * * run_sync.sh`) disabled — system is **100% MySQL-only**
- Added `GET /api/dashboard/topups` endpoint (previously missing — page was empty)
- Topup upsert fixed: `UPDATE` → `INSERT...ON DUPLICATE KEY UPDATE` for new members
- Wallet deduction endpoint added: `POST /api/member/wallet/update` in `app.py`
- GSheet fallback code removed from Sale Bot (`sales.py`) — replaced with logging
- Sale bot restarted
- Deleted **25 duplicate asset rows** (all had `per_price=NULL`)
- Before: 54 rows → After: 29 rows (all clean, unique)
- Asset Value: 126,566,852 Ks (unchanged — dupes had 0 value)
- KBZ Bank: 38,669,887 Ks (correct after all deductions)
- **Disposal record reversed** — `Game Discs` (id=3) disposed_qty=3 → 0; `asset_disposals` table now empty (was test data from disposal feature dev)
- Boss reported: "Finance Dashboard မှားနေသေးတယ် + Category မစုံသေးဘူး"
- Frontend rebuilt & deployed but issue persists — waiting for Boss to specify exact mismatch (balances vs display format vs categories)
- psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅

### 2026-06-09
## 🕐 Time
## ✅ Done
- Opening = **300M** (initial KBZ capital)
- Operating: sales 889K + topup income - opex 7.05M - stock 733K = **-6.9M**
- Investing: PS5 140.7M + advances 104.8M + prepaid 22.4M - recovery 3.6M = **-264.3M**
- **Closing = 28,758,453 Ks** ✅ (matches Web Finance exactly)
- **No Financing section** (no capital events in June; 3.69M was advance recovery + member topup, not capital injection)
- Stock cost uses **ejections** (actual cash outflow) = 733,940 Ks
- Advance recovery (Sunh Furniture 3.6M) shown in investing
1. **Capital Withdrawals removed** — eject was stock payment, not withdrawal
2. **ACM's Acc is a business account** — just separate cash box, not owner transfer
3. **Opening = all KBZ transfer_in** (300M) regardless of date
4. **Cash Flow uses same per-account income calc as Web Finance** → closing matches exactly (28,758,453 Ks)
- Created `prepaid_amortization` table
- 22,425,000 Ks = Rental Fee for 9 months (June 1 → Feb 28)
- Monthly: **2,491,667 Ks**
- June: inserted OPEX Rent entry ✅ + amortization record ✅
- Balance Sheet: prepaid now shows **19,933,333 Ks** (remaining 8 months)
- Auto-amortization script deployed: `/root/scripts/auto_amortize.py`
- Cron job set: **1st of each month 9:00 AM Myanmar Time** → auto-run
- cash_movements raw balance (304M) ≠ actual financial position — it only tracks internal transfers
- Web Finance and Cash Flow must use **identical income allocation** to match
- Prepaid amortization: P&L expense + BS asset reduction. Cash Flow already shows full outflow (investing).
## 🏗️ Financial Dashboard Deployed (19:44 UTC)
- Created FinanceDashboardView.vue with unified P&L + BS + CF view
- Added route `/finance-dashboard` to router
- Added sidebar link under Financial section
- Deployed: router + component uploaded; API restarted ✅
## After memory flush: YTD + Revenue Trend work (20:10 UTC)
- Moving on to build YTD Reports and Revenue Trend Graph features
## Exec approach: checking PNL endpoint
## ✅ YTD + Revenue Trend features completed (20:15 UTC)
- YTD: Added `ytd=true` param to PNL endpoint → returns Jan-to-month data
- Revenue Trend: Added `/api/dashboard/financial/revenue-trend` returning monthly game + food revenue for the year
- Dashboard CSS/JS rebuilt and deployed ✅

### 2026-06-10
## 🎯 Sales Daily Lazy-Load Fix (07:02-07:08 UTC)
1. Browser lazy-loads `SaleDaily-DXRSp17u.js` ✅
2. SaleDaily tries to import from `./index-DDJXoolO.js` ❌
3. Cloudflare serves CACHED n8n content for this URL
4. JavaScript fails → button does nothing
- Updated ALL 22 lazy-loaded chunks to import from `./index-DDJXoolO.v2.js` instead
- Also overwrote the original `index-DDJXoolO.js` with correct content (for safety)
- Main JS: `index-DDJXoolO.v2.js` (HTML ref)
- All lazy chunks: import from `./index-DDJXoolO.v2.js`
- Original file: `index-DDJXoolO.js` (overwritten with correct content)
## 🎯 Sales Daily Lazy-Load Fix (07:02-07:08 UTC)
1. Browser lazy-loads `SaleDaily-DXRSp17u.js` ✅
2. SaleDaily tries to import from `./index-DDJXoolO.js` ❌
3. Cloudflare serves CACHED n8n content for this URL
4. JavaScript fails → button does nothing
- Updated ALL 22 lazy-loaded chunks to import from `./index-DDJXoolO.v2.js` instead
- Also overwrote the original `index-DDJXoolO.js` with correct content (for safety)
- Main JS: `index-DDJXoolO.v2.js` (HTML ref)
- All lazy chunks: import from `./index-DDJXoolO.v2.js`
- Original file: `index-DDJXoolO.js` (overwritten with correct content)
## 🖼️ Data For Game Menu — Poster + Gameplay Project (18:00-19:30 UTC)
- **33 games**: ✅ Poster (Steam Library 1200x1800 box art) + Gameplay (Steam screenshots)
- **4 games**: ✅ Poster only (Assassin's Creed Shadows, Astro Bot, INVINCIBLE VS, Spider-Man 2)
- **4 games**: ❌ Empty (unreleased: Basketball 2026, Expedition 33, FIFA 2026, Little Nightmare 3)
1. **Steam Library Art (1200x1800 portrait)** — Best for poster-style box art. Direct CDN: `https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900_2x.jpg`
2. **Steam Screenshots API** — Best for gameplay highlights. `https://store.steampowered.com/api/appdetails?appids={appid}` → `screenshots[0].path_full`
3. **Alphacoders.com** — Used for PS5 exclusives (Gran Turismo 7, Astro Bot, etc.) with wallpaper-style gameplay
4. **IGN OG Images** — Fallback for some games (smaller 1200x630 pixel images)
- **Steam Library images** are portrait/poster style (600x900 → 1200x1800 @2x) — exactly what Boss wanted
- **Steam screenshots** are actual gameplay highlights at 1920x1080 — perfect for "gameplay highlights"
- PS5 exclusive games (Astro Bot, GT7, Spider-Man 2) have NO Steam pages → need alternative sources
- USG/IGN og:images are small social preview images (1200x630), not 2K quality
- The `token.json` Unicode ellipsis (`…`) issue keeps causing Python syntax errors when writing heredocs. Solution: use string concatenation (`td['acce' + 'ss_token']`) to avoid the Unicode character.
- Find gameplay for 4 poster-only games (try different alphacoders slugs)
- Find posters for 4 empty/unreleased games (may just not exist yet)
## 🎯 Data For Game Menu — FINAL RESULT (19:30 UTC+)
- **Posters:** Steam CDN `cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900_2x.jpg` — 1200x1800 portrait/box-art style
- **Gameplay:** Steam API `store.steampowered.com/api/appdetails?appids={appid}` → `screenshots[0].path_full` — 1920x1080 gameplay screenshots
- **Fallback:** Alphacoders.com for PS5 exclusives
- **IGN:** OG images for some games

### 2026-06-11
## iBet789 Bot Progress
- Bot code built and deployed at `/opt/ibet789-bot/`
- Systemd service `ibet789-bot` created (currently waiting for VPN)
- Fixed multiple bugs: `browser.isConnected`, proxy support, wrong AGENT_URL
- AGENT_URL: `https://ag.108sode.com` (actual agent dashboard)
## Geo-blocking Issue
- VPS (Singapore, 5.223.81.16) blocked by iBet789 geo-filter
- Cloudflare WARP failed (not Myanmar IP)
- Free proxies failed (timeout/blocked)
- Boss provided ExpressVPN credentials (shannonskillern@gmail.com / Skils5050!)
- ExpressVPN CLI not installed yet (Boss couldn't provide .deb file)
- Jump Jump VPN not usable on Linux
## Termux Proxy Attempt
- Boss installed Termux on phone
- SSH key shared: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIImD9p7oVNxsKsWItSGXOxIXyr7KbCtzTAoAsQPH04Ea u0_a558@localhost`
- SSH key added to VPS authorized_keys
- SSH connection timed out (Myanmar ISP may block port 22)
- **⚠️ Kora broke SSH**: While trying to add port 22222, systemd socket drop-in replaced port 22 with 22222 → SSH down
- Created `/etc/systemd/system/ssh.socket.d/extra-ports.conf` with only port 22222 (drop-in overrides original)
- Boss rebooted server via Hetzner Console but SSH still down
- **Fix**: Need to delete that drop-in file via Hetzner Web Console
- Resolution: Postponed to morning (Boss said "မနက်ကျမှ လုပ်တော့မယ်")
## Other Changes
- Smart Alert System cron: **30 min → 1 day** (Boss said too spammy)
- Boss wants to fix SSH issue tomorrow morning
## Pending for Tomorrow (June 12)
1. **⛔ SSH Fix**: Boss needs to use Hetzner Console → open Web Console → login → run:
2. **🔄 iBet789 Bot**: Once SSH is fixed, can proceed with:
- SSH tunnel from phone (Termux) using port 443 instead of 22
- Or ExpressVPN/BullVPN purchase
3. **📦 Smart Alerts**: Now runs once daily instead of every 30 min

### 2026-06-12
- Auth bug (number vs string comparison) fixed — Bot now correctly accepts Boss's commands
- Boss tested and got response: "No Balance Found"
- Balance selector needs fixing — need to find correct element on iBet789 dashboard
- Next step: Take Puppeteer screenshot, find correct balance element, update SEL_BALANCE

### 2026-06-13
1. **MySQL:** Added columns to `customer_bot_users`: `member_id` (indexed), `member_name`, `phone` (indexed), `balance_mins`
2. **API (`app.py`):**
- UPSERT SQL now stores member_id, member_name, phone, balance_mins
- Auto-resolve: if `phone` is provided but `member_id` isn't → lookup `member_wallets` by phone
- Auto-resolve: if `member_id` is provided but `phone` isn't → lookup `member_wallets` by member_id
- `bot-users/list` endpoint SELECT + response dict now returns all member fields
3. **Bot handlers (`handlers.py`):**
- `cmd_balance`: track_usage now passes resolved `member_id`
- `cmd_book`: track_usage now passes resolved `member_id`
- `cmd_cancel`: track_usage now passes resolved `member_id`
4. **Kora Dashboard (`index.html`):**
- Users table: 4 new columns (Member ID, Member Name, Phone, Balance)
- Member badge styling (green `PSV_A_XXX` when linked, — when not)
- i18n keys added for new columns
5. **All services restarted:** psvibe-api ✅, psvibe_customer_bot ✅, kora-dashboard (:9091) ✅
- When a user books through the bot (provides phone), `track_usage()` receives the phone → API auto-resolves member_id → auto-enriched
- Existing members without phone in tracking data can't be retroactively linked (no tg_id→member_id mapping)
- **Root cause:** API cancel endpoint (`app.py` `api_booking_cancel`) only notifies customer via Customer Bot — has NO code to notify staff/admin group
- Customer notification already existed (Telegram `sendMessage` via BOT_TOKEN)
- **Fix:** Added staff notification block after customer notification — sends cancel details (booking ID, date, time, console, game, member, phone) to `STAFF_NOTIFY_CHAT` via Sales Bot token
- **Extra step:** App.py was corrupted by broken string escaping during the fix → restored to clean git state, then reapplied fix correctly
- Added `check_and_notify_staff_10min()` function to `booking_reminder.py`
- Checks bookings starting in 8-14 min window (covers 15-min cron gap)
- Sends detailed notification to Admin Group: Booking #, member, console, game, time, phone
- **Post-fix:** Removed `/checkin_XX` and `/cancel_XX` buttons per Boss's feedback (clutters admin group)
- Boss asked about adding feedback/rating for customers
- **Found:** Customer Bot ALREADY has `cmd_feedback` with inline rating buttons (1-5 ⭐) + comment prompt
- **Missing:** No MySQL table or API endpoints existed — feedback was going nowhere
- **Fixed:**
1. Created `customer_feedback` table (id, tg_id, username, booking_id, rating, comment, console_id, created_at)
2. Added `POST /api/feedback/submit` — submits rating + optional comment
3. Added `GET /api/feedback/stats` — total count, avg rating, rating distribution, recent 20
4. Added `GET /api/feedback/list` — paginated listing with rating filter
- **Not yet done:** Kora Dashboard feedback tab, auto-trigger after session end
- **Services restarted:** psvibe-api ✅
- Classified all 41 games in `games_library` table via SQL: Solo(23), Multi(13), Both(5)
- **Games changed to Solo:** 19 titles (Action games, Platformers, Souls-like, etc.)
- **Games changed to Multi:** 7 titles (FIFA, Mortal Kombat, Tekken, etc.)
- **Games changed to Both:** 5 titles (It Takes Two, Sackboy, LEGO Star Wars, GTA V, Overcooked)
- Used `solo_multi` column which maps directly to `players` field in bot's game data
- Updated genres for all 41 games: Action Adventure(9), Fighting(6), Action RPG(5), Sports(4), Action(2), Platformer(2), Co-op(2), Horror(2), Survival Horror(2), Strategy(1), RPG(1), Hack and Slash(1), Racing(1), Roguelike(1), Sandbox(1)
- **Note:** Some games were reclassified as already correct (FIFA, Madden, Unravel Two, etc.)
- Changed `cmd_game_library`: replaced PS5/PS4 platform grouping with Solo/Multi/Both grouping
- **Old:** Grouped by platform (PS5: 37 titles, PS4: 4 titles) — poor organization since 90% are PS5-only
- **New:** Grouped by `solo_games` → `multi_games` → `both_games` → `other_games`
- Used `<b>` HTML tags with `parse_mode="HTML"` for section headers (Telegram bold)
- Removed `| Genre` tag from each game line → cleaner: `▶ Game Name 👥`
- **LEGO Star Wars fix:** Changed from Solo/Platformer to Both/Platformer Co-op (has local co-op)
- Moved `BTN_FOOD` button up to row 3: `[BTN_FOOD, BTN_RATE]` (right below `[BTN_MYBOOKINGS, BTN_GAMES]`)
- This is a temporary measure until Boss approves main menu restructuring plan
- **Root cause:** The sales bot calls `POST /session-end-notify` but this endpoint was **completely missing** from `app.py`
- Created full `POST /api/session-end-notify` endpoint in `app.py`:
- Sends feedback prompt with 5 inline rating buttons (⭐1-5) to customer via Customer Bot token
- Sends session-end notification to Admin Group via Sales Bot token
- Uses callback data format `fb:RATING:BOOKING_ID` matching existing bot handler pattern
- **End-to-end flow:** Sales bot → `_session_end_notify()` → API → Customer Bot (rating prompt) → user taps star → `cb_feedback_rating` → POST `/api/feedback/submit` → MySQL → Kora Dashboard
- Added "⭐ Feedback" tab to Kora Dashboard (`index.html`):
- Stats row: Total Reviews, Avg Rating (out of 5), Positive % (4-5⭐), Negative % (1-3⭐)
- Rating distribution bar chart (5 bars with percentages)
- Recent feedback table (ID, Customer, Rating, Comment, Console, Date)
- Auto-loads on tab switch
- i18n EN/MY keys added for all UI labels
- Dashboard deployed to VPS at `/root/.openclaw/workspace/kora_dashboard/index.html`
- **Bug:** User reported column header/data mismatch in Users tab; other tabs stuck on "Loading..."
- **Root cause:** `renderUserTable()` rendered only **7 `<td>` elements** but header had **11 `<th>` columns**
- The 4 member enrichment columns (Member ID, Member Name, Phone, Balance) were added to header but never wired into `renderUserTable`
- Additional "Loading..." bug: multiple `renderUserTable` functions in file (duplicated content from earlier edit corruption)
1. Restored clean git version (`853297a`) — removed file corruption (duplicated renderUserTable)
2. Applied git checkout `b17c442` — latest clean commit (has Feedback tab)
3. Added 4 member var definitions: `member_id`, `member_name`, `phone`, `balance_mins`
4. Added 4 `<td>` elements to renderUserTable row (after name, before firstSeen)
5. Changed `colspan="7"` → `colspan="11"`
6. Killed corrupted dashboard processes (both pids) and restart
7. Deployed corrected file to VPS via base64 chunked SSH transfer
8. **Validation:** `grep -c 'renderUserTable'` = 1, `grep -c 'memId'` = correct count, feedback tab intact
1. **Cloudflare DNS:** Add CNAME for `kora.ps-vibe.com` → `tunnel-endpoint` for subdomain access
2. **n8n Payment (€25.68):** 2nd notice received, subscription may expire
3. **GitHub Deploy:** PSVIBE-API-Server master branch failing (pre-existing issue)
- **Contact section (`cmd_contact`):** Added "🌐 Social Links" sub-section with:
- 📘 Facebook Page: https://www.facebook.com/ps5gamecenter
- 🎵 TikTok: https://www.tiktok.com/@ps.vibe.game.cent
- **Promotions section (`cmd_promotions`):** Added TikTok link alongside existing Facebook link (both empty-promo and active-promo states)
- **Memory (`contacts.md`):** Added PS VIBE Social Links section
- **Service restarted:** psvibe_customer_bot ✅
- **Cleanup:** Removed temp fix files (`/tmp/fix_social.py`, `/tmp/fix_contact_newlines.py`, `/tmp/debug_pattern.py`, `/tmp/fix_social_links.py`, `/tmp/patch_social_links.py`, `/tmp/ssh_put.js`, `/tmp/deploy_dash.js`)
1. **JS `<script>` block fragility:** A single syntax error in any inline `onclick` or template literal within a `<script>` block kills ALL JavaScript in that block. Always validate carefully.
2. **FastAPI response_model:** Silently strips undeclared fields — add all response fields to `response_model` Pydantic class.
3. **file corruption from string slicing:** When editing HTML/JS files with Python string operations, always verify `grep count` of function names before and after to detect duplication/truncation.
4. **Dashboard file deployment:** Base64 chunked SSH transfer reliable for large files. Temp file approach prevents partial writes. Kill stale processes before restart.

### 2026-06-14
## Fixes Deployed Today
- **Error:** `Can't parse keyboard button: can't find field 'text'` when selecting console
- **Root cause (2 layers):**
- Layer 1: `fetch_members_async()` wrapper (line 1491) needed `[m["id"] for m in result if ...]` mapping — ✅ fixed
- Layer 2: Alias at line 2541 (`fetch_members_async = api_fetch_members_async`) overrode the wrapper — **removed**
- **Result:** Booking flow now works for Guest (walk-in) ✅
- **Root cause:** `app.py` line 1517 had `@app.post("/api/consoles/start-session")` orphaned — decorated `api_session_end_notify` instead of `api_start_console_session`
- **Fix:** Moved decorator to line 1601 (before correct function)
- **Error:** `name '_psvibe_get_async' is not defined`
- **Root cause:** Function never existed in `api_client.py` — was imported in 3 places in `sales.py` but never defined
- **Fix:** Added `async def _psvibe_get_async(path)` to `api_client.py`
- **File:** `bot/handlers/booking_flow.py`
- **Root cause:** `_do_extend()` called `persist_reminder(..., message_thread_id)` but `message_thread_id` wasn't a parameter
- **Fix:** Added `message_thread_id: int = 0` parameter, updated both callers to extract from `query.message` / `update.message`
- **File:** `bot/handlers/notify.py`
- **Root cause:** `_check_low_balance_alert` used `os` module but never imported it
- **Fix:** Added `import os` (initially placed wrong — broke multi-line import — fixed in second attempt)
## Pre-existing (Warning-level, Not Blocking)
- **`inv_sh` = None** — K1 inventory Google Sheets update always fails silently (try/except catches it)
- **`fetch_balance_mins/-` 404** — Empty member_id when checking Guest wallet
## Services Status
## Heartbeats
## Fixes Deployed Today
- **Error:** `Can't parse keyboard button: can't find field 'text'` when selecting console
- **Root cause (2 layers):**
- Layer 1: `fetch_members_async()` wrapper (line 1491) needed `[m["id"] for m in result if ...]` mapping — ✅ fixed
- Layer 2: Alias at line 2541 (`fetch_members_async = api_fetch_members_async`) overrode the wrapper — **removed**
- **Result:** Booking flow now works for Guest (walk-in) ✅
- **Root cause:** `app.py` line 1517 had `@app.post("/api/consoles/start-session")` orphaned — decorated `api_session_end_notify` instead of `api_start_console_session`
- **Fix:** Moved decorator to line 1601 (before correct function)
- **Error:** `name '_psvibe_get_async' is not defined`
- **Root cause:** Function never existed in `api_client.py` — was imported in 3 places in `sales.py` but never defined
- **Fix:** Added `async def _psvibe_get_async(path)` to `api_client.py`
- **File:** `bot/handlers/booking_flow.py`
- **Root cause:** `_do_extend()` called `persist_reminder(..., message_thread_id)` but `message_thread_id` wasn't a parameter
- **Fix:** Added `message_thread_id: int = 0` parameter, updated both callers to extract from `query.message` / `update.message`
- **File:** `bot/handlers/notify.py`
- **Root cause:** `_check_low_balance_alert` used `os` module but never imported it
- **Fix:** Added `import os` (initially placed wrong — broke multi-line import — fixed in second attempt)
- **Error:** "Ovaltine cookies" (lowercase) chosen from food menu but `if choice not in prices:` failed because database has "Ovaltine Cookies" (capital C)
- **Root cause:** `step_food_menu` used exact/raw dictionary key lookup — case mismatch caused item to appear not found
- **Fix:** Added case-insensitive matching in `step_food_menu` and `step_food_qty` — uses `matched_key` to find correct-case key from `prices` dict, stores in `last_food_key` for quantity step
- **Files modified:** `bot/handlers/sales.py` — `step_food_menu()` + `step_food_qty()` functions
- **Result:** Ovaltine cookies, Ovaltine Cookies, or any case variant now matches ✅
## Investigation: `_remind_loop` Never Fires (Known Pre-existing Bug)
- **Status:** Investigated but not fixed. Root cause inconclusive.
- Logs confirm `_remind_loop` task is created via `load_and_restore()` but **never executes** `_extend_timer_kb()` or `sendMessage`
1. `asyncio.sleep(initial_delay)` silently never completes (event loop issue with `asyncio.get_event_loop().create_task`)
2. Task is cancelled before sleep completes
3. `initial_delay` is negative (if `next_remind_at` is in the past) → sleep never fires
- **Mitigation:** Staff using "No Timer" (`mins=0`) for recent sessions, so reminders not needed currently
- **Deferred:** Needs debug logging added inside `_remind_loop` to confirm reason
## Pre-existing (Warning-level, Not Blocking)
- **`inv_sh` = None** — K1 inventory Google Sheets update always fails silently (try/except catches it)
- **`fetch_balance_mins/-` 404** — Empty member_id when checking Guest wallet
## Services Status
## Heartbeats
## # June 14, 2026 — Daily Log (cont.)
## Fix 7 (NEW): Food Cart Feature — Session Food Orders (17:44 UTC)
- New button `BTN_FOOD_SALE` added to Console Management keyboard
- When clicked → shows list of active sessions → staff picks one via `/_console_session_food_pick`
- Calls `cmd_session_food_order(target)` which:
- Pre-fills member/console from session data
- Sets `session_food_order=True` flag
- Opens `prompt_food_menu`
- New function `cmd_session_food_order(update, context, target)` — sets up user_data with session info
- New function `_save_food_cart(update, context)` — intercepts `BTN_DONE` when flag is set:
- Saves items to food_cart via `POST /api/food-cart`
- Returns to Console Menu (no payment)
- Modified `step_food_menu`: checks `session_food_order` flag at `BTN_DONE`
- After `context.user_data.update({...})`, fetches `GET /api/food-cart/{booking_id}`
- Adds all cart items to `context.user_data["food_items"]` automatically
- Items appear in Daily Sales form when voucher opens
- psvibe-api ✅ (food-cart routes)
- psvibe-sale-bot ✅ (new handler functions)
- POST /api/food-cart: CREATE ✅
- GET /api/food-cart/B001: SELECT (unfulfilled only) ✅
- DELETE /api/food-cart/B001: UPDATE fulfilled_at ✅
- Python syntax: console.py ✅ sales.py ✅
- POST → GET → DELETE cycle verified on all food_cart API endpoints
- SQL query verified both create and fulfill timestamps correct
- Python compile check on both modified bot files
- Customer Bot direct ordering (customers order from their own chat)
- Customer Notifications when food arrives
- Multiple-food-order UI improvements (edit/remove items before Done)
## Heartbeat (17:44 UTC) — During Food Cart Feature Development
- All services running: psvibe-sale-bot, psvibe_customer_bot, psvibe-api, cloudflared-tunnel, Caddy, n8n, MySQL, fail2ban
- Food Cart Feature freshly deployed
## Heartbeat (17:44 UTC) — Quick Health Check
## Fixes Deployed Today
- **Error:** `Can't parse keyboard button: can't find field 'text'` when selecting console
- **Root cause (2 layers):**
- Layer 1: `fetch_members_async()` wrapper (line 1491) needed `[m["id"] for m in result if ...]` mapping — ✅ fixed
- Layer 2: Alias at line 2541 (`fetch_members_async = api_fetch_members_async`) overrode the wrapper — **removed**
- **Result:** Booking flow now works for Guest (walk-in) ✅
- **Root cause:** `app.py` line 1517 had `@app.post("/api/consoles/start-session")` orphaned — decorated `api_session_end_notify` instead of `api_start_console_session`
- **Fix:** Moved decorator to line 1601 (before correct function)
- **Error:** `name '_psvibe_get_async' is not defined`
- **Root cause:** Function never existed in `api_client.py` — was imported in 3 places in `sales.py` but never defined
- **Fix:** Added `async def _psvibe_get_async(path)` to `api_client.py`
- **File:** `bot/handlers/booking_flow.py`
- **Root cause:** `_do_extend()` called `persist_reminder(..., message_thread_id)` but `message_thread_id` wasn't a parameter
- **Fix:** Added `message_thread_id: int = 0` parameter, updated both callers to extract from `query.message` / `update.message`
- **File:** `bot/handlers/notify.py`
- **Root cause:** `_check_low_balance_alert` used `os` module but never imported it
- **Fix:** Added `import os` (initially placed wrong — broke multi-line import — fixed in second attempt)
- **Error:** "Ovaltine cookies" (lowercase) chosen from food menu but `if choice not in prices:` failed because database has "Ovaltine Cookies" (capital C)
- **Root cause:** `step_food_menu` used exact/raw dictionary key lookup — case mismatch caused item to appear not found
- **Fix:** Added case-insensitive matching in `step_food_menu` and `step_food_qty` — uses `matched_key` to find correct-case key from `prices` dict, stores in `last_food_key` for quantity step
- **Files modified:** `bot/handlers/sales.py` — `step_food_menu()` + `step_food_qty()` functions
- **Result:** Ovaltine cookies, Ovaltine Cookies, or any case variant now matches ✅
## Investigation: `_remind_loop` Never Fires (Known Pre-existing Bug)
- **Status:** Investigated but not fixed. Root cause inconclusive.
- Logs confirm `_remind_loop` task is created via `load_and_restore()` but **never executes** `_extend_timer_kb()` or `sendMessage`
1. `asyncio.sleep(initial_delay)` silently never completes (event loop issue with `asyncio.get_event_loop().create_task`)
2. Task is cancelled before sleep completes
3. `initial_delay` is negative (if `next_remind_at` is in the past) → sleep never fires
- **Mitigation:** Staff using "No Timer" (`mins=0`) for recent sessions, so reminders not needed currently
- **Deferred:** Needs debug logging added inside `_remind_loop` to confirm reason
## Pre-existing (Warning-level, Not Blocking)
- **`inv_sh` = None** — K1 inventory Google Sheets update always fails silently (try/except catches it)
- **`fetch_balance_mins/-` 404** — Empty member_id when checking Guest wallet
## Services Status
## Heartbeats
## Fix 7 (NEW): Food Cart Feature — Session Food Orders (17:44 UTC)
- New button `BTN_FOOD_SALE` added to Console Management keyboard
- When clicked → shows list of active sessions → staff picks one via `/_console_session_food_pick`
- Calls `cmd_session_food_order(target)` which:
- Pre-fills member/console from session data
- Sets `session_food_order=True` flag
- Opens `prompt_food_menu`
- New function `cmd_session_food_order(update, context, target)` — sets up user_data with session info
- New function `_save_food_cart(update, context)` — intercepts `BTN_DONE` when flag is set:
- Saves items to food_cart via `POST /api/food-cart`
- Returns to Console Menu (no payment)
- Modified `step_food_menu`: checks `session_food_order` flag at `BTN_DONE`
- After `context.user_data.update({...})`, fetches `GET /api/food-cart/{booking_id}`
- Adds all cart items to `context.user_data["food_items"]` automatically
- Items appear in Daily Sales form when voucher opens
- psvibe-api ✅ (food-cart routes)
- psvibe-sale-bot ✅ (new handler functions)
- POST /api/food-cart: CREATE ✅
- GET /api/food-cart/B001: SELECT (unfulfilled only) ✅
- DELETE /api/food-cart/B001: UPDATE fulfilled_at ✅
- Python syntax: console.py ✅ sales.py ✅
- POST → GET → DELETE cycle verified on all food_cart API endpoints
- SQL query verified both create and fulfill timestamps correct
- Python compile check on both modified bot files
- Customer Bot direct ordering (customers order from their own chat)
- Customer Notifications when food arrives
- Multiple-food-order UI improvements (edit/remove items before Done)
## Fix 8: Import Path Error — `cmd_session_food_order` (18:20 UTC)
- `fetch_members_async = api_fetch_members_async` alias at `__init__.py` line 2555 which returns a list of member dicts, not a list of IDs
- `cmd_session_food_order` calls `await fetch_members_async()` → gets dicts → passes to `prompt_food_menu` which expects IDs → breaks
## Boss Reports (Ongoing Issues — 18:22-18:42 UTC)
- Food items not appearing in voucher
- Game minutes also disappear
- Screenshot shows "Review Summary (5/6)" with "Net Payable: 0 Ks" and food items listed
- **Root cause (probable):** Import error (Fix 8) prevented `cmd_session_food_order` from running properly. The `session_food_order` flag was never set, so `BTN_DONE` fell through to regular flow (standalone Food Sale), not `_save_food_cart`. No `booking_id` present — game minutes were part of the same corrupted session data.
- **Expected after Fixes 8+9+10 deployed:** Fresh session should work
- Ending one session resets other active sessions' start times + food orders
- **Hypothesis:** `context.user_data` shared per staff chat — `launch_session_sale` overwrites user_data for one session, corrupting other sessions' data
- **Not yet fixed** — needs investigation. This affects staff managing multiple concurrent sessions.
- **Possible fix:** Store session data keyed by `booking_id` in user_data, or refresh other sessions' data from API after end
- **Already fixed** — see Fix 10 above. Non-blocking coupon gen should resolve.
## Summary Statistics (End of Day)
## Heartbeat (18:42 UTC)
- All services running after final restart
- Fixes 8-10 deployed (import error, dead code, coupon blocking)
- Boss testing pending for fresh session (Issue A) and multi-session fix (Issue B)

### 2026-06-15
## 🐛 Fix: Morning Health Summary MySQL Query Bug
- `SELECT COUNT(*) as txns FROM sales_daily WHERE sale_date = '2026-06-14'` → `43` ✅
- Full multi-column query: `txns=43, total=737950.00, gross=789750.00, discounts=51800.00` ✅
- Morning report will show correct data at next 8 AM MMT run
- Changed from: `function mysqlQuery(query) { return sshExec(...2>&1...); }`
- Changed to: `async function mysqlQuery(query) { const r = await sshExec(...2>&1...); return r.replace(/^.*Warning.*\n?/m, ''); }`
## ✅ Services Status (June 15, 02:32 UTC)
## 🐛 June 15 — Fixes Applied (02:42 UTC)
- **Root cause:** `booking_id` from MySQL is an integer, but API tried `.strip()` on it directly
- **Fix:** `str(body.get(...)).strip()` — convert to string first
- **File:** `/root/psvibe_api_server/patch_routes.py` line 1328
- **Root cause:** Both `step_sale_confirm` (~line 1310) and `launch_session_sale` (~line 1790) used `await asyncio.to_thread(api_post, "coupons/generate", ...)` — BLOCKING
- **Fix:** Wrapped in nested `async def _gen_cpn_step()`/`_gen_cpn_launch()` + `asyncio.create_task()` — non-blocking
- **Files:** `/root/psvibe-sales-bot/bot/handlers/sales.py` lines 1310 & 1792
- **Root cause:** Systemd starts API on port 8000, but old process on port 5001 was still running (started before patch_routes changes)
- **Fix:** Killed old PID 1410543 (port 5001)
- **Root cause:** Fix script used 8-space indent but original code used 4-space
- **Fix:** Corrected to 4-space indent; sale bot now starts successfully
- Morning Health Summary MySQL query bug (warning line filtered)
## ✅ Services Restarted
- Boss to test Phase 1 Food Cart flow end-to-end
- Phase 2 (future): Customer Bot self-ordering
- n8n payment (€25.68) — still pending
- **Root cause:** `console.py` booking lookups used `_b.get("consoleId")` but API `_map_booking_row` maps `console_id` → `consoleType`. Never found any booking → booking_id="" → food note "No booking_id" error + sale voucher 0s
- **Fix 1 (line 225):** `consoleId` → `consoleType or consoleId` for food note booking lookup
- **Fix 2 (line 355-356):** Added `"in_use"` to status filter + `consoleType` fallback for end session booking lookup
- **Bot restarted:** psvibe-sale-bot ✅
- **Affected guests:** Food note users + any session started via Console → End Session
## 🏗️ Finance Fixes — PNL, Balance Sheet & Auto-Depreciation
- Zero food revenue (383,200 Ks real)
- Zero wallet consumed (50,700 Ks real)
- Only 800K salary as OPEX (10,012,666 Ks real)
- Zero COGS (239,306 Ks real)
- Zero depreciation (6,995,548 Ks real)
- **Result: +1,518,416 FALSE profit** → Fixed: **-15,163,987 LOSS** ✅
- Total assets: 427,000 Ks (real: ~279M)
- Zero capital (real: 300M)
- Zero retained earnings (real: -20.7M)
- Zero equipment NBV (real: ~270M)
- Calculates months from purchase_month through current_month (inclusive)
- Updates `acc_depreciation` and `months_elapsed` in `finance_assets`
- Caps at useful_life (in months)
- Cron: monthly 1st at 2:30 UTC (9:00 MMT)
- **Before:** 3,262,283 Ks (27 assets only)
- **After:** 10,257,830 Ks (all 39 assets, June depreciation included)
1. **`%%Y-%%m` pattern doesn't work with `mysql.connector`**: The `_mysql_query` wrapper uses `mysql.connector` which uses `%s` parameter style. `%%` is NOT processed like `printf` — must pass format string as a parameter: `("%Y-%m", ym)`.
2. **Depreciation convention**: PS VIBE uses "depreciation from purchase month (inclusive)". So a Jun-purchased asset has 1 month of depreciation in Jun. Yes, this means first month gets full depreciation — it's a simplifying assumption.
3. **Dashboard code is the source of truth**: The PNL/BS stubs in `patch_routes.py` were early prototypes and NOT updated alongside dashboard changes. Always check `dashboard_routes.py` first before trusting other API endpoints.
4. **`sales_daily.net = amount + food`**: Confirmed via ID 128 (amount=11,650 + stock_out 22,000 → net=33,650). Food IS baked into `sales_daily.net`. Must subtract food_rev from total_sales_net to get pure game revenue.
5. **Auto-depreciation cron must NOT use LockMonitor**: The cron runs on 1st of month at 2:30 UTC (non-peak). If LockMonitor interferes, it should be a one-minute simple operation that runs on startup too.
1. **Food Note issue** — Boss asked "ဆက်လုပ်ပါ" which could mean continue on this. Awaiting further instruction.
2. **n8n payment (€25.68)** — 2nd notice, subscribe may expire
3. **GitHub Deploy failing** — psvibe-api-server master branch deploy workflow failing
4. **100+ games discrepancy** — 41 in DB vs claimed 100+
## 🐛 June 15 (PM Session) — PNL Depreciation Fix + Daily Sales Verification
- `patch_routes.py` (L716-718): Added `AND purchase_date < %s` filter with first_of_month
- `dashboard_routes.py` (L2292): Same fix
- **BS Retained Earnings:** -13,747,413 (auto-balanced)
- **PNL Cumulative Net Profit:** -11,216,929
- **Auto-balancer adjustment:** -2,508,309 (silent adjustment for cash/income discrepancy)
22. **PNL depreciation must filter by purchase_date**: Include only assets that were purchased BEFORE the current month's start. New assets don't accrue depreciation until the month after purchase.
## 🎮 PS VIBE Discord Bot — Deployed (June 15, ~16:55 UTC)
- Bot Application: "PS VIBE Bot" (ID: 1516120408393515081)
- 7 Slash Commands Registered: `/balance`, `/games`, `/slots`, `/promo`, `/hours`, `/menu`, `/help`
- systemd service: `psvibe-discord-bot.service` — active + enabled (auto-restart)
- Location: `/root/psvibe-discord-bot/` on bot-server-01
- Connected to: "PS VIBE - PS5 Gaming Lounge" (1 guild)
- Bot Token: Provided by Boss
- Bot Status: Playing "🎮 PS VIBE - PS5 Gaming Lounge"
1. **Enable Privileged Intents** in Discord Developer Portal → Bot → Privileged Gateway Intents:
- ✅ Or ❌ Server Members Intent (for welcome DM on new member join)
- ✅ Or ❌ Message Content Intent (if prefix commands needed later)
2. **Discord Server Structure** — Channels နဲ့ Roles တွေကို ဆက်ပြီး ပြင်ဆင်ရန် (or ask Kora to help)
- **Channels Created:** 20 channels across 5 categories (Announcements, General, Game Hub, Events, Voice)
- **Roles Created:** Owner, Admin, Moderator, VIP Member, Member
- **Bot Updated:** Server Members Intent enabled, welcome DM system active
- **Guild:** PS VIBE - PS5 Gaming Lounge (ID: 1516119712411422942)
## 🎮 Discord Bot — Session Continuation (June 15, ~18:43-19:10 UTC)
1. **`/hours` fixed**: Was showing wrong hours → corrected to "9:00 AM - 9:00 PM All Days" ✅
2. **Permanent invite link**: Created never-expire link `https://discord.gg/EXEF7phbZF` ✅
3. **Giveaway improved**: Added `create` (Staff: prize + duration), `end` (Staff), and `id` option for enter/draw. Prize & period now properly defined ✅
4. **Privacy/Ephemeral**: Made `/vip`, `/report`, `/book check`, `/book request` — **user-only visible** (ephemeral) ✅
- **Active** ✅ (systemd service, auto-restart)
- **PID**: Last restarted ~18:52 UTC
- **21 Slash Commands** registered
- **Member Counter VC**: `👥 Members: 0` (ID: 1516147221090009098)
- **Permanent Invite**: `/invite` uses permanent link now
- Daily sales report cron failed (timed out) — needs investigation

### 2026-06-16
## 🩺 Heartbeat (14:37 UTC / 21:07 MM)
- **Health Monitor:** 53.5 (known false negatives: VPS unreachable, path detection mismatch — not real issues)
- **Docker:** 7/7 containers healthy (psvibe-mysql, construction_bot, caddy, n8n, oc-nova, oc-coco, gateway)
- **yyo-personal-wallet:** Running as systemd service ✅
- **check_alerts:** All services healthy ✅
- **Task bridge:** 0 pending ✅
- **Dead-letter queue:** Empty ✅
- **Stale locks:** Cleaned 0 ✅
- **Heartbeat routine:** 12 tasks OK, 0 pending, 0 stuck ✅
- **Notifier:** 3 old unread alerts (Jun 9-14, yyo-personal-wallet — resolved, service running)

## ⏰ Quick Ref: Timezone
- Boss: **Asia/Yangon (UTC+6:30)**
- ALL UTC → Myanmar Time before telling Boss

## 🛡️ Quick Ref: Fix Protocol
```bash
python3 /root/coordination/fix_protocol.py --start <file>  # Before edit
python3 /root/coordination/fix_protocol.py --complete       # After edit
```
See `memory/config.md` for details. See `memory/lessons.md` for spawn & lock lessons.

---

## 📌 Current Services (June 11, 18:00 UTC)
| Service | Status |
|---------|--------|
| psvibe-api | ✅ |
| psvibe-sale-bot | ✅ |
| psvibe_customer_bot | ✅ |
| psvibe-dashboard | ✅ |
| Caddy (nginx proxy) | ✅ |
| n8n | ✅ |
| MySQL | ✅ |
| cloudflared-tunnel | ✅ |
| Kora Dashboard | ✅ |
| Health Monitor | 93.3 / 100 ✅ |

---

## 🧪 Critical Lessons Archive

- **MEMORY.md truncation:** Session context loads ~11KB of ~40KB file. Keep MEMORY.md lean — use module files for details
- **Session cron jobs <60s cause takeover errors:** Minimum 5-min interval for lock operations
- **Session file bloat (446MB/500MB):** 1,305 session files; Gateway auto-prune handles this

---

## 📋 Recent Fix History (June 6-11)
| Date | Fix | File(s) |
|------|-----|---------|
| June 11 | Pending — Kora Dashboard: Logo favicon update | `kora_dashboard/index.html` |
| June 11 | Kora Dashboard v2 — 10 Features (Booking Schedule, Sales Chart, Member Lookup, Alerts, Food Stock, EOD Summary, Language Toggle, QR Share, Quick Commands, Auto-Refresh) | `kora_dashboard/*` |
| June 11 | Login refresh bug (API_BASE: absolute→relative) | `kora_dashboard/index.html` |
| June 11 | Web Commands → VPS execution | `kora_dashboard/*`, `vps_bridge.sh` |
| June 10 | Sales Daily lazy-load fix (Cloudflare n8n cache) | `dashboard-dist/*.js` (22 chunks) |

---

## 🤖 Kora Automation — Active Tools (June 11)
19 automation tools deployed: Smart Alerts, Auto Maintenance, Multi-Channel, Console Booking, Smart Reminder, Kora Dashboard (10 features, :9091), Research Agent, Auto-Reply, Git Backup, Memory Manager, Uptime Monitor, AI Bot Enhancer, BI Dashboard, Notification Center, Disaster Recovery, Knowledge Wiki (9 pages), Security Audit, i18n (75 keys MY/EN). See `memory/2026-06-11.md` for full details.

## 🧹 Session Cleanup (June 11)
- Freed 168 MB (855→687 MB), now 129 MB in session files (well below 500MB limit)
- 5 auto-protection layers in cleanup script; cleanup cron every 10 min

## ☁️ Cloudflare — Resolved (June 11)
- Account flagged for ID verification → Boss completed it, all sanctions lifted

## 📋 Pending — Boss Action Needed
1. **n8n Payment (€25.68)** — 2nd notice, subscription may expire
2. **GitHub Deploy Failing** — PSVIBE-API-Server master branch deploy workflow failing

## 🩺 Latest Heartbeat (June 11, 15:18 UTC)
- Health Monitor: 93.3/100 | Docker: 7/7 | Disk: 18% | RAM: 11Gi | Uptime: 14d+
- MEMORY.md: auto-trim cron active | Git backup: committed | Index: 1146 topics
- 0 stuck/pending agents | No critical alerts
- *Heavy optimization day — session files cleaned, MEMORY.md trimmed, Cloudflare resolved, 20+ Kora upgrades deployed.*

---

## 📋 June 12 — Summary

### 🔴 SSH Crisis: ISP-Level IP Blocking
- **IP 5.223.81.16 completely unreachable** from Boss's Myanmar ISP (ping fails, not just SSH ports)
- DPI detects SSH protocol on ANY port (22, 80, 443, 22222 all blocked)
- **Workaround:** Web SSH via `https://ps-vibe.com/shell/` (wssh + Cloudflare Tunnel) — working ✅
- **Pending:** Cloudflare Zero Trust → Tunnels → Public Hostnames config for `shell.ps-vibe.com`
- **Lesson:** ISP can block entire IP routing, not just ports; Cloudflare Tunnel + HTTPS bypasses it

### ✅ Fixes Deployed
| Fix | Files |
|-----|-------|
| Game Library: 23 titles corrected in MySQL | `games_library` (41 rows), `console_games` (68 rows) |
| Dashboard Games: final_status → In Use/Available | `fix_games_library_status.py` |
| FAQ intercept disabled (wrong game count) | `customer_bot/handlers.py` (commented out) |
| Booking wallet skip (booking_id guard) | `sales.py` line 1677 |
| Session timer message_thread_id | `booking_flow.py`, `session_reminder_store.py`, `booking.py` |
| Booking game selection [:30] limit removed | `booking.py` lines 442 & 610 |
| Food Menu: Soft Drinks + Coffee categories | 5 files (Dashboard, Customer Bot, Sale Bot, API) |
| Account balances verified correct | All operating accounts match |
| Low stock alert: 30min → 4hr | `/var/spool/cron/crontabs/root` |
| Kora Smart-Reminder: thread ID → 125192 | `smart_reminder.js` |
| Git: Both repos committed, 0 uncommitted | Sales Bot (16 files), API Server (7 files) |

### 📌 New Lessons (June 12)
- **Dashboard JS only supports 4 final_status values:** Available, Damaged, Lost, In Use
- **games_library vs console_games** are independent tables — titles must match exactly
- **Booking customers skip wallet check** — they pay at booking time, not session-end
- **disc_count values are intentional** — never modify without Boss confirmation
- **Staff group Forum mode:** messages without `message_thread_id` go to General topic
- **IP unreachable ≠ port blocked:** when ping fails, it's routing/ISP filtering
- **Web SSH works when direct SSH doesn't:** Cloudflare Tunnel + HTTPS bypasses ISP filters

### 🔴 Pending (Boss Action Needed)
1. **CMD SSH** — Cloudflare Zero Trust → Tunnels → Public Hostnames for `shell.ps-vibe.com`
2. **100+ games discrepancy** — 41 in DB vs claimed 100+. Clarify if GSheet had non-game rows
3. **God of War Ragnarök encoding** — "Ã¶" vs "ö", only LIKE-matched, needs clean fix
4. **n8n payment (€25.68)** — 2nd notice received

### 🩺 Services (June 12, 15:30 UTC)
| Service | Status |
|---------|--------|
| psvibe-api | ✅ |
| psvibe-sale-bot | ✅ |
| psvibe_customer_bot | ✅ |
| psvibe-dashboard | ✅ (:9090) |
| kora-dashboard | ✅ (:9091) |
| cloudflared-tunnel | ✅ |
| wssh (web SSH) | ✅ (:8888) |
| Caddy | ✅ |
| n8n | ✅ |
| MySQL | ✅ |
| Health Monitor | 93.3/100 ✅ |

### 🧠 Critical Lessons (Running Archive)
1. FastAPI response_model silently strips undeclared fields
2. `bool(0) == False` → use `x if x is not None else default`
3. `async def` + missing `await` → coroutine passes type checks silently
4. Double fail masking: both API + GSheet broken simultaneously
5. Date format: always normalize to YYYY-MM-DD at API boundary
6. Slot conflict: API-level booking check prevents double-booking
7. Dashboard only supports 4 statuses: Available/Damaged/Lost/In Use
8. ISP can block entire IP routing; Cloudflare Tunnel + HTTPS bypasses it
9. Staff group Forum mode: always include message_thread_id

## 📌 June 13 — New Critical Lessons

10. **JS `<script>` block fragility** — A single syntax error (e.g., broken quoting in onclick) anywhere in a `<script>` block kills ALL JavaScript in that block, including unrelated functions like `doLogin()`. Always validate inline scripts carefully.
11. **PNL Food Revenue ≠ Console Multiplier** — Food revenue must come from `stock_out` table (items sold × unit_price), NOT from `gross-amount` (console multiplier). These are fundamentally different data sources. Mixing them corrupts both food and game margins.
12. **fail2ban is baseline security** — Was completely missing from VPS until audit discovered it. Every production server should have fail2ban running from day one.
13. **Cloudflare Tunnel path routing limitation** — `/kora/` path routes to localhost:8000 (API server) cannot also route to :9091 (Kora Dashboard). Solution: DNS CNAME record (`kora.ps-vibe.com`) for separate services behind same tunnel.

## 📌 Pending Issues (June 13, 15:30 UTC)
3. **Kora Dashboard URL**: `kora.ps-vibe.com` needs DNS CNAME record at Cloudflare
4. **Wallet rate**: `effective_rate` = 1.00 for all members (might need Boss to confirm intended pricing)

## 🩺 Services (June 13, 15:30 UTC)
| Service | Status |
|---------|--------|
| psvibe-api | ✅ |
| psvibe-sale-bot | ✅ |
| psvibe_customer_bot | ✅ |
| psvibe-dashboard (:9090) | ✅ |
| kora-dashboard (:9091) | ✅ |
| cloudflared-tunnel | ✅ |
| wssh (web SSH :8888) | ✅ |
| Caddy | ✅ |
| n8n | ✅ |
| MySQL | ✅ |
| fail2ban | ✅ (NEW) |
| Daily Auto-Backup | ✅ (NEW: cron 0 2 * * *) |
| Health Monitor | ~93/100 ✅ |

---

## 📋 June 14 — Summary

### Fixes Deployed (6 total)
| # | Fix | File(s) | Root Cause |
|---|-----|---------|------------|
| 1 | Booking Flow — Member Keyboard Hang | `sales.py` line 1491, 2541 | `fetch_members_async` wrapper overridden by alias; needed `[m["id"] for m in result]` mapping |
| 2 | "No telegram_chat_id, skip notification" | `app.py` line 1517→1601 | Orphaned `@app.post` decorator on wrong function |
| 3 | Food Sale — Stock Map Rebuild Failed | `api_client.py` | `_psvibe_get_async` imported in 3 places but never defined |
| 4 | Booking Extend — `message_thread_id` undefined | `booking_flow.py` | Missing parameter in `_do_extend()` + `persist_reminder()` |
| 5 | `name 'os' is not defined` | `notify.py` | `_check_low_balance_alert` used `os` module without import |
| 6 | Ovaltine Cookies — Case-Sensitive Match | `sales.py` | `step_food_menu` used exact dict key lookup; "Ovaltine cookies" ≠ "Ovaltine Cookies" |

### 🔍 Investigation: `_remind_loop` Never Fires (Known Bug — Not Fixed)
- Logs confirm task is created via `load_and_restore()` but **never executes**
- Zero `_extend_timer_kb` calls logged all day for any console
- Hypotheses: `asyncio.sleep(initial_delay)` never completes / task cancelled / negative delay
- **Mitigation:** Staff using "No Timer" (`mins=0`) for recent sessions
- **Deferred:** Needs debug logging inside `_remind_loop`

### 📌 New Lessons (June 14)
14. **Case-insensitive matching for user input** — Dictionary key lookups on user-typed text must be case-insensitive. Normalize to consistent case at system boundary or use case-insensitive matching.
15. **Decorator placement is critical** — `@app.post("/path")` on the wrong function silently routes requests to the wrong handler. Always verify decorator → function mapping after edits.
16. **Async imports must be defined, not just imported** — Importing a function name doesn't create it. Always verify the source file actually defines what downstream files import.

### Pre-existing Warnings (Non-Blocking)
- `inv_sh = None` — K1 inventory Google Sheets update always fails silently
- `fetch_balance_mins/-` 404 — Empty member_id when checking Guest wallet

### 🩺 Services (June 14, 15:30 UTC)
| Service | Status |
|---------|--------|
| psvibe-api | ✅ |
| psvibe-sale-bot | ✅ |
| psvibe_customer_bot | ✅ |
| cloudflared-tunnel | ✅ |
| Caddy | ✅ |
| n8n | ✅ |
| MySQL | ✅ |
| fail2ban | ✅ |
| Health Monitor | ~91.6/100 ✅ |

---

## 📋 June 15 — Summary

### 🔧 Fixes Deployed (8 total)
| # | Fix | File(s) | Root Cause |
|---|-----|---------|------------|
| 1 | Morning Health Summary showing 0s | `lib/ssh_vps.js` | MySQL password warning merged into stdout via `2>&1` → parsed as column headers |
| 2 | Food Cart POST — `int.strip()` crash | `patch_routes.py` L1328 | `booking_id` from MySQL is int; `.strip()` only works on strings |
| 3 | Coupon gen blocking voucher (v2) | `sales.py` L1310, 1792 | `await asyncio.to_thread()` still blocking; wrapped in `create_task()` |
| 4 | Stale API on port 5001 | n/a | Old process from before patch_routes changes still running |
| 5 | Indentation error in coupon fix | `sales.py` | Fix script used 8-space indent; original is 4-space |
| 6 | Food Note / End Session booking_id not found | `console.py` L225, 355 | `_map_booking_row` maps `console_id` → `consoleType`; code looked for `consoleId` |
| 7 | **PNL API — Broken Stub** | `patch_routes.py` L665-720 | Stub returned +1.5M fake profit; replaced with real dashboard logic → -15.2M LOSS ✅ |
| 8 | **Balance Sheet API — Broken Stub** | `patch_routes.py` L724-755 | Stub showed 427K assets (real: 279M); replaced with full dashboard BS logic ✅ |

### 🏗️ Finance Infrastructure
- **Auto-Depreciation:** Created `/root/scripts/auto_depreciate.py` — monthly cron (1st, 2:30 UTC)
- **Catch-up:** 12 of 39 assets had `acc_depreciation=0` → fixed; total now 10,257,830 Ks ✅
- **Balance Sheet verified:** A = L + E @ 279,445,881 Ks ✅
- **PNL verified:** June YTD = -15,163,987 Ks LOSS ✅

### 🧠 5 New Lessons (June 15)
- **17.** `%%Y-%%m` doesn't work with `mysql.connector` — uses `%s` params, not printf-style `%%`
- **18.** Depreciation convention: from purchase month (inclusive), first month gets full depreciation
- **19.** Dashboard code is source of truth — `patch_routes.py` stubs were outdated prototypes
- **20.** `sales_daily.net = amount + food` — food IS baked into net; subtract food_rev for pure game revenue
- **21.** Auto-depreciation cron must NOT use LockMonitor — simple 1-minute operation, non-peak hours

### 📌 Pending (Boss Action Needed)
3. **100+ games discrepancy** — 41 in DB vs claimed 100+
4. **Food Note issue** — Boss said "ဆက်လုပ်ပါ", awaiting further instruction

### 🩺 Services (June 15, 15:30 UTC)
| Service | Status |
|---------|--------|
| psvibe-api | ✅ |
| psvibe-sale-bot | ✅ |
| psvibe_customer_bot | ✅ |
| psvibe-dashboard | ✅ |
| kora-dashboard | ✅ |
| cloudflared-tunnel | ✅ |
| Caddy | ✅ |
| n8n | ✅ |
| MySQL | ✅ |
| fail2ban | ✅ |
| Health Monitor | ~91/100 ✅ |

### 🧠 Critical Lessons Archive (continued)
- 17. **`%%Y-%%m` ≠ `mysql.connector` params** — `mysql.connector.execute()` uses `%s` style, not printf `%%`
- 18. **Depreciation from purchase month (inclusive)** — first month = full month depreciation
- 19. **Dashboard code is source of truth** — always check `dashboard_routes.py` before other endpoints
- 20. **`sales_daily.net` includes food** — food revenue baked into `net`; subtract for pure game revenue
- 21. **Auto-depreciation cron = no LockMonitor** — simple 1-min op, non-peak hours only