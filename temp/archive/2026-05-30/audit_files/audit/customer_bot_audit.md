# 🔍 Customer Bot — Full Audit Report

**Date:** 2026-05-28  
**Bot:** `@psvibe_customer_service_bot`  
**VPS:** `5.223.81.16`  
**Repo:** `/root/psvibe-sale-bot/customer_bot/`  
**Status:** 🟡 RUNNING (PID 357061) — but with critical runtime failures  
**Systemd:** `psvibe_customer_bot.service` — properly configured, envs loaded

---

## Executive Summary

The Customer Bot **IS RUNNING** but is effectively **BROKEN** in production. Three P0 issues mean:
1. **Every API call fails silently** (wrong endpoint paths — 404s everywhere)
2. **3 command handlers crash at import time** (missing `booking.py`)
3. **The entire booking flow is stubbed out** (all states are `lambda: None`)

The bot polls Telegram successfully but **cannot serve users**. It logs no errors because exceptions are swallowed in `api.py` catch blocks (return `None` instead of raising).

---

## Phase 1: Handler & Flow Map

### Command Handlers (Registered in `main.py`)

| Command | Handler | Status |
|---|---|---|
| `/start` | `cmd_start` | ✅ Implemented |
| `/menu` | `cmd_menu` | ✅ (delegates to `show_main_menu`) |
| `/today` | `cmd_today` | ✅ Implemented |
| `/rate` | `cmd_rate` | ✅ Implemented |
| `/myid` | `cmd_myid` | ✅ Implemented |
| `/help` | `cmd_help` | ✅ Implemented |
| `/contact` | `cmd_contact` | ✅ Implemented |
| `/location` | `cmd_location` | ✅ Implemented |
| `/promotions` | `cmd_promotions` | ✅ Implemented |
| `/refresh` | `cmd_refresh` | ✅ Implemented |
| `/balance` | `cmd_balance` | ✅ Implemented |
| `/games` | `cmd_game_library` | ✅ Implemented |
| `/status` | `cmd_console_status` | ✅ Implemented |
| `/book` | `cmd_book` | ⚠️ Registered (but booking flow stubbed) |
| `/booking` | `cmd_book` | ⚠️ Alias of `/book` |
| `/cancel` | `cmd_cancel` | ✅ Part of ConversationHandler fallback |
| `/feedback` | `cmd_feedback` | ✅ Implemented |
| `/mybookings` | `cmd_mybookings` | 🔴 **CRASHES** → `from .booking import` fails |
| `/refer` | `cmd_refer` | 🔴 **CRASHES** → `from .booking import` fails |
| `/waitlist` | `cmd_waitlist` | 🔴 **CRASHES** → `from .booking import` fails |

### Callback Handlers

| Pattern | Handler | Status |
|---|---|---|
| `^fb:rate:` | `cb_feedback_rating` | ✅ Registered, logic exists |
| `^fb:comment_prompt:` | `cb_feedback_comment_prompt` | ⚠️ Registered but pattern is `fb:comment_prompt:` not `fbc:` (mismatch with button callback_data `fbc:{rating}:{bk_id}`) |
| `^fb:skip$` | `cb_feedback_skip` | ⚠️ Registered as `fb:skip` but button data is `fbskip` |
| `^bk_mem:` | `lambda: None` | 🔴 **STUB** |
| `^bk_sel:` | `lambda: None` | 🔴 **STUB** |
| `^bk_dc:` | `lambda: None` | 🔴 **STUB** |
| `^bkdate:` | `lambda: None` | 🔴 **STUB** |
| `^(bktime:\|bk_custom:)` | `lambda: None` | 🔴 **STUB** |
| `^bk_con:` | `lambda: None` | 🔴 **STUB** |
| `^bk_dur:` | `lambda: None` | 🔴 **STUB** |
| `^bk_game:` | `lambda: None` | 🔴 **STUB** |
| `^bk_cp:` | `lambda: None` | 🔴 **STUB** |
| `^bk_ok:` | `lambda: None` | 🔴 **STUB** |

### Message Handler

| Filter | Handler | Status |
|---|---|---|
| `TEXT & ~COMMAND` (menu catch-all) | `handle_menu_buttons` | ✅ Routes through menu buttons + AI |

### ConversationHandler — Booking Flow

