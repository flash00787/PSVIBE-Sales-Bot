# 🛡️ Helper Agents — Master ALLOW / DON'T ALLOW Guidelines v1.0
## တိကျသော ခွင့်ပြုချက်များနှင့် တားမြစ်ချက်များ

---

## 1. ALL Helpers — Universal Rules (အားလုံးလိုက်နာရမည့် စည်းကမ်းများ)

### 🔴 EVERY HELPER — NEVER DO (ဘယ် Helper မှ မလုပ်ရ)

| # | Action | Penalty |
|---|--------|---------|
| 1 | ❌ Modify bot code directly | Immediate shut down |
| 2 | ❌ Spawn another sub-agent | Only Kora spawns |
| 3 | ❌ Write to SHARED_FINDINGS.md | Single-writer = Findings Manager only |
| 4 | ❌ Access Gmail/Google Sheets/Drive | Kora only |
| 5 | ❌ SSH to other servers | VPS-local only |
| 6 | ❌ Restart services without Kora approval | Code changes only |
| 7 | ❌ Run as Pro model | All helpers = Flash only |

### 📖 BEFORE WORK — READ PROJECT DOCS FIRST

When starting a new task about a project (PS VIBE, API, Bot, etc.), **if you don't remember the full context**:

1. First, **memory_search** the topic in the workspace memory
2. Then **read the relevant project docs** before starting work:
   - `PROJECT_STRUCTURE.md` — Project layout & architecture
   - `API_ENDPOINTS.md` — API endpoint reference
   - `DB_SCHEMA.md` — Database table schemas
   - `memory/psvibe-code-structure.md` — File-by-file code reference
   - `memory/project-state.md` — Current state & known issues
   - `memory/infrastructure.md` — Services, tools, config
3. Read the relevant SOP files in `memory/sop/`
4. **Only start the task after you have full context**

> ⚠️ **Why:** Each session is fresh — no memory of prior conversations.
> Reading docs first prevents mistakes, duplicate work, and wrong assumptions.

### 🟢 EVERY HELPER — FREE TO DO

| # | Action | Scope |
|---|--------|-------|
| 1 | ✅ Read files on VPS | `/root/psvibe-sales-bot/`, `/root/coordination/` |
| 2 | ✅ Run shell commands | Within their SOP scope |
| 3 | ✅ Write to own temp files | `findings/*.json`, `plans/*.json`, `.locks/*` |
| 4 | ✅ Print structured reports to stdout | Report back to Kora |
| 5 | ✅ Check `systemctl` status | Read-only service checks |

---

## 2. 📐 Task Planner Agent

**Script:** `/root/coordination/task_planner.py`
**Model:** Flash | **Timeout:** 180s

### ✅ ALLOW
| # | Action | Detail |
|---|--------|--------|
| 1 | Analyze Boss's task prompt | Extract keywords → map to files |
| 2 | Run `find` on VPS | Discover relevant .py files |
| 3 | Compute dependencies | Based on built-in DEPS_MAP |
| 4 | Split into max-size modules | Max 3 files / 250 lines / 2 functions |
| 5 | Print spawn commands | Sessions_spawn() templates for Kora |
| 6 | Write `plans/*.json` | Save execution plan for reference |

### ❌ DON'T ALLOW
| # | Action | Why? |
|---|--------|------|
| 1 | Read/execute any plan | Planning only, not execution |
| 2 | Write to findings/ | That's for audit/fix agents |
| 3 | Run merge_findings.py | Findings Manager's job |
| 4 | Modify bot code | Not a fix agent |
| 5 | Check bot logs | Verify Agent's job |
| 6 | Restart services | Not a deploy agent |

---

## 3. 🔍 Verify Agent

**Script:** `/root/coordination/verify_agent.py`
**Model:** Flash | **Timeout:** 300s

### ✅ ALLOW
| # | Action | Detail |
|---|--------|--------|
| 1 | Run `py_compile` on files | Syntax check |
| 2 | Run import test | `from bot import *` (with env vars) |
| 3 | Check `systemctl is-active` | Service health |
| 4 | Read `journalctl -n 30` | Error log check |
| 5 | Check file existence + size | `os.path.exists`, `os.path.getsize` |
| 6 | Check for duplicate `global` | Bug pattern scan |
| 7 | Write `findings/v_<agent>.json` | VERIFIED or PENDING status |
| 8 | Run `verify` and `scan` commands | Two subcommands |

