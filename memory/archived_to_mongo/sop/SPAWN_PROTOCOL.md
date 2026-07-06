# Kora Spawn Protocol — Quick Reference

## ⚠️ CRITICAL: Read COORDINATION_FRAMEWORK.md FIRST
**This protocol is the IMPLEMENTATION guide. The COORDINATION_FRAMEWORK.md is the DESIGN document with all the rules.**

**Before ANY spawn → read COORDINATION_FRAMEWORK.md**
**Golden rule: NEVER parallel on bot/__init__.py**

## 🔀 Auto-Split Rule (3-Minute Trigger)

**If a spawned agent runs >3 minutes AND has decomposable work → SPLIT.**

```
subagents list → any running >3min?
  ├─ YES → Check slots_free > 0?
  │   ├─ YES → Split into narrow-scope agents
  │   │         300s timeout per agent
  │   │         Separate temp files per agent
  │   │         Update Boss: "Splitting into N parts"
  │   └─ NO  → Wait for slot to free up
  └─ NO  → Normal spawn flow
```

**See SOUL.md → Auto-Split Long Tasks for full details.**

## Before sessions_spawn

```bash
# Register task (writes to BOTH journal + active_tasks.json)
python3 memory/kora_spawn.py register <taskName> <model> "<goal>"

# Example:
python3 memory/kora_spawn.py register fix-bug-x "deepseek/deepseek-v4-pro" "Fix the MySQL connection timeout bug"
# Output: 1716880000-fix-bug-x  ← save this task-id!
```

## Spawn the Sub-agent

Use `sessions_spawn` tool with the registered task-id in the description.
Always include `runTimeoutSeconds` (default: 7200 = 2 hours).

```python
# In Kora's code:
sessions_spawn(
    taskName="fix-bug-x",
    model="deepseek/deepseek-v4-pro",
    runTimeoutSeconds=7200,  # 2 hours
    task="## Task: Fix MySQL connection timeout bug\n..."
)
```

### 🛡️ SAFETY NET — EVERY spawn MUST include this (prevents "incomplete turn" errors)

**Task description MUST end with:**
```
SAFETY NET: You MUST end your output with '=== RESULT: OK ||| ERROR: <reason> ==='.
If ANYTHING fails, write details to the temp file AND output an error message.
NEVER stop without producing at least one line of final text output.
```

**Why:** If a sub-agent finishes with `payloads=0` (no text output), the
Gateway will surface "Something went wrong" and may restart. Writing to
a temp file + outputting a completion marker prevents this.

**Before every spawn, Kora MUST verify:**
- [ ] Task has SAFETY NET instructions
- [ ] Task writes to `temp/<name>.txt`
- [ ] Task ends with completion marker
- [ ] Output path is unique

## After Completion

```bash
# Mark complete (removes from active_tasks, updates journal)
python3 memory/kora_spawn.py complete <task-id> <status> "<summary>"

# Status values: completed | failed | partial

# Example:
python3 memory/kora_spawn.py complete 1716880000-fix-bug-x completed "Fixed timeout by adding connection retry logic"
```

## Quick Checks

```bash
python3 memory/kora_spawn.py list      # Active tasks detail
python3 memory/subagent_ctl.py status  # Summary counts
python3 memory/subagent_ctl.py orphans # Stuck/orphaned tasks?
python3 memory/subagent_ctl.py summary # Full dashboard
```

## Slot Management & Auto-Helpers

### Current Config Limits
- **maxConcurrent:** 4 (main agents per session)
- **subagents.maxConcurrent:** 3
- **maxChildrenPerAgent:** 2
- **Always keep track** of how many slots are used
- **When slots are free AND active agents are running with work to do** → auto-spawn helpers

### Auto-Helper Rule 🚀
```
While slots_free > 0 AND active_agents_with_tasks > slots_used:
    spawn_helper_for_long_running_task()
```

**When to spawn helpers:**
1. Any agent running >3 minutes with more states to trace → split the work
2. Finance/Payroll flows (50+ states) → split into sub-flows
3. Fix tasks that affect multiple files → spawn separate fix agents per file
4. Audit tasks that read multiple large files → spawn one per file

**Helper spawn pattern:**
- Use same `taskName` convention: `<originalTask>_helper`
- Set SHORTER timeout (300s = 5 min for helpers, not 2h)
- Keep task CONCISE — helpers just need to produce partial output
- Do NOT register helpers in subagent-journal (too noisy for quick helpers)
- Only register MAIN tasks (fixes, long-running audits) in journal

## Error Handling
If a sub-agent fails or errors → **report to Kora automatically**. 
Kora will assess and decide retry vs manual fix.

