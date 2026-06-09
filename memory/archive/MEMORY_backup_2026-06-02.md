# MEMORY.md — Kora's Long-Term Memory

## 🔴 Golden Rules

See GOLDEN_RULES.md

---

## 🛡️ Stable Workflow Protocol

**fix_protocol.py** at `/root/coordination/fix_protocol.py`

Before ANY code fix (MANDATORY):
```
python3 /root/coordination/fix_protocol.py --start <file>
  → git status check → fix_lock → snapshot (rollback)
After fix:
python3 /root/coordination/fix_protocol.py --complete
  → file integrity + git diff + compile → FAIL=rollback, PASS=auto-commit
```

---

## 📝 Post-Task SOP

See POST_TASK_SOP.md

---

## 🔴 Critical Lessons

### Sync Service Must Actually Run (2026-05-30)
`sync_service.py` existed (860+ lines) but NEVER executed — no cron, no systemd. Code exists ≠ code runs. Fix: created `run_sync.sh` wrapper, cron every 5 min, fixed imports.

### Schema Gaps GSheet→MySQL (2026-05-30)
MySQL `member_wallets` missing 5 GSheet columns. When migrating, compare column-by-column, not table-by-table.

### Tier Calculation Must Be Dynamic (2026-05-30)
Static text tier goes stale. Added MySQL path with dynamic calc: ≥1M → Immortal, ≥300K → Master, else Warrior.

### Booking Endpoints Were gspread-Only (2026-05-30)
MySQL table existed (0 rows) but API used gspread. MySQL table existence ≠ MySQL-backed endpoints.

### ConversationHandler Fallbacks = CRITICAL (2026-05-30)
Every ConversationHandler with text-accepting states MUST have:
1. `fallbacks` entry (catch-all so unmatched text stays in conversation)
2. Menu button interception (`_bk_intercept_menu()`) in every state
3. Expanded skip keyword set

### Auto-Doc MUST Run After EVERY Fix (2026-05-30)
`auto_doc_updater.py` was NEVER called after fixes. Fix is NOT complete until auto-doc runs on VPS AND workspace docs are updated.

### 🤖 Model Routing — Strict Cost Control (2026-06-01)
- **DEFAULT Fix Agent:** DeepSeek Pro — ALWAYS try first
- **Basic Checks/Reports:** DeepSeek Flash (Status Reporter, Dispatch Manager, etc.)
- **Claude Sonnet 4:** LAST RESORT only — DeepSeek fail မှပဲ fallback
- Claude သုံးမယ်ဆိုရင် Boss ကို ခွင့်တောင်းပါ
- Claude 857k tokens / 10min = ငွေဖြုန်းမိခဲ့ (fix_payment_stuck, 2026-06-01)

### 🚫 Spawn Protocol — Strict Enforcement (2026-06-01)
**CRITICAL: NEVER spawn 2+ agents targeting the SAME file simultaneously!**
- ❌ fix_payment_stuck + fix_food_stock_sales both hit `members.py` → LOCK CONFLICT → 10min timeout (2026-06-01)
- ✅ BEFORE spawn: check file-level conflicts manually
- ✅ Use Task Planner FIRST for multi-file work to identify function-level collisions
- ✅ Same file = SEQUENTIAL spawn (wait for first to complete, then second)
- ✅ Different files = PARALLEL spawn OK
- Rules apply even for quick "urgent" fixes

### 💾 SessionWriteLockTimeout Prevention (2026-06-01)
**Root Cause:** Session file grows to 1.2MB (487+ msgs) → write lock held >60s → timeout → gateway restarts.
**Symptom:** `SessionWriteLockTimeoutError: session file locked (timeout 60000ms)` every few messages.
**Fix:**
- Boss MUST use `/new` when session reaches ~200-250 messages
- Lock monitor auto-alerts at 500KB threshold
- Session cleanup auto-deletes old large topic files (>7d, >500KB)
**Prevention:** Auto-pilot monitors session size every 30s via lock_monitor.py

### ⏱️ Sub-Agent Timeout by Task Size (2026-06-01)
System max: 14400s (4h). Match timeout to task:
| Task Type | Timeout |
|-----------|---------|
| Quick check/status | 60-120s |
| Single file fix | 300s (default) |
| Multi-file fix | 600-900s |
| Deep audit / SSH heavy | 900-1200s |
| Large file (bot.js 362KB) | 1200-1800s |
| Full system deploy | 3600-14400s |

