# OPS_REFERENCE.md — PS VIBE Operations Quick Reference

> Location: `/root/coordination/` unless noted.
> VPS: `5.223.81.16` (root@)

---

## Customer Bot — Console Status Handler

> *(Notes recovered from corrupted header — 2026-05-31)*

- **Command:** `/status` → `cmd_console_status`
- **File:** `/root/psvibe-sales-bot/customer_bot/handlers.py` (line 533)
- **Cache pop:** `_api._cache_pop("consoles")` → clears cache before fetch
- **Fetch:** `_api._fetch_consoles()` → async cached via aiohttp
- **API endpoint:** `GET /api/fetch_console_status`
- **Booking data:** `_api._api_get(f"bookings/search?date={today_mmt()}")`
- **Display:** Icons 🟢FREE 🔴IN USE ⚫OFF 🟡RESERVED
- **Cache:** In-memory, 300s TTL, async lock, sweeper every 5 min

---

---

## 🔍 Quick Diagnostics

```bash
# Quick health overview
python3 /root/coordination/status_reporter.py quick

# All 8 integration tests
python3 /root/coordination/integration_tester.py test

# Run unit tests (33 tests, ~0.3s)
python3 /root/coordination/test_runner.py
cd /root/psvibe-sales-bot && python3 -m pytest tests/ -q

# Check individual services
systemctl status psvibe-sale-bot
systemctl status psvibe_customer_bot
systemctl status psvibe-api
journalctl -u psvibe-sale-bot -n 30 --no-pager
```

---

## 📊 Flow Analysis (State Machines)

```bash
# Full state machine audit
python3 /root/coordination/flow_analyzer.py --full

# Check for orphan states
python3 /root/coordination/flow_analyzer.py --states

# Check handler registrations
python3 /root/coordination/flow_analyzer.py --report

# Check for missing await calls
python3 /root/coordination/flow_analyzer.py --check-await
```

**Output highlights:** 27 handlers, 181 BotState entries, 468 functions, callback chain depth, orphan detection ✅

---

## 🗺️ Architecture Mapping

```bash
# Circular import detection
python3 /root/coordination/arch_mapper.py --circular

# Text dependency report
python3 /root/coordination/arch_mapper.py --dep-text

# Mermaid.js diagram generation
python3 /root/coordination/arch_mapper.py --graph

# Graphviz DOT output
python3 /root/coordination/arch_mapper.py --dot
```

**Output highlights:** 56 modules, 966 imports, 53 circular deps, 55 star imports ⚠️

---

## 🔍 Enhanced Validation

```bash
# Full audit (all checks)
python3 /root/coordination/enhanced_validator.py --full

# Async pattern check
python3 /root/coordination/enhanced_validator.py --async-check

# Handler registration validation
python3 /root/coordination/enhanced_validator.py --handlers

# Code pattern issues (prints, bare excepts, shadowing, etc.)
python3 /root/coordination/enhanced_validator.py --patterns

# Function signature validation
python3 /root/coordination/enhanced_validator.py --signatures
```

**Output highlights:** 0 async issues, 0 signature issues, 105 pattern issues (56 prints, 32 shadowed names) ✅/⚠️

---

## ⚙️ Safe Fix Workflow

```bash
# NOTE: fix_safety.py is PER-FILE (--target-file is required, NOT --directory)

# 1. TAKE SNAPSHOT (before any fix)
python3 /root/coordination/fix_safety.py snapshot --target-file bot/handlers/main_menu.py

# 2. VERIFY (after fix)
python3 /root/coordination/fix_safety.py verify --target-file bot/handlers/main_menu.py

# 3. ROLLBACK (if verify fails)
python3 /root/coordination/fix_safety.py rollback --target-file bot/handlers/main_menu.py

# For full-project backup (workflow engine safe-fix uses this):
tar czf /tmp/pre_fix_backup.tar.gz --exclude=__pycache__ --exclude=.git -C /root/psvibe-sales-bot .
tar xzf /tmp/pre_fix_backup.tar.gz -C /root/psvibe-sales-bot
```

**Safety gates (in order):** Syntax ✅ → Imports ✅ → Services ✅ → Tests ✅ → Journal ✅

---

## 🚀 Workflow Engine (NEW — Phase 3)