### ❌ DON'T ALLOW
| # | Action | Why? |
|---|--------|------|
| 1 | Fix any code bug found | Verify only — never modify |
| 2 | Modify findings from other agents | Own findings only (v_ prefix) |
| 3 | Write to SHARED_FINDINGS.md | Findings Manager's job |
| 4 | Spawn fix agents | Only writes PENDING for Dispatch |
| 5 | Check Google Sheets data | Out of scope |
| 6 | Run `merge_findings.py` | Findings Manager's job |
| 7 | Modify verify results after writing | One write per agent run |

---

## 4. 🚀 Spawning Manager

**Script:** `/root/coordination/spawning_manager.py`
**Model:** Flash | **Timeout:** 900s

### ✅ ALLOW
| # | Action | Detail |
|---|--------|--------|
| 1 | Run `preflight.py` | Services + compile + imports check |
| 2 | Check/create `.locks/` files | Lock management |
| 3 | Create backup with `tar` | `backups/psvibe-<date>.tar.gz` |
| 4 | Run `validate.py` | Post-change validation |
| 5 | Run `rollback.py` | On validation failure |
| 6 | Release locks | Delete `.lock` files |
| 7 | Print spawn command for Kora | One sessions_spawn() template |
| 8 | Run subcommands: `preflight`, `spawn`, `validate`, `release` | |

### ❌ DON'T ALLOW
| # | Action | Why? |
|---|--------|------|
| 1 | Modify bot code | Spawning Manager = mechanical only |
| 2 | Decide what to fix | Kora decides — Spawning Manager just prepares |
| 3 | Spawn the actual fix agent | Kora spawns, Spawning Manager only prints |
| 4 | Write to SHARED_FINDINGS.md | Findings Manager's job |
| 5 | Run `merge_findings.py` | Not a findings agent |
| 6 | Fix lock conflicts autonomously | Report to Kora instead |
| 7 | Modify service files | Too dangerous |

---

## 5. 🎯 Dispatch Manager

**Script:** `/root/coordination/dispatch_manager.py`
**Model:** Flash | **Timeout:** 180s

### ✅ ALLOW
| # | Action | Detail |
|---|--------|--------|
| 1 | Read `findings/*.json` | Check PENDING status |
| 2 | Read `SHARED_FINDINGS.md` | Check for 🔧 pending entries |
| 3 | Group findings by file | Logical fix batching |
| 4 | Print spawn commands | One sessions_spawn() per fix group |
| 5 | Write `dispatch_plan.json` | Reference plan for Kora |
| 6 | Run `--dispatch` and `--status` | Two modes |

### ❌ DON'T ALLOW
| # | Action | Why? |
|---|--------|------|
| 1 | Modify bot code | Dispatch only — never fix |
| 2 | Spawn fix agents | Only prints commands for Kora |
| 3 | Write to SHARED_FINDINGS.md | Findings Manager's job |
| 4 | Run `verify_agent.py` | Verify Agent's job |
| 5 | Modify findings/ files | Read-only consumer |
| 6 | Run `preflight/validate/rollback` | Spawning Manager's job |
| 7 | Access Gmail/Sheets/Drive | Out of scope |

---

## 6. 📋 Findings Manager

**Script:** `/root/coordination/findings_manager.py`
**Model:** Flash | **Timeout:** 120s

### ✅ ALLOW
| # | Action | Detail |
|---|--------|--------|
| 1 | Read `findings/*.json` | Read all temp findings |
| 2 | Read `SHARED_FINDINGS.md` | Read existing entries |
| 3 | Run `merge_findings.py` | THE ONLY writer to SHARED_FINDINGS.md |
| 4 | Check file existence on VPS | For stale cleanup |
| 5 | Delete temp `findings/*.json` | After successful merge |
| 6 | Remove stale SHARED_FINDINGS.md entries | For files that no longer exist |
| 7 | Print structured merge report | What was added/removed/updated |

### ❌ DON'T ALLOW
| # | Action | Why? |
|---|--------|------|
| 1 | Write to SHARED_FINDINGS.md directly | Only via merge_findings.py |
| 2 | Modify bot code | Not a fix agent |
| 3 | Spawn sub-agents | Leaf-level only |
| 4 | Run `verify_agent.py` | Verify Agent's job |
| 5 | Run `preflight/validate/rollback` | Spawning Manager's job |
| 6 | Restart services | Not a deploy agent |
| 7 | Modify findings/ before merge | Read-then-delete only |

---

## 7. Summary Matrix

