# Sales Bot — API & Sheet Dependency Audit

**Date:** 2026-05-28  
**Auditor:** OpenClaw Subagent  
**Target:** PS VIBE Sales Telegram Bot (`/root/psvibe-sale-bot`)  
**API Server:** Running on `localhost:8000` (systemd: `psvibe-api`, active)

---

## Executive Summary

| Area | Status | Issues Found |
|------|--------|-------------|
| API Client (48 functions) | ✅ All 48 map to existing endpoints | Method & path alignment correct |
| API Server Endpoints | ✅ All 48 endpoints implemented | 401 auth on unauthenticated calls (expected) |
| Google Sheet Structure | ✅ All referenced tabs exist | Minor column mapping concerns |
| **Fallback / API Usage in Bot** | 🔴 **CRITICAL** | **10 functions bypass the API entirely** |

---

## Step 1: API Client Cross-Check (`api_client.py`)

### 1.1 Function ↔ Endpoint Mapping

All 48 `api_*` functions in `api_client.py` correctly map to their corresponding endpoints on the API server. The OpenAPI schema (`/openapi.json`) confirms every endpoint exists with the correct HTTP method.

#### GET Endpoints (35 functions) — ALL MATCH ✅

| # | Function | API Path | Method |
|---|----------|----------|--------|
| 1 | `api_health` | `/api/health` | GET |
| 2 | `api_fetch_console_status` | `/api/fetch_console_status` | GET |
| 3 | `api_fetch_members` | `/api/fetch_members` | GET |
| 4 | `api_fetch_member_data` | `/api/fetch_member_data/{member_id}` | GET |
| 5 | `api_fetch_wallet_mins` | `/api/fetch_wallet_mins/{member_id}` | GET |
| 6 | `api_fetch_balance_mins` | `/api/fetch_balance_mins/{member_id}` | GET |
| 7 | `api_fetch_member_tier` | `/api/fetch_member_tier/{member_id}` | GET |
| 8 | `api_fetch_staff` | `/api/fetch_staff` | GET |
| 9 | `api_fetch_staff_names` | `/api/fetch_staff_names` | GET |
| 10 | `api_fetch_food_prices` | `/api/fetch_food_prices` | GET |
| 11 | `api_fetch_food_costs` | `/api/fetch_food_costs` | GET |
| 12 | `api_fetch_games` | `/api/fetch_games` | GET |
| 13 | `api_fetch_game_library` | `/api/fetch_game_library` | GET |
| 14 | `api_fetch_console_games` | `/api/fetch_console_games` | GET |
| 15 | `api_get_games_on_console` | `/api/get_games_on_console/{console_id}` | GET |
| 16 | `api_get_consoles_with_game` | `/api/get_consoles_with_game` | GET |
| 17 | `api_fetch_base_rate` | `/api/fetch_base_rate` | GET |
| 18 | `api_fetch_console_multiplier` | `/api/fetch_console_multiplier/{console_id}` | GET |
| 19 | `api_fetch_new_member_defaults` | `/api/fetch_new_member_defaults` | GET |
| 20 | `api_fetch_rank_thresholds` | `/api/fetch_rank_thresholds` | GET |
| 21 | `api_fetch_bonus_table` | `/api/fetch_bonus_table` | GET |
| 22 | `api_fetch_rank_table_display` | `/api/fetch_rank_table_display` | GET |
| 23 | `api_fetch_alltime_effective_rate` | `/api/fetch_alltime_effective_rate` | GET |
| 24 | `api_fetch_member_effective_rate` | `/api/fetch_member_effective_rate/{member_id}` | GET |
| 25 | `api_build_member_rate_dict` | `/api/build_member_rate_dict` | GET |
| 26 | `api_fetch_base_salaries` | `/api/fetch_base_salaries` | GET |
| 27 | `api_fetch_attendance` | `/api/fetch_attendance/{month_str}` | GET |
| 28 | `api_fetch_salary_advances` | `/api/fetch_salary_advances/{month_str}` | GET |
| 29 | `api_fetch_promotions_cached` | `/api/fetch_promotions_cached` | GET |
| 30 | `api_fetch_allowed_staff_ids` | `/api/fetch_allowed_staff_ids` | GET |
| 31 | `api_next_voucher` | `/api/next_voucher` | GET |
| 32 | `api_next_member_id` | `/api/next_member_id` | GET |
| 33 | `api_next_member_row_no` | `/api/next_member_row_no` | GET |
| 34 | `api_fetch_referral_code` | `/api/fetch_referral_code/{member_id}` | GET |
| 35 | `api_fetch_sheets_config` | `/api/sheets/config` | GET |

