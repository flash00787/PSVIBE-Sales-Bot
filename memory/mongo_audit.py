#!/usr/bin/env python3
"""
MongoDB Usage Self-Audit
Checks if MongoDB was available AND used in recent memory entries.
Run anytime: python3 /root/.openclaw/workspace/memory/mongo_audit.py

Exit 0 = MongoDB was used properly
Exit 1 = MongoDB was available but possibly not used (warning)
Exit 2 = MongoDB is down
"""

import sys, os, subprocess, json
from datetime import datetime, timezone, timedelta

MONGO_CLI = "/root/coordination/kora_memory.py"
MEMORY_DIR = os.path.dirname(os.path.abspath(__file__))

def check_mongo_available():
    """Check if MongoDB is reachable."""
    try:
        r = subprocess.run(
            [sys.executable, MONGO_CLI, "code-stats"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            entities = "unknown"
            relations = "unknown"
            for line in r.stdout.split("\n"):
                if "Entities:" in line and "Relations:" in line:
                    parts = line.split("|")
                    entities = parts[0].split(":")[-1].strip() if len(parts) > 0 else "unknown"
                    relations = parts[1].split(":")[-1].strip() if len(parts) > 1 else "unknown"
            print(f"✅ MongoDB available — {entities} entities, {relations} relations")
            return True, entities, relations
        else:
            print(f"❌ MongoDB CLI error (exit {r.returncode})")
            return False, "0", "0"
    except FileNotFoundError:
        print(f"❌ MongoDB CLI not found at {MONGO_CLI}")
        return False, "0", "0"
    except subprocess.TimeoutExpired:
        print(f"❌ MongoDB timeout — connection issue")
        return False, "0", "0"

def check_today_entries():
    """Count today's memory entries."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        r = subprocess.run(
            [sys.executable, MONGO_CLI, "query", "--date-from", today, "--limit", "20"],
            capture_output=True, text=True, timeout=10
        )
        count = 0
        for line in r.stdout.split("\n"):
            if line.strip() and line.strip()[0].isdigit() and ". " in line[:4]:
                count += 1
        
        if count > 0:
            print(f"📝 Today's entries: {count}")
        else:
            print(f"📝 No entries today")
        
        # Check if recent entries include fixes/patches (which should use MongoDB)
        fix_count = 0
        for line in r.stdout.split("\n"):
            if "[fix" in line.lower() or "[bug" in line.lower():
                fix_count += 1
        
        if fix_count > 0:
            print(f"   🐛 Bug/fix entries today: {fix_count}")
        
        return count, fix_count
    except Exception as e:
        print(f"   ⚠️  Query error: {e}")
        return 0, 0

def check_recent_fix_activity():
    """Check if recent memory entries mention fixes without MongoDB context."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    
    try:
        r = subprocess.run(
            [sys.executable, MONGO_CLI, "query", "--date-from", yesterday, "--type", "fix", "--limit", "10"],
            capture_output=True, text=True, timeout=10
        )
        
        fixes_without_mongo = []
        for line in r.stdout.split("\n"):
            if "[fix" in line.lower():
                # Check if MongoDB was used (hint: fix description mentions trace/impact)
                has_mongo_hint = any(kw in line.lower() for kw in ["mongo", "trace", "impact", "code graph"])
                if not has_mongo_hint:
                    fixes_without_mongo.append(line.strip()[:100])
        
        if fixes_without_mongo:
            print(f"\n⚠️  Recent fixes without MongoDB context: {len(fixes_without_mongo)}")
            for f in fixes_without_mongo[:3]:
                print(f"   • {f}")
            return False
        return True
    except Exception:
        return True  # Non-blocking

def main():
    print("=" * 50)
    print("🧠 MongoDB Usage Self-Audit")
    print(f"   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 50)
    print()
    
    available, entities, relations = check_mongo_available()
    if not available:
        print("\n🔴 VERDICT: MongoDB DOWN — fix immediately")
        print("   All debugging must use grep/read as fallback (slow)")
        return 2
    
    count, fix_count = check_today_entries()
    
    all_clear = check_recent_fix_activity()
    
    print()
    print("=" * 50)
    if all_clear:
        print("✅ VERDICT: MongoDB healthy — use kora_memory.py trace FIRST")
    else:
        print("🟡 VERDICT: MongoDB available but underutilized")
        print("   REMINDER: Rule #0 — MongoDB trace BEFORE grep/read")
    print("=" * 50)
    
    return 0 if all_clear else 1

if __name__ == "__main__":
    sys.exit(main())
