# Workflow Scan — 2026-06-02 13:02 UTC

## Summary
- Workflow/SOP files in scan scope: 7
- Additional SOPs found (not in scan list): 5
- Issues found: 20 (Critical: 4, Warning: 11, Info: 5)
- Scripts referenced that should exist (in `/root/coordination/`): ~18
- Local copies in workspace `memory/`: 8 (partial coverage)
- `/root/coordination/` on this sandbox: **DOES NOT EXIST**

---

## File-by-File Assessment

### 1. COORDINATION_FRAMEWORK.md
- **Status:** EXISTS — 18842 bytes
- **File modified:** 2026-05-31 09:19 UTC
- **Header claims:** v3.1, "Last updated: 2026-05-28 20:32 UTC"
- **Findings:**
  - ⚠️ **WARNING (STALE HEADER):** File was modified on May 31 but header says last updated May 28. The header wasn't updated after the last edit.
  - 🔴 **CRITICAL (FALSE CLAIMS):** Sections 8, 9, 10 describe `preflight.py`, `validate.py`, and `rollback.py` as "To be created" — these are marked HIGH priority but there is zero evidence they exist anywhere (no local copies, no VPS evidence, no SOPs).
  - 🔴 **CRITICAL (SILENT DEPRECATION):** The "Automated Tools (To Be Built)" table lists 7 tools (preflight, validate, rollback, log_completion, dep_graph, stale lock cleaner, batch backup) — none have SOPs or known implementations beyond conceptual code snippets in the doc itself.
  - ⚠️ **WARNING: `lock_manager.py`** is referenced extensively (acquire, release, check, force-release) with a full cron job spec, but the script has no dedicated SOP. Only `lock_monitor.py` exists locally (in workspace memory/).
  - ℹ️ **INFO:** The doc is comprehensive (18.8KB) and well-structured, covering spawn protocol, dependency rules, conflict resolution, and the findings system thoroughly.
  - ⚠️ **WARNING (CONTRADICTION):** Section 7 says "config limit: maxConcurrent=25" — but SPAWN_PROTOCOL.md says the hard limit is 5 per session. These numbers differ by 5x.

### 2. DISPATCH_MANAGER_SOP.md
- **Status:** EXISTS — 7588 bytes
- **File modified:** 2026-05-28 19:41 UTC
- **Header claims:** v1.0
- **Findings:**
  - ✅ **CLEAN:** SOP is well-structured with mission, boundaries, SOP steps, edge cases, and quick reference.
  - ⚠️ **WARNING (REFERENCED SCRIPT):** The SOP says the script lives at `/root/coordination/dispatch_manager.py`. A local copy exists at `memory/dispatch_manager.py` (8767 bytes), but not at the expected path on this sandbox. The VPS may have it.
  - ⚠️ **WARNING (DEAD REFERENCE):** The auto-flow diagram references a "Findings Manager" that runs `merge_findings.py` — `merge_findings.py` DOES exist locally in `memory/` (6807 bytes, 2026-05-28), but is expected at `/root/coordination/merge_findings.py` on VPS. No way to verify from this sandbox.
  - ℹ️ **INFO:** SOP is self-consistent with the COORDINATION_FRAMEWORK's findings system design.

### 3. SPAWN_PROTOCOL.md
- **Status:** EXISTS — 12185 bytes
- **File modified:** 2026-05-28 21:41 UTC (no version)
- **Findings:**
  - 🔴 **CRITICAL (SLOT LIMIT CONTRADICTION):** States "Hard Limit: 5 sub-agents per session — the gateway has a hard-coded per-session limit of 5 (cannot be changed)" — but COORDINATION_FRAMEWORK.md section 7 says "maxConcurrent=25, subagents.maxConcurrent=25, maxChildrenPerAgent=20". Severe contradiction that could cause spawn failures.
  - ⚠️ **WARNING (SCRIPT REFERENCES):** References `memory/kora_spawn.py` and `memory/subagent_ctl.py` for registration and task tracking — both DO exist locally. Good.
  - ⚠️ **WARNING (ORPHAN FILES?):** References SPAWNING_MANAGER_SOP.md, TASK_PLANNER_SOP.md, VERIFY_AGENT_SOP.md, GIT_SYNC_SOP.md, STATUS_REPORTER_SOP.md, DEPLOY_MANAGER_SOP.md — ALL exist in `memory/`. Good.
  - ⚠️ **WARNING (LOCK MANAGER):** References `lock_manager.py` at `/root/coordination/` extensively. No local copy, no SOP for it. Only `lock_monitor.py` exists.
  - ℹ️ **INFO:** Good Safety Net section — every spawn task must end with `=== RESULT: OK ||| ERROR: ===`.
  - ⚠️ **WARNING (AUTO-SPLIT RULE):** The 3-minute trigger for auto-splitting is aggressive and has no SOP of its own.

