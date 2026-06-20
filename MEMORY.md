# MEMORY.md — Kora's Long-Term Memory Index

> 🗂️ Short master index. Detailed history → module files in `memory/`.
> Search via `memory_search` or `memory_get(path=memory/<file>.md)`.
## 🔴 Core Docs (workspace root)
| File | Purpose |
|------|---------|
| `GOLDEN_RULES.md` | Golden rules — never break |
| `HEARTBEAT.md` | Periodic tasks & cron schedule |
| `AGENTS.md` | Identity, workflow, hybrid spawning |
| `SOUL.md` | Personality, language, tone |
| `TOOLS.md` | SSH, bots, commands, API keys |
| `PROJECT_STRUCTURE.md` | Project overview (2 repos) |

## 📁 Module Files (`memory/`)

### Systems & Accounts
- **`memory/contacts.md`** — 👥 Contacts, Boss info, friend contacts
- **`memory/emails.md`** — 📧 Gmail accounts, API, Google Drive

### Infrastructure
- **`memory/infrastructure.md`** — 🏗️ Bot paths, services, MySQL, coordination tools
- **`memory/config.md`** — 🔧 Gateway config, lock_monitor, fix_protocol
- **`memory/psvibe-code-structure.md`** — 📂 File-by-file code reference (both repos)
- **`memory/project-state.md`** — 📋 Current project state & known issues

### SOPs & Frameworks (`memory/sop/`)
- **`memory/sop/SPAWN_PROTOCOL.md`** — 🔀 Sub-agent spawn rules & hybrid spawning
- **`memory/sop/POST_TASK_SOP.md`** — 📝 Post-task documentation SOP
- **`memory/sop/COORDINATION_FRAMEWORK.md`** — 🏗️ Agent coordination framework
- **`memory/sop/HELPER_GUIDELINES.md`** — 👷 Helper agent guidelines
- **`memory/sop/heartbeat-procedures.md`** — 💓 Full heartbeat procedures
- **`memory/sop/DISPATCH_MANAGER_SOP.md`** — 📋 Dispatch manager SOP
- **`memory/sop/FINDINGS_MANAGER_SOP.md`** — 🔍 Findings manager SOP
- **`memory/sop/TASK_PLANNER_SOP.md`** — 📊 Task planner SOP
- **`memory/sop/STATUS_REPORTER_SOP.md`** — 📈 Status reporter SOP
- **`memory/sop/VERIFY_AGENT_SOP.md`** — ✅ Verify agent SOP
- **`memory/sop/DEPLOY_MANAGER_SOP.md`** — 🚀 Deploy manager SOP
- **`memory/sop/GIT_SYNC_SOP.md`** — 🔄 Git sync SOP
- **`memory/sop/SPAWNING_MANAGER_SOP.md`** — 🥚 Spawning manager SOP

### Operations
- **`memory/tools-commands.md`** — 🛠️ All coordination tool commands reference
- **`memory/memory-usage-guide.md`** — 📖 How to use the memory system (decision tree, write rules)

### Memory Automation (Phase 3)
- **`memory/session_summary.py`** — Session end auto-summary
- **`memory/memory_index.py`** — Topic search index (1,146 topics)
- **`memory/priority_engine.py`** — P0-P3 priority classifier
- **`memory/memory_pruner.py`** — Dedup & prune (target ~20KB MEMORY.md)
- **`memory/daily_digest.py`** — Daily digest generator
- **`memory/git_backup.py`** — Memory git auto-backup
- **`memory/knowledge_graph.py`** — Entity relationship graph (54 nodes)

### Bugs, Fixes & Lessons
- **`memory/bug-patterns.md`** — 🐛 All known bug patterns (fixed & known)
- **`memory/ERROR_PATTERNS.md`** — ⚡ Quick ref: error → root cause → fix
- **`memory/lessons.md`** — 📚 Critical lessons learned
- **`memory/fix-history.md`** — 📋 Recent fix history (by date)

#

## Quick Reference
- **Latest daily log:** See `memory/2026-06-17.md`
- **Recent fixes:** See `memory/fix-history.md`
- **Bug patterns:** See `memory/bug-patterns.md`
- **Lessons:** See `memory/lessons.md`
- **Project state:** See `memory/project-state.md`

