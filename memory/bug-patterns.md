# 🐛 Bug Patterns — PS VIBE Sales Bot

> ⏳ = Known but unsolved

## Payment Cash Calculation (FIXED)
- `d["cash"] = net - total_paid` → `d["cash"] = payments.get("Cash", 0)`

## Wallet Balance Column H (FIXED — 3 bugs)
- Sale flow, new registration, top-up — none wrote to Card_Wallet Column H
- Added `update_cell` / `batch_update` for Column H in all 3 paths

## Double Multiplier in wallet_game_value (FIXED)
- `eff_mins` already × multiplier, then `wallet_val` applied mult again
- Removed mult from formula when `effective_cost_mins` already includes it

## Member Console Multiplier (FIXED)
- Members always got 1.0x. Added `fetch_console_multiplier()` for non-guest members.

## Console ID URL Encoding (⏳ KNOWN)
- Console IDs = "C - 01" (with spaces), `_api_call()` doesn't URL-encode
- Falls back to gspread (slow but works)

## Customer Bot — Menu Eaten by ConversationHandler (FIXED)
- All reply keyboard menu buttons consumed by booking text handlers
- Added `_bk_intercept_menu()` to all 7 text-accepting states
- **Lesson:** Check ALL related handlers, not just the reported one

## Git Push Blocked by SA JSON (FIXED)
- `git push` blocked because commit contained `kora_drive_sa.json` in cache files
- GitHub push protection — NEVER commit SA JSON

## API Server is SEPARATE from Bot (FIXED)
- Two repos! Sub-agents almost always miss the API server
- **Always check BOTH repos when investigating bugs**
- Include `PROJECT_STRUCTURE.md` in EVERY sub-agent spawn context

## Parallel Agent Collision — Same Function Overwrite (FIXED)
- Multiple fix agents modified the same function (`_fetch_games_from_mysql()`) in parallel
- Speed fix (76f203f) → Topup fix (ef9d733) → Game fix (c4ea16a) — chain of overwrites
- **Use Task Planner FIRST** to identify function-level conflicts

## Bot Crash Loop — KeyError: 0 → 703 Restarts (FIXED)
- `KeyError: 0` in asyncio task crashes bot with NO visible journal error
- systemd `Restart=always` silently restarts (703 lifetime!)
- **Fix:** Added `asyncio.get_event_loop().set_exception_handler()` in `bot/app.py`
- **Check:** `systemctl show <service> -p NRestarts`

## chr() Encoding Corruption in Auto-Fix (FIXED)
- Fix script replaced `d["nm_name"]` with `d[chr(39)+chr(110)+...]` → `d["'nm_name'"]`
- Quotes became part of key! `KeyError` because key is literal `'nm_name'`
- **Fix:** Always `ast.parse()` output before deploying auto-generated code

## MySQL-GSheet Sync Deletion Gap (KNOWN)
- Deleting from GSheet does NOT delete from MySQL `member_wallets`
- n8n handles INSERT/UPDATE only, not DELETE
- Stale rows cause wrong API data
- **Lesson:** Schema gaps include missing DELETE sync

## Missing Comma = API Crash Loop (FIXED 2026-06-02)
- Missing trailing comma in `patch_routes.py` → SyntaxError → API won't start
- systemd restart loop (65+), status shows "activating" forever
- **Fix:** Add comma. **Lesson:** Always `ast.parse()` after manual dict edits.

## MarkdownV2 `-` Character Escape (FIXED 2026-06-02)
- FAQ template `"Mon-Sun: 10AM-11PM"` — unescaped `-` causes `Can't parse entities`
- **Fix:** Use `_to_mdv2()` escape before any MarkdownV2 text

## API Key Mismatch After MySQL Migration (FIXED 2026-06-02)
- CallNames (36/36) & endpoint paths: 100% match
- But **Data keys** 12 mismatch (CRITICAL, HIGH, MED)
- **Fix:** API server dual key format accept + bot `__init__.py` key mapping
- **Lesson:** MySQL migration → check API response keys match bot handler expectations

