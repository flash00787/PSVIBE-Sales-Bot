# Finance + Reports Rebuild Report

**Date:** 2026-05-27 04:36 UTC  
**Task:** Rebuild finance.py, reports.py, payroll.py, salary_adv.py, admin.py, broadcast.py, attendance.py

---

## Issues Found & Fixed

### 1. `broadcast.py` — Missing `from bot import *`
**Severity:** Critical  
`broadcast.py` was missing `from bot import *` at the top. This meant none of the bot's exported names (`__all__`) were available. The file uses `_BROADCAST_ADMIN_IDS`, `_replit_get`, `asyncio`, and other bot globals — all would fail at runtime.

**Fix:** Added `from bot import *` after the module docstring in both staging and deployed versions.

### 2. Private Names Not in `__all__` — Runtime NameErrors
**Severity:** Critical  
The following private (underscore-prefixed) functions/constants were used across handler files but NOT in `bot/__init__.py`'s `__all__` list:

| Name | Used In | Defined In |
|------|---------|------------|
| `_replit_get` | finance.py, reports.py, admin.py, broadcast.py | bot/__init__.py |
| `_replit_post` | finance.py | bot/__init__.py |
| `_BROADCAST_ADMIN_IDS` | broadcast.py | bot/__init__.py |
| `_int` | payroll.py, admin.py | bot/__init__.py |

Since Python's `from module import *` only exports names in `__all__` (or non-underscore names if `__all__` is absent), these names were inaccessible.

**Fix:** Added all 4 names to `__all__` in `bot/__init__.py`.

### 3. `_pin_then` — Cross-File Private Function Reference
**Severity:** Critical  
`_pin_then` was defined in `admin.py` but called from:
- `payroll.py` → `cmd_payroll_cmd()`
- `attendance.py` → `cmd_setattend_cmd()`
- `finance.py` → `cmd_finance()`
- `admin.py` → `cmd_admin()`

Since `_pin_then` was a module-level private function in `admin.py`, it couldn't be accessed by other handler modules.

**Fix:** Moved `_pin_then` from `admin.py` to `bot/__init__.py` and added `_pin_then` to `__all__`. Now all handler files can access it via `from bot import *`.

### 4. `_BIZ_START` — Missing Constant
**Severity:** Critical  
`finance.py`'s `_calc_nbv_per_unit()` function references `_BIZ_START` (the business start date for depreciation calculation), but this constant was only defined in the V1 monolithic main.py — never carried over to V2.

**Fix:** Defined `_BIZ_START = datetime(2026, 6, 1)` in `bot/__init__.py` and added to `__all__`.

---

## Files Modified

| File | Change |
|------|--------|
| `bot/__init__.py` | +6 names in `__all__`, +`_BIZ_START` constant, +`_pin_then` function |
| `bot/handlers/admin.py` | Removed `_pin_then` function definition (moved to bot/__init__.py) |
| `bot/handlers/broadcast.py` | Added `from bot import *` |
| `bot/handlers/finance.py` | Deployed from staging (no code changes needed beyond fix #2) |
| `bot/handlers/reports.py` | Deployed from staging (no code changes needed) |
| `bot/handlers/payroll.py` | Deployed from staging (no code changes needed) |
| `bot/handlers/salary_adv.py` | Deployed from staging (no code changes needed) |
| `bot/handlers/attendance.py` | Deployed from staging (no code changes needed) |

---

## Verification

- ✅ All 7 handler files pass `ast.parse()` syntax check
- ✅ `bot/__init__.py` passes syntax check
- ✅ All 6 private names confirmed present in `__all__`
- ✅ `_pin_then` confirmed moved to `bot/__init__.py` (1 definition, 0 old definitions left)
- ✅ `broadcast.py` confirmed has `from bot import *`
- ✅ Bot restarted successfully (PID 291204, no startup errors)
- ✅ Log shows normal operation: cache refresh, getMe, setMyCommands, getUpdates

---

## Deployment

```bash
# Files deployed via rsync:
for f in finance.py reports.py payroll.py salary_adv.py admin.py broadcast.py attendance.py; do
  rsync -av /root/staging/bot_src/bot/handlers/$f /root/Sales-Tele-Bot_refactored/bot/handlers/
done

# Service restarted:
systemctl restart psvibe-bot-refactored.service
```
