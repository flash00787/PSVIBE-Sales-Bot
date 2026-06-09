# Memory System Scan — 2026-06-02 13:02 UTC

## Summary
- **Total files:** 78 (memory/ = 70 files, root workspace = 5 relevant files, archive/ = 9 files)
- **Total size:** ~1.2 MB (`memory/` directory)
- **Issues found:** 18 (Critical: 2, Warning: 8, Info: 8)

---

## File Inventory

### Workspace Root (Key System Files)
| File | Size | Last Modified | Status |
|------|------|--------------|--------|
| `AGENTS.md` | 7.0K | Jun 2 12:45 | ✅ Current |
| `SOUL.md` | 5.6K | Jun 2 12:46 | ✅ Current |
| `USER.md` | 1.8K | May 30 12:56 | ⚠️ Stale (3 days) |
| `TOOLS.md` | 2.2K | — | ⚠️ Has redacted API key patterns |
| `MEMORY.md` | ~2.3K | — | ⚠️ Refers to missing `memory/daily/` |
| `GOLDEN_RULES.md` | — | — | ✅ Exists |
| `POST_TASK_SOP.md` | — | — | ✅ Exists |
| `PROJECT_STRUCTURE.md` | — | — | ✅ Exists |
| `HEARTBEAT.md` | — | — | ✅ Exists |
| `BOOTSTRAP.md` | — | — | ✅ DELETED (as required) |

### Daily Logs (`memory/`)
| File | Size | Date | Status |
|------|------|------|--------|
| `2026-05-26.md` | 2.4K | May 27 | ✅ |
| `2026-05-27.md` | 1.2K | May 27 | ✅ |
| `2026-05-28.md` | 5.4K | May 28 | ✅ |
| `2026-05-29.md` | 12.5K | May 29 | ✅ |
| `2026-05-30.md` | 1.8K | May 30 | ✅ |
| `2026-05-31.md` | 14.8K | May 31 | ✅ |
| `2026-06-01.md` | 12.2K | Jun 1 | ✅ |
| `2026-06-02.md` | 2.9K | Jun 2 | ✅ |

### Module Files (`memory/`) — Reference Data
| File | Size | Last Mod | Status |
|------|------|----------|--------|
| `contacts.md` | 1.1K | Jun 2 | ✅ Current |
| `emails.md` | 0.7K | Jun 2 | ✅ Current |
| `infrastructure.md` | 2.1K | Jun 2 | ✅ Current |
| `config.md` | 1.2K | Jun 2 | ✅ Current |
| `project-state.md` | 2.2K | Jun 2 | ✅ Current |
| `bug-patterns.md` | 3.5K | Jun 2 | ✅ Current |
| `lessons.md` | 2.9K | Jun 2 | ✅ Current |
| `fix-history.md` | 2.3K | Jun 2 | ✅ Current |
| `heartbeat-procedures.md` | 5.3K | Jun 2 | ✅ Current |
| `tools-commands.md` | 4.6K | Jun 2 | ✅ Current |
| `memory-usage-guide.md` | 4.4K | Jun 2 | ✅ Current |
| `psvibe-code-structure.md` | 2.6K | Jun 2 | ✅ Current |
| `delegation-rules.md` | 4.7K | Jun 2 | ✅ Current |

### Session Tracking (`memory/`)
| File | Size | Last Mod | Status |
|------|------|----------|--------|
| `session-memory.md` | 0.7K | May 30 | ⚠️ Stale (last updated May 30) |
| `session-tracker-last.md` | 0.2K | May 28 | ⚠️ Stale (last updated May 28) |
| `agent-status.md` | 0.2K | Jun 2 | ✅ Current (shows no active tasks) |
| `active_tasks.json` | 34B | May 28 | ✅ Clean (empty) |
| `heartbeat-state.json` | 88B | Jun 2 | ✅ Current |

