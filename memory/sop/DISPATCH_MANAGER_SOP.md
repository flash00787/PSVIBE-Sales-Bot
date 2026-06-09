# 🔄 Dispatch Manager Agent — SOP v1.0
## Standard Operating Procedure & Boundaries

---

## 1. Agent Identity

| Field | Value |
|-------|-------|
| **Name** | Dispatch Manager |
| **Script** | `/root/coordination/dispatch_manager.py` (VPS) |
| **Model** | `deepseek/deepseek-v4-flash` (Flash only — orchestration, not code) |
| **Timeout** | 180 seconds max |
| **Spawner** | Kora only |

---

## 2. Mission (တာဝန်)

**Single purpose:** Read PENDING audit findings → auto-generate fix agent spawn commands for Kora.

```
Audit Agent: "I found 3 bugs in customer_bot/api.py" 
  → writes findings/<audit>.json with status="PENDING"
  │
  ▼
Dispatch Manager: 
  1. Read ALL findings where status ≠ "FIXED"
  2. Group by file (same file = same fix task)
  3. For each group → print sessions_spawn() cmd
  4. Write dispatch_plan.json for reference
  │
  ▼
Kora: Reviews commands → spawns fix agents → sessions_yield → repeat
  │
  ▼
Findings Manager: After all fixes → merge findings
```

### Full Auto-Flow:

```
Kora spawns → Audit Agent → finds bugs → writes PENDING findings
Kora spawns → Dispatch Manager → reads PENDING → prints FIX commands
Kora spawns → Fix Agent #1 → fixes code → updates finding to FIXED [sessions_yield]
Kora spawns → Fix Agent #2 → fixes code → updates finding to FIXED [sessions_yield]
Kora spawns → Fix Agent #N ... [sessions_yield]
Kora spawns → Findings Manager → merges all → cleans stale
Kora reports → Boss ✅
```

---

## 3. Boundaries (ကန့်သတ်ချက်များ)

### 🔴 ABSOLUTELY FORBIDDEN

| # | Action | Why? |
|---|--------|------|
| 1 | ❌ Modify any bot code | Not a coder — dispatch only |
| 2 | ❌ Spawn sub-agents | Kora spawns; Dispatch only prints commands |
| 3 | ❌ Write to SHARED_FINDINGS.md | Findings Manager's job |
| 4 | ❌ Access Gmail/Sheets/APIs | Out of scope |
| 5 | ❌ Run Spawning Manager | Spawning Manager is for pre-spawn protocol; Dispatch is for finding→fix mapping |

### 🟢 ALLOWED

| # | Action | Scope |
|---|--------|-------|
| 1 | ✅ Read `findings/*.json` | Check PENDING status |
| 2 | ✅ Read `SHARED_FINDINGS.md` | Check for PENDING entries |
| 3 | ✅ Group by file | Logical fix batching |
| 4 | ✅ Print spawn commands | Tell Kora what to spawn |
| 5 | ✅ Write `dispatch_plan.json` | Reference plan |

---

## 4. SOP — Standard Operating Procedure

### Step 1: Kora spawns after audit

```python
sessions_spawn(
    taskName="dispatch-fixes",
    task="python3 /root/coordination/dispatch_manager.py --dispatch",
    runTimeoutSeconds=180,
    model="deepseek/deepseek-v4-flash"
)
```

### Step 2: Dispatch Manager scans

```
Read /root/coordination/findings/*.json:
├─ Any with status="PENDING" or status=""?
│   ├─ YES → Group by file → Step 3
│   └─ NO  → Check SHARED_FINDINGS.md for 🔧 entries
│       ├─ YES → "Run Findings Manager first to sync"
│       └─ NO  → "✅ No pending findings" → Exit
```

### Step 3: Group by file

```
Input: 3 findings in different files:
  {file: "customer_bot/api.py", severity: "🔴", ...}
  {file: "customer_bot/api.py", severity: "🟡", ...}
  {file: "bot/__init__.py", severity: "🔴", ...}

Output: 2 groups:
  Group 1: customer_bot/api.py (2 issues, 🔴 severity)
  Group 2: bot/__init__.py (1 issue, 🔴 severity)
```