When a sub-agent FAILS or TIMEOUTS:
1. Check if a retry with same task would help (shorter scope?)
2. If yes, spawn a REPLACEMENT with reduced scope
3. If no, move on and document the gap

## Lock Manager (NEW — 2026-05-28)

**Lock manager is at `/root/coordination/lock_manager.py` on VPS.**

### Before ANY code-modifying spawn:
```bash
# 1. Check if target file is locked
python3 /root/coordination/lock_manager.py check --file "bot/handlers/sales.py"
# → "FREE" = go ahead, "LOCKED by: X" = WAIT

# 2. Acquire lock
python3 /root/coordination/lock_manager.py acquire --agent fix-bug-x --files "bot/handlers/sales.py,bot/__init__.py" --reason "Fix sales flow"
```

### After spawn completes:
```bash
# 3. Release lock
python3 /root/coordination/lock_manager.py release --agent fix-bug-x
```

### Write findings (sub-agent → temp file, NOT direct to SHARED_FINDINGS.md):
```bash
# Sub-agent writes findings to temp file:
python3 -c "import json;e={'id':'fix-1','agent':'fix-bug-x','severity':'🔴','file':'bot/__init__.py','change':'missing→Added','why':'Parallel overwrite','status':'FIXED'};open('/root/coordination/findings/fix-bug-x.json','w').write(json.dumps([e]))"
```

### Kora runs merge (NEVER let sub-agents write SHARED_FINDINGS.md):
```bash
# Only Kora runs this:
python3 /root/coordination/merge_findings.py
```

### 🔴 Files that NEVER allow parallel:
- `bot/__init__.py` — single point of failure
- `bot/app.py` — handler registration
- See COORDINATION_FRAMEWORK.md for full list

## Git Sync Agent (Commit + Push)

**SOP:** `memory/GIT_SYNC_SOP.md`
**Script:** `/root/coordination/git_sync_agent.py` (VPS)

```bash
# After fixes are done and verified → push to GitHub
python3 /root/coordination/git_sync_agent.py full-sync
```

Commands: `status`, `commit`, `push`, `full-sync`

## Status Reporter (Health Reports)

**SOP:** `memory/STATUS_REPORTER_SOP.md`
**Script:** `/root/coordination/status_reporter.py` (VPS)

```bash
# Daily / on-demand health report
python3 /root/coordination/status_reporter.py quick
python3 /root/coordination/status_reporter.py health
python3 /root/coordination/status_reporter.py daily
```

## Deploy Manager (Full Release Deploy)

**SOP:** `memory/DEPLOY_MANAGER_SOP.md`
**Script:** `/root/coordination/deploy_manager.py` (VPS)

Handles full deploys: pre-deploy → backup → stop services → git pull → install → migrations → restart → verify → rollback

```bash
python3 /root/coordination/deploy_manager.py deploy
python3 /root/coordination/deploy_manager.py rollback
```

## Task Planner Agent (Task → Module Decomposition)

**SOP:** `memory/TASK_PLANNER_SOP.md` ⬅️ ALL details
**Script:** `/root/coordination/task_planner.py` (VPS)

Kora gets a task from Boss → Task Planner decomposes into MAX-SIZE modules.

```python
sessions_spawn(
    taskName="plan-task",
    task='python3 /root/coordination/task_planner.py plan --prompt "Add topup feature"',
    runTimeoutSeconds=180,
    model="deepseek/deepseek-v4-flash"
)
# → Output: M1(init)→M2(app)→M3+M4(par)→M5
# → Kora executes sequential + parallel in order
```

**Max Module Size:** files=3 | lines=250 | functions=2 | timeout=900s

## Verify Agent (Auto Re-audit After Fix)

**SOP:** `memory/VERIFY_AGENT_SOP.md` ⬅️ ALL details
**Script:** `/root/coordination/verify_agent.py` (VPS)

After every fix agent completes → auto-verify. This is the **quality gate**.

```python
# After fix agent completes:
sessions_spawn(
    taskName="verify-fix-auth",
    task="""python3 /root/coordination/verify_agent.py verify \
        --agent "fix-auth" \
        --files "customer_bot/api.py"""",
    runTimeoutSeconds=300,
    model="deepseek/deepseek-v4-flash"
)
# → If PASS ✅ → done → Findings Manager
# → If FAIL ❌ → Dispatch Manager → Fix again (max 3 retries)
```

This creates the **Fix → Verify Loop**:
```
Fix Agent → Verify Agent → PASS? → YES → Done
                            → NO  → Re-Dispatch → Fix Again → Verify (max 3x)
```

