# Agents Workflow Scan — 2026-06-02 13:03 UTC

## Summary
- **Registered helper agents (defined):** 9
- **SOPs documented:** 8 SOP files
- **Core framework files:** 5 (COORDINATION_FRAMEWORK, SPAWN_PROTOCOL, delegation-rules, SUBAGENTS_COORDINATION, GOLDEN_RULES)
- **Issues found:** 4
- **Active tasks currently:** 0 (idle)
- **Agent orchestrator:** Kora (DeepSeek V4 Flash — main model)

---

## Agent Inventory

### Primary Orchestrator
| Agent | Model | Role | Tools |
|-------|-------|------|-------|
| **Kora** | DeepSeek V4 Flash | Main orchestrator, communicator | Spawns/manages all helpers, reports to Boss |

### Helper Agents (Defined in SOPs / Coordination Docs)
| # | Helper | Model | Timeout | Script (VPS) | Purpose |
|---|--------|-------|---------|--------------|---------|
| 1 | 📐 **Task Planner** | Flash | 180s | `task_planner.py` | Decompose Boss tasks into modules |
| 2 | 🚀 **Spawning Manager** | Flash | 900s | `spawning_manager.py` | Preflight → Lock → Backup → Spawn → Validate → Release |
| 3 | 🎯 **Dispatch Manager** | Flash | 180s | `dispatch_manager.py` | Read PENDING findings → generate fix commands |
| 4 | 🤖 **Fix Agent (Coder)** | **Pro only** | 300-900s | _(spawned on-demand)_ | Code writing, debugging |
| 5 | 🔍 **Verify Agent** | Flash | 300s | `verify_agent.py` | Auto-verify after fix, quality gate |
| 6 | 📋 **Findings Manager** | Flash | 120s | `findings_manager.py` | Merge findings, clean stale entries |
| 7 | 🔄 **Git Sync Agent** | Flash | 120s | `git_sync_agent.py` | Commit + push |
| 8 | 📊 **Status Reporter** | Flash | 120s | `status_reporter.py` | Health check, daily report |
| 9 | 🎬 **Deploy Manager** | Flash | 300s | `deploy_manager.py` | Full release deploy + rollback |

### Specialized Fallback Models (Documented)
| Agent | Model | API Route | Cost Tier | Use Case |
|-------|-------|-----------|-----------|----------|
| 🐙 DeepSeek V4 Pro | Primary Coder | OpenClaw config | Low ($) | Code writing, debugging |
| 🔧 Claude Sonnet 4 | Reviewer/Fixer | OpenRouter (sk-or-v1-...) | Medium ($$) | Error fixing when Pro fails |
| 🔬 Grok 4.3 | Researcher | xAI (xai-...) | High ($$$) | Library search, research |

### Gateway Limits (From SPAWN_PROTOCOL.md)
| Setting | Value |
|---------|-------|
| Per-session sub-agent limit | **5** (hard-coded) |
| `session.writeLock.acquireTimeoutMs` | **300000** (5 min) [updated 2026-06-02] |
| `maxConcurrent` (config) | **25** |
| `maxChildrenPerAgent` (config) | **20** |
| `subagents.maxConcurrent` (config) | **25** |

> **Note:** Earlier docs reference "10 concurrent" (SUBAGENTS_COORDINATION.md §8) and "≤15 safe" (COORDINATION_FRAMEWORK §7 step 2). These may be outdated relative to the actual 5-slot gateway limit.

---

## SOP Coverage

### Existing SOPs (8 files in `memory/`)
| SOP File | Status | Last Updated | Completeness |
|----------|--------|-------------|--------------|
| ✅ `DISPATCH_MANAGER_SOP.md` | Documented | 2026-05-28 | Full — boundaries, flow, limitations |
| ✅ `SPAWNING_MANAGER_SOP.md` | Documented | 2026-05-28 | Full — multi-phase spawn pipeline |
| ✅ `FINDINGS_MANAGER_SOP.md` | Documented | 2026-05-28 | Full — merge protocol, golden rules |
| ✅ `VERIFY_AGENT_SOP.md` | Documented | 2026-05-28 | Full — checks, PASS/FAIL, retry loop |
| ✅ `TASK_PLANNER_SOP.md` | Documented | 2026-05-28 | Full — max module size, dependency rules |
| ✅ `STATUS_REPORTER_SOP.md` | Documented | 2026-05-28 | Partial detail (referenced by heartbeat) |
| ✅ `GIT_SYNC_SOP.md` | Documented | 2026-05-28 | Full — commit/push/full-sync commands |
| ✅ `DEPLOY_MANAGER_SOP.md` | Documented | 2026-05-28 | Full — pre-deploy, deploy, rollback |
| ✅ `HELPER_GUIDELINES.md` | Documented | 2026-05-29 | Full — ALLOW/DON'T ALLOW per agent |

