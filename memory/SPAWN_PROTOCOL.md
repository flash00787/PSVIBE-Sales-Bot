# Kora Spawn Protocol — Quick Reference

## Before sessions_spawn

```bash
# Register task (writes to BOTH journal + active_tasks.json)
python3 memory/kora_spawn.py register <taskName> <model> "<goal>"

# Example:
python3 memory/kora_spawn.py register fix-bug-x "deepseek/deepseek-v4-pro" "Fix the MySQL connection timeout bug"
# Output: 1716880000-fix-bug-x  ← save this task-id!
```

## Spawn the Sub-agent

Use `sessions_spawn` tool with the registered task-id in the description.
Always include `runTimeoutSeconds` (default: 7200 = 2 hours).

```python
# In Kora's code:
sessions_spawn(
    taskName="fix-bug-x",
    model="deepseek/deepseek-v4-pro",
    runTimeoutSeconds=7200,  # 2 hours
    task="## Task: Fix MySQL connection timeout bug\n..."
)
```

## After Completion

```bash
# Mark complete (removes from active_tasks, updates journal)
python3 memory/kora_spawn.py complete <task-id> <status> "<summary>"

# Status values: completed | failed | partial

# Example:
python3 memory/kora_spawn.py complete 1716880000-fix-bug-x completed "Fixed timeout by adding connection retry logic"
```

## Quick Checks

```bash
python3 memory/kora_spawn.py list      # Active tasks detail
python3 memory/subagent_ctl.py status  # Summary counts
python3 memory/subagent_ctl.py orphans # Stuck/orphaned tasks?
python3 memory/subagent_ctl.py summary # Full dashboard
```

## Error Handling
If a sub-agent fails or errors → **report to Kora automatically**. 
Kora will assess and decide retry vs manual fix.

## Spawn Protocol Rules (Mandatory)
❌ NEVER call sessions_spawn directly without registering first
❌ NEVER forget to complete after sub-agent finishes
✅ ALWAYS register before spawn
✅ ALWAYS complete after spawn finishes
✅ ALWAYS set runTimeoutSeconds explicitly

## Status Values
- `running` — Just spawned
- `completed` — Done successfully
- `partial` — Partially done (needs follow-up)
- `failed` — Failed, needs retry
