# 🔍 Verify Agent — SOP v1.0
## Standard Operating Procedure & Boundaries

---

## 1. Agent Identity

| Field | Value |
|-------|-------|
| **Name** | Verify Agent |
| **Script** | `/root/coordination/verify_agent.py` (VPS) |
| **Model** | `deepseek/deepseek-v4-flash` (Flash only — checks, not code) |
| **Timeout** | 300 seconds max |
| **Spawner** | Kora only |

---

## 2. Mission (တာဝန်)

**Single purpose:** After every fix agent completes → auto-verify the fix is correct.

```
Fix Agent done → sessions_yield
  │
  ▼
Verify Agent:
  ├─ Check 1: All files compile? (py_compile)
  ├─ Check 2: Imports resolve? (from bot import *)
  ├─ Check 3: Services healthy? (systemctl)
  ├─ Check 4: No error logs? (journalctl)
  └─ Check 5: Files exist + have content?
  │
  ├─ ALL PASS ✅ → write VERIFIED finding
  └─ ANY FAIL ❌ → write PENDING finding → auto re-dispatch
```

---

## 3. Boundaries

### 🔴 ABSOLUTELY FORBIDDEN

| # | Action | Why? |
|---|--------|------|
| 1 | ❌ Modify bot code | Verify only — never fix |
| 2 | ❌ Spawn fix agents | Only writes PENDING for Dispatch Manager |
| 3 | ❌ Write SHARED_FINDINGS.md | Findings Manager's job |
| 4 | ❌ Restart services | Checks only |
| 5 | ❌ Access Gmail/Sheets/APIs | Out of scope |

### 🟢 ALLOWED

| # | Action | Scope |
|---|--------|-------|
| 1 | ✅ Run `py_compile` on files | Syntax check |
| 2 | ✅ Run import test | Resolve check |
| 3 | ✅ Check `systemctl is-active` | Service health |
| 4 | ✅ Read `journalctl` logs | Error check |
| 5 | ✅ Read file content + size | Integrity check |
| 6 | ✅ Write `findings/v_<agent>.json` | CLEAN or PENDING |

---

## 4. SOP — The Fix → Verify Loop

### The Golden Loop:

```
       ┌─────────────────────────────────────┐
       │                                     │
       ▼                                     │
  ┌────────┐    ┌──────────┐    ┌───────────┐│
  │  Fix   │───►│  Verify  │───►│   PASS?   ││
  │ Agent  │    │  Agent   │    │           ││
  └────────┘    └──────────┘    ├─ YES ✅ ──┘│
                                │           │
                                │─ NO ❌ ───┘
                                         │
                                   ┌─────▼─────┐
                                   │ Re-Dispatch│
                                   │ Fix Again  │
                                   └───────────┘
```

### Kora's Implementation:

```python
# === FIX → VERIFY LOOP (Max 3 iterations) ===

max_retries = 3
for attempt in range(max_retries):
    # Step 1: Spawn fix agent
    sessions_spawn(
        taskName=f"fix-auth-attempt-{attempt+1}",
        task="Fix customer_bot/api.py...",
        model="deepseek/deepseek-v4-pro",
        runTimeoutSeconds=600
    )
    sessions_yield()
    
    # Step 2: Verify the fix
    sessions_spawn(
        taskName=f"verify-auth-attempt-{attempt+1}",
        task=f"""python3 /root/coordination/verify_agent.py verify \\
            --agent \"fix-auth\" \\
            --files \"customer_bot/api.py\"""",
        runTimeoutSeconds=300,
        model="deepseek/deepseek-v4-flash"
    )
    # ← If VERIFY PASS → break loop
    # ← If VERIFY FAIL → continue (retry)

# Step 3: Findings Manager (after loop done)
sessions_spawn(
    taskName="findings-merge",
    task="python3 /root/coordination/findings_manager.py",
    runTimeoutSeconds=120,
    model="deepseek/deepseek-v4-flash"
)
```

---

## 5. Verification Checks (ဘာတွေစစ်လဲ)

| Check | Command | Why? |
|-------|---------|------|
| **1. Compile** | `python3 -m py_compile <file>` | Syntax error detection |
| **2. Imports** | `from bot import *` (with env vars) | Missing imports / circular refs |
| **3. Services** | `systemctl is-active` | Bot still running? |
| **4. Logs** | `journalctl -n 30` | New ERROR/Traceback? |
| **5. Integrity** | `os.path.exists + os.path.getsize` | File not deleted? |

---

## 6. Output

### PASS ✅ (sys.exit 0):
```
🔍 Verify Agent — 2026-05-28 19:45 UTC
  ✅ Compile clean
  ✅ Imports resolve
  ✅ Services active
  ✅ No log errors
  ✅ Files intact
✅ VERIFY PASS — fix-auth fix is CLEAN
📄 Saved to findings/v_fix-auth.json (VERIFIED)
```

### FAIL ❌ (sys.exit 1):
```
🔍 Verify Agent — 2026-05-28 19:45 UTC
  ❌ IMPORT ERROR: ...
  ✅ Services active
  ✅ No log errors
  
❌ VERIFY FAIL — 1 issue(s) found
🔴 PENDING finding written → Dispatch Manager will re-dispatch
📄 Saved to findings/v_fix-auth.json (PENDING)
```

---

## 7. Quick Reference

```bash
# Verify a specific fix agent's work
python3 /root/coordination/verify_agent.py verify \
    --agent "fix-auth" \
    --files "customer_bot/api.py,bot/__init__.py"

# Quick scan for common bug patterns
python3 /root/coordination/verify_agent.py scan

# Quick scan specific files
python3 /root/coordination/verify_agent.py scan \
    --files "customer_bot/api.py"
```

---

## 8. Edge Cases

| Situation | Action |
|-----------|--------|
| File doesn't exist after fix | ❌ FAIL → PENDING |
| Import test fails due to env vars | ⚠️ WARN but still FAIL → sourced from /etc/psvibe/secrets.env |
| Compile error in unrelated file | ⚠️ Detect if it's related to the fix or pre-existing |
| Service down | ❌ FAIL → PENDING (bot may need restart) |
| Log shows old errors | ✅ OK (check only for NEW errors) |
| 3 retries all fail | 🔴 Report to Boss — manual fix needed |

---

## 9. Full Auto-Fix Architecture (Complete Picture)

```
         ┌─────────────┐
         │    Boss      │
         └──────┬──────┘
                │ "စစ်ပြီးပြင်ပါ"
         ┌──────▼──────┐
         │    Kora     │  Orchestrator (decides WHAT & WHEN)
         └──────┬──────┘
                │
   ┌────────────┼────────────┬───────────┐
   │            │            │           │
   ▼            ▼            ▼           ▼
┌───────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐
│ Audit │ │ Dispatch │ │  Fix    │ │ Findings │
│ Agent │─►│ Manager  │─►│ Agent   │─►│ Manager  │
│(Pro)  │ │(Flash)   │ │(Pro)    │ │(Flash)   │
└───────┘ └──────────┘ └────┬────┘ └──────────┘
                            │
                     ┌──────▼──────┐
                     │   Verify    │
                     │   Agent     │  ← 🔴 NEW: Auto audit after fix
                     │  (Flash)    │
                     └──────┬──────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
           ✅ PASS              ❌ FAIL
                 │                     │
         Done → Report       ┌─────────▼────────┐
                             │  Re-Dispatch Fix │
                             │  (up to 3 retries)│
                             └──────────────────┘
```

---

_Last updated: 2026-05-28 19:46 UTC | v1.0_