### Scripts in `memory/` (Technical/Operational)
| File | Size | Notes |
|------|------|-------|
| `consolidator.py` | 10.4K | ✅ Code |
| `daily_digest.py` | 13.5K | ✅ Code |
| `git_backup.py` | 7.7K | ✅ Code |
| `heartbeat_routine.py` | 9.1K | ✅ Code |
| `knowledge_graph.py` | 26.5K | ✅ Code |
| `memory_index.py` | 10.3K | ✅ Code |
| `memory_maintenance.py` | 13.7K | ⚠️ Orphaned? (no HEARTBEAT.md ref) |
| `memory_pruner.py` | 24.7K | ✅ Code |
| `priority_engine.py` | 14.3K | ✅ Code |
| `session_summary.py` | 5.0K | ✅ Code |
| `session_tracker.py` | 1.7K | ✅ Code |
| `session_start.py` | 1.2K | ✅ Code |
| `boot_protocol.py` | 10.2K | ✅ Code |
| `lock_monitor.py` | 24.7K | ✅ Code |
| `kora_spawn.py` | 6.1K | ✅ Code |
| `spawning_manager.py` | 11.7K | ✅ Code |
| `dispatch_manager.py` | 8.8K | ✅ Code |
| `findings_manager_agent.py` | 4.9K | ✅ Code |
| `verify_agent.py` | 11.3K | ✅ Code |
| `task_planner.py` | 24.2K | ✅ Code |
| `task_retry.py` | 2.2K | ✅ Code |
| `subagent_ctl.py` | 12.1K | ✅ Code |
| `subagent_safety.py` | 2.9K | ✅ Code |
| `merge_findings.py` | 6.8K | ⚠️ Orphaned (no direct SOP ref) |
| `cleanup_session_locks.sh` | 2.0K | ✅ Script |
| `smart_session_cleanup.sh` | 2.4K | ✅ Script |

### Specification / SOP Files in `memory/`
| File | Size | Notes |
|------|------|-------|
| `SPAWN_PROTOCOL.md` | 12.2K | SOP |
| `HELPER_GUIDELINES.md` | 15.5K | SOP |
| `COORDINATION_FRAMEWORK.md` | 18.8K | SOP |
| `DEPLOY_MANAGER_SOP.md` | 3.2K | SOP |
| `DISPATCH_MANAGER_SOP.md` | 7.6K | SOP |
| `FINDINGS_MANAGER_SOP.md` | 6.4K | SOP |
| `GIT_SYNC_SOP.md` | 2.1K | SOP |
| `SPAWNING_MANAGER_SOP.md` | 6.8K | SOP |
| `STATUS_REPORTER_SOP.md` | 2.1K | SOP |
| `TASK_PLANNER_SOP.md` | 8.9K | SOP |
| `VERIFY_AGENT_SOP.md` | 7.9K | SOP |
| `IMPLEMENTATION_LOG.md` | 2.5K | ⚠️ Spec log (from Phase 2/3) |
| `PHASE3_SPEC.md` | 6.4K | ⚠️ Spec (Phase 3 spec doc) |
| `UPGRADE_SPEC.md` | 4.0K | ⚠️ Spec (Phase 2 spec doc) |
| `AUDIT_REPORT_TEMPLATE.md` | 2.4K | Template |
| `ARCHIVED_LESSONS.md` | 5.2K | ⚠️ Duplicate of lessons.md? |
| `integration-plan.md` | 9.9K | ⚠️ Stale? (May 28) |
| `test-report.md` | 3.7K | ⚠️ Specific test run, likely orphaned |

### Generated Data Files (`memory/`)
| File | Size | Notes |
|------|------|-------|
| `knowledge-graph.json` | 179K | ✅ Generated data |
| `memory-index.json` | 93K | ✅ Generated index |
| `subagent-journal.json` | 6.1K | ✅ Operational data |
| `active_tasks.json` | 34B | ✅ Operational (empty) |
| `heartbeat-state.json` | 88B | ✅ Operational |

### Archive (`memory/archive/`)
| File | Size | Notes |
|------|------|-------|
| `COORDINATION.md` | 4.6K | DEPRECATED |
| `ERROR_PATTERNS.md` | 6.3K | ✅ Archived |
| `KNOWLEDGE_INDEX.md` | 4.8K | ✅ Archived |
| `MASTER_INVENTORY.md` | 14.5K | ✅ Archived |
| `MEMORY_FULL_2026-05-29.md` | 32K | ✅ Archived (pre-split backup) |
| `MEMORY_backup_2026-06-02.md` | 16K | ✅ Recent backup |
| `OPS_REFERENCE.md` | 16K | ✅ Archived |
| `SUBAGENTS_COORDINATION.md` | 24K | ✅ Archived |
| `ps5_news.md` | 47K | ⚠️ Large archived news feed |

### Other (`memory/`)
| Item | Notes |
|------|-------|
| `digests/2026-05-28-digest.md` | ⚠️ Only 1 digest for 8 daily logs |
| `__pycache__/` | ⚠️ Python cache files (3 files) |
| `daily/` | ❌ **MISSING** — referenced in MEMORY.md & fix-history.md |
| `ARCHIVE.md` | ❌ **MISSING** — referenced in UPGRADE_SPEC.md |

