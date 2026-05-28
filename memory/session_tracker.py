#!/usr/bin/env python3
"""
Session Tracker — Writes session start/end markers and cross-reference data.
Used by boot protocol and shutdown hooks.

Usage:
    python3 session_tracker.py start   # Record session start
    python3 session_tracker.py end     # Record session end
"""

import json
import os
import sys
from datetime import datetime, timezone

MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKER_PATH = os.path.join(MEMORY_DIR, "session-tracker-last.md")
MEMORY_PATH = os.path.join(MEMORY_DIR, "session-memory.md")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mark_start():
    ts = now_iso()
    with open(TRACKER_PATH, "w") as f:
        f.write("# Session Tracker — Last Run\n\n")
        f.write(f"**Timestamp:** {ts}\n\n")
        f.write("Status: running\n")
    with open(MEMORY_PATH, "a") as f:
        f.write(f"\n### 🟢 Session Start — {ts}\n")
    print(f"[TRACKER] Session started at {ts}")


def mark_end():
    ts = now_iso()
    with open(TRACKER_PATH, "w") as f:
        f.write("# Session Tracker — Last Run\n\n")
        f.write(f"**Timestamp:** {ts}\n\n")
        f.write("Status: completed\n")
    with open(MEMORY_PATH, "a") as f:
        f.write(f"\n### 🔴 Session End — {ts}\n")
    print(f"[TRACKER] Session ended at {ts}")


def main():
    if len(sys.argv) < 2:
        print("Usage: session_tracker.py start|end")
        sys.exit(1)

    action = sys.argv[1].lower()
    if action == "start":
        mark_start()
    elif action == "end":
        mark_end()
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