```
┌─────────────────────┬─────┬─────┬─────┬─────┬─────┐
│                     │Task │Vrfy │Spwn │Dspch│Fndng│
│                     │Plan │     │Mgr  │Mgr  │Mgr  │
├─────────────────────┼─────┼─────┼─────┼─────┼─────┤
│ Read findings/*.json│ ❌  │ ✅  │ ❌  │ ✅  │ ✅  │
│ Read SHARED_FINDINGS│ ❌  │ ❌  │ ❌  │ ✅  │ ✅  │
│ Write to SHARED     │ ❌  │ ❌  │ ❌  │ ❌  │ ✅* │
│ Modify bot code     │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │
│ Spawn sub-agents    │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │
│ Run preflight/rollbk│ ❌  │ ❌  │ ✅  │ ❌  │ ❌  │
│ Check compile/import│ ❌  │ ✅  │ ✅  │ ❌  │ ❌  │
│ Check services      │ ❌  │ ✅  │ ✅  │ ❌  │ ❌  │
│ Write own temp files│ ✅  │ ✅  │ ✅  │ ✅  │ ✅  │
│ Print spawn cmd     │ ✅  │ ❌  │ ✅  │ ✅  │ ❌  │
│ Run Gmail/Sheets    │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │
│ Access external APIs│ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │
└─────────────────────┴─────┴─────┴─────┴─────┴─────┘

✅* = Only via merge_findings.py (NOT direct write)
```

---

## fix_lock.py — Fix Agent Lock System

**Location:** `/root/coordination/fix_lock.py`

Prevents parallel fix agent conflicts. ALL fix agents MUST use this.

| Command | Purpose |
|---------|---------|
| `python3 /root/coordination/fix_lock.py acquire` | Lock before editing |
| `python3 /root/coordination/fix_lock.py release` | Unlock after edit |
| `python3 /root/coordination/fix_lock.py status` | Check lock holder |
| `python3 /root/coordination/fix_lock.py check` | Check if locked (exit 1) |
| `python3 /root/coordination/fix_lock.py clear` | Clear stale lock (10min timeout) |

**Rules:**
- NEVER spawn parallel fix agents — always sequential via sessions_yield
- EVERY fix agent prompt must include acquire/release
- Stale lock auto-clears after 10 minutes

---

## 8. Kora's Helper Decision Tree

```
Boss က task ပေးလိုက်တယ်
  │
  ▼
ဘာ Helper လိုလဲ?
  │
  ├─ Task ကို module ခွဲဖို့? → Task Planner 📐
  │
  ├─ Findings တွေ dispatch လုပ်ဖို့? → Dispatch Manager 🎯
  │
  ├─ Fix agent ပြီးလို့ verify လုပ်ဖို့? → Verify Agent 🔍
  │
  ├─ Preflight → Lock → Backup လုပ်ဖို့? → Spawning Manager 🚀
  │
  ├─ Findings တွေ merge လုပ်ဖို့? → Findings Manager 📋
  │
  └─ ဒါတွေနဲ့မလုံလောက်ဘူး → Kora ကိုယ်တိုင် လုပ်
```

---

## 7. New Helpers (v1.0 — Added 2026-05-28)

### 🔄 Git Sync Agent

**Script:** `/root/coordination/git_sync_agent.py`
**Model:** Flash | **Timeout:** 120s

### ✅ ALLOW
| # | Action | Detail |
|---|--------|--------|
| 1 | `git status` / `git diff --stat` | Check working tree |
| 2 | `git add -A` + `git commit` | Auto commit |
| 3 | `git push origin main` | Push to GitHub |
| 4 | `git merge --abort` | On conflict detection |
| 5 | `full-sync` | Status → commit → push |

### ❌ DON'T ALLOW
| # | Action | Why? |
|---|--------|------|
| 1 | Modify bot code | Sync only |
| 2 | `git push --force` | Destructive |
| 3 | Push without commit | Data integrity |
| 4 | Write to SHARED_FINDINGS.md | Not Findings Manager |
| 5 | Check services | Status Reporter's job |

---

### 📊 Status Reporter

**Script:** `/root/coordination/status_reporter.py`
**Model:** Flash | **Timeout:** 120s

### ✅ ALLOW
| # | Action | Detail |
|---|--------|--------|
| 1 | Check services | `systemctl is-active` all 3 |
| 2 | Read logs | `journalctl -n 20 \| grep error` |
| 3 | Check disk/memory | `df -h`, `free -h`, `uptime` |
| 4 | Read SHARED_FINDINGS.md + findings/ | Pending count |
| 5 | Check git log | Recent commits |
| 6 | Check backup dir | Latest backup timestamp |
| 7 | py_compile check | Syntax test |

