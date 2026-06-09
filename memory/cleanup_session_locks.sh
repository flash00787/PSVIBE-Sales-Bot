#!/bin/bash
# Clean stale OpenClaw session lock files to prevent deadlocks
# 
# Heuristic: Remove lock files whose maxHoldMs (17 min) has elapsed
# AND the lock file holder (gateway PID) is still alive = deadlock scenario
#
# Run from heartbeat or cron every 5 minutes

LOCK_DIR="/home/node/.openclaw/agents/main/sessions"
CLEANED=0
ERRORS=0
NOW_EPOCH=$(date +%s)

for lockfile in "$LOCK_DIR"/*.jsonl.lock; do
    [ -f "$lockfile" ] || continue
    
    # Read lock metadata
    LOCK_DATA=$(cat "$lockfile" 2>/dev/null)
    LOCK_PID=$(echo "$LOCK_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin)['pid'])" 2>/dev/null)
    CREATED_AT=$(echo "$LOCK_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin)['createdAt'])" 2>/dev/null)
    MAX_HOLD=$(echo "$LOCK_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin)['maxHoldMs'])" 2>/dev/null)
    
    [ -z "$LOCK_PID" ] && continue
    [ -z "$CREATED_AT" ] && continue
    [ -z "$MAX_HOLD" ] && MAX_HOLD=1020000  # default 17 min
    
    # Calculate lock age in seconds
    CREATED_EPOCH=$(date -d"${CREATED_AT%Z}+00:00" +%s 2>/dev/null || date -d"${CREATED_AT}" +%s 2>/dev/null)
    [ -z "$CREATED_EPOCH" ] && continue
    
    LOCK_AGE=$(( NOW_EPOCH - CREATED_EPOCH ))
    MAX_HOLD_SEC=$((MAX_HOLD / 1000))
    
    # Check if PID is alive
    if kill -0 "$LOCK_PID" 2>/dev/null; then
        # PID alive - only clean if lock is older than maxHoldMs (truly stale)
        if [ "$LOCK_AGE" -gt "$MAX_HOLD_SEC" ]; then
            echo "STALE: $lockfile (PID=$LOCK_PID ALIVE, age=${LOCK_AGE}s > maxHold=${MAX_HOLD_SEC}s)"
            rm -f "$lockfile" 2>/dev/null && CLEANED=$((CLEANED+1)) || ERRORS=$((ERRORS+1))
        fi
    else
        # PID dead - always clean
        echo "DEAD-PID: $lockfile (PID=$LOCK_PID DEAD, age=${LOCK_AGE}s)"
        rm -f "$lockfile" 2>/dev/null && CLEANED=$((CLEANED+1)) || ERRORS=$((ERRORS+1))
    fi
done

echo "LOCK_CLEANUP: cleaned=$CLEANED errors=$ERRORS"
exit 0
