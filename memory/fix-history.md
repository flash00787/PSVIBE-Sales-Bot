# 📋 Fix History

> Recent major fixes. Full daily logs at `memory/YYYY-MM-DD.md`

## 2026-06-20 — Sale Bot Approve/Reject + Customer Bot Duration Conflict

### #44: Text Polish Script Miss — return 0 Tuple 🐛
| Bug | Files | Root Cause | Fix |
|-----|-------|-----------|-----|
| Python script missed `return 0` on line 493 | `customer_bot/booking_handlers.py` L493 | `line.strip() == 'return 0'` didn't match `return 0  # Console is Active/Unavailable` due to trailing comment | Manual fix: `return 0, ""` |

### #45: Rejected Bookings Trigger Duplicate Warning 🐛
| Bug | Files | Root Cause | Fix |
|-----|-------|-----------|-----|
| "Duplicate Booking Detected!" on rejected bookings | `customer_bot/booking_handlers.py` L2318, L2397 | Status filter excluded only `("cancelled", "done")` — "rejected" bookings still triggered overlap check | Added `"rejected"` → `("cancelled", "done", "rejected")` in both BK_CONFIRM paths |

### #38: Sale Bot Approve Button Crash 🐛
| Bug | Files | Root Cause | Fix |
|-----|-------|-----------|-----|
| Approve button → UnboundLocalError | `admin_bookings.py` L302-325 | `consoles_with_game` variable only defined inside `if not chosen:` auto-assign block, but accessed in `if chosen:` block when customer chose own console | Moved `consoles_with_game` init BEFORE all branching; fetch once at top |

### #39: Sale Bot Reject Button Crash 🐛
| Bug | Files | Root Cause | Fix |
|-----|-------|-----------|-----|
| Reject button → UnboundLocalError | `admin_bookings.py` L267-285 | `bk_info` variable only defined inside `if action == "approve":` block, but accessed in `else:` (reject) block | Moved `bk_info` fetch OUTSIDE approve block — now shared |

### #40: Reject Reason Feature 🆕
| Feature | Files | Details |
|---------|-------|---------|
| Reject လုပ်ရင် reason ထည့်လို့ရ | `admin_bookings.py`, `app.py` | When "❌ Reject" clicked → prompts for reason with Skip button. Reason shown in card + customer notification. State stored in `bot_data` (not `user_data`) to avoid ConversationHandler interference. New handlers: `handle_reject_reason` (group -1), `cb_reject_skip` |

### #42: Customer Bot Duration — Auto-Assign v3 🐛
| Bug | Files | Root Cause | Fix |
|-----|-------|-----------|-----|
| Auto-assign still crashes on duration conflict | `customer_bot/booking_handlers.py` | (1) `available` list empty → no console_id → API crash, (2) `_validate_response()` raises ValueError for HTTP 4xx → caught by `except Exception`, never reaches max_dur code | (1) Added `else` block: when available empty, find any matching console, calc max_dur, return go_back, (2) Added `except ValueError` before `except Exception` — treats API errors as booking failures with max_dur check |

### #43: Customer Bot Duration — Text Polish ✨
| Improvement | Files | Details |
|-------------|-------|----------|
| Natural Burmese message format | `customer_bot/booking_handlers.py` | Changed from "Max duration: X min သာရပါမည်" to "XX:XX မှာ Booking ရှိနေလို့ XX min ပဲ ရပါတော့မယ် ခင်ဗျ" — shows WHY only X minutes available. `_get_max_duration_for_console()` now returns `(max_mins, next_booking_time)` tuple. Updated all 4 error message sites. |

## 2026-06-19 — Booking System Concurrency Fixes (H1, C1, H2)

### H1: Approve Overlap Lock 🔒
| Bug | Files | Root Cause | Fix |
|-----|-------|-----------|-----|
| Staff ၂ယောက် တပြိုင်နက် approve → နှစ်ယောက်စလုံးအောင် | `app.py` L1415 | Overlap check တွင် row-level lock မရှိ — race condition | `SELECT ... FOR UPDATE` lock ထည့် — တစ်ယောက်ပဲအောင် |

