#!/bin/bash
# Cleanup orphaned OpenClaw gateway processes
# Run: bash /root/.openclaw/workspace/cleanup_orphaned_gateway.sh

CURRENT_GATEWAY=$(systemctl --user show openclaw-gateway.service -p MainPID 2>/dev/null | cut -d= -f2)
echo "Current gateway PID: ${CURRENT_GATEWAY:-unknown}"

# Find orphaned tini + openclaw processes (user 1000, running 1+ hour, not in current control group)
ORPHANS=$(ps -eo pid,uid,etime,args | awk '$2==1000 && /tini.*gateway/ && $3 ~ /-/ {print $1}')
ORPHANS_NODE=$(ps -eo pid,uid,etime,args | awk '$2==1000 && /openclaw$/ && $3 ~ /-/ {print $1}')

ALL_ORPHANS="$ORPHANS $ORPHANS_NODE"
ALL_ORPHANS=$(echo $ALL_ORPHANS | xargs)

if [ -z "$ALL_ORPHANS" ]; then
    echo "No orphaned processes found."
    exit 0
fi

echo "Found orphaned PIDs: $ALL_ORPHANS"
for pid in $ALL_ORPHANS; do
    if [ "$pid" != "$CURRENT_GATEWAY" ] && [ "$pid" != "" ]; then
        echo "Killing orphan PID $pid..."
        kill -9 $pid 2>/dev/null
    fi
done
echo "Cleanup complete."
