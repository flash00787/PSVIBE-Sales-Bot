#!/usr/bin/env python3
"""
Heartbeat Routine Script — Periodic health check for sub-agent tasks.

Usage:
    python3 heartbeat_routine.py

Reads subagent-journal.json AND active_tasks.json to detect stuck/pending tasks
(>30 min idle), updates heartbeat-state.json, auto-generates agent-status.md,
and prints a one-line summary.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta

MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
JOURNAL_PATH = os.path.join(MEMORY_DIR, "subagent-journal.json")
STATE_PATH = os.path.join(MEMORY_DIR, "heartbeat-state.json")
ACTIVE_TASKS_PATH = os.path.join(MEMORY_DIR, "active_tasks.json")
AGENT_STATUS_PATH = os.path.join(MEMORY_DIR, "agent-status.md")
SUBAGENT_CTL_PATH = os.path.join(MEMORY_DIR, "subagent_ctl.py")

STUCK_THRESHOLD_MINUTES = 30


def load_json(path, default=None):
    """Load a JSON file, returning default on failure."""
    if default is None:
        default = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path, data):
    """Save data as JSON with pretty-printing."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def now_iso():
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(ts):
    """Parse ISO-8601 timestamp string, return naive or aware datetime (UTC)."""
    if ts is None:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt
    except (ValueError, TypeError):
        return None


def age_minutes(iso_ts):
    """Return age in minutes since the given ISO timestamp, or None if unparseable."""
    dt = parse_iso(iso_ts)
    if dt is None:
        return None
    return (datetime.now(timezone.utc) - dt).total_seconds() / 60.0


def analyze_journal():
    """
    Scan subagent-journal.json entries for stuck and pending tasks.

    Returns:
        (ok_count, pending_count, stuck_count, stuck_tasks, pending_tasks)
    """
    journal = load_json(JOURNAL_PATH)
    entries = journal.get("entries", [])

    now_dt = datetime.now(timezone.utc)
    stuck_tasks = []
    pending_tasks = []
    ok_count = 0

    for entry in entries:
        status = entry.get("status", "unknown")

        if status in ("running", "pending"):
            # Check spawn time for stuck threshold
            spawned = parse_iso(entry.get("spawned"))
            completed = parse_iso(entry.get("completed"))

            if spawned is None:
                # Can't determine age — treat as pending
                pending_tasks.append({
                    "id": entry.get("id"),
                    "taskName": entry.get("taskName"),
                    "status": status,
                    "spawned": entry.get("spawned"),
                })
                continue

            age_minutes_val = (now_dt - spawned).total_seconds() / 60

            if age_minutes_val > STUCK_THRESHOLD_MINUTES:
                stuck_tasks.append({
                    "id": entry.get("id"),
                    "taskName": entry.get("taskName"),
                    "status": status,
                    "spawned": entry.get("spawned"),
                    "ageMinutes": round(age_minutes_val, 1),
                    "summary": entry.get("summary", ""),
                    "source": "journal",
                })
            else:
                pending_tasks.append({
                    "id": entry.get("id"),
                    "taskName": entry.get("taskName"),
                    "status": status,
                    "spawned": entry.get("spawned"),
                })
        elif status in ("completed", "success", "partial"):
            ok_count += 1
        elif status == "failed":
            ok_count += 1  # failed is terminal, count as "OK" (not stuck)

    stuck_count = len(stuck_tasks)
    pending_count = len(pending_tasks)

    return ok_count, pending_count, stuck_count, stuck_tasks, pending_tasks


