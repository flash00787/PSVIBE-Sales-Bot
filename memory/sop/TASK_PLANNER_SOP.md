# 📐 Task Planner Agent — SOP v1.0
## Standard Operating Procedure & Boundaries

---

## 1. Agent Identity

| Field | Value |
|-------|-------|
| **Name** | Task Planner Agent |
| **Script** | `/root/coordination/task_planner.py` (VPS) |
| **Model** | `deepseek/deepseek-v4-flash` (Flash only — planning, not code) |
| **Timeout** | 180 seconds max |
| **Spawner** | Kora only |

---

## 2. Mission (တာဝန်)

**Single purpose:** Decompose Boss's high-level tasks into modular sub-agent units that fit within MAX SIZE limits.

```
Boss: "ဒီဟာကို လုပ်ပါ"
  │
  ▼
Task Planner Agent:
  1. Analyze task → infer relevant files
  2. Apply MAX SIZE rules → split into modules
  3. Compute dependencies between modules
  4. Determine execution order (sequential + parallel)
  5. Print spawn commands for each module
  6. Save detailed plan to plans/ directory
  │
  ▼
Kora: reads plan → spawns in correct order → yield → spawn → yield
```

---

## 3. MAX MODULE SIZE RULES (မချိုးဖောက်ရ)

```
┌─────────────┬──────────┬────────────────────────┐
│ Metric      │ Max      │ Why?                   │
├─────────────┼──────────┼────────────────────────┤
│ Files       │ 3        │ Sub-agent focus limit  │
│ Lines       │ 250      │ Generation quality cap │
│ Functions   │ 2        │ Single responsibility  │
│ Timeout     │ 900s     │ Cost & slot management │
│ Dep Depth   │ 3        │ Cascade risk control   │
└─────────────┴──────────┴────────────────────────┘
```

### 🔴 BLOCKING FILES (NEVER MODIFY IN PARALLEL)

| File | Why? |
|------|------|
| `bot/__init__.py` | 100% blast radius — everything imports from it |
| `bot/app.py` | Router — all handlers register here |

### ⚠️ SEPARATION RULES (NEVER IN SAME MODULE)

| Rule | Why? |
|------|------|
| `__init__.py` + `app.py` | Both blocking — each gets own module |
| `__init__.py` + `customer_bot/` | Too many cascading changes |
| `api_client.py` + `customer_bot/` | Dependency inversion risk |

### 🟢 PARALLEL OK (SAME DEP LEVEL, NO CONFLICTS)
- Independent files (no shared imports)
- Same dependency level (waiting for same thing)
- No blocking file involvement
- Not in separation rules list

### 🔴 SEQUENTIAL ONLY
- Blocking files (`__init__.py`, `app.py`)
- Files with shared dependencies
- Cascade-risk changes

---

## 4. Boundaries

### 🔴 ABSOLUTELY FORBIDDEN

| # | Action | Why? |
|---|--------|------|
| 1 | ❌ Modify bot code | Planner only — never fix |
| 2 | ❌ Spawn sub-agents | Kora spawns; Planner only prints commands |
| 3 | ❌ Write to SHARED_FINDINGS.md | Findings Manager's job |
| 4 | ❌ Run code/verify/merge | Planning only |
| 5 | ❌ Access Gmail/Sheets/APIs | Out of scope |

### 🟢 ALLOWED

| # | Action | Scope |
|---|--------|-------|
| 1 | ✅ Read file list on VPS | `os.path.exists` check |
| 2 | ✅ Run `find` command | File discovery |
| 3 | ✅ Generate execution plan | JSON + print |
| 4 | ✅ Write `plans/*.json` | Save plan for reference |

---

## 5. SOP — အဆင့်ဆင့်

### Step 1: Kora spawns after getting task from Boss

```python
sessions_spawn(
    taskName="plan-fix-task",
    task="python3 /root/coordination/task_planner.py plan --prompt \"Add topup feature\"",
    runTimeoutSeconds=180,
    model="deepseek/deepseek-v4-flash"
)
```

### Step 2: Task Planner analyzes

```
Input: "Add topup feature with wallet, payment, admin"

Step 1: File Discovery
  ├─ keyword "topup" → bot/payment.py, bot/handlers/admin.py
  ├─ keyword "wallet" → bot/wallet.py
  ├─ keyword "payment" → bot/payment.py
  ├─ keyword "member" → bot/handlers/member.py
  └─ always + bot/__init__.py, bot/app.py

Step 2: Apply Max Size Rules
  ├─ 6 files found → 5 modules after splitting
  ├─ __init__.py → M1 (blocking, sequential)
  ├─ app.py → M2 (blocking, depends on M1)
  ├─ payment.py + wallet.py → M3/M4 (parallel OK)
  └─ admin.py → M5 (depends on M1 + M2)

Step 3: Execution Order
  └─ M1 → M2 → M3+M4 → M5
```

### Step 3: Output spawn commands