### 4. delegation-rules.md
- **Status:** EXISTS — 4687 bytes
- **File modified:** 2026-06-02 12:46 UTC
- **Findings:**
  - ✅ **CLEAN:** Most recently updated of all workflow files. Reflects current helper model selections and integration with the workflow system.
  - ⚠️ **WARNING (WORKFLOW ENGINE):** References `/root/coordination/workflow_engine.py` with 4 pipeline modes (quality, full-audit, safe-fix, auto-deploy) — but there is no evidence of this script existing locally, and no SOP for it. Similarly, `quality_gate.py` and `fix_protocol.py` are referenced in TOOLS.md but have no SOPs.
  - ℹ️ **INFO:** Good "What Kora NEVER Does" section that prevents manual code editing.
  - ℹ️ **INFO:** Model selections table (Flash vs Pro) is up-to-date and matches other SOPs.

### 5. VERIFY_AGENT_SOP.md
- **Status:** EXISTS — 7907 bytes
- **File modified:** 2026-05-28 19:46 UTC
- **Header claims:** v1.0
- **Findings:**
  - ✅ **CLEAN:** Well-structured SOP with clear mission, boundaries, and the golden Fix→Verify Loop (max 3 retries).
  - ⚠️ **WARNING (SCRIPT PATH):** Script at `/root/coordination/verify_agent.py` — local copy exists at `memory/verify_agent.py` (11333 bytes, 2026-05-28). May or may not be deployed to VPS.
  - ⚠️ **WARNING (VERIFICATION SCOPE):** The verification checks (compile, imports, services, logs, integrity) are comprehensive but rely on VPS-only commands (`systemctl`, `journalctl`, `from bot import *`). Cannot be run from the workspace sandbox.
  - ℹ️ **INFO:** The SOP correctly handles edge cases (file missing, import test failing due to env vars, service down, etc.)

### 6. FINDINGS_MANAGER_SOP.md
- **Status:** EXISTS — 6388 bytes
- **File modified:** 2026-05-28 19:22 UTC
- **Header claims:** v1.0
- **Findings:**
  - ✅ **CLEAN:** Clear single-purpose SOP. Correctly enforces the golden rule (no direct writes to SHARED_FINDINGS.md).
  - ✅ **GOOD:** References only `merge_findings.py` for writes — consistent with the framework.
  - ⚠️ **WARNING (SCRIPT):** Primary script at `/root/coordination/findings_manager.py` — local copy exists as `memory/findings_manager_agent.py` (4912 bytes, 2026-05-28). The naming mismatch (findings_manager.py vs findings_manager_agent.py) between SOP and actual file could cause confusion.
  - ⚠️ **WARNING (DEPENDENCY):** Relies on `merge_findings.py` at `/root/coordination/merge_findings.py` — local copy exists at `memory/merge_findings.py`. If VPS doesn't have it, the entire findings system breaks.
  - ℹ️ **INFO:** 120s timeout is tight but reasonable for a simple file merge script.

### 7. AGENTS.md
- **Status:** EXISTS — 7038 bytes
- **File modified:** 2026-06-02 12:45 UTC
- **Findings:**
  - ✅ **CLEAN:** Current, well-maintained workspace guide. Updated today.
  - ⚠️ **WARNING (GOLDEN_RULES.md):** References `GOLDEN_RULES.md` ("See GOLDEN_RULES.md") — file exists at workspace root (2925 bytes, 2026-05-31). ✅ Verified.
  - ⚠️ **WARNING (SPAWN PROTOCOL REFERENCE):** Points to `memory/SPAWN_PROTOCOL.md` for spawn rules. This file was also scanned — no contradictions found between AGENTS.md and SPAWN_PROTOCOL.md.
  - ✅ **GOOD:** References `POST_TASK_SOP.md` which exists at workspace root (1699 bytes).
  - ℹ️ **INFO:** Security rules about credentials and secrets_map.json are clear.

---

## Cross-File Issues

### 🔴 CRITICAL: Contradictory Sub-agent Limits