---

## Findings

### 🔴 CRITICAL

#### C1. `MEMORY.md` references `memory/daily/` — directory does not exist
- **File:** `MEMORY.md` line: "`memory/2026-06-02.md` & `memory/daily/` — Raw daily logs"
- **Also in:** `fix-history.md` references `memory/daily/YYYY-MM-DD.md`
- **Impact:** Navigational dead-end for any agent following the path
- **Fix:** Either create `memory/daily/` and symlink/move daily logs there, or update references to point to `memory/` directly.

#### C2. API Key patterns in `TOOLS.md` expose key prefixes
- **File:** `TOOLS.md` shows `xai-...` and `sk-or-...` patterns
- **Impact:** While values are redacted, the key prefixes and locations (OpenRouter, xAI) are visible. If this file is ever shared or included in spawn context, it leaks credential structure.
- **Fix:** Move API key names to a restricted file (e.g., `secrets_map.json`) and reference only that.

### 🟡 WARNING

#### W1. `session-memory.md` is stale (last updated 2026-05-30)
- **File:** `memory/session-memory.md` — still shows "Workspace: Clean — 13 root .md files, ~330 stale files archived" and Quality Gate 100/100
- **Age:** 3 days stale
- **Impact:** Current state info is outdated; may lead to incorrect assumptions during session recovery
- **Fix:** Update or remove — this was the Phase 2 migration marker

#### W2. `session-tracker-last.md` is very stale (2026-05-28)
- **File:** `memory/session-tracker-last.md` — still shows a fix pipeline from May 28
- **Age:** 5 days stale
- **Impact:** No longer reflects current session state
- **Fix:** Update with latest session timestamp or remove

#### W3. Missing `memory/daily/` directory
- **File:** Referenced in `MEMORY.md` and `fix-history.md` but does not exist
- **Impact:** Broken navigation reference
- **Fix:** Create directory or remove references

#### W4. Missing `memory/ARCHIVE.md` (referenced in UPGRADE_SPEC.md)
- **File:** `UPGRADE_SPEC.md` mentions `memory/ARCHIVE.md` as target for pruned P2/P3 entries
- **Status:** Doesn't exist
- **Impact:** Pruner has no target for archived entries
- **Fix:** Create `memory/ARCHIVE.md` or remove references

#### W5. SOP/Spec files mixed with operational memory
- **Files:** 18+ spec/SOP/template files in `memory/` (H*_SOP.md, PHASE3_SPEC.md, etc.)
- **Impact:** Clutters the memory namespace; `memory_search` will return SOP results alongside actual memory
- **Recommendation:** Move to `memory/sop/` subdirectory

#### W6. Python cache files in `memory/__pycache__/`
- **Files:** 3 `.pyc` files (daily_digest, lock_monitor, memory_pruner)
- **Impact:** Cache files should not be in a memory/documentation directory
- **Fix:** Add to `.gitignore` and clean periodically

#### W7. Only 1 digest generated for 8 daily logs
- **File:** `memory/digests/` contains only `2026-05-28-digest.md` (189 bytes, nearly empty)
- **Impact:** Digest system not producing output regularly
- **Fix:** Run `daily_digest.py` for recent days or remove digests/ directory

#### W8. Orphaned/stale script files
- **Files:**
  - `memory/memory_maintenance.py` (13.7K) — no reference in HEARTBEAT.md or SOPs
  - `memory/merge_findings.py` (6.8K) — orphaned, no direct SOP reference  
  - `memory/test-report.md` (3.7K) — one-time test output, likely orphaned
  - `memory/integration-plan.md` (9.9K) — likely stale (May 28)
- **Impact:** Dead weight in memory directory; wastes `memory_search` resources

### 🔵 INFO

#### I1. `USER.md` last updated May 30 (3 days old)
- Still accurate content, but could be refreshed with any new Boss preferences

#### I2. `ARCHIVED_LESSONS.md` vs `lessons.md`
- **Files:** Both exist in `memory/`
- `ARCHIVED_LESSONS.md` (5.2K) — may contain duplicate/older lessons
- `lessons.md` (2.9K) — current lessons
- **Verify:** Cross-check for duplication; consider removing `ARCHIVED_LESSONS.md`

#### I3. `memory/archive/MEMORY_backup_2026-06-02.md` is very recent (today)
- **Size:** 16K — contains same content as MEMORY.md
- This is a legitimate backup, but note it was created today (June 2)
- Ensure the backup process doesn't create duplicates on every run

