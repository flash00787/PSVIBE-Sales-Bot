#!/usr/bin/env python3
"""
Sub-agent Safety Net — prevents "incomplete turn" errors by ensuring
every spawned sub-agent produces output even when things go wrong.

Usage:
    python3 memory/subagent_safety.py validate <task_description_file>
    python3 memory/subagent_safety.py wrap <command>

PREVENTION: When writing sessions_spawn task descriptions, always include:
  "SAFETY NET: You MUST end your output with '=== RESULT: OK ||| ERROR: <reason> ==='.
   If anything fails, write to the temp file and output '=== RESULT: ERROR === <details>'.
   NEVER stop without producing output."
"""

import sys
import os


def validate_task(task_text: str) -> list[str]:
    """Check if a task description has proper safety net."""
    issues = []
    
    required_patterns = [
        ("output file", ["write", "output", "save", "temp"]),
        ("safety net", ["safety", "error", "fail", "never stop"]),
        ("completion marker", ["result", "done", "complete", "finish"]),
    ]
    
    text_lower = task_text.lower()
    
    for name, keywords in required_patterns:
        if not any(kw in text_lower for kw in keywords):
            issues.append(f"Missing: {name} indicator (expected one of: {keywords})")
    
    return issues


def check_stuck_subagents():
    """Quick check for sub-agents that may have stopped without completing."""
    import json
    import time
    
    active_path = "/home/node/.openclaw/workspace/memory/active_tasks.json"
    if not os.path.exists(active_path):
        return "No active tasks file"
    
    with open(active_path) as f:
        tasks = json.load(f)
    
    now = time.time()
    stuck = []
    
    for task in tasks:
        if task.get("status") not in ("running", "pending"):
            continue
        age = now - task.get("started_at", now)
        if age > 900:  # 15 min stuck threshold
            stuck.append({
                "id": task.get("id"),
                "name": task.get("name"),
                "age_min": round(age / 60, 1),
                "model": task.get("model", "unknown"),
            })
    
    if not stuck:
        return "All active tasks healthy"
    
    return f"⚠️ {len(stuck)} stuck task(s): {[t['name'] for t in stuck]}"


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "validate":
        # Read from stdin or file
        text = sys.stdin.read() if not sys.stdin.isatty() else ""
        if not text and len(sys.argv) >= 3:
            with open(sys.argv[2]) as f:
                text = f.read()
        issues = validate_task(text)
        if issues:
            print("❌ SAFETY ISSUES:")
            for i in issues:
                print(f"  • {i}")
            sys.exit(1)
        else:
            print("✅ Task safety check passed")
    
    elif len(sys.argv) >= 2 and sys.argv[1] == "check":
        print(check_stuck_subagents())
    
    else:
        print(__doc__.strip())
