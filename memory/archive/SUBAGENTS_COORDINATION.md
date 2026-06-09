# 🤖 Sub-Agents Coordination Guide

> **Author:** Kora — Ko Aung Chan Myint's Personal AI Assistant
> **Last Updated:** 2026-05-27 (22:14 UTC)
> **Rule Update:** Coding tasks → **Pro model only** (no Flash)

---

## 1. Overview — What Are Sub-Agents?

Sub-agents ဆိုတာ Main Agent (ဥပမာ Kora) ကနေ ခွဲထွက်မွေးဖွားလိုက်တဲ့ **Child Agent** တစ်ခုပါ။

- **Main Agent** = စကားပြောနေတဲ့ Agent (Kora)
- **Sub-agent** = အလုပ်တစ်ခုအတွက် သီးသန့်မွေးလိုက်တဲ့ Agent (Coder, Researcher, etc.)

### ဘာကြောင့် Sub-agents သုံးတာလဲ?

| အားသာချက် | ရှင်းလင်းချက် |
|---|---|
| ⚡ **Parallel Processing** | တစ်ပြိုင်နက်တည်း အလုပ်မျိုးစုံလုပ်လို့ရ |
| 🎯 **Specialization** | Coder, Researcher, Reviewer — သီးသန့် Model သုံးလို့ရ |
| 🔄 **Isolation** | Sub-agent error က main session ကို မထိခိုက်စေဘူး |
| 🧹 **Clean Context** | Sub-agent က context သန့်သန့်နဲ့ စတယ် (overload မဖြစ်ဘူး) |

---

## 2. Architecture — System Design

```
┌─────────────────────────────────────────────┐
│              Main Session (Kora)             │
│   Model: DeepSeek V4 Flash (Router)         │
│   Language: Burmese + English Tech Terms    │
│   Role: Orchestrator & Communicator         │
├─────────────────────────────────────────────┤
│                                             │
│   spawns_subagents()                        │
│        │                                    │
│        ├── ⭐ Coder ────────────────────────┤
│        │    Model: DeepSeek V4 Pro          │
│        │    Cost: Low ($)                   │
│        │    Use: Code writing, debugging    │
│        │                                    │
│        ├── 🔧 Reviewer/Fixer ──────────────┤
│        │    Model: Claude Sonnet 4          │
│        │    Route: OpenRouter API           │
│        │    Cost: Medium ($$)               │
│        │    Use: Error fixing, code review  │
│        │                                    │
│        └── 🔍 Researcher ──────────────────┤
│             Model: Grok 4.3                 │
│             Route: xAI API                  │
│             Cost: High ($$$)                │
│             Use: Library search, research   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 3. How Sub-Agents Work (Step-by-Step)

### Step 1: Task Analysis (Main Agent)
Main Agent က လက်ခံရရှိတဲ့ Task ကို ပိုင်းခြားသုံးသပ်တယ်။

```
User: "PS VIBE အတွက် Telegram Bot အသစ်ရေးပေး"
       │
       ▼
Kora Analysis:
  ├── This is a CODE task → Coder subagent သုံးမယ်
  ├── Heavy code (76+ files) → DeepSeek V4 Pro သုံးမယ်
  └── Coordination file တွေလိုမယ် → Shared files သုံးမယ်
```

### Step 2: Sub-agent Spawning
`sessions_spawn()` tool နဲ့ သားစပ်တူ Agent ကို မွေးဖွားတယ်။

```python
# Conceptual flow (not actual code):
subagent = sessions_spawn(
    task="Write the task brief here...",
    model="deepseek/deepseek-v4-pro",  # Specific model
    context="isolated"                   # Clean context
)
```

### Step 3: Wait for Completion
Main Agent က `sessions_yield()` နဲ့ စောင့်ဆိုင်းတယ်။

```
sessions_yield()
    │
    ▼
[Main Agent pauses here — no tool calls]
    │
    ▼
[Sub-agent completes] → [Result comes back]
    │
    ▼