### C1: Console Start-Session Lock 🔒
| Bug | Files | Root Cause | Fix |
|-----|-------|-----------|-----|
| Console status race — session ၂ခု တပြိုင်နက်စ | `app.py` L1882 | `console_status` check က transaction အပြင်မှာ — stale read | Console_status check ကို transaction အတွင်း `FOR UPDATE` နဲ့ ရွှေ့ |

### H2: Walk-in Session → Pending Booking Warning ⚠️
| Bug | Files | Root Cause | Fix |
|-----|-------|-----------|-----|
| Staff walk-in က pending/confirmed booking ကျော်နိုင် | `app.py` L2180-2202, `booking.py` | `status='Active'` ပဲစစ် — pending/confirmed မစစ် | Active → 409 BLOCK (အရင်အတိုင်း); Pending/Confirmed → ⚠️ WARNING only (မတား); Bot က warning message ပြ |

**Verification:** All 3 fixes deployed, API + bots restarted ✅

---

## 2026-06-18 — Broadcast System Fix + Feature

### Fix 5: Broadcast API Returns Wrong Key + Route Order Bug
| Bug | Files | Root Cause | Fix |
|-----|-------|-----------|-----|
| Broadcast always "targets not found" | `patch_routes.py:594`, `app.py:1440` | API returned `member_id` (not `telegram_chat_id`); route after `{booking_id}` catch-all → 422 | Return `telegram_ids` from DISTINCT query; move route BEFORE `{booking_id}` |

### Feature: Customer Bot `/admin_broadcast`
| File | Description |
|------|-------------|
| `customer_bot/broadcast.py` (new) | Admin-only broadcast to all customer bot users via `/admin_broadcast <message>` |
| `customer_bot/main.py` | Registered `CommandHandler("admin_broadcast", cmd_admin_broadcast)` |
| `/etc/psvibe/secrets.env` | Added `ADMIN_USER_IDS=6296803251` (Boss only) |

**Verification:** API returns 44 targets ✅, Boss included ✅

---

## 2026-06-18 — Cancel Confirmed Booking Fix + Display Data Fix

### Fix 3: PATCH /api/bookings/{id}/status — Can't Cancel Confirmed Bookings
| Bug | Files | Root Cause | Fix |
|-----|-------|-----------|-----|
| Sale Bot cancel on confirmed bookings returns "already processed" | `psvibe_api_server/app.py` L1400 | `WHERE status='pending'` hardcoded — only allowed cancel from pending | If status='cancelled' → `WHERE status IN ('pending','confirmed','pending_check_in')` |

### Fix 4: Cancel Display Shows "?" Instead of Booking Data
| Bug | Files | Root Cause | Fix |
|-----|-------|-----------|-----|
| Cancel confirmation message shows ? for name, date, time, console | `bot/handlers/booking_flow.py` L492-572 | `_do_cancel_booking` used PATCH response (only `{booking_id, status}`) for display and customer notification | Fetch full booking data BEFORE cancelling via GET; use pre-fetched data for both staff + customer messages |

**Verification:** Both fixes deployed, bots restarted ✅

---

## 2026-06-18 — Session Timer Drift + Console start_time Reset

### Fix 1: Session Timer Drift on Bot Restart
| Bug | Files | Root Cause | Fix |
|-----|-------|-----------|-----|
| Bot restart → timer drifts 2h+ forward | `session_reminder_store.py` | `_end_dt_iso = now + planned_mins` used restart-time `now` instead of original start time | Calculate from stored `end_t` (HH:MM) + dual-layer: restore layer validates drift < 300s |

**Verification:** 5 consecutive restarts, max drift 12s ✅

### Fix 2: _sync_console_status() Resets Active Console start_time
| Bug | Files | Root Cause | Fix |
|-----|-------|-----------|-----|
| Checkin/cancel → sync → console timer resets | `psvibe_api_server/app.py` | `_sync_console_status()` always set `start_time=NOW()` unconditionally | Check if already Active → skip start_time update; only set for newly activated consoles |

### Fix 3: Existing Active Consoles Restored
Same root cause as Fix 2 — verified all active consoles in DB.

