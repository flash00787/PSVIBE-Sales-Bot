#!/usr/bin/env python3
"""
merge_findings.py — Kora-only findings merger
- Reads individual temp findings from /root/coordination/findings/*.json
- Upserts into SHARED_FINDINGS.md (update if exists, add if new)
- Cleans stale entries (files that no longer exist on VPS)
- Single-writer: ONLY Kora calls this, never sub-agents
"""
import os, json, subprocess, re
from datetime import datetime

FD = "/root/coordination/findings"
SF = "/root/coordination/SHARED_FINDINGS.md"
BD = "/root/psvibe-sales-bot"

def run(c,t=10):
    try:
        r = subprocess.run(c,shell=True,capture_output=True,text=True,timeout=t)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except: return -1,"","X"

def load_findings():
    """Load all temp findings from /root/coordination/findings/*.json"""
    entries = {}
    if not os.path.isdir(FD): return entries
    for fname in sorted(os.listdir(FD)):
        if not fname.endswith(".json"): continue
        path = os.path.join(FD, fname)
        try:
            with open(path) as f: data = json.load(f)
            if isinstance(data, list):
                for e in data: entries[e.get("id", fname+str(data.index(e)))] = e
            elif isinstance(data, dict):
                entries[data.get("id", fname)] = data
        except: pass
    return entries

def load_existing():
    """Parse SHARED_FINDINGS.md into list of entries"""
    entries = []
    if not os.path.exists(SF): return entries
    with open(SF) as f: content = f.read()
    # Extract table rows
    in_table = False
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("| ----"): in_table = True; continue
        if not in_table or not line.startswith("|"): continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) >= 6:  # id, agent, sev, file, before_after, why, status
            entries.append({
                "id": cols[0],
                "agent": cols[1],
                "severity": cols[2],
                "file": cols[3],
                "change": cols[4],
                "why": cols[5],
                "status": cols[6] if len(cols) > 6 else "FIXED"
            })
    return entries

def file_exists_on_vps(filepath):
    """Check if a file still exists on VPS"""
    full = os.path.join(BD, filepath) if not filepath.startswith("/") else filepath
    if "*" in filepath or "?" in filepath: return True  # glob pattern, skip
    return os.path.exists(full)

def upsert(existing, new_entries):
    """Merge new entries into existing. Update if same id, append if new."""
    existing_by_id = {e["id"]: e for e in existing}
    for e in new_entries:
        eid = e.get("id", e.get("agent","") + e.get("file",""))
        existing_by_id[eid] = e  # upsert
    return list(existing_by_id.values())

def clean_stale(entries):
    """Remove entries for files that no longer exist on VPS"""
    cleaned = []
    removed = []
    for e in entries:
        fp = e.get("file", "")
        # Extract file path from format like "bot/__init__.py" or "bot/__init__.py:1288"
        match = re.match(r"([^:]+)", fp)
        fpath = match.group(1) if match else fp
        if file_exists_on_vps(fpath):
            cleaned.append(e)
        else:
            removed.append(e)
    return cleaned, removed

def fmt_entry(e):
    """Format a single entry as markdown table row"""
    eid = e.get("id", e.get("agent","?") + e.get("file","?"))
    agent = e.get("agent", "?")
    sev = e.get("severity", "🔴")
    file = e.get("file", "?")
    change = e.get("change", "→")
    why = e.get("why", "")
    status = e.get("status", "FIXED")
    status_icon = "✅" if status == "FIXED" else "🔧"
    return f"| {eid} | {agent} | {sev} | {file} | {change} | {why} | {status_icon} |"

def write_sf(entries, removed=None, findings_dir=None):
    """Write SHARED_FINDINGS.md"""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    # Count by severity
    critical = sum(1 for e in entries if "🔴" in e.get("severity",""))
    high = sum(1 for e in entries if "🟡" in e.get("severity",""))
    medium = sum(1 for e in entries if "🟢" in e.get("severity",""))
    pending = sum(1 for e in entries if e.get("status","FIXED") != "FIXED")
    fixed = len(entries) - pending
    
    lines = [
        f"# SHARED FINDINGS — Consolidated",
        f"## Last updated: {now} | Total: {len(entries)} entries",
        f"",
        f"| # | Agent | Sev | File | Before → After | Why? | Status |",
        f"|---|-------|-----|------|----------------|------|--------|",
    ]
    for e in entries:
        lines.append(fmt_entry(e))
    
    lines += [
        "",
        "---",
        "## 📊 Summary",
        f"**🔴 {critical} Critical | 🟡 {high} High | 🟢 {medium} Medium**",
        f"**Fixed: {fixed} | Pending: {pending}**",
        "",
    ]
    
    if removed:
        lines.append(f"## 🗑️ Removed (stale — {len(removed)} entries)")
        lines.append("| File | Reason |")
        lines.append("|------|--------|")
        for e in removed:
            lines.append(f"| {e.get('file','?')} | File no longer exists on VPS |")
        lines.append("")
    
    lines.append("---")
    lines.append("## 🔍 Protocol")
    lines.append("- **Sub-agents:** Write findings to `/root/coordination/findings/<agent>.json` (NEVER write SHARED_FINDINGS.md directly)")
    lines.append("- **Kora:** Runs `merge_findings.py` to merge temp findings → updates SHARED_FINDINGS.md + cleans stale")
    lines.append("- **Single-writer rule:** Only Kora writes SHARED_FINDINGS.md — no parallel overwrites")
    
    with open(SF, "w") as f:
        f.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    print(f"📂 Scanning {FD}/ for temp findings...")
    new = load_findings()
    print(f"   Found {len(new)} new entry(s)")
    
    print(f"📖 Loading existing {SF}...")
    existing = load_existing()
    print(f"   Found {len(existing)} existing entry(s)")
    
    print(f"🔀 Merging...")
    merged = upsert(existing, list(new.values()))
    print(f"   Result: {len(merged)} entries")
    
    print(f"🧹 Checking stale files...")
    cleaned, removed = clean_stale(merged)
    if removed:
        print(f"   Removed {len(removed)} stale entries")
        for e in removed:
            print(f"     - {e.get('file','?')} ({e.get('agent','?')})")
    else:
        print(f"   No stale entries found")
    
    print(f"✍️ Writing {SF}...")
    write_sf(cleaned, removed)
    
    # Clean up temp files
    if os.path.isdir(FD):
        for fname in os.listdir(FD):
            if fname.endswith(".json"):
                os.remove(os.path.join(FD, fname))
        print(f"   Temp files cleaned: {len(os.listdir(FD))} remaining")
    
    print("✅ Done")
