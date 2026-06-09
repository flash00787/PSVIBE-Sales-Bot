#!/usr/bin/env python3
"""
Task Planner Agent — Decompose Boss's tasks into modular sub-agent units.

Flow:
  1. Kora gets a task from Boss → feeds to Task Planner
  2. Task Planner analyzes → breaks into MAX SIZE modules
  3. Writes execution plan as modules_plan.json
  4. Kora reads plan → spawns in correct order

Max Module Size Rules (မချိုးရ):
  ┌─────────────┬──────────┐
  │ Metric      │ Limit    │
  ├─────────────┼──────────┤
  │ Files       │ MAX 3    │
  │ Lines       │ MAX 250  │
  │ Functions   │ MAX 2    │
  │ Timeout     │ MAX 900s │
  │ Risk        │ 1 per    │
  └─────────────┴──────────┘

Usage (by Kora):
    sessions_spawn(
        taskName="plan-task",
        task='python3 /root/coordination/task_planner.py plan --prompt "Add topup feature to Sales Bot"',
        runTimeoutSeconds=180,
        model="deepseek/deepseek-v4-flash"
    )
"""
import argparse, json, os, re, sys
from datetime import datetime, timezone

PLANS_DIR = "/root/coordination/plans"
os.makedirs(PLANS_DIR, exist_ok=True)

# ─── Module Size Limits (THE RULES) ─────────────────

MAX_LIMITS = {
    "files": 3,           # Max 3 files per module
    "lines": 250,         # Max 250 LOC changes per module
    "functions": 2,       # Max 2 functions per module
    "timeout_seconds": 900,  # Max 15 min per module
    "dep_depth": 3,       # Max dependency chain depth
}

# 🔴 BLOCKING FILES — NEVER parallel on these
BLOCKING_FILES = [
    "bot/__init__.py",  # 100% blast radius
    "bot/app.py",       # Router — changes cascade
]

# ─── Dependency Rules ─────────────────────────────

# Known dependency map (used if file not found on VPS)
DEPS_MAP = {
    "bot/api_client.py": [],
    "bot/config.py": [],
    "bot/db.py": ["bot/config.py"],
    "bot/staff.py": ["bot/api_client.py"],
    "bot/payment.py": ["bot/staff.py", "bot/db.py"],
    "bot/handlers/": ["bot/__init__.py", "bot/app.py"],
    "bot/__init__.py": ["bot/api_client.py", "bot/config.py"],
    "bot/app.py": ["bot/__init__.py"],
    "customer_bot/api.py": [],
    "customer_bot/handlers/": ["customer_bot/api.py"],
    "api/": ["bot/api_client.py", "bot/db.py"],
}

# ⚠️ Files that should NOT be in same module (too risky)
SEPARATE_FILES = [
    ("bot/__init__.py", "bot/app.py"),
    ("bot/__init__.py", "customer_bot/api.py"),
    ("bot/api_client.py", "customer_bot/handlers/"),
]

# ─── Module Planning Engine ──────────────────────────

def run(c, t=10):
    try:
        import subprocess
        r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except: return -1, "", "TIMEOUT"

def get_files_from_prompt(prompt):
    """Infer files from prompt content"""
    files = []
    prompt_lower = prompt.lower()
    
    # Map common keywords to files
    keyword_file_map = {
        "payment": ["bot/payment.py", "bot/__init__.py", "bot/app.py"],
        "topup": ["bot/payment.py", "bot/handlers/admin.py", "bot/__init__.py"],
        "booking": ["bot/handlers/booking.py", "bot/admin_bookings.py", "bot/__init__.py"],
        "customer": ["customer_bot/", "customer_bot/api.py", "customer_bot/handlers/"],
        "api": ["api/", "bot/api_client.py"],
        "auth": ["bot/staff.py", "customer_bot/api.py"],
        "member": ["bot/handlers/member.py", "bot/__init__.py"],
        "wallet": ["bot/wallet.py", "bot/__init__.py"],
        "referral": ["bot/handlers/referral.py"],
        "report": ["bot/report_generator.py", "api/"],
        "database": ["bot/db.py", "bot/config.py"],
        "deploy": ["deploy/", "docker-compose.yml"],
    }
    
    for keyword, filelist in keyword_file_map.items():
        if keyword in prompt_lower:
            files.extend(filelist)
    
    # Deduplicate while keeping order
    seen = set()
    return [f for f in files if not (f in seen or seen.add(f))]

def check_file_exists(rel_path):
    """Check if file exists on VPS"""
    full = os.path.join("/root/psvibe-sales-bot", rel_path)
    return os.path.exists(full)

