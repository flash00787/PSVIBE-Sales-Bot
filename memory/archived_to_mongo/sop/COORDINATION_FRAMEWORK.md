# 🔗 Sub-agent Coordination Framework (v2.0)
## မချိုးဖောက်ရ — ဒါက Red Line

### Problem Statement (Why This Exists)
**2026-05-28 18:30 UTC:** 6 parallel sub-agents modified `bot/__init__.py` simultaneously → 35+ bugs in chain reaction:
- Redundant `global` declarations → SyntaxError
- Missing enum values → NameError  
- Duplicate function definitions → conflict
- Corrupted alias lines → chain-reaction crash
- Indentation errors from partial overwrites

**This framework exists to NEVER let this happen again.**

---

## 0. FILE DEPENDENCY MAP (Critical)

### 🔴 Crown Jewel Files (NEVER parallel — sequential ONLY)

```
                    ┌──────────────────────┐
                    │   bot/__init__.py     │ ◄── LITERALLY EVERYTHING imports this
                    │  (2494 lines)         │
                    └──────────┬───────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                   ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │ bot/app.py   │   │ handlers/*   │   │ api_client   │
    │ (states,     │   │ (20 files)   │   │ .py          │
    │  handlers)   │   │              │   │              │
    └──────────────┘   └──────────────┘   └──────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
           ┌──────────────┐     ┌──────────────┐
           │ customer_bot │     │ main.py      │
           │ (6 files)    │     │ (entry point)│
           └──────────────┘     └──────────────┘
```

