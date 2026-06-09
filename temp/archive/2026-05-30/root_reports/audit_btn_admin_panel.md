# 🔍 DEEP AUDIT: ⚙️ Admin Panel — Full Admin System
**Date:** 2026-05-28 18:24 UTC
**Bot:** PS VIBE Sales Bot (psvibe-sale-bot.service)
**VPS:** 5.223.81.16

---

## EXECUTIVE SUMMARY

**CRITICAL FINDING: 12 runtime symbols are MISSING from `bot/__init__.py` `__all__` — all admin sub-menus will crash with `NameError` when accessed.**

The bot compiles and starts successfully (syntax is fine), but any admin action that hits these code paths will fail. The missing symbols affect: PIN-gated entry, booking approvals, attendance wizards, and the entire Finance module.

---

## AUDIT MATRIX

### 1. 🔐 ⚙️ Admin Panel (`BTN_ADMIN = "🔧 Admin Panel"`)

| Criterion | Status | Details |
|-----------|--------|---------|
| Entry | `cmd_admin()` → `_pin_then("admin", ...)` | **BROKEN** — `_pin_then` missing |
| PIN check | `step_admin_pin()` verifies against `STOCK_ACCESS_PIN` | ✅ OK |
| Delete PIN message | `await update.message.delete()` | ✅ OK |
| Wrong PIN | Returns `show_main_menu()` with error | ✅ OK |
| Correct PIN routing | `_after_pin` → payroll/kpi/setattend/finance or admin menu | ✅ OK |
| State transitions | `ADMIN_PIN → ADMIN_MENU → ...` | ✅ OK |
| Error handling | `step_admin_pin` has try/except for delete | ✅ OK |
| async/await | All handlers async | ✅ OK |

**Issue:** `_pin_then` is not defined anywhere. When `/admin` is typed, a `NameError` will be raised at runtime.

---

### 2. 📦 Stock Update (`BTN_STOCK_UPDATE`)

| Criterion | Status | Details |
|-----------|--------|---------|
| Handler | `show_stock_menu()` (in stock.py) | ✅ OK (separate module) |
| Flow | Admin PIN → Stock Menu → STOCK_PIN → ... | ✅ OK |

**No admin-specific issues found.** (Stock uses its own PIN via `STOCK_ACCESS_PIN`.)

---

### 3. 📅 Attendance (`BTN_ADMIN_ATTEND`)

| Criterion | Status | Details |
|-----------|--------|---------|
| Entry (direct `/setattend`) | `cmd_setattend_cmd()` → `_pin_then("setattend", ...)` | **BROKEN** — `_pin_then` missing |
| Entry (via admin menu) | `cmd_setattend()` bypasses PIN (admin already authed) | ✅ OK |
| Flow | `step_attend_staff → step_attend_leave → step_attend_late → step_attend_deduct → _attend_save_and_next` | ✅ OK |
| Button constants | `BTN_ATTEND_DONE`, `BTN_ATTEND_SKIP` | **BROKEN** — both missing |
| Save logic | `save_attendance()` → Sheet/API | ✅ OK |
| State transitions | `ATTEND_STAFF → ATTEND_LEAVE → ATTEND_LATE → ATTEND_DEDUCT` | ✅ OK |
| Error handling | Try/except on save | ✅ OK |
| Skip handlers | All three skip flows work correctly | ✅ OK |

**Issues:**
1. `cmd_setattend_cmd()` uses `_pin_then` — will crash
2. `BTN_ATTEND_DONE` and `BTN_ATTEND_SKIP` undefined — will crash when wizard shows those buttons

---

### 4. 💸 Salary Advance (`BTN_ADMIN_SAL_ADV`)

| Criterion | Status | Details |
|-----------|--------|---------|
| Admin menu entry | Routes to `cmd_admin_sal_adv()` in admin.py | ✅ OK |
| Flow | `step_sal_adv_staff → step_sal_adv_amt → step_sal_adv_pay → step_sal_adv_confirm` | ✅ OK |
| API calls | Direct gspread `sh.append_row()` | ✅ OK |
| State transitions | `SAL_ADV_STAFF → SAL_ADV_AMT → SAL_ADV_PAY → SAL_ADV_CONFIRM → ADMIN_MENU` | ✅ OK |
| Validation | Amount parsed as int with comma stripping | ✅ OK |
| Error handling | Try/except on sheet write | ✅ OK |
| async/await | All async, gspread in executor | ✅ OK |

