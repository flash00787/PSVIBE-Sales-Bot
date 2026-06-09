#!/usr/bin/env python3
"""
Task Retry Helper — Spawns a new sub-agent to retry a failed/partial task.

Usage:
    python3 task_retry.py <task-id> [--summary "optional context"]

Reads the failed task from subagent-journal.json, prints recommended
retry instructions for the user to copy as a new sessions_spawn call.
"""

import json
import os
import sys

MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
JOURNAL_PATH = os.path.join(MEMORY_DIR, "subagent-journal.json")


def load_journal(path):
    with open(path, "r") as f:
        return json.load(f)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 task_retry.py <task-id> [--summary \"context\"]")
        sys.exit(1)

    task_id = sys.argv[1]

    # Extract optional summary override
    extra_summary = ""
    for i, arg in enumerate(sys.argv):
        if arg == "--summary" and i + 1 < len(sys.argv):
            extra_summary = sys.argv[i + 1]

    journal = load_journal(JOURNAL_PATH)
    entries = journal.get("entries", [])

    # Find the task
    target = None
    for e in entries:
        if e.get("id") == task_id:
            target = e
            break

    if target is None:
        print(f"❌ Task '{task_id}' not found in journal.")
        sys.exit(1)

    task_name = target.get("taskName", "unknown")
    status = target.get("status", "unknown")
    summary = target.get("summary", "")
    model = target.get("model", "deepseek/deepseek-v4-pro")

    print(f"=== Retry Task: {task_id} ({task_name}) ===")
    print(f"  Previous status: {status}")
    print(f"  Previous summary: {summary}")
    if extra_summary:
        print(f"  Additional context: {extra_summary}")
    print()
    print("To retry, spawn a new sub-agent with this task:")
    print()
    print(f"  sessions_spawn:")
    print(f"    taskName: retry-{task_name}")
    if model:
        print(f"    model: {model}")
    print(f"    task: |")
    print(f"      RETRY: {task_name}")
    print(f"      Previous attempt failed/partial: {summary}")
    if extra_summary:
        print(f"      Context: {extra_summary}")
    print(f"      Read current state, finish remaining work.")
    print()


if __name__ == "__main__":
    main()
