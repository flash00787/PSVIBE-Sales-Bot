#!/usr/bin/env python3
"""
Memory Maintenance — Orchestrates Kora's memory script pipeline.

Runs integrated scripts in correct order with graceful error handling.

Usage:
    python3 memory/memory_maintenance.py              # Quick status overview
    python3 memory/memory_maintenance.py --heartbeat   # Heartbeat pipeline (index → graph → backup)
    python3 memory/memory_maintenance.py --manual      # Manual pipeline (summary → digest → audit → pruner-dry-run)
    python3 memory/memory_maintenance.py --run-all     # Full pipeline (heartbeat + manual)
    python3 memory/memory_maintenance.py --dry-run     # Preview only — print commands, don't execute
    python3 memory/memory_maintenance.py --step <name> # Run a single step by name

Steps (by name):
    index-rebuild       → memory_index --rebuild
    graph-rebuild       → knowledge_graph --rebuild
    git-backup          → git_backup --auto
    session-summary     → session_summary --generate --session YYYY-MM-DD
    daily-digest        → daily_digest --all
    priority-audit      → priority_engine --audit
    pruner-status       → memory_pruner --status
    pruner-dryrun       → memory_pruner --dry-run

Heartbeat pipeline:  index-rebuild → graph-rebuild → git-backup
Manual pipeline:     session-summary → daily-digest → priority-audit → pruner-status → pruner-dryrun

NOTE: memory_pruner --apply is NEVER run automatically. Always review --dry-run first.
"""

import os
import sys
import subprocess
import argparse
import time
from datetime import datetime, timezone

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(SCRIPT_DIR)

SCRIPTS = {
    "memory_index.py": os.path.join(SCRIPT_DIR, "memory_index.py"),
    "knowledge_graph.py": os.path.join(SCRIPT_DIR, "knowledge_graph.py"),
    "git_backup.py": os.path.join(SCRIPT_DIR, "git_backup.py"),
    "daily_digest.py": os.path.join(SCRIPT_DIR, "daily_digest.py"),
    "priority_engine.py": os.path.join(SCRIPT_DIR, "priority_engine.py"),
    "memory_pruner.py": os.path.join(SCRIPT_DIR, "memory_pruner.py"),
    "session_summary.py": os.path.join(SCRIPT_DIR, "session_summary.py"),
}

# ── Step definitions ───────────────────────────────────────────────────────
# Each step: (display_name, script, args, priority, auto_safe)
# auto_safe=True means safe for unattended/heartbeat execution

STEPS = {
    "index-rebuild": {
        "name": "Topic Index Rebuild",
        "script": "memory_index.py",
        "args": ["--rebuild"],
        "auto_safe": True,
    },
    "graph-rebuild": {
        "name": "Knowledge Graph Rebuild",
        "script": "knowledge_graph.py",
        "args": ["--rebuild"],
        "auto_safe": True,
    },
    "git-backup": {
        "name": "Git Auto-Backup",
        "script": "git_backup.py",
        "args": ["--auto"],
        "auto_safe": True,
    },
    "session-summary": {
        "name": "Session Summary",
        "script": "session_summary.py",
        "args": ["--generate", "--update-memory"],  # --session added dynamically
        "auto_safe": False,
        "needs_session_date": True,
    },
    "daily-digest": {
        "name": "Daily Digest (All)",
        "script": "daily_digest.py",
        "args": ["--all"],
        "auto_safe": False,
    },
    "priority-audit": {
        "name": "Priority Engine Audit",
        "script": "priority_engine.py",
        "args": ["--audit"],
        "auto_safe": False,
    },
    "pruner-status": {
        "name": "Pruner Status Check",
        "script": "memory_pruner.py",
        "args": ["--status"],
        "auto_safe": False,
    },
    "pruner-dryrun": {
        "name": "Pruner Dry-Run",
        "script": "memory_pruner.py",
        "args": ["--dry-run"],
        "auto_safe": False,
    },
}

