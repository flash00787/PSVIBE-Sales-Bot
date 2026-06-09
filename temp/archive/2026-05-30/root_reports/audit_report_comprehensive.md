# Audit Report: Booking/Stock/Other Handlers
**Generated:** 2026-05-28 20:35 UTC
**Source:** `/root/psvibe-sales-bot/bot/` + `/root/psvibe_api_server/app.py`

---

## EXECUTIVE SUMMARY

14 files analyzed. **Major finding:** Most handlers bypass `api_client.py` typed functions and call the API server directly via `_replit_*` wrappers. **7 `_replit_*` paths do not match any server route** — calls silently return None. **6 locations still use direct gspread operations** (DEPRECATED).

---

## 1. api_client.py — 48 Typed API Functions Available

All GET/POST/PUT/DELETE endpoints properly defined. Each function wraps `_api_call()` with the correct method and path.

✅ All 48 functions present and callable.

---

## 2. API Server Routes (FastAPI) — 62 Route Endpoints

All 48 api_client.py endpoints have matching server routes ✅

---

## 3. _replit_* Bypass Wrappers (3 functions in bot __init__.py)

These wrappers call `{API_BASE_URL}/api/{path}` **directly**, bypassing `api_client.py` entirely:

| Function | Purpose |
|----------|---------|
| `_replit_get(path)` | GET request to API server |
| `_replit_post(path, payload)` | POST request to API server |
| `_replit_delete(path)` | DELETE request to API server |

**Issue:** These are a parallel, inconsistent set of API calls. Some handlers use both `_replit_*` AND `api_*` patterns.

---

## 4. Handler-by-Handler Analysis

### 4.1 handlers/booking.py (1089 lines)

| Check | Finding |
|-------|---------|
| `api_*` calls | **NONE** — 0 API client function calls |
| `_replit_*` calls | `_replit_get("sheets/consoles")` — ❌ No matching server route `GET /api/sheets/consoles` |
| | `_replit_get("bookings?status=pending")` — ❌ No route; should be `bookings/search?status=pending` |
| | `_replit_get("bookings?status=confirmed")` — ❌ Same issue |
| | `_replit_get("bookings")` — ❌ No `GET /api/bookings` (only `POST /api/bookings` exists) |
| | `_replit_post("bookings", payload)` — ✅ `POST /api/bookings` exists |
| Gspread calls | None found ✅ |
| BTN refs | 15 unique, all defined in bot __init__.py ✅ |

**🔴 Issues:** 
- Uses `_replit_*` exclusively, never calls `api_client.py`
- 4 of 5 `_replit_*` paths don't exist as server routes
- `_replit_get("bookings?status=...")` should be `_replit_get("bookings/search?status=...")`

---

### 4.2 handlers/booking_flow.py (745 lines)

| Check | Finding |
|-------|---------|
| `api_*` calls | `_api_base()` — ❌ This is NOT an api_client function! Defined in bot __init__.py |
| `_replit_*` calls | `_replit_get("bookings?status=confirmed")` — ❌ Wrong path (no GET /api/bookings) |
| | `_replit_get("bookings/{bk_id}")` — ✅ `GET /api/bookings/{booking_id}` exists |
| Gspread calls | None found ✅ |
| BTN refs | 1 unique, defined ✅ |

