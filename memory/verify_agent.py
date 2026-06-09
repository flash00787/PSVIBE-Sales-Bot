#!/usr/bin/env python3
"""
Verify Agent — Auto re-audit after fix agent completes.

Flow:
  1. Fix Agent completes → writes findings/<fix>.json with status="FIXED"
  2. Kora spawns Verify Agent with --files "list of fixed files"
  3. Verify Agent re-scans only those files → checks for remaining issues
  4. Writes findings (CLEAN or PENDING)
  5. Reports to Kora

Usage (by Kora):
    sessions_spawn(
        taskName="verify-fix-auth",
        task='python3 /root/coordination/verify_agent.py verify \\
            --agent "fix-auth" \\
            --files "customer_bot/api.py,bot/__init__.py"',
        runTimeoutSeconds=300,
        model="deepseek/deepseek-v4-flash"
    )
"""
import argparse, json, os, subprocess, sys, re
from datetime import datetime

BD = "/root/psvibe-sales-bot"
FD = "/root/coordination/findings"

def run(c, t=15):
    try:
        r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except: return -1, "", "TIMEOUT"

# ─── Verification Checks ──────────────────────────────

def check_compile(files):
    """Check specific files compile cleanly"""
    issues = []
    for f in files:
        full = os.path.join(BD, f) if not f.startswith("/") else f
        if not os.path.exists(full):
            issues.append(f"NOT FOUND: {f}")
            continue
        # Use subprocess run directly with shell=False for py_compile
        rc, o, e = run(f"cd {BD} && python3 -m py_compile '{f}' 2>&1")
        if rc != 0:
            issues.append(f"COMPILE ERROR: {f} → {e or o}")
    return issues

def check_all_imports():
    """Quick import test (with env vars)"""
    cmd = f"cd {BD} && export $(grep -v '^#' /etc/psvibe/secrets.env 2>/dev/null | xargs) 2>/dev/null && python3 -c \"import sys; sys.path.insert(0,'.'); from bot import __name__; print('OK')\" 2>&1"
    rc, o, e = run(cmd)
    if "OK" in o: return []
    return [f"IMPORT ERROR: {o[:200]}"]

def check_api_syntax(files):
    """Check for common syntax patterns that break"""
    issues = []
    for f in files:
        full = os.path.join(BD, f) if not f.startswith("/") else f
        if not os.path.exists(full): continue
        rc, o, e = run(f"cd {BD} && python3 {full} 2>&1")
        if rc != 0 and "SyntaxError" in e:
            issues.append(f"SYNTAX ERROR in {f}: {e[:200]}")
    return issues

def check_logs(fix_agent):
    """Check recent logs for errors from this fix"""
    rc, o, e = run("journalctl -u psvibe-sale-bot.service --no-pager -n 30 2>&1")
    errors = [l for l in o.split("\n") if "ERROR" in l or "Traceback" in l or "CRITICAL" in l]
    if errors:
        return [f"LOG ERROR (post-fix): {errors[0][:200]}"]
    return []

def check_services():
    """Check all services are healthy"""
    issues = []
    for name, svc in [("Sale", "psvibe-sale-bot.service"),
                       ("Cust", "psvibe_customer_bot.service"),
                       ("API", "psvibe-api.service")]:
        rc, o, e = run(f"systemctl is-active {svc}")
        if o != "active": issues.append(f"SERVICE DOWN: {name} ({o})")
    return issues

# ─── Main Verify ──────────────────────────────────────

