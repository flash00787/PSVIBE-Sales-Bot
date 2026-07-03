#!/usr/bin/env python3
"""
Kora Boot Protocol — Phase 2 Context Awareness
Scans subagent-journal.json AND active_tasks.json for incomplete/partial tasks
at session startup.
Exit 0 = all clear, Exit 1 = incomplete tasks found.
Uses only stdlib.

Flags:
    --json      Output machine-parseable JSON instead of human-readable text.
    --no-fail   Always exit 0, even when incomplete tasks are found.
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
JOURNAL_PATH = os.path.join(MEMORY_DIR, "subagent-journal.json")
ACTIVE_TASKS_PATH = os.path.join(MEMORY_DIR, "active_tasks.json")

STALE_THRESHOLD_MINUTES = 30

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # workspace root
PROJECT_STATE_DIR = os.path.join(WS, "project-state")
SESSION_TRACKER = os.path.join(PROJECT_STATE_DIR, "session-tracker-last.md")


def load_json(path, default=None):
    """Load a JSON file safely. Returns default on missing/corrupt file."""
    if default is None:
        default = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return default


def format_timestamp(ts):
    """Convert ISO timestamp to human-readable."""
    if ts is None:
        return "unknown"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, TypeError):
        return str(ts)


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


def detect_orphans(active_tasks, journal_entries):
    """
    Find tasks in active_tasks.json that are NOT present in the journal.

    Returns list of (task_id, task_dict) tuples.
    """
    journal_ids = set()
    for e in journal_entries:
        jid = e.get("id")
        if jid:
            journal_ids.add(jid)

    orphans = []
    for tid, tdata in active_tasks.items():
        if tid not in journal_ids:
            orphans.append((tid, tdata))
    return orphans


def detect_stale(journal_entries):
    """
    Find journal entries with status 'running' and spawned > threshold ago.

    Returns list of dicts with entry data + ageMinutes.
    """
    stale = []
    for e in journal_entries:
        if e.get("status") == "running":
            age = age_minutes(e.get("spawned"))
            if age is not None and age > STALE_THRESHOLD_MINUTES:
                stale.append({
                    "entry": e,
                    "ageMinutes": round(age, 1),
                })
    return stale


def build_json_output(running, partial, orphans, stale):
    """Build machine-parseable JSON summary."""
    result = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hasIncomplete": bool(running or partial or orphans or stale),
        "counts": {
            "running": len(running),
            "partial": len(partial),
            "orphans": len(orphans),
            "stale": len(stale),
        },
        "running": [
            {
                "id": e.get("id"),
                "taskName": e.get("taskName", "unknown"),
                "spawned": e.get("spawned"),
                "summary": e.get("summary", ""),
            }
            for e in running
        ],
        "partial": [
            {
                "id": e.get("id"),
                "taskName": e.get("taskName", "unknown"),
                "spawned": e.get("spawned"),
                "summary": e.get("summary", ""),
            }
            for e in partial
        ],
        "orphans": [
            {
                "id": tid,
                "taskName": tdata.get("taskName", "unknown"),
                "spawned": tdata.get("spawned"),
                "goal": tdata.get("goal", ""),
            }
            for tid, tdata in orphans
        ],
        "stale": [
            {
                "id": s["entry"].get("id"),
                "taskName": s["entry"].get("taskName", "unknown"),
                "spawned": s["entry"].get("spawned"),
                "ageMinutes": s["ageMinutes"],
            }
            for s in stale
        ],
    }
    return result


def _check_mongo():
    """
    Phase 4: Quick MongoDB availability + stats check.
    Returns True if MongoDB is reachable and has data.
    """
    import subprocess
    MEMORY_CLI = "/root/coordination/kora_memory.py"
    mongo_available = False

    # Check 1: Code graph stats (fast, validates connection + data)
    try:
        result = subprocess.run(
            [sys.executable, MEMORY_CLI, "code-stats"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if "Entities:" in line or "Relations:" in line:
                    print(f"   {line.strip()}")
            mongo_available = True
        else:
            print(f"   ⚠️  code-stats failed (exit {result.returncode})")
    except FileNotFoundError:
        print(f"   ⚠️  kora_memory.py not found at {MEMORY_CLI}")
        return False
    except subprocess.TimeoutExpired:
        print("   ⚠️  MongoDB timeout — connection issue")
        return False
    except Exception as e:
        print(f"   ⚠️  MongoDB check error: {e}")
        return False

    # Check 2: Session MongoDB usage score
    MONGO_SCORE_FILE = "/tmp/.kora_mongo_score"
    if os.path.exists(MONGO_SCORE_FILE):
        try:
            with open(MONGO_SCORE_FILE) as sf:
                score = int(sf.read().strip() or 0)
            if score > 0:
                print(f"   🎯 Session MongoDB score: {score} trace(s)")
            else:
                print(f"   ⚠️  Session MongoDB score: 0 — MongoDB NOT used yet this session")
        except Exception:
            pass
    else:
        print("   🆕 New session — MongoDB score starts at 0")

    # Check 3: Today's entries count
    try:
        today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        result = subprocess.run(
            [sys.executable, MEMORY_CLI, "query", "--date-from", today_utc, "--limit", "1"],
            capture_output=True, text=True, timeout=10
        )
        # Count entries by counting numbered lines (each entry starts with "N.")
        entry_count = 0
        for line in result.stdout.strip().split("\n"):
            if line.strip() and (line.strip()[0].isdigit() and "." in line[:3]):
                entry_count += 1
        if entry_count > 0:
            print(f"   📝 Today's entries: {entry_count}")
        else:
            print("   📝 No entries today yet")
    except Exception:
        pass  # Non-critical, skip silently

    return mongo_available


def check_project_state():
    """Check project state for session handoff context."""
    projects = []
    if os.path.isdir(PROJECT_STATE_DIR):
        for f in sorted(os.listdir(PROJECT_STATE_DIR)):
            if f.endswith(".md") and f != "session-tracker-last.md":
                projects.append(f.replace(".md", ""))

    last_session = None
    active_project = None
    try:
        with open(SESSION_TRACKER, "r") as f:
            for line in f:
                l = line.strip()
                if "Last Updated:" in l:
                    last_session = l.split("Last Updated:")[-1].strip()
                if "Active Project:" in l:
                    active_project = l.split("Active Project:")[-1].strip()
    except (FileNotFoundError, IOError):
        pass

    return projects, last_session, active_project


def main():
    # Parse flags
    json_output = "--json" in sys.argv
    no_fail = "--no-fail" in sys.argv

    # Phase 2: Clean stale session lock files (prevents deadlock)
    cleanup_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cleanup_session_locks.sh")
    if os.path.exists(cleanup_script):
        import subprocess
        try:
            result = subprocess.run(
                ["bash", cleanup_script],
                capture_output=True, text=True, timeout=15
            )
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    print(f"  {line}")
            if result.returncode != 0:
                print(f"  ⚠ Lock cleanup stderr: {result.stderr.strip()}")
        except Exception as e:
            print(f"  ⚠ Lock cleanup failed: {e}")
    print()

    # Phase 3: Check project state / session handoff
    projects, last_session, active_project = check_project_state()
    
    # 🚨 HELPER-FIRST REFLEX REMINDER
    print("🔔 HELPER REFLEX: Task arrives → check: \"Is there a helper for this?\"")
    print("   HEARTBEAT.md → helpers | OPS_REFERENCE.md → triggers | SOUL.md → decision tree")
    print("   NEVER SSH / read code / grep manually. Always spawn agents.")
    print()

    # 🧠 Phase 4: MongoDB Memory System Check (Rule #69)
    print("🧠 MONGO REFLEX: Bug/function/endpoint/table → kora_memory.py trace FIRST, grep SECOND")
    mongo_ok = _check_mongo()
    if mongo_ok:
        print("   ✅ MongoDB available — use kora_memory.py trace/search BEFORE grep/read")
    else:
        print("   ⚠️  MongoDB unavailable — fallback to grep (report to Boss)")
    print()
    
    if projects:
        print(f"📊 Projects: {', '.join(projects)}")
    if active_project:
        print(f"📌 Active: {active_project}")
    if last_session:
        print(f"🕐 Last session: {last_session}")

        # Check if session is stale
        try:
            last_dt = datetime.fromisoformat(last_session.replace(" UTC", "+00:00"))
            hours_since = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
            if hours_since > 4:
                print(f"⏰ {hours_since:.1f}h since last session — please check project state")
        except ValueError:
            pass
    print()

    journal = load_json(JOURNAL_PATH, {"entries": []})
    entries = journal.get("entries", [])

    active_registry = load_json(ACTIVE_TASKS_PATH, {"version": 1, "active": {}})
    active_tasks = active_registry.get("active", {})

    running = []
    partial = []

    for e in entries:
        status = e.get("status")
        completed = e.get("completed")

        if status == "running" or completed is None:
            running.append(e)
        if status == "partial":
            partial.append(e)

    orphans = detect_orphans(active_tasks, entries)
    stale = detect_stale(entries)

    has_incomplete = bool(running or partial or orphans or stale)

    if json_output:
        output = build_json_output(running, partial, orphans, stale)
        print(json.dumps(output, indent=2, ensure_ascii=False))
        if no_fail:
            return 0
        return 1 if has_incomplete else 0

    # Human-readable output
    if running:
        print("🔴 RUNNING TASKS FOUND:")
        for e in running:
            name = e.get("taskName", "unknown")
            spawned = format_timestamp(e.get("spawned", "unknown"))
            summary = e.get("summary", "no summary")
            print(f"   ✅ {name} (spawned: {spawned})")
            if summary:
                print(f"     {summary}")
        print()

    if partial:
        print("🟡 PARTIAL TASKS:")
        for e in partial:
            name = e.get("taskName", "unknown")
            spawned = format_timestamp(e.get("spawned", "unknown"))
            summary = e.get("summary", "no summary")
            print(f"   ✅ {name} (spawned: {spawned})")
            if summary:
                print(f"     {summary}")
        print()

    if orphans:
        print("🔴 ORPHANED TASKS (active_tasks.json but not in journal):")
        for tid, tdata in orphans:
            name = tdata.get("taskName", "unknown")
            spawned = format_timestamp(tdata.get("spawned", "unknown"))
            goal = tdata.get("goal", "no goal")
            print(f"   ⚠  {tid}: {name} (spawned: {spawned})")
            if goal:
                print(f"     Goal: {goal}")
        print()

    if stale:
        print("🟡 STALE TASKS (running >{}min in journal):".format(STALE_THRESHOLD_MINUTES))
        for s in stale:
            e = s["entry"]
            name = e.get("taskName", "unknown")
            spawned = format_timestamp(e.get("spawned", "unknown"))
            print(f"   ⏳ {name} (spawned: {spawned}, age: {s['ageMinutes']}min)")
        print()

    if not has_incomplete:
        print("✅ All tasks complete")

    if no_fail:
        return 0
    return 1 if has_incomplete else 0


if __name__ == "__main__":
    sys.exit(main())