### Dependency Rules:
| File | Who imports it | Blast radius |
|------|--------------|--------------|
| **bot/__init__.py** | ALL handler files, app.py, api_client.py, main.py, customer_bot/* | **CRITICAL — 100%** |
| **bot/app.py** | main.py | **HIGH — bot won't start** |
| **bot/handlers/*.py** | app.py, main.py | **MEDIUM — one feature breaks** |
| **bot/api_client.py** | handlers/*.py, customer_bot/api.py | **HIGH — all API calls** |
| **customer_bot/*.py** | customer_bot/main.py | **MEDIUM — isolated** |
| **psvibe_api_server/** | Only itself (serves API) | **LOW — can restart independently** |

**🔴 Rule: If you modify `bot/__init__.py`, you MUST re-validate ALL imports after.**

---

## 1. Pre-Spawn Protocol (Mandatory, Every Time)

### Step 1: Run Pre-Flight Check

```bash
python3 /root/coordination/preflight.py
```

This script checks:
1. ❓ Are any other agents active? (checks lock manager)
2. ❓ Target files locked? (checks lock manager)
3. 🟢 Current services healthy? (checks systemctl)
4. 🟢 Current code compiles? (checks py_compile)
5. 🛑 If ANY check fails → BLOCK spawn → report to Boss

### Step 2: Create Auto-Backup

```bash
python3 /root/coordination/preflight.py --backup
```
This creates:
- `/root/backups/pre-<taskname>-<timestamp>.tar.gz` (full bot dir)
- `/root/backups/pre-<taskname>-<timestamp>-files/` (individual files)

### Step 3: Acquire Locks

```bash
# For each file the task will modify:
python3 /root/coordination/lock_manager.py acquire \
  --agent <taskname> \
  --files "bot/handlers/sales.py" \
  --reason "Fix sales multi-payment flow"
```

### Step 4: Only Then Spawn

After preflight passes AND locks acquired → safe to `sessions_spawn`.

---

## 2. Post-Completion Protocol (Mandatory)

### Step 1: Verify No Other Agent Overwrote Your Changes

```bash
# Compare current file with backup
diff /root/psvibe-sales-bot/bot/__init__.py \
     /root/backups/<backup-dir>/bot/__init__.py
```

If DIFF shows unexpected changes (not your own) → **SOMEBODY ELSE MODIFIED THIS FILE** → Report to Boss.

### Step 2: Run Full Validation Suite

```bash
python3 /root/coordination/validate.py
```

This runs:
1. ✅ `py_compile` on ALL .py files
2. ✅ `from bot import *` import test
3. ✅ `systemctl restart` all 3 services
4. ✅ `systemctl is-active` check
5. ✅ Log check for errors (last 50 lines)
6. ✅ API health check: `curl -s http://localhost:8000/health`

**If ANY check fails → AUTO-ROLLBACK:**

```bash
python3 /root/coordination/rollback.py --backup <backup-path>
systemctl restart psvibe-sale-bot.service psvibe_customer_bot.service
systemctl restart psvibe-api.service
```

### Step 3: Release Locks

```bash
python3 /root/coordination/lock_manager.py release --agent <taskname>
```

### Step 4: Update Audit Trail

```bash
python3 /root/coordination/log_completion.py \
  --agent <taskname> \
  --files "bot/handlers/sales.py" \
  --summary "Fixed multi-payment: added PAY_METHOD/PAY_AMOUNT states" \
  --status "completed"
```

---

## 3. Automated Tools (To Be Built)

| Tool | File | Purpose | Priority |
|------|------|---------|----------|
| 🔍 Pre-flight checker | `/root/coordination/preflight.py` | Check locks, services, backups | 🔴 HIGH |
| ✅ Validator | `/root/coordination/validate.py` | Full validation suite | 🔴 HIGH |
| ↩️ Rollback engine | `/root/coordination/rollback.py` | Auto-rollback on failure | 🔴 HIGH |
| 📝 Audit logger | `/root/coordination/log_completion.py` | Log to AGENT_LOCKS.md | 🟡 MEDIUM |
| 🧬 Dependency graph | `/root/coordination/dep_graph.py` | Find what imports what | 🟢 LATER |
| ⏰ Stale lock cleaner | cron job (every 30 min) | Auto-clean locks >30 min old | 🟡 MEDIUM |
| 💾 Batch backup | `preflight.py --backup` | Auto-backup before changes | 🔴 HIGH |

---

## 4. Stale Lock Auto-Cleanup (Cron Job)

```bash
# Every 30 minutes, clean locks older than 30 minutes
*/30 * * * * root python3 /root/coordination/lock_manager.py force-release --older-than 30
```

This prevents:
- Agent crashes leaving dangling locks
- Timeout agents not releasing locks
- Session restarts without cleanup

---

## 5. Conflict Resolution Protocol

### What happens when two agents want the SAME file?

| Situation | Resolution |
|-----------|-----------|
| Agent A holds lock, Agent B wants same file | **Agent B WAITS** — checks back every 2 min |
| Agent A's lock is stale (>30 min) | Cron auto-clears lock, Agent B acquires it |
| Two agents need same file for DIFFERENT fixes | **SEQUENTIAL** — Agent A finishes first, then Agent B |
| Same file, same fix needed | **MERGE** — If fixes are non-overlapping lines, write to different sections |

### Priority Queue:
```
Priority 1: Boss direct request (["Boss asked me to"])
Priority 2: Crash fix (bot is DOWN → urgent)
Priority 3: Audit fix (found bug → should fix)
Priority 4: Refactor / improvement (nice to have)
```

---

## 6. Agent Communication Protocol

### Shared Findings File (v2.1 — Single-Writer System)
**Location:** `/root/coordination/SHARED_FINDINGS.md`
**Merge tool:** `/root/coordination/merge_findings.py`
**Temp findings dir:** `/root/coordination/findings/`

#### Why This Design?
**Problem:** If sub-agents directly write SHARED_FINDINGS.md, they'll overwrite each other (same crash as bot code).

**Solution:** Split into TWO roles:

| Role | What they write | Where | Lock needed? |
|------|----------------|-------|-------------|
| **Sub-agent** | Discovered findings | `findings/<agent_name>.json` (temp file) | ❌ No — each agent writes own file |
| **Kora (only)** | Merges all → updates SHARED_FINDINGS.md | `SHARED_FINDINGS.md` | ✅ Kora = single writer only |

#### 🔴 Golden Rule — NEVER directly write SHARED_FINDINGS.md

Only Kora runs `merge_findings.py`. Sub-agents NEVER write SHARED_FINDINGS.md.

#### Sub-agent Protocol (When you find a bug)

```bash
# 1. Write to temp file (NOT SHARED_FINDINGS.md!)
python3 -c "
import json
entry = {
    'id': 'fix-sales-1',           # unique ID
    'agent': 'fix-sales',           # your agent name
    'severity': '🔴',               # 🔴 🟡 🟢 ⚪
    'file': 'bot/__init__.py',      # file path with issue
    'change': 'missing→Added',      # before → after
    'why': 'Lost in parallel',      # root cause
    'status': 'FIXED'               # FIXED / PENDING
}
json.dump([entry], open('/root/coordination/findings/fix-sales.json', 'w'))
"
```

#### Kora Protocol (After sub-agents complete)

```bash
# 1. Merge all temp findings → update SHARED_FINDINGS.md
python3 /root/coordination/merge_findings.py

