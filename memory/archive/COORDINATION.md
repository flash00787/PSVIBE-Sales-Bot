# Kora Agent Coordination Protocol

> ⚠️ **DEPRECATED (2026-05-30)** — This is the old V1 multi-agent coordination protocol.
> The current system uses 25 tools at `/root/coordination/` with Workflow Engine, Task Bridge, and Hybrid Batch execution.
> This file is kept for historical reference (referenced by SUBAGENTS_COORDINATION.md).
> **Do NOT use this protocol for new work.**

## Rules (MUST FOLLOW) [LEGACY]

1. **Interface spec first** — Before spawning any sub-agent, `COORDINATION.md` and `path_mapping.json` MUST exist and be up to date.
2. **No raw paths** — All file/directory paths MUST use the obfuscated keys from `path_mapping.json`. Agents NEVER reference raw absolute paths.
3. **Function names** — Agent A → Agent B communication uses explicitly defined function names from this file. No ad-hoc naming.
4. **TASK.md** — Agent B (Coder/Executor) MUST follow TASK.md exactly. No deviations, no scope creep.
5. **AGENT_STATUS.md** — Each agent MUST write its completion status (PASS/FAIL + notes) immediately after finishing.
6. **Fail fast** — Use flash model + high timeout (10m for code-gen). No retries on timeout.
7. **Narrow scope** — Keep code-writing agents focused on one thing only. Avoid scope expansion.
8. **Coordination files are shared** — All agents read/write to the same COORDINATION.md, AGENT_STATUS.md, and path_mapping.json.

## Shared Storage Location

```
/root/.coordination/        ← Shared coordination directory on VPS
├── COORDINATION.md         ← This file (interface spec + rules)
├── path_mapping.json       ← Obfuscated path mappings
├── AGENT_STATUS.md         ← Completion tracking
└── TASK.md                 ← Current task brief (created per-task)
```

## Agent Roles

| Role | Model | Responsibility |
|------|-------|----------------|
| **Orchestrator** | flash-model | Creates TASK.md, spawns agents, monitors AGENT_STATUS.md |
| **Coder** | `deepseek/deepseek-v4-pro` | Writes/modifies code per TASK.md |
| **Reviewer/Fixer** | `anthropic/claude-sonnet-4-20250514` | Debugs code errors that Coder can't solve |
| **Researcher** | `x-ai/grok-4-3` | Researches libraries/updates before coding |

## Defined Interface Functions

These are the ONLY function names agents use to communicate results:

| Function | Direction | Purpose |
|----------|-----------|---------|
| `task_assigned(task_id)` | Orchestrator → Coder | Signals new task in TASK.md |
| `code_complete(status, notes)` | Coder → Orchestrator | Code written, status=PASS/FAIL |
| `review_needed(file_path, error)` | Coder → Reviewer | Code error, needs review/fix |
| `review_complete(status, fix_notes)` | Reviewer → Orchestrator | Review done |
| `research_needed(query)` | Coder → Researcher | Needs library/API research |
| `research_complete(findings)` | Researcher → Coder | Research results |
| `deploy_requested(target)` | Orchestrator → Deployer | Deploy to target directory |
| `deploy_complete(status)` | Deployer → Orchestrator | Deploy done |

## Agent Workflow

```
Orchestrator ──task_assigned──→ Coder
                                  │
                     ┌────────────┼────────────┐
                     ▼            ▼            ▼
             code_complete   review_needed  research_needed
                     │            │            │
                     │            ▼            ▼
                     │     Reviewer      Researcher
                     │            │            │
                     │     review_complete  research_complete
                     │            │            │
                     └────────────┴────────────┘
                              │
                              ▼
                     deploy_requested
                              │
                              ▼
                        Deployer
                              │
                              ▼
                      deploy_complete
```

## TASK.md Format

```markdown
# Task: <task_id>

## Objective
<clear one-sentence objective>

## Scope
- <task boundaries>
- <what NOT to do>

## Deliverables
- <file 1> → <path mapping key>
- <file 2> → <path mapping key>

## Verification
- <how to verify success>
- <expected output>
```

## AGENT_STATUS.md Entry Format

```markdown
## Agent: <role> — <timestamp>

**Task:** <task_id>
**Status:** PASS | FAIL
**Notes:** <summary>
**Files changed:** <list>
```
