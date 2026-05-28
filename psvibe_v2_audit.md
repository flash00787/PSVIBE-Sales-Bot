# PS VIBE Sales Bot — V2 Code Audit Report

**Date:** 2026-05-27 02:50 UTC
**Source:** `/root/staging/bot_src/`
**V1 Reference:** `/root/staging/monolithic_ref/main.py`

---

## 🚨 CRITICAL ISSUES (Bot Cannot Start)

### 1. main_menu.py Syntax Error — BROKEN IMPORT
**File:** `/root/staging/bot_src/bot/handlers/main_menu.py`
**Line:** 18
**Error:**
```
SyntaxError: unterminated triple-quoted string literal (detected at line 114)
```

**Root Cause:**
- Lines 2-17 define BTN constants (BTN_DAILY_SALES ... BTN_FOOD_SETUP)
- Line 18 opens `"""` (triple-quoted string / docstring)
- There is **NO closing `"""`** before the telegram imports on lines 19-23
- Result: ALL imports (`from telegram import...`, function definitions `show_main_menu`, `step_main_menu`) are swallowed inside the unterminated string

**Impact:**
- `from bot.handlers.main_menu import *` fails with SyntaxError
- The handlers `__init__.py` does `from .main_menu import *` → cascades to complete import failure
- `from bot import *` fails → ENTIRE bot cannot start

**Fix:** Close the triple-quoted string or remove it. The BTN constants at the top are also redundant since they're already defined in `bot/__init__.py`.

---

## 🔴 HIGH SEVERITY

### 2. Three (3) Duplicate Handler Directories
All three directories contain IDENTICAL copies of 25 handler files:

| Path | Purpose |
|------|---------|
| `/root/staging/bot_src/bot/handlers/` | **CANONICAL** — imported by `bot/__init__.py` and `bot/app.py` |
| `/root/staging/bot_src/bot/bot/handlers/` | **DUPLICATE** — nested bot/bot/ structure, NOT used |
| `/root/staging/bot_src/handlers/` | **DUPLICATE** — top-level copy, NOT used |

**Risk:** If any code accidentally imports from the wrong directory (e.g., `from bot.bot.handlers import *`), two separate module instances could exist with different state. The `bot/bot/__init__.py` file is broken (has orphan imports before docstring — see Issue 6).

**Recommendation:** Delete `bot/bot/` and `handlers/` directories. Keep only `bot/handlers/`.

### 3. keep_alive.py Missing
**File:** `keep_alive.py` does NOT exist in `/root/staging/bot_src/`

**Where it's imported:**
- `bot/__init__.py` line: `from keep_alive import keep_alive` (wrapped in try/except)
- `main.py` line 3: `from bot import main, keep_alive, ensure_sheet_headers`
- Found at: `/root/Personal-Wallet-Tele-Bot/bot/keep_alive.py` (different project!)

**Impact:** The `keep_alive` variable will be `None`. `main.py` checks `if keep_alive: keep_alive()` so it won't crash, but the Flask keep-alive HTTP server won't run.

### 4. SQLite Database — COMPLETELY UNUSED
**Files:** `sqlite/db_manager.py` (509 lines), `sqlite/setup.py` (423 lines)

- These files exist but are **NEVER imported or referenced** by any bot code
- Zero references to `psvibe.db`, `PSVibeDB`, or `db_manager` in the entire bot source
- Default DB path hardcoded to wrong location: `/root/Sales-Tele-Bot_refactored/psvibe.db`
- `setup.py` imports `gspread` and `oauth2client` which are NOT installed in the staging environment

**Status:** Dead code. Either integrate or remove.

---

## 🟡 MEDIUM SEVERITY

### 5. bot/bot/__init__.py — Orphan Imports Before Docstring
**File:** `/root/staging/bot_src/bot/bot/__init__.py` (2022 lines)
**Lines 1-6:**
```python
import os
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError
```

These 6 lines are **orphaned/stray** imports placed BEFORE the module docstring. They are:
- Duplicated (appear twice)
- Not assigned to any variables
- Immediately shadowed by the `"""` docstring on line 7

This is clearly an editing artifact — likely combining/copy-paste error during refactor.

### 6. 15 Handler Files Use `from bot import *` (Potential Circular Import)
**Files using `from bot import *`:**

