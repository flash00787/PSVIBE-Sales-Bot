# 📋 Fix History

> Recent major fixes. Full daily logs at `memory/YYYY-MM-DD.md`

## 2026-06-16 — Sale Bot Fixes: AYA Pay, Session Reminders, Cleanup

### 1. AYA Pay Missing from Constants
| Bug | File | Root Cause |
|-----|------|-----------|
| AYA Pay disappeared after restart/apply_fixes | `bot/constants.py`, `apply_fixes.py` | `PAY_METHODS` had `[Cash, KPay, WavePay]` only — AYA Pay missing from BOTH files |
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

### Lessons
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