**States Defined (16 states):**
```
BK_MEMBER_CHECK(0) → BK_MEMBER_SELECT(1) → BK_PHONE_VERIFY(2) → BK_DATA_CONFIRM(3) →
BK_NAME(4) → BK_PHONE(5) → BK_DATE(6) → BK_TIME(7) →
BK_CONSOLE(8) → BK_DURATION(9) → BK_GAME(10) → BK_CONSOLE_PREF(11) →
BK_CONFIRM(12) → BK_DUP_WARN(13) → BK_DISC_WARN(14) → BK_CON_CONFLICT(15)
```
**All stubbed with `lambda u,c: None`** — no actual booking logic exists.

### States Not in ConversationHandler but Defined

```
WL_PREF=100, WL_NAME=101, WL_PHONE=102, WL_CONFIRM=103
```
These waitlist states are **defined but never used** — waitlist handlers also point to the missing `booking.py`.

### Issues Found

1. **🔴 P0: `from .booking import` fails** — `booking.py` doesn't exist at `customer_bot/booking.py`. The actual files are at:
   - `/root/psvibe-sale-bot/bot/handlers/booking.py`
   - `/root/psvibe-sale-bot/handlers/booking.py`

2. **🔴 P0: All booking conversation states are stubs** — every state has `lambda u,c: None`

3. **🔴 P1: Feedback callback pattern mismatch** — `cb_feedback_comment_prompt` registered for `^fb:comment_prompt:` but buttons use `fbc:{rating}:{bk_id}`. The `fb:skip` pattern also mismatches button data `fbskip`.

4. **⚠️ P2: Handler re-definition bug** — `BK_*` constants are defined twice in `handlers.py`:
   - First: Lines ~20-24 via `range(16)` unpack
   - Second: Lines ~280-283 via `range(16)` unpack (duplicate re-definition)

5. **⚠️ P2: `BK_END = -1`** — defined locally in handlers.py (line ~285) but also exported from `__init__.py`. In `main.py`, `BK_END` is used as a state with `MessageHandler`, but the export is confusing since it's a magic number, not a ConversationHandler state range.

6. **⚠️ P2: `show_main_menu` doesn't show menu keyboard** — just sends "Welcome" text without `reply_markup=MAIN_MENU_KB`

7. **⚠️ P2: Dead functions** — `_bk_intercept_menu()`, `_bk_step()`, and `_fmt_hour()` (in handlers.py, duplicate of prompts.py version) are defined but never called

8. **⚠️ P2: `/cancel` command** — The ConversationHandler has `CommandHandler("cancel", cmd_cancel)` as fallback, but `main.py` also registers `CommandHandler("cancel", cmd_cancel)` globally. The global one will always intercept first, bypassing the conversation fallback.

9. **⚠️ P2: `cmd_book_from_chat`** — Defined but never registered as a handler

---

## Phase 2: API Integration Verification

### API_BASE_URL
- **Setting:** `http://localhost:8000` ✅ (API server confirmed running)
- **API_KEY:** Loaded correctly from `/etc/psvibe/secrets.env` ✅

### Endpoint Mapping — CRITICAL MISMATCHES

The customer bot's `api.py` calls paths that **DO NOT EXIST** on the backend:

| Called by Bot | Expected Backend Path | Actual Backend Path | Status |
|---|---|---|---|
| `/api/sheets/config` | `/api/sheets/config` | `/api/sheets/config` | ✅ Works |
| `/api/sheets/members-list` | `/api/sheets/members-list` | `/api/fetch_members` | 🔴 404 |
| `/api/sheets/game-library` | — | `/api/fetch_games` or `/api/fetch_game_library` | 🔴 404 |
| `/api/sheets/consoles` | — | `/api/fetch_console_status` | 🔴 404 |
| `/api/sheets/settings/contacts` | — | **DOES NOT EXIST** | 🔴 404 |
| `/api/sheets/promotions` | — | `/api/fetch_promotions_cached` | 🔴 404 |
| `/api/sheets/sales-summary` | — | **DOES NOT EXIST** | 🔴 404 |
| `/api/bot-users/track` | — | **DOES NOT EXIST** | 🔴 404 |
| `/api/sheets/log` | — | **DOES NOT EXIST** | 🔴 404 |
| `/api/bookings?telegramChatId=...` | — | **DOES NOT EXIST** | 🔴 404 |
| `/api/bookings/{id}` (GET) | — | **DOES NOT EXIST** | 🔴 404 |
| `/api/bookings/{id}/status` (PATCH) | — | **DOES NOT EXIST** | 🔴 404 |
| `/api/feedback` (POST) | — | **DOES NOT EXIST** | 🔴 404 |

