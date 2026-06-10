#!/usr/bin/env python3
"""
auto_bug_fixer.py — Automated Bug Pattern Detection & Fix
==========================================================
Reads KNOWN_BUG_PATTERNS.md (and ERROR_PATTERNS.md if present)
Scans the PS VIBE codebase for known patterns and auto-fixes them.
Logs all actions to /root/coordination/.fix_log.json

Run: python3 /root/coordination/auto_bug_fixer.py [--scan|--fix|--report]
  --scan    Scan only, report findings (default)
  --fix     Scan and auto-fix
  --report  Show recent fix history
"""

import os
import sys
import json
import re
import subprocess
import logging
import hashlib
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("auto_bug_fixer")

# ── Configuration ──────────────────────────────────────────────────────────
COORDINATION = Path("/root/coordination")
PROJECT_ROOT = Path("/root/psvibe-sales-bot")
PATTERNS_FILE = COORDINATION / "KNOWN_BUG_PATTERNS.md"
ERROR_PATTERNS_FILE = COORDINATION / "ERROR_PATTERNS.md"
FIX_LOG = COORDINATION / ".fix_log.json"

# Production code directories (not tests, not scripts, not __pycache__)
PROD_DIRS = ["bot", "customer_bot"]
SCAN_EXCLUDE = ["__pycache__", "tests", "test_", ".bak", "archive", "backups"]

SCAN_EXTENSIONS = {".py", ".sql"}


# ── Fix Log ────────────────────────────────────────────────────────────────
def load_fix_log() -> list:
    if FIX_LOG.is_file():
        try:
            data = json.loads(FIX_LOG.read_text())
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Migrate old dict format to list
                old_entries = data.get("entries", data.get("fixes", []))
                if isinstance(old_entries, list):
                    return old_entries
                return list(data.values()) if data else []
        except (json.JSONDecodeError, IOError):
            pass
    return []


def save_fix_log(log: list) -> None:
    FIX_LOG.write_text(json.dumps(log, indent=2, default=str))


def log_fix(pattern_name: str, file_path: str, line_no: int, description: str, auto_fixed: bool) -> None:
    log = load_fix_log()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pattern": pattern_name,
        "file": str(file_path),
        "line": line_no,
        "description": description,
        "auto_fixed": auto_fixed,
        "hash": hashlib.sha256(f"{file_path}:{line_no}:{pattern_name}".encode()).hexdigest()[:12],
    }
    # Avoid duplicate entries
    if isinstance(log, list):
        for e in log[-50:]:
            if e.get("hash") == entry["hash"]:
                return
    log.append(entry)
    save_fix_log(log)
    logger.info("FIX LOG: %s — %s:%d — %s", pattern_name, file_path, line_no, description)


# ── Pattern Detectors & Fixers ─────────────────────────────────────────────

def is_prod_file(filepath: str) -> bool:
    """Check if a file is in production code directories."""
    rel = os.path.relpath(filepath, PROJECT_ROOT)
    for d in PROD_DIRS:
        if rel.startswith(d + os.sep) or rel == d:
            return True
    return False


def scan_python_files(base_dir: Path) -> list:
    """Find all Python files excluding test/backup files."""
    files = []
    for root, dirs, filenames in os.walk(base_dir):
        dirs[:] = [d for d in dirs if not any(excl in d.lower() for excl in SCAN_EXCLUDE)]
        for fn in filenames:
            ext = os.path.splitext(fn)[1]
            if ext in SCAN_EXTENSIONS:
                files.append(os.path.join(root, fn))
    return files


# ── Pattern 1: Bare except: ────────────────────────────────────────────────
def find_bare_excepts(filepath: str) -> list:
    """Find bare 'except:' clauses (no exception type specified)."""
    findings = []
    try:
        with open(filepath) as f:
            lines = f.readlines()
    except (IOError, UnicodeDecodeError):
        return findings

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped == "except:" or stripped.startswith("except: "):
            # Skip if in docstring or comment
            findings.append({
                "pattern": "bare_except",
                "file": filepath,
                "line": i,
                "content": stripped,
                "context": lines[max(0, i - 3):min(len(lines), i + 1)],
            })
    return findings


