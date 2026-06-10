#!/bin/bash
# Bulk Session Cleanup — Aggressive mode for 446MB/500MB situation
SESSIONS_DIR="/home/node/.openclaw/agents/main/sessions"
TARGET_FREE_MB=150  # Free up 150MB
DRY=false; [ "$1" = "--dry-run" ] && DRY=true

echo "=== Bulk Session Cleanup $(date -u +%H:%M) ==="
echo "Before: $(du -sh $SESSIONS_DIR | cut -f1)"

# Step 1: Delete trajectory files > 6h old (these are debug logs, bulk of size)
old_traj=$(find "$SESSIONS_DIR" -maxdepth 1 -name "*.trajectory.jsonl" -mmin +360 2>/dev/null | wc -l)
if [ "$old_traj" -gt 0 ]; then
    traj_size=$(find "$SESSIONS_DIR" -maxdepth 1 -name "*.trajectory.jsonl" -mmin +360 -printf '%s\n' 2>/dev/null | awk '{s+=$1} END {print s}')
    traj_size_mb=$((traj_size / 1048576))
    [ "$DRY" = false ] && find "$SESSIONS_DIR" -maxdepth 1 -name "*.trajectory.jsonl" -mmin +360 -delete 2>/dev/null
    echo "  >6h trajectory: $old_traj files, ~${traj_size_mb}MB deleted"
fi

# Step 2: Delete session files > 2 days old
old_sess=$(find "$SESSIONS_DIR" -maxdepth 1 -name "*.jsonl" -mtime +2 2>/dev/null | wc -l)
if [ "$old_sess" -gt 0 ]; then
    [ "$DRY" = false ] && find "$SESSIONS_DIR" -maxdepth 1 -name "*.jsonl" -mtime +2 -delete 2>/dev/null
    echo "  >2d session: $old_sess files deleted"
fi

# Step 3: For remaining sessions, keep last 5 per prefix (aggressive)
ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null | \
  awk -F/ '{print $NF}' | \
  sed 's/\.jsonl$//' | \
  sed 's/-topic-[0-9]*$//' | \
  sort | uniq -c | sort -rn | \
  awk '$1 > 5 {print $2, $1}' > /tmp/bulk_sess.tmp

while read -r prefix count; do
    [ -z "$prefix" ] && continue
    total=$(ls "$SESSIONS_DIR/${prefix}"*.jsonl 2>/dev/null | wc -l)
    excess=$((total - 5))
    if [ "$excess" -gt 0 ]; then
        [ "$DRY" = false ] && ls -t "$SESSIONS_DIR/${prefix}"*.jsonl 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null
        echo "    ${prefix}: ${total}->5"
    fi
done < /tmp/bulk_sess.tmp
rm -f /tmp/bulk_sess.tmp

echo "After: $(du -sh $SESSIONS_DIR | cut -f1)"