[Main Agent resumes — processes result]
```

### Step 4: Result Aggregation
Sub-agent တွေဆီက ရလဒ်တွေကို စုစည်းပြီး User ကို မြန်မာလိုပြန်ပေးတယ်။

---

## 4. Model Routing Strategy

| Task Type | Model ရွေးချယ်မှု | API Key Source |
|---|---|---|
| **Code Writing** (ပုံမှန်) | DeepSeek V4 Pro | OpenClaw config |
| **Code Debug** (DeepSeek မရရင်) | Claude Sonnet 4 | OpenRouter (`sk-or-v1-...`) |
| **Research / Library Search** | Grok 4.3 | xAI (`xai-...`) |
| **Simple Questions** | DeepSeek V4 Flash | OpenClaw config |

### ဘယ် Model ကို ဘယ်အချိန်သုံးမလဲ?

```
အလုပ်ဝင်လာရင်
  │
  ├── Code ရေးဖို့လား?
  │     ├── Yes → DeepSeek V4 Pro (primary coder)
  │     └── No  → ရှေ့ဆက်စဉ်းစား
  │
  ├── Code error တက်နေလား?
  │     ├── DeepSeek မရ → Claude Sonnet 4 (reviewer)
  │     └── ရတယ် → DeepSeek V4 Pro နဲ့ဆက်
  │
  ├── New library / update လိုလား?
  │     └── Yes → Grok 4.3 (researcher)
  │
  └── Simple ဖြေရုံပဲလား?
        └── Yes → DeepSeek V4 Flash (main router)
```

---

## 5. Function Name & API Consistency (CRITICAL)

> **⚠️ This is the #1 cause of failure when multiple sub-agents write code together.**

### 5.1 The Problem

Sub-agents တစ်ယောက်ချင်းစီက သီးခြား spawn လုပ်ထားတာမို့ —

| Sub-agent A (Handler) | Sub-agent B (Database) | ❌ Mismatch! |
|---|---|---|
| `get_user_info()` | `fetch_user_data()` | Different names, same purpose |
| `update_balance()` | `add_balance()` | Logic split between files |
| `import db_helpers` | `from utils import *` | Inconsistent imports |
| Returns dict | Returns tuple | Caller breaks |

### 5.2 The Solution: Interface Spec First!

**Sub-agents မမွေးခင် → Interface Spec ကို အရင်ရေးရမယ်။**

```
                     BEFORE spawning ANY sub-agent:
                                  │
                                  ▼
┌──────────────────────────────────────────────────────┐
│           INTERFACE SPEC (COORDINATION.md)           │
│                                                      │
│  1. 📋 Function Signatures (exact names + params)    │
│  2. 📂 Module Structure (exact file paths)           │
│  3. 🏷️  Naming Convention (snake_case / camelCase)   │
│  4. 🔗 Import Paths (exact from...import...)          │
│  5. 📤 Return Types (what each function returns)      │
│  6. 🚨 Error Handling (raise vs return None)          │
│  7. 📁 File Assignments (who writes which file)       │
└──────────────────────────────────────────────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                ▼                 ▼                 ▼
         Sub-agent A        Sub-agent B        Sub-agent C
         (writes file1)     (writes file2)     (writes file3)
         MUST follow        MUST follow        MUST follow
         Interface Spec     Interface Spec     Interface Spec
```

### 5.3 Interface Spec Template

```markdown
# INTERFACE SPEC — [Project Name]

## Naming Convention
- **Functions:** `snake_case()` — e.g. `get_user_balance()`
- **Classes:** `PascalCase` — e.g. `UserHandler`, `DatabaseManager`
- **Constants:** `UPPER_SNAKE_CASE` — e.g. `DEFAULT_TIMEOUT = 30`
- **Files:** `snake_case.py` — e.g. `user_handler.py`

## Module Structure
```
project/
├── app.py              ← Entry point (writes: Agent A)
├── handlers/
│   ├── __init__.py     ← Exports all handlers
│   ├── user.py         ← get_user(), create_user() (writes: Agent B)
│   └── payment.py      ← process_payment() (writes: Agent C)
└── utils/
    ├── __init__.py
    ├── db.py           ← query_db(), execute_db() (writes: Agent D)
    └── helpers.py      ← format_response() (writes: Agent D)
```

## Function Signatures (Exact API Contract)

### File: handlers/user.py
```python
def get_user(user_id: int) -> dict | None
    # Returns user dict or None if not found

def create_user(name: str, phone: str) -> dict
    # Returns created user dict

def update_balance(user_id: int, amount: float) -> bool
    # Returns True/False
```

### File: utils/db.py
```python
def query_db(sql: str, params: tuple = ()) -> list[dict]
    # Returns list of row dicts
def execute_db(sql: str, params: tuple = ()) -> int
    # Returns affected row count
```

