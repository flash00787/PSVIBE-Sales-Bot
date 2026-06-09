#!/usr/bin/env python3
"""Sub-agent coordination lock manager.

Usage:
    python3 lock_manager.py acquire --agent <name> --files "<file1,file2>" --reason "..."
    python3 lock_manager.py release --agent <name>
    python3 lock_manager.py status
    python3 lock_manager.py check --file "<path>"
    python3 lock_manager.py force-release --older-than <minutes>
"""

import os
import sys
import json
import time
import argparse

LOCK_DIR = "/root/coordination/.locks"
LOCK_FILE = "/root/coordination/AGENT_LOCKS.md"


def _lock_path(agent, filepath):
    safe = filepath.replace("/", "_").replace(".", "_")
    return os.path.join(LOCK_DIR, f"{agent}.{safe}.lock")


def _all_locks():
    locks = {}
    if not os.path.isdir(LOCK_DIR):
        return locks
    for fname in os.listdir(LOCK_DIR):
        if not fname.endswith(".lock"):
            continue
        fpath = os.path.join(LOCK_DIR, fname)
        try:
            with open(fpath) as f:
                data = json.load(f)
            agent = data["agent"]
            locks[agent] = data
        except (json.JSONDecodeError, KeyError):
            pass
    return locks


def _write_lock(agent, files, reason):
    os.makedirs(LOCK_DIR, exist_ok=True)
    data = {
        "agent": agent,
        "files": files,
        "reason": reason,
        "started": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "started_ts": time.time(),
    }
    for f in files:
        lp = _lock_path(agent, f)
        with open(lp, "w") as fh:
            json.dump(data, fh)
    _update_md()
    return data


def _remove_lock(agent):
    removed = []
    if not os.path.isdir(LOCK_DIR):
        return removed
    for fname in os.listdir(LOCK_DIR):
        if fname.startswith(f"{agent}.") and fname.endswith(".lock"):
            os.remove(os.path.join(LOCK_DIR, fname))
            removed.append(fname)
    _update_md()
    return removed


def _is_locked(filepath):
    for agent, data in _all_locks().items():
        if filepath in data.get("files", []):
            return agent
    return None


def _update_md():
    locks = _all_locks()
    lines = [
        "# Agent Locks — AUTO-GENERATED — DO NOT EDIT\n",
        "",
        "## Active Agents",
    ]
    if not locks:
        lines.append("*No active agents*")
    else:
        lines.append("| Agent ID | Task | Files Locked | Started |")
        lines.append("|----------|------|-------------|---------|")
        for agent, data in locks.items():
            files = ", ".join(data.get("files", []))
            started = data.get("started", "?")
            reason = data.get("reason", "?")
            lines.append(f"| {agent} | {reason} | {files} | {started} |")

    lines += [
        "",
        "## File Lock Table",
        "| File | Locked By | Started | Status |",
        "|------|-----------|---------|--------|",
        "| bot/__init__.py | :red_square: RESERVED | --- | NEVER parallel |",
        "| bot/app.py | :red_square: RESERVED | --- | NEVER parallel |",
    ]
    for agent, data in locks.items():
        for f in data.get("files", []):
            lines.append(f"| {f} | {agent} | {data.get('started','?')} | :lock: locked |")

    lines.append("")
    with open(LOCK_FILE, "w") as fh:
        fh.write("\n".join(lines))


def cmd_acquire(args):
    files = [f.strip() for f in args.files.split(",")]
    for f in files:
        existing = _is_locked(f)
        if existing:
            print(f"FAIL: {f} already locked by {existing}")
            sys.exit(1)
    data = _write_lock(args.agent, files, args.reason)
    print(f"Lock acquired: {args.agent} -> {files}")
    return data


def cmd_release(args):
    removed = _remove_lock(args.agent)
    if removed:
        print(f"Released: {args.agent} ({len(removed)} locks removed)")
    else:
        print(f"No locks found for {args.agent}")


def cmd_status(args):
    locks = _all_locks()
    if not locks:
        print("No active locks")
        return
    print(f"{len(locks)} active lock(s):")
    for agent, data in locks.items():
        files = ", ".join(data.get("files", []))
        started = data.get("started", "?")
        reason = data.get("reason", "?")
        age_m = int((time.time() - data.get("started_ts", 0)) / 60)
        print(f"  [{agent}] {reason}")
        print(f"    Files: {files}")
        print(f"    Since: {started} ({age_m}m ago)")


def cmd_check(args):
    agent = _is_locked(args.file)
    if agent:
        print(f"LOCKED by: {agent}")
        sys.exit(0)
    else:
        print(f"FREE")
        sys.exit(0)


def cmd_force_release(args):
    cutoff = time.time() - (args.older_than * 60)
    released = []
    for agent, data in _all_locks().items():
        if data.get("started_ts", 0) < cutoff:
            _remove_lock(agent)
            released.append(agent)
    if released:
        print(f"Force-released stale locks: {released}")
    else:
        print("No stale locks found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sub-agent lock manager")
    sub = parser.add_subparsers(dest="cmd")

    p_acquire = sub.add_parser("acquire")
    p_acquire.add_argument("--agent", required=True)
    p_acquire.add_argument("--files", required=True)
    p_acquire.add_argument("--reason", required=True)

    p_release = sub.add_parser("release")
    p_release.add_argument("--agent", required=True)

    sub.add_parser("status")

    p_check = sub.add_parser("check")
    p_check.add_argument("--file", required=True)

    p_fr = sub.add_parser("force-release")
    p_fr.add_argument("--older-than", type=int, required=True)

    args = parser.parse_args()
    if args.cmd == "acquire":
        cmd_acquire(args)
    elif args.cmd == "release":
        cmd_release(args)
    elif args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "check":
        cmd_check(args)
    elif args.cmd == "force-release":
        cmd_force_release(args)
    else:
        parser.print_help()