#### POST Endpoints (6 functions) — ALL MATCH ✅

| # | Function | API Path | Method |
|---|----------|----------|--------|
| 36 | `api_create_booking` | `/api/create_booking` | POST |
| 37 | `api_save_attendance` | `/api/save_attendance` | POST |
| 38 | `api_save_receipt_json` | `/api/save_receipt_json` | POST |
| 39 | `api_add_console_game` | `/api/add_console_game` | POST |
| 40 | `api_save_referral_code` | `/api/save_referral_code` | POST |
| 41 | `api_add_console_to_setting` | `/api/add_console_to_setting` | POST |

#### PUT Endpoints (5 functions) — ALL MATCH ✅

| # | Function | API Path | Method |
|---|----------|----------|--------|
| 42 | `api_end_booking` | `/api/end_booking/{booking_id}` | PUT |
| 43 | `api_cancel_booking` | `/api/cancel_booking/{booking_id}` | PUT |
| 44 | `api_set_game_disc_count` | `/api/set_game_disc_count` | PUT |
| 45 | `api_update_game_library_install` | `/api/update_game_library_install` | PUT |
| 46 | `api_update_member_effective_rate` | `/api/update_member_effective_rate` | PUT |

#### DELETE Endpoints (2 functions) — ALL MATCH ✅

| # | Function | API Path | Method |
|---|----------|----------|--------|
| 47 | `api_remove_console_game` | `/api/remove_console_game` | DELETE |
| 48 | `api_remove_console_from_setting` | `/api/remove_console_from_setting/{console_id}` | DELETE |

### 1.2 HTTP Method Verification

Curl tests confirm:
- `/api/fetch_members` returns **405** on POST, **401** on GET → confirms GET-only ✅
- All other endpoints return **401** (auth required) on unauthenticated access → confirms they exist ✅
- `/api/health` returns **200** without auth → confirmed ✅

### 1.3 Parameter Mismatches — NONE FOUND ✅

All `api_client.py` functions pass parameters correctly:
- Path parameters (e.g., `{member_id}`) → embedded in URL path ✅
- Query parameters (e.g., `game_title` in `get_consoles_with_game`) → passed via `params` dict ✅
- JSON body parameters (POST/PUT) → passed via `json_data` dict ✅
- Auth → API key sent as `?api_key=...` query parameter ✅

### 1.4 Error Handling in `api_client.py`

The `_api_call` helper wraps every call in `try/except` with a catch-all, logging warnings and returning `None` on any failure. This is solid for a client library. ✅

---

## Step 2: Google Sheet Structure Check

### 2.1 Sheet Identity

- **Sheet ID:** `1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA` (from `.env`)
- **Service Account:** `/root/psvibe-sale-bot/service_account.json`
- **Total Tabs:** 27 worksheets

### 2.2 Tab Verification

| Bot Reference | Tab Name in Sheet | Exists? | Row Count | Col Count | Notes |
|--------------|-------------------|---------|-----------|-----------|-------|
| `sales_sh` | `Sales_Daily` | ✅ | 1000 | 25 (18 used) | Voucher sales records |
| `setting_sh` | `Setting` | ✅ | 1000 | 27 (25 used) | All config data |
| `member_sh` | `Card_Wallet` | ✅ | 1000 | 29 (18 used) | Member wallet data |
| `stock_sh` | `Stock_Out` | ✅ | 1000 | 25 (8 used) | Stock outflow |
| `stock_in_sh` | `Stock_In` | ✅ | 1000 | 29 (8 used) | Stock inflow |
| `topup_sh` | `TopUp_Log` | ✅ | 1000 | 26 (13 used) | Top-up history |
| `inv_sh` | `Inventory` | ✅ | 1000 | 29 (12 used) | Inventory tracking |
| `get_att_sh()` | `Attendance_Log` | ✅ | 200 | 6 (5 used) | Staff attendance |
| `get_booking_sh()` | `Console_Booking` | ✅ | 1000 | 9 | Console bookings |
| `get_salary_adv_sh()` | `Salary_Advance` | ✅ | 500 | 5 | Salary advances |
| `get_game_lib_sh()` | `Game_Library` | ✅ | 993 | 29 (21 used) | Game library |
| `get_console_games_sh()` | `Console_Games` | ✅ | 968 | 5 | Game install records |