## Import Paths (Must be exact!)
```python
from handlers.user import get_user, create_user, update_balance
from utils.db import query_db, execute_db
from utils.helpers import format_response
```

## Error Handling Convention
- **DB errors:** `execute_db()` → raises `DatabaseError`
- **Not found:** `get_user()` → returns `None` (not raise)
- **Validation:** Handler functions → returns `{"error": "message"}` dict on error
- **Success:** Always return `True` / dict — never mix types
```

### 5.4 Shared Constants & Enums

```python
# constants.py — ALL sub-agents must import from here, never hardcode!

# Status codes
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_BANNED = "banned"

# Error messages
ERR_USER_NOT_FOUND = "User not found"
ERR_INSUFFICIENT_BALANCE = "Insufficient balance"
ERR_INVALID_INPUT = "Invalid input"

# Config keys (for env vars)
CONFIG_DB_HOST = "DB_HOST"
CONFIG_DB_PORT = "DB_PORT"
CONFIG_BOT_TOKEN = "BOT_TOKEN"
```

### 5.5 Verification Checklist (Before Sub-agents Start)

Main Agent (Kora) က အောက်ပါ checklist ကို **Interface Spec ကို finalize** လုပ်ပြီးမှသာ sub-agents တွေကို spawn လုပ်ရမယ် —

```
□ Function signatures အားလုံး ရှင်းရှင်းလင်းလင်းရှိလား?
□ Return types ကိုက်ညီမှုရှိလား? (dict/list/bool/None)
□ Import paths တွေ exact ဖြစ်လား? (no relative chaos)
□ Naming convention တစ်ခုတည်းကို အားလုံးလိုက်နာလား?
□ Error handling pattern တူညီလား?
□ File assignments က sub-agent တစ်ယောက်စီအတွက် ရှင်းရှင်းလင်းလင်းရှိလား?
□ Shared constants ကို သီးသန့် file တစ်ခုမှာ ထားပြီးလား?
```

### 5.6 Real Example: What Happens Without Interface Spec

PS VIBE Refactored Bot မှာ ဖြစ်ခဲ့တဲ့ အမှားများ —

| Problem | Root Cause | Fix |
|---|---|---|
| `now_mmt()` missing in 13 files | Sub-agents က function name ကို မသိဘူး | Interface spec ထဲမှာ include လုပ် |
| `_ALLOWED_USER_IDS` hardcoded vs function | တစ်ယောက်က hardcode, တစ်ယောက်က function | Shared constant file သုံး |
| `from telegram.ext import ...` missing in app.py | Import paths ကို agree မလုပ်ခဲ့ဘူး | Spec ထဲမှာ exact imports ရေး |

---

## 6. Multi-Agent Coordination Pattern

Agent တစ်ခုထက်ပိုပြီး တွဲဖက်အလုပ်လုပ်စေချင်ရင် အောက်ပါ Pattern ကို သုံးတယ်။

### Pattern: "Interface-First Coordination"

```
┌─────────────────────────────────────────────────┐
│         1. Create Shared Interface Spec         │
│                 (COORDINATION.md)               │
└─────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────┐
│         2. Create Path Mapping                  │
│             (path_mapping.json)                 │
│           Obfuscated paths for agents           │
└─────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Sub-agent A  │  │  Sub-agent B  │  │  Sub-agent C  │
│   (Coder)    │  │ (Researcher) │  │  (Reviewer)  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│         3. Each writes to AGENT_STATUS.md       │
│           - Task completed status               │
│           - Output location                     │
│           - Errors (if any)                     │
└─────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────┐
│         4. Main Agent (Kora)                    │
│           - Reads all AGENT_STATUS.md           │
│           - Aggregates results                  │
│           - Reports to user in Burmese          │
└─────────────────────────────────────────────────┘
```

### Key File Structure

```
📁 shared-storage/
├── 📄 COORDINATION.md     ← Rules all agents must follow
├── 📄 path_mapping.json   ← Obfuscated file paths
├── 📄 AGENT_STATUS.md     ← Each agent writes completion
└── 📁 outputs/            ← Sub-agent output files
```

---

## 7. Best Practices

### ✅ Do's
- **Keep scope narrow** — Sub-agent တစ်ခုကို အလုပ်တစ်ခုပဲပေးပါ
- **Use shared spec first** — Agent တွေမမွေးခင် interface spec ကိုအရင်ရေးပါ
- **Fail fast** — Timeout သတ်မှတ်ပြီး မအောင်ရင် ရပ်လိုက်ပါ
- **Write completion status** — AGENT_STATUS.md ကို update လုပ်ပါ
- **Clean context** — `context="isolated"` သုံးပါ (fork မသုံးပါနဲ့)
- **Interface Spec ကို Task မစခင် Finalize** — Sub-agents ကို spawn မလုပ်ခင် spec ကိုအရင်အတည်ပြုပါ

### ❌ Don'ts
- Sub-agent ကို context တွေအများကြီးမပေးပါနဲ့
- Parallel လုပ်နေတဲ့ agent တွေကို သူများ output ကို မမှီခိုပါစေနဲ့
- ရှည်လျားတဲ့ task ဆို timeout ကို လုံလောက်အောင်ထားပါ (10 min+)
- Function name တွေကို guess မလုပ်ပါနဲ့ — Interface Spec ကိုပဲ လိုက်နာပါ

---

## 8. Agent-Level Timeout Configuration

### 🤖 Kora Settings

| Setting | Value |
|---|---|
| **Sub-agent Timeout** | **2 hours** (120 min) |
| **Max Retries** | **3** |
| **Concurrent Sub-agents** | **10** |

### 🤖 Nova Settings

| Setting | Value |
|---|---|
| **Sub-agent Timeout** | **30 min** |
| **Max Retries** | **2** |
| **Concurrent Sub-agents** | **5** |

### Comparison

| Metric | Kora | Nova |
|---|---|---|
| ⏱️ Timeout | 120 min | 30 min |
| 🔄 Retries | 3 | 2 |
| 🏗️ Concurrent | 10 | 5 |
| 🎯 Purpose | Heavy coding, orchestration | Lighter tasks, quick responses |

### Why These Values?

| Agent | Reasoning |
|---|---|
| **Kora** (2h / 3 retry / 10 concurrent) | Heavy code-gen (PS VIBE bot has 12K+ lines, 76 files), complex orchestration, multiple parallel sub-agents လိုတယ် |
| **Nova** (30m / 2 retry / 5 concurrent) | Lighter agent, simpler tasks, Ye Yint Oo's personal assistant — quick responses လိုတယ် |

---

## 9. Per-Task Timeout Guidelines

| Task Type | Timeout | Model | Notes |
|---|---|---|---|
| Code generation (small) | 5 min | DeepSeek V4 Pro | Under 500 lines |
| Code generation (large) | 10 min | DeepSeek V4 Pro | Multi-file projects |
| Code review | 5 min | Claude Sonnet 4 | Error analysis |
| Research | 5 min | Grok 4.3 | Library/update search |
| Simple reply | N/A | DeepSeek V4 Flash | Main session only |

---

## 8.5 Kora's Role — Manager Only (DO NOT Code)

- **Rule from:** Boss Osmo (2026-05-27)
- Kora's **primary model** (DeepSeek V4 Flash) = **conversation + agent management ONLY**
- **NEVER** write/fix code directly — always delegate to agent sub-agents
- Agent sub-agents must always use **Pro models** for coding (DeepSeek V4 Pro / Claude Sonnet 4)
- Exception: Code reading/analysis only (no modifications) → Flash allowed
- **Manage agents well** = Kora's #1 priority

## 9.1 Hard Rule: Coding Tasks → Pro Model ONLY

> **Rule established by:** Boss Osmo
> **Date:** 2026-05-27

### ဒီ Rule က ဘာလို့လဲ?

Coding task တွေအတွက် **Pro model (DeepSeek V4 Pro)** ကိုပဲ သုံးရမယ်။ Flash model ကို **လုံးဝ** မသုံးရဘူး။

| Task Type | Allowed Model | Forbidden Model |
|---|---|---|
| Code generation | ✅ DeepSeek V4 Pro | ❌ DeepSeek V4 Flash |
| Code review | ✅ Claude Sonnet 4 | ❌ DeepSeek V4 Flash |
| Code bug fix | ✅ DeepSeek V4 Pro / Claude Sonnet 4 | ❌ DeepSeek V4 Flash |
| Research for code | ✅ Grok 4.3 | ❌ DeepSeek V4 Flash |
| **Non-coding** (reply, explain, read) | ✅ DeepSeek V4 Flash (main) | Allowed |

### Implementation

```python
# sessions_spawn() for coding → ALWAYS use Pro:
sessions_spawn(
    task="...",
    model="deepseek/deepseek-v4-pro",  # ✅ Pro only!
    context="isolated",
    runTimeoutSeconds=600
)

