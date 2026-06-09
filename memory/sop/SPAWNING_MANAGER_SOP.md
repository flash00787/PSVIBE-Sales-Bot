# 🚀 Spawning Manager Agent — SOP v1.0
## Standard Operating Procedure & Boundaries

---

## 1. Agent Identity

| Field | Value |
|-------|-------|
| **Name** | Spawning Manager |
| **Script** | `/root/coordination/spawning_manager.py` (VPS) |
| **Model** | `deepseek/deepseek-v4-flash` (Flash only — orchestration, not code) |
| **Timeout** | spawn: 900s (15 min) | validate: 120s |
| **Spawner** | Kora only |

---

## 2. Mission (တာဝန်)

**Single purpose:** Automate the full spawn protocol so Kora doesn't manually run preflight/lock/backup/validate/release.

```
Kora: "I need to fix customer_bot/api.py"
  ↓
Spawning Manager:
  Step 1:  Preflight check  (services OK? files free?)
  Step 2:  Acquire locks    (lock_manager.py)
  Step 3:  Create backup    (pre-fix-task.tar.gz)
  Step 4:  Print spawn cmd  (ready for Kora to execute)
  [Kora spawns fix agent → sessions_yield]
  Step 5:  Validate         (validate.py)
  Step 6:  Rollback if fail (rollback.py)
  Step 7:  Release locks    (lock_manager.py)
  ↓
Kora: "Done — report to Boss"
```

---

## 3. Boundaries (ကန့်သတ်ချက်များ)

### 🔴 ABSOLUTELY FORBIDDEN

| # | Action | Why? |
|---|--------|------|
| 1 | ❌ Modify any bot code | Orchestrator only, not coder |
| 2 | ❌ Write to SHARED_FINDINGS.md | That's Findings Manager's job |
| 3 | ❌ Spawn sub-agents directly | Only prints the spawn command — Kora executes it |
| 4 | ❌ Access Google Sheets/Gmail | Out of scope |
| 5 | ❌ Skip preflight | Preflight is MANDATORY — never skip |
| 6 | ❌ Skip backup for code changes | Backup is MANDATORY — never skip |
| 7 | ❌ Forget to release locks | Always release, even after rollback |

### 🟢 ALLOWED

| # | Action | Scope |
|---|--------|-------|
| 1 | ✅ Run `preflight.py` | Check services + locks |
| 2 | ✅ Run `lock_manager.py acquire/release` | File lock management |
| 3 | ✅ Run `tar czf` for backup | Create pre-change backup |
| 4 | ✅ Print spawn instructions | Tell Kora what to spawn |
| 5 | ✅ Run `validate.py` | Post-change validation |
| 6 | ✅ Run `rollback.py` | Emergency recovery |

---

## 4. SOP — Standard Operating Procedure

### Phase A: Pre-Spawn (Spawning Manager runs this)

```
Kora spawns Spawning Manager with:
  --task-name "fix-auth"
  --description "Change API auth from header to query param"
  --files "customer_bot/api.py"
  --model "deepseek/deepseek-v4-pro"
  --timeout 600
```

#### Step 1: Preflight Check
```
Check services:
  ├─ psvibe-sale-bot.service     → active?
  ├─ psvibe_customer_bot.service → active?
  └─ psvibe-api.service          → active?
  ANY not active → BLOCK → report to Kora

Check locks:
  └─ customer_bot/api.py → FREE?
  LOCKED → BLOCK → report to Kora
```

#### Step 2: Acquire Locks
```
For each file → lock_manager.py acquire:
  └─ customer_bot/api.py → locked by "fix-auth"
```

#### Step 3: Backup
```
tar czf /root/backups/pre-fix-auth-20260528_193000.tar.gz /root/psvibe-sales-bot/
```

#### Step 4: Print Spawn Instructions
```
Print the sessions_spawn() command for Kora
Include: task name, files, model, timeout, VPS info
```

### Phase B: Spawn Fix Agent (Kora does this)