**No critical issues.** (This handler uses `from bot import *` but only references symbols actually in `__all__`.)

---

### 5. 💰 Payroll (`BTN_PAYROLL`)

| Criterion | Status | Details |
|-----------|--------|---------|
| Direct `/payroll` | `cmd_payroll_cmd()` → `_pin_then("payroll", ...)` | **BROKEN** — `_pin_then` missing |
| Via admin menu | `cmd_payroll()` directly (bypasses PIN) | ✅ OK |
| Calc function | `calc_monthly_payroll()` | ✅ OK |
| Data sources | Sales_Daily, TopUp_Log, Setting (staff+base salaries), Attendance_Log, Salary_Advance | ✅ OK |
| API calls | All through gspread wrappers (with API fallback) | ✅ OK |
| Error handling | Try/except in `cmd_payroll()` | ✅ OK |
| async/await | All async | ✅ OK |
| State return | Returns `show_main_menu()` | ✅ OK |

**Note:** `cmd_payroll()` returns to `show_main_menu()` (MAIN_MENU state) rather than admin menu. This is intentional — payroll is a read-only view.

---

### 6. 📈 Staff KPI (`BTN_STAFF_KPI`)

| Criterion | Status | Details |
|-----------|--------|---------|
| Direct `/kpi` | `cmd_kpi_cmd()` → `_pin_then("kpi", ...)` | **BROKEN** — `_pin_then` missing |
| Via admin menu | `cmd_staff_kpi()` (in broadcast.py) | ✅ OK |
| Implementation | Fetches `sheets/report-data` via `_replit_get()` | ✅ OK |
| Error handling | Handles None from API | ✅ OK |
| async/await | All async | ✅ OK |

---

### 7. 📊 Monthly P&L (`BTN_ADMIN_PNL`)

| Criterion | Status | Details |
|-----------|--------|---------|
| Handler | `cmd_admin_pnl()` | ✅ OK |
| API call | `_replit_get("sheets/pnl")` | ✅ OK |
| Calc function | `calc_monthly_pnl()` in admin.py (used by API) | ✅ OK |
| Error handling | Try/except, fallback on API error | ✅ OK |
| Formatting | `Markdown` parse mode with thousands separator | ✅ OK |
| State return | Returns `show_admin_menu()` | ✅ OK |

**Clean.** No missing dependencies.

---

### 8. 💵 Cash Flow (`BTN_ADMIN_CF`)

| Criterion | Status | Details |
|-----------|--------|---------|
| Handler | `cmd_admin_cashflow()` | ✅ OK |
| API call | `_replit_get("sheets/pnl")` — reuses P&L data | ✅ OK |
| Error handling | Try/except | ✅ OK |
| State return | Returns `show_admin_menu()` | ✅ OK |

**Clean.**

---

### 9. 💳 Card Liability (`BTN_ADMIN_LIB`)

| Criterion | Status | Details |
|-----------|--------|---------|
| Handler | `cmd_admin_liability()` | ✅ OK |
| API calls | `_replit_get("sheets/liability")`, `_replit_get("sheets/pnl")` | ✅ OK |
| Error handling | Comprehensive try/except with fallback message | ✅ OK |
| Graceful degradation | If PNL unavailable, shows only liability data | ✅ OK |

**Clean.**

---

### 10. ⚙️ Console စီမံ (`BTN_CON_MANAGE`)

| Criterion | Status | Details |
|-----------|--------|---------|
| Handler | `show_con_mgmt_menu()` | ✅ OK |
| Sub-options | List, Add, Delete consoles | ✅ OK |
| Flows | Add: `CON_ADD_ID → CON_ADD_TYPE → CON_ADD_MULT` | ✅ OK |
| | Delete: `CON_DEL_SELECT` with confirmation | ✅ OK |
| Validation | Duplicate check on add, existence check on delete | ✅ OK |
| Error handling | Try/except on sheet writes | ✅ OK |
| Runtime update | Updates `VALID_CONSOLES` set in real-time | ✅ OK |

**Clean.**

---

### 11. 📊 Promo Reports (`BTN_PROMO_REPORTS`)

| Criterion | Status | Details |
|-----------|--------|---------|
| Handler | `cmd_promo_reports()` in reports.py | ✅ OK |
| Implementation | Fetches from Promotions sheet + sales data | ✅ OK |
| Error handling | Try/except with logging | ✅ OK |

**Clean.**

---

### 12. 💼 Finance (`BTN_FINANCE`)

