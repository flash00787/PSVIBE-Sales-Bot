
## AppArmor Status & Management

- AppArmor kernel module remains loaded and profiles (`docker-default`, `snap-confine`, `rsyslogd`) are in enforce mode, preventing direct file modification via SSH `exec` commands.
- **Impact of Uninstalling AppArmor:** Significantly weakens system security, removes protection against zero-day exploits, and reduces audit logs. Not recommended for public-facing servers.
- **Bypassing AppArmor for OpenClaw:**
    1.  **Modify AppArmor Profiles (Recommended & Secure):** Adjust specific profiles to grant necessary permissions (e.g., read/write access to certain directories) for OpenClaw processes. This involves switching to complain mode, auditing denied actions, adding rules to the profile, and reloading the profile.
    2.  **Completely Disable/Uninstall AppArmor (Risky):** Removes all security restrictions, but exposes the VPS to significant security vulnerabilities.

## Contact Information

- **Chan Su Su Hlaing:** chansusuhlaing@gmail.com

## Google Drive Access
- **OpenClaw Service Account:** `openclawagent@open-claw-agent-497416.iam.gserviceaccount.com`
- **SA Key File:** `/home/node/.openclaw/workspace/kora_drive_sa.json` (also copied to VPS at `/root/Sales-Tele-Bot/kora_drive_sa.json`)
- **PS VIBE Drive Root Folder ID:** `1V6ctTJpXaoRIDnrfxwhVO72I7jfD5GsS`
- **Accessible Drive Structure:**
  - 📂 **Design Files/** — Logos (.ai), Member Cards (.ai), Collaterals (.pdf), Social Profiles, Fonts, PNG/JPG assets
  - 📂 **Financial Statements/** — All Google Sheets (Staff File, Owner Master File, Bot Analytics, test file)
  - 📂 **Menu Book/** — Astro menu JPG posters (9 images)
  - 📊 **Discussion** — Sheet
  - 📄 **Member topup ranking plan** — Google Doc
- **Access Method:** Use `kora_drive_sa.json` SA key with Google Drive API v3 (readonly scope)
- **Scopes:** `https://www.googleapis.com/auth/drive.readonly`
- **Notes:** This is SEPARATE from the VPS bot's service account (`user-408@ps-vibe-sales-tele-bot.iam.gserviceaccount.com`). This SA is for Kora's/OpenClaw's direct Drive access only.

## Boss Info — Ko Aung Chan Myint (ကိုအောင်ချမ်းမြင့်)

### Business & Professional
- **Founder & Manager:** PS VIBE - PS5 Gaming Lounge. Tagline: "Play The Game. Share The VIBE!"
- **Director:** Synergy Hub (digital business card project — Kora)
- **Education:** Professional Diploma in Financial Management at Strategy First International College (Zoom)
- **Gmail:** chanmyint123456789@gmail.com

### Lifestyle & Interests
- **Vehicle:** BYD Han EV (EVnet/MEVP)
- **Cycling:** Road cyclist (completed 200K Strava challenge), researches bike gear (action cameras, cycle computers)
- **Fragrances:** Luxury collection — Dior Sauvage Elixir, Casamorati Mefisto, Creed Aventus
- **Travel:** Frequent traveler — Bangkok, Vietnam (Hanoi, Sapa, Halong Bay)
- **Food:** Korean cuisine, Singapore chicken rice (ကြက်ဆီထမင်း), မုန့်ဟင်းခါး

### PS VIBE Rules
- Always source minute balance data exclusively from Column H of the "Card_wallet" tab in Google Sheets.
- Receipt templates: Remove Burmese footer text (no 'ကျေးဇူးတင်ပါသည် ပြန်လည်ကြွရောက်ပါ').

### Addressing
- **Direct/internal:** "Boss" or "အစ်ကို"
- **External/third parties:** "Ko Aung Chan Myint" (ကိုအောင်ချမ်းမြင့်)
- **Email:** chanmyint123456789@gmail.com

## Email Setup
- Gmail API via OAuth 2.0 (readonly + send scopes)
- Token: `/home/node/.openclaw/workspace/token.json`
- Secret: `/home/node/.openclaw/workspace/secret.json`
- Sender script: `/home/node/.openclaw/workspace/send_email_api.py`
- Send method: HTTPS (port 443) — SMTP blocked by DigitalOcean

## Sales Bot Versions & Backup Inventory (2026-05-27)

### Version Naming
- **V.1 (Restored Version)** — Monolithic `main.py` (12,249 lines), restored from `main.py.bak.phase4`. **Currently RUNNING** on psvibe-bot.service (PID 247137). Full Telegram imports, working.
- **V.2 (Refactored/Phase 4)** — Modular (76 .py files, 26 handler modules). **STOPPED**. Import bugs FIXED in staging, verified by runtime test. Not deployed to production.

### Version V.1 — Backup Locations

**📍 VPS (Primary — on-machine):** `/root/backups/`
- `psvibe-monolithic-restored-20260527_000345.tar.gz` (11MB) — **V.1 monolithic backup** (pid lock, logs, .bak files preserved)

**📍 Staging (reference copy):** `/root/staging/monolithic_ref/` — Full copy of running V.1 code

**⏳ Pending:** Workspace base64 copy (not yet downloaded)

### Version V.2 — Backup Locations

**📍 VPS `/root/backups/`:**
- `psvibe-refactored_20260526_233759.tar.gz` (396KB) — V.2 with tonight's fixes (now_mmt, _ALLOWED_USER_IDS, app.py imports)
- `psvibe-bot-refactored_20260526_232503_fullbackup.tar.gz` (408KB) — Previous V.2 full backup
- `predeploy_Sales-Tele-Bot_refactored_20260526_232608.tar.gz` — V.2 pre-deploy from staging
- `psvibe-restored-by-agent_20260526_234949.tar.gz` — Manus sandbox restore (also Phase 4 modular)

**📍 Workspace (Kora Container):**
- `2026-05-26_refactored_backup.b64` (528KB) — V.2 refactored code backup
- `2026-05-26_original_backup.b64` (30MB) — Old buggy Phase 4 original
- MD5 fingerprints for both

**📍 Staging:** `/root/staging/bot_src/` — V.2 tested & verified (23 checks, runtime test PASSED)

### Other Archived Versions
- `psvibe-original_20260526_233759.tar.gz` (22MB) — Old VPS original (same import bugs, NOT V.1)
- `psvibe-bot-original_20260526_232504.tar.gz` (22MB) — Previous original backup

### Deploy Process (from now on)
1. Copy code → `/root/staging/bot_src/`
2. Run: `/root/staging/scripts/deploy.sh /root/staging/bot_src /root/psvibe-sale-bot`
3. On failure: `/root/staging/scripts/rollback.sh`

### ⏳ Pending
- Google Drive upload (needs SA write scope enabled)
- Cross-check existing MD5 fingerprints vs new V.1 backup
- Push final working code to GitHub

## Gemini API Key Configuration
- **Location:** `~/.openclaw/agents/main/agent/auth-profiles.json`
- **Configuration:** Two API keys are configured in an array within this file.
- **Rotation:** OpenClaw uses an internal mechanism to rotate these keys for Gemini API calls.
- **Status:** Keys are located and configured for rotation. Individual key functionality testing is pending.

## Agent Coordination Pattern (Good Behavior — 2026-05-27)

When spawning multiple sub-agents that need to coordinate:

1. **Create shared interface spec FIRST** before spawning (file on VPS or workspace)
2. **Use obfuscated path mapping** (path_mapping.json) — agents never use raw paths
3. **Create COORDINATION.md** on shared storage with rules all agents must follow
4. **Each agent writes completion status** to AGENT_STATUS.md
5. **Fail fast strategy:** Use flash model + high timeout (10m for code-gen) + instruct no retries
6. **Keep code-writing agents focused** — narrow scope avoids timeout
7. All agents read/write to the same coordination files for sync

## Sub-Agent Timeout Config (per Agent)

### Kora (updated 2026-05-28)
- **Sub-agent Timeout:** 2 hours (120 min) — config: `agents.defaults.subagents.runTimeoutSeconds = 7200`
- **Max Retries:** 2
- **Concurrent Sub-agents:** 30
- **Error Reporting:** Sub-agent error/failure → report to Kora automatically
- Reason: Heavy coding projects (PS VIBE 12K+ lines), complex orchestration

### Nova (updated 2026-05-27)
- **Sub-agent Timeout:** 30 min
- **Max Retries:** 2
- **Concurrent Sub-agents:** 10
- Reason: Lighter tasks, personal assistant context

## Coding Rule: Pro Model Only
- **Rule from:** Boss Osmo (2026-05-27)
- **Coding tasks:** NEVER use DeepSeek V4 Flash — must use Pro model (DeepSeek V4 Pro)
- **Code review:** Claude Sonnet 4 or DeepSeek V4 Pro
- **Research for code:** Grok 4.3
- **Exception:** Code reading/analysis only (no writing) → Flash allowed
- **Non-coding** (chat, explain, read) → Flash is fine

## Kora's Role Rule (from Boss Osmo 2026-05-27)
- **Primary role:** Conversation with Boss + agent management/coordination
- **NEVER directly edit code** — delegate all coding to agent sub-agents (Pro model)
- **Manage agents well** = Kora's #1 priority
- **Primary model** (DeepSeek V4 Flash) = for conversation & managing agents only

## 🧠 Memory & Sub-agent Tracking System (2026-05-28 Upgrade — Phase 2)

### Design Principles
- **Write it down, every time.** No mental notes — files survive session restarts.
- **Structured + Readable.** JSON for machine parsing, MD for human reading.
- **Boot-time restore.** On startup, read recent journal to rebuild context.
- **Real-time active registry.** Know what's running RIGHT NOW, not just on boot.
- **Orphan detection.** Catch sub-agents that went missing or got stuck.

### File Inventory

| File | Purpose | Format |
|------|---------|--------|
| `memory/subagent-journal.json` | All sub-agent spawns, completions, results | JSON (structured) — V2 |
| `memory/active_tasks.json` | Currently-RUNNING sub-agents (real-time) | JSON (lightweight) |
| `memory/agent-status.md` | Live human-readable dashboard | Markdown (auto-generated) |
| `memory/subagent_ctl.py` | Master control script (register/complete/list/status/orphans/summary) | Python (executable) |
| `memory/session-memory.md` | Current session running log | Markdown |
| `memory/session-tracker-last.md` | Last session timestamp + status | Markdown |
| `memory/heartbeat-state.json` | Last heartbeat check + stuck/pending tasks | JSON |
| `memory/YYYY-MM-DD.md` | Daily notes | Markdown |
| `memory/consolidator.py` | Daily log → MEMORY.md auto-consolidation | Python |
| `memory/boot_protocol.py` | Startup check: journal + active_tasks scan | Python |
| `HEARTBEAT.md` | Memory maintenance task list | Markdown |

### Sub-agent Journal Entry Schema (V2)
```json
{
  "id": "unique-id",
  "taskName": "shorthand-label",
  "task": "full task description",
  "model": "provider/model",
  "spawned": "ISO-8601",
  "completed": "ISO-8601 or null",
  "status": "running|completed|partial|failed",
  "summary": "what happened",
  "sessionKey": "main|session:<key>",
  "channel": "telegram|discord|etc",
  "resultFile": "/path/to/output or null"
}
```

### Active Tasks Registry (real-time)
```json
{
  "version": 1,
  "active": {
    "<task-id>": {
      "taskName": "...",
      "model": "provider/model",
      "spawned": "ISO-8601",
      "task": "full description",
      "goal": "what it should accomplish"
    }
  }
}
```

### Boot Protocol (Session Startup)
1. Run `python3 memory/boot_protocol.py` — checks BOTH journal + active_tasks
2. Detects:
   - **Partial tasks** (journal status=partial)
   - **Running tasks** (journal status=running)
   - **Orphans** (in active_tasks but NOT in journal — missing cleanup)
   - **Stale** (journal running >30min — likely stuck)
3. Use `--json` for machine-parseable output
4. Use `--no-fail` to always exit 0
5. Report to Boss any pending/incomplete work

### Spawn Protocol (When spawning sub-agents)
1. **BEFORE** `sessions_spawn`:
   ```bash
   python3 memory/subagent_ctl.py register <taskName> <model> "<goal>"
   ```
   This writes to BOTH journal + active_tasks.json, outputs a task-id
2. Call `sessions_spawn` with the task
3. **AFTER** completion:
   ```bash
   python3 memory/subagent_ctl.py complete <task-id> <status> "<summary>"
   ```
   This removes from active_tasks, updates journal

### Quick Dashboard
```bash
python3 memory/subagent_ctl.py status    # Summary counts
python3 memory/subagent_ctl.py list      # Active tasks detail
python3 memory/subagent_ctl.py orphans   # Check for stuck/orphaned
python3 memory/subagent_ctl.py summary   # Full dashboard to agent-status.md
```

### Heartbeat Memory Maintenance (every ~4h)
- Run: `python3 memory/heartbeat_routine.py`
  - Scans BOTH journal + active_tasks for stuck/pending
  - Auto-generates agent-status.md
  - Updates heartbeat-state.json
- Run: `python3 memory/consolidator.py --apply`
  - Distills daily logs into MEMORY.md
  - Deduplicates against existing content
- Prune outdated entries from MEMORY.md

## Memory (2026-05-26)

### Cross-Check: Monolithic vs Refactored (Analysis Complete)
- **Monolithic backup saved:** `/root/backups/psvibe-monolithic-restored-20260527_000345.tar.gz` (11MB)
| Metric | Monolithic (main.py.bak.phase4) | Refactored (Phase 4) |
|---|---|---|
| Structure | Single `main.py` (12,249 lines) | 76 .py files, 26 handler modules |
| Functions | 395 defs | 426 defs |
| Telegram imports | ✅ Full (`from telegram.ext import Application, ...`) | ❌ Missing in `app.py` (references via `from bot import *`) |
| `now_mmt()` | ✅ Defined globally | ✅ In `__init__.py`, but 13 handler modules missing import (FIXED) |
| `_ALLOWED_USER_IDS` | ✅ Hardcoded in `show_main_menu()` | ❌ Missing from handlers (FIXED with `fetch_allowed_staff_ids()`) |
| error_handler | ✅ `NetworkError, TimedOut` imported inside function | ✅ Fixed (help.py has import inside function) |
| Google Sheets | Same `gspread` + `oauth2client` pattern | Same — exact duplicate via `__init__.py` |
| Cache refresh | Background task every 5 min | Same — duplicate in `app.py` |
| auth_middleware | None (auth inside `show_main_menu()`) | ✅ TypeHandler at group=-999 (better!) |
| api_server | Was NOT in original — Manus sandbox added it | Not present |
| app.py | N/A (everything in main.py) | 455 lines, missing Telegram imports at module level |

### Refactored Version — Fixes Needed (Patch List)
- 1. **app.py** — Add `from telegram import Update, BotCommand` + `from telegram.ext import (Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ApplicationHandlerStop, ContextTypes, filters, TypeHandler)` + `import os` before any handler references
- 2. **Handler modules (13 files)** — `from bot import now_mmt` already added ✅
- 3. **_ALLOWED_USER_IDS** — Replaced with `fetch_allowed_staff_ids()` from Sheets ✅
- 4. **help.py error_handler** — `from telegram.error import NetworkError, TimedOut, Conflict` already fixed ✅
- 5. **main.py** — `from dotenv import load_dotenv` removed (service uses EnvironmentFile) ✅

### Current State
- **Monolithic version RUNNING**: psvibe-bot.service (PID 243060)
- **Refactored project STOPPED**: psvibe-bot-refactored.service
- **Customer bot**: using /root/Sales-Tele-Bot/customer_bot.py (monolithic, Manus sandbox version, 5,725 lines)
- **Service difference**: monolithic has no auth middleware (auth inside show_main_menu) — refactored had better architecture

## Memory (2026-05-27)

### OpenClaw Gateway Restart
- Gateway restart completed successfully (port 18789, LAN bind)
- Minor message confusion due to system auto-restart notifications in chat

### Nova Backup & Docker Compose Setup
- Nova's backup files organized in `backups/nova-backup/`
- `nova_openclaw.json` — Nova Telegram config (real bot token)
- `nova_docker_compose_section.yml` — Nova compose section
- `docker-compose.yml.bak` — Full original compose
- New `docker-compose.yml` created with 3 agents: **Nova** (3002), **CoCo** (3003), **GayZoeLay** (3004)
- Nova's deployable config at `configs/nova/openclaw.json`
- Nova setup guide: `configs/nova/NOVA_SETUP.md`

### Nova Info (from Ye Yint Oo's Gmail)
- **Owner:** Ye Yint Oo (Malboro) — Telegram: 8336350778
- Nova is Ye Yint Oo's personal AI assistant, runs on OpenClaw (local PC setup)
- Can do: file r/w, web search, code run, image/music/video gen, reminders, Gmail
- Gmail has 2 intro emails from Ye Yint Oo about Nova

### CoCo & GayZoeLay
- Placeholder configs created at `configs/coco/openclaw.json` and `configs/gayzoelay/openclaw.json`
- Need Telegram bot tokens from @BotFather

## Memory (2026-05-28)

### Session Summary (2026-05-28)

### ✅ Completed
- ✅ Phase 2 memory upgrade implementation
- ✅ Verification of all test steps

### ❌ Pending
- ❌ sync-service-create retry
- App.py MySQL integration is pending

### 💡 Key Decisions
- decision: Pro model for coding tasks
- Flash model for conversation only is a new rule
- Boss wants daily updates

### 📝 Notes
- Sequential batch processing preferred

### Phase 3 Audit (10:26 UTC)
- Audit agent ran full checks on Phase 3 work
- Sync Service Integration: ✅ PASS
- BI Dashboard: ✅ PASS
- Report Generator: ⚠️ PARTIAL — bot restart needed. Fixed by restarting psvibe-sale-bot.service.
- PDF generation (report_pdf) not implemented