## Coupon API Field Name Mismatch (FIXED — 2026-06-05)
- Bot checked `cd.get("coupon_code")`/`cd.get("coupon_mins")` but API returns `code`/`minutes`
- **Root cause:** Bot-side field names differed from API response schema — no shared type definition
- **Fix:** Changed to `cd.get("code")`/`cd.get("minutes")` in `sales.py`
- **Lesson:** When adding API calls, verify response field names match the actual API output, not assumed names

## Wallet Deduction Endpoint Missing Variable (FIXED — 2026-06-05)
- `api_member_wallet_update()` used `deduct_mins` without reading it from request → NameError
- **Fix:** Added `deduct_mins = req.get("deduct_mins")` before usage
- **Pattern:** Python NameError in API endpoints — variable used but never read from request body

## GSheet _LazyWorksheet .title Returns Bound Method (FIXED — 2026-06-05)
- `getattr(worksheet, 'title', '')` on `_LazyWorksheet` proxy returns a bound method, not a string
- **Fix:** Use `getattr(worksheet, '_name', None)` first, fallback to `getattr(worksheet, 'title', '')`
- **Pattern:** gspread proxy objects may have properties that look like attributes but are methods

## API Client Auto-Unwrap Confusion (FIXED — 2026-06-06)
- Customer Bot's `_api._api_get()` auto-unwraps `{"success":true,"data":{items}}` → `{items}` directly
- When code checks `resp.get("success")` on already-unwrapped data → key doesn't exist → always fails
- **Same pattern as Sales Bot's double-unwrap** (`__init__.py` line ~95, fixed 2026-06-03)
- **Fix:** Just check `if not resp:` and use `items = resp or {}`
- **Pattern:** Any `_api_get` / `_api_call` with "get" in name likely unwraps data. Audit ALL handlers if one mismatches.

## Unicode Escape Corruption in Auto-Fix Pipeline (FIXED — 2026-06-06)
- Burmese Unicode escapes (`\u1012\u103d\u102c...`) can be corrupted by auto-fix/auto-commit scripts
- Escaped sequences get re-escaped → garbled text displayed ("ဒွာသေါင္နေါဇွေနှင္းး")
- **Fix:** Use simple English text or direct Unicode chars, never double-escaped sequences
- **Pattern:** When bot shows garbled/nonsense Burmese text → check for corrupted Unicode escape sequences

## Python .pyc Cache Stale (FIXED — 2026-06-09)
- Edit .py file → restart service → `NameError: name 'X' is not defined` even though X is clearly in file
- **Root cause:** Python cached bytecode (`.pyc`/`__pycache__`) still has old code; `systemctl restart` doesn't clear it
- **Fix:** `find ... -name '*.pyc' -delete` AND `find ... -name '__pycache__' -type d -exec rm -rf {} +` THEN restart
- **Pattern:** Any backend edit that returns "not defined" error despite correct code

## String replace() Whitespace Mismatch (FIXED — 2026-06-09)
- Python patch script with `txt.replace(old, new)` silently does nothing — no error, no change
- **Root cause:** `old` string has different whitespace/newline count than actual file (e.g., `\n\n` vs `\n`)
- **Fix:** Use `repr(txt[idx:idx+N])` to verify exact whitespace before patching
- **Pattern:** After Python patch script says "done" but file hasn't changed

## Balance Sheet: Retained Earnings Missing Depreciation (FIXED — 2026-06-09)
- After adding Fixed Assets depreciation, BS shows Assets > L+E
- **Root cause:** `retained = ti - te - cost_of_sold - member_liab` — no `- total_dep`
- **Fix:** `retained = ti - te - cost_of_sold - member_liab - total_dep`
- **Pattern:** Any time accumulated depreciation is added to BS, retained earnings must subtract it too
