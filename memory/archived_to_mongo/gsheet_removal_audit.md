# GSheet Removal Audit — /api/sheets/* Endpoints

**Audit Date:** 2026-07-01
**Goal:** Determine which `/api/sheets/*` endpoints are still used, which are dead code, and suggest MySQL migration paths.

---

## Executive Summary

**All 14 `/api/sheets/*` endpoints are already reading from MySQL, NOT Google Sheets.** The `/api/sheets/*` prefix is a legacy naming convention — every endpoint queries MySQL tables/settings. The GSheet dependency still exists in `sheets_client.py` (the `gspread` library + caches) but the `/api/sheets/*` endpoints no longer use it.

**What still uses GSheets:**
- `app.py` imports `sheets_client` functions but only calls `invalidate_cache("bookings")` (6 callsites) — these invalidate a dead cache
- `phase5_patch.py` uses `get_worksheet()` + `float_safe()` (but this is a migration tool, already applied)
- `archive/patch_app.py` (archived, irrelevant)
- `sync_service.py` — already completely gutted (stub only, no GSheet calls)

**Dashboard:** Zero usage of `/api/sheets/*` endpoints. Dashboard uses `/api/finance/*` and `/api/bookings/*`.

---

## Endpoint-by-Endpoint Audit

### 1. GET /api/sheets/inventory
- **Source:** `patch_routes.py:103`
- **Returns:** `{items: [{name, category, qty, cost, price, total}], categories, total_cost}` — FIFO valuation
- **MySQL tables used:** `stock_in`, `stock_out` (via `inventory_fifo.get_fifo_valuation()`)
- **Called by:**
  - `bot/handlers/stock.py:112` — Stock check command
  - `bot/handlers/stock.py:217` — Stock status display
  - `bot/handlers/reports.py:18` — End-of-day report (gathered in parallel)
- **Status:** ✅ Already MySQL, GSheet-free
- **Rename suggestion:** Move to `/api/stock/fifo-valuation`

### 2. GET /api/sheets/config
- **Source:** `patch_routes.py:119` (first definition, returns base_rate + console_multipliers)
  — AND — `patch_routes.py:644` (second definition, returns ALL config via `_mysql_get_settings_dict()`)
  > ⚠️ **Duplicate!** The second definition overwrites the first. All callers now get the full config map.
- **MySQL tables used:** `settings_config`
- **Called by:**
  - `bot/__init__.py:144` — `_psvibe_get("sheets/config")` [SYNC]
  - `bot/api_client.py:439` — `api_fetch_sheets_config()` [SYNC]
  - `bot/api_client.py:644` — `api_fetch_sheets_config_async()` [ASYNC]
  - `customer_bot/api.py:503` — `_api_get("sheets/config")` [ASYNC]
- **Status:** ✅ Already MySQL, GSheet-free
- **Note:** Customer bot uses this to read `console_multipliers` for pricing (line 562)
- **Rename suggestion:** Move to `/api/config`

### 3. GET /api/sheets/consoles
- **Source:** `patch_routes.py:142`
- **Returns:** `{consoles: [{console_id, status, current_game, current_member, start_time}], date}`
- **MySQL tables used:** `console_status`, `console_booking`
- **Called by:**
  - `bot/handlers/waitlist.py:24` — Waitlist manager checks console availability
- **Status:** ✅ Already MySQL, GSheet-free
- **Rename suggestion:** Move to `/api/consoles`

### 4. GET /api/sheets/stock-today
- **Source:** `patch_routes.py:172`
- **Returns:** `{date, stock_in: [{item, qty, cost}], stock_out: [{item, qty, cost}], in_total, out_total}`
- **MySQL tables used:** `stock_in`, `stock_out`
- **Called by:**
  - `bot/handlers/reports.py:80` — Daily stock report
- **Status:** ✅ Already MySQL, GSheet-free
- **Rename suggestion:** Move to `/api/stock/daily`

### 5. GET /api/sheets/report-data
- **Source:** `patch_routes.py:212`
- **Returns:** `{date, total_sales, voucher_count, payment_breakdown, console_usage, top_ups, members_served}`
- **MySQL tables used:** `sales_daily`, `console_booking`, `topup_log`
- **Called by:**
  - `bot/handlers/broadcast.py:86` — End-of-day broadcast message
- **Status:** ✅ Already MySQL, GSheet-free
- **Rename suggestion:** Move to `/api/reports/daily`

