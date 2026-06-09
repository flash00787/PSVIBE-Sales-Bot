# HEARTBEAT.md — Periodic Tasks

## 🩺 Unified Health Monitor (Hourly auto-check)
```bash
python3 /home/node/.openclaw/workspace/coordination/kora_health_monitor.py --json 2>&1 | tail -1
```

## 🤖 Automated Scripts (Every ~4h heartbeat)
```bash
python3 /home/node/.openclaw/workspace/coordination/kora_health_monitor.py --json 2>&1 | tail -1
python3 /home/node/.openclaw/workspace/memory/heartbeat_routine.py
python3 /home/node/.openclaw/workspace/memory/consolidator.py --all
python3 /root/coordination/notifier.py list --unread
python3 /root/coordination/task_bridge.py list pending
```

## 🧹 Stale Lock Cleanup
```bash
bash /home/node/.openclaw/workspace/memory/cleanup_session_locks.sh
```

## ✅ Heartbeat Checklist
- [ ] Run health monitor (quick check)
- [ ] Run heartbeat_routine (stuck agents)
- [ ] Run consolidator (daily logs)
- [ ] Check workflow notifications
- [ ] Check pending tasks
- [ ] Check health alerts: `python3 /root/coordination/check_alerts.py`
- [ ] Check stale locks cleanup
- [ ] Check queue manager: `python3 /root/coordination/queue_manager.py --dead-letter`
- [ ] Check sub-agent fallback rate (>3 = report Boss)

> **Full procedures:** See `memory/heartbeat-procedures.md`
> **Post-task SOP:** See `POST_TASK_SOP.md`
