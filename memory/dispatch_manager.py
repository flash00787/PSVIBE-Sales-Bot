#!/usr/bin/env python3
"""
Dispatch Manager Agent — Auto-dispatch fix agents from audit findings.

Flow:
  1. Audit agent writes findings → findings/<audit>.json (with status="PENDING")
  2. Kora spawns Dispatch Manager
  3. Dispatch Manager reads PENDING findings, groups by file
  4. For each group → prints structured spawn cmd for Kora
  5. Kora iterates spawns + yields
  6. Fix agents update findings to "FIXED"
  7. Kora runs Findings Manager → merge

Usage (by Kora):
    sessions_spawn(
        taskName="dispatch-fixes",
        task="python3 /root/coordination/dispatch_manager.py --dispatch",
        runTimeoutSeconds=180,
        model="deepseek/deepseek-v4-flash"
    )
"""
import argparse, json, os, subprocess, sys
from datetime import datetime

SF = "/root/coordination/SHARED_FINDINGS.md"
FD = "/root/coordination/findings"

def run(c, t=10):
    try:
        r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except: return -1, "", "TIMEOUT"

def load_pending():
    """Load all findings with status=PENDING or empty status"""
    if not os.path.isdir(FD):
        return []
    pending = []
    for fname in sorted(os.listdir(FD)):
        if not fname.endswith(".json"): continue
        try:
            with open(os.path.join(FD, fname)) as f:
                data = json.load(f)
            if isinstance(data, list):
                for e in data:
                    if not e.get("status") or e.get("status") == "PENDING":
                        pending.append(e)
            elif isinstance(data, dict):
                if not data.get("status") or data.get("status") == "PENDING":
                    pending.append(data)
        except: pass
    return pending

def load_sf_pending():
    """Load pending findings from SHARED_FINDINGS.md"""
    if not os.path.exists(SF): return []
    pending = []
    with open(SF) as f:
        for line in f:
            if line.startswith("|") and "🔧" in line:  # 🔧 = PENDING status
                pending.append(line.strip())
    return pending

def group_by_file(entries):
    """Group entries by file path for efficient fix batching"""
    groups = {}
    for e in entries:
        fp = e.get("file", "unknown")
        # Extract base file path (remove line numbers like :2450)
        base = fp.split(":")[0] if ":" in fp else fp
        if base not in groups:
            groups[base] = []
        groups[base].append(e)
    return groups

def find_bot_path(grouped_files):
    """Try to find the main file for bot/__init__.py grouping"""
    # If __init__.py is involved, always return that as primary
    for fp in grouped_files:
        if "__init__.py" in fp:
            return fp
    return list(grouped_files.keys())[0] if grouped_files else "unknown"

def generate_spawn_commands(groups):
    """For each group, generate a spawn command"""
    commands = []
    for filepath, entries in sorted(groups.items()):
        # Deduce fix description from entries
        changes = [e.get("change", "unknown") for e in entries if e.get("change")]
        desc = "; ".join(changes[:3])  # Max 3 changes per description
        if len(changes) > 3:
            desc += f" +{len(changes)-3} more"
        
        # Determine timeout based on severity and count
        has_critical = any("🔴" in e.get("severity","") for e in entries)
        timeout = 900 if has_critical else 600
        if len(entries) > 5: timeout = 1200
        
        # Determine model
        model = "deepseek/deepseek-v4-pro"
        
        # Determine task name
        safe_name = filepath.replace("/", "_").replace(".py", "").replace(":", "_")[:40]
        
        commands.append({
            "taskName": f"fix-{safe_name}",
            "description": desc[:100],
            "files": filepath,
            "model": model,
            "timeout": timeout,
            "entries": len(entries),
            "severity": max((e.get("severity","🟢") for e in entries), key=lambda x: ["🔴","🟡","🟢","⚪"].index(x if x in "🔴🟡🟢⚪" else "🟢")),
            "filepath": filepath,
            "entry_ids": [e.get("id","?") for e in entries],
        })
    return commands