### ⏰ Auto-Pilot Cron System (2026-06-01)
| Cron Job | Interval | Purpose |
|----------|----------|--------|
| lock-monitor-cleanup | 30s | Scan .lock files, clean stale/dead locks + self-cleanup |
| session-cleanup | 1 hr | Delete >1d old sessions, keep last 10 per prefix, delete old large topic bloat |
| Heartbeat | 4 hr | Memory maintenance, consolidator, health check |
| Gmail Check | 8:00/20:00 MMT | Read & report important emails |
| VPS Monitor | 8:30/20:30 MMT | Health alerts, system resource check |
| PS5 News | 6 hr | Research gaming news |
| Weekly Scan | Sun 8:00 MMT | Full code quality audit |

**Lock Monitor vs Session Cleanup:**
- Lock Monitor: Cleans `.lock` files (deadlock prevention)
- Session Cleanup: Cleans `.jsonl` session files (disk bloat prevention)
- Both needed — they target different file types

**Session Size Rule:** /new every ~200-250 messages. Main session >500KB (1.2MB = 487msgs) causes `SessionWriteLockTimeoutError`. Lock monitor auto-alerts at threshold.

**Session File Bloat Root Cause (2026-06-01):**
- 6,565 session files (2.0 GB) caused Gateway errors
- Main culprit: lock monitor cron creating 1,570 sessions/day (55s interval)
- Fix: Reduced duplicates (3→1 cron), interval 30s with self-cleanup (keeps 10), + session cleanup cron (1h, >1d)
- Result: 1,930 files / 516M steady state (78% reduction) ✅

---

## ⏰ Timezone Preference
- **Boss with time:** ALWAYS use Myanmar Time (Asia/Yangon, UTC+6:30)
- Convert ALL UTC → Myanmar Time before telling Boss

---

## 👥 Contacts & Boss Info

### Contacts
- **Chan Su Su Hlaing:** chansusuhlaing@gmail.com
- **You Ko Htet:** rein020124@gmail.com
- **Wi Wi:** thirishetpaing.t@gmail.com
- **Ye Yint Oo:** yeyintoo12345678@gmail.com — Telegram: `8336350778`
- **Ye Myat:** yemyat.7.14.1999@gmail.com

### Boss — Ko Aung Chan Myint
- **Business:** Founder & Manager — PS VIBE - PS5 Gaming Lounge
- **Tagline:** "Play The Game. Share The VIBE!"
- **Director:** Synergy Hub
- **Email:** chanmyint123456789@gmail.com
- **Rules:** Card_wallet → Column H only. Receipt templates: NO Burmese footer text.

---

## 📧 Email & Google

**Gmail API:** OAuth 2.0 (readonly + send), token.json + secret.json. Sender: `send_email_api.py` (HTTPS 443).

**Gmail Accounts:**
1. `chanmyint123456789@gmail.com` — ✅ Active
2. `aungchanmyint.psvibe@gmail.com` — ⏳ Pending
3. `aungchanmyint.shs@gmail.com` — ⏳ Pending

**Google Drive:** SA key at `kora_drive_sa.json`, PS VIBE Drive Root: `1V6ctTJpXaoRIDnrfxwhVO72I7jfD5GsS`.

---

## 🐛 Known Crash Patterns

### Sub-agent Spawn Crash (2026-05-31)
- **Root cause:** Spawning 3+ agents AND responding in same message → gateway crashes
- **Why:** Completion events arrive while spawn response is still processing → session conflict
- **Fix:**
  - MAX 2 agents per spawn message (NOT 5)
  - After ANY spawn → `sessions_yield()` immediately
  - Spawn message = 1-2 lines MAX (no lengthy explanation)
  - Process completion events ONE at a time
  - See AGENTS.md → 🚨 CRASH PREVENTION section

## 🐛 Known Bug Patterns (PS VIBE Sales Bot)

### Payment Cash Calculation (FIXED)
- `d["cash"] = net - total_paid` → `d["cash"] = payments.get("Cash", 0)`

### Wallet Balance Column H (FIXED — 3 bugs)
- Sale flow, new registration, top-up — none wrote to Card_Wallet Column H
- Added update_cell/batch_update for Column H in all 3 paths

### Double Multiplier in wallet_game_value (FIXED)
- eff_mins already × multiplier, then wallet_val applied mult again
- Removed mult from formula when effective_cost_mins already includes it

### Member Console Multiplier (FIXED)
- Members always got 1.0x. Added fetch_console_multiplier for non-guest members.

### Console ID URL Encoding (2026-05-30 — KNOWN)
- Console IDs = "C - 01" (with spaces), `_api_call()` doesn't URL-encode. Bug #5 fix triggers this.
- **Not yet fixed** (falls back to gspread)

### Customer Bot — Menu Buttons Eaten by ConversationHandler (FIXED)
- All reply keyboard menu buttons consumed by booking text handlers. Added `_bk_intercept_menu()` to all 7 text-accepting states.
- **Lesson:** When Boss reports bug, check ALL related handlers, not just the reported one.