# NEVER do this for coding:
sessions_spawn(
    task="...",
    model="deepseek/deepseek-v4-flash",  # ❌ NO! Flash for coding!
    ...
)
```

### Why?
- **DeepSeek V4 Flash** = cheap, fast, good for chat/explain/lookup but **not precise enough for code**
- **DeepSeek V4 Pro** = slower, pricier, but **produces production-ready code** with correct syntax, imports, and logic
- Pro model ကို coding အတွက်သုံးမှ code quality ကောင်းမယ်၊ error တွေနည်းမယ်

### Exception
- Code **reading/analysis only** (no writing) → Flash allowed
- Code **review** (already written code) → Claude Sonnet 4 or DeepSeek V4 Pro


## 9. Security Notes

- **API Keys** — ဘယ် sub-agent ကိုမှ raw API key မပေးပါနဲ့
- **File Paths** — Path mapping သုံးပြီး obfuscate လုပ်ပါ
- **SSH Access** — Sub-agent တွေက secret key တွေကို တိုက်ရိုက်မသုံးပါစေနဲ့
- **Credentials** — `secrets_map.json` ကနေပဲ လှမ်းညွှန်းပါ (တန်ဖိုးမပေးပါ)

---

## 11. Example Workflow (Real Scenario)

**Scenario:** PS VIBE Sales Bot Refactored Version ကို Deploy လုပ်မယ်

```
1. Kora (Main) က Task ကို ပိုင်းခြားတယ်
   ├── Code review လုပ်ဖို့ → Sub-agent မွေးမယ်
   └── Deploy script ရေးဖို့ → နောက် Sub-agent တစ်ခု