def print_report(commands):
    """Print dispatch report with spawn instructions"""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    total_entries = sum(c["entries"] for c in commands)
    
    print("=" * 55)
    print(f"  🔄 Dispatch Manager — {now}")
    print(f"  Pending findings: {total_entries} → {len(commands)} fix group(s)")
    print("=" * 55)
    print()
    
    if not commands:
        print("  ✅ No pending findings — everything is FIXED")
        print()
        return []
    
    for i, cmd in enumerate(commands, 1):
        print(f"  ─── Fix #{i}: {cmd['taskName']} ───")
        print(f"  🎯 File:    {cmd['files']}")
        print(f"  📝 Desc:    {cmd['description']}")
        print(f"  🔒 Severity: {cmd['severity']} ({cmd['entries']} issue(s))")
        print(f"  🤖 Model:   {cmd['model']}")
        print(f"  ⏱ Timeout: {cmd['timeout']}s")
        print()
        print(f"  Kora, run this:")
        print(f"  sessions_spawn(")
        print(f'      taskName="{cmd["taskName"]}",')
        print(f'      task="""Fix {cmd["description"]}')
        print()
        print(f"  VPS: 5.223.81.16 (key /root/.openclaw/workspace/.ssh/id_rsa)")
        print(f"  Files: {cmd['files']}")
        print(f"  Bot path: /root/psvibe-sales-bot")
        print(f'      """,')
        print(f'      model="{cmd["model"]}",')
        print(f'      runTimeoutSeconds={cmd["timeout"]},')
        print(f"  )")
        print()
    
    # Print summary table
    print("  ─── Summary ───")
    print(f"  | # | Task | File | Entries | Severity |")
    print(f"  |---|------|------|---------|----------|")
    for i, cmd in enumerate(commands, 1):
        print(f"  | {i} | {cmd['taskName'][:25]:25s} | {cmd['files'][:25]:25s} | {cmd['entries']:3d} | {cmd['severity']} |")
    print()
    print(f"  Total: {len(commands)} fix command(s) | {total_entries} issue(s)")
    print()
    print("  ⚡ After ALL fixes complete → run Findings Manager:")
    print("  sessions_spawn(taskName='findings-merge', task='python3 /root/coordination/findings_manager.py', runTimeoutSeconds=120)")
    print()
    
    return commands

def status_findings():
    """Show current pending findings status"""
    pending = load_pending()
    pending_sf = load_sf_pending()
    
    print("  📋 Pending findings (temp files):", len(pending))
    for e in pending:
        s = e.get("severity","?")
        f = e.get("file","?")
        c = e.get("change","?")[:40]
        print(f"    {s} {f:40s} {c}")
    
    print()
    print(f"  📋 Pending findings (SHARED_FINDINGS.md): {len(pending_sf)}")
    for l in pending_sf[:5]:
        print(f"    {l[:80]}")
    if len(pending_sf) > 5:
        print(f"    ... +{len(pending_sf)-5} more")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Dispatch Manager — Auto-dispatch fix agents")
    p.add_argument("--dispatch", action="store_true", help="Analyze pending findings and print spawn commands")
    p.add_argument("--status", action="store_true", help="Show pending findings status")
    a = p.parse_args()
    
    if a.status:
        status_findings()
    elif a.dispatch:
        pending = load_pending()
        if not pending:
            # Fall back to SHARED_FINDINGS.md
            pending_sf = load_sf_pending()
            if pending_sf:
                print("  ⚠️  Pending findings found in SHARED_FINDINGS.md but not in temp files.")
                print("  ⚡ Run Findings Manager first to sync:")
                print("  sessions_spawn(taskName='findings-merge', task='python3 /root/coordination/findings_manager.py', runTimeoutSeconds=120)")
            else:
                print("  ✅ No pending findings — everything is FIXED")
            sys.exit(0)
        
        groups = group_by_file(pending)
        commands = generate_spawn_commands(groups)
        print_report(commands)
        
        if commands:
            # Write dispatch plan as JSON for reference
            plan = {"generated": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "commands": commands}
            with open("/root/coordination/dispatch_plan.json", "w") as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)
            print(f"  📄 Dispatch plan saved: /root/coordination/dispatch_plan.json")
            print()
    else:
        pending = load_pending()
        print(f"  📊 {len(pending)} pending finding(s) in {FD}/")
        p.print_help()
