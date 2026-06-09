#!/bin/bash
# Smart Session Cleanup v2.1 — Robust (no sh-in-pipe bugs)
# Step 1: Delete files >1 day old
# Step 2: For session prefixes with >10 files, keep newest 10
# Step 3: Clean old large topic files (>7d, >500k)

SESSIONS_DIR="/home/node/.openclaw/agents/main/sessions"
DRY=false; [ "$1" = "--dry-run" ] && DRY=true

echo "=== Session Cleanup $(date -u +%H:%M) ==="

# Step 1: Bulk delete >1 day old files
old=$(find "$SESSIONS_DIR" -maxdepth 1 -name "*.jsonl" -mtime +1 2>/dev/null | wc -l)
if [ "$old" -gt 0 ]; then
    [ "$DRY" = false ] && find "$SESSIONS_DIR" -maxdepth 1 -name "*.jsonl" -mtime +1 -delete 2>/dev/null
    echo "  >1d deleted: $old"
fi

# Clean old checkpoints
ck=$(find "$SESSIONS_DIR" -maxdepth 1 -name "*.checkpoint.*.jsonl" -mtime +1 2>/dev/null | wc -l)
if [ "$ck" -gt 0 ]; then
    [ "$DRY" = false ] && find "$SESSIONS_DIR" -maxdepth 1 -name "*.checkpoint.*.jsonl" -mtime +1 -delete 2>/dev/null
    echo "  Checkpoints: $ck"
fi

# Step 2: Keep last 10 per session prefix
echo "  Sessions with >10 files:"

# Get prefixes with >10 files safely
ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null | \
  awk -F/ '{print $NF}' | \
  sed 's/\.jsonl$//' | \
  sed 's/-topic-[0-9]*$//' | \
  sed 's/\.checkpoint\..*//' | \
  sort | uniq -c | sort -rn | \
  awk '$1 > 10 {print $2, $1}' > /tmp/sess_cleanup_prefixes.tmp

while read -r prefix count; do
    [ -z "$prefix" ] && continue
    total_files=$(ls "$SESSIONS_DIR/${prefix}"*.jsonl 2>/dev/null | wc -l)
    excess=$((total_files - 10))
    if [ "$excess" -gt 0 ]; then
        [ "$DRY" = false ] && ls -t "$SESSIONS_DIR/${prefix}"*.jsonl 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null
        echo "    ${prefix}: ${total_files}->10"
    fi
done < /tmp/sess_cleanup_prefixes.tmp
rm -f /tmp/sess_cleanup_prefixes.tmp

# Final stats
remaining=$(find "$SESSIONS_DIR" -maxdepth 1 -name "*.jsonl" 2>/dev/null | wc -l)
size=$(du -sh "$SESSIONS_DIR" 2>/dev/null | cut -f1)
echo "  Remaining: $remaining files, $size"
[ "$DRY" = true ] && echo "  [DRY RUN]"

# Step 3: Clean old large topic session files (>7d old, >500k)
echo "  Old large sessions:"
# Use find directly instead of piping to while (avoids sh subshell bug)
find "$SESSIONS_DIR" -maxdepth 1 -name "*-topic-*.jsonl" -mtime +7 -size +500k 2>/dev/null > /tmp/sess_cleanup_large.tmp

if [ -s /tmp/sess_cleanup_large.tmp ]; then
    large_count=0
    while read -r f; do
        [ -z "$f" ] && continue
        [ "$DRY" = false ] && rm -f "$f"
        echo "    Deleted: $(basename "$f")"
        large_count=$((large_count + 1))
    done < /tmp/sess_cleanup_large.tmp
    echo "  Removed: $large_count bloat files"
else
    echo "    (none)"
fi
rm -f /tmp/sess_cleanup_large.tmp
