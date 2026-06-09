# Sales Bot — Fix 10 Write Functions to Use API (SB-1)

**Date:** 2026-05-28  
**Fix:** OpenClaw Subagent  
**Target:** `/root/psvibe-sale-bot/bot/__init__.py`  
**Backup:** `/root/psvibe-sale-bot/bot/__init__.py.bak-20260528`

---

## Summary

Added `_HAS_API` gates to all 10 write functions that were bypassing the API server (`psvibe-api`, `localhost:8000`). These functions now try the API first and fall back to direct gspread only if the API call fails.

## Changes Made

### 1. Import Block (line ~18)

Added 10 WRITE `api_*` function imports alongside the existing READ imports:

```python
from bot.api_client import (
    # ... existing 35 READ imports ...
    # ── WRITE operations  ──
    api_create_booking, api_end_booking, api_cancel_booking,
    api_save_attendance, api_add_console_game, api_remove_console_game,
    api_set_game_disc_count, api_update_game_library_install,
    api_add_console_to_setting, api_remove_console_from_setting,
)
```

### 2. Fixed Functions

| # | Function | API Call | Gate Pattern |
|---|----------|----------|-------------|
| 1 | `create_booking` | `api_create_booking()` → `POST /api/create_booking` | Try API → extract `booking_id` from response → fallback |
| 2 | `end_booking` | `api_end_booking()` → `PUT /api/end_booking/{id}` | Try API → return `True` on success → fallback |
| 3 | `cancel_booking` | `api_cancel_booking()` → `PUT /api/cancel_booking/{id}` | Try API → return `True` on success → fallback |
| 4 | `save_attendance` | `api_save_attendance()` → `POST /api/save_attendance` | Try API → return (void) on success → fallback |
| 5 | `add_console_game` | `api_add_console_game()` → `POST /api/add_console_game` | Try API → invalidate cache → return `True` → fallback |
| 6 | `remove_console_game` | `api_remove_console_game()` → `DELETE /api/remove_console_game` | Try API → invalidate cache → return `True` → fallback |
| 7 | `set_game_disc_count` | `api_set_game_disc_count()` → `PUT /api/set_game_disc_count` | Try API → invalidate cache → return `True` → fallback |
| 8 | `update_game_library_install` | `api_update_game_library_install()` → `PUT /api/update_game_library_install` | Try API → return `True` on success → fallback |
| 9 | `add_console_to_setting` | `api_add_console_to_setting()` → `POST /api/add_console_to_setting` | Try API → return `True` on success → fallback |
| 10 | `remove_console_from_setting` | `api_remove_console_from_setting()` → `DELETE /api/remove_console_from_setting/{id}` | Try API → return `True` on success → fallback |

### 3. Gate Pattern

All functions follow the same pattern:

```python
def some_function(...):
    if _HAS_API:
        result = api_some_function(...)
        if result is not None:
            return True  # or booking_id, or just return (void)
        logging.warning("API api_some_function() failed, falling back to gspread")
    # ... existing gspread fallback code ...
```

Key behaviors:
- **API available** (`_HAS_API = True`): Calls the API endpoint. The API server (`psvibe-api`) handles the actual sheet write, cache invalidation, and logging.
- **API unavailable** (`_HAS_API = False` or API returns `None`): Falls back to direct gspread — the existing behavior is preserved as-is.
- **Cache invalidation**: For functions with local caches (`_CGAME_ROWS`, `_GAME_ROWS`), the cache is invalidated in both paths.

## Deployment

1. Backed up original to `/root/psvibe-sale-bot/bot/__init__.py.bak-20260528`
2. Uploaded fixed file via SFTP
3. Restarted `psvibe-sale-bot` systemd service
4. **Status**: Bot is running (`active (running)`, PID 381911)

## Verification

- ✅ Bot starts without import errors (imports all 10 WRITE api functions)
- ✅ `_HAS_API` set to `True` (API client available)
- ✅ API server logs show bot reads via API (`GET /api/sheets/config` 200 OK)
- ✅ All 10 functions preserve gspread fallback behavior

## What Changed in the Architecture

**Before:**
```
Bot → gspread → Google Sheets  (reads: API → gspread fallback)
API Server → gspread → Google Sheets  (independent, no awareness of bot writes)
```

**After:**
```
Bot → API Server (localhost:8000) → gspread → Google Sheets  (reads AND writes)
       ↳ gspread fallback (if API unavailable)
```

## Remaining Work

The audit report mentions two additional items not addressed by this fix:
1. **Card_Wallet Column L has no header** — cosmetic, low priority
2. **Duplicate "Referral_Code" column in Card_Wallet** — cosmetic, low priority
3. **`save_referral_code` and `update_member_effective_rate`** in `__init__.py` — these also appear to lack `_HAS_API` gates (audit says they have them, but the code doesn't show it). Worth checking separately.

## Rollback

```bash
cp /root/psvibe-sale-bot/bot/__init__.py.bak-20260528 /root/psvibe-sale-bot/bot/__init__.py
systemctl restart psvibe-sale-bot
```
