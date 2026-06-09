#!/usr/bin/env python3
"""Pre-flight check before spawning a sub-agent.

Usage:
    python3 preflight.py check --agent fix-bug --files "bot/handlers/sales.py"
    python3 preflight.py backup
    python3 preflight.py backup --task-name fix-bug

Returns:
    PASS / WARN / FAIL (exit code 0/1/2)
"""

import os
import sys
import subprocess
import argparse
import tarfile
from datetime import datetime

BOT_DIR = "/root/psvibe-sales-bot"
LOCK_MGR = "/root/coordination/lock_manager.py"
BACKUP_DIR = "/root/backups"


def _run(cmd, timeout=30):
    """Run a shell command, return (rc, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"


def _check_locks(files):
    """Check if any target file is locked by another agent."""
    issues = []
    for f in files:
        if not f.strip():
            continue
        rc, out, err = _run(f"python3 {LOCK_MGR} check --file \"{f}\"" 2>/dev/null)
        # lock_manager returns exit 0 for LOCKED
        if "LOCKED" in out:
            issues.append(f"  LOCKED: {f} -> {out}")
    return issues


def _check_services():
    """Check all 3 services are healthy."""
    services = [
        ("Sale Bot", "psvibe-sale-bot.service"),
        ("Customer Bot", "psvibe_customer_bot.service"),
        ("API Server", "psvibe-api.service"),
    ]
    issues = []
    for name, svc in services:
        rc, out, err = _run(f"systemctl is-active {svc}")
        if out != "active":
            issues.append(f"  DOWN: {name} ({svc}) -> {out}")
    return issues


def _check_compile():
    """Check all .py files compile."""
    rc, out, err = _run(
        f"cd {BOT_DIR} && errors=0 && "
        f"for f in $(find . -name '*.py'); do "
        f"  python3 -m py_compile \"$f\" 2>&1 | grep -v '^$' && errors=$((errors+1)); "
        f"done; echo \"TOTAL_ERR=$errors\""
    )
    for line in out.split("\n"):
        if "TOTAL_ERR=" in line:
            n = int(line.split("=")[1])
            if n > 0:
                return [f"  COMPILE_FAIL: {n} file(s) with errors"]
            return []
    return []


def _check_imports():
    """Check bot imports work (with env vars from secrets file)."""
    env_file = "/etc/psvibe/secrets.env"
    rc, out, err = _run(
        f"cd {BOT_DIR} && "
        f"export $(grep -v '^#' {env_file} 2>/dev/null | xargs) 2>/dev/null && "
        f"python3 -c 'import sys; sys.path.insert(0,"."); from bot import __name__; print("IMPORT_OK")' 2>&1 | tail -5"
    )
    if "IMPORT_OK" in out:
        return []
    return [f"  IMPORT_FAIL: {out[:300]}"]


def cmd_check(args):
    """Run full pre-flight check."""
    files = [f.strip() for f in args.files.split(",")] if args.files else []

    all_issues = []
    warnings = []

    print("Checking locks...")
    lock_issues = _check_locks(files)
    all_issues.extend(lock_issues)
    if lock_issues:
        for i in lock_issues:
            print(f"  {i}")

    print("Checking services...")
    svc_issues = _check_services()
    all_issues.extend(svc_issues)
    if svc_issues:
        for i in svc_issues:
            print(f"  {i}")
    else:
        print("  All services active")

    print("Checking code compilation...")
    compile_issues = _check_compile()
    all_issues.extend(compile_issues)
    if compile_issues:
        for i in compile_issues:
            print(f"  {i}")
    else:
        print("  All files compile OK")

    print("Checking imports...")
    import_issues = _check_imports()
    all_issues.extend(import_issues)
    if import_issues:
        for i in import_issues:
            print(f"  {i}")
    else:
        print("  Imports OK")

    print()
    print("=" * 45)
    print("PRE-FLIGHT CHECK RESULTS")
    print("=" * 45)

    if all_issues:
        print(f"\nBLOCKED - {len(all_issues)} issue(s)")
        sys.exit(1)
    else:
        print("\nALL CHECKS PASSED - safe to spawn")
        sys.exit(0)


def cmd_backup(args):
    """Create timestamped backup of bot directory."""
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    task = args.task_name or "unknown"
    backup_file = os.path.join(BACKUP_DIR, f"pre-{task}-{ts}.tar.gz")

    os.makedirs(BACKUP_DIR, exist_ok=True)

    with tarfile.open(backup_file, "w:gz") as tar:
        tar.add(BOT_DIR, arcname="psvibe-sales-bot")

    size_kb = os.path.getsize(backup_file) // 1024
    print(f"Backup created: {backup_file} ({size_kb} KB)")
    return backup_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-flight spawn checker")
    sub = parser.add_subparsers(dest="cmd")

    p_check = sub.add_parser("check")
    p_check.add_argument("--agent", required=True, help="Agent name/task ID")
    p_check.add_argument("--files", help="Files to modify (comma-separated)")

    p_backup = sub.add_parser("backup")
    p_backup.add_argument("--task-name", default="manual", help="Task name for backup")

    args = parser.parse_args()
    if args.cmd == "check":
        cmd_check(args)
    elif args.cmd == "backup":
        cmd_backup(args)
    else:
        parser.print_help()
        sys.exit(1)