def estimate_lines_changed(filepath, prompt):
    """Rough estimate of lines that would change"""
    prompt_lower = prompt.lower()
    base = 50  # baseline
    
    # Scale estimate based on complexity keywords
    if "add" in prompt_lower or "implement" in prompt_lower: base += 80
    if "api" in prompt_lower or "endpoint" in prompt_lower: base += 60
    if "handler" in prompt_lower or "command" in prompt_lower: base += 40
    if "database" in prompt_lower or "db" in prompt_lower: base += 50
    if "fix" in prompt_lower and "multiple" in prompt_lower: base += 30
    if "test" in prompt_lower: base += 100
    
    return base

def compute_dependencies(files):
    """Compute dependency order among a set of files"""
    deps = {}
    for f in files:
        # Check exact match
        if f in DEPS_MAP:
            deps[f] = DEPS_MAP[f]
        else:
            # Check prefix match
            deps[f] = []
            for pattern, deplist in DEPS_MAP.items():
                if pattern.endswith("/"):
                    if f.startswith(pattern):
                        deps[f].extend(deplist)
    
    return deps

def check_separation_rule(files):
    """Check if any file pair violates separation rule"""
    violations = []
    for (a, b) in SEPARATE_FILES:
        found_a = any(a in f for f in files)
        found_b = any(b in f for f in files)
        if found_a and found_b:
            violations.append((a, b))
    return violations

def size_check(files, prompt):
    """Check if a module fits within max size limits"""
    issues = []
    
    # File count check
    if len(files) > MAX_LIMITS["files"]:
        issues.append(f"❌ TOO MANY FILES: {len(files)} > {MAX_LIMITS['files']}")
    
    # Lines estimate check
    total_lines = sum(estimate_lines_changed(f, prompt) for f in files)
    if total_lines > MAX_LIMITS["lines"]:
        issues.append(f"❌ TOO MANY LINES: ~{total_lines} > {MAX_LIMITS['lines']}")
    
    # Blocking file check
    for bf in BLOCKING_FILES:
        if bf in files:
            issues.append(f"⚠️ BLOCKING FILE: {bf} — no parallel allowed")
    
    # Separation check
    violations = check_separation_rule(files)
    for (a, b) in violations:
        issues.append(f"⚠️ SEPARATION RULE: {a} + {b} should not be in same module")
    
    return issues, total_lines