# Pipelines
HEARTBEAT_PIPELINE = ["index-rebuild", "graph-rebuild", "git-backup"]
MANUAL_PIPELINE = ["session-summary", "daily-digest", "priority-audit", "pruner-status", "pruner-dryrun"]

# ── Helpers ────────────────────────────────────────────────────────────────

def get_today_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def run_step(step_name, dry_run=False, extra_args=None):
    """Execute a single step. Returns (success: bool, output: str, elapsed: float)."""
    step = STEPS.get(step_name)
    if not step:
        return False, f"Unknown step: {step_name}", 0.0

    script_path = SCRIPTS.get(step["script"])
    if not script_path or not os.path.isfile(script_path):
        return False, f"Script not found: {step['script']}", 0.0

    cmd = [sys.executable, script_path] + step["args"]
    if extra_args:
        cmd.extend(extra_args)

    if dry_run:
        return True, f"[DRY-RUN] Would run: {' '.join(cmd)}", 0.0

    label = step["name"]
    print(f"\n{'─' * 60}")
    print(f"▶ {label}")
    print(f"  {' '.join(cmd)}")
    print(f"{'─' * 60}")

    t0 = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=120,  # 2-minute timeout per step
        )
        elapsed = time.time() - t0
        success = result.returncode == 0

        if success:
            status = "✅ OK"
        else:
            status = f"❌ FAILED (exit code {result.returncode})"

        print(f"  {status}  ({elapsed:.1f}s)")

        if result.stdout.strip():
            # Indent output for readability
            for line in result.stdout.strip().split("\n"):
                print(f"  │ {line}")

        if result.stderr.strip():
            for line in result.stderr.strip().split("\n"):
                print(f"  ⚠ {line}")

        output = result.stdout.strip() or "(no output)"
        return success, output, elapsed

    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        print(f"  ⏱ TIMEOUT (>120s)")
        return False, "Step timed out after 120 seconds", elapsed
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  ❌ ERROR: {e}")
        return False, str(e), elapsed


def run_pipeline(steps, dry_run=False):
    """Run a sequence of steps, continuing on failure. Returns summary dict."""
    results = []
    total_start = time.time()

    for step_name in steps:
        step = STEPS.get(step_name)
        extra_args = []

        # Handle session-summary date
        if step and step.get("needs_session_date"):
            extra_args = ["--session", get_today_str()]

        success, output, elapsed = run_step(step_name, dry_run=dry_run, extra_args=extra_args)
        results.append({
            "step": step_name,
            "label": step["name"] if step else step_name,
            "success": success,
            "output": output[:200] if output else "",
            "elapsed": elapsed,
        })

    total_elapsed = time.time() - total_start

    return {
        "results": results,
        "total_elapsed": total_elapsed,
        "dry_run": dry_run,
    }


def print_report(summary):
    """Print a formatted summary report."""
    results = summary["results"]
    dry_run = summary["dry_run"]
    total_elapsed = summary["total_elapsed"]

    passed = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])

    mode = "DRY-RUN PREVIEW" if dry_run else "EXECUTION REPORT"

    print(f"\n{'═' * 60}")
    print(f"  Memory Maintenance — {mode}")
    print(f"  Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'═' * 60}")

    for r in results:
        icon = "✅" if r["success"] else "❌"
        print(f"  {icon} {r['label']:<30s} ({r['elapsed']:.1f}s)")
        if not r["success"] and not dry_run:
            print(f"     ⚠ {r['output']}")

    print(f"  {'─' * 40}")
    print(f"  Total: {passed} passed, {failed} failed")
    if not dry_run:
        print(f"  Duration: {total_elapsed:.1f}s")
    print(f"{'═' * 60}")

    return failed == 0