### Missing SOPs (Requested in task, not found)
| Requested File | Status | Notes |
|----------------|--------|-------|
| ❌ `AGENT_DISPATCHER_SOP.md` | **MISSING** | Dispatch Manager SOP exists at `DISPATCH_MANAGER_SOP.md` (different filename) |
| ❌ `AGENT_DEVELOPER_SOP.md` | **MISSING** | No dedicated developer/Fix Agent SOP exists — coders spawned as sub-agents without standalone SOP |
| ❌ `AGENT_FIX_SOP.md` | **MISSING** | No dedicated fix SOP — fix procedure defined in COORDINATION_FRAMEWORK.md and SPAWN_PROTOCOL.md, plus `fix_protocol.py` |

### Fix Protocol Scripts (VPS coordination tools)
| Tool | Path | Purpose |
|------|------|---------|
| ✅ `fix_protocol.py` | `/root/coordination/fix_protocol.py` | --start (lock+snapshot) / --complete (verify+commit) |
| 🔶 `preflight.py` | `/root/coordination/preflight.py` | **Designed but status unclear** — referenced as TO-BE-BUILT in COORDINATION_FRAMEWORK |
| 🔶 `validate.py` | `/root/coordination/validate.py` | **Designed but status unclear** — referenced as TO-BE-BUILT |
| 🔶 `rollback.py` | `/root/coordination/rollback.py` | **Designed but status unclear** — referenced as TO-BE-BUILT |
| ✅ `lock_manager.py` | `/root/coordination/lock_manager.py` | Confirmed operational — referenced in SPAWN_PROTOCOL |
| ✅ `merge_findings.py` | `/root/coordination/merge_findings.py` | Confirmed operational |

---

## Known Issues (from `bug-patterns.md` & `archive/ERROR_PATTERNS.md`)

### Directly Agent-Related Issues
| # | Issue | Status | Severity |
|---|-------|--------|----------|
| 1 | **Parallel Agent Collision** — Multiple fix agents overwrote same function (`_fetch_games_from_mysql()`) in parallel | ✅ FIXED (Task Planner + lock manager) | 🔴 Critical |
| 2 | **6 parallel agents on `bot/__init__.py`** — 35+ bugs chain reaction (redundant globals, missing enums, duplicate functions) | ✅ FIXED (parallel ban on crown jewels) | 🔴 Critical |
| 3 | **chr() Encoding Corruption** — Auto-fix script replaced `d["nm_name"]` with `d[chr(39)+chr(110)+...]` generating literal `'nm_name'` keys | ✅ FIXED (always `ast.parse()` output) | 🔴 Critical |
| 4 | **Missing Comma in patch_routes.py** — SyntaxError → API crash loop (65+ restarts) | ✅ FIXED 2026-06-02 | 🔴 Critical |
| 5 | **API Key Mismatch After MySQL Migration** — 12 data key mismatches | ✅ FIXED 2026-06-02 | 🔴 Critical |

### Long-Standing (Not Yet Fixed)
| # | Issue | Status | Notes |
|---|-------|--------|-------|
| 1 | **Console ID URL Encoding** (`C - 01` with spaces not encoded) | ⏳ KNOWN | Falls back to gspread (slow) |
| 2 | **MySQL-GSheet Sync Deletion Gap** — Deleting GSheet doesn't delete MySQL | ⏳ KNOWN | n8n handles INSERT/UPDATE only |

---

## Workflow Assessment

### 1. Role Separation Between Agents

**Assessment: GOOD — clear separation with hard boundaries**

