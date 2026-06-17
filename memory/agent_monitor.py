#!/usr/bin/env python3
"""
🤖 Agent Performance Monitor
Tracks sub-agent spawns, success/failure rates, and model fallback patterns.
"""
import json, os, subprocess, time, re
from datetime import datetime, timezone

WORKSPACE = "/root/.openclaw/workspace"
LOG_FILE = os.path.join(WORKSPACE, "memory/agent_stats.json")
MAX_HISTORY = 100

def load_stats():
    try:
        with open(LOG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "total_spawns": 0,
            "success": 0,
            "failure": 0,
            "fallback_count": 0,
            "model_stats": {},
            "recent_failures": [],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

def save_stats(stats):
    stats["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, "w") as f:
        json.dump(stats, f, indent=2)

def record_spawn(model="unknown", success=True, fallback=False, error=""):
    stats = load_stats()
    stats["total_spawns"] += 1
    if success:
        stats["success"] += 1
    else:
        stats["failure"] += 1
        stats["recent_failures"].insert(0, {
            "time": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "error": error[:200]
        })
        stats["recent_failures"] = stats["recent_failures"][:20]
    if fallback:
        stats["fallback_count"] += 1
    
    # Track per-model stats
    if model not in stats["model_stats"]:
        stats["model_stats"][model] = {"spawns": 0, "success": 0, "failures": 0}
    stats["model_stats"][model]["spawns"] += 1
    if success:
        stats["model_stats"][model]["success"] += 1
    else:
        stats["model_stats"][model]["failures"] += 1
    
    save_stats(stats)
    return stats

def report():
    """Generate a human-readable performance report"""
    stats = load_stats()
    total = stats["total_spawns"]
    if total == 0:
        return "No sub-agent activity recorded yet."
    
    success_rate = round(stats["success"] / total * 100, 1)
    fallback_rate = round(stats.get("fallback_count", 0) / total * 100, 1)
    
    lines = [
        f"📊 Agent Performance Report",
        f"━━━━━━━━━━━━━━━━━━━━━",
        f"Total spawns: {total}",
        f"Success rate: {stats['success']}/{total} ({success_rate}%)",
        f"Fallback rate: {fallback_rate}%",
    ]
    
    # Model breakdown
    lines.append(f"\n🤖 By Model:")
    for model, ms in sorted(stats["model_stats"].items()):
        rate = round(ms["success"] / ms["spawns"] * 100, 1) if ms["spawns"] > 0 else 0
        status = "✅" if rate >= 90 else "⚠️" if rate >= 70 else "🔴"
        lines.append(f"  {status} {model}: {ms['spawns']} spawns, {rate}% success")
    
    # Recent failures
    failures = stats.get("recent_failures", [])
    if failures:
        lines.append(f"\n❌ Recent Failures ({len(failures)} in history):")
        for f in failures[:5]:
            lines.append(f"  • [{f['time'][:16]}] {f['model']}")
            if f['error']:
                lines.append(f"    → {f['error'][:100]}")
    
    # Alerts
    alerts = []
    if success_rate < 80:
        alerts.append(f"🔴 CRITICAL: Success rate is {success_rate}%")
    if fallback_rate > 10:
        alerts.append(f"⚠️ High fallback rate: {fallback_rate}%")
    
    if alerts:
        lines.append(f"\n🚨 Alerts:")
        for a in alerts:
            lines.append(f"  {a}")
    
    return "\n".join(lines)

def check_subagent_health():
    """Check if sub-agents are stuck or unhealthy"""
    stats = load_stats()
    total = stats["total_spawns"]
    if total < 5:
        return "OK"  # Not enough data
    
    success_rate = round(stats["success"] / total * 100, 1)
    if success_rate < 60:
        return "CRITICAL"
    elif success_rate < 80:
        return "WARN"
    return "OK"

if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "report"
    
    if action == "report":
        print(report())
    elif action == "health":
        status = check_subagent_health()
        print(f"SUBAGENT_HEALTH: {status}")
    elif action == "record":
        model = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        success = sys.argv[3] == "true" if len(sys.argv) > 3 else True
        fallback = sys.argv[4] == "true" if len(sys.argv) > 4 else False
        error = sys.argv[5] if len(sys.argv) > 5 else ""
        record_spawn(model, success, fallback, error)
        print(f"Recorded: {model} {'✓' if success else '✗'}")