### API Functions → Endpoint Map

**`api.py` exports:**

| Function | Method | Path | Status |
|---|---|---|---|
| `_api_get` | GET | `{API_BASE}/api/{path}` | ✅ Generic helper |
| `_api_post` | POST | `{API_BASE}/api/{path}` | ✅ Generic helper |
| `_api_patch` | PATCH | `{API_BASE}/api/{path}` | ✅ Generic helper |
| `_api_delete` | DELETE | `{API_BASE}/api/{path}` | ✅ Generic helper |
| `_tg_send` | POST | `api.telegram.org/bot{TOKEN}/sendMessage` | ✅ External |
| `_fetch_games` | GET | `api/sheets/game-library` | 🔴 404 |
| `_fetch_games_full` | GET | `api/sheets/game-library` | 🔴 404 |
| `_fetch_members` | GET | `api/sheets/members-list` | 🔴 404 |
| `_fetch_consoles` | GET | `api/sheets/consoles` | 🔴 404 |
| `_fetch_contacts` | GET | `api/sheets/settings/contacts` | 🔴 404 |
| `_fetch_promotions` | GET | `api/sheets/promotions` | 🔴 404 |
| `_fetch_config` | GET | `api/sheets/config` | ✅ 200 |
| `_fetch_sales_data` | GET | `api/sheets/sales-summary` | 🔴 404 |
| `_get_linked_phone` | GET | `api/bookings?telegramChatId=...` | 🔴 404 |
| `_get_linked_member_id` | (calls `_get_linked_phone`) | — | 🔴 Cascading |
| `log_to_sheet` | POST | `api/sheets/log` | 🔴 404 |
| `track_usage` | POST | `api/bot-users/track` | 🔴 404 |

### Impact

Every "403" call (Not Found → swallowed) means:

- **Game library never loads** — `cmd_game_library` returns "⚠️ Game data မရဘူး"
- **Console status never loads** — `cmd_console_status` returns "⚠️ Console data မရပါ"
- **Member lookups fail** — `_search_member` returns `{"found": False}`
- **Contact info fails** — `cmd_contact` shows no admin contacts
- **Promotions fail** — always shows "no promotions"
- **Balance check fails** — `cmd_balance` always shows "not linked"
- **Today's status fails** — `cmd_today` shows no data
- **Usage tracking silently fails** — no Bot_Users updates
- **AI logs never written** — no sheet logging
- **Bookings can't be canceled via text** — `_text_cancel_booking` fails on API call
- **My Bookings crashes** — import error from missing `booking.py`

---

## Phase 3: AI Functionality Status

### Gemini Setup
- **API Key:** `GEMINI_API_KEY` present in env ✅
- **Library:** `google-genai 2.6.0` installed in venv ✅
- **Model:** `gemini-3.5-flash` configured ✅
- **Client init:** `asyncio.Lock` prevents race conditions ✅

### Async Bug Fix Verification
- ✅ All `await` keywords are present in async functions
- ✅ `_get_gemini_client()` uses `async with _client_init_lock`
- ✅ `_ai_reply()` properly awaits `_get_gemini_client()`, `_build_search_tool()`, `_get_cached_system_prompt()`, etc.
- ✅ Gemini calls wrapped in `asyncio.to_thread()` (SDK is sync)
- ✅ Typing indicator managed via `asyncio.create_task()`
- ✅ No synchronous blocking calls detected

### Rate Limiting
- ✅ Per-user cooldown: 3 seconds (`_AI_COOLDOWN = 3.0`)
- ✅ `_check_ai_rate_limit()` checks `_ai_last_call` dict
- ✅ Rate-limited users are silently skipped (logged but no reply)

### Prompt Caching
- ✅ System prompt cached with 60s TTL (`_PROMPT_CACHE_TTL = 60`)
- ✅ Cache key includes: priority_care flag + current hour
- ✅ AI query response cache: 120s TTL with MD5 hash key
- ✅ Cached responses still logged to sheet and tracked