### 6. GET /api/sheets/staff-breakdown
- **Source:** `patch_routes.py:264`
- **Returns:** `{staff_name: {base_salary, deductions, advances, net_pay}}` (current month)
- **MySQL tables used:** `staff_records`, `attendance_log`, `salary_advance`
- **Called by:**
  - `bot/handlers/broadcast.py:107` — End-of-day broadcast
- **Status:** ✅ Already MySQL, GSheet-free
- **Rename suggestion:** Move to `/api/staff/breakdown`

### 7. GET /api/sheets/pnl
- **Source:** `patch_routes.py:316`
- **Returns:** `{month, revenue: {console_rental, food_sales, product_sales, topup_sales}, expenses: {salaries, utilities, supplies, rent, other}, total_revenue, total_expenses, net_profit}`
- **MySQL tables used:** `sales_daily`, `topup_log`, `staff_records`
- **Called by:**
  - `bot/handlers/reports.py:293` — Monthly P&L report (with `?m=YYYY-MM` param)
- **Status:** ✅ Already MySQL, GSheet-free
- **Note:** A more comprehensive version exists as `/api/finance/pnl` (in the same file). This one is simpler.
- **Rename suggestion:** Consider merging into `/api/finance/pnl` or rename to `/api/reports/pnl`

### 8. GET /api/sheets/liability
- **Source:** `patch_routes.py:361`
- **Returns:** `{wallet_liability_mins, wallet_liability_ks, salary_advances, outstanding_payables, total_liability}`
- **MySQL tables used:** `member_wallets`, `settings_config`, `salary_advance`
- **Called by:**
  - **DEAD CODE** — No callers found in Sale Bot, Customer Bot, or Dashboard
- **Status:** ✅ Already MySQL, but unused
- **Recommendation:** Remove or keep as `/api/liability` if needed for dashboard later

### 9. GET /api/sheets/payment-methods
- **Source:** `patch_routes.py:408`
- **Returns:** `{payment_methods: [...]}` from MySQL settings
- **MySQL tables used:** `settings_config` (key: `payment_methods`)
- **Called by:**
  - **DEAD CODE** — No callers found. Sale Bot's `fetch_payment_methods()` returns a hardcoded `list(PAY_METHODS)` constant, NOT an API call.
- **Status:** ✅ Already MySQL, but unused
- **Recommendation:** Remove

### 10. GET /api/sheets/promotions
- **Source:** `patch_routes.py:424`
- **Returns:** `{promotions: [{id, promo_name, discount_type, discount_value, start_date, end_date, status}]}`
- **MySQL tables used:** `promotions`
- **Called by:**
  - **DEAD CODE** — No callers found (unfiltered, `promotions/all` is used instead)
- **Status:** ✅ Already MySQL, but unused
- **Recommendation:** Remove (duplicate of `/promotions/all`)

### 11. GET /api/sheets/promotions/all
- **Source:** `patch_routes.py:433`
- **Returns:** `{promotions: [{id, promo_name, discount_type, discount_value, start_date, end_date, status, notes}]}` — includes `notes` field
- **MySQL tables used:** `promotions`
- **Called by:**
  - `bot/handlers/reports.py:107` — Promotions summary report
- **Status:** ✅ Already MySQL, GSheet-free
- **Rename suggestion:** Move to `/api/promotions`

### 12. GET /api/sheets/promotions-log
- **Source:** `patch_routes.py:442`
- **Returns:** `{promotions_log: [{id, voucher_no, promo_id, promo_title, member_id, console_id, gross_total, discount_amt, net_total, staff_name, promo_date}]}` (last 500)
- **MySQL tables used:** `promotions_log`
- **Called by:**
  - `bot/handlers/reports.py:110` — Promotions summary report
- **Status:** ✅ Already MySQL, GSheet-free
- **Rename suggestion:** Move to `/api/promotions/log`

### 13. POST /api/sheets/promotions-log
- **Source:** `patch_routes.py:451`
- **Writes:** Promotion usage record to MySQL
- **MySQL tables used:** `promotions_log`
- **Called by:**
  - `bot/handlers/sales.py:1578` — Records promotion usage during checkout
- **Status:** ✅ Already MySQL, GSheet-free
- **Rename suggestion:** Move to `POST /api/promotions/log`

### 14. POST /api/sheets/log (defined in app.py, NOT patch_routes.py)
- **Source:** `app.py:3513`
- **Action:** Fire-and-forget AI interaction logger — **NO sheet write**, just `logger.info()`
- **Called by:**
  - `customer_bot/api.py:624` — `log_to_sheet()` function
- **Status:** ✅ Already neutered (no GSheet write). Effectively a no-op.
- **Note:** This was migrated silently. The customer bot still calls it but it does nothing useful.
- **Recommendation:** Remove or rename to `/api/log/ai-interaction`

