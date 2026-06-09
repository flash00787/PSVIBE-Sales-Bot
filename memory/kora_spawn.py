#!/usr/bin/env python3
"""
Kora Spawn Helper — Automates register → sessions_spawn → complete flow.

Usage:
    python3 kora_spawn.py <task-name> <model> "<goal>" -- "<sessions_spawn_args>"

    # Dry-run (preview only):
    python3 kora_spawn.py --dry-run my-task "deepseek/deepseek-v4-pro" "Fix X bug"
    
    # Register + print task-id for Kora to use manually:
    python3 kora_spawn.py --register-only my-task "deepseek/deepseek-v4-pro" "Fix X bug"

This script:
1. Registers task in journal + active_tasks.json
2. Outputs the task-id and session_spawn command for Kora to use
3. Kora calls sessions_spawn separately
4. Kora calls `python3 kora_spawn.py --complete <task-id> <status> "<summary>"` after

For now, this is a register/complete helper. Full automation (auto-spawn) 
requires OpenClaw's sessions_spawn tool which can't be called from CLI.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
JOURNAL_PATH = os.path.join(MEMORY_DIR, "subagent-journal.json")
ACTIVE_PATH = os.path.join(MEMORY_DIR, "active_tasks.json")


def load_json(path):
    if not os.path.exists(path):
        return {} if "active" in path else {"version": 2, "metadata": {}, "entries": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def generate_task_id(task_name):
    ts = int(time.time())
    safe_name = task_name[:20].replace(" ", "_")
    return f"{ts}-{safe_name}"


def cmd_register(args):
    """Register a new task. Usage: register <taskName> <model> <goal>"""
    if len(args) < 3:
        print("Usage: register <task-name> <model> <goal>", file=sys.stderr)
        sys.exit(1)

    task_name = args[0]
    model = args[1]
    goal = " ".join(args[2:])

    task_id = generate_task_id(task_name)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Update journal
    journal = load_json(JOURNAL_PATH)
    if "metadata" not in journal:
        journal["metadata"] = {}
    if "entries" not in journal:
        journal["entries"] = []
    
    # V2 schema check
    if journal.get("version") != 2:
        journal["version"] = 2
        journal["metadata"]["upgradedToV2"] = True

    entry = {
        "id": task_id,
        "taskName": task_name,
        "task": goal,
        "model": model,
        "spawned": now,
        "completed": None,
        "status": "running",
        "summary": "registered — waiting for spawn",
        "sessionKey": "agent:main:telegram:default:direct:6296803251",
        "channel": "telegram",
        "resultFile": None,
    }
    journal["entries"].append(entry)
    journal["metadata"]["lastUpdated"] = now
    save_json(JOURNAL_PATH, journal)

    # Update active tasks
    active = load_json(ACTIVE_PATH)
    if "version" not in active:
        active["version"] = 1
    if "active" not in active:
        active["active"] = {}
    
    active["active"][task_id] = {
        "taskName": task_name,
        "model": model,
        "spawned": now,
        "task": goal,
        "goal": goal,
        "sessionKey": "agent:main:telegram:default:direct:6296803251",
        "channel": "telegram",
    }
    save_json(ACTIVE_PATH, active)

    print(task_id)
    return task_id


def cmd_complete(args):
    """Mark a task as complete. Usage: complete <task-id> <status> <summary>"""
    if len(args) < 3:
        print("Usage: complete <task-id> <status> <summary>", file=sys.stderr)
        sys.exit(1)

    task_id = args[0]
    status = args[1]
    summary = " ".join(args[2:])

    valid_statuses = {"completed", "failed", "partial"}
    if status not in valid_statuses:
        print(f"Invalid status: {status}. Use: {', '.join(sorted(valid_statuses))}", file=sys.stderr)
        sys.exit(1)

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Update journal
    journal = load_json(JOURNAL_PATH)
    found = False
    for entry in journal.get("entries", []):
        if entry["id"] == task_id:
            entry["status"] = status
            entry["completed"] = now
            entry["summary"] = summary
            found = True
            break

    if not found:
        print(f"Warning: task {task_id} not found in journal", file=sys.stderr)
    else:
        journal["metadata"]["lastUpdated"] = now
        save_json(JOURNAL_PATH, journal)

    # Remove from active tasks
    active = load_json(ACTIVE_PATH)
    if task_id in active.get("active", {}):
        del active["active"][task_id]
        save_json(ACTIVE_PATH, active)

    print(f"✅ {task_id}: {status}")
    return True


def cmd_list_active(args):
    """List all active (running) tasks."""
    active = load_json(ACTIVE_PATH)
    tasks = active.get("active", {})
    if not tasks:
        print("No active tasks.")
        return
    
    for tid, info in sorted(tasks.items()):
        elapsed = ""
        if "spawned" in info:
            try:
                spawned = datetime.fromisoformat(info["spawned"].replace("Z", "+00:00"))
                delta = datetime.now(timezone.utc) - spawned
                mins = int(delta.total_seconds() / 60)
                elapsed = f" ({mins}m ago)"
            except:
                pass
        print(f"  {tid}: {info.get('taskName', '?')}{elapsed} — {info.get('goal', '')[:60]}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "register":
        cmd_register(sys.argv[2:])
    elif command == "complete":
        cmd_complete(sys.argv[2:])
    elif command == "list":
        cmd_list_active(sys.argv[2:])
    elif command == "--help":
        print(__doc__)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
