# 🛠️ Tool Commands — Full Reference

> Referenced by TOOLS.md. All tools at `/root/coordination/` unless noted.

---

## Core Dev
```bash
python3 /root/coordination/flow_analyzer.py --analyze --states --report --check-await
python3 /root/coordination/arch_mapper.py --circular --dep-text
python3 /root/coordination/enhanced_validator.py --full
python3 /root/coordination/quality_gate.py --quick
python3 /root/coordination/tool_orchestrator.py 2>&1 | tail -20
```

## Workflow Engine
```bash
python3 /root/coordination/workflow_engine.py --status
python3 /root/coordination/workflow_engine.py --run quality|full-audit|safe-fix|auto-deploy
python3 /root/coordination/workflow_engine.py --retry
python3 /root/coordination/workflow_engine.py --history
```

## Documentation
```bash
python3 /root/coordination/auto_doc_updater.py --summary "Fixed X: brief description"
```

## Task Bridge
```bash
python3 /root/coordination/task_bridge.py create --pipeline safe-fix --step "Fix X" --files path/file.py
python3 /root/coordination/task_bridge.py list pending
python3 /root/coordination/task_bridge.py complete <task-id> --status ok --message "Fixed"
```

## Notifier
```bash
python3 /root/coordination/notifier.py send --title "Title" --message "Msg" --level success
python3 /root/coordination/notifier.py list --unread
```

## Fix Protocol (MANDATORY)
```bash
python3 /root/coordination/fix_protocol.py --start bot/handlers/admin.py    # before edit
python3 /root/coordination/fix_protocol.py --complete                       # verify + diff + commit
python3 /root/coordination/fix_protocol.py --complete --rollback            # on failure
```

## Hybrid Batch
```bash
python3 /root/coordination/batch_coordinator.py --estimate file1.py file2.py
python3 /root/coordination/batch_coordinator.py --auto-split file1.py file2.py file3.py
python3 /root/coordination/batch_coordinator.py --dispatch batches.json --priority high
python3 /root/coordination/batch_coordinator.py --status
python3 /root/coordination/batch_coordinator.py --merge
python3 /root/coordination/batch_coordinator.py --retry 2
```

## Queue Manager
```bash
python3 /root/coordination/queue_manager.py --enqueue --task "fix sales.py" --priority high
python3 /root/coordination/queue_manager.py --list
python3 /root/coordination/queue_manager.py --dead-letter
```

## Verify Agent
```bash
python3 /root/coordination/verify_agent.py verify --files "bot/handlers/admin.py" --partial
python3 /root/coordination/verify_agent.py merge-check --files "admin.py" "console_mgmt.py"
```

## Auto Healer
```bash
python3 /root/coordination/auto_healer.py check
python3 /root/coordination/auto_healer.py status
```

## Other
```bash
python3 /root/coordination/check_alerts.py               # Check health alerts
python3 /root/coordination/fix_safety.py snapshot --target-file bot/handlers/main_menu.py
python3 /root/coordination/fix_safety.py verify --target-file bot/handlers/main_menu.py
python3 /root/coordination/health_dashboard.py            # Dashboard status
python3 /root/coordination/dashboard.py --port 9090       # Start dashboard
sudo /root/psvibe_api_server/run_sync.sh                  # MySQL sync
```

## TTS
- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod

## Coordination Tools Table

### Core Analysis Tools
| Tool | Lines | Purpose |
|------|-------|---------|
| Flow Analyzer | 742 | State machine analysis, callback depth |
| Architecture Mapper | 754 | Module dependency graph, circular import detection |
| Enhanced Validator | 996 | Async pattern check, code pattern scanning |
| Quality Gate | 227 | Unified quality score (0-100) |
| Tool Orchestrator | 207 | 6-tool dependency-ordered run |

### Phase 2 Tools
| Tool | Purpose |
|------|---------|
| Auto Git Sync | Auto-commit (dry-run every 6h) |
| Service Watchdog | systemd watchdog (3 services, auto-restart) |
| Status Board | Real-time JSON snapshot |
| Health Dashboard | Comprehensive overview |
| CPU Watchdog | Auto-kill stuck processes >5 min |

### Phase 3 — Workflow
| Tool | Lines | Purpose |
|------|-------|---------|
| Workflow Engine | 330+ | 4 pipelines with auto-rollback |
| Task Bridge | 185 | Sub-agent ⇄ Engine bridge |
| Notifier | 155 | Pipeline event relay |
| Auto Healer | 190 | Service watchdog (3 failures → restart) |

### Phase 4 — Hybrid Batch
| Tool | Lines | Purpose |
|------|-------|---------|
| Batch Coordinator v2 | 1200 | 11 commands: plan/dispatch/status/merge/rollback |
| Queue Manager | — | Priority queue + dead-letter |
| Timeout Auto-Split | 517 | Auto-split long-running agents |