**Result: ALL 12 tab references exist in the sheet.** ✅

### 2.3 Column Index Verification

#### Setting Sheet (`setting_sh`)

| Code Reference | Column | Header Value | Expected? | Status |
|---------------|--------|-------------|-----------|--------|
| `col_values(8)` → console names | H | "Console ID" | Yes | ✅ |
| `col_values(9)` → console types | I | "Type" | Yes | ✅ |
| `col_values(10)` → multipliers | J | "Multiplier" | Yes | ✅ |
| `col_values(19)` → staff names | S | "Staff Names" | Yes | ✅ |
| `col_values(20)` → base salaries | T | "Base Salary" | Yes | ✅ |
| `col_values(4)` → food names | D | "Food Name" | Yes | ✅ |
| `col_values(5)` → food prices | E | "Selling Price" | Yes | ✅ |
| `col_values(6)` → food costs | F | "Cost Price" | Yes | ✅ |
| `cell(30, 2)` → allowed staff IDs | B30 | `6296803251,8539344655,8336350778` | Yes | ✅ |
| `cell(2, 2)` → base rate | B2 | `10,000` | Yes (Base Rate) | ✅ |
| `cell(20, 2)` → new member price | B20 | `90,000` | Yes (Card Price) | ✅ |
| `cell(21, 2)` → new member mins | B21 | `600` | Yes (Base Mins) | ✅ |
| `cell(3, 13)` → master threshold | M3 | `300,000` | Yes | ✅ |
| `cell(4, 13)` → immortal threshold | M4 | `1,000,000` | Yes | ✅ |
| `get("O1:R5")` → rank table | O-R | Top-up/Warrior/Master/Immortal | Yes | ✅ |

#### Card_Wallet Sheet (`member_sh`)

| Code Reference | Column | Header Value | Expected? | Status |
|---------------|--------|-------------|-----------|--------|
| `col_values(1)` → row numbers | A | "No" | Yes | ✅ |
| `col_values(2)` → member IDs | B | "Member ID" | Yes | ✅ |
| `row[7]` (col H) → wallet mins | H | "Balance Mins" | Yes | ✅ |
| `row[11]` (col L) → effective rate | L | *(empty header)* | ⚠️ | **See note** |
| `row[16]` (col Q) → referral code | Q | "Referral_Code" | Yes | ✅ |
| `cell(1, 11)` → reg_staff header | K | "Reg_Staff" | Yes | ✅ |
| `cell(1, 17)` → referral header | Q | "Referral_Code" | Yes | ✅ |

### 2.4 Column Concerns

#### ⚠️ Concern 1: Card_Wallet Column L (index 12) — No Header

The code uses `member_sh.update_cell(i, 12, ...)` to write effective rates for members, but **column L (index 12) has no header label**. The `update_member_effective_rate()` function reads `row[11]` (0-indexed) which maps to col L. The data exists but it's untitled.

**Impact:** Low. Data is readable/writable, just no visual label in the sheet.

#### ⚠️ Concern 2: Duplicate "Referral_Code" Columns

The Card_Wallet sheet has **two columns named "Referral_Code"**: column N (index 14) AND column Q (index 17). The code uses `row[16]` which maps to col Q (the second one). Column N appears to be a legacy/duplicate.

**Impact:** Low. Code consistently uses col Q (index 17). The duplicate header is a cosmetic issue.

---

## Step 3: 🔴 CRITICAL — API Usage & Fallback Analysis

### The `_HAS_API` Gate

The bot uses `_HAS_API` flag (set by trying to import `api_client`) to decide whether to use the API or fall back to direct gspread:
```python
try:
    from bot.api_client import (...)  # 30+ api_* functions
    _HAS_API = True
except ImportError:
    _HAS_API = False
```

### 3.1 Functions WITH API Fallback (22 functions) ✅

These functions check `_HAS_API` and gracefully fall back to gspread:

| Function | API Call | GSpread Fallback | Error Handling |
|----------|----------|------------------|----------------|
| `fetch_console_status` | `api_fetch_console_status()` | Setting + Booking sheets | No explicit try/except |
| `fetch_members` | `api_fetch_members()` | `member_sh.col_values(2)` | No explicit try/except |
| `fetch_member_data` | `api_fetch_member_data(id)` | `_get_member_rows()` lookup | No explicit try/except |
| `fetch_wallet_mins` | `api_fetch_wallet_mins(id)` | `_get_member_rows()` → `row[7]` | No explicit try/except |
| `fetch_balance_mins` | `api_fetch_balance_mins(id)` | `member_sh.get("A:H")` → `row[7]` | ✅ try/except |
| `fetch_member_tier` | `api_fetch_member_tier(id)` | `_get_member_rows()` → `row[6]` | ✅ try/except |
| `fetch_staff` | `api_fetch_staff()` | `setting_sh.col_values(19)` | ✅ try/except |
| `fetch_staff_names` | `api_fetch_staff_names()` | Via `fetch_staff()` | Inherited |
| `fetch_food_prices` | `api_fetch_food_prices()` | `setting_sh.col_values(4,5)` | No explicit try/except |
| `fetch_food_costs` | `api_fetch_food_costs()` | `setting_sh.col_values(4,6)` | No explicit try/except |
| `fetch_games` | `api_fetch_games()` | `get_game_lib_sh()` | ✅ try/except |
| `fetch_console_games` | `api_fetch_console_games()` | `get_console_games_sh()` | ✅ try/except |
| `fetch_base_rate` | `api_fetch_base_rate()` | `setting_sh.cell(2,2)` | No explicit try/except |
| `fetch_console_multiplier` | `api_fetch_console_multiplier(id)` | `setting_sh.col_values(8,10)` | ✅ try/except |
| `fetch_new_member_defaults` | `api_fetch_new_member_defaults()` | `setting_sh.cell(20,2)` | ✅ try/except |
| `fetch_rank_thresholds` | `api_fetch_rank_thresholds()` | `setting_sh.cell(3,13)` | ✅ try/except |
| `fetch_bonus_table` | `api_fetch_bonus_table()` | `setting_sh.get("O2:R5")` | ✅ try/except |
| `fetch_rank_table_display` | `api_fetch_rank_table_display()` | `setting_sh.get("O1:R5")` | ✅ try/except |
| `build_member_rate_dict` | `api_build_member_rate_dict()` | `_get_member_rows()` | ✅ try/except |
| `fetch_member_effective_rate` | `api_fetch_member_effective_rate(id)` | `_get_member_rows()` → `row[11]` | ✅ try/except |
| `fetch_base_salaries` | `api_fetch_base_salaries()` | `setting_sh.col_values(19,20)` | ✅ try/except |
| `fetch_attendance` | `api_fetch_attendance(month)` | `get_att_sh().get("A:E")` | ✅ try/except |
| `fetch_promotions_cached` | `api_fetch_promotions_cached()` | `_replit_get()` cache | No explicit try/except |
| `fetch_allowed_staff_ids` | `api_fetch_allowed_staff_ids()` | `setting_sh.cell(30,2)` | No explicit try/except |
| `next_voucher` | `api_next_voucher()` | `sales_sh.col_values(2)` | ✅ try/except |
| `next_member_id` | `api_next_member_id()` | `member_sh.col_values(2)` | ✅ try/except |
| `next_member_row_no` | `api_next_member_row_no()` | `member_sh.col_values(1)` | ✅ try/except |
| `fetch_referral_code` | `api_fetch_referral_code(id)` | `member_sh.get("A:Q")` | ✅ try/except |
| `save_referral_code` | `api_save_referral_code(id,code)` | `member_sh.update_cell()` | ✅ try/except |
| `update_member_effective_rate` | `api_update_member_effective_rate()` | `member_sh.update_cell(i,12)` | ✅ try/except |
| `save_receipt_json` | `api_save_receipt_json()` | Local file write | ✅ try/except |
| `fetch_salary_advances` | `api_fetch_salary_advances(month)` | Via `get_salary_adv_sh()` | Inherited |
| `get_consoles_with_game` | `api_get_consoles_with_game()` | Via `fetch_console_games()` | No explicit try/except |
| `get_games_on_console` | `api_get_games_on_console(cid)` | Via `fetch_console_games()` | No explicit try/except |
| `fetch_alltime_effective_rate` | `api_fetch_alltime_effective_rate()` | Via `build_member_rate_dict()` | ✅ try/except |
| `fetch_sheets_config` | `api_fetch_sheets_config()` | Not used in bot currently | N/A |