### Lessons
- NEVER calculate end_time from `datetime.now()` during restore — use stored `end_t` HH:MM
- `_sync_console_status()` must be idempotent — check current state before overwriting fields
- Dual-layer protection (restore + validate) essential for timer integrity across restarts

---

## 2026-06-16 — Sale Bot Fixes: AYA Pay, Session Reminders, Cleanup

### 1. AYA Pay Missing from Constants
| Bug | File | Root Cause |
|-----|------|-----------|
| AYA Pay disappeared after restart/apply_fixes | `bot/constants.py`, `apply_fixes.py` | `PAY_METHODS` had `[Cash, KPay, WavePay]` only — AYA Pay missing from BOTH files |

### 7. _SESSION_TOTAL_MINS Persistence
| Bug | Files | Root Cause |
|-----|-------|-----------|
| Bot restart → extend reminder shows "Plan: 1 min" | `session_reminder_store.py`, `booking_flow.py` | `_SESSION_TOTAL_MINS` dict was in-memory only, never persisted to `session_reminders.json` |
| **Fix:** Added "AYA Pay" to both `constants.py` PAY_METHODS constant and `apply_fixes.py` injection list |

### 2. Session Extended Reminder Broken (2 bugs)
| Bug | File | Root Cause | Fix |
|-----|------|-----------|-----|
| Extended sessions → no reminder | `booking_flow.py`, `console.py` | `_do_extend()` didn't pass `message_thread_id`; `notify_update()` called without thread_id | Added `message_thread_id` through call chain, `notify_update()` → `kwargs.get("message_thread_id")` |
| Reminder shows "Plan: 1 min" after extend | `session_reminder_store.py` | Missing `_SESSION_TOTAL_MINS` dict; `rem_mins` calculated remaining seconds instead of accumulated total | Added `_SESSION_TOTAL_MINS` tracking + cleanup on session end |
| Stale sessions with no reminder | `session_reminder_store.py`, `fix_reminders.py` | C-06 had `message_thread_id=null`; C-09 had no reminder entry at all | Created `fix_reminders.py` script + manual restore |

### 4. Session Extend — Double /api/ Path → 404
| Bug | File | Root Cause | Fix |
|-----|------|-----------|-----|
| Session extend → API 404, duration not updated | `booking_flow.py` L630 | `_do_extend()` called `_psvibe_post_async("/api/bookings/extend-duration", ...)` — path starts with `/api/` but `_api_call_async()` ALREADY prepends `/api/`, causing URL `{base}/api/api/...` = 404 | Changed path to `"bookings/extend-duration"` (without `/api/` prefix) |

### 3. Cleanup & Security
| Fix | Details |
|-----|---------|
| Stale .bak files (14) cleaned | All `.bak` files left from old auto-fix pipeline removed |
| Dead GSheet batcher disabled | `input_logger.py` background task running every 5s → made no-op; GSheets fully replaced by MySQL |
| Real GSheet fallback code removed | `sales.py` had actual GSheet fallback that interfered with MySQL operations |
| STOCK_PIN removed from `.env.example` | Production PIN leaked to GitHub-tracked file → replaced with `<set_in_secrets>` placeholder |

### 4. Customer Booking — Slot Availability Date Filter
| Bug | File | Root Cause | Fix |
|-----|------|-----------|-----|
| Slot availability always shows "No consoles available" | `psvibe_api_server/app.py` | `GET /api/search-bookings` endpoint had NO `date` parameter — client sends date but API ignores it, SQL returns ALL bookings across ALL dates | Added `date: str = Query("")` to endpoint, dynamic WHERE clause builds `booking_date=%s` filter when date provided; date format normalization for 5 formats

## 2026-06-17 — Session Extend DB Sync & Orphaned Bookings

### Bug: Console Status Not Updated After Session Extend
| Bug | Files | Root Cause | Fix |
|-----|-------|-----------|-----|
| `/status` shows OLD duration after extend | `booking_flow.py` L629-636 | `_do_extend()` used `asyncio.ensure_future(_psvibe_post_async(...))` — fire-and-forget. API error silently swallowed → DB not updated → console status reads old `duration_mins` from DB | Changed to `await _psvibe_post_async(...)` + added staff warning message on failure |

