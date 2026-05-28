# PS VIBE Sales Bot — Phase 6 Refactor Summary

**Date:** 2026-05-26  
**Bot Version:** 2026.05.05-r1  
**Refactor Target:** Modularize the 539KB, 12,142-line monolithic handlers.py into maintainable domain modules.

---

## 1. What Was Changed

### A. Duplicate `__init__.py` — RESOLVED

**Problem:** Two identical (but slightly divergent) `__init__.py` files existed:
- `/root/Sales-Tele-Bot/__init__.py` (outer package marker, 174 states)
- `/root/Sales-Tele-Bot/bot/__init__.py` (actual package, 177 states)

The outer version was 3 states behind (`BOOK_LINK`, `WL_MENU`, `ADJUST_TIME` missing) and lacked several functions (`_replit_delete`, `fetch_allowed_staff_ids`, waitlist buttons).

**Solution:**
- `bot/__init__.py` is now the **canonical version** (`__init___refactored.py`)
- The outer `/root/Sales-Tele-Bot/__init__.py` becomes a **minimal re-export**:
  ```python
  from bot import *  # noqa: F401,F403
  ```
- This eliminates the duplicate while maintaining backward compatibility.

### B. handlers.py Split — 26 DOMAIN MODULES

The monolithic `handlers.py` (12,142 lines, ~539KB, 347 functions) has been split into:

| Module | Lines | Functions | Description |
|--------|-------|-----------|-------------|
| `_common.py` | — | N/A | (Imports only; shared via `bot` package) |
| `main_menu.py` | ~85 | 2 | show_main_menu, step_main_menu |
| `members.py` | ~1,132 | 33 | New Member, Top Up, Member Lookup, Staff Select |
| `sales.py` | ~1,265 | 25 | Daily Sales wizard (member→console→mins→food→confirm) |
| `discount.py` | ~430 | 5 | Discount, Promotions, Bundle FOC |
| `stock.py` | ~209 | 9 | Stock Out, Inventory View, Stock Menu |
| `stock_in.py` | ~280 | 10 | Stock In (Restock) flow |
| `booking.py` | ~1,072 | 24 | Console Booking, Staff Advance Booking |
| `waitlist.py` | ~270 | 8 | Waitlist Management |
| `admin_bookings.py` | ~230 | 5 | Admin Booking Approve/Reject |
| `games.py` | ~404 | 10 | Game Library (add/edit/delete) |
| `console.py` | ~333 | 8 | Console Menu, Game Change, End Session |
| `console_mgmt.py` | ~142 | 6 | Console CRUD (add/delete from Setting) |
| `ginst.py` | ~230 | 9 | Console-Game Install Tracking |
| `ssd_disc.py` | ~447 | 16 | SSD Management, Game Discs Record |
| `finance.py` | ~2,555 | 106 | OPEX, Assets, Prepaid, Payables, Receivables, Settle, Capital, Partners |
| `admin.py` | ~544 | 13 | Admin Panel, Monthly P&L, Cashflow, Liability |
| `salary_adv.py` | ~166 | 4 | Salary Advance flow |
| `attendance.py` | ~166 | 8 | Attendance (Leave/Late) wizard |
| `payroll.py` | ~227 | 4 | Monthly Payroll, Staff KPI |
| `reports.py` | ~334 | 5 | Today's Report, Inventory, Stock Today, Promo Reports |
| `broadcast.py` | ~78 | 2 | Broadcast, Staff KPI display |
| `booking_flow.py` | ~712 | 17 | Session Timer, Booking Cancel/Extend |
| `notify.py` | ~82 | 3 | Customer Notifications, Low Balance Alerts |
| `commands.py` | ~85 | 6 | /topup, /check, /member, /ranks shortcuts |
| `help.py` | ~77 | 3 | /version, /help, error_handler |
| `referral.py` | ~48 | 2 | Referral Code assignment |

**Total: 347 functions** across 26 modules.

### C. State Enum — FIXED

**Before:**
```python
(MAIN_MENU, MEMBER, CONSOLE, ..., WL_MENU) = range(177)
```

**After:**
```python
from enum import IntEnum

class BotState(IntEnum):
    """Bot conversation states with integer values for ConversationHandler."""
    MAIN_MENU = 0
    MEMBER = 1
    CONSOLE = 2
    ...
    WL_MENU = 176

# Module-level aliases for backward compatibility
MAIN_MENU = BotState.MAIN_MENU
MEMBER = BotState.MEMBER
...
```

This provides type safety, IDE autocomplete, and documentation while maintaining full backward compatibility — all existing code using `MAIN_MENU`, `MEMBER`, etc. continues to work unchanged.

### D. Star Imports — FIXED

**Problem:** `from bot import *` imports everything indiscriminately.

**Solution:** Added comprehensive `__all__` to `bot/__init__.py` with **379 explicitly listed names**:
- All public constants (`BTN_*`, `N8N_*`, `VALID_CONSOLES`, etc.)
- All state constants (`MAIN_MENU`, `MEMBER`, etc.)
- All public functions (`show_main_menu`, `fetch_members`, etc.)
- The `BotState` class