---

## Caller Summary Table

| Endpoint | Sale Bot | Customer Bot | Dashboard |
|----------|----------|-------------|-----------|
| `GET /sheets/inventory` | ✅ (3 callers) | ❌ | ❌ |
| `GET /sheets/config` | ✅ (3 callers) | ✅ (1 caller) | ❌ |
| `GET /sheets/consoles` | ✅ (1 caller) | ❌ | ❌ |
| `GET /sheets/stock-today` | ✅ (1 caller) | ❌ | ❌ |
| `GET /sheets/report-data` | ✅ (1 caller) | ❌ | ❌ |
| `GET /sheets/staff-breakdown` | ✅ (1 caller) | ❌ | ❌ |
| `GET /sheets/pnl` | ✅ (1 caller) | ❌ | ❌ |
| `GET /sheets/liability` | ❌ **DEAD** | ❌ | ❌ |
| `GET /sheets/payment-methods` | ❌ **DEAD** | ❌ | ❌ |
| `GET /sheets/promotions` | ❌ **DEAD** | ❌ | ❌ |
| `GET /sheets/promotions/all` | ✅ (1 caller) | ❌ | ❌ |
| `GET /sheets/promotions-log` | ✅ (1 caller) | ❌ | ❌ |
| `POST /sheets/promotions-log` | ✅ (1 caller) | ❌ | ❌ |
| `GET /sheets/weekly-report` | ✅ (1 caller) | ❌ | ❌ |
| `POST /sheets/log` | ❌ | ✅ (1 caller) | ❌ |

**Dashboard uses NONE of these.** It has its own `/api/finance/*` endpoints.

---

## sheets_client.py — Remaining GSheet Dependency Audit

### Where sheets_client is still imported/used:

| File | Import/Usage | Status |
|------|-------------|--------|
| `app.py:93-96` | Imports 8 functions, but only calls `invalidate_cache("bookings")` (6 call sites) | **Residual** — no actual GSheet reads |
| `phase5_patch.py` | Uses `get_worksheet()`, `float_safe()` | **Migration tool** — already applied, can be archived |
| `archive/patch_app.py` | Heavy usage of `get_sales_daily_rows()`, `get_topup_log_rows()` | **Archived** — ignore |
| `sync_settings_to_mysql.py` | Has own copies of `int_safe()`, `float_safe()` (does NOT import sheets_client) | **Semi-independent** — uses gspread directly via its own `get_worksheet()` |

### app.py invalidate_cache call sites:
```
Line 716  → /api/bookings/extend          (after extending booking)
Line 1651 → /api/bookings (POST)          (after creating booking)
Line 1809 → /api/bookings/{id}/cancel     (after cancelling)
Line 2235 → session_timer end_session     (after ending session)
Line 2857 → admin/staff panel             (after staff booking action)
Line 2970 → session_timer extend          (after timer extension)
```
All 6 calls are **dead weight** — they invalidate a GSheet cache that nothing reads anymore.

### sync_service.py
Already gutted — 28-line stub. All GSheet sync functions replaced with no-ops. Comment at top reads: *"GSheet Sync is DISABLED (migrated to MySQL only)"*

---

## Cleanup Roadmap

### Phase 1: Safe (renamed endpoints, backward compatible)
1. Create new endpoints with clean names (e.g., `/api/config`, `/api/consoles`, `/api/reports/daily`)
2. Have old `/api/sheets/*` endpoints redirect/mirror for 1 release cycle
3. Update bot callers to use new endpoint names
4. Remove old `/api/sheets/*` endpoints

### Phase 2: Remove GSheet dependency entirely
1. Delete `sheets_client.py` (205 lines, all gspread/Google Sheets code)
2. Remove `import ... from sheets_client` from `app.py:93-96`
3. Remove all 6 `invalidate_cache("bookings")` calls from `app.py`
4. Uninstall `gspread` from venv: `pip uninstall gspread`
5. Remove `SERVICE_ACCOUNT_FILE`, `SHEET_ID`, `SHEET_*` constants from `config.py`
6. Remove Google service account JSON key file
7. Delete `phase5_patch.py` (already applied)
8. Delete `sync_settings_to_mysql.py` (already migrated)

### Phase 3: Remove dead endpoints
1. `GET /api/sheets/liability` — unused
2. `GET /api/sheets/payment-methods` — unused  
3. `GET /api/sheets/promotions` — duplicate of `/promotions/all`
4. `POST /api/sheets/log` — no-op (or rename to proper logging endpoint)

