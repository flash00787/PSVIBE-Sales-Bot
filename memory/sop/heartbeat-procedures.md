# 💓 Heartbeat Procedures (Full Detail)

> Detailed procedures referenced by HEARTBEAT.md.
> Run by Kora at every heartbeat cycle (~4h).

---

## 🧠 Memory Maintenance Checklist
1. Run `heartbeat_routine.py` — checks stuck/pending sub-agents
2. Run `consolidator.py --all` — extracts daily log summaries
3. Review recent daily files (`memory/YYYY-MM-DD.md`) for significant events
4. Consolidate learnings into MEMORY.md (distill, don't duplicate)
5. Prune outdated entries from MEMORY.md
6. Update `memory/heartbeat-state.json` with results
7. Check health alerts: `python3 /root/coordination/check_alerts.py` (exit 1 → alert → message Boss)
8. Check weekly scan: `test -f /root/coordination/findings/import_regression_alert.json && echo ALERT`

## 🧹 Stale Lock Cleanup
```bash
bash /home/node/.openclaw/workspace/memory/cleanup_session_locks.sh
```
- On session boot (via boot_protocol.py)
- Every heartbeat
- PID dead → always clean | PID alive + age > 17min → clean (stale) | else keep

## 💚 Service Health Check
```python
sessions_spawn(taskName="heartbeat-status", 
    task="python3 /root/coordination/status_reporter.py quick",
    runTimeoutSeconds=60, model="deepseek/deepseek-v4-flash")
# → If critical → message Boss | If normal → silent (NO_REPLY)
```

## 🔍 Findings Check
```python
sessions_spawn(taskName="heartbeat-dispatch",
    task="python3 /root/coordination/dispatch_manager.py --status",
    runTimeoutSeconds=60, model="deepseek/deepseek-v4-flash")
# → If > 0 pending → dispatch | If 0 → silent
```

## ✅ Sub-agent Check
- Running >30 min = stuck → use `task_retry.py <task-id>`
- Report stuck tasks to Boss

## 🆕 Queue Manager Check
```bash
python3 /root/coordination/queue_manager.py --list
python3 /root/coordination/queue_manager.py --dequeue  # if pending
python3 /root/coordination/queue_manager.py --dead-letter  # > 0 → flag Boss
```

## 🆕 Timeout Auto-Split Check
```bash
python3 /root/coordination/timeout_auto_split.py --status
# → If agents >5 min → flag and suggest split
```

## 🆕 Notification Relay
When heartbeat finds unread notifications:
```
NOTIFICATIONS FOUND:
  - [Pipeline: Quality Gate] Steps: 4/4 ✅
  - [Critical: Service X] Alert details...
```
Mark as read: `python3 /root/coordination/notifier.py mark-all`

## 🆕 Task Bridge Relay
When heartbeat finds pending sub-agent tasks, spawn with:
```python
sessions_spawn(taskName=f"wf-{task['task_id']}",
    task=f"SAFETY NET: ... Task from Workflow Engine: {task['pipeline']}/{task['step']} ...")
```

## 🛡️ Sub-agent Safety Net
Every `sessions_spawn` task description MUST include:
```
SAFETY NET: You MUST end with '=== RESULT: OK ||| ERROR: <reason> ==='.
If anything fails, write to temp file. NEVER stop without final output.
```

## 🚨 Crash Prevention — Spawn + Yield
- MAX 2 agents per spawn message
- After spawn → `sessions_yield()` IMMEDIATELY
- Spawn message = 1-2 lines MAX (no explanation text!)
- Recovery: check temp files → re-spawn if missing

## Pre-spawn Safety Checklist
- [ ] Task has "SAFETY NET" instructions
- [ ] Task writes to `temp/<name>.txt`
- [ ] Task ends with `OK | ERROR`
- [ ] File path unique (no parallel overwrites)
- [ ] Context includes PROJECT_STRUCTURE.md (both repos)
- [ ] Task mentions which repo (bot: `/root/psvibe-sales-bot/` or API: `/root/psvibe_api_server/`)

## 🔄 Fix → Verify Loop
After ANY fix → spawn Verify Agent:
```python
sessions_spawn(taskName="verify-fix",
    task='python3 /root/coordination/verify_agent.py verify --agent "fix-X" --files "file.py"',
    runTimeoutSeconds=300, model="deepseek/deepseek-v4-flash")
```
Checks: compile ✓ | imports ✓ | services ✓ | logs ✓ | integrity ✓
PASS ✅ → Findings Manager | FAIL ❌ → Re-dispatch (max 3)

## 🚀 Auto-Helper Slot Check
- Slots free > 0 + agents with pending work → auto-spawn helpers
- Short timeout (300s) for helpers, long (900-14400s) for fixes

## 🔀 Auto-Split Long-Running Tasks
Agent >3 min with multi-step work → check slots → split into narrow-scope agents
- Max 15-18 parallel split agents
- Each: narrow scope + 300s timeout + separate temp file
- After all complete → merge → single report

## 🔀 Hybrid Batch Monitoring
- Check parallel agents: `subagents action=list`
- Any running >10 min → check temp files: `cat temp/hybrid_batch_*.txt`
- Check batch coordinator: `python3 /root/coordination/batch_coordinator.py --status`
- Failed → re-dispatch (max 2) | All done → merge → single restart

## ⚖️ Role Reminders
- Kora NEVER does anything manually — helper first
- ANY task → helper first | Only do myself if no helper exists
- Hybrid batch: independent files → parallel auto-spawn

## ✍️ Session Persistence
- Significant activity → write to `memory/YYYY-MM-DD.md`
- Update `memory/session-memory.md` with current state
- Update `memory/session-tracker-last.md` with last run timestamp

## 📊 Stats & Fallback Monitoring
- Track message_count in heartbeat-state.json
- Log subagent spawn count and failure rate
- Review stats every 4th heartbeat
- Check fallback: `grep -l "fallback\|timed out\|retrying" /home/node/.openclaw/agents/main/sessions/*.jsonl | tail -5`
- >3 fallback events in 4h → report Boss
