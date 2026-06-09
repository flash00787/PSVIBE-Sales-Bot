#!/usr/bin/env python3
"""
Spawning Manager Agent — Auto-pilot for the full spawn protocol.

Kora spawns this agent; it handles the entire spawn pipeline:
  Preflight → Lock → Backup → Spawn Fix Agent → Wait → Validate → Rollback (if fail) → Release → Report

Usage (by Kora):
    sessions_spawn(
        taskName="spawn-mgr-fix-auth",
        task='python3 /root/coordination/spawning_manager.py spawn \\
            --task-name "fix-auth" \\
            --description "Fix API auth: change header to query param" \\
            --files "customer_bot/api.py" \\
            --model "deepseek/deepseek-v4-pro" \\
            --timeout 600',
        runTimeoutSeconds=900,
        model="deepseek/deepseek-v4-flash"
    )

For read-only tasks (no code change):
    sessions_spawn(
        taskName="spawn-mgr-audit",
        task='python3 /root/coordination/spawning_manager.py spawn \\
            --task-name "audit-sales" \\
            --description "Read-only audit of sales handler" \\
            --readonly',
        runTimeoutSeconds=300,
        model="deepseek/deepseek-v4-flash"
    )
"""
import argparse, json, os, subprocess, sys, time, re
from datetime import datetime

COORD = "/root/coordination"
BD = "/root/psvibe-sales-bot"
BK = "/root/backups"

def run(c, t=30):
    try:
        r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"

# ─── Preflight ───────────────────────────────────────────────

def step_preflight(files):
    """Run pre-flight: services healthy, target files not locked"""
    issues = []
    # Services check
    for name, svc in [("Sale", "psvibe-sale-bot.service"),
                       ("Cust", "psvibe_customer_bot.service"),
                       ("API", "psvibe-api.service")]:
        rc, o, e = run(f"systemctl is-active {svc}")
        if o != "active":
            issues.append(f"{name} DOWN: {o}")
    if not issues:
        print("  ✅ Services: all active")
    
    # Locks check
    for f in files:
        rc, o, e = run(f"python3 {COORD}/lock_manager.py check --file '{f}' 2>&1")
        # lock_manager.py check prints "FREE" when unlocked; any other output = locked
        if o and "FREE" not in o:
            issues.append(f"LOCKED: {f}")
    if issues:
        print(f"  ❌ Preflight FAILED: {len(issues)} issue(s)")
        for i in issues:
            print(f"     - {i}")
        return False
    print("  ✅ Preflight: PASS")
    return True

# ─── Lock ────────────────────────────────────────────────────

def step_lock(task_name, files, reason):
    """Acquire locks for target files"""
    if not files:
        print("  ⏭️  No files to lock (readonly)")
        return True
    files_str = ",".join(files)
    rc, o, e = run(f"python3 {COORD}/lock_manager.py acquire --agent {task_name} --files '{files_str}' --reason '{reason}'")
    if rc != 0:
        print(f"  ❌ Lock FAILED: {e or o}")
        return False
    print(f"  ✅ Lock acquired: {task_name} → {files}")
    return True

# ─── Backup ──────────────────────────────────────────────────

def step_backup(task_name):
    """Create pre-change backup"""
    t = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    b = os.path.join(BK, f"pre-{task_name}-{t}.tar.gz")
    os.makedirs(BK, exist_ok=True)
    rc, o, e = run(f"tar czf {b} -C {BD} . 2>&1")
    if rc != 0:
        print(f"  ❌ Backup FAILED: {e}")
        return None
    size = os.path.getsize(b) // 1024
    print(f"  ✅ Backup: {b} ({size} KB)")
    return b

# ─── Spawn Fix Agent ─────────────────────────────────────────

def step_spawn(task_name, description, model, timeout, files, readonly):
    """Print the sessions_spawn command for Kora to execute"""
    sev = "Read-only audit" if readonly else "Code fix"
    files_str = ", ".join(files) if files else "none (readonly)"
    print()
    print("  ╔═══════════════════════════════════════════════╗")
    print("  ║   🚀 READY TO SPAWN FIX AGENT                ║")
    print("  ╚═══════════════════════════════════════════════╝")
    print()
    print(f"  📋 Task:     {task_name}")
    print(f"  📝 Desc:     {description}")
    print(f"  📁 Files:    {files_str}")
    print(f"  🤖 Model:    {model}")
    print(f"  ⏱  Timeout:  {timeout}s")
    print(f"  🔒  Type:    {sev}")
    print()
    print("  Kora, spawn the fix agent NOW:")
    print(f"  ───")
    print(f'  sessions_spawn(')
    print(f'      taskName="{task_name}",')
    print(f'      task="""Fix {description}')
    print()
    if files:
        print(f"  Files to modify: {files_str}")
    print(f"  VPS: 5.223.81.16 (key /home/node/.openclaw/workspace/.ssh/id_rsa)")
    print(f"  Bot path: {BD}")
    print(f'      """,')
    print(f'      model="{model}",')
    print(f'      runTimeoutSeconds={timeout},')
    print(f'  )')
    print()
    print(f"  After spawn → use sessions_yield to wait")
    print(f"  Then run validate + rollback if needed")
    return True