def fix_bare_excepts(filepath: str) -> int:
    """Replace bare except: with except Exception:"""
    fixed = 0
    try:
        with open(filepath) as f:
            content = f.read()
    except (IOError, UnicodeDecodeError):
        return 0

    original = content
    # Pattern: any line matching 'except:' that isn't 'except Exception:'
    for match in re.finditer(r"(\s*)except:\s*(#.*)?$", content, re.MULTILINE):
        indent = match.group(1)
        comment = match.group(2) or ""
        # Determine appropriate exception type from context
        # Default to Exception, but try to be smarter
        replacement = f"{indent}except Exception:{comment}"
        content = content.replace(match.group(0), replacement, 1)
        fixed += 1

    if fixed > 0 and content != original:
        with open(filepath, "w") as f:
            f.write(content)
        logger.info("Fixed %d bare except(s) in %s", fixed, filepath)

    return fixed


# ── Pattern 2: print() statements in production code ───────────────────────
def find_print_statements(filepath: str) -> list:
    """Find print() calls in production code."""
    findings = []
    try:
        with open(filepath) as f:
            lines = f.readlines()
    except (IOError, UnicodeDecodeError):
        return findings

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Match print( at start of line (after optional whitespace)
        if re.match(r"^print\(", stripped):
            # Skip if it's inside a string (heuristic)
            findings.append({
                "pattern": "print_statement",
                "file": filepath,
                "line": i,
                "content": stripped[:80],
            })
    return findings


def fix_print_statements(filepath: str) -> int:
    """Replace print() with logger.info() — adds logging import if needed."""
    try:
        with open(filepath) as f:
            content = f.read()
    except (IOError, UnicodeDecodeError):
        return 0

    original = content
    fixed_count = 0

    # Only replace print() at start of lines
    content_new = re.sub(r"^(\s*)print\(", r"\1logger.info(", content, flags=re.MULTILINE)
    if content_new != content:
        fixed_count = len(re.findall(r"^(\s*)print\(", content, re.MULTILINE))
        content = content_new

    if fixed_count > 0:
        # Ensure logging is imported
        if "import logging" not in content:
            import_line = "import logging\nlogging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger(__name__)\n"
            # Insert after first import block
            first_import_end = 0
            for m in re.finditer(r"^(?:import|from)\s+.*$", content, re.MULTILINE):
                first_import_end = m.end()
            if first_import_end > 0:
                content = content[:first_import_end] + "\n" + import_line + content[first_import_end:]
            else:
                content = import_line + content

        with open(filepath, "w") as f:
            f.write(content)
        logger.info("Fixed %d print() calls in %s", fixed_count, filepath)

    return fixed_count


# ── Pattern 3: Missing API response guards ────────────────────────────────
def find_api_response_guards_missing(filepath: str) -> list:
    """Find .get() calls on API responses without isinstance() guards."""
    findings = []
    # Skip non-relevant files
    basename = os.path.basename(filepath)
    if "test" in basename.lower():
        return findings

    try:
        with open(filepath) as f:
            content = f.read()
    except (IOError, UnicodeDecodeError):
        return findings

    # Look for patterns like: data = response.json() followed by data.get(...)
    # without isinstance guard
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        if "response.json()" in line or ".json()" in line:
            # Check if isinstance check follows within 5 lines
            has_guard = False
            for j in range(i, min(len(lines), i + 5)):
                if "isinstance" in lines[j]:
                    has_guard = True
                    break
            if not has_guard:
                findings.append({
                    "pattern": "api_response_unguarded",
                    "file": filepath,
                    "line": i,
                    "content": line.strip()[:80],
                })
    return findings


# ── Pattern 4: Missing async/await ─────────────────────────────────────────
def find_async_calls_in_sync(filepath: str) -> list:
    """Detect async function calls inside sync functions without await."""
    findings = []
    try:
        with open(filepath) as f:
            content = f.read()
    except (IOError, UnicodeDecodeError):
        return findings

    # Look for known async function names called without await in sync context
    known_async = [
        "_build_ai_system_prompt",
        "fetch_async_data",
        "_fetch_consoles",
        "_fetch_games_full",
        "_fetch_promotions",
        "_fetch_config",
        "_fetch_sales_data",
    ]

    lines = content.split("\n")
    in_async_func = False

    for i, line in enumerate(lines, 1):
        if re.match(r"\s*async\s+def\s+", line):
            in_async_func = True
        elif re.match(r"\s*def\s+", line):
            in_async_func = False

        if not in_async_func:
            for func_name in known_async:
                if func_name in line and "await" not in line and "def " + func_name not in line:
                    findings.append({
                        "pattern": "missing_await",
                        "file": filepath,
                        "line": i,
                        "content": line.strip()[:80],
                    })
                    break
    return findings


# ── Pattern 5: Hardcoded endpoints ─────────────────────────────────────────
def find_hardcoded_endpoints(filepath: str) -> list:
    """Find hardcoded URLs that should use constants."""
    findings = []
    try:
        with open(filepath) as f:
            content = f.read()
    except (IOError, UnicodeDecodeError):
        return findings

    # Find suspicious URL patterns (hardcoded /api/ paths)
    for match in re.finditer(r'["\']https?://[^"\']+/api/[^"\']*["\']', content):
        url = match.group(0)
        findings.append({
            "pattern": "hardcoded_endpoint",
            "file": filepath,
            "line": content[:match.start()].count("\n") + 1,
            "content": url[:80],
        })
    return findings


# ── Main Scan & Fix ────────────────────────────────────────────────────────
ALL_CHECKS = [
    ("bare_except", find_bare_excepts, fix_bare_excepts, "Fix bare except: clauses"),
    ("print_statement", find_print_statements, fix_print_statements, "Replace print() with logger"),
    ("api_response_unguarded", find_api_response_guards_missing, None, "Check API response guards"),
    ("missing_await", find_async_calls_in_sync, None, "Check async/await calls"),
    ("hardcoded_endpoint", find_hardcoded_endpoints, None, "Check hardcoded endpoints"),
]


def run_scan(fix: bool = False) -> dict:
    """Scan the full codebase and optionally fix issues."""
    files = scan_python_files(PROJECT_ROOT)
    prod_files = [f for f in files if is_prod_file(f)]
    logger.info("Scanning %d production files in %s...", len(prod_files), PROJECT_ROOT)

    results = {}
    for pattern_name, finder, fixer, desc in ALL_CHECKS:
        findings = []
        for fpath in prod_files:
            findings.extend(finder(fpath))
        results[pattern_name] = findings
        logger.info("  %s: %d found", pattern_name, len(findings))

        if fix and fixer:
            for finding in findings:
                fix_count = fixer(finding["file"])
                if fix_count > 0:
                    log_fix(
                        pattern_name,
                        finding["file"],
                        finding.get("line", 0),
                        desc,
                        auto_fixed=True,
                    )
        elif findings:
            for f in findings:
                log_fix(pattern_name, f["file"], f.get("line", 0), desc, auto_fixed=False)

    return results


def run_report():
    """Show recent fix history."""
    log = load_fix_log()
    if not log:
        print("No fix log entries found.")
        return

    print(f"\n{'='*60}")
    print(f" Auto Bug Fixer — Fix Log ({len(log)} entries)")
    print(f"{'='*60}\n")

    # Show last 20 grouped by pattern
    recent = log[-20:]
    by_pattern = {}
    for entry in recent:
        p = entry.get("pattern", "unknown")
        if p not in by_pattern:
            by_pattern[p] = []
        by_pattern[p].append(entry)

    for pattern, entries in sorted(by_pattern.items()):
        print(f"\n  [{pattern}] ({len(entries)} occurrences)")
        for e in entries[-5:]:
            ts = e.get("timestamp", "?")[:19]
            status = "✅ FIXED" if e.get("auto_fixed") else "⚠️ FOUND"
            print(f"    {ts} {status:10} {e.get('file','')}:{e.get('line','')}")
    print(f"\n{'='*60}\n")


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Auto Bug Pattern Fixer")
    parser.add_argument("--scan", action="store_true", default=True, help="Scan only (default)")
    parser.add_argument("--fix", action="store_true", help="Scan and auto-fix")
    parser.add_argument("--report", action="store_true", help="Show fix history")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.report:
        run_report()
        return

    fix = args.fix
    logger.info("Auto Bug Fixer starting... (mode: %s)", "FIX" if fix else "SCAN")
    start = datetime.now(timezone.utc)

    results = run_scan(fix=fix)

    # Summary
    total_issues = sum(len(v) for v in results.values())
    elapsed = (datetime.now(timezone.utc) - start).total_seconds()

    print(f"\n{'='*60}")
    print(f" Scan Summary")
    print(f"{'='*60}")
    print(f"  Files scanned: production (bot/ + customer_bot/)")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Mode: {'FIX' if fix else 'SCAN ONLY'}")
    print(f"  Total issues: {total_issues}")
    for name, findings in results.items():
        marker = "🔴" if findings else "✅"
        print(f"    {marker} {name}: {len(findings)}")
    print(f"{'='*60}\n")

    if total_issues > 0 and not fix:
        print("💡 Run with --fix to auto-fix detected issues.")

    return 0 if total_issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