- **Each helper has a SINGLE responsibility** documented in a dedicated SOP
- ALL helpers are Flash-only (orchestration, not code) — Fix Agent is the only Pro model exception
- Universal DON'T-ALLOW rules in `HELPER_GUIDELINES.md` enforce: no modifying code, no spawning children, no direct SHARED_FINDINGS.md writes
- **Findings Manager** is the single writer for SHARED_FINDINGS.md — prevents collision
- The pipeline is **strictly linear**: Audit → Dispatch → Fix → Verify → Findings → Git → Deploy

**Minor concern:** Fix Agent (Pro coder) lacks a standalone SOP. Its behavior is defined implicitly across COORDINATION_FRAMEWORK.md and SPAWN_PROTOCOL.md rather than in a dedicated `AGENT_FIX_SOP.md` or `AGENT_DEVELOPER_SOP.md`.

### 2. Spawn Protocol Compliance

**Assessment: COMPREHENSIVE with some drift risks**

**Strengths:**
- Multi-step spawn pipeline documented in COORDINATION_FRAMEWORK §1-2 (Pre-flight → Backup → Lock → Spawn → Validate → Rollback → Release)
- Spawning Manager can automate the entire pipeline (SOP exists)
- Lock manager with stale-cleanup cron (every 30 min) prevents deadlocks
- All sub-agents require SAFETY NET ending marker
- Kill switch: per-session max 5 agents (prevents overwhelming gateway)
- Fix → Verify loop with max 3 retries

**Concerns (Drift Risks):**
1. **The gateway hard-limit is 5 per session** — older docs reference "10 concurrent" (SUBAGENTS_COORDINATION.md §8) and "≤15 safe" (COORDINATION_FRAMEWORK §7). These are misleading if the real limit is 5.
2. **Auto-Split Rule (3 min trigger)** — Documented but requires active monitoring. No automated watchdog script confirmed.
3. **preflight.py, validate.py, rollback.py** are described as "To Be Built" in COORDINATION_FRAMEWORK §3 but already referenced in SPAWN_PROTOCOL as active commands. Status unclear — may not exist on VPS yet.
4. **The Spawning Manager** wraps the full pipeline but requires a 3-phase spawn (Phase 1: spawning_manager.py → Phase 2: actual fix → Phase 3: spawning_manager validate). This is complex.

### 3. Delegation Clarity

**Assessment: EXCELLENT — the most mature part of the system**

