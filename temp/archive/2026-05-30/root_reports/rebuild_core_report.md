# Rebuild Core Bot Report — 2026-05-27

## Files Checked & Fixed

### 1. `bot/handlers/commands.py` — 🔴 CRITICAL FIX
**Issue:** Missing `from bot.handlers import *`. Without it, functions like `show_main_menu()`, `prompt_tu_member()`, `show_mm_menu()`, `prompt_mm_lookup()`, `prompt_nm_name()`, `show_rank_info()` were all undefined — would cause `NameError` at runtime.

**Fix:** Added `from bot.handlers import *` at top (after module docstring). Now commands.py can access both handler functions and bot-level API functions via the import chain:
```
commands.py → from bot.handlers import *
  → bot/handlers/__init__.py → from bot import * (added earlier)
    → bot/__init__.py → all API functions (_replit_get, now_mmt, fetch_members, etc.)
```

### 2. `bot/handlers/help.py` — 🟡 MINOR FIX
**Issue:** `from bot import *` was placed BEFORE the module docstring, making the docstring non-functional (Python reads the first string after import as docstring).

**Fix:** Moved `from bot import *` to after the docstring. Changed to `from bot.handlers import *` for consistency with other handlers. Functions accessed: `now_mmt`, `BOT_VERSION`, `logging`, `NetworkError`, `TimedOut`, `Conflict`.

### 3. `bot/handlers/main_menu.py` — 🟢 NO ISSUES
Already had proper imports and matches V1 logic. V2 enhancements:
- Added `fetch_allowed_staff_ids()` authorization check in `show_main_menu()`
- Added `BTN_SBK_WAITLIST` routing to `cmd_waitlist_mgmt()`
- Added `BTN_GAME_LIB_MENU` routing to `show_game_menu()`

### 4. `bot/__init__.py` — 🟢 VERIFIED
- `_replit_get` defined at line ~8309 ✅
- `_replit_post` defined at line ~8355 ✅
- `_replit_patch` defined at line ~8324 ✅
- `_replit_delete` defined at line ~(after _replit_post) ✅
- All states, constants, button labels defined ✅
- `from bot.handlers import *` at bottom (line after everything) ✅

## Import Chain (for reference)
```
bot/__init__.py         → defines ALL functions/states/constants
                        → ends with: from bot.handlers import *
                            ↓
bot/handlers/__init__.py → imports all handler submodules
                         → ends with: from bot import *  (re-exports bot-level)
                             ↓
Individual handlers     → from bot.handlers import *
                         → have access to both handler names AND bot names
```

## Deployment
```
rsync -av main_menu.py → /root/Sales-Tele-Bot_refactored/bot/handlers/
rsync -av commands.py  → /root/Sales-Tele-Bot_refactored/bot/handlers/
rsync -av help.py      → /root/Sales-Tele-Bot_refactored/bot/handlers/
systemctl restart psvibe-bot-refactored.service
```

## Verification
- ✅ All 3 files pass `python3 -c "import ast; ast.parse(...)"` syntax check
- ✅ Bot restarted cleanly (`Application started`, `getMe 200`, `setMyCommands 200`)
- ✅ No import errors in logs
- ✅ Background cache refresh running
- ✅ Telegram polling active (HTTP 200 responses)
