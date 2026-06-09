# ERROR_PATTERNS.md — Known Error Patterns & Fixes

> Auto-documented error patterns — when you see these, you know the fix.

---

### Bug #28: Sync Service Never Running (2026-05-30)
**Error:** GSheet data changes not reflected in MySQL
**File:** `/root/psvibe_api_server/sync_service.py`
**Root Cause:** `sync_service.py` used `mysql.connector` (not installed) instead of `pymysql`. `run_sync.sh` used system python3 not venv python.
**Fix:** Created `run_sync.sh` wrapper loading venv python. Fixed import to pymysql.
**Pattern:** When sync service exists but data doesn't match → check if service is actually running. Check `run_sync.sh` uses venv python.

---

### Bug #29: API Server vs Bot — Two Separate Repos (2026-05-31)
**Error:** Bot-side fix agents never touch API server code
**Key Insight:** Bot code is at `/root/psvibe-sales-bot/` (GitHub: PSVIBE-Sales-Bot). API server is at `/root/psvibe_api_server/` (GitHub: PSVIBE-API-Server). Sub-agents usually only work in the bot repo and miss the API server.
**Fix:** Always check BOTH repos when investigating. API Server routes queries to API server repo.
**Pattern:** When a bot fix doesn't work → the actual bug is likely in the API server repo.

---

### Bug #30: Member Registration — API Ignores Bot Data (2026-05-31)
**Error:** New member has wrong ID (uses `M-{timestamp}` instead of bot-generated ID) and wallet mins always 0
**File:** `/root/psvibe_api_server/app.py` — `api_members_register()`
**Root Cause:** API hardcoded `member_id = f"M-{int(time.time())}"` ignoring bot's `req.get("member_id")`. Wallet INSERT used `balance_mins=0` hardcoded.
**Fix:** Changed to `req.get("member_id", "")` with fallback. Added `initial_mins = req.get("initial_mins", 0)` and used in wallet INSERT.
**Pattern:** API server is authoritative for data storage. Always check API for parameter usage.

---

### Bug #31: Topup — Field Name Mismatch (2026-05-31)
**Error:** Topup creates log entry but doesn't update wallet balance
**Files:** Bot: `/root/psvibe-sales-bot/bot/handlers/members.py` — API: `/root/psvibe_api_server/app.py`
**Root Cause:** Bot sends `minutes` field, API expects `mins_added`. API's topup endpoint didn't update `member_wallets` MySQL table.
**Fix:** Bot changed `minutes` → `mins_added` (and it's referral bonus variant). API added MySQL wallet update with `balance_mins + mins_added`.
**Pattern:** Field name mismatches between bot and API cause silent failures (try/except). Check field names in API docs/code.

---

### Bug #32: Game List — MySQL Column Mapping Wrong (2026-05-31)
**Error:** Game list shows disc count numbers instead of genre, empty console status
**Files:** `/root/psvibe_api_server/sync_service.py`, `/root/psvibe_api_server/app.py`
**Root Cause (3 layers):**
1. `sync_service.py` mapped Columns: D(disc count)→genre, F(C-01 checkbox)→disc_count, status→wrong col
2. `app.py` `_fetch_games_from_mysql()` returned `None` (broken by speed fix commit `76f203f`)
3. `c4ea16a` fixed column mapping but ALSO pushed kora_drive_sa.json → git push blocked
**Fix:** Sync column mapping corrected (col 3→disc_count, col 20→solo_multi|genre). `_fetch_games_from_mysql()` restored.
**Pattern:** MySQL data stale? Run `run_sync.sh` manually. Check both repos when push blocked.

---

### Bug #33: Multiple Agent Overwrite (2026-05-31)
**Error:** Parallel fix agents overwrote each other's work
**Timeline:**
1. `76f203f` (Speed fix): Set `_fetch_games_from_mysql()` → return None
2. `ef9d733` (Topup fix): Restored function with proper MySQL query
3. `c4ea16a` (Game fix): Reverted to return None AGAIN (agent based on older commit)
4. `064dfdf` (Final fix): Restored function correctly
**Fix:** Sequential fixes only for same-function changes. Lock file per function.
**Pattern:** Parallel agents MUST NOT modify the same function. Use Task Planner to detect conflicts first.

---

### Bug #34: API Key Issues Causing False Zero Results (2026-05-31)
**Error:** API returns 0 games despite MySQL having 37 rows
**Root Cause:** Truncated API key in curl test commands caused 401 error, misinterpreted as empty data
**Fix:** Always use full API key from environment file for testing
**Pattern:** When API health shows `data_source: mysql` but endpoint returns empty — verify API key first!

---

### Bug #35: GitHub Push Blocked by Secret Scanning (2026-05-31)
**Error:** `git push` fails with "Repository secret found" for kora_drive_sa.json
**Files:** `/root/psvibe_api_server/.git/` — commit `c4ea16a` contains cache files that reference SA key
**Cause:** SA JSON file path referenced in commit content; GitHub push protection blocks it
**Fix:** Remove offending files from git history with `git filter-repo` or `git filter-branch`, or add to `.gitignore` and force push.
**Pattern:** Never commit service account JSON files. Push protection is a feature, not a bug.

---

### Bug #36: Missing Trailing Comma in Python Dict Crashes API (2026-06-02)
**Error:** psvibe-api.service keeps restarting (counter 65+), `systemctl is-active` shows "activating" forever
**Files:** `/root/psvibe_api_server/patch_routes.py`
**Log:** `SyntaxError: invalid syntax` at line 41 (`"game_name": "gameName"`)
**Root Cause:** `"phone": "phone"` was missing trailing comma → Python parsed as invalid syntax
**Fix:** Added comma after `"phone": "phone"`
**Pattern:** When API service keeps crashing on startup → check `server.log` for SyntaxError. Missing commas happen when editing dicts manually.
**Lesson:** After ANY edit to a Python dict, verify with `ast.parse()` or `python3 -c "compile(...)"`

---

### Bug #37: MarkdownV2 Reserved Characters in FAQ Template (2026-06-02)
**Error:** `Can't parse entities: character '-' is reserved and must be escaped with the preceding '\'`
**Files:** `/root/psvibe-sales-bot/customer_bot/ai.py` (_build_faq_template)
**Root Cause:** FAQ template `"Mon-Sun: 10AM-11PM"` contained `-` character not escaped for Telegram MarkdownV2
**Fix:** Escaped `-` → `\-` in template. Also wrapped faq_reply through `_to_mdv2()` escape function before sending
**Pattern:** When `sendMessage` returns 400 with "Can't parse entities" → check for unescaped MarkdownV2 special chars (`_ * [ ] ( ) ~ \` > # + - = | { } . !`)
