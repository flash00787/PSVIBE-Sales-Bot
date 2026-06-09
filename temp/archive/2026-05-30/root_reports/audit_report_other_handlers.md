# DEEP AUDIT: Sales Bot — Remaining Handler Files
## VPS: 5.223.81.16 | Date: 2026-05-28

---

## 1. broadcast.py (144 lines)

### Functions
| Function | Type | Async | Handler Registered? |
|---|---|---|---|
| `cmd_broadcast` | CommandHandler /broadcast | ✅ async | ✅ app.py:78, 348, 400, 434 |
| `cmd_staff_kpi` | CommandHandler /kpi | ✅ async | ✅ app.py:77, 347, 399, 433 |

### Issues
- **🐛 BLOCKING I/O in async handler (#1):** `cmd_staff_kpi` calls `_replit_get("sheets/report-data")` and `_replit_get("sheets/staff-breakdown")` synchronously. `_replit_get` does HTTP via `urllib.request.urlopen` which blocks the event loop. Should wrap with `await asyncio.to_thread(_replit_get, ...)`.
- **⚠️ Code organization:** `cmd_staff_kpi` is a KPI/report handler living in `broadcast.py`. Should ideally be in `reports.py`.

### API Calls
- `_replit_get("bookings/broadcast-targets")` → response: `{"telegram_ids": [...]}` ✅
- `_replit_get("sheets/report-data")` → response: `{"summary": {...}, "stock_today": {...}}` ✅
- `_replit_get("sheets/staff-breakdown")` → response: `{"staff": {...}}` ✅

### Error Handling
- Broadcast: try/except per recipient ✅
- API failures: guarded with `if not data:` ✅
- No stubs/NotImplementedError ✅

### Import Style
- `from bot import *` ✅ (line 3)
- Module docstring on lines 1-2 ✅

---

## 2. commands.py (43 lines)

### Functions
| Function | Type | Async | Handler Registered? |
|---|---|---|---|
| `cmd_cancel` | CommandHandler /cancel | ✅ async | ✅ app.py:64, 328, 389 |
| `cmd_topup` | CommandHandler /topup | ✅ async | ✅ app.py:72, 338, 395 |
| `cmd_member_mgmt` | CommandHandler /member | ✅ async | ✅ app.py:70, 336, 393 |
| `cmd_check_member` | CommandHandler /check | ✅ async | ✅ app.py:73, 339, 396 |
| `cmd_newmember` | CommandHandler /newmember | ✅ async | ✅ app.py:71, 337, 394 |
| `cmd_ranks` | CommandHandler /ranks | ✅ async | ✅ app.py:74, 340, 397 |

### Issues
- **✅ Clean.** All functions are simple delegates to other handlers. No API calls, no blocking I/O.

### Import Style
- `from bot import *` ✅ (line 3)
- Module docstring on lines 1-2 ✅

---

## 3. help.py (85 lines)

### Functions
| Function | Type | Async | Handler Registered? |
|---|---|---|---|
| `cmd_version` | CommandHandler /version | ✅ async | ✅ app.py:66, 332, 391 |
| `cmd_help` | CommandHandler /help | ✅ async | ✅ app.py:65, 331, 390 |
| `error_handler` | error_handler | ✅ async | ✅ app.py:22 + add_error_handler |

### Issues
- **✅ Clean.** Error handler correctly discriminates NetworkError/TimedOut (warning) vs Conflict (warning) vs other (error with exc_info). No API calls.

### Import Style
- `from bot.handlers import *` ✅ (line 3)
- Module docstring on lines 1-2 ✅

---

## 4. notify.py (72 lines)

### Functions
| Function | Type | Async | Handler Registered? |
|---|---|---|---|
| `_notify_customer` | Utility (customer notif) | ❌ sync | N/A — called via `asyncio.to_thread` from sales.py:1226, admin_bookings.py:224, booking_flow.py:139/475, booking.py:470 |
| `get_customer_chat_id` | Utility (chat lookup) | ❌ sync | N/A — called via `asyncio.to_thread` from sales.py:1207, booking_flow.py:123 |
| `_check_low_balance_alert` | Coroutine (fire-and-forget) | ✅ async | N/A — spawned via `asyncio.create_task` from sales.py:1226 |

### Issues
- **⚠️ Messy docstring (#2):** Line 2 `from bot import *` is INSIDE the docstring (not executed). Line 4 has the real `from bot import *`. Functionally works but is confusing.
  ```
  Line 1: """PS VIBE Bot — Handler module.
  Line 2: from bot import *       ← Inside docstring! Not executed
  Line 3: """
  Line 4: from bot import *       ← Real import
  ```

### API Calls
- `get_customer_chat_id` calls `_replit_get(f"bookings?memberId={member_id}")` ✅
- `_notify_customer` calls Telegram Bot API directly via `urllib.request` ✅

### Error Handling
- All three functions have try/except with logging ✅
- No stubs/NotImplementedError ✅

---

## 5. referral.py (136 lines)

### Functions
| Function | Type | Async | Handler Registered? |
|---|---|---|---|
| `prompt_referral_code` | Prompt (flow entry) | ✅ async | N/A — called from members.py:103 |
| `step_referral_code` | MessageHandler | ✅ async | ✅ app.py:325 (REFERRAL_CODE state) |

### Issues
- **🐛 Import before docstring (#3):** Line 1 is `from bot import *`, line 2 starts the docstring. The docstring becomes an orphaned string literal.
- **🐛 BLOCKING I/O (#4):** `prompt_referral_code` calls `fetch_referral_code(member_id)` synchronously — this does HTTP (API call) + gspread fallback. Should wrap with `await asyncio.to_thread(fetch_referral_code, member_id)`.
- **🐛 BLOCKING I/O (#5):** `step_referral_code` calls `member_sh.get_all_values()` synchronously at line 91. This is a blocking Google Sheets API call in an async handler. Should wrap with `await asyncio.to_thread(member_sh.get_all_values)`.
- **⚠️ Legacy pattern:** Uses `asyncio.get_event_loop().run_in_executor(None, ...)` instead of the modern `asyncio.to_thread()`.

### API Calls
- `fetch_referral_code(member_id)` → HTTP API + gspread fallback ✅
- `save_referral_code(member_id, code)` → gspread write ✅
- `member_sh.get_all_values()` → gspread read ✅
- `fetch_members()` → gspread/API read ✅

### Error Handling
- Try/except around uniqueness check ✅
- Save result checked with `if ok:` ✅
- Member existence validated before save ✅

---

## 6. discount.py (435 lines)

### Functions
| Function | Type | Async | Handler Registered? |
|---|---|---|---|
| `prompt_discount` | Prompt (flow entry) | ✅ async | N/A — called from sales.py:758, 771 |
| `prompt_promo_select` | Prompt (promo picker) | ✅ async | N/A — called from step_discount |
| `step_promo_select` | MessageHandler | ✅ async | ✅ app.py:154 (PROMO_SELECT state) |
| `step_bundle_foc` | MessageHandler | ✅ async | ✅ app.py:155 (BUNDLE_FOC state) |
| `step_discount` | MessageHandler | ✅ async | ✅ app.py:153 (DISCOUNT state) |

### Issues
- **🐛 Import before docstring (#6):** Same as referral.py — `from bot import *` on line 1 before docstring.
- **⚠️ Missing logger (#7):** Unlike all other handler modules, discount.py does NOT create `logger = logging.getLogger(__name__)`. This means warning/error logs from discount.py won't have proper module attribution.
- **⚠️ Duplicate `from datetime import...` (#8):** discount.py imports `from datetime import datetime, timezone, timedelta` at line 8, but `from bot import *` already makes `datetime` available (bot/__init__.py imports it).

### API Calls
- `fetch_promotions_cached()` — via `asyncio.to_thread` ✅
- `fetch_base_rate()` — synchronous call, called directly (line 20) in `prompt_discount`. This does HTTP/gspread but is a simple value fetch. Minor, but could also use `asyncio.to_thread`.

### Error Handling
- Manual discount validation: range checks ✅
- Promotion matching with fallback ✅
- Wallet session discount → bonus mins conversion ✅
- Selected promotion validation ✅

---

## Summary of Issues Found

| # | Severity | File | Issue |
|---|---|---|---|
| 1 | 🐛 MEDIUM | broadcast.py:64,97 | `_replit_get` blocking calls in async `cmd_staff_kpi` |
| 2 | ⚠️ LOW | notify.py:1-4 | Docstring contains `from bot import *` (cosmetic) |
| 3 | ⚠️ LOW | referral.py:1-3 | Import before module docstring |
| 4 | 🐛 MEDIUM | referral.py:24 | `fetch_referral_code` blocking call in async `prompt_referral_code` |
| 5 | 🐛 MEDIUM | referral.py:91 | `member_sh.get_all_values()` blocking call in async `step_referral_code` |
| 6 | ⚠️ LOW | discount.py:1-3 | Import before module docstring |
| 7 | ⚠️ LOW | discount.py | Missing `logger = logging.getLogger(__name__)` |
| 8 | ⚠️ TRIVIAL | discount.py:8 | Duplicate `from datetime import...` (comes from `bot import *` anyway) |

## Handler Registration Audit

All handler functions have matching `add_handler` registrations in `app.py`:
- ✅ `cmd_broadcast` — registered at lines 78, 348, 400, 434
- ✅ `cmd_staff_kpi` — registered (in other audit)
- ✅ `cmd_cancel` — registered at lines 64, 328, 389
- ✅ `cmd_topup` — registered at lines 72, 338, 395
- ✅ `cmd_member_mgmt` — registered at lines 70, 336, 393
- ✅ `cmd_check_member` — registered at lines 73, 339, 396
- ✅ `cmd_newmember` — registered at lines 71, 337, 394
- ✅ `cmd_ranks` — registered at lines 74, 340, 397
- ✅ `cmd_version` — registered at lines 66, 332, 391
- ✅ `cmd_help` — registered at lines 65, 331, 390
- ✅ `error_handler` — registered at line 22 + add_error_handler at 55
- ✅ `step_referral_code` — registered at line 325 (REFERRAL_CODE state)
- ✅ `step_discount` — registered at line 153 (DISCOUNT state)
- ✅ `step_promo_select` — registered at line 154 (PROMO_SELECT state)
- ✅ `step_bundle_foc` — registered at line 155 (BUNDLE_FOC state)
- ✅ `_notify_customer`, `get_customer_chat_id`, `_check_low_balance_alert` — utility functions, no handler registration needed
- ✅ `prompt_referral_code` — called from members.py:103, no direct handler registration needed
- ✅ `prompt_discount` — called from sales.py:758/771, no direct handler registration needed
- ✅ `prompt_promo_select` — called from step_discount, no direct handler registration needed

## Stub/NotImplementedError Audit
- ✅ No stubs or NotImplementedError in any of the 6 files

## Async/Await Audit
- All handler functions are properly `async def` ✅
- All `await` calls are on awaitable objects ✅
- `asyncio.to_thread` used correctly for blocking calls in discount.py ✅

---

## Fixes Applied

1. **broadcast.py:62-68, 96-98** — Wrapped `_replit_get` in `await asyncio.to_thread()`
2. **notify.py:1-4** — Fixed docstring (removed `from bot import *` from inside)
3. **referral.py:1-3** — Moved `from bot import *` after module docstring
4. **referral.py:24** — Changed `fetch_referral_code(member_id)` to `await asyncio.to_thread(fetch_referral_code, member_id)`
5. **referral.py:91** — Changed `member_sh.get_all_values()` to `await asyncio.to_thread(member_sh.get_all_values)`
6. **discount.py:1-3** — Moved `from bot import *` after module docstring
7. **discount.py** — Added `logger = logging.getLogger(__name__)`