def split_into_modules(files, prompt, existing_modules=None):
    """Split files into max-size modules"""
    existing_modules = existing_modules or []
    modules = []
    remaining = list(files)
    
    # Apply blocking file rule — each blocking file gets its own module
    blocking_in_list = [f for f in remaining if f in BLOCKING_FILES or any(f.startswith(b) for b in [p for p in BLOCKING_FILES if p.endswith("/")])]
    for bf in blocking_in_list:
        if bf in remaining:
            modules.append({
                "id": f"M{len(modules)+1}",
                "name": f"Modify {os.path.basename(bf)}",
                "files": [bf],
                "depends_on": [],
                "blocking": True,
                "lines_est": estimate_lines_changed(bf, prompt),
                "separations": [],
                "timeout": 300,  # Quick — single file
                "model": "deepseek/deepseek-v4-pro",
            })
            remaining.remove(bf)
    
    # Group remaining by directory (like files together)
    grouped = {}
    for f in remaining:
        prefix = os.path.dirname(f)
        if prefix not in grouped:
            grouped[prefix] = []
        grouped[prefix].append(f)
    
    # Build modules from groups
    for prefix, file_list in sorted(grouped.items()):
        # Check separation violations within this group
        violations = check_separation_rule(file_list)
        
        if violations:
            # Split violated pairs
            for (a, b) in violations:
                a_files = [f for f in file_list if a in f]
                b_files = [f for f in file_list if b in f]
                others = [f for f in file_list if f not in a_files and f not in b_files]
                
                if a_files:
                    modules.append({
                        "id": f"M{len(modules)+1}",
                        "name": f"Modify {os.path.basename(prefix or 'core')} (A)",
                        "files": a_files,
                        "depends_on": [],
                        "blocking": True,
                        "lines_est": estimate_lines_changed(a_files[0], prompt),
                        "separations": [(a, b)],
                        "timeout": 400,
                        "model": "deepseek/deepseek-v4-pro",
                    })
                if b_files:
                    modules.append({
                        "id": f"M{len(modules)+1}",
                        "name": f"Modify {os.path.basename(prefix or 'core')} (B)",
                        "files": b_files,
                        "depends_on": [],
                        "blocking": True,
                        "lines_est": estimate_lines_changed(b_files[0], prompt),
                        "separations": [(a, b)],
                        "timeout": 400,
                        "model": "deepseek/deepseek-v4-pro",
                    })
                if others:
                    modules.append({
                        "id": f"M{len(modules)+1}",
                        "name": f"Modify {os.path.basename(prefix or 'core')} (other)",
                        "files": others,
                        "depends_on": [],
                        "lines_est": estimate_lines_changed(others[0] if others else "", prompt),
                        "timeout": 300,
                        "model": "deepseek/deepseek-v4-pro",
                    })
        else:
            # Check if all fit in one module
            issues, total_est = size_check(file_list, prompt)
            if not issues:
                modules.append({
                    "id": f"M{len(modules)+1}",
                    "name": f"Modify {os.path.basename(prefix or 'core')}",
                    "files": file_list,
                    "depends_on": [],
                    "blocking": any(f in BLOCKING_FILES for f in file_list),
                    "lines_est": total_est,
                    "separations": [],
                    "timeout": min(900, 300 + total_est),
                    "model": "deepseek/deepseek-v4-pro",
                })
            else:
                # Split into chunks
                for i, f in enumerate(file_list):
                    modules.append({
                        "id": f"M{len(modules)+1}",
                        "name": f"Modify {os.path.basename(f)}",
                        "files": [f],
                        "depends_on": [],
                        "blocking": f in BLOCKING_FILES,
                        "lines_est": estimate_lines_changed(f, prompt),
                        "separations": [],
                        "timeout": 300,
                        "model": "deepseek/deepseek-v4-pro",
                    })
    
    # Compute dependency links between modules
    for i, mod_a in enumerate(modules):
        a_files = mod_a["files"]
        for j, mod_b in enumerate(modules):
            if i == j: continue
            b_files = mod_b["files"]
            # Does module B depend on module A?
            for a_file in a_files:
                for bf in b_files:
                    deps_for_bf = compute_dependencies(b_files).get(bf, [])
                    if a_file in deps_for_bf:
                        # M_b depends on M_a → M_a runs first
                        mod_b["depends_on"].append(mod_a["id"])
    
    # Determine execution order (topological sort)
    mod_ids = {m["id"]: m for m in modules}
    ordered = []
    visited = set()
    
    def visit(mid):
        if mid in visited: return
        visited.add(mid)
        m = mod_ids[mid]
        for dep in m.get("depends_on", []):
            visit(dep)
        ordered.append(mid)
    
    for m in modules:
        visit(m["id"])
    
    # Update timeout based on position
    for m in modules:
        if m["blocking"]:
            m["timeout"] = min(900, max(300, m["timeout"]))
        else:
            m["timeout"] = min(600, max(180, m["timeout"]))
    
    return modules, ordered

def infer_parallel_groups(modules, ordered):
    """Find modules that CAN run in parallel"""
    parallel_groups = []
    used = set()
    
    for m in modules:
        if m["id"] in used: continue
        if m["blocking"]:
            continue  # Blocking files = sequential only
        
        # Find other modules with same dependency set and no conflicts
        group = [m["id"]]
        used.add(m["id"])
        for m2 in modules:
            if m2["id"] in used: continue
            if m2["blocking"]: continue
            
            # Can they run together?
            if set(m.get("depends_on", [])) == set(m2.get("depends_on", [])):
                # Check separation rule
                combined_files = m["files"] + m2["files"]
                violations = check_separation_rule(combined_files)
                if not violations:
                    group.append(m2["id"])
                    used.add(m2["id"])
        
        if len(group) > 1:
            parallel_groups.append(group)
    
    return parallel_groups

# ─── Plan Command ────────────────────────────────────