- `delegation-rules.md` has a clear decision tree for every task type
- **Golden Rule #1**: "NEVER Manual Work — Zero Exceptions" (GOLDEN_RULES.md)
- **Golden Rule #2**: "Sub-Agent/Helper First" — every task spawns a helper
- **Golden Rule #5**: "NO Direct Code Editing" — Fix Agent (Pro) only
- 14 explicit task-to-helper mappings with model and timeout specifications
- Fallback chain documented: Pro → Claude Sonnet 4 → Grok 4.3 → Flash
- Helper guidelines per agent (ALLOW/DON'T ALLOW) are explicit

**Minor concern:** The `context="isolated"` flag mentioned in SUBAGENTS_COORDINATION.md §4 may not match current OpenClaw API (tool is `sessions_spawn` with `taskName`/`model`/`task` params, not `context`). Need to verify actual API compatibility.

### 4. Known Bug Patterns Relevant to Agent Workflow

**FIXED (should stay fixed due to safeguards):**
- Parallel collision on bot/__init__.py → Protected by lock manager + sequential-only rule
- Function name mismatch between agents → Protected by Interface Spec First protocol
- Direct SHARED_FINDINGS.md writes → Protected by single-writer pattern
- Code quality issues from Flash models → Protected by "Pro only for coding" rule
- Stale locks → Protected by 30-min cron cleanup

**STILL AT RISK:**
- Multiple agents targeting different parts of the same handler file could still conflict at function boundaries
- Auto-Split might create more agents than the 5-slot gateway limit can handle
- Interface Spec depends on Kora writing it correctly — no automated enforcement
- The Agent DISPATCH_MANAGER_SOP / AGENT_DEVELOPER_SOP / AGENT_FIX_SOP requested names don't exist (but functionally equivalent docs exist under different names)

### 5. Fallback Chain Documentation

**Assessment: FUNCTIONAL**

- Primary: DeepSeek V4 Flash (Kora main) for orchestration
- Coding: DeepSeek V4 Pro (primary) → Claude Sonnet 4 (fallback) via OpenRouter
- Research: Grok 4.3 via xAI API
- All API keys stored in secrets/TOOLS.md (never exposed to sub-agents)
- **Missing:** No documented retry/fallback strategy for when all 5 sub-agent slots are used AND a high-priority task arrives — the queue should handle this but `task_queue.json` doesn't currently exist (empty temp/ directory for the file)

---

## Recommendations

### 🔴 Critical Fixes

1. **Resolve slot limit discrepancy** — Update all docs (SUBAGENTS_COORDINATION.md, COORDINATION_FRAMEWORK.md, AGENTS.md) to reflect the actual gateway per-session limit of 5. Current references to "10 concurrent" and "≤15 safe" are outdated.

2. **Verify VPS scripts exist** — Check production status of `preflight.py`, `validate.py`, and `rollback.py` on the VPS. These are referenced as active commands in SPAWN_PROTOCOL.md but marked "To Be Built" in COORDINATION_FRAMEWORK.md §3.

3. **Create task_queue.json** — If a agent slot queue is intended (GOLDEN_RULES.md §7: "Slot Full → QUEUE"), ensure the implementation exists at `temp/task_queue.json`. Currently absent.

### 🟡 Improvements

4. **Create dedicated Fix Agent SOP** — The code-writing/Pro model sub-agent is the most critical actor. It deserves its own SOP (e.g., `AGENT_FIX_SOP.md`) with exact rules for file modification, Interface Spec adherence, and error handling.

5. **Audit old coordination docs** — `archive/COORDINATION.md` (deprecated 2026-05-30) uses `context="isolated"`, `path_mapping.json`, and `AGENT_STATUS.md` patterns that may not align with current tools. `archive/SUBAGENTS_COORDINATION.md` has similar drift. These should be annotated or pruned.

6. **Standardize SOP naming** — The task requested `AGENT_DISPATCHER_SOP.md` but the actual file is `DISPATCH_MANAGER_SOP.md`. While functionally equivalent, consistent naming (`*_SOP.md`) reduces confusion for future audits.

### 🟢 Nice-to-Haves

7. **Add automated slot watcher** — A cron or daemon that monitors sub-agent slots and auto-splits running agents >3 min, reducing manual oversight.

8. **Interface Spec automation** — Consider a template script or schema validation for Interface Spec files to reduce risk of human error when defining function contracts across agents.

---

## Files Referenced in This Scan

| File | Status |
|------|--------|
| `memory/SPAWN_PROTOCOL.md` | ✅ Read |
| `memory/delegation-rules.md` | ✅ Read |
| `memory/COORDINATION_FRAMEWORK.md` | ✅ Read |
| `memory/archive/SUBAGENTS_COORDINATION.md` | ✅ Read |
| `memory/archive/COORDINATION.md` | ✅ Read (deprecated) |
| `memory/bug-patterns.md` | ✅ Read |
| `memory/DISPATCH_MANAGER_SOP.md` | ✅ Read |
| `memory/SPAWNING_MANAGER_SOP.md` | ✅ Read |
| `memory/HELPER_GUIDELINES.md` | ✅ Read |
| `memory/GOLDEN_RULES.md` | ✅ Read |
| `memory/config.md` | ✅ Read |
| `memory/agent-status.md` | ✅ Read |
| `memory/archive/MASTER_INVENTORY.md` | ✅ Read |
| `memory/kora_spawn.py` | ✅ Verified |
| `memory/subagent_ctl.py` | ✅ Verified |
| `AGENTS.md` | ✅ Read (in startup context) |
| `TOOLS.md` | ✅ Read (in startup context) |
| `POST_TASK_SOP.md` | ✅ Read |
| `memory/AGENT_DISPATCHER_SOP.md` | ❌ Not found |
| `memory/AGENT_DEVELOPER_SOP.md` | ❌ Not found |
| `memory/AGENT_FIX_SOP.md` | ❌ Not found |
