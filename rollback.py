#!/usr/bin/env python3
"""Emergency rollback when validation fails.

Usage:
    python3 rollback.py --backup /root/backups/pre-task-20260528_183000.tar.gz
    python3 rollback.py --latest                    # Use latest backup
    python3 rollback.py list                        # List available backups

Steps:
1. Stop all 3 services
2. Restore from backup
3. Restart all 3 services
4. Validate again
"""

import os
import sys
import subprocess
import argparse
import tarfile
import glob
import time

BOT_DIR = "/root/psvibe-sales-bot"
BACKUP_DIR = "/root/backups"
SERVICES = [
    "psvibe-sale-bot.service",
    "psvibe_customer_bot.service",
    "psvibe-api.service",
]


def _run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"


def _stop_services():
    print("🛑 Stopping all services...")
    for svc in SERVICES:
        rc, out, err = _run(f"systemctl stop {svc}")
        if rc == 0:
            print(f"  ✅ {svc} stopped")
        else:
            print(f"  ⚠ {svc} stop: {err[:100]}")


def _start_services():
    print("▶️ Starting all services...")
    for svc in SERVICES:
        rc, out, err = _run(f"systemctl start {svc}")
        if rc == 0:
            print(f"  ✅ {svc} started")
        else:
            print(f"  ❌ {svc} start failed: {err[:100]}")
    time.sleep(3)


def _restore_tar(backup_path):
    print(f"📦 Restoring from: {backup_path}")
    if not os.path.exists(backup_path):
        print(f"  ❌ Backup not found: {backup_path}")
        return False

    # Remove current bot dir (but keep backups)
    _run(f"rm -rf {BOT_DIR}")

    # Extract backup
    with tarfile.open(backup_path, "r:gz") as tar:
        tar.extractall("/root")

    print(f"  ✅ Restored {BOT_DIR} from backup")
    return True


def _restore_individual(backup_dir):
    """Restore individual files from a files backup directory."""
    if not os.path.isdir(backup_dir):
        return False
    print(f"📄 Restoring individual files from: {backup_dir}")
    for fname in os.listdir(backup_dir):
        src = os.path.join(backup_dir, fname)
        # Convert filename back to path
        rel_path = fname.replace("_", "/")
        dst = os.path.join(BOT_DIR, rel_path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(src) as fin:
            with open(dst, "w") as fout:
                fout.write(fin.read())
        print(f"  ✅ Restored: {rel_path}")
    return True


def cmd_rollback(args):
    print("=" * 55)
    print("🔄 EMERGENCY ROLLBACK")
    print("=" * 55)

    if args.latest:
        backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "pre-*.tar.gz")), reverse=True)
        if not backups:
            print("❌ No backups found!")
            sys.exit(1)
        backup_path = backups[0]
        print(f"📂 Using latest backup: {os.path.basename(backup_path)}")
    elif args.backup:
        backup_path = args.backup
    else:
        print("❌ Specify --backup or --latest")
        sys.exit(1)

    # Step 1: Stop services
    _stop_services()

    # Step 2: Restore
    ok = _restore_tar(backup_path)

    # Also check for individual files backup (same name but -files suffix)
    files_dir = backup_path.replace(".tar.gz", "-files")
    if os.path.isdir(files_dir):
        _restore_individual(files_dir)

    if not ok:
        print("❌ Rollback FAILED")
        sys.exit(1)

    # Step 3: Start services
    _start_services()

    # Step 4: Quick validation
    print("🔍 Running quick validation...")
    rc, out, err = _run(f"cd {BOT_DIR} && python3 -m py_compile bot/__init__.py 2>&1")
    if rc == 0:
        print("  ✅ Code compiles")
    else:
        print(f"  ⚠ Compile warning (may need manual fix): {out[:200]}")

    # Check services
    for svc in SERVICES:
        rc, out, err = _run(f"systemctl is-active {svc}")
        if out == "active":
            print(f"  ✅ {svc} running")
        else:
            print(f"  ❌ {svc} → {out}")

    print()
    print("🎉 Rollback complete!")
    print(f"   Backup used: {backup_path}")
    print("   Validate with: python3 /root/coordination/validate.py")


def cmd_list(args):
    backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "pre-*.tar.gz")), reverse=True)
    if not backups:
        print("No backups found.")
        return
    print(f"{'Backup File':<55} {'Size':<10} {'Date':<20}")
    print("-" * 85)
    for b in backups:
        name = os.path.basename(b)
        size = os.path.getsize(b)
        size_str = f"{size//1024}KB" if size < 1024*1024 else f"{size//(1024*1024)}MB"
        mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(b)))
        print(f"{name:<55} {size_str:<10} {mtime:<20}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Emergency rollback")
    sub = parser.add_subparsers(dest="cmd")

    p_rollback = sub.add_parser("rollback")
    p_rollback.add_argument("--backup", help="Backup file path")
    p_rollback.add_argument("--latest", action="store_true", help="Use latest backup")

    sub.add_parser("list")

    args = parser.parse_args()
    if args.cmd == "rollback":
        cmd_rollback(args)
    elif args.cmd == "list":
        cmd_list(args)
    else:
        parser.print_help()