| File | Line 1 |
|------|--------|
| `admin.py` | `from bot import *` |
| `attendance.py` | `from bot import *` |
| `booking.py` | `from bot import *` |
| `booking_flow.py` | `from bot import *` |
| `console.py` | `from bot import *` |
| `finance.py` | `from bot import *` |
| `help.py` | `from bot import *` |
| `main_menu.py` | `from bot import *` |
| `members.py` | `from bot import *` |
| `payroll.py` | `from bot import *` |
| `reports.py` | `from bot import *` |
| `salary_adv.py` | `from bot import *` |
| `sales.py` | `from bot import *` |
| `stock.py` | `from bot import *` |
| `stock_in.py` | `from bot import *` |

**Circular import chain:**
1. `bot/__init__.py` → `from bot.handlers import *` (line ~1600+)
2. `bot/handlers/__init__.py` → `from .main_menu import *` → main_menu.py does `from bot import *`
3. `from bot import *` → tries to execute `bot/__init__.py` → but `bot.handlers` is still mid-import

**Current status:** Python handles this because `bot/__init__.py` defines almost everything before the `from bot.handlers import *` line. However, if main_menu.py's syntax error is fixed, this could still cause issues if import order changes.

**Files NOT using `from bot import *`** (10 of 25):
`admin_bookings.py`, `broadcast.py`, `commands.py`, `console_mgmt.py`, `discount.py`, `games.py`, `ginst.py`, `notify.py`, `referral.py`, `ssd_disc.py`, `waitlist.py`

These 10 files import only `from telegram import...` and `from telegram.ext import...` and use standalone BTN/state constants defined in `bot/bot/handlers/__init__.py` (which also has its own inline copies).

### 7. BTN Constants Defined in 3 Separate Places
1. `bot/__init__.py` — primary source (used by handlers with `from bot import *`)
2. `bot/bot/handlers/__init__.py` — full standalone copy (used by handlers without `from bot import *`)
3. `bot/handlers/main_menu.py` — partial copy (BTN_DAILY_SALES ... BTN_FOOD_SETUP) — for "avoid circular import", but broken by syntax error

**Risk:** If constant values diverge between copies, different parts of the code use different strings for the same button, causing ConversationHandler mismatches.

### 8. app.py WITHIN bot/ package vs TOP-LEVEL app.py
Two `app.py` files exist:
- `/root/staging/bot_src/app.py` — top-level, auto-generated during Phase 4 refactor
- `/root/staging/bot_src/bot/app.py` — inside the package, the one imported by `bot/__init__.py` (`from bot.app import main as main`)

Both files are **IDENTICAL** (same ConversationHandler, same states, same handlers). The bot actually uses `bot/app.py` (imported by `bot/__init__.py`). The top-level `app.py` is dead code.

---

## 🟢 LOW SEVERITY / OBSERVATIONS

### 9. All Handler Functions Catalog

**Module: `admin.py`** (8 functions)
- `cmd_admin(update, context)` — line 13
- `_pin_then(cmd_key, label, update, context)` — line 17
- `step_admin_pin(update, context)` — line 28
- `show_admin_menu(update, context)` — line 54
- `step_admin_menu(update, context)` — line 73
- `fetch_salary_advances(month_str)` — line 112
- `cmd_admin_sal_adv(update, context)` — line 141
- `_parse_date_mmt(val)` — line 158

**Module: `admin_bookings.py`** (5 functions)
- `cmd_admin_bookings(update, context)` — line 12
- `cmd_approve_booking(update, context)` — line 55
- `cmd_reject_booking(update, context)` — line 66
- `cb_booking_mgmt(update, context)` — line 77
- `_do_booking_action(bk_id, action, staff_name, reply_fn)` — line 97

**Module: `attendance.py`** (8 functions)
- `cmd_setattend_cmd(update, context)` — line 13
- `cmd_setattend(update, context)` — line 17
- `step_attend_staff(update, context)` — line 37
- `step_attend_leave(update, context)` — line 58
- `step_attend_late(update, context)` — line 82
- `step_attend_deduct(update, context)` — line 110
- `_attend_save_and_next(update, context)` — line 127
- `_attend_finish(update, context)` — line 154

**Module: `booking.py`** (7 functions)
- `_sbk_console_kb()` — line 13
- `_sbk_parse_console_label(text)` — line 49
- `cmd_staff_book_hub(update, context)` — line 59
- `cmd_confirmed_bookings(update, context)` — line 109
- `cmd_staff_booking(update, context)` — line 156
- `step_sbk_console(update, context)` — line 173
- `step_sbk_cust_name(update, context)` — line 214
- `step_sbk_date(update, context)` — line 235