## Dispatch Manager (Findings → Auto-Fix)

**SOP:** `memory/DISPATCH_MANAGER_SOP.md` ⬅️ ALL details
**Script:** `/root/coordination/dispatch_manager.py` (VPS)

Audit agent finds bugs → writes PENDING findings → Dispatch Manager reads them → prints fix commands.

```python
# After audit: auto-dispatch fixes
sessions_spawn(
    taskName="dispatch",
    task="python3 /root/coordination/dispatch_manager.py --dispatch",
    runTimeoutSeconds=180,
    model="deepseek/deepseek-v4-flash"
)
# → prints sessions_spawn() for each fix group
# → Kora iterates spawn → yield → spawn → yield
```

See `memory/DISPATCH_MANAGER_SOP.md` for full details.

## Spawning Manager Agent (Automated)

**SOP:** `memory/SPAWNING_MANAGER_SOP.md` ⬅️ ALL details here
**Script:** `/root/coordination/spawning_manager.py` (VPS)

Instead of manual preflight→lock→backup→spawn→validate→release,
let Spawning Manager handle it:

```python
# Phase 1: Spawning Manager runs pre-spawn protocol
sessions_spawn(
    taskName="spawn-mgr-fix-auth",
    task='python3 /root/coordination/spawning_manager.py spawn \
        --task-name "fix-auth" \
        --description "Fix API auth" \
        --files "customer_bot/api.py" \
        --model "deepseek/deepseek-v4-pro" \
        --timeout 600',
    runTimeoutSeconds=900,
    model="deepseek/deepseek-v4-flash"
)
# → prints preflight result + spawn instructions

# Phase 2: Kora spawns the actual fix agent
sessions_spawn(
    taskName="fix-auth",
    task="Fix customer_bot/api.py...",
    model="deepseek/deepseek-v4-pro",
    runTimeoutSeconds=600,
)
sessions_yield()

# Phase 3: Spawning Manager runs validation
sessions_spawn(
    taskName="spawn-mgr-validate",
    task='python3 /root/coordination/spawning_manager.py validate \
        --task-name "fix-auth" \
        --backup /root/backups/pre-fix-auth-*.tar.gz',
    runTimeoutSeconds=120,
    model="deepseek/deepseek-v4-flash"
)
```

See `memory/SPAWNING_MANAGER_SOP.md` for full details.

## Spawn Protocol Rules (Mandatory)
### For MAIN Tasks (fixes, long audit, multi-file work):
❌ NEVER call sessions_spawn directly without:
   1. Checking COORDINATION_FRAMEWORK.md
   2. Checking VPS lock manager for target files
   3. Acquiring locks via lock_manager.py
❌ NEVER forget to release locks
✅ ALWAYS register (kora_spawn.py) before spawn
✅ ALWAYS complete (kora_spawn.py) after spawn finishes
✅ ALWAYS set runTimeoutSeconds explicitly
✅ For findings merge, use findings-manager agent (120s timeout, Flash model OK)

### For QUICK Helpers (<5 min expected runtime):
✅ Direct spawn allowed (no registration needed)
✅ Use shorter timeout (300s)
✅ Keep scope narrow — one file or one flow per helper
✅ MUST still check lock manager if modifying code
✅ Delete temp/helper output when no longer needed

## Findings Manager Agent (Dedicated Helper)

**SOP:** `memory/FINDINGS_MANAGER_SOP.md` ⬅️ ALL details here
**Script:** `/root/coordination/findings_manager.py` (VPS)
**Report template:** `memory/AUDIT_REPORT_TEMPLATE.md`

### Quick Reference:
```python
# After sub-agents complete → spawn findings manager:
sessions_spawn(
    taskName="findings-merge",
    task="Run python3 /root/coordination/findings_manager.py",
    runTimeoutSeconds=120,
    model="deepseek/deepseek-v4-flash"
)
```

### What it does:
1. Reads `findings/<agent>.json` temp files
2. Runs `merge_findings.py` (upsert + stale cleanup)
3. Prints structured report → Kora reports to Boss

### 3 Golden Rules:
1. ❌ NEVER write SHARED_FINDINGS.md directly
2. ❌ NEVER modify bot code
3. ❌ NEVER spawn sub-agents

See `memory/FINDINGS_MANAGER_SOP.md` for full SOP, boundaries, edge cases.

## Status Values
- `running` — Just spawned
- `completed` — Done successfully
- `partial` — Partially done (needs follow-up)
- `failed` — Failed, needs retry
- `timeout` — Ran out of time