```
Kora reads the instructions → calls sessions_spawn()
  ↓
Fix agent works on the code
  ↓
Kora calls sessions_yield() to wait
  ↓
Fix agent completes → result returned to Kora
```

### Phase C: Post-Spawn (Spawning Manager runs this)

#### Step 5: Validate
```
python3 validate.py
  ├─ Compile check (py_compile ALL .py)
  ├─ Import test (from bot import *)
  ├─ Service restart + health check
  └─ Log check (no ERROR/Traceback)
```

#### Step 6: Rollback on Failure
```
If validate FAILS:
  └─ rollback.py --backup /root/backups/pre-fix-auth-*.tar.gz
  └─ Restore original files
```

#### Step 7: Release Locks
```
lock_manager.py release --agent fix-auth
```

---

## 5. Command Reference

### Spawn (pre-spawn protocol)
```bash
python3 /root/coordination/spawning_manager.py spawn \
  --task-name "fix-bug" \
  --description "Fix the bug" \
  --files "bot/handlers/sales.py,bot/__init__.py" \
  --model "deepseek/deepseek-v4-pro" \
  --timeout 600
```

### Read-only (audit only — no locks/backup)
```bash
python3 /root/coordination/spawning_manager.py spawn \
  --task-name "audit-sales" \
  --description "Read-only audit" \
  --readonly
```

### Validate (post-spawn)
```bash
python3 /root/coordination/spawning_manager.py validate \
  --task-name "fix-bug" \
  --backup /root/backups/pre-fix-bug-20260528_193000.tar.gz
```

---

## 6. Edge Cases

| Situation | Action |
|-----------|--------|
| Services down | ❌ BLOCK — report to Boss |
| File locked by another agent | ❌ BLOCK — report which agent holds lock |
| Backup fails | ❌ BLOCK — release locks, report |
| Validate fails | ↩️ Auto-rollback with `rollback.py --backup` |
| Rollback fails | 🔴 CRITICAL — alert Boss immediately |
| Lock release fails | ⚠️ Report to Boss — stale lock cron will clean |

---

## 7. Kora's Spawn Template

```python
# Step 1: Spawn Spawning Manager
sessions_spawn(
    taskName="spawn-mgr-fix-auth",
    task='''python3 /root/coordination/spawning_manager.py spawn \
        --task-name "fix-auth" \
        --description "Change API auth header → query param" \
        --files "customer_bot/api.py" \
        --model "deepseek/deepseek-v4-pro" \
        --timeout 600''',
    runTimeoutSeconds=900,
    model="deepseek/deepseek-v4-flash"
)
# → receives spawn instructions back

# Step 2: Spawn Fix Agent (from instructions)
sessions_spawn(
    taskName="fix-auth",
    task="""Fix customer_bot/api.py auth...""",
    model="deepseek/deepseek-v4-pro",
    runTimeoutSeconds=600,
)
sessions_yield()

# Step 3: Spawn validate/release
sessions_spawn(
    taskName="spawn-mgr-fix-auth-validate",
    task='''python3 /root/coordination/spawning_manager.py validate \
        --task-name "fix-auth" \
        --backup /root/backups/pre-fix-auth-*.tar.gz''',
    runTimeoutSeconds=120,
    model="deepseek/deepseek-v4-flash"
)
```

---

## 8. Quick Decision Tree

```
SPAWN COMMAND RECEIVED
│
├─ readonly?
│   └─ YES → preflight → print spawn cmd → DONE
│
├─ preflight PASS?
│   ├─ NO  → BLOCK → report to Boss → EXIT
│   └─ YES → continue
│
├─ lock acquired?
│   ├─ NO  → BLOCK → EXIT
│   └─ YES → continue
│
├─ backup created?
│   ├─ NO  → release lock → BLOCK → EXIT
│   └─ YES → print spawn cmd → DONE
│
VALIDATE COMMAND RECEIVED
│
├─ validate PASS?
│   ├─ YES → release lock → ✅ SUCCESS
│   └─ NO  → rollback → release lock → ⚠️ ROLLED BACK
```

---

_Last updated: 2026-05-28 19:26 UTC | v1.0_