### 3.2 🔴 Functions BYPASSING API (10 functions)

These functions have corresponding `api_*` wrappers in `api_client.py` AND the API server implements the endpoints, but the bot's `__init__.py` **never calls them**, going straight to direct gspread:

| # | Function | API Available? | Bot Uses API? | What Bot Does Instead |
|---|----------|---------------|---------------|----------------------|
| 1 | **`create_booking`** | `api_create_booking()` | ❌ | `get_booking_sh().append_row()` |
| 2 | **`end_booking`** | `api_end_booking(id)` | ❌ | `get_booking_sh().update()` |
| 3 | **`cancel_booking`** | `api_cancel_booking(id)` | ❌ | `get_booking_sh().update()` |
| 4 | **`save_attendance`** | `api_save_attendance()` | ❌ | `get_att_sh().update()` / `append_row()` |
| 5 | **`add_console_game`** | `api_add_console_game()` | ❌ | `get_console_games_sh().append_row()` |
| 6 | **`remove_console_game`** | `api_remove_console_game()` | ❌ | `get_console_games_sh().delete_rows()` |
| 7 | **`set_game_disc_count`** | `api_set_game_disc_count()` | ❌ | `get_game_lib_sh().update_cell()` |
| 8 | **`update_game_library_install`** | `api_update_game_library_install()` | ❌ | `wb.worksheet("Game_Library").update_cell()` |
| 9 | **`add_console_to_setting`** | `api_add_console_to_setting()` | ❌ | `setting_sh.update()` |
| 10 | **`remove_console_from_setting`** | `api_remove_console_from_setting()` | ❌ | `setting_sh.update()` |

**These are the most critical functions in the bot** — they handle:
- Starting/ending console sessions (revenue generation)
- Managing bookings (operations)
- Staff attendance (payroll)
- Game library management (inventory)
- Console configuration (pricing)

### 3.3 Risks of Direct GSpread Access

1. **No single source of truth**: The API server and the bot both write to sheets directly. Changes made via API won't reflect in the bot until cache TTL expires.
2. **Race conditions**: Concurrent writes from bot + API server can cause data loss.
3. **No audit trail**: API server logs all mutations. Direct gspread writes are invisible to the API.
4. **Rate limit exposure**: Direct gspread calls eat into Google Sheets API quotas independently.
5. **Cache inconsistency**: Functions like `add_console_game` invalidate `_CGAME_ROWS` cache, but if the API server made a change, the bot's cache is stale.
6. **No retry logic**: The `_SHEETS_RETRY_CODES` wrapper (429/500/503 retry) is applied at the worksheet level, but the bot's direct calls bypass the unified error handling the API server provides.

---

## Step 4: Summary of Issues by Severity

### 🔴 Critical (Should Fix Immediately)

1. **10 mutation functions bypass the API** — The bot reads data through the API (with fallback) but writes data directly to Google Sheets. This creates a split-brain architecture where:
   - **Read path**: API → Sheets (with fallback to direct)
   - **Write path**: Direct Sheets only (no API)
   - The API server has no visibility into bookings, attendance, game management, or console configuration changes made by the bot.

2. **No `_HAS_API` gate on write functions** — If the API server is unavailable, the bot silently falls back to direct gspread (which works), but this means:
   - The API server never learns about the mutation
   - No consistency between API and bot state
   - No audit trail

### ⚠️ Warning (Should Fix Soon)

3. **`save_attendance` has no API call at all** — Unlike other functions that check `_HAS_API`, `save_attendance` goes straight to `get_att_sh()`. The API endpoint exists and works, but is completely ignored.

4. **`save_receipt_json` API saves to log only** — The API server's implementation only logs (doesn't actually save receipts to sheets), while the bot saves to local files AND posts to the API. The API endpoint is effectively a no-op for the receipt data.

5. **Card_Wallet Column L has no header** — The effective_rate column lacks a header label, making the sheet harder to audit manually.

### ℹ️ Info (Low Priority)

6. **Duplicate "Referral_Code" column in Card_Wallet** — Columns N and Q are both labeled "Referral_Code". Code uses col Q. Col N is unused/legacy.