#### I4. `memory/archive/MEMORY_FULL_2026-05-29.md` (32K)
- Pre-split full MEMORY.md backup — good to have in archive
- No issues

#### I5. `memory/archive/ps5_news.md` (47K)
- Largest file in archive — raw PS5 news feed
- Consider whether this needs to be preserved in the memory system

#### I6. `fix-history.md` references `memory/daily/` incorrectly
- **Line:** "Full daily logs at `memory/daily/YYYY-MM-DD.md`"
- Should be `memory/YYYY-MM-DD.md` (no daily/ subdir)

#### I7. `HEARTBEAT.md` references `coordination/kora_health_monitor.py` — verify path
- Path shown: `/home/node/.openclaw/workspace/coordination/kora_health_monitor.py`
- This is a workspace-local path; the VPS `/root/coordination/` has the coordination tools
- Check if this file exists in both locations

#### I8. Memory module count is healthy
- 13 well-organized module files in `memory/` (contacts, emails, infrastructure, config, project-state, bug-patterns, lessons, fix-history, heartbeat-procedures, tools-commands, memory-usage-guide, psvibe-code-structure, delegation-rules)
- All updated on June 2 ✅
- `MEMORY.md` index is accurate for all module files

---

## Recommendations

### Immediate (High Priority)
1. **Fix MEMORY.md and fix-history.md** to remove references to nonexistent `memory/daily/` directory
2. **Create `memory/daily/`** directory (empty, for future use) OR update all references to point to `memory/`
3. **Update `session-memory.md`** with current state or archive it
4. **Update `session-tracker-last.md`** with latest session timestamp

### Short-term (Medium Priority)
5. **Move SOP/spec files** to `memory/sop/` subdirectory (SOPs, HELPER_GUIDELINES.md, COORDINATION_FRAMEWORK.md, spec docs, templates)
6. **Remove or update stale files:** `memory/test-report.md`, `memory/integration-plan.md`, `memory/memory_maintenance.py`, `memory/merge_findings.py`
7. **Create `memory/ARCHIVE.md`** for pruner output, or remove reference from UPGRADE_SPEC.md
8. **Add `__pycache__/` to `.gitignore`** (if git-tracked) and clean
9. **Cross-check `ARCHIVED_LESSONS.md` vs `lessons.md`** — consolidate and remove duplicate

### Long-term (Low Priority)
10. **Verify `coordination/kora_health_monitor.py`** exists at workspace path
11. **Consider `ps5_news.md` archiving strategy** — 47K in memory may be better served by a dedicated script
12. **Run `daily_digest.py`** for remaining 7 days or clean up digests/ dir
13. **Consider moving TOOLS.md API key references** to `secrets_map.json` pattern per AGENTS.md security rules
14. **Review all 24 Python scripts in memory/ for actual usage** — some may be superseded by VPS coordination tools

---

## MEMORY.md Index Verification

| Referenced File | Status | Notes |
|----------------|--------|-------|
| `GOLDEN_RULES.md` | ✅ | Exists |
| `POST_TASK_SOP.md` | ✅ | Exists |
| `HEARTBEAT.md` | ✅ | Exists |
| `AGENTS.md` | ✅ | Exists |
| `SOUL.md` | ✅ | Exists |
| `TOOLS.md` | ✅ | Exists |
| `PROJECT_STRUCTURE.md` | ✅ | Exists |
| `SPAWN_PROTOCOL.md` | ✅ | Exists (in memory/) |
| `memory/contacts.md` | ✅ | Exists |
| `memory/emails.md` | ✅ | Exists |
| `memory/infrastructure.md` | ✅ | Exists |
| `memory/config.md` | ✅ | Exists |
| `memory/psvibe-code-structure.md` | ✅ | Exists |
| `memory/project-state.md` | ✅ | Exists |
| `memory/heartbeat-procedures.md` | ✅ | Exists |
| `memory/tools-commands.md` | ✅ | Exists |
| `memory/memory-usage-guide.md` | ✅ | Exists |
| `memory/bug-patterns.md` | ✅ | Exists |
| `memory/lessons.md` | ✅ | Exists |
| `memory/fix-history.md` | ✅ | Exists |
| `memory/2026-06-02.md` | ✅ | Exists |
| `memory/daily/` | ❌ | **MISSING** — referenced but does not exist |
| `memory/archive/` | ✅ | Exists |

---

*Scan completed by Kora Memory Audit Subagent — 2026-06-02 13:02 UTC*
