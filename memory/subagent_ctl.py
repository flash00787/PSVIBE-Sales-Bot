#!/usr/bin/env python3
"""
Kora Sub-Agent Control Script — Phase 2 Master Controller
Manages active_tasks.json registry: register, complete, list, status, orphans, summary.
Uses only stdlib.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta

MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
ACTIVE_TASKS_PATH = os.path.join(MEMORY_DIR, "active_tasks.json")
JOURNAL_PATH = os.path.join(MEMORY_DIR, "subagent-journal.json")
AGENT_STATUS_PATH = os.path.join(MEMORY_DIR, "agent-status.md")

STALE_THRESHOLD_MINUTES = 30


# ── JSON Helpers ────────────────────────────────────────────────────────────

def load_json(path, default=None):
    """Load a JSON file safely. Returns default on missing/corrupt file."""
    if default is None:
        default = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return default


def save_json(path, data):
    """Save data as pretty-printed JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def now_iso():
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(ts):
    """Parse ISO-8601 timestamp string to UTC datetime. Returns None on failure."""
    if ts is None:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def age_minutes(iso_ts):
    """Return age in minutes since the given ISO timestamp, or None if unparseable."""
    dt = parse_iso(iso_ts)
    if dt is None:
        return None
    return (datetime.now(timezone.utc) - dt).total_seconds() / 60.0


# ── Commands ────────────────────────────────────────────────────────────────

def cmd_register(task_name, model, goal):
    """Register a new task in active_tasks.json. Outputs the generated task-id."""
    registry = load_json(ACTIVE_TASKS_PATH, {"version": 1, "active": {}})
    active = registry.setdefault("active", {})

    task_id = f"{int(time.time())}-{task_name[:20]}"
    session_key = os.environ.get("OPENCLAW_SESSION_KEY", "unknown")
    channel = os.environ.get("OPENCLAW_CHANNEL", "telegram")

    active[task_id] = {
        "taskName": task_name,
        "model": model,
        "spawned": now_iso(),
        "task": goal,
        "sessionKey": session_key,
        "channel": channel,
        "goal": goal,
    }
    registry["version"] = 1
    save_json(ACTIVE_TASKS_PATH, registry)
    print(task_id)
    return 0


def cmd_complete(task_id, status, summary):
    """Remove a task from active_tasks.json by task-id."""
    registry = load_json(ACTIVE_TASKS_PATH, {"version": 1, "active": {}})
    active = registry.get("active", {})

    if task_id not in active:
        print(f"Task '{task_id}' not found in active registry", file=sys.stderr)
        return 1

    del active[task_id]
    registry["active"] = active
    save_json(ACTIVE_TASKS_PATH, registry)
    print(f"Removed '{task_id}' from active tasks")
    return 0


def cmd_list():
    """List all active tasks with details."""
    registry = load_json(ACTIVE_TASKS_PATH, {"version": 1, "active": {}})
    active = registry.get("active", {})

    if not active:
        print("No active tasks")
        return 0

    for task_id, task in active.items():
        age = age_minutes(task.get("spawned"))
        age_str = f"{age:.0f}m" if age is not None else "?"
        model = task.get("model", "?")
        goal = task.get("goal", task.get("task", "?"))
        print(f"  [{task_id}]")
        print(f"    Name:    {task.get('taskName', '?')}")
        print(f"    Model:   {model}")
        print(f"    Running: {age_str}")
        print(f"    Goal:    {goal[:80]}")
        print()
    return 0


def cmd_status():
    """Quick dashboard: counts + warnings for long-running tasks."""
    registry = load_json(ACTIVE_TASKS_PATH, {"version": 1, "active": {}})
    active = registry.get("active", {})

    total = len(active)
    long_running = []
    warning = []

    for task_id, task in active.items():
        age = age_minutes(task.get("spawned"))
        if age is not None and age > STALE_THRESHOLD_MINUTES:
            long_running.append((task_id, task, age))

    # Also check journal for running entries
    journal = load_json(JOURNAL_PATH, {"entries": []})
    journal_running = [e for e in journal.get("entries", []) if e.get("status") == "running"]

    print(f"Active tasks: {total}")
    print(f"Journal running: {len(journal_running)}")

    if total == 0 and len(journal_running) == 0:
        print("✅ All clear — no active or running tasks")
        return 0

    if long_running:
        print(f"\n⚠  WARNING — {len(long_running)} task(s) running >{STALE_THRESHOLD_MINUTES}min:")
        for task_id, task, age in long_running:
            print(f"  - {task_id}: {task.get('taskName','?')} ({age:.0f}m)")

    if journal_running:
        print(f"\n📋 Journal entries with status=running:")
        for e in journal_running:
            age = age_minutes(e.get("spawned"))
            age_str = f" ({age:.0f}m)" if age is not None else ""
            print(f"  - {e.get('id','?')}: {e.get('taskName','?')}{age_str}")

    return 0


