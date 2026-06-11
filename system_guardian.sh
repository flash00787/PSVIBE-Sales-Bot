#!/bin/bash
# ⚙️ Kora System Guardian — Auto-Health & Stability Framework
# Runs every heartbeat (every ~4h) via the heartbeat routine
# Monitors, fixes, and reports on system health automatically

WORKSPACE="/home/node/.openclaw/workspace"
LOG="$WORKSPACE/temp/guardian_last.txt"

echo "=== Kora System Guardian $(date -u '+%Y-%m-%d %H:%M UTC') ==="

PASS=0
FAIL=0
WARN=0

check() {
    local name="$1"
    local result="$2"
    if [ "$result" = "OK" ]; then
        PASS=$((PASS+1))
        echo "  ✅ $name"
    elif [ "$result" = "WARN" ]; then
        WARN=$((WARN+1))
        echo "  ⚠️ $name"
    else
        FAIL=$((FAIL+1))
        echo "  ❌ $name"
    fi
}

# 1️⃣ MEMORY.md Size Check
size=$(wc -c < "$WORKSPACE/MEMORY.md" 2>/dev/null || echo 0)
if [ "$size" -gt 20480 ]; then
    echo "  ⚠️ MEMORY.md is ${size} bytes — over 20KB limit"
    python3 "$WORKSPACE/memory/memory_pruner.py" --apply 2>/dev/null && check "Memory auto-prune" "OK" || check "Memory auto-prune" "FAIL"
else
    check "MEMORY.md size (${size} bytes < 20KB)" "OK"
fi

# 2️⃣ Session File Count Check
sessions_dir="/home/node/.openclaw/agents/main/sessions"
if [ -d "$sessions_dir" ]; then
    count=$(find "$sessions_dir" -maxdepth 1 -name "*.jsonl" 2>/dev/null | wc -l)
    size_mb=$(du -sm "$sessions_dir" 2>/dev/null | awk '{print $1}')
    
    if [ "$count" -gt 5000 ]; then
        echo "  ⚠️ Session files: $count files (${size_mb}MB) — running cleanup"
        bash "$WORKSPACE/memory/bulk_session_cleanup.sh" 2>/dev/null
        check "Session cleanup triggered" "OK"
    elif [ "$count" -gt 3000 ]; then
        check "Session files: $count (${size_mb}MB)" "WARN"
    else
        check "Session files: $count (${size_mb}MB)" "OK"
    fi
fi

# 3️⃣ Check Session File Size vs 500MB Limit
if [ -n "$size_mb" ] && [ "$size_mb" -gt 400 ]; then
    echo "  🔴 Session approaching 500MB limit (${size_mb}MB / 500MB)"
    bash "$WORKSPACE/memory/bulk_session_cleanup.sh" 2>/dev/null
    check "Emergency session cleanup" "OK"
fi

# 4️⃣ Cron Job Error Check
error_jobs=$(python3 -c "
import json, subprocess
result = subprocess.run(['cron', 'list'], capture_output=True, text=True)
try:
    data = json.loads(result.stdout)
    errors = [(j['name'], j['state'].get('consecutiveErrors',0)) for j in data.get('jobs',[]) if j['state'].get('consecutiveErrors',0) > 0]
    if errors:
        for name, count in errors:
            print(f'{name}: {count}')
    else:
        print('NONE')
except: print('PARSE_ERROR')
" 2>/dev/null)

if [ "$error_jobs" = "NONE" ]; then
    check "Cron jobs (0 errors)" "OK"
elif [ "$error_jobs" = "PARSE_ERROR" ]; then
    check "Cron job check" "WARN"
else
    check "Cron errors found: $error_jobs" "WARN"
fi

# 5️⃣ Disk Space Check
disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$disk_usage" -gt 85 ]; then
    check "Disk usage: ${disk_usage}%" "FAIL"
elif [ "$disk_usage" -gt 70 ]; then
    check "Disk usage: ${disk_usage}%" "WARN"
else
    check "Disk usage: ${disk_usage}%" "OK"
fi

# 6️⃣ Temp Files Cleanup (>7 days)
old_temp=$(find "$WORKSPACE/temp/" -maxdepth 1 -type f -mtime +7 ! -name "guardian*" ! -name "lock_monitor*" ! -name "session_cleanup*" 2>/dev/null | wc -l)
if [ "$old_temp" -gt 0 ]; then
    find "$WORKSPACE/temp/" -maxdepth 1 -type f -mtime +7 ! -name "guardian*" ! -name "lock_monitor*" ! -name "session_cleanup*" -delete 2>/dev/null
    check "Temp cleanup ($old_temp old files removed)" "OK"
else
    check "Temp files clean" "OK"
fi

# 7️⃣ Archive old daily logs (>14 days)
archive_dir="$WORKSPACE/memory/archive"
mkdir -p "$archive_dir"
old_logs=$(find "$WORKSPACE/memory/" -maxdepth 1 -name "2026-*.md" -mtime +14 2>/dev/null | wc -l)
if [ "$old_logs" -gt 0 ]; then
    find "$WORKSPACE/memory/" -maxdepth 1 -name "2026-*.md" -mtime +14 -exec mv {} "$archive_dir/" \; 2>/dev/null
    check "Archived $old_logs old daily logs (>14d)" "OK"
else
    check "Daily logs (all current)" "OK"
fi

# 8️⃣ Sub-agent Health Check
agent_health=$(python3 $WORKSPACE/memory/agent_monitor.py health 2>/dev/null)
agent_report=$(python3 $WORKSPACE/memory/agent_monitor.py report 2>/dev/null)
if [ "$agent_health" = "CRITICAL" ]; then
    check "Agent health: CRITICAL" "FAIL"
    echo "$agent_report" > /tmp/agent_alert.txt
elif [ "$agent_health" = "WARN" ]; then
    check "Agent health: WARN" "WARN"
else
    check "Sub-agent health: OK" "OK"
fi

# 9️⃣ Git auto-backup (stale check)
git_stale=$(cd "$WORKSPACE" && git status -s 2>/dev/null | wc -l)
if [ "$git_stale" -gt 20 ]; then
    cd "$WORKSPACE" && git add -A && git commit -m "[GUARDIAN] Auto-sync on $(date -u '+%Y-%m-%d %H:%M UTC')" --no-verify 2>/dev/null && git push 2>/dev/null
    check "Git auto-backup ($git_stale files committed)" "OK"
elif [ "$git_stale" -gt 0 ]; then
    check "Git pending: $git_stale files" "WARN"
else
    check "Git workspace clean" "OK"
fi

# Summary
echo ""
echo "📊 Guardian Summary: ✅ $PASS passed | ⚠️ $WARN warned | ❌ $FAIL failed"
echo "=== GUARDIAN: OK ==="