**🔴 Issues:**
- `api_base()` is NOT an api_client.py function (it's in bot __init__.py)
- `_replit_get("bookings?status=confirmed")` path doesn't exist

---

### 4.3 handlers/stock.py (243 lines)

| Check | Finding |
|-------|---------|
| `api_*` calls | **NONE** |
| `_replit_*` calls | `_replit_get("sheets/inventory")` — ❌ No matching server route `GET /api/sheets/inventory` |
| Gspread calls | **🔴 3 active direct gspread calls (DEPRECATED):** |
| | Line 16: `inv_sh.col_values(7)` — direct gspread read |
| | Line 26-27: `inv_sh.update("K1", ...)` — direct gspread write |
| | Line 198: `stock_sh.append_row(...)` — direct gspread write |
| BTN refs | 4 unique, all defined ✅ |

**🔴 Issues:**
- 3 active direct gspread operations with DEPRECATED comments in code
- `_replit_get("sheets/inventory")` has no matching server route

---

### 4.4 handlers/stock_in.py (292 lines)

| Check | Finding |
|-------|---------|
| `api_*` calls | **NONE** |
| `_replit_*` calls | None |
| Gspread calls | **🔴 1 active direct gspread call (DEPRECATED):** |
| | Line 252: `stock_in_sh.append_row(...)` — direct gspread write |
| BTN refs | 5 unique, all defined ✅ |

**🔴 Issue:** 1 direct gspread call with DEPRECATED comment

---

### 4.5 handlers/referral.py (138 lines)

| Check | Finding |
|-------|---------|
| `api_*` calls | **NONE** — 0 API calls of any kind |
| `_replit_*` calls | None |
| Gspread calls | None found ✅ |
| BTN refs | 3 unique, all defined ✅ |

**⚠️ Note:** No API calls at all. May rely on direct bot-state functions (`save_referral_code`, `fetch_referral_code` from __init__.py which wrap API).

---

### 4.6 handlers/discount.py (438 lines)

| Check | Finding |
|-------|---------|
| `api_*` calls | **NONE** |
| `_replit_*` calls | None |
| Gspread calls | None found ✅ |
| BTN refs | 5 unique, all defined ✅ |

**⚠️ Note:** No external API calls. Discount logic is entirely in-memory / conversation state.

---

### 4.7 handlers/waitlist.py (286 lines)

| Check | Finding |
|-------|---------|
| `api_*` calls | **NONE** |
| `_replit_*` calls | `_replit_get("sheets/consoles")` — ❌ No matching server route |
| | `_replit_get("waitlist")` — ❌ No matching server route `GET /api/waitlist` |
| | `_replit_get("waitlist?status=waiting")` — ❌ Same issue |
| | `_replit_post("waitlist/notify", ...)` — ❌ No matching server route |
| | `_replit_delete("waitlist/{entry_id}")` — ❌ No matching server route |
| Gspread calls | None found ✅ |
| BTN refs | 5 unique, all defined ✅ |

**🔴 Issues:**
- **ALL 5 `_replit_*` paths have no matching server route** — waitlist data silently not loaded
- No fallback to direct gspread or alternative data source

---

### 4.8 handlers/attendance.py (174 lines)

| Check | Finding |
|-------|---------|
| `api_*` calls | **NONE** |
| `_replit_*` calls | None |
| Gspread calls | None found ✅ |
| BTN refs | 3 unique, all defined ✅ |

**⚠️ Note:** Relies on `save_attendance()` / `fetch_attendance()` from bot __init__.py (which wrap api_client.py functions).

---

### 4.9 handlers/broadcast.py (145 lines)

| Check | Finding |
|-------|---------|
| `api_*` calls | **NONE** |
| `_replit_*` calls | `_replit_get("bookings/broadcast-targets")` — ❌ No matching server route |
| | `_replit_get("sheets/report-data")` — ❌ No matching server route |
| | `_replit_get("sheets/staff-breakdown")` — ❌ No matching server route |
| Gspread calls | Comment only (line 102 mentions previous direct gspread) ✅ |
| BTN refs | 1 unique, defined ✅ |

**🔴 Issues:**
- **ALL 3 `_replit_*` paths have no matching server route** — data silently fails

---

### 4.10 handlers/notify.py (74 lines)

| Check | Finding |
|-------|---------|
| `api_*` calls | **NONE** |
| `_replit_*` calls | `_replit_get("bookings?memberId={member_id}")` — ❌ Should be `bookings/search` |
| Gspread calls | None found ✅ |
| BTN refs | None |

**🔴 Issue:** `_replit_get("bookings?memberId=...")` must use `bookings/search?telegram_chat_id=...`

---

### 4.11 handlers/games.py (412 lines)

| Check | Finding |
|-------|---------|
| `api_*` calls | **NONE** — uses direct gspread for game data |
| `_replit_*` calls | None |
| Gspread calls | **🔴 2 active direct gspread calls:** |
| | Line 363: `sh.update_cell(row_num, 21, meta)` — updates game metadata |
| | Line 393: `sh.delete_rows(target["row"])` — deletes game row |
| BTN refs | 10 unique, all defined ✅ |

**🔴 Issues:**
- 2 active direct Google Sheets operations (games database modify/delete)
- No API calls at all; `get_game_lib_sh()` returns raw gspread worksheet

---

### 4.12 handlers/ssd_disc.py (459 lines)

| Check | Finding |
|-------|---------|
| `api_*` calls | **NONE** |
| `_replit_*` calls | None |
| Gspread calls | None found ✅ (likely uses bot module's cached data) |
| BTN refs | 13 unique, all defined ✅ |

---

## 5. Summary Table

| Handler | Lines | api* calls | Missing funcs | Gspread refs | BTN refs | _replit* calls |
|---------|------:|-----------:|--------------:|-------------:|---------:|---------------:|
| booking.py | 1089 | 0 | 0 | 0 | 15 | 5 |
| booking_flow.py | 745 | 1 | 1 | 0 | 1 | 2 |
| stock.py | 243 | 0 | 0 | **3 🔴** | 4 | 1 |
| stock_in.py | 292 | 0 | 0 | **1 🔴** | 5 | 0 |
| referral.py | 138 | 0 | 0 | 0 | 3 | 0 |
| discount.py | 438 | 0 | 0 | 0 | 5 | 0 |
| waitlist.py | 286 | 0 | 0 | 0 | 5 | **5 🔴** |
| attendance.py | 174 | 0 | 0 | 0 | 3 | 0 |
| broadcast.py | 145 | 0 | 0 | 0 | 1 | **3 🔴** |
| notify.py | 74 | 0 | 0 | 0 | 0 | 1 |
| games.py | 412 | 0 | 0 | **2 🔴** | 10 | 0 |
| ssd_disc.py | 459 | 0 | 0 | 0 | 13 | 0 |

---

## 6. Key Issues Found

### 🔴 Critical: `_replit_*` paths with no matching server route

The following `_replit_*` paths are used in handlers but have **no matching route** in the API server:

| Path | Used In | Suggested Fix |
|------|---------|---------------|
| `sheets/consoles` | booking.py, waitlist.py | Server route missing — add `GET /api/sheets/consoles` or use `api_fetch_console_status()` |
| `sheets/inventory` | stock.py | Server route missing — add `GET /api/sheets/inventory` or implement via api_client.py |
| `sheets/report-data` | broadcast.py | Server route missing — add `GET /api/sheets/report-data` |
| `sheets/staff-breakdown` | broadcast.py | Server route missing — add `GET /api/sheets/staff-breakdown` |
| `waitlist` (GET) | waitlist.py | Server route missing — add `GET /api/waitlist` |
| `waitlist/notify` | waitlist.py | Server route missing — add `POST /api/waitlist/notify` |
| `waitlist/{entry_id}` (DELETE) | waitlist.py | Server route missing — add `DELETE /api/waitlist/{entry_id}` |
| `bookings/broadcast-targets` | broadcast.py | Server route missing — add |
| `bookings?status=...` | booking.py, booking_flow.py | Use `bookings/search?status=...` instead |
| `bookings?memberId=...` | notify.py | Use `bookings/search?telegram_chat_id=...` instead |

### 🔴 Direct gspread Operations (6 locations)

| File | Line | Operation |
|------|------|-----------|
| stock.py | 16-27 | `inv_sh.col_values()`, `inv_sh.update()` — Inventory value calculation |
| stock.py | 198 | `stock_sh.append_row()` — Stock Out record |
| stock_in.py | 252 | `stock_in_sh.append_row()` — Stock In record |
| games.py | 363 | `sh.update_cell()` — Game metadata edit |
| games.py | 393 | `sh.delete_rows()` — Game deletion |

### ⚠️ Architectural: `_replit_*` bypasses `api_client.py`

**12 out of 12 handler files make ZERO api_* calls.** Every handler bypasses the typed api_client.py wrappers, using either:
- `_replit_*()` direct wrappers (bypass layer)
- Direct gspread calls (deprecated)
- Bot `__init__.py` functions (some wrap API, some use gspread directly)

The api_client.py typed functions are essentially unused by these handlers.

### ❓ `api_base()` in booking_flow.py (line 257)

`api_base()` is NOT an `api_client.py` function — it's defined in `bot/__init__.py`. The regex matched it because of the `api_` prefix. **This is a false positive** in the initial scan. It's used to construct a URL string directly rather than calling a typed API function.

---

## 7. Recommendations

1. **Fix missing server routes** — Add the 10 `_replit_*` paths listed above as proper FastAPI routes, or update handler code to use existing routes
2. **Migrate **_**replit_* to api_client.py** — Replace all `_replit_*` calls with typed `api_*()` functions, or add new typed functions for missing endpoints
3. **Eliminate direct gspread** — Replace `inv_sh`, `stock_sh`, `stock_in_sh`, `get_game_lib_sh()` calls with API endpoints
4. **Fix booking query paths** — Change `bookings?status=...` and `bookings?memberId=...` to use `bookings/search?status=...` and `bookings/search?telegram_chat_id=...`
5. **Add typed wrappers** — For waitlist, sheets/inventory, sheets/report-data, and similar, add proper `api_*()` functions to `api_client.py`

---

*Audit complete.*