```bash
# 4 pipelines: quality | full-audit | safe-fix | auto-deploy

# Quick quality check (~2s)
python3 /root/coordination/workflow_engine.py --run quality

# Full system audit (~7s)
python3 /root/coordination/workflow_engine.py --run full-audit

# Safe fix with auto-rollback (~2s)
python3 /root/coordination/workflow_engine.py --run safe-fix

# Auto deploy pipeline (~3s)
python3 /root/coordination/workflow_engine.py --run auto-deploy

# Retry last failed pipeline
python3 /root/coordination/workflow_engine.py --retry

# View history
python3 /root/coordination/workflow_engine.py --history
```

## 📋 Task Bridge (Sub-agent ↔ Workflow)

```bash
# Create sub-agent task
python3 /root/coordination/task_bridge.py create --pipeline safe-fix --step "Fix" --files handler.py

# List pending tasks
python3 /root/coordination/task_bridge.py list pending

# Complete task
python3 /root/coordination/task_bridge.py complete <task-id> --status ok --message "Fixed"
```

## 🔔 Notifier (Pipeline Alerts)

```bash
# Send notification (pipeline auto-sends on completion)
python3 /root/coordination/notifier.py send --title "Pipeline done" --message "4/4 ✅" --level success

# Check unread
python3 /root/coordination/notifier.py list --unread

# Mark all read
python3 /root/coordination/notifier.py mark-all
```

## 🩺 Auto-Healer (Service Self-Repair)

```bash
# Check + auto-heal if needed (3 failures → restart → verify → notify)
python3 /root/coordination/auto_healer.py check

# View status
python3 /root/coordination/auto_healer.py status

# View history
python3 /root/coordination/auto_healer.py history
```

---

## 🚀 Phase 2 — New Tools

### Auto Git Sync
```bash
# Manual push with custom message
python3 /root/coordination/auto_git_sync.py -m "fix: description"

# Dry-run (check changes only)
python3 /root/coordination/auto_git_sync.py --dry-run

# Auto: runs every 6 hours via cron (dry-run only, commit on manual call)
```

### Service Watchdog
```bash
# Status
systemctl status psvibe-watchdog

# Manual check
python3 /root/coordination/service_watchdog.py

# Auto restarts failed services + writes alert to findings/
```

### Status Board
```bash
# Generate snapshot
python3 /root/coordination/status_board.py

# View the JSON
cat /root/coordination/status_board.json
```

### Auto Verify (Post-Fix Safety)
```bash
# Run after any code change — tests + services + journal check
python3 /root/coordination/auto_verify.py

# On FAIL: auto rollback via fix_safety.py + writes alert
```

### Intersession Auto-Handoff
```bash
# Runs automatically on session start
python3 /home/node/.openclaw/workspace/memory/boot_protocol.py
# Shows: active projects, last session time, stale check, incomplete tasks
```

### Cron Health Check
```bash
# Check all crons are running + logs are fresh
python3 /root/coordination/cron_health.py --check

# Auto-repair missing crons
python3 /root/coordination/cron_health.py --repair
```

### Star Import Analyzer
```bash
# Scan all files for `from bot import *`
python3 /root/coordination/star_import_analyzer.py --scan

# Generate detailed fix report (JSON)
python3 /root/coordination/star_import_analyzer.py --report
```

---

## 🔧 Import Validation

```bash
# Scan all handler files
python3 /root/coordination/import_scanner.py scan --all-handlers

# Scan modified files only
python3 /root/coordination/import_scanner.py scan --modified

# Cross-module import validation
python3 /root/coordination/import_scanner.py scan --cross-module
```

---

## 🧪 Test Framework

```bash
# Run all tests (CI mode)
python3 /root/coordination/test_runner.py

# Run with verbose output
cd /root/psvibe-sales-bot && python3 -m pytest tests/ -v

# Run specific test file
cd /root/psvibe-sales-bot && python3 -m pytest tests/test_members.py -v

# Run with coverage
cd /root/psvibe-sales-bot && python3 -m pytest tests/ --cov=handlers
```

**33 tests:** main_menu(5), members(5), sales(6), booking(3), reports(4), finance(5), stock(5) ✅

---

## 🚀 Full Code Quality Audit (CI Pipeline)

```bash
# Complete pipeline (run in order)
python3 /root/coordination/flow_analyzer.py --full           # Stage 1: Flow
python3 /root/coordination/arch_mapper.py --circular          # Stage 2: Arch
python3 /root/coordination/enhanced_validator.py --full       # Stage 3: Validate
python3 /root/coordination/import_scanner.py scan --all-handlers  # Lint
python3 /root/coordination/test_runner.py                      # Tests
python3 /root/coordination/integration_tester.py test          # Integration
```

---

## 📦 Service Management

