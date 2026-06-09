# Sales Bot Completeness Audit

**Date:** 2026-05-28
**Codebase:** `/root/psvibe-sale-bot/`
**Python files:** 31 (.py files in `bot/` and `bot/handlers/`)
**Total LOC:** ~15,000+ across bot package

---

## 1. Critical Bugs

### 1.1 BotState Class Name Collision (CRITICAL)

**File:** `bot/__init__.py`
**Lines:** 864 (IntEnum) and 1560 (dataclass)

The `BotState` name is defined twice:
1. **Line 864:** `class BotState(IntEnum)` — conversation states (0–176)
2. **Line 1560:** `@dataclass class BotState` — config/member cache container

The second definition **shadows** the first. After module load, `BotState` resolves to the `@dataclass`, not the `IntEnum`. 

**Impact:** "Works by accident." Module-level aliases (`MAIN_MENU = BotState.MAIN_MENU`, etc.) were assigned *before* the shadow, so they retain correct integer values. `app.py` uses these bare aliases (e.g., `MAIN_MENU: [handler...]`), so the conversation flow works. However:
- `from bot import BotState` returns the dataclass, not the IntEnum
- Any code relying on `BotState.MAIN_MENU` after import would silently fail
- The `__all__` exports `BotState`, but which one? (It's evaluated at module load, so it captures the IntEnum, but then the namespace value changes)

**Fix:** Rename the dataclass to `BotConfig` or `CacheState`:

```python
@dataclass
class BotConfig:  # was: BotState
    cfg: dict = field(default_factory=dict)
    cfg_ts: float = 0.0
    member_rows: list = field(default_factory=list)
    member_ts: float = 0.0
```

### 1.2 Duplicate `keep_alive` Function

**Files:** 
- `bot/__init__.py` line 164 — used by `main.py`
- `bot/keep_alive.py` line 76 — **dead code, never imported**

`main.py` does `from bot import keep_alive` which resolves to the version in `__init__.py`. The standalone `keep_alive.py` module is **never imported by anything** — it is dead code.

Both functions serve a health-check HTTP server on port 8080. The `__init__.py` version uses aliased imports (`_HTTPServer`, `_BaseHandler`); the standalone version uses the real names.

**Fix:** Delete `bot/keep_alive.py` or consolidate into a single implementation.

---

## 2. Broken / Suspicious Imports

### 2.1 Dead `fcntl` Import

**File:** `bot/__init__.py` line 7
```python
import fcntl
```
`fcntl` is imported at module level but **never used anywhere** in the file. This is a Unix-specific module and has no purpose here since file locking was removed or never implemented.

**Fix:** Remove the import.

### 2.2 Dead `signal` Import

**File:** `bot/__init__.py` line 8
```python
import signal
```
`signal` is never used anywhere in `__init__.py`. Signal handling is done in `main.py`.

**Fix:** Remove the import.

### 2.3 Dead `sys` Import

**File:** `bot/keep_alive.py` line 8
```python
import sys
```
`sys` is never used in `keep_alive.py`.

**Fix:** Remove the import.

### 2.4 Dead `sys` Import

**File:** `bot/app.py` line 3
```python
import sys
```
`sys` is never used in `app.py`.

**Fix:** Remove the import.

### 2.5 Unused Telegram Import: `ForceReply`

**File:** `bot/__init__.py` line 173
```python
from telegram import BotCommand, ForceReply, InlineKeyboardButton, ...
```
`ForceReply` is imported in `__init__.py` but **only used** in `handlers/booking_flow.py` (which does its own local import from `telegram`). Since `__init__.py` re-exports via `from bot.handlers import *`, the `ForceReply` from `__init__.py` isn't needed.

**Impact:** Low — just wasted namespace slot. `ReplyKeyboardRemove` is similarly available in both places.

### 2.6 All Handler Step Functions Verified — ALL PRESENT ✅

Every `step_*` function referenced in `app.py`'s `states` dict has a corresponding `def step_*` in the handlers directory. **Zero missing step functions.**

### 2.7 All Callback Functions Verified — ALL PRESENT ✅

Every `cb_*` function registered in `app.py` has a corresponding definition. **Zero missing callbacks.**

### 2.8 All Command Handlers Verified — ALL PRESENT ✅

Every `CommandHandler` in `app.py`'s entry points, fallbacks, and standalone registrations has a corresponding `async def cmd_*` function. **Zero missing command handlers.**

---

## 3. `__all__` Export Issues

**File:** `bot/__init__.py` line 131

### 3.1 All 379 `__all__` Names ARE Defined ✅

No names in `__all__` are missing definitions.

### 3.2 17 Public Names Defined but NOT in `__all__`

| Name | Type | Description |
|---|---|---|
| `RetryingWorksheet` | class | gspread Worksheet wrapper with auto-retry |
| `SheetsPermissionError` | class | Custom exception for 403 errors |
| `fetch_game_library` | function | Alias for `fetch_games` |
| `write_console_game` | function | Alias for `add_console_game` |
| `delete_console_game` | function | Alias for `remove_console_game` |
| `keep_alive` | function | Health-check HTTP server launcher |
| `creds` | variable | gspread credentials |
| `gc` | variable | gspread client |
| `wb` | variable | Spreadsheet handle |
| `sales_sh` | variable | Sales_Daily worksheet |
| `setting_sh` | variable | Setting worksheet |
| `member_sh` | variable | Card_Wallet worksheet |
| `stock_sh` | variable | Stock_Out worksheet |
| `stock_in_sh` | variable | Stock_In worksheet |
| `topup_sh` | variable | TopUp_Log worksheet |
| `inv_sh` | variable | Inventory worksheet |
| `scope` | variable | Google Sheets API scope list |

**Recommendation:** Add `RetryingWorksheet`, `SheetsPermissionError`, `keep_alive`, and the three aliases (`fetch_game_library`, `write_console_game`, `delete_console_game`) to `__all__`. The gspread globals (`creds`, `gc`, `wb`, `*_sh`, `scope`) should remain private if not needed externally.

---

## 4. Handler Registration Check

**File:** `bot/app.py`

### 4.1 Error Handler ✅
```python
app.add_error_handler(error_handler)
```
Registered correctly at line 50. `error_handler` is defined in `handlers/help.py` and properly imported.

### 4.2 Auth Middleware ✅
```python
app.add_handler(TypeHandler(Update, _auth_middleware), group=-999)
```
Registered at group=-999 (highest priority). Correctly blocks unauthorized users before any handler runs.

### 4.3 Custom Extend Reply Handler ✅
```python
app.add_handler(MessageHandler(..., handle_custom_extend_reply), group=-1)
```
Registered at group=-1 (before ConversationHandler at group 0). Properly intercepts extension replies.

### 4.4 ConversationHandler States ✅
All 177 states (0–176) are registered with `MessageHandler` entries. Every state name from `BotState(IntEnum)` maps to a handler.

### 4.5 Global Callback Handlers ✅
11 inline-button callback handlers registered after the ConversationHandler:
- `cb_extend_timer`, `cb_booking_mgmt`, `cb_wl_action`, `cb_cancel_booking`, `cb_cancel_with_reason`, `cb_booking_arrive` (x2),

### 4.6 Standalone Fallback Handlers ✅
35 standalone `CommandHandler` entries for cold-start `/command` usage.

### 4.7 `/finance` Command Registration

The `/finance` command is **only in standalone fallback handlers and ConversationHandler fallbacks**, not in `entry_points`. The ConversationHandler fallbacks section includes:
```python
CommandHandler("finance", cmd_finance),
```
This means `/finance` works as a fallback (when in any conversation state), and from cold start (via standalone handler). But if no conversation is active and the user isn't in a state, the standalone handler catches it. This is acceptable.

---

## 5. Dead Code Detection

### 5.1 Dead Module
- **`bot/keep_alive.py`** — Entire file is dead code (see section 1.2)

### 5.2 Dead Imports

| File | Line | Import | Status |
|---|---|---|---|
| `bot/__init__.py` | 7 | `import fcntl` | Dead |
| `bot/__init__.py` | 8 | `import signal` | Dead |
| `bot/app.py` | 3 | `import sys` | Dead |
| `bot/keep_alive.py` | 8 | `import sys` | Dead |
| `bot/__init__.py` | 174 | `from telegram.error import NetworkError, TimedOut` | Used only in `handlers/help.py` which does its own import |

### 5.3 No TODO/FIXME/HACK Found ✅
Zero TODO, FIXME, or HACK comments across all 31 Python files. Codebase is clean in this regard.

### 5.4 No Commented-Out Blocks Found ✅
No large (>5 line) commented-out code blocks detected.

### 5.5 Unused `.env` Variables

| Variable | In `.env` | Used in code |
|---|---|---|
| `REPLIT_DOMAINS` | ✅ | ❌ Never referenced |
| `ANALYTICS_SHEET_ID` | ✅ | ❌ Never referenced |

### 5.6 `.env` References External Secrets File

`.env` header says: `secrets now live in /etc/psvibe/secrets.env`

But **no code loads from `/etc/psvibe/secrets.env`**. No `python-dotenv` or `load_dotenv()` call targeting that path exists.

---

## 6. Config & Environment Check

### 6.1 Env Vars Missing from `.env`

| Variable | Required by code | In `.env` | Notes |
|---|---|---|---|
| `BOT_TOKEN` | `os.environ["BOT_TOKEN"]` — **hard crash if missing** | ❌ | Must be in `/etc/psvibe/secrets.env` or elsewhere |
| `API_KEY` | `os.environ.get("API_KEY", "")` — graceful fallback | ❌ | API calls silently fail without it |
| `RECEIPT_SECRET` | `os.environ.get("RECEIPT_SECRET", "")` — graceful | ❌ | Receipt push to API will fail |
| `ADMIN_USER_IDS` | `os.environ.get("ADMIN_USER_IDS", "")` — graceful | ❌ | Broadcast will allow all staff or no one |
| `HEALTH_PORT` | `os.environ.get("HEALTH_PORT", "8080")` — has default | ❌ | OK, 8080 default |

### 6.2 Env Vars Present and Used ✅

| Variable | `.env` | Used |
|---|---|---|
| `STAFF_NOTIFY_CHAT` | ✅ | ✅ staff notification group |
| `SHEET_ID` | ✅ | ✅ Google Sheets ID |
| `STOCK_PIN` | ✅ | ✅ Stock access PIN |
| `API_BASE_URL` | ✅ | ✅ API server URL |
| `LOW_BALANCE_THRESHOLD` | ✅ | ✅ Low-balance notification |
| `N8N_SESSION_WEBHOOK` | ✅ | ✅ Session timer webhook |
| `N8N_BOOKING_WEBHOOK` | ✅ | ✅ Booking reminder webhook |
| `CUSTOMER_BOT_TOKEN` | ❌ but `os.environ.get()` | ✅ Customer notification bot |

### 6.3 `.env` Path Issue

The `.env` file is at `/root/psvibe-sale-bot/.env` but no code explicitly loads it via `python-dotenv` or similar. Environment variables may be sourced at system level (systemd, shell profile, etc.). This is acceptable if the deployment mechanism sources `.env` before running the bot.

---

## 7. Python Version Compatibility

### 7.1 `asyncio.get_event_loop()` in `app.py` line 467 ⚠️

```python
loop = asyncio.get_event_loop()
loop.create_task(_bg_cache_refresh())
```

In Python 3.10+, `asyncio.get_event_loop()` emits a **DeprecationWarning** if there's no running event loop. Since the bot is inside `app.run_polling()`, a loop should already be running, so this is **currently safe** but should be migrated to `asyncio.get_running_loop()` for future compatibility.

### 7.2 `asyncio.new_event_loop()` in `main.py` ✅

```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
main()
```
This is the correct pattern for creating a fresh loop on restart. No deprecation issue.

### 7.3 Type Hints

Code uses modern syntax like `dict[str, int]` and `list[dict]` which requires Python 3.9+. No `typing.Dict`/`typing.List` usage found. ✅

### 7.4 f-strings

All f-strings are standard — no compatibility issues for Python 3.6+. ✅

---

## 8. Summary of Findings

| Severity | Count | Description |
|---|---|---|
| 🔴 Critical | 2 | BotState class collision, duplicate keep_alive |
| 🟡 Medium | 5 | Dead imports (fcntl, signal, sys×2), unused .env vars |
| 🟢 Low | 17 | Names not in `__all__`, unused telegram imports |
| ℹ️ Info | 3 | Deprecation path, .env loading, `/etc/psvibe/secrets.env` |

---

## 9. Recommendations (Priority Order)

### Immediate

1. **Rename `@dataclass BotState`** to `BotConfig` to eliminate the class name collision. Update references in `_get_cfg()` and cache logic.
2. **Delete `bot/keep_alive.py`** — it's dead code and duplicates the `keep_alive()` in `__init__.py`.
3. **Add `BOT_TOKEN` to `.env`** or document how it's loaded (systemd env, secrets.env, etc.)

### Short Term

4. Remove dead imports: `fcntl`, `signal` from `__init__.py`; `sys` from `app.py` and `keep_alive.py`.
5. Remove `REPLIT_DOMAINS` and `ANALYTICS_SHEET_ID` from `.env` or implement their usage.
6. Either implement `/etc/psvibe/secrets.env` loading or remove the reference from `.env` header.
7. Add missing public names to `__all__`: `RetryingWorksheet`, `SheetsPermissionError`, `keep_alive`, `fetch_game_library`, `write_console_game`, `delete_console_game`.

### Nice to Have

8. Replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in `app.py:467`.
9. Remove redundant `ForceReply` and `NetworkError`/`TimedOut` imports from `__init__.py` since handlers import them directly.
10. Consider moving `_delete_session_game` to a more appropriate location (it mutates both cache state and sheet state but is placed among alias definitions).
