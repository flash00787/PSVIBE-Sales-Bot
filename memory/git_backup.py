#!/usr/bin/env python3
"""
Git Auto-Backup — Kora Memory System (Phase 3, Item 6)
stdlib only: subprocess, os, sys, datetime

Commands:
  --init               Initialize git repo at memory/ if not exists
  --commit "msg"       Add all + commit with given message
  --auto               Auto-commit with timestamp message (inits if needed)
  --status             Show git status summary
  --log [N]            Show last N commits (default 5)
"""

import os
import sys
import subprocess
import datetime
import argparse

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GITIGNORE = os.path.join(REPO_DIR, ".gitignore")
GITIGNORE_CONTENT = """# Kora Memory — gitignore
*.b64
*.tar.gz
*.pyc
__pycache__/
node_modules/
.git/
"""


def run_git(args, cwd=None, check=True, capture=True):
    """Run a git command, return stdout or raise on error."""
    if cwd is None:
        cwd = REPO_DIR
    cmd = ["git"] + args
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture,
            text=True,
            check=check,
        )
        return result.stdout.strip() if capture else ""
    except subprocess.CalledProcessError as e:
        if not check:
            return ""
        print(f"[ERROR] git {' '.join(args)}", file=sys.stderr)
        if e.stderr:
            print(f"  {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def git_repo_exists():
    """Return True if .git directory exists under REPO_DIR."""
    return os.path.isdir(os.path.join(REPO_DIR, ".git"))


def ensure_safe_dir():
    """Add REPO_DIR to git safe.directory config to avoid dubious-ownership errors."""
    try:
        subprocess.run(
            ["git", "config", "--global", "--add", "safe.directory", REPO_DIR],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        pass  # Non-fatal — may already be configured


def ensure_git_config():
    """Set minimal git user config if missing, so commits don't fail."""
    for key, value in [("user.name", "Kora"), ("user.email", "kora@local")]:
        try:
            result = subprocess.run(
                ["git", "config", "--global", key],
                capture_output=True,
                text=True,
                check=False,
            )
            if not result.stdout.strip():
                subprocess.run(
                    ["git", "config", "--global", key, value],
                    capture_output=True,
                    text=True,
                    check=False,
                )
        except Exception:
            pass


def cmd_init():
    """Initialize git repo and create .gitignore."""
    if git_repo_exists():
        print("[OK] Git repo already initialized.")
        return

    ensure_safe_dir()
    ensure_git_config()

    print("[INIT] Initializing git repository...")
    run_git(["init"])

    # Create .gitignore
    with open(GITIGNORE, "w") as f:
        f.write(GITIGNORE_CONTENT)
    print(f"[OK] Created .gitignore at {GITIGNORE}")

    # Initial add + commit of .gitignore
    run_git(["add", ".gitignore"])
    run_git(["commit", "-m", "[KORA MEMORY] Repo initialized"])
    print("[OK] Git repo initialized successfully.")


def cmd_commit(message):
    """Add all files and commit with the given message."""
    if not git_repo_exists():
        print("[ERROR] Git repo not initialized. Run --init first.", file=sys.stderr)
        sys.exit(1)

    ensure_safe_dir()
    ensure_git_config()

    # Stage everything
    run_git(["add", "-A"])

    # Check if there's anything to commit
    status_out = run_git(["status", "--porcelain"])
    if not status_out:
        print("[OK] Nothing to commit — working tree clean.")
        return

    # Commit
    try:
        run_git(["commit", "-m", message])
    except SystemExit:
        # Fallback with explicit author if git config is missing
        run_git([
            "commit",
            "-m", message,
            "--author=Kora <kora@local>",
        ])

    # Count files
    files = [l for l in status_out.split("\n") if l.strip()]
    print(f"[OK] Committed {len(files)} file(s): \"{message}\"")


def cmd_auto():
    """Auto-commit with timestamp message. Inits repo if needed."""
    ensure_safe_dir()
    ensure_git_config()

    if not git_repo_exists():
        print("[AUTO] Repo not initialized — running --init first...")
        cmd_init()

    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M")
    message = f"[KORA MEMORY] {timestamp}"
    cmd_commit(message)


def cmd_status():
    """Show git status summary."""
    if not git_repo_exists():
        print("[ERROR] Git repo not initialized. Run --init first.", file=sys.stderr)
        sys.exit(1)

    ensure_safe_dir()

    # Short status
    porcelain = run_git(["status", "--porcelain"])
    if porcelain:
        lines = porcelain.split("\n")
        added = sum(1 for l in lines if l.startswith("A") or l.startswith("?? "))
        modified = sum(1 for l in lines if l.startswith(" M") or l.startswith("M "))
        deleted = sum(1 for l in lines if l.startswith(" D") or l.startswith("D "))
        renamed = sum(1 for l in lines if l.startswith("R "))
        print(f"[STATUS] Changes pending:")
        print(f"  New/Untracked: {added}")
        print(f"  Modified:      {modified}")
        print(f"  Deleted:       {deleted}")
        if renamed:
            print(f"  Renamed:       {renamed}")
        print(f"  Total:         {len(lines)}")
    else:
        print("[STATUS] Working tree clean — no changes.")

    # Branch info
    try:
        branch = run_git(["branch", "--show-current"])
        print(f"  Branch: {branch}")
    except SystemExit:
        pass


def cmd_log(n=5):
    """Show last N commits."""
    if not git_repo_exists():
        print("[ERROR] Git repo not initialized. Run --init first.", file=sys.stderr)
        sys.exit(1)

    ensure_safe_dir()

    try:
        output = run_git([
            "log",
            f"-{n}",
            "--oneline",
            "--decorate",
        ])
    except SystemExit:
        output = run_git([
            "log",
            f"-{n}",
            "--pretty=format:%h %s",
        ])

    if output:
        print(f"[LOG] Last {n} commits:")
        for line in output.split("\n"):
            print(f"  {line}")
    else:
        print("[LOG] No commits yet.")


def main():
    parser = argparse.ArgumentParser(
        description="Kora Memory Git Auto-Backup",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize git repo (safe if already exists)",
    )
    parser.add_argument(
        "--commit",
        type=str,
        metavar="MSG",
        help="Add all files and commit with message",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-commit with timestamp (inits repo if needed)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show git status summary",
    )
    parser.add_argument(
        "--log",
        type=int,
        nargs="?",
        const=5,
        metavar="N",
        help="Show last N commits (default 5)",
    )

    args = parser.parse_args()

    # Dispatch
    if args.init:
        cmd_init()
    elif args.commit:
        cmd_commit(args.commit)
    elif args.auto:
        cmd_auto()
    elif args.status:
        cmd_status()
    elif args.log is not None:
        cmd_log(args.log)
    else:
        # No args — show usage
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