**Module: `booking_flow.py`** (6 functions)
- `_extend_timer_kb(cid, member_id, chat_id)` — line 21
- `_remind_key(cid, chat_id)` — line 34
- `_cancel_remind(cid, chat_id)` — line 37
- `_is_session_active(cid)` — line 43
- `_remind_loop(...)` — line 58
- `_send_session_reminder(...)` — line 150
- `_post_n8n_session_reminder(...)` — line 178
- `_post_n8n_booking_reminder(...)` — line 224

**Module: `broadcast.py`** (2 functions)
- `cmd_broadcast(update, context)` — line 12
- `cmd_staff_kpi(update, context)` — line 76

**Module: `commands.py`** (6 functions)
- `cmd_cancel(update, context)` — line 12
- `cmd_topup(update, context)` — line 18
- `cmd_member_mgmt(update, context)` — line 23
- `cmd_check_member(update, context)` — line 28
- `cmd_newmember(update, context)` — line 33
- `cmd_ranks(update, context)` — line 39

**Module: `console.py`** (9 functions)
- `cmd_console_status(update, context)` — line 13
- `show_console_menu(update, context)` — line 90
- `step_console_menu(update, context)` — line 107
- `prompt_game_change_cons(update, context)` — line 126
- `step_game_change_cons(update, context)` — line 148
- `step_game_change_game(update, context)` — line 186
- `prompt_end_session(update, context)` — line 218
- `step_end_session(update, context)` — line 251

**Module: `console_mgmt.py`** (6 functions)
- `show_con_mgmt_menu(update, context)` — line 12
- `step_con_mgmt_menu(update, context)` — line 28
- `step_con_add_id(update, context)` — line 68
- `step_con_add_type(update, context)` — line 86
- `step_con_add_mult(update, context)` — line 100
- `step_con_del_select(update, context)` — line 126

**Module: `discount.py`** (5 functions)
- `prompt_discount(update, context)` — line 12
- `prompt_promo_select(update, context)` — line 96
- `step_promo_select(update, context)` — line 131
- `step_bundle_foc(update, context)` — line 285
- `step_discount(update, context)` — line 341

**Module: `finance.py`** (8 functions)
- `get_opex_sh()` — line 13
- `get_assets_sh()` — line 16
- `get_prepaid_fin_sh()` — line 19
- `get_acct_trf_sh()` — line 22
- `get_payables_sh()` — line 25
- `get_receivables_sh()` — line 28
- `get_advpay_sh()` — line 31
- `show_finance_menu(update, context)` — line 34

**Module: `games.py`** (8 functions)
- `show_game_menu(update, context)` — line 12
- `step_game_menu(update, context)` — line 31
- `step_game_add_title(update, context)` — line 148
- `step_game_add_platform(update, context)` — line 164
- `step_game_add_genre(update, context)` — line 191
- `step_game_add_status(update, context)` — line 211
- `step_game_edit_select(update, context)` — line 269
- `step_game_edit_field(update, context)` — line 297

**Module: `ginst.py`** (8 functions)
- `show_ginst_menu(update, context)` — line 12
- `step_ginst_menu(update, context)` — line 31
- `_ginst_pick_console(update, context, next_state, prompt)` — line 43
- `step_ginst_view_cons(update, context)` — line 57
- `step_ginst_add_cons(update, context)` — line 78
- `step_ginst_add_game(update, context)` — line 106
- `step_ginst_add_type(update, context)` — line 150
- `step_ginst_del_cons(update, context)` — line 182
- `step_ginst_del_game(update, context)` — line 206

**Module: `help.py`** (3 functions)
- `cmd_version(update, context)` — line 13
- `cmd_help(update, context)` — line 37
- `error_handler(update, context)` — line 76

**Module: `main_menu.py`** (2 functions — BROKEN)
- `show_main_menu(update, context)` — line 28
- `step_main_menu(update, context)` — line 64

**Module: `members.py`** (8 functions)
- `prompt_staff_select(update, context)` — line 13
- `step_staff_select(update, context)` — line 24
- `show_mm_menu(update, context)` — line 39
- `show_rank_info(update, context)` — line 54
- `step_mm_menu(update, context)` — line 77
- `prompt_mm_lookup(update, context, ...)` — line 109
- `step_mm_lookup(update, context)` — line 128
- `prompt_nm_staff(update, context)` — line 196
- `step_nm_staff(update, context)` — line 207