### Git Push Blocked by Service Account JSON (2026-05-31)
- `git push` for API Server blocked because commit `c4ea16a` contained `kora_drive_sa.json` content in cache files
- GitHub's push protection is a security feature, not a bug
- **Fix:** Remove offending file from git history, or NEVER commit SA JSON in the first place

### API Server is a SEPARATE Repo (2026-05-31)
- **IMPORTANT:** Two repos! Bot at `/root/psvibe-sales-bot/` (GH: PSVIBE-Sales-Bot) and API Server at `/root/psvibe_api_server/` (GH: PSVIBE-API-Server)
- Sub-agents almost always ONLY work in the bot repo and MISS the API server
- **Always check BOTH repos when investigating bugs**
- **PROJECT_STRUCTURE.md** = master reference (both repos, services, Docker, MySQL, endpoints) — include in EVERY sub-agent spawn context

### Parallel Agent Collision: Same Function Overwrite (2026-05-31)
- Multiple fix agents modified the same function (`_fetch_games_from_mysql()`) in parallel
- Speed fix (76f203f) broke it, Topup fix (ef9d733) restored it, Game fix (c4ea16a) broke it again
- **Use Task Planner FIRST** to identify function-level conflicts before spawning fix agents

### Sub-Agent Timeout Pattern (2026-05-31)
- 1200s timeout STILL not enough when agents investigate deeply
- Root causes: SSH round-trip overhead (3-5s/call × 10+ calls), deep investigation, multi-file scope
- **Solution (Option A):** Kora investigates via exec SSH (fast), spawns agents with EXACT text replacements only

---

## 🏗️ Infrastructure

### Sales Bot (V2 Modular)
- **Path:** `/root/psvibe-sales-bot/` (109 .py files)
- **3 Services:** psvibe-sale-bot | psvibe_customer_bot | psvibe-api
- **Tests:** 33 unit tests, 17/17 API endpoints verified
- **Architecture:** Bot → API (:8000) → MySQL (primary) → gspread (cold fallback)
- **API Server:** Separate repo at `/root/psvibe_api_server/`
- **MySQL:** Docker container `psvibe-mysql` (127.0.0.1:3306), DB: `psvibe_api`

### Coordination Tools (25 total at `/root/coordination/`)
Full inventory in TOOLS.md. Key tools: flow_analyzer, arch_mapper, enhanced_validator, quality_gate, fix_protocol (MANDATORY), workflow_engine, batch_coordinator, auto_doc_updater.

### Cloudflare Tunnel
- `cloudflared-tunnel.service` — ps-vibe.com → localhost:8000
- RECEIPT_BASE_URL: `https://ps-vibe.com` (all encrypted)

### Sub-Agent Config
- **Timeout:** 300s default spawn, 14400s system max. **Model:** Flash (mgmt), Pro (code).
- **Subagent fallback:** deepseek/deepseek-v4-pro → deepseek/deepseek-v4-flash → google/gemini-2.5-flash → google/gemini-3.5-flash
- **MaxConcurrent:** 25 (both main & subagent), subagents.maxConcurrent=25, maxChildrenPerAgent=20
- **Fallback:** Pro → Flash → Gemini 2.5 Flash → Gemini 3.5 Flash
- **Auth:** OpenRouter (Claude Sonnet 4 fixes), xAI (Grok research)

---

## 🔴 May 31 Bug Fixes & Lessons

### Bug: Bot Crash Loop (KeyError: 0 → 703 Restarts)
- `KeyError: 0` in asyncio task crashed bot with NO error visible in journal
- systemd `Restart=always` silently restarted — 703 lifetime restarts
- **Fix:** Added `asyncio.get_event_loop().set_exception_handler()` in `bot/app.py` to catch task-level exceptions
- **Lesson:** When bot seems "slow" but no errors shown, check systemd restart count (`systemctl show <service> -p NRestarts`)

### Bug: Automated Fix Script chr() Encoding Corruption
- Fix script replaced `d["nm_name"]` with `d[chr(39)+chr(110)+...]` → `d["'nm_name'"]` (quotes part of key!)
- Result: KeyError because key became literal `'nm_name'` instead of `nm_name`
- **Lesson:** Automated code generators/fix scripts MUST verify output with ast.parse() before deploying

### Bug: MySQL-GSheet Sync Deletion Gap
- Deleting member from GSheet (Card_Wallet) does NOT delete from MySQL `member_wallets`
- n8n sync → MySQL only handles INSERT/UPDATE, not DELETE
- Stale rows cause wrong data returned by API
- **Lesson:** Schema gaps aren't just missing columns — they include missing DELETE sync