def cmd_plan(args):
    prompt = args.prompt
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    print("=" * 55)
    print(f"  📐 Task Planner — {now}")
    print(f"  Task: {prompt[:80]}")
    print("=" * 55)
    print()
    
    # Step 1: Infer relevant files
    print("─── Step 1: File Discovery ───")
    files = get_files_from_prompt(prompt)
    if not files:
        print("  ⚠️  No specific files inferred from prompt.")
        print("  ℹ️️  Must pass --files or refine prompt.")
        print()
        # Prompt-based fallback: just generate a generic plan
        print("  🔮 Would analyze: codebase for relevant patterns")
        print()
        sys.exit(1)
    
    # Verify files exist on VPS
    existing = [f for f in files if check_file_exists(f)]
    missing = [f for f in files if not check_file_exists(f)]
    
    for f in existing:
        print(f"  ✅ {f}")
    for f in missing:
        print(f"  ⚠️  {f} (not found — will check subdirs)")
    
    # Expand missing files — search subdirectories
    expanded = []
    for f in missing:
        base = os.path.basename(f)
        # Search in common directories
        rc, o, e = run(f"find /root/psvibe-sales-bot -name '*.py' -path '*{base}*' 2>/dev/null | head -5")
        if o:
            expanded.extend(o.split("\n"))
        else:
            expanded.append(f)
    
    all_files = list(dict.fromkeys(existing + expanded))
    print(f"  Total relevant files: {len(all_files)}")
    print()
    
    # Step 2: Apply max size rules and split
    print("─── Step 2: Module Decomposition ───")
    print(f"  📏 Max Module Size Rules:")
    print(f"     • Files: {MAX_LIMITS['files']}")
    print(f"     • Lines: {MAX_LIMITS['lines']}")
    print(f"     • Functions: {MAX_LIMITS['functions']}")
    print(f"     • Timeout: {MAX_LIMITS['timeout_seconds']}s")
    print(f"     • Dep Depth: {MAX_LIMITS['dep_depth']}")
    print(f"  🔴 Blocking (no parallel): {', '.join(BLOCKING_FILES)}")
    print()
    
    modules, order = split_into_modules(all_files, prompt)
    
    print(f"  📊 Split into {len(modules)} module(s)")
    for i, m in enumerate(modules, 1):
        sep_warn = " ⚠️ SEPARATED" if m.get("separations") else ""
        block_tag = " 🔴 PARALLEL BLOCKED" if m.get("blocking") else " 🟢 PARALLEL OK"
        deps = f" → dep: {', '.join(m['depends_on'])}" if m.get('depends_on') else ""
        print(f"  {i}. {m['id']}: {', '.join(m['files'][:3])} (~{m['lines_est']}L){sep_warn}{block_tag}{deps}")
    print()
    
    # Step 3: Determine execution order
    print("─── Step 3: Execution Order ───")
    print(f"  Sequential chain: {' → '.join(order)}")
    print()
    
    # Step 4: Parallel groups
    parallel_groups = infer_parallel_groups(modules, order)
    if parallel_groups:
        print("─── Step 4: Parallel Groups ───")
        for g in parallel_groups:
            print(f"  ⚡ Parallel: {' + '.join(g)}")
        print()
    
    # Step 5: Generate spawn commands
    print("─── Step 5: Spawn Commands ───")
    for m in modules:
        task_name = m["name"].lower().replace(" ", "_")[:30]
        task_name = re.sub(r'[^a-z0-9_]', '', task_name)
        
        files_str = ", ".join(m["files"])
        desc = prompt[:60]
        
        print(f"  ── Module {m['id']}: {m['name']} ──")
        print(f"  🎯 Files: {files_str}")
        print(f"  ⏱️  Timeout: {m['timeout']}s")
        print(f"  🔒 Blocking: {'YES' if m.get('blocking') else 'no'}")
        print()
        print(f"  sessions_spawn(")
        print(f"      taskName=\"{task_name}\",")
        print(f"      task=\"\"\"Modify {files_str}")
        print(f"  {desc}")
        print(f"  VPS: 5.223.81.16 (key /root/psvibe-sales-bot)")
        print(f"      \"\"\",")
        print(f"      model=\"{m['model']}\",")
        print(f"      runTimeoutSeconds={m['timeout']},")
        print(f"  )")
        print()
    
    # Step 6: Save plan
    plan = {
        "generated": now,
        "prompt": prompt,
        "max_limits": MAX_LIMITS,
        "total_modules": len(modules),
        "execution_order": order,
        "parallel_groups": parallel_groups,
        "modules": []
    }
    
    for m in modules:
        plan["modules"].append({
            "id": m["id"],
            "name": m["name"],
            "files": m["files"],
            "depends_on": m.get("depends_on", []),
            "blocking": m.get("blocking", False),
            "lines_est": m.get("lines_est", 50),
            "separations": m.get("separations", []),
            "timeout": m.get("timeout", 300),
            "model": m["model"],
            "spawn_cmd": f'sessions_spawn(taskName="{task_name}", task="Modify {files_str}", model="{m["model"]}", runTimeoutSeconds={m["timeout"]})'
        })
    
    # Write plan file
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r'[^a-z0-9]', '_', prompt[:30].lower())
    plan_file = os.path.join(PLANS_DIR, f"plan_{safe_name}_{timestamp}.json")
    with open(plan_file, "w") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    
    print(f"  📄 Plan saved: {plan_file}")
    print()
    
    # Summary
    print("─── Summary ───")
    print(f"  | # | Module | Files | Lines | Timeout | Blocking | Deps |")
    print(f"  |---|--------|-------|-------|---------|----------|------|")
    for i, m in enumerate(modules, 1):
        print(f"  | {i} | {m['id']:7s} | {len(m['files']):3d} | {m['lines_est']:4d} | {m['timeout']:4d}s | {'🔴' if m.get('blocking') else '🟢':6s} | {'→'.join(m.get('depends_on',[''])):4s} |")
    
    print(f"  Total: {len(modules)} modules | Sequential: {' → '.join(order)}")
    print(f"  ⚠️  Golden Rule: Fix Blocking modules one at a time, yield in between")