```
M1 (__init__.py) → sessions_spawn(taskName="fix-init", ...)
M2 (app.py) → sessions_spawn(taskName="fix-app", ...) [wait M1]
M3 + M4 (payment, wallet) → PARALLEL: sessions_spawn both! 
M5 (admin.py) → sessions_spawn(taskName="fix-admin", ...) [wait M1+M2]
```

### Step 4: Kora executes

```python
# Sequential: M1 first
sessions_spawn(taskName="fix-init", ...)
sessions_yield()

# M2 second (depends on M1)
sessions_spawn(taskName="fix-app", ...)
sessions_yield()

# Parallel: M3 + M4 (same dep level)
sessions_spawn(taskName="fix-payment", ...)
sessions_spawn(taskName="fix-wallet", ...)
sessions_yield()

# M5 last (depends on M1 + M2)
sessions_spawn(taskName="fix-handler", ...)
sessions_yield()
```

---

## 6. Knowledge Base — File Patterns

### Keyword → File Mapping

| Keyword | Files |
|---------|-------|
| `payment`, `topup` | `bot/payment.py`, `bot/__init__.py` |
| `booking` | `bot/handlers/booking.py`, `bot/admin_bookings.py` |
| `customer` | `customer_bot/`, `customer_bot/api.py` |
| `auth` | `bot/staff.py`, `customer_bot/api.py` |
| `member`, `wallet` | `bot/handlers/member.py`, `bot/wallet.py` |
| `referral` | `bot/handlers/referral.py` |
| `report` | `bot/report_generator.py`, `api/` |
| `database`, `db` | `bot/db.py`, `bot/config.py` |
| `api` (general) | `api/`, `bot/api_client.py` |
| `deploy` | `deploy/`, `docker-compose.yml` |

### Dependency Map

```
bot/api_client.py      → (none)
bot/config.py           → (none)
bot/db.py              → bot/config.py
bot/staff.py           → bot/api_client.py
bot/payment.py         → bot/staff.py, bot/db.py
bot/handlers/          → bot/__init__.py, bot/app.py
bot/__init__.py        → bot/api_client.py, bot/config.py
bot/app.py             → bot/__init__.py
customer_bot/api.py    → (none)
customer_bot/handlers/ → customer_bot/api.py
api/                   → bot/api_client.py, bot/db.py
```

---

## 7. Quick Reference

```bash
# Plan a task
python3 /root/coordination/task_planner.py plan --prompt "Fix booking bug in Sales Bot"

# With specific files
python3 /root/coordination/task_planner.py plan --prompt "Fix auth" --files "bot/staff.py,customer_bot/api.py"

# List saved plans
python3 /root/coordination/task_planner.py list

# View a saved plan
python3 /root/coordination/task_planner.py show --plan /root/coordination/plans/plan_xxx.json

# Show rules
python3 /root/coordination/task_planner.py rules
```

---

## 8. Kora's Full Workflow Template

```python
# === TASK PLANNER → EXECUTE WORKFLOW ===

# Step 1: Plan the task
sessions_spawn(
    taskName="plan-task",
    task='python3 /root/coordination/task_planner.py plan --prompt "Add feature X"',
    runTimeoutSeconds=180,
    model="deepseek/deepseek-v4-flash"
)
# ← Kora reads plan, sees: M1 (init) → M2 (app) → M3+M4 (parallel)

# Step 2: Execute M1 (blocking)
sessions_spawn(taskName="fix-m1", task="Modify bot/__init__.py for feature X", model="deepseek/deepseek-v4-pro", runTimeoutSeconds=300)
sessions_yield()
sessions_spawn(taskName="verify-m1", task="python3 /root/coordination/verify_agent.py verify --agent fix-m1 --files bot/__init__.py", ...)
# ← if FAIL → redispatch fix

# Step 3: Execute M2 (depends on M1)
sessions_spawn(taskName="fix-m2", task="Modify bot/app.py for feature X", ...)
sessions_yield()
sessions_spawn(taskName="verify-m2", ...)

# Step 4: Execute M3+M4 (parallel — same dep level)
sessions_spawn(taskName="fix-m3", ...)
sessions_spawn(taskName="fix-m4", ...)
sessions_yield()
# Verify both

# Step 5: Execute M5 (depends on M1+M2)
sessions_spawn(taskName="fix-m5", ...)
sessions_yield()
sessions_spawn(taskName="verify-m5", ...)

# Step 6: Findings Manager
sessions_spawn(taskName="findings-merge", task="python3 /root/coordination/findings_manager.py", ...)

# Step 7: Report to Boss
print("Boss — Feature X done ✅")
```

---

## 9. Edge Cases

| Situation | Action |
|-----------|--------|
| Prompt has no matching keywords | Search files by pattern, fall back to "scan codebase" generic plan |
| File doesn't exist on VPS | Search subdirectories with `find` command |
| More than 10 files needed | Group by directory + dependency level |
| All files are blocking | Sequential only — no parallel groups |
| Unknown file dependencies | Mark as independent, add warning |
| Task is "fix bug" (no feature keywords) | Infer from "fix", "bug", "error" = scan + audit pattern |

---

_Last updated: 2026-05-28 19:57 UTC | v1.0_