---

## Proposed New Endpoint Names

| Current | Proposed |
|---------|----------|
| `/api/sheets/inventory` | `/api/stock/fifo-valuation` |
| `/api/sheets/config` | `/api/config` |
| `/api/sheets/consoles` | `/api/consoles` |
| `/api/sheets/stock-today` | `/api/stock/daily` |
| `/api/sheets/report-data` | `/api/reports/daily` |
| `/api/sheets/staff-breakdown` | `/api/staff/breakdown` |
| `/api/sheets/pnl` | `/api/reports/pnl` (or merge into `/api/finance/pnl`) |
| `/api/sheets/weekly-report` | `/api/reports/weekly` |
| `/api/sheets/promotions/all` | `/api/promotions` |
| `/api/sheets/promotions-log` | `/api/promotions/log` (GET) |
| `/api/sheets/promotions-log` (POST) | `/api/promotions/log` (POST) |
| `/api/sheets/log` | `/api/log/ai-interaction` |

---

## Files That Need Editing for Full Removal

### API Server (`/root/psvibe_api_server/`)
| File | Action |
|------|--------|
| `config.py` | Remove `SHEET_ID`, `SHEET_*` constants, `SERVICE_ACCOUNT_FILE`, `SHEETS_SCOPES`, `CACHE_TTL_*` |
| `sheets_client.py` | **DELETE** (205 lines of gspread code) |
| `app.py` | Remove import of sheets_client (lines 93-96), remove 6 `invalidate_cache` calls, keep/rename `/api/sheets/log` |
| `patch_routes.py` | Rename 13 /api/sheets/* endpoints to clean names |
| `sync_service.py` | Already done (28-line stub) |
| `phase5_patch.py` | Archive or delete (already applied) |
| `sync_settings_to_mysql.py` | Archive or delete (already migrated) |

### Sale Bot (`/root/psvibe-sales-bot/`)
| File | Action |
|------|--------|
| `bot/__init__.py:144` | `_psvibe_get("sheets/config")` → `_psvibe_get("config")` |
| `bot/api_client.py:439` | `"sheets/config"` → `"config"` |
| `bot/api_client.py:644` | `"sheets/config"` → `"config"` |
| `bot/handlers/broadcast.py:86` | `"sheets/report-data"` → `"reports/daily"` |
| `bot/handlers/broadcast.py:107` | `"sheets/staff-breakdown"` → `"staff/breakdown"` |
| `bot/handlers/stock.py:112` | `"sheets/inventory"` → `"stock/fifo-valuation"` |
| `bot/handlers/stock.py:217` | `"sheets/inventory"` → `"stock/fifo-valuation"` |
| `bot/handlers/sales.py:1578` | `"sheets/promotions-log"` → `"promotions/log"` |
| `bot/handlers/waitlist.py:24` | `"sheets/consoles"` → `"consoles"` |
| `bot/handlers/reports.py:18` | `"sheets/inventory"` → `"stock/fifo-valuation"` |
| `bot/handlers/reports.py:80` | `"sheets/stock-today"` → `"stock/daily"` |
| `bot/handlers/reports.py:107` | `"sheets/promotions/all"` → `"promotions"` |
| `bot/handlers/reports.py:110` | `"sheets/promotions-log"` → `"promotions/log"` |
| `bot/handlers/reports.py:292` | `"sheets/weekly-report"` → `"reports/weekly"` |
| `bot/handlers/reports.py:293` | `f"sheets/pnl?m={m_str}"` → `f"reports/pnl?m={m_str}"` |

### Customer Bot (`/root/psvibe-sales-bot/customer_bot/`)
| File | Action |
|------|--------|
| `customer_bot/api.py:503` | `"sheets/config"` → `"config"` |
| `customer_bot/api.py:624` | `"sheets/log"` → `"log/ai-interaction"` (or remove call entirely) |

### Dashboard (`/root/psvibe-dashboard/`)
- No changes needed — zero references to `/api/sheets/*`

---

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| Breaking Sale Bot | LOW | All bot calls use `_psvibe_get_async` which falls back to empty `[]` or `{}` on error |
| Breaking Customer Bot | LOW | Same fallback pattern (`_api_get` returns None on failure) |
| Breaking Dashboard | NONE | Dashboard never called these endpoints |
| GSheet still needed as read-only reference | LOW | GSheet can still be viewed manually; `sync_settings_to_mysql.py` could be run one final time |
| `invalidate_cache` removal causes errors | NONE | Cache is never read anymore — removing is safe |