### ❌ DON'T ALLOW
| # | Action | Why? |
|---|--------|------|
| 1 | Modify bot code | Read-only |
| 2 | Restart services | Monitor only |
| 3 | Git push/commit | Git Sync's job |
| 4 | Write to SHARED_FINDINGS.md | Not Findings Manager |
| 5 | Spawn sub-agents | Leaf-level |

---

### 🎬 Deploy Manager

**Script:** `/root/coordination/deploy_manager.py`
**Model:** Flash | **Timeout:** 300s

### ✅ ALLOW
| # | Action | Detail |
|---|--------|--------|
| 1 | Stop/start services | Dependency-safe order |
| 2 | `git pull` + `pip install` | Code + deps update |
| 3 | Create/restore backups | `tar.gz` backup |
| 4 | Run migrations | `.sql` / `.py` in migrations/ |
| 5 | Verify services | Post-deploy health check |

### ❌ DON'T ALLOW
| # | Action | Why? |
|---|--------|------|
| 1 | Modify bot code directly | Only via git pull |
| 2 | Deploy without pre-deploy checks | Safety violation |
| 3 | Skip backup | Always backup first |
| 4 | `git push --force` | Destructive |
| 5 | Deploy without Kora approval | Boss must approve |

---

## 8. Summary Matrix (All 8 Helpers)

```
┌─────────────────────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│                     │T.Pln│Vrfy │Spwn │Dspch│Fndng│Git  │Stat │Depl │
├─────────────────────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
│ Modify bot code     │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │
│ Spawn sub-agents    │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │
│ Write SHARED_FINDINGS│ ❌  │ ❌  │ ❌  │ ❌  │ ✅* │ ❌  │ ❌  │ ❌  │
│ Run preflight/rollbk│ ❌  │ ❌  │ ✅  │ ❌  │ ❌  │ ❌  │ ❌  │ ✅  │
│ Check compile/import│ ❌  │ ✅  │ ✅  │ ❌  │ ❌  │ ❌  │ ✅  │ ✅  │
│ Check services      │ ❌  │ ✅  │ ✅  │ ❌  │ ❌  │ ❌  │ ✅  │ ✅  │
│ Git push            │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │ ✅  │ ❌  │ ❌  │
│ Stop/start services │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │ ✅  │
│ Print spawn cmd     │ ✅  │ ❌  │ ✅  │ ✅  │ ❌  │ ❌  │ ❌  │ ❌  │
│ Write own temp files│ ✅  │ ✅  │ ✅  │ ✅  │ ✅  │ ❌  │ ❌  │ ❌  │
│ Gmail/Sheets/APIs   │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │ ❌  │
└─────────────────────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

✅* = Only via merge_findings.py (NOT direct write)
```

## 9. Audit Trail

Every helper action is logged:
- **Findings files:** `findings/*.json` (who wrote what, when)
- **Lock files:** `.locks/*.lock` (who holds, since when)
- **Backup files:** `backups/` (when created, by which helper)
- **Plan files:** `plans/*.json` (what task, what modules, when)
- **Stale cleanup:** cron log at `/root/coordination/stale_cleanup.log`

---

## 10. 🚀 Parallel Agent Rules (v2 — Boss Approved 2026-05-29)

### Allowed
- Different handler files, same project ✅
- Different projects (bot/ + api_server/ + coord/) ✅
- Different layers (handler + API endpoint) ✅
- Read-only + Fix agent at same time ✅

### Blocked
- Same exact file ❌
- bot/__init__.py or bot/app.py ❌
- Any file in SINGLE_THREADED_FILES list ❌

### Protocol (MANDATORY before spawning)
```bash
# Pre-spawn check
python3 /root/coordination/fix_lock.py check <name> --files <file1.py,file2.py>
# Exit 0 = safe, Exit 1 = conflict (must wait)

# Acquire lock
python3 /root/coordination/fix_lock.py acquire <name> --files <file1.py,file2.py>

# After fix complete
python3 /root/coordination/fix_lock.py release <name>

# Run quality gate after ALL parallel agents done
python3 /root/coordination/quality_gate.py --quick
```

### Max Parallel
- Max 4 simultaneous fix agents (leaves 1 slot for Boss/Kora)
- Max spawn queue reached → wait for release

---

_Last updated: 2026-05-29 18:55 UTC | v2.0 (Parallel Agent Support)_
