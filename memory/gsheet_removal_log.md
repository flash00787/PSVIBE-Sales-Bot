# GSheet Removal Log — API Server Cleanup

**Date:** 2026-07-01 16:42 UTC
**Status:** ✅ COMPLETE — API running, backward-compatible

---

## Phase 1: New Clean Endpoints (ADDED)

Added to `/root/psvibe_api_server/patch_routes.py` (end of file):

| New Endpoint | Mirrors | Status |
|---|---|---|
| `GET /api/config` | `GET /api/sheets/config` (2nd, full settings) | ✅ |
| `GET /api/consoles` | `GET /api/sheets/consoles` | ✅ |
| `GET /api/stock/daily` | `GET /api/sheets/stock-today` | ✅ |
| `GET /api/stock/valuation` | `GET /api/sheets/inventory` | ✅ |
| `GET /api/reports/daily` | `GET /api/sheets/report-data` | ✅ |
| `GET /api/reports/weekly` | `GET /api/sheets/weekly-report` | ✅ |
| `GET /api/reports/pnl` | `GET /api/sheets/pnl` | ✅ |
| `GET /api/staff/breakdown` | `GET /api/sheets/staff-breakdown` | ✅ |
| `GET /api/promotions` | `GET /api/sheets/promotions/all` | ✅ |
| `GET /api/promotions/log` | `GET /api/sheets/promotions-log` (GET) | ✅ |
| `POST /api/promotions/log` | `POST /api/sheets/promotions-log` (POST) | ✅ |

All old `/api/sheets/*` endpoints preserved for backward compatibility.

---

## Phase 2: Removed GSheet Dependency from app.py

1. **Removed import block** (lines 93-96): `from sheets_client import (get_workbook, ..., invalidate_cache, ...)`
2. **Removed SHEET_* constants** from config import: No longer imported from config.py
3. **Removed 6 `invalidate_cache("bookings")` calls** from:
   - Line 716 — `api_extend_booking_duration`
   - Line 1651 — `api_create_booking` (deprecated)
   - Line 1809 — `api_update_booking_status`
   - Line 2235 — session end handler
   - Line 2857 — session move handler
   - Line 2970 — session swap handler

---

## Phase 3: Deleted Obsolete Files

| File | Size | Reason |
|---|---|---|
| `sheets_client.py` | 9.2 KB | Contains all gspread/Google Sheets API code |
| `sync_console_mults.py` | 1.8 KB | Migration tool, already applied |
| `sync_settings_to_mysql.py` | 3.8 KB | Migration tool, already applied |
| `phase5_patch.py` | 3.2 KB | Migration tool, already applied |
| `service_account.json` | 2.4 KB | Google service account key — security risk |

---

## Phase 4: Cleaned config.py

Removed:
- `SERVICE_ACCOUNT_FILE`
- `SHEET_ID`
- `SHEETS_SCOPES`
- All `SHEET_*` constants (14)
- All `CACHE_TTL_*` constants (8)

Kept: `API_TITLE`, `API_VERSION`, `API_DESCRIPTION`, `HOST`, `PORT`, `DEBUG`, `API_KEY`, `MMT_HOURS`, `MMT_MINUTES`, MySQL config

---

## Phase 5: gspread Uninstall — SKIPPED

**Not uninstalled** because `gspread` is still imported by:
- `/root/psvibe_api_server/analytics_sync.py` — analytics sync service
- `/root/psvibe_api_server/gsheet_to_mysql.py` — one-time migration tool

These are separate services not part of the API runtime. Can be removed when those tools are migrated.

---

## Phase 6: Verification

```
✅ python3 AST parse: app.py, patch_routes.py, config.py — all OK
✅ No remaining invalidate_cache calls in app.py or patch_routes.py
✅ No remaining sheets_client imports in app.py
✅ All 5 obsolete files confirmed deleted
```

## Phase 7: Restart

```
✅ systemctl restart psvibe-api → Active (running)
✅ /api/health → {"status":"ok","services":{"api":"running"}}
✅ All old /api/sheets/* endpoints still active (401 = auth OK)
✅ All new /api/* endpoints responding (401 = auth OK)
```

---

## What Did NOT Change

- ✅ All `/api/sheets/*` endpoints preserved (backward compatible)
- ✅ Bot files untouched
- ✅ Dashboard untouched
- ✅ `sync_service.py` already gutted (28-line stub)
- ✅ `analytics_sync.py` and `gsheet_to_mysql.py` untouched

---

## Next Steps (Future)

1. **Update bot callers** to use new endpoints (`/api/config`, `/api/consoles`, etc.)
2. **Remove old `/api/sheets/*` endpoints** after 1 release cycle
3. **Remove dead endpoints**: `/api/sheets/liability`, `/api/sheets/payment-methods`, `/api/sheets/promotions`
4. **Remove `POST /api/sheets/log`** (no-op now)
5. **Migrate `analytics_sync.py`** away from gspread, then uninstall gspread