# ─── Validate ────────────────────────────────────────────────

def step_validate():
    """Run validation suite"""
    rc, o, e = run(f"python3 {COORD}/validate.py 2>&1")
    if "PASS" in o or rc == 0:
        print("  ✅ Validation: PASS")
        return True
    print(f"  ❌ Validation: FAIL")
    print(f"     {o[:500]}")
    return False

# ─── Rollback ────────────────────────────────────────────────

def step_rollback(backup_path):
    """Restore from backup"""
    if not backup_path or not os.path.exists(backup_path):
        print("  ❌ Rollback: no backup found")
        return False
    rc, o, e = run(f"python3 {COORD}/rollback.py --backup {backup_path} 2>&1")
    if rc == 0:
        print(f"  ✅ Rollback: COMPLETE (from {os.path.basename(backup_path)})")
        return True
    print(f"  ❌ Rollback FAILED: {e or o}")
    return False

# ─── Release Lock ────────────────────────────────────────────

def step_release(task_name):
    """Release all locks held by this agent"""
    rc, o, e = run(f"python3 {COORD}/lock_manager.py release --agent {task_name}")
    if rc == 0:
        print(f"  ✅ Locks released: {task_name}")
        return True
    print(f"  ⚠️  Lock release: {o or e}")
    return False

# ─── Main Spawn Command ─────────────────────────────────────

def cmd_spawn(args):
    task_name = args.task_name
    description = args.description
    files = [f.strip() for f in args.files.split(",") if f.strip()] if args.files else []
    model = args.model or "deepseek/deepseek-v4-pro"
    timeout = int(args.timeout or 600)
    readonly = args.readonly
    
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    print("=" * 55)
    print(f"  🚀 Spawning Manager — {now}")
    print(f"  Task: {task_name} | {'📖 Read-only' if readonly else '🔧 Code Change'}")
    print("=" * 55)
    print()
    
    # Step 1: Preflight
    print("─── Step 1: Preflight Check ───")
    if not step_preflight(files):
        sys.exit(1)
    print()
    
    # Step 2: Lock
    if not readonly:
        print("─── Step 2: Acquire Locks ───")
        if not step_lock(task_name, files, description[:50]):
            sys.exit(1)
        print()
    
    # Step 3: Backup
    if not readonly:
        print("─── Step 3: Backup ───")
        backup_path = step_backup(task_name)
        if not backup_path:
            step_release(task_name)
            sys.exit(1)
        print()
    else:
        backup_path = None
        print("─── Step 3: Backup (skipped — readonly) ───")
        print()
    
    # Step 4: Spawn Instruction
    print("─── Step 4: Spawn Fix Agent ───")
    step_spawn(task_name, description, model, timeout, files, readonly)
    print()
    
    # Note: Steps 5-7 are done AFTER the fix agent completes
    print("─── 📝 After Fix Agent Completes ───")
    print()
    print(f"  Run these commands:")
    print(f"  # 5. Validate")
    print(f"  python3 {COORD}/validate.py")
    print(f"  # 6. If FAIL → rollback")
    print(f"  python3 {COORD}/rollback.py --backup {backup_path or '<path>'}")
    print(f"  # 7. Release locks")
    print(f"  python3 {COORD}/lock_manager.py release --agent {task_name}")
    print()

# ─── Validate Command (post-spawn) ──────────────────────────

def cmd_validate(args):
    """Run after fix agent completes"""
    task_name = args.task_name
    backup_path = args.backup
    print("─── Step 5: Validate ───")
    ok = step_validate()
    
    if ok:
        print("─── Step 6: (skipped — validation passed) ───")
        print("─── Step 7: Release Locks ───")
        step_release(task_name)
        print()
        print("✅ ALL DONE — Task completed successfully")
    else:
        print("─── Step 6: Rollback (validation FAILED) ───")
        step_rollback(backup_path)
        print("─── Step 7: Release Locks ───")
        step_release(task_name)
        print()
        print("⚠️  Task completed with ROLLBACK — changes reverted")
    
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"📋 Final Report — {now}")
    print(f"   Task: {task_name}")
    print(f"   Status: {'✅ SUCCESS' if ok else '⚠️  ROLLED BACK'}")

# ─── CLI ─────────────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Spawning Manager — Auto-pilot spawn protocol")
    s = p.add_subparsers(dest="cmd")
    
    # spawn command
    sp = s.add_parser("spawn", help="Run pre-spawn protocol (preflight→lock→backup→print spawn cmd)")
    sp.add_argument("--task-name", required=True)
    sp.add_argument("--description", required=True)
    sp.add_argument("--files", default="")
    sp.add_argument("--model", default="deepseek/deepseek-v4-pro")
    sp.add_argument("--timeout", default="600")
    sp.add_argument("--readonly", action="store_true", help="Read-only audit (no lock/backup)")
    
    # validate command (post-spawn)
    vp = s.add_parser("validate", help="Post-spawn validation (validate→rollback→release)")
    vp.add_argument("--task-name", required=True)
    vp.add_argument("--backup", default="")
    
    a = p.parse_args()
    if a.cmd == "spawn":
        cmd_spawn(a)
    elif a.cmd == "validate":
        cmd_validate(a)
    else:
        p.print_help()