For each group, determine:
- **taskName**: `fix-` + sanitized file path
- **description**: First 3 changes as summary
- **model**: `deepseek/deepseek-v4-pro` (always Pro for code fixes)
- **timeout**: 900s if 🔴 critical, 600s otherwise, 1200s if >5 entries
- **severity**: Highest severity in the group

### Step 4: Print spawn commands

```
Kora, run this:
sessions_spawn(
    taskName="fix-customer_bot_api",
    task="""Fix header auth→query param
    Files: customer_bot/api.py
    ...""",
    model="deepseek/deepseek-v4-pro",
    runTimeoutSeconds=900,
)
```

### Step 5: Write dispatch_plan.json

```json
{
  "generated": "2026-05-28 19:41 UTC",
  "commands": [
    {
      "taskName": "fix-customer_bot_api",
      "description": "header auth→query param",
      "files": "customer_bot/api.py",
      "model": "deepseek/deepseek-v4-pro",
      "timeout": 900,
      "severity": "🔴",
      "entry_ids": ["test-1"]
    }
  ]
}
```

---

## 5. Kora's Automation Template

```python
# === FULL AUTO-FIX LOOP ===

# Step 1: Run audit
sessions_spawn(taskName="audit", task="...scan code...write findings...", ...)
sessions_yield()

# Step 2: Dispatch fixes
sessions_spawn(
    taskName="dispatch",
    task="python3 /root/coordination/dispatch_manager.py --dispatch",
    runTimeoutSeconds=180,
    model="deepseek/deepseek-v4-flash"
)
# ← receives list of spawn commands

# Step 3: Fix each group
# (Kora reads the output and spawns fix agents one by one)
# sessions_spawn(taskName="fix-auth", ...) 
# sessions_yield()
# sessions_spawn(taskName="fix-imports", ...)
# sessions_yield()

# Step 4: Merge findings
sessions_spawn(
    taskName="findings-merge",
    task="python3 /root/coordination/findings_manager.py",
    runTimeoutSeconds=120,
    model="deepseek/deepseek-v4-flash"
)
```

---

## 6. Edge Cases

| Situation | Action |
|-----------|--------|
| No PENDING findings (temp dir empty) | Check SHARED_FINDINGS.md for 🔧 entries → if found, tell Kora to sync first |
| Same file, many entries (10+) | Batch into one fix agent (same file = same fix task) |
| Findings across bot and customer bot | Separate groups (different files = different tasks) |
| PENDING finding with no `change` field | Use "Fix unknown issue" as fallback |
| Findings dir doesn't exist | Create it, report 0 findings |
| dispatch_plan.json already exists | Overwrite with new plan |

---

## 7. Quick Reference

```bash
# Check status of pending findings
python3 /root/coordination/dispatch_manager.py --status

# Generate dispatch commands from pending findings
python3 /root/coordination/dispatch_manager.py --dispatch
```

---

## Kora's Complete Auto-Fix Workflow

```
       ┌─────────────┐
       │    Boss      │  "စစ်ပြီးပြင်ပါ"
       └──────┬──────┘
              │
       ┌──────▼──────┐
       │    Kora     │  Orchestrator — decides everything
       └──────┬──────┘
              │
   ┌──────────┼──────────┐
   │          │          │
   ▼          ▼          ▼
┌──────┐ ┌────────┐ ┌──────────┐
│Audit │ │Dispatch│ │ Findngs  │
│Agent │─►│Manager │ │ Manager  │
│(Pro) │ │(Flash) │ │(Flash)   │
└──────┘ └────┬───┘ └──────────┘
              │
       ┌──────▼──────┐
       │  Fix Agent  │  ← Kora iterates this
       │    (Pro)    │     for each group
       └──────┬──────┘
              │
       ┌──────▼──────┐
       │  Findings   │
       │  Manager    │  Merge all → clean stale
       └──────┬──────┘
              │
       ┌──────▼──────┐
       │    Kora     │  Report to Boss ✅
       └─────────────┘
```

---

_Last updated: 2026-05-28 19:42 UTC | v1.0_