# ─── List Plans ──────────────────────────────────────

def cmd_list(args):
    plans = sorted(os.listdir(PLANS_DIR))
    if not plans:
        print("  📭 No plans saved yet")
        return
    print(f"  📋 Saved Plans ({len(plans)}):")
    for p in plans[-10:]:  # Show last 10
        try:
            with open(os.path.join(PLANS_DIR, p)) as f:
                data = json.load(f)
            print(f"  📄 {p}")
            print(f"     Task: {data.get('prompt', '?')[:60]}")
            print(f"     Modules: {data.get('total_modules', '?')} | Order: {' → '.join(data.get('execution_order', []))}")
        except:
            print(f"  📄 {p} (unreadable)")

# ─── Size Rules Info ─────────────────────────────────

def cmd_rules(args):
    print("=" * 55)
    print("  📏 Task Planner — Max Module Size Rules")
    print("=" * 55)
    print()
    print("  ┌─────────────┬──────────┬────────────────────────┐")
    print("  │ Metric      │ Max      │ Why?                   │")
    print("  ├─────────────┼──────────┼────────────────────────┤")
    print("  │ Files       │ 3        │ Sub-agent focus limit  │")
    print("  │ Lines       │ 250      │ Generation quality cap │")
    print("  │ Functions   │ 2        │ Single responsibility  │")
    print("  │ Timeout     │ 900s     │ Cost & slot management │")
    print("  │ Dep Depth   │ 3        │ Cascade risk control   │")
    print("  └─────────────┴──────────┴────────────────────────┘")
    print()
    print("  🔴 BLOCKING FILES (NEVER parallel):")
    for bf in BLOCKING_FILES:
        print(f"     • {bf}")
    print()
    print("  ⚠️  SEPARATION RULES (NEVER same module):")
    for (a, b) in SEPARATE_FILES:
        print(f"     • {a} + {b}")
    print()
    print("  🟢 PARALLEL OK: Independent files, same dep level, no conflicts")
    print("  🔴 SEQUENTIAL ONLY: Blocking files, shared deps, separation rules")
    print()

# ─── Show Plan Detail ─────────────────────────────────

def cmd_show(args):
    plan_file = args.plan
    try:
        with open(plan_file) as f:
            data = json.load(f)
    except:
        print(f"  ❌ Cannot read: {plan_file}")
        sys.exit(1)
    
    print(f"  📄 Plan: {plan_file}")
    print(f"  Task: {data.get('prompt', '?')}")
    print(f"  Generated: {data.get('generated', '?')}")
    print(f"  Modules: {data.get('total_modules', '?')}")
    print(f"  Order: {' → '.join(data.get('execution_order', []))}")
    print()
    
    for m in data.get("modules", []):
        print(f"  ── {m['id']}: {m['name']} ──")
        print(f"     Files: {', '.join(m['files'])}")
        print(f"     Lines: ~{m['lines_est']} | Timeout: {m['timeout']}s")
        print(f"     Blocking: {m.get('blocking', False)}")
        if m.get("depends_on"): print(f"     Deps: {', '.join(m['depends_on'])}")
        print()

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Task Planner Agent — Decompose tasks into modular units")
    s = p.add_subparsers(dest="cmd")
    
    plan = s.add_parser("plan", help="Generate a task execution plan")
    plan.add_argument("--prompt", required=True, help="Task description from Boss")
    plan.add_argument("--files", default="", help="Specific files to include (comma-separated)")
    
    ls = s.add_parser("list", help="List saved plans")
    
    show = s.add_parser("show", help="Show a saved plan")
    show.add_argument("--plan", required=True, help="Plan file path")
    
    rules = s.add_parser("rules", help="Show max module size rules")
    
    a = p.parse_args()
    if a.cmd == "plan": cmd_plan(a)
    elif a.cmd == "list": cmd_list(a)
    elif a.cmd == "show": cmd_show(a)
    elif a.cmd == "rules": cmd_rules(a)
    else: p.print_help()
