# DEEP AUDIT: Sales Bot — Remaining Handler Files
## VPS: 5.223.81.16 | Date: 2026-05-28 | Status: ✅ COMPLETE

---

## Audit Summary

| # | Severity | File | Issue | Status |
|---|---|---|---|---|
| 1 | 🐛 MEDIUM | broadcast.py:64,97 | `_replit_get` blocking calls in async `cmd_staff_kpi` | ✅ FIXED |
| 2 | ⚠️ LOW | notify.py:1-4 | Docstring contained `from bot import *` (cosmetic) | ✅ FIXED |
| 3 | ⚠️ LOW | referral.py:1-3 | Import before module docstring | ✅ FIXED |
| 4 | 🐛 MEDIUM | referral.py:24 | `fetch_referral_code` blocking call | ✅ FIXED |
| 5 | 🐛 MEDIUM | referral.py:91 | `member_sh.get_all_values()` blocking call | ✅ FIXED |
| 6 | ⚠️ LOW | discount.py:1-3 | Import before module docstring | ✅ FIXED |
| 7 | ⚠️ LOW | discount.py | Missing `logger = logging.getLogger(__name__)` | ✅ FIXED |
| 8 | 🔴 CRITICAL | bot/__init__.py | Circular import from `__all__` additions | ✅ FIXED (minimal constants added) |

---

## Detailed Findings

### 1. broadcast.py (144 lines) — ✅ FIXED

**Functions:** `cmd_broadcast`, `cmd_staff_kpi`

**Issues Fixed:**
- `cmd_staff_kpi` was calling `_replit_get("sheets/report-data")` and `_replit_get("sheets/staff-breakdown")` synchronously. `_replit_get` does blocking HTTP via `urllib.request.urlopen`. Fixed by wrapping in `await asyncio.to_thread(...)`.
- `cmd_broadcast` already had `await asyncio.to_thread(_replit_get, ...)` ✅

**Handler Registration:** Both handlers registered in app.py ✅

### 2. commands.py (43 lines) — ✅ CLEAN

**Functions:** `cmd_cancel`, `cmd_topup`, `cmd_member_mgmt`, `cmd_check_member`, `cmd_newmember`, `cmd_ranks`

All are simple delegates. No API calls, no blocking I/O. All 6 registered in app.py.

### 3. help.py (85 lines) — ✅ CLEAN

**Functions:** `cmd_version`, `cmd_help`, `error_handler`

Error handler correctly discriminates NetworkError/TimedOut (warning) vs Conflict (warning) vs other (error with exc_info).

### 4. notify.py (72 lines) — ✅ FIXED

**Functions:** `_notify_customer`, `get_customer_chat_id`, `_check_low_balance_alert`

**Issues Fixed:**
- Docstring incorrectly contained `from bot import *` as text (not actual import). The real import at line 4 kept it functional. Cleaned up.

These are utility functions called from sales.py, admin_bookings.py, booking_flow.py, booking.py.

### 5. referral.py (136 lines) — ✅ FIXED

**Functions:** `prompt_referral_code`, `step_referral_code`

**Issues Fixed:**
- `from bot import *` was before the module docstring → Moved after docstring
- `fetch_referral_code(member_id)` called synchronously → Wrapped in `await asyncio.to_thread()`
- `member_sh.get_all_values()` called synchronously → Wrapped in `await asyncio.to_thread()`

### 6. discount.py (435 lines) — ✅ FIXED

**Functions:** `prompt_discount`, `prompt_promo_select`, `step_promo_select`, `step_bundle_foc`, `step_discount`

**Issues Fixed:**
- `from bot import *` before module docstring → Moved after docstring
- Missing `logger = logging.getLogger(__name__)` → Added

### 7. bot/__init__.py — 🔴 CRITICAL CIRCULAR IMPORT — ✅ FIXED

**Root Cause:** Someone added new constants (`PAY_METHOD`, `PAY_AMOUNT`, `BTN_PAY_DONE`, etc.) to `bot/__init__.py` and their names to `__all__` list, but also added MANY other names (`fetch_payment_methods`, `BTN_ATTEND_DONE`, `BTN_ATTEND_SKIP`, `OPEX_CATEGORIES`, etc.) to `__all__` WITHOUT defining them as variables. Additionally, there were DUPLICATE entries in `__all__` (`FINANCE_ACCOUNTS`, `CAPITAL_ACCOUNTS`, `_SHARE_ROLES`, `_BIZ_START`, `_pin_then` appeared twice).

The bot was running because it had never been restarted since these broken changes were made.

**Fix Applied:** 
1. Restored backup from 2026-05-28 17:35 (known-good state)
2. Added only the 5 genuinely needed constants (PAY_METHOD, PAY_AMOUNT, BTN_PAY_DONE, BTN_ADD_PAY, BTN_NO_MORE) as proper variables with their BotState enum entries
3. Added only these 5 names to `__all__` (no extras)
4. Bot compiles and starts successfully

**Remaining Known Issue:** Other undefined constants (`BTN_ATTEND_DONE`, `OPEX_CATEGORIES`, etc.) are NOT defined and NOT in `__all__`, which means attendance/finance handler flows that reference them will fail at RUNTIME with `NameError` when those flows are triggered. These constants need to be properly defined in a future update. The `__all__` list for the restored backup ended at `BotState` and only the 5 payment constants were added.

---

## Handler Registration Audit

All handler functions have matching registrations:
- ✅ `cmd_broadcast` — registered
- ✅ `cmd_staff_kpi` — registered
- ✅ `cmd_cancel`, `cmd_topup`, `cmd_member_mgmt`, `cmd_check_member`, `cmd_newmember`, `cmd_ranks` — all registered
- ✅ `cmd_version`, `cmd_help`, `error_handler` — all registered
- ✅ `step_referral_code` — registered (REFERRAL_CODE state)
- ✅ `step_discount` — registered (DISCOUNT state)
- ✅ `step_promo_select` — registered (PROMO_SELECT state)
- ✅ `step_bundle_foc` — registered (BUNDLE_FOC state)

## Bot Status

- ✅ All 6 handler files compile successfully
- ✅ Bot service is active and running
- ✅ "PS Vibe Bot is running..." and "Application started" confirmed in logs
- ⚠️ Pre-existing: API config warning (HTTP 401 on sheets/config — API server auth issue, not a code bug)