```bash
# Service commands
systemctl restart psvibe-sale-bot
systemctl restart psvibe_customer_bot
systemctl restart psvibe-api
systemctl daemon-reload   # after file changes

# Check all services
systemctl is-active psvibe-sale-bot psvibe_customer_bot psvibe-api

# Logs
journalctl -u psvibe-sale-bot -n 50 -f   # follow mode
journalctl -u psvibe_customer_bot -n 50
journalctl -u psvibe-api -n 50
```

---

## 📂 Project Locations

| Path | Purpose |
|------|---------|
| `/root/psvibe-sales-bot/` | PS VIBE Sales Bot (109 .py files) |
| `/root/psvibe-sales-bot/tests/` | Unit tests (33 tests, pytest 9.0.3) |
| `/root/coordination/` | Dev Structure tools (6 tools) |
| `/root/coordination/findings/` | Audit/fix findings output |
| `/root/backups/` | Snapshot backups |
| `/root/staging/` | Deploy staging directory |
| `/opt/construction-bot/` | Three Brothers Construction Bot (Docker) |
| `/root/scripts/construction-bot-manager.sh` | Construction Bot manager (READ-ONLY) |
| `/root/YYO-Personal-Wallet/` | YYO Personal Wallet Bot |
| `/root/scripts/wallet-bot-manager.sh` | Wallet Bot manager (READ-ONLY for Nova) |
| `/opt/openclaw/nova/` | Nova workspace (host mount → container: `/home/node/.openclaw/`) |

---

## 🛡️ Nova Access

```bash
# Nova Host API (from inside Nova's container)
curl -s -X POST http://127.0.0.1:7890/exec \
  -H "Authorization: Bearer $(cat /home/node/.openclaw/host-api-token.txt)" \
  -d '{"cmd":"systemctl status psvibe-sale-bot"}'

# Or use helper script
bash /home/node/.openclaw/host-exec.sh "python3 /root/coordination/status_reporter.py quick"
```

**Nova Access Rules:**
- Self-upgrade: FULL ✅ | YYO Wallet: READ-ONLY ✅ | Construction Bot: NO ACCESS ❌
- Write access to YYO Wallet: Requires SOP docs + code quality audit
- No SSH key, no SSH password — Host API only

---

## 🔒 Fix Lock System (fix_lock.py)

**Location:** `/root/coordination/fix_lock.py`

Prevents parallel fix agent conflicts. Lock file at `/tmp/.fix_lock` with 10-min stale timeout.

```bash
# Acquire lock before fixing
python3 /root/coordination/fix_lock.py acquire

# Check if lock is held
python3 /root/coordination/fix_lock.py status

# Check if another agent holds it (exit 1 if locked)
python3 /root/coordination/fix_lock.py check

# Release after fix
python3 /root/coordination/fix_lock.py release

# Clear stale lock (manual override)
python3 /root/coordination/fix_lock.py clear
```

**CRITICAL RULE:** Fix agents MUST acquire lock before editing files. NEVER spawn parallel fix agents.

---

## 💻 Direct Node.js SSH (Quick VPS Checks)

Replace sub-agents for simple VPS operations. Use `require('ssh2')` from workspace.

```node
var {Client}=require("ssh2");
var fs=require("fs");
var k=fs.readFileSync("/home/node/.openclaw/workspace/.ssh/id_rsa");
var c=new Client();
c.on("ready",function(){
c.exec("COMMAND_HERE",function(e,s){
if(e){console.error(e.message);c.end();return;}
var o="";
s.on("data",function(d){o+=d.toString();});
s.stderr.on("data",function(d){o+="[S]"+d.toString();});
s.on("close",function(){console.log(o);c.end();});
});
}).connect({host:"5.223.81.16",username:"root",privateKey:k,readyTimeout:15000});
```

**For big Python scripts:** Write to `/tmp/`, base64 encode, pipe to python:
```bash
timeout 30 python3 /tmp/script.py 2>&1
```

---

## 🔒 Parallel Fix Lock (v2 — File-Level Locking)

**Files:** `/root/coordination/fix_lock.py`

Allows concurrent fix agents as long as they touch DIFFERENT files. Same file = BLOCKED.

### Commands
```bash
# Acquire lock for files
python3 /root/coordination/fix_lock.py acquire <agent_name> --files file1.py,file2.py

# Release lock after done
python3 /root/coordination/fix_lock.py release <agent_name>

# Check if files conflict with active agents
python3 /root/coordination/fix_lock.py check <agent_name> --files file1.py,file2.py

# Show all active locks
python3 /root/coordination/fix_lock.py status

# Clear all locks (startup/reset)
python3 /root/coordination/fix_lock.py clear
```

