#!/usr/bin/env python3
"""Full validation suite after a sub-agent completes.

Usage:
    python3 validate.py              # Full validation + restart
    python3 validate.py --quick      # Skip restart (syntax + import only)
    python3 validate.py --verbose    # Detailed output

Returns:
    PASS (exit 0) / FAIL (exit 1)
    On FAIL, also prints exact rollback command.
"""

import os
import sys
import subprocess
import argparse
import time

BOT_DIR = "/root/psvibe-sales-bot"
SERVICES = [
    ("Sale Bot", "psvibe-sale-bot.service"),
    ("Customer Bot", "psvibe_customer_bot.service"),
    ("API Server", "psvibe-api.service"),
]


def _run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)


def step_compile():
    """Step 1: Syntax check ALL .py files."""
    rc, out, err = _run(
        f"cd {BOT_DIR} && "
        f"errors=0; "
        f"for f in $(find . -name '*.py'); do "
        f"  python3 -m py_compile \"$f\" 2>&1 | grep -v '^$' && errors=$((errors+1)); "
        f"done; "
        f"echo \"TOTAL_ERRORS=$errors\""
    )
    for line in out.split("\n"):
        if "TOTAL_ERRORS=" in line:
            n = int(line.split("=")[1])
            return n == 0, f"{n} file(s) with errors"
    return False, "Could not determine compile result"


def step_import():
    """Step 2: Check bot import chain."""
    rc, out, err = _run(
        f"cd {BOT_DIR} && python3 -c "
        f"\"import sys; sys.path.insert(0,'.'); from bot import __name__; print('IMPORT_OK')\""
    )
    if "IMPORT_OK" in out:
        return True, "All imports resolved"
    return False, f"Import failed: {out[:200]}"


def step_restart():
    """Step 3: Restart ALL services."""
    results = []
    for name, svc in SERVICES:
        rc, out, err = _run(f"systemctl restart {svc}")
        results.append((name, svc, rc == 0))
    return results


def step_service_check():
    """Step 4: Verify all services are active."""
    time.sleep(2)  # Give services time to start
    results = []
    for name, svc in SERVICES:
        rc, out, err = _run(f"systemctl is-active {svc}")
        results.append((name, svc, out == "active", out))
    return results


def step_log_check():
    """Step 5: Check last 50 log lines for errors."""
    all_clean = True
    issues = []
    for name, svc in SERVICES:
        rc, out, err = _run(f"journalctl -u {svc} --no-pager -n 50 2>/dev/null | grep -iE '(ERROR|Traceback|CRITICAL|FAILURE)' || echo 'NO_ERRORS'")
        if "NO_ERRORS" not in out and out:
            all_clean = False
            issues.append(f"  🔴 {name}: Errors found")
            for line in out.split("\n")[:5]:
                issues.append(f"     {line[:150]}")
    return all_clean, issues


def step_api_health():
    """Step 6: Check API health endpoint."""
    rc, out, err = _run("curl -sf http://localhost:8000/health 2>/dev/null || echo 'API_DOWN'")
    if "API_DOWN" in out:
        return False, "API health check FAILED"
    return True, "API healthy"


def main():
    parser = argparse.ArgumentParser(description="Post-fix validation")
    parser.add_argument("--quick", action="store_true", help="Skip restart, syntax + import only")
    parser.add_argument("--verbose", action="store_true", help="Detailed output")
    args = parser.parse_args()

    results = []

    # Always run compile + import
    print("🧪 Step 1/6: Compile check...")
    ok, msg = step_compile()
    status = "✅" if ok else "❌"
    results.append(("Compile check", ok, msg))
    print(f"  {status} {msg}")
    if not ok and args.verbose:
        print(f"  (Run: cd {BOT_DIR} && python3 -m py_compile <file> for details)")

    print("🧪 Step 2/6: Import test...")
    ok, msg = step_import()
    status = "✅" if ok else "❌"
    results.append(("Import test", ok, msg))
    print(f"  {status} {msg}")

    if not args.quick:
        print("🧪 Step 3/6: Restart services...")
        svc_results = step_restart()
        for name, svc, ok in svc_results:
            status = "✅" if ok else "❌"
            results.append((f"Restart {name}", ok, svc))
            print(f"  {status} {svc} restarted")

        print("🧪 Step 4/6: Service health check...")
        health_results = step_service_check()
        for name, svc, ok, msg in health_results:
            status = "✅" if ok else "❌"
            results.append((f"Health {name}", ok, msg))
            print(f"  {status} {name} → {msg}")

        print("🧪 Step 5/6: Log error check...")
        clean, issues = step_log_check()
        status = "✅" if clean else "❌"
        results.append(("Log check", clean, "No errors" if clean else "Errors found"))
        print(f"  {status} {'No errors in logs' if clean else 'Errors detected'}")
        if not clean and args.verbose:
            for issue in issues:
                print(f"     {issue}")

        print("🧪 Step 6/6: API health check...")
        ok, msg = step_api_health()
        status = "✅" if ok else "❌"
        results.append(("API health", ok, msg))
        print(f"  {status} {msg}")

    # Summary
    print()
    print("=" * 55)
    print("VALIDATION SUMMARY")
    print("=" * 55)
    all_pass = True
    for name, ok, msg in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        if not ok:
            all_pass = False
        print(f"  {status} | {name}: {msg[:80]}")

    if all_pass:
        print()
        print("🎉 ALL VALIDATIONS PASSED")
        sys.exit(0)
    else:
        print()
        print("❌ SOME VALIDATIONS FAILED")
        print()
        print("To rollback, run:")
        LAST_BACKUP = subprocess.run(
            "ls -t /root/backups/pre-*.tar.gz 2>/dev/null | head -1",
            shell=True, capture_output=True, text=True
        ).stdout.strip()
        if LAST_BACKUP:
            print(f"  python3 /root/coordination/rollback.py --backup {LAST_BACKUP}")
        else:
            print("  (No backups found, manual rollback needed)")
        sys.exit(1)


if __name__ == "__main__":
    main()