This makes `from bot import *` controlled and explicit — no unintended namespace pollution.

---

## 2. Files NOT Modified (Safety)

Per constraints, these files are **untouched**:
- `.env` — environment variables
- `service_account.json` — Google service account credentials
- `main.py` — entry point
- `app.py` — application setup

---

## 3. Deployment Strategy

### Safety First — Parallel Directory Approach

A **deployment script** (`deploy_refactored.sh`) has been created that:

1. **Creates** `/root/Sales-Tele-Bot_refactored/` — a parallel directory
2. **Copies** `.env` and `service_account.json` from production (read-only)
3. **Uploads** all refactored source files to the staging directory
4. **Creates** a **symlink switch script** (`/root/switch_bot_version.sh`)

### How to Switch Versions

```bash
# Check current status
ssh root@167.71.196.120 'bash /root/switch_bot_version.sh status'

# Activate refactored version (stops services, switches, restarts)
ssh root@167.71.196.120 'bash /root/switch_bot_version.sh activate-refactored'

# Rollback to original
ssh root@167.71.196.120 'bash /root/switch_bot_version.sh activate-original'
```

The switch script:
- Stops both `psvibe-bot` and `psvibe-customer` services
- Updates the symlink `/root/Sales-Tele-Bot_active`
- Updates systemd service files to point to the symlink
- Restarts services
- **Instant rollback** — just switch the symlink back

---

## 4. Files Created (Local Workspace)

```
refactor_staging/
├── __init___refactored.py        # Merged canonical bot/__init__.py (IntEnum + __all__)
├── __init___outer_minimal.py     # Minimal outer __init__.py for VPS root
├── __init___merged.py           # Raw merged copy from bot/__init__.py
├── handlers/                    # 26 domain-split modules
│   ├── __init__.py              # Re-exports all domain modules
│   ├── main_menu.py             # 2 functions
│   ├── members.py               # 33 functions
│   ├── sales.py                 # 25 functions
│   ├── discount.py              # 5 functions
│   ├── stock.py                 # 9 functions
│   ├── stock_in.py              # 10 functions
│   ├── booking.py               # 24 functions
│   ├── waitlist.py              # 8 functions
│   ├── admin_bookings.py        # 5 functions
│   ├── games.py                 # 10 functions
│   ├── console.py               # 8 functions
│   ├── console_mgmt.py          # 6 functions
│   ├── ginst.py                 # 9 functions
│   ├── ssd_disc.py              # 16 functions
│   ├── finance.py               # 106 functions
│   ├── admin.py                 # 13 functions
│   ├── salary_adv.py            # 4 functions
│   ├── attendance.py            # 8 functions
│   ├── payroll.py               # 4 functions
│   ├── reports.py               # 5 functions
│   ├── broadcast.py             # 2 functions
│   ├── booking_flow.py          # 17 functions
│   ├── notify.py                # 3 functions
│   ├── commands.py              # 6 functions
│   ├── help.py                  # 3 functions
│   └── referral.py              # 2 functions
├── deploy_refactored.sh          # Deployment script
├── split_handlers_v3.py          # The splitter tool
├── create_refactored_init.py    # The IntEnum + __all__ generator
└── (original files preserved)
    ├── main.py
    ├── app.py
    ├── .env
    └── psvibe-*.service
```

---

## 5. Verification Checklist

- [x] handlers.py successfully fetched from VPS (539KB, 12,142 lines)
- [x] Duplicate __init__.py identified and merged (174 vs 177 states)
- [x] 347 functions mapped to 26 domain modules
- [x] State enum converted from `range(177)` to `BotState(IntEnum)`
- [x] `__all__` added with 379 explicitly exported names
- [x] Deployment script created with parallel directory strategy
- [x] Symlink switch script for instant rollback
- [x] .env and service_account.json preserved (not modified)
- [x] No services restarted or modified on VPS

---

## 6. Known Considerations

1. **Circular imports:** The pattern `bot/__init__.py` → `bot/handlers/__init__.py` → domain modules → `from bot import *` creates the same circular import pattern as the original. This is safe because the handler import happens at the **bottom** of `bot/__init__.py`, after all helpers/config are defined.

2. **Inner helper functions:** Four inner/nested functions (`sort_key`, `dfmt` (x2), `edit_fn`) defined inside other functions are NOT extracted as separate modules. They live inside their parent functions across the split — this is correct behavior as they are closures.

3. **Stock In module:** Contains copies of `_replit_get`, `_replit_patch`, `_replit_post` because these have a longer timeout (30s) than the versions in `bot/__init__.py` (8s). Consider consolidating in a future cleanup.

4. **Finance module** (106 functions, 2,555 lines): The largest domain. Could be further split into `finance_opex.py`, `finance_assets.py`, `finance_payables.py`, etc. in a future iteration.
