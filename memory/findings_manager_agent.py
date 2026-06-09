#!/usr/bin/env python3
"""
Findings Manager Agent — Dedicated merge_findings helper for Kora.

Usage (by Kora):
    sessions_spawn(
        taskName="findings-merge",
        task="Run /root/coordination/findings_manager.py and report results",
        runTimeoutSeconds=120
    )

This script:
1. Checks /root/coordination/findings/ for new temp files
2. Runs merge_findings.py (upsert + clean stale)
3. Prints a summary report for Kora
4. Never writes SHARED_FINDINGS.md directly (merge_findings.py does it)
"""
import json, os, subprocess, sys
from datetime import datetime

FD = "/root/coordination/findings"
SF = "/root/coordination/SHARED_FINDINGS.md"
MF = "/root/coordination/merge_findings.py"

def run(c, t=15):
    try:
        r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"

def check_findings_dir():
    """Check what's in findings/"""
    if not os.path.isdir(FD):
        return []
    files = [f for f in os.listdir(FD) if f.endswith(".json")]
    entries = []
    for f in files:
        try:
            with open(os.path.join(FD, f)) as fh:
                data = json.load(fh)
            if isinstance(data, list):
                entries.extend(data)
            elif isinstance(data, dict):
                entries.append(data)
        except json.JSONDecodeError:
            pass
    return entries

def check_sf_exists():
    """Check if SHARED_FINDINGS.md has content"""
    if not os.path.exists(SF):
        return False
    with open(SF) as f:
        content = f.read()
    # Check if there are table rows beyond the header
    rows = [l for l in content.split("\n") if l.startswith("|") and not l.startswith("|---")]
    return len(rows) > 1

def run_merge():
    """Run merge_findings.py"""
    cwd = os.path.dirname(MF) or "/root/coordination"
    rc, out, err = run(f"cd {cwd} && python3 {MF} 2>&1")
    return rc, out, err

def get_summary():
    """Get summary from SHARED_FINDINGS.md"""
    if not os.path.exists(SF):
        return {"total": 0, "critical": 0, "high": 0, "medium": 0}
    with open(SF) as f:
        content = f.read()
    rows = [l for l in content.split("\n") if l.startswith("|") and not l.startswith("|---") and not l.startswith("| #")]
    # Count severity from table rows
    sevs = {"🔴": 0, "🟡": 0, "🟢": 0, "⚪": 0}
    total = 0
    for row in rows:
        cols = row.split("|")
        if len(cols) >= 4:
            sev = cols[3].strip() if len(cols) > 3 else ""
            for s in sevs:
                if s in sev:
                    sevs[s] += 1
                    total += 1
    return {"total": total, **{k: v for k, v in sevs.items()}}

def extract_stale(content):
    """Extract stale entries from output"""
    stale = []
    for line in content.split("\n"):
        if "Removed" in line and "stale" in line:
            stale.append(line)
        elif line.startswith("     - "):
            stale.append(line.strip())
    return stale

def print_report(rc, merge_output, before_count, stale_count):
    """Print structured report for Kora"""
    summary = get_summary()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    print("=" * 50)
    print(f"📋 Findings Manager Report — {now}")
    print("=" * 50)
    print()
    
    if rc != 0:
        print(f"❌ MERGE FAILED (exit code {rc})")
        print(f"   Error: {merge_output[:500]}")
        sys.exit(1)
    
    print(f"📥 Input: {before_count} new finding(s)")
    print(f"📊 Output: {summary['total']} entries in SHARED_FINDINGS.md")
    if stale_count:
        print(f"🗑️  Stale removed: {stale_count}")
    print()
    
    print(f"   🔴 Critical: {summary['🔴']}")
    print(f"   🟡 High:     {summary['🟡']}")
    print(f"   🟢 Medium:   {summary['🟢']}")
    print()
    
    print("✅ Merge complete — SHARED_FINDINGS.md updated")
    print()

if __name__ == "__main__":
    before = check_findings_dir()
    print(f"🔎 Checking {FD}/... found {len(before)} new finding(s)")
    
    sf_ok = check_sf_exists()
    
    rc, out, err = run_merge()
    
    # Extract stale count from output
    stale_lines = extract_stale(out)
    stale_count = 0
    for l in stale_lines:
        if "Removed" in l:
            parts = l.split()
            for p in parts:
                if p.isdigit():
                    stale_count = int(p)
                    break
    
    print_report(rc, out, len(before), stale_count)
    
    if stale_lines:
        print("🗑️  Removed stale entries:")
        for l in stale_lines:
            print(f"   {l}")
        print()
    
    print("---")
    print("📁 Location: /root/coordination/SHARED_FINDINGS.md")
    print("🔗 Protocol: sub-agents → findings/<agent>.json | Kora → merge_findings.py")
