# Archived Lessons

Historical/verbose lessons archived from MEMORY.md to keep the working file lean.

---

## 🚀 Hybrid Batch Execution (Archived 2026-05-30)

**Pattern:** Parallel batch execution — multiple Fix Agents spawning on independent files simultaneously.

### Why:
- Sequential fixes: task B က task A ပြီးမှစ → ~50 min for 5 fixes
- Hybrid parallel: 3 agents parallel → ~20 min for same 5 fixes (60% faster)

### Rules:
- **Dependency check:** Files that import from each other → same agent (sequential)
- **Independent files:** Different handlers, different modules → parallel ✅
- **Same file edits:** NEVER parallel on same file → conflict risk
- **Max parallel:** 5 agents per batch round (buffer 3-4 slots free)
- **Timeout:** 300s per parallel agent (narrow scope should be fast)
- **Merge:** All done → single merge report → single service restart
- **Rollback:** Per-batch rollback if one fails (don't rollback passing batches)

### Kora Tools Upgraded:
- **fix_protocol.py:** Global lock → per-file lock
- **batch_coordinator.py:** New tool at /root/coordination/
- **verify_agent.py:** Partial verify mode
- **SOUL.md:** Hybrid Decision Tree added
- **HEARTBEAT.md:** Batch monitoring added
- **AGENTS.md:** Hybrid spawning rules added

---

## 🚀 Hybrid Batch Execution — Phase 2 Upgrades (2026-05-30, 14:40-15:10 UTC)

### 9 Features Delivered in 15 min via 5 Parallel Agents (75% Faster Than Sequential)
**Total coordination tools: 20 → 25** at `/root/coordination/`

| # | Feature | Tool | Purpose |
|---|---------|------|---------|
| 1 | **Auto-Split Reflex** | SOUL.md + AGENTS.md | Kora auto-detects independent files → parallel spawn. Dependency check: same-file = sequential, different-bot = always parallel |
| 2 | **Queue Manager** | `queue_manager.py` (NEW) | Priority queue + dead-letter queue + auto-dispatch when slots free |
| 3 | **Telegram Batch Notify** | `notifier.py` (UPGRADED) | `send-batch`, `batch-status`, `batch-summary`, `send-tg`, `batch-complete` |
| 4 | **Smart Auto-Retry** | `batch_coordinator.py` (UPGRADED) | `--retry` command: analyzes failure type → suggests fix → re-spawns (max 2 retries) |
| 5 | **Cross-Bot Batching** | `batch_coordinator.py` | Different bots = always parallel. Cross-bot file edit + read-only = parallel. |
| 6 | **Priority Scheduling** | `batch_coordinator.py` + `queue_manager.py` | High priority tasks get slots first in queue |
| 7 | **Estimate Accuracy Tracker** | `batch_coordinator.py` | `--estimate-log` command tracks predicted vs actual time per batch |
| 8 | **Timeout Auto-Split** | `timeout_auto_split.py` (NEW, 517 lines) | Monitor/split long-running agents, daemon mode |
| 9 | **Batch History Dashboard** | `dashboard.py` + `dashboard.html` (NEW) | Self-contained web UI on port 9090, dark PS VIBE theme, 5 API endpoints |

### Key Decisions:
- **Max parallel per round:** 5 agents (buffer 3-4 slots for emergency)
- **Merge strategy:** All done → single merge report → single service restart
- **Rollback:** Per-batch if one fails (don't rollback passing batches)
- **Dependency rule:** File A imports File B → same agent (sequential). No shared imports → parallel.
- **The system proved itself:** 2 rounds of parallel batches this session, both faster than sequential.

### Coordination Tools — Full Inventory (25 tools)
- **Core (12):** flow_analyzer, arch_mapper, enhanced_validator, import_scanner, integration_tester, fix_safety, quality_gate, tool_orchestrator, star_import_fixer, smart_import_resolver, auto_verify, cron_health
- **Phase 2 (4):** auto_git_sync, service_watchdog, status_board, health_dashboard
- **Phase 3 (5):** workflow_engine, task_bridge, notifier, auto_healer, fix_protocol
- **Phase 4 — Hybrid Batch (4):** batch_coordinator, queue_manager, timeout_auto_split, dashboard

---

## 🐘 MySQL Migration — Detailed History (2026-05-30, 18:40-18:57 UTC)

### State Before:
- MySQL Docker container running (43h) with 21 tables, ~1500 rows synced from GSheet
- BUT API server (app.py) used gspread for ALL data operations — MySQL container had data but was UNUSED
- Bot code had `_HAS_API` pattern (try API first, gspread fallback) since day 1 — already designed for this
- Root cause of bot slowness: EVERY data read/write through GSheets = 200-800ms API round-trip

### What Was Fixed:
- Seeded member_wallets table from members
- Fixed MySQL wrapper functions (returned `[]` on empty, which bypassed gspread fallback)
- Added 6 missing wrapper functions (_fetch_games, _fetch_base_rate, etc.)
- Patched 6 gspread-only endpoints with MySQL fallback
- 17/17 endpoints verified passing

### New Architecture:
```
Bot (api_client.py) → API Server (:8000) → MySQL (primary) → gspread (cold fallback)
```
Dashboard reads now sub-3ms vs 200-800ms before.

### Lessons:
1. **MySQL container running ≠ MySQL in use** — always check app.py for actual imports
2. **Bot had migration pattern ready** (`_HAS_API`) — API-first design was already in place
3. **GSheets as source of truth is OK** for Boss direct viewing, but API should read from MySQL for speed
4. **Credentials:** root/PsVibe@MySQL2024!, psvibe_user/PsVibe@User2024!