### Search Tool
- ✅ `search_member` Gemini function declaration built correctly
- ✅ Two-turn flow: Turn 1 with tool → Turn 2 with function result
- ✅ `_search_member()` searches by ID, phone, name
- ✅ Rank computation reads live thresholds from config
- ⚠️ However, **both `_fetch_members()` and `_fetch_config()` will fail** due to API path mismatch (see Phase 2)

### Error Handling
- ✅ Retry logic for 429, 502, 503 with exponential backoff (1s → 2s → 4s)
- ✅ User-friendly Burmese error messages for rate limits, 503, generic errors
- ✅ Fallback text when Gemini returns empty response
- ⚠️ `_ai_reply()` catches all exceptions but `api.py` functions swallow errors (return `None`), so the AI function will work for pure text responses but **member lookups will silently fail**

---

## Phase 4: Sheet Integration

### Sheet ID
- **Setting:** `1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA` (from `.env`) ✅
- **Service Account:** Authenticated via `service_account.json` ✅
- **gspread:** v6.2.1 installed ✅

### Sheet Structure (from gspread)
The sales bot's `bot/__init__.py` references these worksheets in the Google Sheet:
- `Sales_Daily` — Daily sales records
- `Setting` — Config (rates, multipliers, contacts, staff, etc.)
- `Card_Wallet` — Member data (IDs, names, phones, wallet mins, rank, spend)
- `Stock_Out` — Stock outflow records
- `Stock_In` — Stock inflow records
- `TopUp_Log` — Top-up transactions
- `Inventory` — Current inventory
- `Game_Library` — Game catalog
- `Console_Games` — Console-game installation mapping
- `Console_Booking` — Booking records
- `Attendance_Log` — Staff attendance

### Bot_Users Sheet
- **🔴 Bot_Users sheet does NOT exist** — The customer bot calls `api/bot-users/track` which is a broken path. The gspread-based sales bot references `Bot_Users` as a concept but the actual tracking happens through the API.
- **`track_usage()` function** in `api.py` silently fails every time
- **`log_to_sheet()` function** in `api.py` also silently fails

### Sheet Access
- ✅ gspread successfully connected and reading from `Card_Wallet`, `Game_Library`, `Setting` sheets
- ✅ Service account has Editor access (verified by successful reads)
- ⚠️ Write operations go through the API which has mismatched endpoints

---

## Phase 5: Code Completeness & Quality

### Import Check

| Import | Source | Status |
|---|---|---|
| `from .data.prompts import ...` | `data/prompts.py` | ✅ Resolves |
| `from . import api as _api` | `api.py` | ✅ Resolves |
| `from .ai import _ai_reply` | `ai.py` | ✅ Resolves |
| `from .data.games import ...` | `data/games.py` | ✅ Resolves |
| `from .booking import ...` | `customer_bot/booking.py` | 🔴 **DOES NOT EXIST** |
| `from bot import MMT, now_mmt, today_str` | `bot/__init__.py` | ✅ Resolves |

### Dead Code
1. `_bk_intercept_menu()` — defined but never called
2. `_bk_step()` — defined but never called
3. `cmd_book_from_chat()` — defined but never registered as handler
4. `_fmt_hour()` in handlers.py — duplicate of `_fmt_hour()` in prompts.py
5. `BOOKING_INTENT_FILTER` — defined but never registered as a filter
6. `_detect_booking_intent()` — defined but not used (booking flow is stubbed)
7. `BUFFER_GLOBAL_WAIT = 0.25` — defined but never used
8. `CONSOLE_TYPES`, `DURATION_OPTS` — defined but never used

### Error Handling Issues
1. **🔴 P2: Silent failures in api.py** — All `_fetch_*` functions catch `ValueError` and return `None`/`[]`/`{}` instead of raising. This means the 404s from wrong endpoints are silently swallowed with no log indication.
2. **⚠️ P2: `log_to_sheet`** catches `Exception` and only logs warning — API failures in logging are invisible
3. **⚠️ P2: `track_usage`** catches `Exception` and only logs warning — usage tracking failures are invisible
4. **⚠️ P2: Handler import would crash** — `cmd_mybookings`, `cmd_refer`, `cmd_waitlist` would raise `ImportError` if called, but since they're lazily imported inside the functions, the crash only happens at call time, not startup

### Duplicate Definitions
1. **`BK_MEMBER_CHECK` through `BK_CON_CONFLICT`** — defined twice in handlers.py (lines ~20 and ~280)
2. **`_fmt_hour()`** — defined in both `handlers.py` and `prompts.py`