| Criterion | Status | Details |
|-----------|--------|---------|
| Direct `/finance` | `cmd_finance()` → `_pin_then("finance", ...)` | **BROKEN** — `_pin_then` missing |
| Via admin menu | `show_finance_menu()` directly | ✅ OK |
| All sub-flows | OPEX, Asset, Prepaid, Transfer, Payable, Receivable, Advance, Capital, Shareholder, Settlements, Reports, Setup | — |

**All finance sub-flows use MISSING symbols:**
- `OPEX_CATEGORIES` — undefined → `NameError` on OPEX entry
- `FINANCE_ACCOUNTS` — undefined → `NameError` on all account selection steps
- `PAY_METHODS` — undefined → `NameError` on payment step
- `ASSET_CATEGORIES` — undefined → `NameError` on asset entry
- `PREPAID_CATEGORIES` — undefined → `NameError` on prepaid entry
- `CAPITAL_ACCOUNTS` — undefined → `NameError` on capital entry
- `_SHARE_ROLES` — undefined → `NameError` on shareholder add
- `_BIZ_START` — undefined → `NameError` on asset dispose (NBV calc)

---

## 🔴 CRITICAL FINDINGS: Missing Runtime Symbols

### Complete List of Missing Definitions

| # | Symbol | Used In | Impact |
|---|--------|---------|--------|
| 1 | `_pin_then` | admin.py, attendance.py, payroll.py, finance.py | **ALL PIN-gated admin entry points crash** |
| 2 | `_replit_patch` | admin_bookings.py, booking_flow.py, sales.py | **Booking approve/reject crashes** |
| 3 | `BTN_ATTEND_DONE` | attendance.py | **Attendance wizard finish button shows NameError** |
| 4 | `BTN_ATTEND_SKIP` | attendance.py | **Attendance skip button shows NameError** |
| 5 | `OPEX_CATEGORIES` | finance.py | **OPEX recording crashes** |
| 6 | `FINANCE_ACCOUNTS` | finance.py | **ALL finance account selection crashes** |
| 7 | `PAY_METHODS` | finance.py | **OPEX payment selection crashes** |
| 8 | `ASSET_CATEGORIES` | finance.py | **Asset recording crashes** |
| 9 | `PREPAID_CATEGORIES` | finance.py | **Prepaid expense recording crashes** |
| 10 | `CAPITAL_ACCOUNTS` | finance.py | **Capital recording crashes** |
| 11 | `_SHARE_ROLES` | finance.py | **Shareholder creation crashes** |
| 12 | `_BIZ_START` | finance.py | **Asset disposal NBV calc crashes** |

### Root Cause
These symbols are used by handlers via `from bot import *` but are NOT listed in `bot/__init__.py`'s `__all__` tuple. The bot starts fine because Python doesn't resolve names in function bodies until call time — these are latent runtime bugs that only surface when a user triggers the affected code paths.

---

## ✅ POSITIVE FINDINGS

1. **Auth/PIN**: `step_admin_pin()` correctly validates against `STOCK_ACCESS_PIN`, deletes the PIN message for security, and routes to the appropriate post-PIN action.

2. **State machine**: All conversation states are properly defined in `BotState(IntEnum)` with integer values 0–168. State transitions are consistent.

3. **async/await**: All handlers are properly `async def`, and blocking operations (gspread, HTTP) go through `asyncio.to_thread()`.

4. **Error handling**: Most handlers have try/except blocks. Finance module has particularly thorough error handling with user-friendly messages.

5. **API/fallback pattern**: Handlers consistently try API first, fall back to direct gspread, and log warnings.

6. **No NotImplemented stubs**: Every button route has a fully implemented handler.

7. **Data integrity**: Attendance, payroll, salary advance, and all finance modules properly validate numeric inputs with defensive parsing.

---

## FIX PLAN

Add the following definitions to `bot/__init__.py` (after the existing button constants, before the `from bot.handlers import *` line) and update `__all__`:

1. `_pin_then()` — PIN gate function
2. `_replit_patch()` — HTTP PATCH for API
3. `BTN_ATTEND_DONE` / `BTN_ATTEND_SKIP` — Button constants
4. `OPEX_CATEGORIES`, `FINANCE_ACCOUNTS`, `PAY_METHODS`, `ASSET_CATEGORIES`, `PREPAID_CATEGORIES`, `CAPITAL_ACCOUNTS`, `_SHARE_ROLES` — Category lists
5. `_BIZ_START` — Business start date constant