### Cleanup: Orphaned Active Bookings
| Console | Issue | Fix |
|---------|-------|-----|
| C-01, C-03, (empty) | 3 `console_booking` records had `status='Active'` but console was Free — session ended without updating booking to 'Done' | `UPDATE console_booking SET status='Done' WHERE id IN (434,444,463)` |

### Lessons
- `asyncio.ensure_future()` = fire-and-forget = silent failure. If the result matters (DB sync), always `await`.
- When ending a session, verify BOTH `console_status.status='Free'` AND `console_booking.status='Done'`. If only console_status is updated, the orphaned Active booking skews extend/status queries.
- `PAY_METHODS` must be synced in **both** `constants.py` and `apply_fixes.py` — modifying only one causes inconsistency
- Reminder persistence needs `message_thread_id` at EVERY extend point, not just initial booking
- `_SESSION_TOTAL_MINS` is required for proper remaining-time display after session extension
- API endpoint parameters must be checked in ALL 3 places: (1) function signature, (2) SQL WHERE clause, (3) client call — missing any one = silent bug

---

## 2026-06-09 — Pending Bookings Fix + Kora Upgrade Integration

### Bug Fix: Pending Bookings Display
- **SHA:** `d606bed`
- **Files:** `customer_bot/booking.py`
- **Fixes:**
  - `_format_booking_line`: robust `.get()` fallback chain for console type
  - `_parse_booking_datetime_mmt`: handle MySQL datetime/date objects (not just strings)
  - `cmd_cancel_booking`: added `parse_mode=Markdown`, better error result unwrapping
- **API fix:** `app.py` `api_search_bookings`: derive consoleType from console_id instead of hardcoding PS5
- **Verification:** py_compile PASS, API health PASS, all 3 services active

### Kora Upgrade Phase 3 — Fully Integrated
- **Memory Git Backup:** 1,470 files committed (bitbckt to GitHub)
- **Memory Pruner:** 3 exact dupes + 26 similar merged (1.1 KB saved)
- **Memory Index:** Rebuilt (1,146 topics, 47 files)
- **Daily Digest:** Auto-generated for June 9
- **Knowledge Graph:** Rebuilt (54 nodes, 1,423 edges)
- **HEARTBEAT.md:** All Phase 3 tools added to ~4h routine
- **MEMORY.md:** Index updated with Phase 3 references

---

## 2026-06-03 — MEGA FIX DAY (15+ bugs)

### Session 1: Core Sales Bot + Customer Bot
| Bug | SHA/File | Root Cause |
|-----|----------|------------|
| Sales Daily stuck (member) | `__init__.py` lines 95,496,650 | Missing `await` on async calls |
| Food Menu empty | `settings_config` MySQL | `food_costs` was `{}` (empty) |
| Customer Bot cancelled bookings | `handlers.py`, `booking.py` | No status filter in welcome banner |

### Session 2: Web Dashboard
| Fix | Files | What |
|-----|-------|------|
| Sidebar on all pages | `AppLayout.vue` | Created reusable layout wrapper |
| MySQL data loading | 6 views | Changed `axios.get()` → `apiClient` (JWT) |
| Food Stock dedup | API query | `WHERE category='Food'` filter |
| Promotions dedup | API query | INNER JOIN + GROUP BY |
| Food Stock Split (4 pages) | Vue views | Menu Register, Stock In, Stock Out, Inventory |
| Menu Register save | API + Vue | Fixed `rowcount`→`lastrowid`, removed hardcoded filter |
| Stock In payment | MySQL + API + Vue | Added payment_method, paid_by, staff_name fields |

### Session 3: 3 More Sales Bot Bugs
| Bug | File | Root Cause | Fix |
|-----|------|-----------|-----|
| Sales Daily STILL stuck | `__init__.py` | `_replit_get_async` double-unwrapping API data | Dict-filtering + list guards |
| Gift member balance 1200→600 | `sales.py` | Redundant `api_add_topup` after `members/register` | Removed duplicate call |
| 90k purchase spam | `sales.py` | No max-minutes validation | `MAX_SESSION_MINS = 1440` |