2. COORDINATION.md ကို VPS ပေါ်မှာတည်ဆောက်တယ်
   ├── File paths တွေကို define လုပ်တယ်
   ├── Rules တွေချမှတ်တယ်
   └── Agent တစ်ယောက်ချင်းစီရဲ့ တာဝန်ကိုသတ်မှတ်တယ်

3. Sub-agent A (Reviewer) ကို spawn လုပ်တယ်
   ├── Model: Claude Sonnet 4 (error တွေ့ဖို့)
   ├── Task: Check refactored code for import bugs
   └── Timeout: 5 min

4. sessions_yield() — စောင့်တယ်

5. Sub-agent A ပြီးရင် result ကို AGENT_STATUS.md မှာရေးတယ်

6. Kora က result တွေကိုစုပြီး Boss ကို Report ပြန်ပေးတယ်
```

---

## 11. Full Workflow: From Task to Deployment

```
[Boss requests] → [Task arrives at Kora]
                         │
                   1. Analyze Task
                   2. Plan sub-agents needed
                         │
                         ▼
              ✏️  Write INTERFACE SPEC
                 - Function names (exact!)
                 - Module structure (exact!)
                 - Import paths (exact!)
                 - Naming convention
                 - Who writes what
                         │
                         ▼
              ✅ Verify Interface Spec Checklist
                         │
                         ▼
              🚀 Spawn Sub-agents (parallel)
                    ├── Agent A → writes file A
                    ├── Agent B → writes file B
                    └── Agent C → writes file C
                         │
                         ▼
              ⏳ sessions_yield() — wait for all
                         │
                         ▼
              🔍 Verify results against Interface Spec
                 - Function names match?
                 - Import paths work?
                 - No missing pieces?
                         │
                         ▼
              📋 Report to Boss in Burmese
                         │
                         ▼
              ✅ Done
```

---

## 12. Tools Reference

| Tool | Usage |
|---|---|
| `sessions_spawn()` | Sub-agent အသစ်မွေးဖွားဖို့ |
| `sessions_yield()` | Sub-agent ပြီးဖို့စောင့်ဖို့ |
| `subagents list` | Active sub-agents စစ်ဖို့ |
| `subagents kill` | Sub-agent ရပ်ဖို့ (လိုအပ်ရင်) |
| `write` / `read` | Shared files ရေးဖို့ / ဖတ်ဖို့ |
| `edit` | Shared files ပြင်ဆင်ဖို့ |

---

> **Note:** This guide is based on Kora's actual configuration and tools. 
> Agent-specific details (model names, API keys) may vary per environment.
> 
> **Golden Rule:** Interface Spec First! အရင်ရေးမှသာ Sub-agents ကို မွေးပါ။