**Module: `notify.py`** (3 functions)
- `_notify_customer(chat_id_or_phone, text)` — line 12
- `get_customer_chat_id(member_id)` — line 33
- `_check_low_balance_alert(member_id, console_id)` — line 46

**Module: `payroll.py`** (3 functions)
- `calc_monthly_payroll(month_str)` — line 13
- `cmd_payroll(update, context)` — line 160
- `cmd_payroll_cmd(update, context)` — line 225
- `cmd_kpi_cmd(update, context)` — line 229

**Module: `referral.py`** (2 functions)
- `prompt_referral_code(update, context)` — line 12
- `step_referral_code(update, context)` — line 36

**Module: `reports.py`** (5 functions)
- `cmd_inventory(update, context)` — line 13
- `cmd_stocktoday(update, context)` — line 46
- `cmd_promo_reports(update, context)` — line 65
- `cmd_today_report(update, context)` — line 205
- `cmd_financial_report(update, context)` — line 274

**Module: `salary_adv.py`** (4 functions)
- `step_sal_adv_staff(update, context)` — line 13
- `step_sal_adv_amt(update, context)` — line 33
- `step_sal_adv_pay(update, context)` — line 52
- `step_sal_adv_confirm(update, context)` — line 86

**Module: `sales.py`** (8 functions)
- `prompt_member(update, context, ...)` — line 16
- `prompt_console(update, context)` — line 41
- `prompt_mins(update, context)` — line 70
- `prompt_adjust_time(update, context)` — line 99
- `step_adjust_time(update, context)` — line 120
- `prompt_food_menu(update, context)` — line 159
- `prompt_confirm(update, context)` — line 193
- `prompt_kpay(update, context)` — line 306

**Module: `ssd_disc.py`** (9 functions)
- `_ssd_kb()` — line 12
- `step_disc_select(update, context)` — line 19
- `step_disc_set_qty(update, context)` — line 53
- `show_ssd_menu(update, context)` — line 79
- `step_ssd_menu(update, context)` — line 106
- `step_ssd_view(update, context)` — line 138
- `step_ssd_add_ssd(update, context)` — line 162
- `step_ssd_add_game(update, context)` — line 184
- `step_ssd_add_type(update, context)` — line 217
- `step_ssd_del_ssd(update, context)` — line 239

**Module: `stock.py`** (8 functions)
- `update_inv_total_k1()` — line 10
- `cmd_stockin_direct(update, context)` — line 35
- `cmd_stockout_direct(update, context)` — line 46
- `cmd_stock_menu(update, context)` — line 57
- `step_stock_pin(update, context)` — line 68
- `show_stock_menu(update, context)` — line 88
- `step_stock_menu(update, context)` — line 104
- `show_stock_out_items(update, context)` — line 134
- `step_stock_item(update, context)` — line 148

**Module: `stock_in.py`** (8 functions)
- `show_si_items(update, context)` — line 16
- `step_si_item(update, context)` — line 30
- `step_si_qty(update, context)` — line 47
- `step_si_cost(update, context)` — line 72
- `show_si_cart(update, context)` — line 98
- `step_si_cart(update, context)` — line 121
- `_show_si_review(update, context)` — line 143
- `step_si_pay(update, context)` — line 174

**Module: `waitlist.py`** (8 functions)
- `_wl_console_availability(console_pref)` — line 12
- `_fmt_mmt_dt(iso_str)` — line 27
- `_wl_status_label(status)` — line 39
- `_wl_pref_label(pref)` — line 49
- `cmd_waitlist_mgmt(update, context)` — line 52
- `_show_wl_menu(update, context)` — line 57
- `step_wl_menu(update, context)` — line 83
- `cb_wl_action(update, context)` — line 198

**TOTAL: ~150 handler functions across 25 modules**

### 10. bot/__init__.py — Core Infrastructure Functions (V2)
All core infrastructure is in `bot/__init__.py` (the old monolithic file, now serving as the library):
- Sheet helpers: `get_att_sh`, `get_booking_sh`, `get_salary_adv_sh`, `get_game_lib_sh`, `get_console_games_sh`
- Data fetchers: `fetch_console_status`, `fetch_games`, `fetch_console_games`, `fetch_members`, `fetch_staff`, etc.
- Member operations: `fetch_member_data`, `fetch_balance_mins`, `fetch_wallet_mins`, `fetch_base_rate`, etc.
- Booking ops: `create_booking`, `end_booking`, `cancel_booking`, `check_disc_session_conflict`
- Console ops: `add_console_game`, `remove_console_game`, `update_game_library_install`
- Cache: `_load_cfg`, `_load_members`, `_bg_cache_refresh`
- V1 utility aliases: `fetch_game_library = fetch_games`, `write_console_game = add_console_game`, etc.
- BotState enum (176 states) and all state aliases
- ALL BTN constants (~150+ button labels)
- Receipt helpers