def cmd_orphans():
    """
    Detect orphaned tasks:
      - Tasks in active_tasks.json NOT present in journal → orphaned
      - Journal entries with status "running" and spawned >30min ago → stale
    """
    registry = load_json(ACTIVE_TASKS_PATH, {"version": 1, "active": {}})
    active = registry.get("active", {})
    journal = load_json(JOURNAL_PATH, {"entries": []})
    entries = journal.get("entries", [])

    journal_ids = set()
    for e in entries:
        jid = e.get("id")
        if jid:
            journal_ids.add(jid)

    # Orphans: in active_tasks but not in journal
    orphan_ids = [tid for tid in active if tid not in journal_ids]

    # Stale journal: status=running + spawned >30min ago
    stale_entries = []
    for e in entries:
        if e.get("status") == "running":
            age = age_minutes(e.get("spawned"))
            if age is not None and age > STALE_THRESHOLD_MINUTES:
                stale_entries.append((e, age))

    has_issues = bool(orphan_ids or stale_entries)

    if not has_issues:
        print("✅ No orphaned or stale tasks found")
        return 0

    if orphan_ids:
        print("🔴 ORPHANED TASKS (in active_tasks.json, not in journal):")
        for tid in orphan_ids:
            t = active[tid]
            age = age_minutes(t.get("spawned"))
            age_str = f" ({age:.0f}m)" if age is not None else ""
            print(f"  - {tid}: {t.get('taskName','?')}{age_str}")
        print()

    if stale_entries:
        print("🟡 STALE JOURNAL ENTRIES (running >30min):")
        for e, age in stale_entries:
            print(f"  - {e.get('id','?')}: {e.get('taskName','?')} ({age:.0f}m)")
        print()

    return 1 if has_issues else 0


def cmd_summary():
    """Generate agent-status.md dashboard."""
    registry = load_json(ACTIVE_TASKS_PATH, {"version": 1, "active": {}})
    active = registry.get("active", {})
    journal = load_json(JOURNAL_PATH, {"entries": []})
    entries = journal.get("entries", [])

    gen_time = now_iso()
    gen_display = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    lines.append("# Agent Status Dashboard")
    lines.append(f"*Generated: {gen_display}*")
    lines.append("")

    # Active tasks section
    if active:
        lines.append("## 🟢 Active Tasks ({})".format(len(active)))
        lines.append("| Task | Model | Running For | Goal |")
        lines.append("|------|-------|-------------|------|")
        for task_id, task in active.items():
            name = task.get("taskName", "?")
            model = task.get("model", "?")
            age = age_minutes(task.get("spawned"))
            age_str = f"{age:.0f}m" if age is not None else "?"
            goal = task.get("goal", task.get("task", ""))[:60]
            lines.append(f"| {name} | {model} | {age_str} | {goal} |")
        lines.append("")
    else:
        lines.append("## 🟢 Active Tasks")
        lines.append("*No active tasks*")
        lines.append("")

    # Recent tasks from journal (last 24h)
    now_dt = datetime.now(timezone.utc)
    cutoff = now_dt - timedelta(hours=24)
    recent = []

    for e in entries:
        completed = parse_iso(e.get("completed"))
        spawned = parse_iso(e.get("spawned"))
        ts = completed or spawned
        if ts is not None and ts > cutoff:
            recent.append(e)

    lines.append("## ⏳ Recent Tasks (last 24h)")
    if recent:
        for e in recent:
            status = e.get("status", "?")
            icon = {"completed": "✅", "failed": "❌", "partial": "🟡", "running": "🔄"}.get(status, "❓")
            name = e.get("taskName", "?")
            completed = parse_iso(e.get("completed"))
            ago_str = ""
            if completed:
                ago = (now_dt - completed).total_seconds() / 60
                ago_str = f" ({ago:.0f}m ago)"
                if ago > 60:
                    ago_str = f" ({ago/60:.1f}h ago)"
            summary = e.get("summary", "")[:60]
            lines.append(f"- {icon} {name}{ago_str}")
            if summary:
                lines.append(f"  _{summary}_")
    else:
        lines.append("*No recent tasks*")

    lines.append("")

    # Write to file
    content = "\n".join(lines) + "\n"
    with open(AGENT_STATUS_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    # Also print to stdout
    print(content.strip())
    return 0


# ── Main ────────────────────────────────────────────────────────────────────

USAGE = """subagent_ctl.py — Kora Sub-Agent Master Controller

Usage:
  python3 subagent_ctl.py register <taskName> <model> <goal>
  python3 subagent_ctl.py complete <task-id> <status> <summary>
  python3 subagent_ctl.py list
  python3 subagent_ctl.py status
  python3 subagent_ctl.py orphans
  python3 subagent_ctl.py summary

Commands:
  register   Register a task before spawning. Outputs task-id.
  complete   Remove a completed task from active registry.
  list       List all currently active tasks.
  status     Dashboard with counts and warnings for long-running tasks.
  orphans    Find orphaned (active but not in journal) and stale tasks.
  summary    Generate agent-status.md dashboard.
"""


def main():
    args = sys.argv[1:]

    if not args:
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    cmd = args[0]

    if cmd == "register":
        if len(args) < 4:
            print("Usage: subagent_ctl.py register <taskName> <model> <goal>", file=sys.stderr)
            sys.exit(1)
        sys.exit(cmd_register(args[1], args[2], " ".join(args[3:])))

    elif cmd == "complete":
        if len(args) < 4:
            print("Usage: subagent_ctl.py complete <task-id> <status> <summary>", file=sys.stderr)
            sys.exit(1)
        sys.exit(cmd_complete(args[1], args[2], " ".join(args[3:])))

    elif cmd == "list":
        sys.exit(cmd_list())

    elif cmd == "status":
        sys.exit(cmd_status())

    elif cmd == "orphans":
        sys.exit(cmd_orphans())

    elif cmd == "summary":
        sys.exit(cmd_summary())

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
