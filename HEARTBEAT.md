# HEARTBEAT.md — Periodic Tasks

## 🤖 Automated Scripts (Run at every ~4h heartbeat)

```bash
# 1. Check stuck sub-agents
python3 /home/node/.openclaw/workspace/memory/heartbeat_routine.py

# 2. Consolidate daily logs to MEMORY.md
python3 /home/node/.openclaw/workspace/memory/consolidator.py --all
```

## 🧠 Memory Maintenance (Every ~4 hours)
1. ✅ Run `heartbeat_routine.py` — checks stuck/pending sub-agents
2. ✅ Run `consolidator.py --all` — extracts daily log summaries
3. Review recent daily files (`memory/YYYY-MM-DD.md`) — new significant events?
4. Consolidate learnings into MEMORY.md (distill, don't duplicate)
5. Prune outdated entries from MEMORY.md
6. Update `memory/heartbeat-state.json` with results

## ✅ Sub-agent Check
- Any sub-agent still running past expected timeout? (>30 min = stuck)
- Any partial/failed entries that need follow-up?
  - Use: `python3 /home/node/.openclaw/workspace/memory/task_retry.py <task-id>`
- Spawn a fix sub-agent if needed (Pro model only!)
- Report stuck tasks to Boss if found

## ✍️ Session Persistence
- If session has significant activity → write to daily memory file
- Update `memory/session-memory.md` with current state
- Update `memory/session-tracker-last.md` with last run timestamp

## ⚙️ Boot Protocol (Run at session start)
```bash
python3 /home/node/.openclaw/workspace/memory/boot_protocol.py
```