| Source | Stated Limit |
|--------|-------------|
| `COORDINATION_FRAMEWORK.md` §7 | ≤15 safe, 16-18 caution, 19+ halt. Config: maxConcurrent=25 |
| `SPAWN_PROTOCOL.md` | "Hard Limit: 5 sub-agents per session (cannot be changed)" |

**Impact:** If the true limit is 5 (as SPAWN_PROTOCOL asserts), spawning 6+ agents in parallel will silently fail. The framework's "≤15 safe" guidance would cause over-spawn errors.

### 🔴 CRITICAL: `/root/coordination/` Script Ecosystem Has Large Gaps

**Scripts with NO evidence of existence (neither local copy, nor SOP):**
| Script | Where Referenced | Priority in Framework |
|--------|-----------------|----------------------|
| `preflight.py` | COORDINATION_FRAMEWORK §8 | 🔴 HIGH (To Be Built) |
| `validate.py` | COORDINATION_FRAMEWORK §9 | 🔴 HIGH (To Be Built) |
| `rollback.py` | COORDINATION_FRAMEWORK §10 | 🔴 HIGH (To Be Built) |
| `lock_manager.py` | SPAWN_PROTOCOL, COORDINATION_FRAMEWORK | 🔴 HIGH |
| `log_completion.py` | COORDINATION_FRAMEWORK §2 | 🟡 MEDIUM |
| `dep_graph.py` | COORDINATION_FRAMEWORK §3 | 🟢 LATER |
| `workflow_engine.py` | TOOLS.md, delegation-rules.md | Active use |
| `quality_gate.py` | TOOLS.md | Active use |
| `fix_protocol.py` | TOOLS.md | Active use |
| `auto_doc_updater.py` | TOOLS.md | Active use |
| `check_alerts.py` | TOOLS.md | Active use |
| `dashboard.py` | TOOLS.md | Active use |
| `tool_orchestrator.py` | TOOLS.md | Active use |
| `git_sync_agent.py` | SPAWN_PROTOCOL | Active use |
| `status_reporter.py` | SPAWN_PROTOCOL | Active use |
| `deploy_manager.py` | SPAWN_PROTOCOL | Active use |

**Known local workspace copies (in `memory/`):**
| File | Size | Date |
|------|------|------|
| `dispatch_manager.py` | 8767B | 2026-05-28 |
| `spawning_manager.py` | 11676B | 2026-05-28 |
| `task_planner.py` | 24201B | 2026-05-28 |
| `findings_manager_agent.py` | 4912B | 2026-05-28 |
| `merge_findings.py` | 6807B | 2026-05-28 |
| `verify_agent.py` | 11333B | 2026-05-28 |
| `kora_spawn.py` | 6071B | 2026-05-28 |
| `subagent_ctl.py` | 12102B | 2026-05-28 |

**NOTE:** The gap between "To Be Built" (never deployed) and "Active use" scripts (referenced in TOOLS.md but may not be deployed) is concerning. Without VPS access, we cannot confirm which scripts actually exist on the server.

### ⚠️ WARNING: Inconsistent Timestamps in Framework Header

`COORDINATION_FRAMEWORK.md` claims "Last updated: 2026-05-28 20:32 UTC" but the actual file modification date is **2026-05-31 09:19 UTC** — a 3-day gap where the header was not updated. This suggests either:
- An edit was made without updating the version header, or
- The file was touched without meaningful changes

### ⚠️ WARNING: Naming Inconsistency — findings_manager_agent.py

- SOP says: `/root/coordination/findings_manager.py`
- Local file is: `memory/findings_manager_agent.py`
- If the VPS has it as `findings_manager.py` and not `findings_manager_agent.py`, the workspace copy has a different name than the deployed version.

### ℹ️ INFO: SOPs Are Flash-Model-Only — Good Consistency

All agent SOPs (Dispatch, Verify, Findings, Task Planner, Spawning Manager) consistently specify `deepseek/deepseek-v4-flash` as the model, while fix agents use `deepseek/deepseek-v4-pro`. This is consistent across delegation-rules.md and all individual SOPs.

### ℹ️ INFO: Safety Net Pattern Is Universal

The `=== RESULT: OK ||| ERROR: <reason> ===` safety net pattern is referenced in AGENTS.md, SPAWN_PROTOCOL.md, and delegation-rules.md — good cross-document consistency.

---

## Missing SOPs

These agents/scripts are referenced in the workflow but have NO dedicated SOP:

| Missing SOP | Referenced In |
|-------------|---------------|
| `LOCK_MANAGER_SOP.md` | COORDINATION_FRAMEWORK, SPAWN_PROTOCOL (lock_manager.py) |
| `PREFLIGHT_SOP.md` | COORDINATION_FRAMEWORK §8 (preflight.py) |
| `VALIDATE_SOP.md` | COORDINATION_FRAMEWORK §9 (validate.py) |
| `ROLLBACK_SOP.md` | COORDINATION_FRAMEWORK §10 (rollback.py) |
| `WORKFLOW_ENGINE_SOP.md` | TOOLS.md, delegation-rules.md (workflow_engine.py) |
| `QUALITY_GATE_SOP.md` | TOOLS.md (quality_gate.py) |
| `FIX_PROTOCOL_SOP.md` | TOOLS.md (fix_protocol.py) |
| `AUTO_DOC_UPDATER_SOP.md` | TOOLS.md (auto_doc_updater.py) |
| `TOOL_ORCHESTRATOR_SOP.md` | TOOLS.md (tool_orchestrator.py) |
| `DEPLOY_MANAGER_SOP.md` | EXISTS ✅ (was in scan-adjacent set) |
| `GIT_SYNC_SOP.md` | EXISTS ✅ |
| `STATUS_REPORTER_SOP.md` | EXISTS ✅ |
| `TASK_PLANNER_SOP.md` | EXISTS ✅ |
| `SPAWNING_MANAGER_SOP.md` | EXISTS ✅ |

**SOP coverage: 5 of ~15 referenced agents have SOPs** (33% coverage for agents; 0 scripts have their own SOP).

---

## Script Availability Check (on this sandbox)

| Script | Expected Path (VPS) | Local Copy in `memory/` | SOP Exists? |
|--------|---------------------|------------------------|-------------|
| `dispatch_manager.py` | `/root/coordination/` | ✅ 8767B | ✅ DISPATCH_MANAGER_SOP.md |
| `task_planner.py` | `/root/coordination/` | ✅ 24201B | ✅ TASK_PLANNER_SOP.md |
| `spawning_manager.py` | `/root/coordination/` | ✅ 11676B | ✅ SPAWNING_MANAGER_SOP.md |
| `findings_manager.py` | `/root/coordination/` | ⚠️ `findings_manager_agent.py` (name mismatch) | ✅ FINDINGS_MANAGER_SOP.md |
| `merge_findings.py` | `/root/coordination/` | ✅ 6807B | (Part of FINDINGS_MANAGER_SOP) |
| `verify_agent.py` | `/root/coordination/` | ✅ 11333B | ✅ VERIFY_AGENT_SOP.md |
| `kora_spawn.py` | (workspace) | ✅ 6071B | (Referenced in SPAWN_PROTOCOL) |
| `subagent_ctl.py` | (workspace) | ✅ 12102B | (Referenced in SPAWN_PROTOCOL) |
| `lock_monitor.py` | (workspace) | ✅ 24713B | ❌ No SOP |
| `subagent_safety.py` | (workspace) | ✅ 3092B | ❌ No SOP |
| `task_retry.py` | (workspace) | ✅ 2207B | ❌ No SOP |
| `preflight.py` | `/root/coordination/` | ❌ MISSING | ❌ (described in framework only) |
| `validate.py` | `/root/coordination/` | ❌ MISSING | ❌ (described in framework only) |
| `rollback.py` | `/root/coordination/` | ❌ MISSING | ❌ (described in framework only) |
| `lock_manager.py` | `/root/coordination/` | ❌ MISSING | ❌ |
| `log_completion.py` | `/root/coordination/` | ❌ MISSING | ❌ |
| `workflow_engine.py` | `/root/coordination/` | ❌ MISSING | ❌ |
| `quality_gate.py` | `/root/coordination/` | ❌ MISSING | ❌ |
| `fix_protocol.py` | `/root/coordination/` | ❌ MISSING | ❌ |
| `auto_doc_updater.py` | `/root/coordination/` | ❌ MISSING | ❌ |
| `check_alerts.py` | `/root/coordination/` | ❌ MISSING | ❌ |
| `dashboard.py` | `/root/coordination/` | ❌ MISSING | ❌ |
| `tool_orchestrator.py` | `/root/coordination/` | ❌ MISSING | ❌ |
| `git_sync_agent.py` | `/root/coordination/` | ❌ MISSING | ✅ GIT_SYNC_SOP.md |
| `status_reporter.py` | `/root/coordination/` | ❌ MISSING | ✅ STATUS_REPORTER_SOP.md |
| `deploy_manager.py` | `/root/coordination/` | ❌ MISSING | ✅ DEPLOY_MANAGER_SOP.md |