def analyze_active_tasks():
    """
    Scan active_tasks.json for stale entries not covered by the journal.

    Returns:
        (active_stuck, active_pending) — lists of dicts
    """
    registry = load_json(ACTIVE_TASKS_PATH, {"version": 1, "active": {}})
    active = registry.get("active", {})

    active_stuck = []
    active_pending = []

    for task_id, task in active.items():
        spawned_ts = task.get("spawned")
        age = age_minutes(spawned_ts)

        if age is None:
            active_pending.append({
                "id": task_id,
                "taskName": task.get("taskName", "?"),
                "status": "running",
                "spawned": spawned_ts,
            })
            continue

        if age > STUCK_THRESHOLD_MINUTES:
            active_stuck.append({
                "id": task_id,
                "taskName": task.get("taskName", "?"),
                "status": "running",
                "spawned": spawned_ts,
                "ageMinutes": round(age, 1),
                "summary": task.get("goal", task.get("task", "")),
                "source": "active_tasks",
            })
        else:
            active_pending.append({
                "id": task_id,
                "taskName": task.get("taskName", "?"),
                "status": "running",
                "spawned": spawned_ts,
            })

    return active_stuck, active_pending


def generate_agent_status():
    """
    Generate agent-status.md using subagent_ctl.py summary command.
    Falls back to manual generation if subagent_ctl.py is unavailable.
    """
    if os.path.exists(SUBAGENT_CTL_PATH):
        try:
            result = subprocess.run(
                [sys.executable, SUBAGENT_CTL_PATH, "summary"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                print(result.stdout.strip())
                return True
            else:
                print("[heartbeat] subagent_ctl.py summary failed: " + result.stderr.strip(),
                      file=sys.stderr)
        except (subprocess.TimeoutExpired, OSError) as e:
            print(f"[heartbeat] Could not run subagent_ctl.py: {e}", file=sys.stderr)

    # Fallback: write directly
    fallback_status()
    return False


def fallback_status():
    """Manual fallback to write agent-status.md when subagent_ctl.py is unavailable."""
    gen_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Agent Status Dashboard",
        f"*Generated: {gen_time} (fallback)*",
        "",
        "## 🟢 Active Tasks",
        "*Status unavailable — subagent_ctl.py not found*",
        "",
        "## ⏳ Recent Tasks (last 24h)",
        "*Status unavailable*",
        "",
    ]
    with open(AGENT_STATUS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def update_state(stuck_tasks, pending_tasks):
    """Write updated heartbeat-state.json."""
    state = {
        "lastHeartbeat": now_iso(),
        "stuckTasks": stuck_tasks,
        "pendingTasks": pending_tasks,
    }
    save_json(STATE_PATH, state)


def main():
    # Analyze journal
    ok_count, pending_count, stuck_count, stuck_tasks, pending_tasks = analyze_journal()

    # Also check active_tasks.json for additional stale/pending
    active_stuck, active_pending = analyze_active_tasks()

    # Merge results, avoiding duplicates by task id
    existing_ids = set()
    all_stuck = []
    all_pending = []

    for t in stuck_tasks:
        existing_ids.add(t["id"])
        all_stuck.append(t)
    for t in pending_tasks:
        existing_ids.add(t["id"])
        all_pending.append(t)

    for t in active_stuck:
        if t["id"] not in existing_ids:
            all_stuck.append(t)
            existing_ids.add(t["id"])
    for t in active_pending:
        if t["id"] not in existing_ids:
            all_pending.append(t)
            existing_ids.add(t["id"])

    # Update heartbeat state
    update_state(all_stuck, all_pending)

    # Generate agent-status.md dashboard
    generate_agent_status()

    # Summary to stdout
    total_stuck = len(all_stuck)
    total_pending = len(all_pending)
    summary = f"[HEARTBEAT] {ok_count} tasks OK, {total_pending} pending, {total_stuck} stuck"
    print(summary)

    if all_stuck:
        print("  ⚠ Stuck tasks:")
        for t in all_stuck:
            source = t.get("source", "?")
            print(f"    - [{source}] {t['id']}: {t.get('summary', t.get('taskName', '?'))} ({t.get('ageMinutes','?')}min)")

    if all_pending:
        print("  ⏳ Pending tasks:")
        for t in all_pending:
            print(f"    - {t['id']}: {t.get('taskName', '?')}")


if __name__ == "__main__":
    main()
