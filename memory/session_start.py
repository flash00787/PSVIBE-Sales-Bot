#!/usr/bin/env python3
"""
Kora Session Start Marker — Phase 2 Context Awareness
Adds a timestamped session-start marker to session-memory.md,
then runs boot_protocol.py to check for incomplete tasks.
Uses only stdlib.
"""

import subprocess
import sys
import os
from datetime import datetime, timezone

MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_MEMORY_PATH = os.path.join(MEMORY_DIR, "session-memory.md")
BOOT_PROTOCOL_PATH = os.path.join(MEMORY_DIR, "boot_protocol.py")


def add_session_marker(path):
    now = datetime.now(timezone.utc)
    marker = f"\n### 🟢 Session Start — {now.strftime('%Y-%m-%d %H:%M UTC')}\n"

    with open(path, "a") as f:
        f.write(marker)

    return now


def run_boot_protocol():
    result = subprocess.run(
        [sys.executable, BOOT_PROTOCOL_PATH],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    return result.returncode


def main():
    session_time = add_session_marker(SESSION_MEMORY_PATH)
    print(f"Session started: {session_time.strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    exit_code = run_boot_protocol()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