### Rules (Exit 0 = OK, Exit 1 = Blocked)
| Scenario | Result |
|----------|--------|
| Same project, DIFFERENT handler files | ✅ ALLOWED |
| Different projects (bot/ + api_server/) | ✅ ALLOWED |
| Different layers (handler + API endpoint) | ✅ ALLOWED |
| Read-only + Fix | ✅ ALLOWED |
| Same exact file | ❌ BLOCKED |
| bot/__init__.py or bot/app.py | ❌ BLOCKED |
| Single-threaded files listed in SINGLE_THREADED_FILES | ❌ BLOCKED |

### Max Parallel: 4 simultaneous fix agents

---

## 🌐 API Inventory Endpoint

**`GET /api/sheets/inventory`** at `/root/psvibe_api_server/app.py:2050`

Aggregates MySQL `inventory` and `stock_out` tables:
```sql
SELECT i.item_name, i.category, i.quantity - COALESCE(SUM(s.quantity),0) as current_stock
FROM inventory i LEFT JOIN stock_out s ON i.item_name = s.item_name
GROUP BY i.item_name
```

Returns: `{"items": [{"name":"...", "current_stock": N}], "success": true}`

**Note:** MySQL tables currently empty — need data entry for stock filter to work.

---

## ⚡ Kora Workflow Triggers (Boss ပြော → Helper ခေါ်)

**CRITICAL: NEVER do anything manually. Task arrives → check this table first.**

| Boss Says | DO THIS | DON'T Do This |
|-----------|---------|---------------|
| "စစ်ကြည့်" / "audit" / "check"  | **Task Planner (Flash)** → break down → Fix Agent if needed | SSH ဝင်ပြီး ကိုယ်တိုင်မဖတ် |
| "ပြင်ပါ" / "fix" / "ဖြေရှင်း" | **Fix Agent (Pro)** → **Verify Agent** | Code ကိုယ်တိုင်မပြင် |
| "ဘာလို့" / "analyze" / "why" | **Task Planner (Flash)** → run tools | Journal/SSH ကိုယ်တိုင်မဖတ် |
| "flow" / "logic" / "cross check" | **Task Planner** → **Fix Agent** → **Verify Agent** | Code ကိုယ်တိုင်မဖတ် |
| "architecture" / "dependency" | **Architecture Mapper** | Import chain မလိုက် |
| "service check" / "health" | **Status Reporter** | systemctl မစစ် |
| "test" / "pytest" | **Test Runner** | pytest မခေါ် |
| "Git push" / "commit" | **Git Sync Agent** | git command မရိုက် |
| "deploy" | **Deploy Manager** | Service မချိန်း |
| "data" / "database" / "query" | **Task Planner** → **Fix Agent (Pro)** | SQL ကိုယ်တိုင်မရိုက် |

---

## 📜 SOP Documents

| Document | Path | Purpose |
|----------|------|---------|
| FIX_AGENT_SOP.md | `/root/coordination/` | Fix procedure rules (6 rules) |
| DEV_TEAM_SOP.md | `/root/coordination/` | Team workflow & roles |
| MULTI_PASS_PROTOCOL.md | `/root/coordination/` | 3-pass fix strategy |
| CODEBASE_CONTEXT.md | `/root/coordination/` | Project conventions |
| KNOWN_BUG_PATTERNS.md | `/root/coordination/` | Past incidents log |
| DEV_TEAM_SOP.md | `/root/coordination/` | Developer workflow |

---

## 🔐 Secrets

| Service | Location | Notes |
|---------|----------|-------|
| Gmail OAuth | `/home/node/.openclaw/workspace/token.json` | Auto-refresh |
| Gmail Secret | `/home/node/.openclaw/workspace/secret.json` | Client ID/Secret |
| SSH Key | `/home/node/.openclaw/workspace/.ssh/id_rsa` | VPS root access |
| VPS Secret Key | `S1_PSVIBE_2024` | SSH password (legacy) |
| Gemini API Keys | `openclaw.json` auth config | 2 keys in rotation |
| DeepSeek API Keys | `auth-profiles.json` | 5 keys in rotation |
| OpenRouter Key | `TOOLS.md` | Claude Sonnet 4 fallback |
| Grok API Key | `TOOLS.md` | Research tasks |
| Nova Host API Token | `/opt/openclaw/nova/host-api-token.txt` | Nova container access |
| Kora Drive SA | `/home/node/.openclaw/workspace/kora_drive_sa.json` | Google Drive readonly |

---

*Created: 2026-05-29. Update whenever tools change.*