## Memory (2026-06-16)

### 🎮 Discord Bot V3 — Full Feature Upgrade (20:00-20:45 UTC)

### ✅ New Modules Created (6 files in `/root/psvibe-discord-bot/modules/`)
| Module | File | Size | Description |
|--------|------|------|-------------|
| Balance & Stats | `balance.js` | 8.8 KB | `/balance [query]` + `/my-stats` via live API |
| Achievements | `achievements.js` | 7.9 KB | `/achievements` + auto-check on events |
| Daily Rewards | `daily.js` | 7.3 KB | `/daily` with streak system (50-150 XP) |
| LFG System | `lfg.js` | 14.2 KB | `/lfg create|list|join|leave|cancel` |
| Auto-Mod | `automod.js` | 18.7 KB | `/automod toggle|whitelist|warn|strikes|reset` |
| Birthday Cron | `birthday-cron.js` | 10.7 KB | Auto birthday wishes every hour |

### ✅ Core Files Updated
- `deploy-commands.js` — 27 → 35 commands (+8 new)
- `bot.js` — Imports all modules, routes commands, hooks into events
- Auto-mod listener attached in `ready` event ✅
- Birthday cron (1h interval) attached ✅
- LFG cleanup (30min interval) attached ✅
- Achievement check in `messageCreate`, `guildMemberAdd`, `guildMemberUpdate` ✅
- Help command updated with all V3 commands ✅

### ✅ Commands Deployed + Bot Restarted
- 35 commands registered via `node deploy-commands.js` ✅
- `systemctl restart psvibe-discord-bot` ✅
- Syntax check: all modules + bot.js + deploy-commands.js passed ✅
- Bot active, no errors in logs ✅

### 📊 Complete Command List (35 Total)
- 🎮 Gaming:       /games /slots /promo /rank-tiers /tournament
- 💳 Account:      /balance /my-stats
- 🏆 XP & Levels:  /rank /leaderboard /daily /achievements
- 🍕 Food & Info:  /hours /menu
- 📅 Booking:      /book check /book request
- 🎵 Music:        /play /skip /stop /queue /nowplaying
- 🌟 Community:    /suggest /giveaway /vip /report /invite /8ball /dice /set-birthday /lfg
- 🔧 Staff:        /automod /event /status-set
- 🎫 Support:      /ticket open /ticket close
- 💎 Features:     /poll /help

### ⚠️ Pending Items
- `BIRTHDAY_FILE` error and `getLevel` error seen in old process logs (pre-restart) — current process is clean
- Some unhandled interaction warnings (non-blocking, cosmetic)
- Boss said to continue with docs update

### 🔧 Bot Running Status (20:45 UTC)
- ✅ PS VIBE Bot — active (pid 147161, 60.5MB mem)
- ✅ 35 commands registered
- ✅ Auto-mod, birthday cron, LFG cleanup all active
- ✅ No errors in current session

### Bot Analytics Tab Added to Kora Dashboard
- Tab button + content panel added to `/root/.openclaw/workspace/kora_dashboard/index.html`
- 6 stats cards, user segments, top commands, peak hours panels
- User table expanded 11→16 columns (Sessions, Bookings, Total Spend, Tags, Funnel Step)
- Tags rendered as colored badges
- i18n keys for both EN/MY
- Auto-refresh every 60s
- Dashboard serving HTTP 200 on port 9091 ✅

## Memory (2026-06-17)

### 🔴 VPS DOWN — 5.223.81.16 SSH Connection Refused
- **Time detected:** 19:31 UTC (02:01 AM Myanmar Time)
- **Status:** ❌ UNRESOLVED

### Disaster Recovery Backup Failure (5/6 items failed)
- All 5 remote-dependent items failed with `ECONNREFUSED 5.223.81.16:22`:
- ❌ MySQL Database
- ❌ Sale Bot Code
- ❌ API Server Code
- ❌ Dashboard Build
- ❌ Systemd Services
- ✅ Kora Config (local only, 483.1 KB)

### SSH Test
- ssh root@5.223.81.16:22 → Connection refused
- Confirmed: VPS is actively refusing SSH. May be down, firewalled, or sshd crashed.

