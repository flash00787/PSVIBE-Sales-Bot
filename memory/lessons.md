# 📚 Critical Lessons

## 🔴 Golden Rules
See `GOLDEN_RULES.md` (workspace root)

## 🔴 Post-Task SOP
See `POST_TASK_SOP.md` (workspace root)

---

## Code Exists ≠ Code Runs (2026-05-30)
- `sync_service.py` (860+ lines) existed but NEVER executed — no cron, no systemd
- **Fix:** Created `run_sync.sh` wrapper, cron every 5 min, fixed imports
- **Lesson:** Verify execution setup, not just code existence

## Schema Gaps: GSheet→MySQL Migration (2026-05-30)
- MySQL `member_wallets` missing 5 GSheet columns
- **Fix:** Compare column-by-column, not table-by-table

## Tier Must Be Dynamic (2026-05-30)
- Static text tier goes stale. Added MySQL path with dynamic calc:
  - ≥1M → Immortal
  - ≥300K → Master
  - else → Warrior

## Booking Endpoints Were gspread-Only (2026-05-30)
- MySQL table existed (0 rows) but API used gspread
- MySQL table existence ≠ MySQL-backed endpoints

## ConversationHandler Fallbacks = CRITICAL (2026-05-30)
Every ConversationHandler with text-accepting states MUST have:
1. `fallbacks` entry (catch-all so unmatched text stays in conversation)
2. Menu button interception (`_bk_intercept_menu()`) in every state
3. Expanded skip keyword set

## Auto-Doc MUST Run After EVERY Fix (2026-05-30)
- `auto_doc_updater.py` was NEVER called after fixes
- **Fix is NOT complete** until auto-doc runs on VPS AND workspace docs updated
- **Command:** `python3 /root/coordination/auto_doc_updater.py --summary "Fixed X: ..."`

## 🤖 Model Routing — Strict Cost Control (2026-06-01)
- **DEFAULT Fix Agent:** DeepSeek Pro — ALWAYS try first
- **Basic Checks/Reports:** DeepSeek Flash
- **Claude Sonnet 4:** LAST RESORT only — only when DeepSeek fails
- Claude 857k tokens / 10min = money wasted!

## 🚫 Spawn Protocol (2026-06-01)
See `memory/SPAWN_PROTOCOL.md` for full details
- **NEVER** spawn 2+ agents targeting the SAME file simultaneously
- MAX 2 agents per spawn message
- After ANY spawn → `sessions_yield()` immediately
- Same file = SEQUENTIAL; Different files = PARALLEL

## SessionWriteLockTimeout Prevention (2026-06-01→02)
- **Root Cause:** `session.writeLock.acquireTimeoutMs` defaulted to 60s
- **Fix:** Config → 300s (5 min) + maintenance mode enforce + 300mb cap
- **Lesson:** Always check built-in config before building external tools

## Sub-Agent Timeout by Task Size (2026-06-01)
| Task Type | Timeout |
|-----------|---------|
| Quick check/status | 60-120s |
| Single file fix | 300s (default) |
| Multi-file fix | 600-900s |
| Deep audit / SSH heavy | 900-1200s |
| Large file (bot.js 362KB) | 1200-1800s |
| Full system deploy | 3600-14400s |

## Auto-Pilot Cron System (2026-06-01)
See `HEARTBEAT.md` for full schedule
- 30s: Lock monitor + cleanup
- 1 hr: Session cleanup (>1d, keep 10)
- 4 hr: Heartbeat (memory, health, notifications)
- 8:00/20:00 MMT: Gmail check
- 8:30/20:30 MMT: VPS monitor
- 6 hr: PS5 gaming news
- Sun 8:00 MMT: Full code quality audit

## VPS Hot-Patching = Whack-a-Mole (2026-06-02)
- Pending Bookings bug: multiple fixes applied interactively on VPS one-at-a-time (key mappings, aliases, .get() fallbacks) — bug still open after 4+ rounds
- **Lesson:** When a bug resists the first fix, STOP hot-patching. Do an end-to-end flow trace FIRST, then fix the root cause once.
- Pattern: key_mapping→alias_conflict→fallback→still_broken → each fix masks the real issue
- **Better approach:** Read full data flow (Bot → API → MySQL → Response), trace the exact path, find ALL mismatches at once, fix in ONE batch.

## FastAPI response_model Silently Strips Fields (2026-06-05)
- `@app.post(..., response_model=GenericResponse)` — if GenericResponse only has `success`/`message`/`data` but endpoint returns `{"error":"msg","code":500}`, FastAPI strips `error` and `code` silently
- **Result:** Bot always sees `{"success":false,"error":"unknown"}` — real error was filtered out
- **Fix:** Always audit response_model classes against actual return shapes. Add all fields that any code path might return.
- **Lesson:** FastAPI's response_model is a filter, not just a schema hint. Missing fields = silently dropped data.

## API Auto-Unwrap Pattern — Check ALL `_api_get()` Callers (2026-06-06)
- Customer Bot's `_api._api_get()` auto-unwraps `{success,data}` → raw data
- Same pattern as Sales Bot's `_api_get()` / `_replit_get_async`
- **Lesson:** Before writing NEW code that calls `_api_get()`, scan the codebase for how OTHER handlers use it. The wrong pattern (checking `success`/`data`) is a common mistake.

## Layered Root Causes — Don't Fix Until All Found (2026-06-06)
- Food Menu bug had **3 distinct root causes** but was reported as 1 symptom
- Fix attempt 1 fixed cause A (menu routing) but B (API unwrap) + C (Unicode) remained
- Fix attempt 2 fixed cause A better but B + C remained
- Fix attempt 3 started on B but C corrupted the fix
- **Lesson:** When a fix doesn't work after 2 attempts, STOP hot-patching. List ALL possible root causes exhaustively before editing. Or: spawn a sub-agent to do a full code trace first.

## Unicode Escape Sequences in Auto-Commit Pipeline (2026-06-06)
- Auto-fix commits may corrupt `\uXXXX` escape sequences in Burmese text
- The pipeline re-processes the file and can double-escape: `\u1012` → `\\u1012`
- **Lesson:** For Burmese text in Telegram bots, use direct Unicode string literals (Python handles UTF-8 natively) or simple English text. Never use `\u` escape sequences if you can avoid them.

## 2026-06-17: `COALESCE('', val)` SQL Trap
**Problem:** `COALESCE(%s, staff_name)` with empty string `''` returns `''` because empty string IS NOT NULL in SQL. PATCH sends `req.get("staffName", "")` → `""` → `COALESCE('', 'Real Name')` returns `''` → wipes existing data.
**Fix:** Always wrap with `NULLIF`: `COALESCE(NULLIF(%s, ''), staff_name)`.
**File:** `app.py` line 1335 (PATCH /api/bookings/{id}/status)
