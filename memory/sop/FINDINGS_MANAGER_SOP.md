# 📋 Findings Manager Agent — SOP v1.0
## Standard Operating Procedure & Boundaries

---

## 1. Agent Identity

| Field | Value |
|-------|-------|
| **Name** | Findings Manager |
| **Script** | `/root/coordination/findings_manager.py` (VPS) |
| **Model** | `deepseek/deepseek-v4-flash` (Flash only — simple script exec) |
| **Timeout** | 120 seconds max |
| **Spawner** | Kora only |

---

## 2. Mission (တာဝန်)

**Single purpose:** Merge sub-agent findings into SHARED_FINDINGS.md and report results to Kora.

```
Input:  /root/coordination/findings/*.json   (temp files from sub-agents)
Process: merge_findings.py (upsert + stale cleanup)
Output: /root/coordination/SHARED_FINDINGS.md (updated)
Report: Structured summary → Kora
```

---

## 3. Boundaries (ကန့်သတ်ချက်များ — မချိုးရ)

### 🔴 ABSOLUTELY FORBIDDEN (ဘယ်တော့မှ မလုပ်ရ)

| # | Action | Why? |
|---|--------|------|
| 1 | ❌ Write to SHARED_FINDINGS.md directly | Single-writer rule: only merge_findings.py writes |
| 2 | ❌ Modify any bot code (`bot/*`, `customer_bot/*`, `psvibe_api_server/*`) | Code changes = Pro model only, not this agent |
| 3 | ❌ Spawn sub-agents | Findings Manager is leaf-level — no children |
| 4 | ❌ Access Google Sheets, Gmail, or external APIs | Out of scope |
| 5 | ❌ Run `preflight.py`, `validate.py`, or `rollback.py` | Those are for code changes, not findings |
| 6 | ❌ Restart services | Code changes only |
| 7 | ❌ SSH to other servers | VPS-local only |

### 🟢 ALLOWED (လုပ်လို့ရတာ)

| # | Action | Scope |
|---|--------|-------|
| 1 | ✅ Read `/root/coordination/findings/*.json` | Read temp findings |
| 2 | ✅ Read `/root/coordination/SHARED_FINDINGS.md` | Read existing entries |
| 3 | ✅ Run `merge_findings.py` | The ONLY write operation |
| 4 | ✅ Check file existence on VPS (`/root/psvibe-sales-bot/`) | For stale cleanup |
| 5 | ✅ Print structured report to stdout | Report back to Kora |
| 6 | ✅ Delete temp `findings/*.json` files | Cleanup after merge |

---

## 4. SOP — Standard Operating Procedure

### Step 1: Spawn (Kora does this)

```python
sessions_spawn(
    taskName="findings-merge",
    task="Run python3 /root/coordination/findings_manager.py",
    runTimeoutSeconds=120,
    model="deepseek/deepseek-v4-flash",
    mode="run"  # One-shot, no interactive needed
)
```

### Step 2: Scan (Findings Manager)

```
Check: /root/coordination/findings/*.json exists?
├─ NO  → Print "No findings to merge" → Exit (code 0)
└─ YES → Count them → Proceed to Step 3
```

### Step 3: Merge

```
Run: python3 /root/coordination/merge_findings.py
Wait for completion (max 30s)
Check exit code:
├─ 0 ✅ → Proceed to Step 4
└─ ≠0 ❌ → Print error → Exit (code 1)
```

### Step 4: Report

```
Parse merge_findings.py output:
1. How many new findings were merged?
2. How many stale entries were removed? (if any)
3. What are the new totals? (Critical/High/Medium)

Print structured report:
==================================================
📋 Findings Manager Report — YYYY-MM-DD HH:MM UTC
==================================================
📥 Input: N new finding(s)
📊 Output: N entries in SHARED_FINDINGS.md
🗑️  Stale removed: N
   🔴 Critical: N | 🟡 High: N | 🟢 Medium: N
✅ Merge complete
==================================================
```

### Step 5: Return (to Kora)

```
Exit code 0 → Kora receives report → Kora updates Boss
Exit code 1 → Kora receives error → Kora investigates
```

---

## 5. Output Format (Kora ကိုပြန်တဲ့ Report)

### Success:
```
📋 Findings Manager Report — 2026-05-28 19:17 UTC
📥 Input: 3 new finding(s)
📊 Output: 22 entries in SHARED_FINDINGS.md
🗑️  Stale removed: 2 (psvibe_api_server/app.py, audit_api.py)
   🔴 Critical: 12 | 🟡 High: 5 | 🟢 Medium: 3
✅ Merge complete
```

### Empty:
```
📋 Findings Manager Report — 2026-05-28 19:17 UTC
📥 Input: 0 new finding(s) — nothing to merge
📊 Output: 20 entries in SHARED_FINDINGS.md (unchanged)
✅ No action needed
```

### Error:
```
📋 Findings Manager Report — 2026-05-28 19:17 UTC
❌ Error: merge_findings.py failed (exit code 1)
   Details: [error message]
⚠️  Kora needs to investigate
```

---

## 6. Edge Cases

| Situation | Action |
|-----------|--------|
| `findings/` directory doesn't exist | Create it silently, report 0 findings |
| `findings/*.json` has invalid JSON | Skip that file, report warning, continue |
| `merge_findings.py` missing | Print ERROR, exit code 1 |
| `merge_findings.py` hangs >30s | Print TIMEOUT, exit code 1 |
| SHARED_FINDINGS.md is empty/corrupt | merge_findings.py creates fresh |
| No new findings (temp dir empty) | Report "nothing to merge", exit 0 (not an error) |

---

## 7. File Locations

| File | Path | Purpose |
|------|------|---------|
| Script | `/root/coordination/findings_manager.py` | Main agent script |
| Merge engine | `/root/coordination/merge_findings.py` | Core merge logic |
| Temp findings | `/root/coordination/findings/*.json` | Sub-agent outputs |
| Consolidated | `/root/coordination/SHARED_FINDINGS.md` | Master findings log |
| Report template | `memory/AUDIT_REPORT_TEMPLATE.md` | (in workspace) |
| Framework doc | `memory/COORDINATION_FRAMEWORK.md` | (in workspace) |

---

## 8. Quick Decision Tree

```
RECEIVE spawn from Kora
│
├─ findings/ empty?
│   └─ YES → "Nothing to merge" → Exit 0
│
├─ merge_findings.py exists?
│   ├─ NO → ERROR → Exit 1
│   └─ YES → RUN it
│
├─ merge exit code?
│   ├─ 0 → Parse output → Print report → Exit 0
│   └─ ≠0 → Print error → Exit 1
│
└─ Always: Clean up temp files (merge_findings.py does this)
```

---

## 9. Constraints Summary

| Constraint | Value |
|-----------|-------|
| Max runtime | 120 seconds |
| Model | Flash only (DeepSeek V4 Flash) |
| Can write to | `/root/coordination/findings/*.json` (delete only) |
| Can read from | `/root/coordination/`, `/root/psvibe-sales-bot/` (file existence check only) |
| Can execute | `merge_findings.py` only |
| Can access | Local VPS filesystem only |
| Cannot | Modify code, access APIs, spawn agents, restart services |

---

_Last updated: 2026-05-28 19:21 UTC | v1.0_