### Session 4: Booking Timeout
| Bug | File | Root Cause | Fix |
|-----|------|-----------|-----|
| No cancel notification | `auto_cancel_no_shows.py` | Wrong env var names → 401 errors | Fixed variable names + Telegram notify |
| Expired→confirmed display | `booking.py` | No time-based filtering | 15min grace period + expired status |

### Session 5: Console + Game Library
| Bug | File | Root Cause | Fix |
|-----|------|-----------|-----|
| Console Status not showing | `__init__.py` | `_list_keywords` had `"consoles"` (API returns `"console"`) | Changed 3 locations |
| Console Status message too long | `commands.py` | All 37 games listed → 6650 chars | 3 games + "+34 more" |
| Game Library missing imports | `ginst.py`, `ssd_disc.py`, `games.py` | Circular import issues | Fixed import chains |
| Game Library wrong API params | `api_client.py`, `__init__.py` | `row_num` instead of `game_title` | Fixed param names |
| Console/Games display v2 | `console.py`, `games.py` | Display redesign | Simplified + pagination + search |

### Session 6: Sale Completion Bugs
| Bug | File | Root Cause | Fix |
|-----|------|-----------|-----|
| Coupon code not generated | `console.py` | Double-unwrap `result.get("data")` → `None` | Changed to `result` |
| Food stock not deducted | `app.py` | No `stock-out` API endpoint existed | Added `POST /api/inventory/stock-out` |
| Wallet balance not deducted | `app.py`, `sales.py` | Google Sheets only, no MySQL update | Added `POST /api/wallet/deduct` + sales.py call |
| Sale Daily promotion list error | (same stack) | Stock/wallet deduction APIs not yet tested | Endpoints added |

### Session 7: Food Data Path
| Bug | File | Root Cause | Fix |
|-----|------|-----------|-----|
| Sale Daily food data not available | `app.py`, `__init__.py` | API queried `category='Food'` (items are `category='Beverages'`) | Changed to `IN ('Food','Beverages')` |

### Session 8: Layout Restructure + Session Start/End
| Bug | File | Root Cause | Fix |
|-----|------|-----------|-----|
| Session Start/End broken | `sales.py` | Missing imports for 4 functions (NameError) | Added direct + lazy imports |
| Menu too many buttons | `console.py`, `games.py`, `app.py` | Game Add/Delete/Discs/SSD in bot | Removed → Web only; moved Install under Consoles |

## 2026-06-06 — Food Menu Fix (Customer Bot)

### Bug: 🍕 Food Menu Not Showing
| Attempt | Commit | Root Cause Still Present |
|---------|--------|--------------------------|
| 1 | `69ff077` | BTN_FOOD not in `_bk_intercept_menu` + API unwrap logic wrong + Unicode escape corruption |
| 2 | (no commit) | API unwrap logic still wrong |
| 3 | (no commit) | Unicode escape corruption + API unwrap logic |
| 4 | (no commit) | API unwrap logic still used `resp.get("success")` |
| **FINAL** | `1dd1be1` | ✅ ALL fixed |

### Changes Made
| File | What |
|------|------|
| `customer_bot/handlers.py` | `_bk_intercept_menu`: Added BTN_FOOD, BTN_BALANCE, BTN_REFER to menu_actions dict |
| `customer_bot/handlers.py` | `cmd_food_menu`: Rewrote — removed `resp.get("success")`, removed `resp.get("data")`, clean English loading text |
| `customer_bot/handlers.py` | Flexible text matching: removed "menu" (too broad) |
| `customer_bot/main.py` | Removed duplicate MessageHandler for BTN_FOOD |

### Root Causes
1. **`_bk_intercept_menu` missing BTN_FOOD** — booking conversation silently ate the button
2. **API auto-unwrap mismatch** — `_api._api_get()` auto-unwraps `{success,data}` → raw `{items}`, but code checked `resp.get("success")` / `resp.get("data")` → always failed
3. **Unicode escape corruption** — Auto-fix pipeline corrupted `\u` sequences → garbled Burmese text