7. **`set_game_disc_count` has API but uses gspread directly** — Like the other 9 bypass functions, it uses direct gspread. However, it has proper cache invalidation and error handling.

8. **`_get_cfg()` caching layer** — Some reads use `_get_cfg()` caching which adds another layer between API and sheets. Makes debugging harder when data doesn't match.

---

## Step 5: Recommendations

### Immediate Fix: Add `_HAS_API` gates to all 10 bypassed functions

```python
def create_booking(console_id, member_id, staff, notes="", planned_end=""):
    if _HAS_API:
        result = api_create_booking(console_id, member_id, staff, notes, planned_end)
        if result is not None:
            return result.get("data", {}).get("booking_id", "")
        logging.warning("API create_booking failed, falling back to gspread")
    # ... existing gspread code ...
```

Apply this pattern to ALL 10 bypassed functions:
1. `create_booking`
2. `end_booking`
3. `cancel_booking`
4. `save_attendance`
5. `add_console_game`
6. `remove_console_game`
7. `set_game_disc_count`
8. `update_game_library_install`
9. `add_console_to_setting`
10. `remove_console_from_setting`

### Medium-Term: Clean Up

- Add header label to Card_Wallet column L ("Effective_Rate")
- Remove duplicate "Referral_Code" column N in Card_Wallet
- Consider removing the `_get_cfg()` caching for consistency
- Add metric tracking to distinguish API vs direct gspread calls

### Validation: Test After Fix

After adding `_HAS_API` gates:
1. Verify API server logs show mutations
2. Verify sheet data consistency between API and bot views
3. Run a session end-to-end: create booking → end booking → check both sheet and API

---

## Appendix A: Sheet Tab Inventory (All 27 Tabs)

| Tab Name | Rows | Cols | Used By Bot? |
|----------|------|------|-------------|
| Dashboard | 1000 | 27 | Analytics only |
| Sales_Daily | 1000 | 25 | ✅ `sales_sh` |
| Stock_Out | 1000 | 25 | ✅ `stock_sh` |
| Game_Library | 993 | 29 | ✅ `get_game_lib_sh()` |
| TopUp_Log | 1000 | 26 | ✅ `topup_sh` |
| Card_Wallet | 1000 | 29 | ✅ `member_sh` |
| Inventory | 1000 | 29 | ✅ `inv_sh` |
| Stock_In | 1000 | 29 | ✅ `stock_in_sh` |
| Setting | 1000 | 27 | ✅ `setting_sh` |
| Salary_Payroll | 200 | 12 | Analytics only |
| Attendance_Log | 200 | 6 | ✅ `get_att_sh()` |
| Salary_Advance | 500 | 5 | ✅ `get_salary_adv_sh()` |
| Receipts | 1000 | 26 | Receipt storage |
| Console_Booking | 1000 | 9 | ✅ `get_booking_sh()` |
| Console_Games | 968 | 5 | ✅ `get_console_games_sh()` |
| Capital_Setup | 500 | 16 | Finance module |
| Assets_Register | 500 | 16 | Finance module |
| OPEX_Log | 500 | 16 | Finance module |
| Accounts | 500 | 16 | Finance module |
| Account_Transfers | 500 | 16 | Finance module |
| Payables | 500 | 16 | Finance module |
| Receivables | 500 | 16 | Finance module |
| Advance_Staff | 500 | 16 | Finance module |
| Prepaid_Expenses | 500 | 16 | Finance module |
| Advance_Payments | 500 | 16 | Finance module |
| Promotions | 200 | 14 | Promo module |
| Promotions_Log | 1000 | 10 | Promo module |

---

## Appendix B: API Server Architecture

```
FastAPI Server (psvibe-api, localhost:8000)
├── app.py          — 48 route handlers + auth middleware
├── config.py       — Sheet IDs, MySQL config, API keys
├── sheets_client.py — gspread wrappers with caching
├── models.py       — Pydantic models
├── analytics.py    — Analytics endpoints
├── sync_service.py — MySQL ↔ Sheets sync
├── db_client.py    — MySQL connection pool
└── dashboard_bot.py — Dashboard bot integration
```

The API server uses the SAME Google Sheet and service account as the bot, which is why split-brain writes are possible.

---

*End of Audit Report*