### Action Taken
- [ ] Set morning reminder to notify Boss at 8:30 AM Myanmar Time
- [ ] Logged in daily memory

### Suggestion System — Full Integration (Discord + Web Dashboard)

### What Was Done

#### 1. Discord Bot — Staff Review Commands (`/root/psvibe-discord-bot/bot.js`)
- Converted the `/suggest` command from a simple input to subcommand-based:
- `/suggest create <game> [reason]` — Submit a suggestion
- `/suggest approve <id>` — Staff only — Sets status to "approved", updates embed in #suggestions with green ✅
- `/suggest reject <id> [reason]` — Staff only — Sets status to "rejected", updates embed with red ❌
- `/suggest list` — Staff only — Shows all pending suggestions
- `/suggest view <id>` — Anyone — View any suggestion by ID

#### 2. deploy-commands.js
- Updated to register all 5 subcommands under `/suggest`. Deployed successfully (35 commands).

#### 3. API Server (`/root/psvibe_api_server/app.py`)
- Added 3 new endpoints:
- `GET /api/suggestions?status=pending|approved|rejected`
- `GET /api/suggestions/<id>`
- `PUT /api/suggestions/<id>`

#### 4. Kora Dashboard (`/root/.openclaw/workspace/kora_dashboard/index.html`)
- Added "💡 Suggestions" tab with stats, filters, sorting, action buttons, detail modal.

#### 5. Data Normalization — Fixed suggestion #1 missing `status` field.

### Services Restarted
- `psvibe-discord-bot` ✅
- `psvibe-api` ✅

### Files Modified
- `/root/psvibe-discord-bot/bot.js`, `deploy-commands.js`, `suggestions.json`

### Phase 3.7 — Waitlist Auto-Notify on Booking Cancel ✅ (04:35 UTC)

### What Was Done
- When a booking is cancelled, the system now auto-notifies the first matching waitlisted customer via Telegram.

### Files Modified
- Lines 1905–1971: Added `_auto_notify_waitlist()` helper function
- Lines 2016–2025: Fire-and-forget call in `api_booking_cancel()`
- Lines 1338–1352: Added to `PATCH /api/bookings/{id}/status` when status=cancelled

### Key Design Decisions
- Waitlist lives in `console_booking` with `status='Waiting'` (no separate table)
- Uses `asyncio.create_task()` fire-and-forget — cancel NEVER fails due to waitlist
- Matches by `booking_date` + `console_id` (with `console_type` fallback via JOIN)
- Oldest waiting entry (by `created_at ASC`) gets Notified first
- Telegram notification sent via Customer Bot / Sale Bot

### Verification
- Syntax check: ✅ Both files pass
- API restart: ✅ Active
- Cancel booking #531 (C-10): ✅ Cancelled, console freed
- Cancel booking #490 + waitlist entry #535 match: ✅ Entry marked Notified
- Existing cancel preserved: ✅ No breakage

### Phase 1-3 Full Verification & Bug Fixes (05:00 UTC)

### Verification Results
| ✅ Pass | ၁၂ ချက် |
| ⚠️ Partial → Fixed | ၃ ချက် |
| ❌ Critical → Fixed | ၁ ချက် (P3.3) |

### 3 Fixes Applied
- **P3.3 Booking Conflicts SQL:** `time_slot` → `start_time` in SQL query (app.py line 4150)
- **P1.1 Index:** Created `idx_date_console_time(booking_date, console_id, start_time)`, dropped old incomplete index
- **P2.1 Timer Dedup:** `session_timer.py` now skips API-side timer when booking has `telegram_chat_id` (bot handles own reminders)
- **Final Status:** All 15 features verified + working ✅

## Memory (2026-06-19)

### Heartbeat Check (13:08 MMT)
- Health monitor: overall 53.5 (mostly false positives - core files exist, VPS reachable)
- Dead-letter queue: empty
- Git backup: OK (5 files committed)
- Memory index: 1436 topics
- Knowledge graph: 54 nodes, 1419 edges
- Lock cleanup: 0 cleaned
- yyo-personal-wallet: old alerts (Jun 9-16), checking status