### Lesson
- When `_api_get` auto-unwraps, DON'T check `success`/`data` — just use the response directly
- The `_bk_intercept_menu` pattern must include EVERY button that should work during booking
- Multiple fix attempts = root cause was layered. Fix protocol should check ALL layers at once.

---

## 2026-06-02

### Booking ↔ Console Status Link
- **SHA:** `941d0a5`
- **Files:** `admin_bookings.py`, `booking_flow.py`
- **Changes:** Console_Booking sheet auto-update (Scheduled/Done rows)
- **Flow:** Confirm → "Scheduled" | Cancel/No-show → "Done" | Session start → cleanup

### Booking Confirm → Notify Customer
- **SHA:** `6e3c556`
- **Files:** `admin_bookings.py`
- **Changes:** Telegram notification to customer when booking confirmed
- **Burmese message:** "မင်္ဂလာပါ... သင်၏ Booking ကို အတည်ပြုပြီးပါပြီ"

### Customer Bot "My Booking" Fix
- **SHA:** `6e3c556`
- **Files:** `customer_bot/booking.py`
- **Changes:** Friendly Burmese message when no bookings; API error handling

### Session Lock Timeout Permanent Fix
- **Files:** `openclaw.json`, `memory/lock_monitor.py`
- **Changes:** acquireTimeoutMs 60s→300s, maintenance enforce+300mb cap

## 2026-06-16 — Fix 8: Food Cart Not Loading in Session End Voucher
- **Bug:** Food note items saved to food_cart table but never loaded in voucher at session end
- **Root cause:** `step_end_session()` in `console.py` — after `end_booking_async()` changed status to 'Done', the second lookup for `_linked_bk_id` used a status filter ('confirmed','arrived','in_use','Active') that excluded 'Done'. Result: empty booking_id passed to `launch_session_sale()`, food cart never fetched.
- **Fix:** Use `bk_id` from console_status `booking_id` directly (already found before end_booking). Fallback to member lookup only if `bk_id` was empty.
- **File:** `bot/handlers/console.py` — `step_end_session()`
- **Status:** ✅ Deployed + verified syntax OK

## 2026-06-16 — Fix 9: Food Cart Release Flags + Stock Out (19:33 UTC)

### Bug 1: `context.user_data.clear()` kills food-cart release flags
| Bug | File | Root Cause | Fix |
|-----|------|-----------|-----|
| Food cart items never released at sale confirm | `bot/handlers/sales.py` L1395-1399 | `step_sale_confirm()` calls `context.user_data.clear()` BEFORE `_sale_bg()` closure reads `_food_cart_loaded` and `_stock_held` flags → release API never fires | Save flags to local vars before `clear()`, use in closure |

### Bug 2: Food cart items skip stock_out entirely
| Bug | File | Root Cause | Fix |
|-----|------|-----------|-----|
| `food-cart/release` never called → no stock_out records | `bot/handlers/sales.py` | Items with `from_cart=True` skip `api_add_stock_out()`. The `food-cart/release` API handles stock_out, but Bug 1 prevented it from running | Bug 1 fix ensures release API runs, which records stock_out |
- **Files:** `bot/handlers/sales.py`
- **Status:** ✅ Deployed + bot restarted (PID 136936)

## 2026-06-16 — Fix 10: `calc_duration()` Ignores Extended Minutes (20:09 UTC)

### Bug: Session end voucher shows wrong game_amt (missing extended minutes)
| Bug | File | Root Cause | Fix |
|-----|------|-----------|-----|
| Extended minutes not reflected in voucher game_amt | `bot/handlers/console.py` | `step_end_session()` calls `calc_duration(start_t)` which uses wall-clock elapsed time instead of `_SESSION_TOTAL_MINS`. Extended minutes tracked in dict but never read at session end | Modified `step_end_session()` to read `_SESSION_TOTAL_MINS` and use it as session duration when available |
- **Files:** `bot/handlers/console.py` — `step_end_session()`
- **Status:** ⚠️ Edit failed on first try, needs manual verification