# This does:
#   1. Reads all /root/coordination/findings/*.json
#   2. Reads existing SHARED_FINDINGS.md
#   3. UPSERTS — same id = update, new id = append
#   4. Cleans stale entries (files no longer on VPS)
#   5. Writes updated SHARED_FINDINGS.md
#   6. Deletes all temp .json files
```

#### Stale Cleanup (Auto)

`merge_findings.py` checks every entry:
- Does the file path still exist on VPS (`/root/psvibe-sales-bot/<path>`)?
- ❌ No → Remove entry, add to 🗑️ Removed section
- ✅ Yes → Keep entry

#### Viewing the Findings Table

```markdown
| # | Agent | Sev | File | Before → After | Why? | Status |
|---|-------|-----|------|----------------|------|--------|
| 1 | booking | 🔴 | bot/__init__.py | missing→Added | Parallel overwrite | ✅ |
| 2 | booking | 🟡 | bot/handlers/booking_flow.py | sync→async | Blocking in async | ✅ |
```

#### Findings Manager Agent (Dedicated)

**SOP:** `memory/FINDINGS_MANAGER_SOP.md`
**Script:** `/root/coordination/findings_manager.py`

Kora spawns this agent after sub-agents complete. It automatically:
- Scans `findings/*.json` for new entries
- Runs `merge_findings.py` (upsert + stale cleanup)
- Returns structured report to Kora

**Key constraints:** Flash model only, 120s timeout, NEVER writes directly to SHARED_FINDINGS.md

#### Audit Report Template
**Location:** `memory/AUDIT_REPORT_TEMPLATE.md`

Use this template for all new audit reports. Key sections:
- 🔴 Critical | 🟡 High | 🟢 Medium | ⚪ Low (table with Why? column)
- ✅ CLEAN section (verified files)
- 📊 Summary table
- 🔍 Root Cause Analysis paragraph
- Files Modified list

**Agents MUST read SHARED_FINDINGS before modifying any file.**  
**Agents MUST write a finding when they discover something.**

---

## 7. Spawn Decision Tree (v2 — More Precise)

```
NEW TASK REQUESTED
│
├─ 1. CATEGORIZE
│   ├─ READ-ONLY (audit, check, analyze)
│   │   └─ 👉 No locks needed → spawn freely
│   │
│   └─ CODE CHANGE
│       ├─ Which files?
│       │
│       ├─ bot/__init__.py?
│       │   └─ 🔴 MUST be SEQUENTIAL
│       │       ├─ Check: any other agent active? → WAIT
│       │       ├─ Backup: preflight.py --backup
│       │       ├─ Acquire lock
│       │       └─ Spawn (ONE AT A TIME)
│       │
│       ├─ bot/app.py?
│       │   └─ 🔴 MUST be SEQUENTIAL (same as __init__.py)
│       │
│       ├─ Single handler file? (e.g., handlers/sales.py)
│       │   ├─ Check lock: lock_manager.py check --file
│       │   ├─ FREE → acquire → spawn (parallel OK if different file)
│       │   └─ LOCKED → WAIT or re-scope
│       │
│       ├─ Multiple files?
│       │   ├─ ALL in different dirs (e.g., handlers/ + customer_bot/)?
│       │   │   └─ parallel safe (check each individually)
│       │   └─ Any in bot/__init__.py or bot/app.py?
│       │       └─ 🔴 MUST be SEQUENTIAL
│       │
│       ├─ API server? (psvibe_api_server/)
│       │   └─ 🟢 Always parallel safe (isolated codebase)
│       │
│       └─ Customer bot only? (customer_bot/)
│           └─ 🟢 Parallel safe (but check imports from bot/__init__.py)
│
├─ 2. SLOT CHECK
│   ├─ ≤ 3 active → safe to spawn freely
│   ├─ 4 active → CAUTION (at main-agent limit; reserve for critical fixes)
│   ├─ 5+ active → HALT (maxConcurrent=4)
│   │ # (Actual config: maxConcurrent=4, subagents.maxConcurrent=3, maxChildrenPerAgent=2)
│
└─ 3. EXECUTE
    ├─ Backup (preflight.py --backup)
    ├─ Acquire lock (lock_manager.py acquire)
    ├─ Spawn (sessions_spawn)
    ├─ Wait (sessions_yield)
    ├─ Validate (validate.py)
    ├─ Rollback on failure (rollback.py)
    └─ Release lock (lock_manager.py release)
```

---

## 7a. Task Planner Agent (Boss Task → Module Decomposition)

**SOP:** `memory/TASK_PLANNER_SOP.md`
**Script:** `/root/coordination/task_planner.py`

Decomposes Boss's high-level tasks into modular sub-agent units.

**Max Module Size Rules:**
```
┌─────────────┬──────────┐
│ Metric      │ Max      │
├─────────────┼──────────┤
│ Files       │ 3        │
│ Lines       │ 250      │
│ Functions   │ 2        │
│ Timeout     │ 900s     │
│ Dep Depth   │ 3        │
└─────────────┴──────────┘

🔴 Blocking: bot/__init__.py, bot/app.py (NEVER parallel)
```

**Flow:**
```
Boss: "Add topup feature" → Task Planner → M1(init)→M2(app)→M3+M4(par)→M5
                                    ↓
                             Kora executes in order
```

**Key constraints:** Flash model only, 180s max, NEVER modifies code.

## 7b. Dispatch Manager (Audit → Auto-Fix Pipeline)

**SOP:** `memory/DISPATCH_MANAGER_SOP.md`
**Script:** `/root/coordination/dispatch_manager.py`

Bridges audit agents → fix agents. Reads PENDING findings, groups by file, prints spawn commands.

**Flow:**
```
Audit Agent → writes PENDING findings → Dispatch Manager → prints FIX commands → Kora spawns fix agents
```

**Key constraints:** Flash model only, 180s max, NEVER modifies code or spawns directly.

## 7b. Verify Agent (Auto Re-audit After Fix)

**SOP:** `memory/VERIFY_AGENT_SOP.md`
**Script:** `/root/coordination/verify_agent.py`

After every fix agent completes → auto-verify the fix is correct. If PASS → done. If FAIL → re-dispatch.

**The Golden Loop (max 3 retries):**
```
Fix Agent → Verify Agent → PASS? → YES → Done
                            → NO  → Re-Dispatch → Fix Again → Verify Again
```

**Checks:** py_compile ✓ | imports ✓ | services ✓ | logs ✓ | file integrity ✓

**Key constraints:** Flash model only, 300s max, NEVER modifies code.

## 7c. Spawning Manager Agent (Dedicated)

**SOP:** `memory/SPAWNING_MANAGER_SOP.md`
**Script:** `/root/coordination/spawning_manager.py`

Automates the entire spawn pipeline so Kora doesn't do it manually:
```
Preflight → Lock → Backup → Print Spawn Cmd → [Kora spawns] → Validate → Rollback → Release
```

**Key constraints:** Flash model only, 900s max, NEVER modifies code directly, NEVER writes SHARED_FINDINGS.md

---

## 8. Implementation: Pre-Flight Script

**To be created at `/root/coordination/preflight.py`:**

```python
#!/usr/bin/env python3
"""Pre-flight check before spawning a sub-agent.

Usage:
    python3 preflight.py check --agent fix-bug --files "bot/handlers/sales.py"
    python3 preflight.py backup
"""
# Key checks:
# 1. Lock status for target files
# 2. Systemd services health
# 3. Current code compiles (py_compile)
# 4. Bot running and polling
# 5. Backup creation

# Returns: PASS / WARN / FAIL
# If FAIL → blocks spawn, tells Kora why
```

---

## 9. Implementation: Validation Script

**To be created at `/root/coordination/validate.py`:**

```python
#!/usr/bin/env python3
"""Full validation after a sub-agent completes.

Usage:
    python3 validate.py
    python3 validate.py --verbose
    python3 validate.py --quick  # skip restart

Checks:
1. py_compile ALL .py files
2. from bot import * import test
3. Restart all 3 services
4. systemctl is-active (x3)
5. Log check (last 50 lines, no ERROR/Traceback)
6. API health check (curl)
7. Telegram polling check (log grep)

Returns: PASS / FAIL
If FAIL → prints rollback command
"""
```

---

## 10. Implementation: Rollback Script

**To be created at `/root/coordination/rollback.py`:**

```python
#!/usr/bin/env python3
"""Emergency rollback when validation fails.

Usage:
    python3 rollback.py --backup /root/backups/pre-task-20260528_183000.tar.gz

Steps:
1. Stop all 3 services
2. Restore from backup (.tar.gz or individual files)
3. Restart all 3 services
4. Validate again
5. Report result
"""
```

---

## 11. The Golden Commandments (v2.1)

1. **THOU SHALT NOT run parallel on `bot/__init__.py`** — sequential only, forever
2. **THOU SHALT ALWAYS pre-flight check** before spawning any code-changing agent
3. **THOU SHALT ALWAYS backup** before modifying code
4. **THOU SHALT ALWAYS validate + rollback on failure**
5. **THOU SHALT RELEASE locks** when done
6. **THOU SHALT WRITE findings** to `findings/<agent>.json` (NOT SHARED_FINDINGS.md directly)
7. **THOU SHALT NOT write SHARED_FINDINGS.md** — only Kora runs merge_findings.py
8. **THOU SHALT READ SHARED_FINDINGS** before starting any task
9. **THOU SHALT REPORT to Boss** — every spawn, every completion, every rollback
10. **STALE LOCKS** auto-cleaned every 30 min (cron)
11. **STALE FINDINGS** auto-removed by merge_findings.py
12. **WHEN IN DOUBT, GO SEQUENTIAL** — parallel is an optimization, not a default

---

## 12. Quick Reference Card (செய்யရန်/မလုပ်ရန်)

| Action | ✅ Do | ❌ Don't |
|--------|-------|---------|
| Parallel on different handlers | ✅ Different files, both free | ❌ Same file or one is __init__.py |
| Modify __init__.py | ✅ Sequential, backup first | ❌ Parallel with anyone |
| Quick fix (1 file) | ✅ Lock, fix, validate, release | ❌ Skip pre-flight |
| Read-only audit | ✅ Spawn freely | ❌ Waste time with locks |
| During crash (bot DOWN) | ✅ Sequential emergency fix | ❌ Panic and parallel |
| Rollback needed | ✅ `rollback.py --backup X` | ❌ Keep broken state |
| Stale lock found | ✅ Cron auto-cleans | ❌ Manual delete .lock files |
| Found a bug | ✅ Write to `findings/<agent>.json` | ❌ Write directly to SHARED_FINDINGS.md |
| Stale finding | ✅ merge_findings.py auto-removes | ❌ Manual edit of SHARED_FINDINGS.md |

---

_Last updated: 2026-06-02 | v3.1 | Added: Auto-Split Rule (3-min trigger), Live Updates Rule_