---

## Recommendations

### 🔴 Immediate (Fixes to avoid failures)

1. **Resolve the slot limit contradiction.** Determine the true per-session sub-agent limit. If it's 5, update COORDINATION_FRAMEWORK.md §7 to match. If it's 25, update SPAWN_PROTOCOL.md. This is the most dangerous contradiction — it can cause silent spawn failures.

2. **SSH into VPS and audit `/root/coordination/`.** Determine which scripts actually exist. Update TOOLS.md, SOPs, and framework docs to match reality. Mark "To Be Built" scripts clearly — don't let them masquerade as existing tools.

3. **If lock_manager.py doesn't exist on VPS, build it or remove references.** The entire pre-spawn lock protocol depends on it. Alternatively, confirm whether the lock system is actually being used or has been abandoned.

4. **Create SOPs for preflight.py, validate.py, rollback.py, and lock_manager.py** or explicitly mark them as deprecated and document the alternative workflow.

### 🟡 Medium (Quality improvements)

5. **Fix COORDINATION_FRAMEWORK.md header.** Update the "Last updated" date to match the actual file modification date (2026-05-31).

6. **Rename `findings_manager_agent.py` to `findings_manager.py`** to match the SOP naming, or update the SOP to reference the correct name.

7. **Create a `LOCK_MANAGER_SOP.md`** for lock_manager.py (or lock_monitor.py) — the lock system is central to the framework but has no standalone SOP.

8. **Audit the "To Be Built" script list.** Of the 7 tools listed in COORDINATION_FRAMEWORK §3, have any been built? If so, update the section. If not, create a timeline or remove stale references.

9. **Review the auto-split 3-minute trigger.** This is aggressive and should have its own SOP or at least be documented more thoroughly.

### 🟢 Nice-to-Have

10. **Create SOPs for TOOLS.md scripts** — `workflow_engine.py`, `quality_gate.py`, `fix_protocol.py`, `auto_doc_updater.py`, `tool_orchestrator.py`, `check_alerts.py`, `dashboard.py` all appear in TOOLS.md as active commands but have no SOPs.

11. **Add a cross-reference matrix** in COORDINATION_FRAMEWORK.md linking each referenced script to its SOP and implementation file.

12. **Consolidate SPAWN_PROTOCOL.md and the spawn decision tree from COORDINATION_FRAMEWORK.** They overlap significantly; one could reference the other to reduce duplication.

---

## Appendix: Referenced Files (Cross-Check)

| Referenced File | Path | Status |
|----------------|------|--------|
| AGENTS.md | `workspace/AGENTS.md` | ✅ Scanned |
| GOLDEN_RULES.md | `workspace/GOLDEN_RULES.md` | ✅ Exists (not scanned) |
| SOUL.md | `workspace/SOUL.md` | ✅ Exists (not scanned) |
| USER.md | `workspace/USER.md` | ✅ Exists (not scanned) |
| POST_TASK_SOP.md | `workspace/POST_TASK_SOP.md` | ✅ Exists (not scanned) |
| HEARTBEAT.md | `workspace/HEARTBEAT.md` | ✅ Exists (not scanned) |
| TOOLS.md | `workspace/TOOLS.md` | (loaded in context) |
| MEMORY.md | `workspace/MEMORY.md` | (main session only) |
| SHARED_FINDINGS.md | `/root/coordination/SHARED_FINDINGS.md` | ❌ Not reachable (VPS only) |
| AGENT_LOCKS.md | (referenced, no path given) | ❌ Missing |
| AUDIT_REPORT_TEMPLATE.md | `memory/AUDIT_REPORT_TEMPLATE.md` | ✅ Exists (not scanned) |
| TASK_PLANNER_SOP.md | `memory/TASK_PLANNER_SOP.md` | ✅ Exists (not in scan list) |
| SPAWNING_MANAGER_SOP.md | `memory/SPAWNING_MANAGER_SOP.md` | ✅ Exists (not in scan list) |
| GIT_SYNC_SOP.md | `memory/GIT_SYNC_SOP.md` | ✅ Exists (not in scan list) |
| STATUS_REPORTER_SOP.md | `memory/STATUS_REPORTER_SOP.md` | ✅ Exists (not in scan list) |
| DEPLOY_MANAGER_SOP.md | `memory/DEPLOY_MANAGER_SOP.md` | ✅ Exists (not in scan list) |