---

## 🔴 Priority Fixes

### P0 — CRITICAL (Bot non-functional)

| # | Issue | Fix |
|---|---|---|
| 1 | **API endpoint paths all wrong** | Rewrite all `_fetch_*`, `log_to_sheet`, `track_usage` paths in `api.py` to match actual backend endpoints: `fetch_members`, `fetch_games`, `fetch_console_status`, `fetch_promotions_cached`. For missing endpoints (`bot-users/track`, `sheets/log`, `sheets/settings/contacts`, `bookings/*`, `feedback`), either create backend endpoints or implement fallback. |
| 2 | **Missing `customer_bot/booking.py`** | Copy `/root/psvibe-sale-bot/handlers/booking.py` to `/root/psvibe-sale-bot/customer_bot/booking.py` and adapt imports. |
| 3 | **Booking conversation fully stubbed** | Migrate booking handlers from the old `_v1_compat.py` backup (mentioned in `main.py` docstring). All `lambda u,c: None` must be replaced with real handlers. |

### P1 — HIGH (Features broken)

| # | Issue | Fix |
|---|---|---|
| 4 | **Feedback callback pattern mismatch** | Change `cb_feedback_comment_prompt` registration pattern from `^fb:comment_prompt:` to `^fbc:` and `cb_feedback_skip` from `^fb:skip$` to `^fbskip$` to match actual button data. |
| 5 | **Missing backend endpoints needed by bot** | The backend needs new endpoints: `POST /api/bot-users/track`, `POST /api/sheets/log`, `GET /api/sheets/settings/contacts`, `GET /api/bookings?telegramChatId=`, `GET /api/bookings/{id}`, `PATCH /api/bookings/{id}/status`, `POST /api/feedback`. |

### P2 — MEDIUM (Code quality)

| # | Issue | Fix |
|---|---|---|
| 6 | **Duplicate BK_* constant definitions** | Remove the second `range(16)` unpack at lines ~280. |
| 7 | **`show_main_menu` missing keyboard** | Add `reply_markup=MAIN_MENU_KB` to the reply. |
| 8 | **`/cancel` double registration** | Remove the global `CommandHandler("cancel", cmd_cancel)` — it's already in the ConversationHandler fallback. |
| 9 | **Remove dead code** | Delete unused functions: `_bk_intercept_menu`, `_bk_step`, `cmd_book_from_chat`, `_fmt_hour` (duplicate in handlers.py), `BOOKING_INTENT_FILTER`, `_detect_booking_intent`, `BUFFER_GLOBAL_WAIT`, `CONSOLE_TYPES`, `DURATION_OPTS`. |
| 10 | **Silent API failures** | Add `logging.error()` before returning `None` in `_fetch_*` catch blocks so failures are visible in logs. |

### P3 — LOW (Nice to have)

| # | Issue | Fix |
|---|---|---|
| 11 | **Unused waitlist states** | Either implement waitlist functionality or remove `WL_PREF`-`WL_CONFIRM` state constants. |
| 12 | **`BK_END = -1` magic number** | Use a proper sentinel like `BK_END = 16` or define it explicitly. |
| 13 | **`_is_tracked_customer` async but unused** | Either use it or remove it. |

---

## Summary

The Customer Bot has **excellent architecture** (clean separation, async-first, caching, rate limiting) but is **critically broken** because:

1. **API paths don't match the backend** — every data fetch returns 404 (silently swallowed)
2. **Booking module is missing** — 3 command handlers crash on import
3. **Booking conversation is entirely stubbed** — all 16 states are no-ops

The bot effectively only handles:
- `/start` (greeting with no keyboard)
- `/help` (text list)
- `/contact` (empty unless contacts cached)
- `/rate` (empty — API fails)
- `/myid` (works — no API needed)
- `/refresh` (works — clears user_data)
- **AI chat** (works for text-only responses, but member/balance lookups fail silently)

**Estimated fix effort:** Medium (1-2 days)
- P0 fixes: Rewrite API paths (~2 hours) + copy booking.py (~30 min) + restore booking handlers from backup (~3 hours)
- P1 fixes: Create missing backend endpoints (~4 hours) + fix callback patterns (~30 min)
- P2 fixes: Code cleanup (~2 hours)