def print_status():
    """Show a quick overview of all scripts and their availability."""
    print("📊 Memory Maintenance — Status Overview")
    print(f"   Workspace: {WORKSPACE}")
    print(f"   Memory Dir: {SCRIPT_DIR}")
    print(f"   Date: {get_today_str()}")
    print()

    print("   Scripts:")
    for script_name, path in SCRIPTS.items():
        exists = os.path.isfile(path)
        icon = "✅" if exists else "❌"
        print(f"     {icon} {script_name}")

    print()
    print("   Pipelines:")
    print(f"     Heartbeat: {' → '.join(HEARTBEAT_PIPELINE)}")
    print(f"     Manual:    {' → '.join(MANUAL_PIPELINE)}")
    print()
    print("   Usage:")
    print(f"     {sys.argv[0]} --heartbeat    Run heartbeat pipeline")
    print(f"     {sys.argv[0]} --manual       Run manual pipeline (dry-run safe)")
    print(f"     {sys.argv[0]} --run-all      Run everything")
    print(f"     {sys.argv[0]} --dry-run      Preview without execution")
    print(f"     {sys.argv[0]} --step <name>  Run a single step")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Kora Memory Maintenance — Script Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                       Quick status overview
  %(prog)s --heartbeat           Run index rebuild → graph rebuild → git backup
  %(prog)s --heartbeat --dry-run Preview heartbeat pipeline without executing
  %(prog)s --manual              Run manual pipeline (session → digest → audit → pruner)
  %(prog)s --step index-rebuild  Run only the index rebuild step
  %(prog)s --step pruner-status  Show MEMORY.md pruning stats

Available steps: index-rebuild, graph-rebuild, git-backup,
                 session-summary, daily-digest, priority-audit,
                 pruner-status, pruner-dryrun
        """,
    )

    parser.add_argument(
        "--heartbeat",
        action="store_true",
        help="Run heartbeat pipeline (index → graph → backup)",
    )
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Run manual pipeline (summary → digest → audit → pruner preview)",
    )
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Run full pipeline (heartbeat + manual)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview commands without executing anything",
    )
    parser.add_argument(
        "--step",
        type=str,
        metavar="NAME",
        help="Run a single step by name",
    )

    args = parser.parse_args()

    # ── Status (no flags) ────────────────────────────────────────────
    if not any([args.heartbeat, args.manual, args.run_all, args.step]):
        print_status()
        return

    # ── Single step ──────────────────────────────────────────────────
    if args.step:
        if args.step not in STEPS:
            print(f"❌ Unknown step: {args.step}")
            print(f"   Available: {', '.join(sorted(STEPS.keys()))}")
            sys.exit(1)

        if args.step == "pruner-apply":
            print("⚠️  WARNING: --apply is destructive!")
            print("   Run pruner-dryrun first and review before using --step pruner-apply.")
        else:
            # Run as a single-step "pipeline"
            summary = run_pipeline([args.step], dry_run=args.dry_run)
            all_ok = print_report(summary)
            sys.exit(0 if all_ok else 1)

    # ── Build pipeline ───────────────────────────────────────────────
    steps_to_run = []

    if args.run_all:
        steps_to_run = HEARTBEAT_PIPELINE + MANUAL_PIPELINE
    elif args.heartbeat:
        steps_to_run = HEARTBEAT_PIPELINE
    elif args.manual:
        steps_to_run = MANUAL_PIPELINE

    if not steps_to_run:
        print("❌ No pipeline selected. Use --heartbeat, --manual, or --run-all.")
        sys.exit(1)

    # ── Safety warning for manual pipeline ───────────────────────────
    if not args.dry_run and args.manual:
        print("⚠️  Manual pipeline will read and write files.")
        print("   memory_pruner --dry-run is safe (preview only).")
        print("   memory_pruner --apply is NEVER run automatically.\n")

    # ── Execute ──────────────────────────────────────────────────────
    summary = run_pipeline(steps_to_run, dry_run=args.dry_run)
    all_ok = print_report(summary)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