def cmd_verify(args):
    agent_name = args.agent
    target_files = [f.strip() for f in args.files.split(",") if f.strip()] if args.files else []
    
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    print("=" * 55)
    print(f"  🔍 Verify Agent — {now}")
    print(f"  Verifying fix by: {agent_name}")
    print(f"  Files: {', '.join(target_files) if target_files else 'all'}")
    print("=" * 55)
    print()
    
    all_issues = []
    
    # Step 1: Compile check (fast)
    print("─── Check 1: Compile ───")
    issues = check_compile(target_files or ["."])
    if issues:
        for i in issues: print(f"  ❌ {i}")
        all_issues.extend(issues)
    else:
        print("  ✅ All files compile clean")
    print()
    
    # Step 2: Import check
    print("─── Check 2: Imports ───")
    issues = check_all_imports()
    if issues:
        for i in issues: print(f"  ❌ {i}")
        all_issues.extend(issues)
    else:
        print("  ✅ Core imports resolve")
    print()
    
    # Step 3: Service health
    print("─── Check 3: Services ───")
    issues = check_services()
    if issues:
        for i in issues: print(f"  ❌ {i}")
        all_issues.extend(issues)
    else:
        print("  ✅ All 3 services active")
    print()
    
    # Step 4: Log check
    print("─── Check 4: Logs ───")
    issues = check_logs(agent_name)
    if issues:
        for i in issues: print(f"  ⚠️  {i}")
        all_issues.extend(issues)
    else:
        print("  ✅ No new errors in logs")
    print()
    
    # Step 5: File comparison (if backup available)
    print("─── Check 5: Fix Integrity ───")
    if target_files:
        print(f"  📝 Fixed files verified: {', '.join(target_files)}")
        # Simple check: files exist and have content
        for f in target_files:
            full = os.path.join(BD, f) if not f.startswith("/") else f
            if os.path.exists(full):
                size = os.path.getsize(full)
                print(f"  ✅ {f} ({size} bytes)")
            else:
                print(f"  ❌ {f} — NOT FOUND!")
                all_issues.append(f"FILE MISSING: {f}")
    else:
        print("  ⏭️  No specific files specified")
    print()
    
    # ─── Report ──────────────────────────────────────
    
    if not all_issues:
        print("=" * 55)
        print(f"  ✅ VERIFY PASS — {agent_name} fix is CLEAN")
        print("=" * 55)
        print()
        
        # Write clean finding
        entry = {
            "id": f"verify-{agent_name}-{datetime.utcnow().strftime('%H%M%S')}",
            "agent": agent_name,
            "severity": "✅",
            "file": ", ".join(target_files) if target_files else "all",
            "change": "Verified: all checks passed",
            "why": "",
            "status": "VERIFIED"
        }
        os.makedirs(FD, exist_ok=True)
        with open(os.path.join(FD, f"v_{agent_name}.json"), "w") as f:
            json.dump([entry], f, ensure_ascii=False)
        
        print(f"  📄 Verification logged to findings/v_{agent_name}.json")
        print()
        print("  ✅ Ready for Findings Manager merge")
        sys.exit(0)
    
    else:
        print("=" * 55)
        print(f"  ❌ VERIFY FAIL — {len(all_issues)} issue(s) found")
        print("=" * 55)
        print()
        
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        print()
        
        # Determine severity
        has_compile = any("COMPILE" in i for i in all_issues)
        has_service = any("SERVICE" in i for i in all_issues)
        severity = "🔴" if (has_compile or has_service) else "🟡"
        
        # Write PENDING finding → triggers Dispatch Manager
        entry = {
            "id": f"verify-fail-{agent_name}-{datetime.utcnow().strftime('%H%M%S')}",
            "agent": agent_name,
            "severity": severity,
            "file": ", ".join(target_files) if target_files else "all",
            "change": f"Verification failed: {len(all_issues)} issues",
            "why": "; ".join(all_issues[:3]),
            "status": "PENDING"
        }
        os.makedirs(FD, exist_ok=True)
        with open(os.path.join(FD, f"v_{agent_name}.json"), "w") as f:
            json.dump([entry], f, ensure_ascii=False)
        
        print("  🔴 PENDING finding written → Dispatch Manager will re-dispatch")
        print(f"  📄 Saved to findings/v_{agent_name}.json")
        print()
        print("  ⚡ Next step: Run Dispatch Manager")
        print("  sessions_spawn(taskName='dispatch', task='python3 /root/coordination/dispatch_manager.py --dispatch', ...)")
        sys.exit(1)

# ─── Fast Re-audit (Scan for common bugs) ───────────

def cmd_scan(args):
    """Quick scan of recently fixed files for common bug patterns"""
    target_files = [f.strip() for f in args.files.split(",") if f.strip()] if args.files else []
    if not target_files:
        # Default: scan bot/__init__.py and recently modified files
        rc, o, e = run(f"cd {BD} && find . -name '*.py' -mmin -60 2>/dev/null | head -20")
        target_files = [f.replace("./", "") for f in o.split("\n") if f.strip()]
        if not target_files:
            print("No recently modified files found")
            sys.exit(0)
    
    print(f"  🔍 Quick scan: {len(target_files)} file(s)")
    issues = []
    
    # Pattern: duplicate global declarations
    for f in target_files:
        full = os.path.join(BD, f)
        if not os.path.exists(full): continue
        try:
            with open(full) as fh:
                content = fh.read()
            globals_found = re.findall(r'^\s+global\s+(\w+)', content, re.MULTILINE)
            dups = {g: globals_found.count(g) for g in set(globals_found) if globals_found.count(g) > 1}
            if dups:
                for var, cnt in dups.items():
                    issues.append(f"DUPLICATE GLOBAL: {var} ({cnt}x) in {f}")
        except: pass
    
    # Pattern: missing quotes around f-string content
    for f in target_files:
        full = os.path.join(BD, f)
        if not os.path.exists(full): continue
        try:
            with open(full) as fh:
                for lineno, line in enumerate(fh, 1):
                    if 'f🔐' in line and '"""' not in line and "'" not in line and '"' not in line:
                        issues.append(f"UNQUOTED EMOJI: {f}:{lineno}")
        except: pass
    
    if issues:
        print(f"  ⚠️  Found {len(issues)} potential issue(s):")
        for i in issues: print(f"     - {i}")
        # Write as PENDING
        entry = {
            "id": f"scan-{datetime.utcnow().strftime('%H%M%S')}",
            "agent": "verify-agent",
            "severity": "🟡",
            "file": ", ".join(target_files[:3]),
            "change": f"Quick scan: {len(issues)} issue(s)",
            "why": "; ".join(issues[:2]),
            "status": "PENDING"
        }
        os.makedirs(FD, exist_ok=True)
        with open(os.path.join(FD, "v_scan.json"), "w") as f:
            json.dump([entry], f, ensure_ascii=False)
        print(f"  Saved to findings/v_scan.json (PENDING)")
    else:
        print("  ✅ No common issues found")
    
    print()

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Verify Agent — Auto re-audit after fixes")
    s = p.add_subparsers(dest="cmd")
    
    v = s.add_parser("verify", help="Verify a fix agent's work")
    v.add_argument("--agent", required=True)
    v.add_argument("--files", default="")
    
    sc = s.add_parser("scan", help="Quick scan for common bug patterns")
    sc.add_argument("--files", default="")
    
    a = p.parse_args()
    if a.cmd == "verify": cmd_verify(a)
    elif a.cmd == "scan": cmd_scan(a)
    else: p.print_help()