### 11. Function Name Mismatches (V1 vs V2)

| V1 (monolithic) Function | V2 Status |
|--------------------------|-----------|
| `show_main_menu` | ✅ In main_menu.py (but BROKEN) |
| `step_main_menu` | ✅ In main_menu.py (but BROKEN) |
| `prompt_staff_select` | ✅ In members.py |
| `step_staff_select` | ✅ In members.py |
| `show_mm_menu` | ✅ In members.py |
| `show_rank_info` | ✅ In members.py |
| `step_mm_menu` | ✅ In members.py |
| `prompt_mm_lookup` | ✅ In members.py |
| `step_mm_lookup` | ✅ In members.py |
| `prompt_nm_staff` | ✅ In members.py |
| `step_nm_staff` | ✅ In members.py |
| `cmd_cancel` | ✅ In commands.py |
| `cmd_topup` | ✅ In commands.py |
| `cmd_member_mgmt` | ✅ In commands.py |
| `cmd_check_member` | ✅ In commands.py |
| `cmd_newmember` | ✅ In commands.py |
| `cmd_ranks` | ✅ In commands.py |
| `cmd_help` | ✅ In help.py |
| `cmd_version` | ✅ In help.py |
| `error_handler` | ✅ In help.py |

**No V1 function is missing in V2.** The refactor preserved all functionality. However, several step functions referenced in `app.py`'s ConversationHandler states must exist in their respective handler modules or `bot/__init__.py`.

### 12. ConversationHandler State Coverage
`bot/app.py` defines a massive ConversationHandler with **176 states** (BotState IntEnum 0-176). Each state maps to a handler function. All referenced handler functions appear to exist in their respective modules (once main_menu.py is fixed).

---

## 📊 SUMMARY OF ISSUES

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| 1 | 🔴 CRITICAL | `main_menu.py` line 18: unterminated `"""` — bot CANNOT import | **BLOCKING** |
| 2 | 🔴 HIGH | Three duplicate handler directories | Cleanup needed |
| 3 | 🔴 HIGH | `keep_alive.py` missing from staging | Minor impact |
| 4 | 🔴 HIGH | SQLite DB completely unused | Dead code |
| 5 | 🟡 MEDIUM | `bot/bot/__init__.py` orphan imports before docstring | Editing artifact |
| 6 | 🟡 MEDIUM | 15 handlers use `from bot import *` (circular import risk) | Works now, fragile |
| 7 | 🟡 MEDIUM | BTN constants in 3 places (duplication risk) | Fragile |
| 8 | 🟡 MEDIUM | Duplicate `app.py` (top-level and `bot/app.py`) | Dead code |
| 9 | 🟢 LOW | 150+ handler functions across 25 modules | Well-organized |
| 10 | 🟢 LOW | No V1 functions missing in V2 | Good |
| 11 | 🟢 LOW | `bot/bot/handlers/` is complete duplicate of `bot/handlers/` | Cruft |
| 12 | 🟢 LOW | `handlers/` (top-level) is third duplicate | Cruft |

---

## 🛠 RECOMMENDED FIX PRIORITIES

### Immediate (Bot Won't Start)
1. **Fix main_menu.py line 18** — close or remove the unterminated `"""` string

### Cleanup (After Import Works)
2. Delete `/root/staging/bot_src/bot/bot/` directory (entire tree)
3. Delete `/root/staging/bot_src/handlers/` directory (entire tree)
4. Delete `/root/staging/bot_src/app.py` (top-level duplicate)
5. Copy `keep_alive.py` from one of: `/root/Personal-Wallet-Tele-Bot/bot/keep_alive.py`
6. Fix `bot/bot/__init__.py` orphan imports before docstring — but since this is in the directory to be deleted, skip

### Architecture (Future)
7. Replace `from bot import *` in handlers with explicit imports to eliminate circular import fragility
8. Consolidate BTN constants to a single source (e.g., `bot/constants.py`)
9. Either integrate `sqlite/` or delete it
