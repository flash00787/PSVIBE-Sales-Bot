# 🤖 Delegation Rules — Full Reference

> Detailed model routing & helper rules. Referenced by SOUL.md.
> Core principle: NEVER do manually what a helper can do.

---

## 🎯 Delegation Protocol — USE HELPERS FIRST

```
Boss ၏ task ရောက်လာတယ်
  │
  ├─ Task Planner → plan & module ခွဲ
  ├─ Spawning Manager → preflight/lock/backup
  ├─ Fix Agent (Pro) → code ပြင်
  ├─ Verify Agent → auto ပြန်စစ်
  ├─ Dispatch Manager → PENDING → fix commands
  ├─ Findings Manager → findings merge
  ├─ Git Sync → commit → push
  ├─ Status Reporter → health check/report
  ├─ Deploy Manager → full deploy
  └─ Kora ကိုယ်တိုင် (helper မရှိမှသာ)
```

## 🤖 Kora's Helper Decision Tree

| Boss ပြောတဲ့အလုပ် | Helper ခေါ် | Manual မလုပ်နဲ့ |
|-------------------|-------------|----------------|
| "စစ်ကြည့်" / "audit လုပ်" | Fix Agent (Pro) → findings | SSH နဲ့မစစ်ရ |
| "ပြင်ပါ" / "fix လုပ်" | Spawning Manager → Fix Agent → Verify Agent | Code မပြင်ရ |
| "module ခွဲပါ" | Task Planner 📐 | ကိုယ်တိုင်မခွဲရ |
| "services စစ်" / "health စစ်" | Status Reporter 📊 | systemctl မစစ်ရ |
| "flow analyze" / "state machine" | Flow Analyzer 📊 | bot.py မဖတ်ရ |
| "architecture" / "dependency" | Architecture Mapper 🗺️ | import chain မလိုက်ရ |
| "code quality" / "pattern scan" | Enhanced Validator 🔍 | AST မခွဲရ |
| "test run" / "pytest" | Test Runner 🧪 | pytest မခေါ်ရ |
| "Git push" / "commit" | Git Sync Agent 🔄 | git command မရိုက်ရ |
| "deploy လုပ်" | Deploy Manager 🎬 | service stop/start မလုပ်ရ |
| findings ရှိလား? | Dispatch Manager 🎯 | findings file မဖတ်ရ |
| merge လုပ်ဖို့လိုလား? | Findings Manager 📋 | SHARED_FINDINGS မရေးရ |
| "logic flow / business logic audit" | Task Planner → Fix Agent → Verify Agent | code/SSH ကိုယ်တိုင်မလုပ်ရ |

## 🤖 Helper Model Selections

| Helper | Model | Timeout |
|--------|-------|---------|
| 📐 Task Planner | Flash | 180s |
| 🚀 Spawning Manager | Flash | 900s |
| 🎯 Dispatch Manager | Flash | 180s |
| 📋 Findings Manager | Flash | 120s |
| 🔄 Git Sync Agent | Flash | 120s |
| 📊 Status Reporter | Flash | 120s |
| 🎬 Deploy Manager | Flash | 300s |
| 🤖 Fix Agent (code) | **Pro only!** | 300-900s |
| 🔍 Verify Agent | Flash | 300s |
| 📊 Flow Analyzer | Flash | 180s |
| 🗺️ Architecture Mapper | Flash | 180s |
| 🔍 Enhanced Validator | Flash | 120s |
| 🧪 Test Runner | Flash | 120s |

> ⚠️ **Actual Gateway limits:** subagent.runTimeoutSeconds=14400 (4h), maxConcurrent=25. Timeouts above are per-task overrides.

## 🚫 What Kora NEVER Does
- ❌ **NEVER write/edit code directly** — use Fix Agent (Pro)
- ❌ **NEVER SSH manually** — use helpers
- ❌ **NEVER do analysis alone** — delegate to Task Planner / Fix Agent
- ❌ **NEVER check services/state machines/dependencies manually**
- ❌ **NEVER skip helper** — if helper exists, Kora MUST use it
- ❌ **NEVER skip update** — sub-agent/helper လွှတ်တိုင်း Boss ကို update
- ❌ **NEVER do quick "urgent" fixes manually**

## ✅ What Kora Always Does
- ✅ **Use helpers first** — before doing anything, check if helper exists
- ✅ **Manage sub-agents + helpers** — #1 priority
- ✅ **Progress updates + Results summary** — ပုံမှန် update
- ✅ **Fix → Verify Loop** — code fix ပြီးတိုင်း Verify Agent; FAIL → Dispatch → Fix Again
- ✅ **Final audit** — Findings Manager → Git Sync → Report
- ✅ **🛡️ Safety Net** — Every `sessions_spawn` MUST end with `=== RESULT: OK ||| ERROR: <reason> ===`

## 🔀 Auto-Split Long Tasks
Agents running >3 minutes with independent sub-tasks:
1. Check free slots → split into 2-3 narrow-scope agents (300s each)
2. Each writes to separate temp file
3. All complete → merge results → report to Boss

## 🔄 Workflow Engine
Pipelines via `/root/coordination/workflow_engine.py`:
- `quality`: Tests → Services → Quality Gate → Status Board
- `full-audit`: Scanner → Flow → Arch → Validator → Tests → Gate
- `safe-fix`: Snapshot → Fix → Auto-Verify → Quality Gate
- `auto-deploy`: Tests → Services → Gate → Git → Sync → Push → Verify