### Missing Comma in Dict = API Crash Loop (2026-06-02)
- `"phone": "phone"` missing trailing comma in `patch_routes.py` → SyntaxError → API won't start
- systemd keeps restarting (counter 65+), status shows "activating" forever
- **Fix:** Add missing comma. **Lesson:** Always `ast.parse()` after manual dict edits.

### MarkdownV2 `-` Character Escape (2026-06-02)
- FAQ template `"Mon-Sun: 10AM-11PM"` — unescaped `-` causes `Can't parse entities` error
- **Fix:** Use `_to_mdv2()` escape function before sending any MarkdownV2 text

### Architecture: Dynamic Payment Method Selection
- Replaced hardcoded `prompt_tu_kpay`/`step_tu_kpay` with dynamic multi-method flow
- Payment methods read from Setting!Y (Cash, KPay, WavePay, Bank Transfer, etc.)
- Users can split one transaction across multiple payment methods
- Backward compatible: kpay/cash columns still populated in GSheet
- Applied to both Top Up and New Member registration

### UI Pattern: Button Row Merge (3→2)
- 3 separate button rows merged to 2: `[[default], [BTN_CUSTOM, BTN_GIFT], NAV]`
- Gift card moved behind "Enter Different Amount" for cleaner UI

### 🩺 Unified Health Monitor (2026-06-01)
- Created `coordination/kora_health_monitor.py` — checks all 5 pillars in one pass (30 checks)
- Created `coordination/vps_exec.js` — Node.js SSH2 bridge for Gateway→VPS connectivity
- Auto-runs hourly via Gateway cron `kora-health-monitor`; alerts only if score < 90
- Current baseline: 97/100 across 5 pillars

### API Key Mismatch Fix After MySQL Migration (2026-06-02)
CallNames (36/36) နဲ့ Endpoint paths က 100% match ဖြစ်ပေမဲ့ **Data keys** 12 ခုမှာ mismatch ရှိတယ်:
- **CRITICAL:** `fetch_console_games` mappingမရှိ, `get_consoles_with_game` GET endpoint က req:dict body သုံး (broken), `get_games_on_console` return type မှား, `add_console_game` POST keys မကိုက်
- **HIGH:** `fetch_member_effective_rate` float ပြန်ရမဲ့အစား dict, `fetch_attendance`/`fetch_base_salaries` format မှား
- **MED:** `fetch_promotions_cached` unwrap မလုပ်, `save_attendance`/`save_receipt_json` POST body keys မကိုက်
- **Fix pattern:** API server က dual key format accept လုပ်တယ် (legacy + new). Bot __init__.py မှာ key mapping ထည့်တယ်.
- **Lesson:** MySQL migration လုပ်တိုင်း API response keys နဲ့ bot handler မျှော်လင့်တဲ့ keys တွေ match ဖြစ်မဖြစ် သေချာစစ်ရမယ်။

### 🔍 Comprehensive Scan — 100/100 Quality Gate (2026-06-01 07:43 UTC)
- Full-audit pipeline: 6/6 passed in 18.5s (import scanner, flow analyzer, arch mapper, enhanced validator, tests 104/104, quality gate 100/100)
- All 3 services active: psvibe-sale-bot, psvibe-api, psvibe_customer_bot
- Sonnet 4 analysis from May 31 (17:34 UTC) confirmed **STALE** — all 5 reported bugs already fixed in same-session fixes
- Stale analysis lesson: After intensive fix sessions, external analyses become irrelevant quickly — always re-scan live code first
- Live verification (AST analysis) confirmed: handler return states, tu_/nm_ separation, ConversationHandler fallbacks, console URL encoding, API error handling — all clean

### 💾 Session Lock Timeout — Permanent Fix (2026-06-02)
**Root Cause:** `session.writeLock.acquireTimeoutMs` defaulted to 60,000ms (60s). Subagent completing → writing to main session trajectory → lock contention → 60s not enough → `SessionWriteLockTimeoutError`.
**Fix Applied:**
1. **config:** `acquireTimeoutMs: 60s → 300s (5 min)` — subagent patiently waits for lock
2. **config:** `maintenance.mode: enforce` + `maxDiskBytes: 300mb` — gateway auto-cleans old files
3. **config:** `maintenance.pruneAfter: 7d`, `resetArchiveRetention: 2d`
4. **lock_monitor.py:** `TRAJECTORY_MAX_AGE_DAYS: 7→2`, `TRAJECTORY_FORCE_CLEAN_KB=10000` added — 10MB files auto-force-cleaned
5. **Immediate cleanup:** 6 × 10MB trajectory files deleted (194MB freed)
6. **Result:** Subagent lock timeout eliminated entirely. Session dir capped at 300MB.
**Lesson:** Gateway source (`/app/dist/`) contains tunable session.writeLock params. Always check built-in config before building external tools.
