#!/usr/bin/env python3
"""Archive large .md files to MongoDB, then clean up from disk."""

import os, json, subprocess, sys
from datetime import datetime

BASE = "/root/.openclaw/workspace/memory/"
ARCHIVE_DIR = os.path.join(BASE, "archived_to_mongo")

# Files to archive: (relative_path, type, title, tags)
FILES = [
    ("booking-session-separation-plan.md", "audit", "Booking Session Separation Plan", "booking,plan,archive"),
    ("ARCHIVE.md", "audit", "Legacy ARCHIVE.md — Comprehensive Memory Archive", "archive,legacy"),
    ("projects/acm_wallet/mysql-migration-impact.md", "audit", "ACM Wallet MySQL Migration Impact Analysis", "acm_wallet,migration,archive"),
    ("analysis/multi_project_architecture_2026-06-25.md", "audit", "Multi-Project Architecture Analysis (Jun 2026)", "architecture,analysis,archive"),
    ("booking-features-plan.md", "audit", "Booking Features Implementation Plan", "booking,plan,archive"),
    ("booking-audit-deep-round2.md", "audit", "Booking Audit Deep Round 2", "booking,audit,archive"),
    ("psvibe-comprehensive-scan.md", "audit", "PS VIBE Comprehensive System Scan", "psvibe,scan,archive"),
    ("booking_upgrade_audit.md", "audit", "Booking Upgrade Audit", "booking,upgrade,audit,archive"),
    ("admin-group-notif-audit.md", "audit", "Admin Group Notification Audit", "notification,audit,archive"),
    ("booking-session-separation-audit.md", "audit", "Booking Session Separation Audit", "booking,session,audit,archive"),
    ("bug-patterns.md", "lesson", "Kora Bug Patterns Reference", "bug,pattern,reference,archive"),
    ("booking-system-audit-2026-06-19.md", "audit", "Booking System Audit — June 19", "booking,system,audit,archive"),
    ("sop/COORDINATION_FRAMEWORK.md", "general", "Coordination Framework SOP", "sop,coordination,framework,archive"),
    ("sop/HELPER_GUIDELINES.md", "general", "Helper Guidelines SOP", "sop,helper,guidelines,archive"),
    ("sop/SPAWNING_MANAGER_SOP.md", "general", "Spawning Manager SOP", "sop,spawning,manager,archive"),
    ("sop/SPAWN_PROTOCOL.md", "general", "Spawn Protocol SOP", "sop,spawn,protocol,archive"),
    ("booking-audit-complete.md", "audit", "Booking Audit Complete Report", "booking,audit,complete,archive"),
    ("customer-bot-notif-audit.md", "audit", "Customer Bot Notification Audit", "customer_bot,notification,audit,archive"),
    ("gsheet_removal_audit.md", "audit", "GSheet Removal Audit", "gsheet,removal,audit,archive"),
    ("booking-timeslot-audit.md", "audit", "Booking Timeslot Audit", "booking,timeslot,audit,archive"),
]

def write_to_mongo(rel_path, entry_type, title, tags):
    full_path = os.path.join(BASE, rel_path)
    if not os.path.exists(full_path):
        print(f"  ⏭️  NOT FOUND: {rel_path}")
        return False

    with open(full_path, "r") as f:
        content = f.read()

    size_kb = len(content) / 1024
    print(f"  📄 {rel_path} ({size_kb:.0f}KB) → MongoDB...")

    cmd = [
        sys.executable, "/root/coordination/kora_memory.py", "write",
        "--type", entry_type,
        "--title", title,
        "--content", content,
        "--status", "archived",
        "--tags", tags,
        "--date", datetime.now().strftime("%Y-%m-%d"),
        "--severity", "low",
        "--extra", json.dumps({"archived_from": rel_path, "original_size_kb": round(size_kb, 1)})
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        print(f"  ✅ Stored: {title}")
        return True
    else:
        print(f"  ❌ Error: {result.stderr[:500]}")
        return False

def main():
    print("=" * 60)
    print("📦 Archiving large .md files to MongoDB")
    print("=" * 60)
    print()

    # Create archive dir
    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    success = 0
    fail = 0
    skipped = 0

    for rel_path, entry_type, title, tags in FILES:
        full_path = os.path.join(BASE, rel_path)
        if not os.path.exists(full_path):
            print(f"  ⏭️  NOT FOUND: {rel_path}")
            skipped += 1
            continue

        if write_to_mongo(rel_path, entry_type, title, tags):
            # Move file to archive dir
            parent = os.path.dirname(os.path.join(ARCHIVE_DIR, rel_path))
            os.makedirs(parent, exist_ok=True)
            dest = os.path.join(ARCHIVE_DIR, rel_path)
            os.rename(full_path, dest)
            print(f"     📁 Moved → archived_to_mongo/{rel_path}")
            success += 1
        else:
            fail += 1

    print()
    print("=" * 60)
    print(f"📊 Results: {success} archived ✅ | {fail} failed ❌ | {skipped} skipped ⏭️")
    print("=" * 60)
    print()
    print("🔍 How to retrieve:")
    print('   kora_memory.py search "<topic>"                    # Full-text search')
    print('   kora_memory.py query --status archived --limit 10  # List archived entries')
    print('   kora_memory.py export --type audit                 # Export to .md files')
    print()

if __name__ == "__main__":
    main()
