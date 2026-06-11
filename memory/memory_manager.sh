#!/bin/bash
# memory_manager.sh — Memory Consolidation Orchestrator
# Chains all memory tools into a single pipeline.
#
# Usage:
#   bash memory_manager.sh auto          # Full auto pipeline (consolidate + prune + index + digest)
#   bash memory_manager.sh daily         # Daily digest + consolidate
#   bash memory_manager.sh hourly        # Light cycle (index + prune)
#   bash memory_manager.sh session       # Session-end summary
#   bash memory_manager.sh status        # Show memory stats

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(dirname "$DIR")"
LOG="$DIR/memory_manager.log"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

# ── Helper: count files by extension ──
count_files() {
  local ext="$1"
  local dir="${2:-$DIR}"
  find "$dir" -maxdepth 1 -name "*.$ext" 2>/dev/null | wc -l
}

# ── Status report ──
status() {
  echo "📊 Memory System Status"
  echo "━━━━━━━━━━━━━━━━━━━━━"
  echo "📁 Daily logs:   $(count_files md "$DIR") files ($(du -sh "$DIR"/*.md 2>/dev/null | tail -1 | awk '{print $1}') total)"
  echo "📁 Memory index: $(wc -c < "$DIR/memory-index.json" 2>/dev/null || echo 0) bytes"
  echo "📁 Digests:      $(count_files md "$DIR/digests") digests"
  echo "📁 Research:     $(ls "$DIR/research/"*.md 2>/dev/null | wc -l) files"
  echo "📁 Knowledge:    $(ls "$WORKSPACE/knowledge/"*.json 2>/dev/null | wc -l) knowledge bases"
  echo ""
  echo "🧩 Tools available:"
  for tool in consolidator daily_digest memory_pruner memory_index; do
    if [ -f "$DIR/$tool.py" ]; then
      echo "  ✅ $tool.py"
    else
      echo "  ❌ $tool.py"
    fi
  done
}

# ── Hourly light cycle ──
hourly() {
  log "🔄 Hourly memory cycle starting..."
  
  if [ -f "$DIR/memory_pruner.py" ]; then
    python3 "$DIR/memory_pruner.py" --apply 2>&1 | tail -3 | while read line; do log "  $line"; done
  fi
  
  if [ -f "$DIR/memory_index.py" ]; then
    python3 "$DIR/memory_index.py" --rebuild 2>&1 | tail -2 | while read line; do log "  $line"; done
  fi
  
  log "✅ Hourly cycle complete"
}

# ── Daily digest + consolidate ──
daily() {
  log "📅 Daily memory cycle starting..."
  
  if [ -f "$DIR/consolidator.py" ]; then
    python3 "$DIR/consolidator.py" --apply 2>&1 | tail -5 | while read line; do log "  $line"; done
  fi
  
  if [ -f "$DIR/memory_pruner.py" ]; then
    python3 "$DIR/memory_pruner.py" --apply 2>&1 | tail -3 | while read line; do log "  $line"; done
  fi
  
  if [ -f "$DIR/memory_index.py" ]; then
    python3 "$DIR/memory_index.py" --rebuild 2>&1 | tail -2 | while read line; do log "  $line"; done
  fi
  
  if [ -f "$DIR/daily_digest.py" ]; then
    python3 "$DIR/daily_digest.py" 2>&1 | tail -5 | while read line; do log "  $line"; done
  fi
  
  # Git auto-commit memory changes
  if cd "$WORKSPACE" 2>/dev/null && git rev-parse --is-inside-work-tree 2>/dev/null; then
    git add "$DIR/"*.md "$DIR/digests/"*.md "$DIR/"*.json 2>/dev/null
    git commit -m "🧠 Memory auto-sync $(date '+%Y-%m-%d %H:%M')" 2>/dev/null && log "✅ Memory committed to git"
  fi
  
  log "✅ Daily cycle complete"
}

# ── Session-end summary ──
session() {
  log "📝 Session-end memory update..."
  
  if [ -f "$DIR/session_summary.py" ]; then
    python3 "$DIR/session_summary.py" 2>&1 | tail -10 | while read line; do log "  $line"; done
  fi
  
  # Git commit if dirty
  if cd "$WORKSPACE" 2>/dev/null && git rev-parse --is-inside-work-tree 2>/dev/null; then
    git add "$DIR/"*.md "$DIR/"*.json 2>/dev/null
    git commit -m "🧠 Session-end $(date '+%Y-%m-%d %H:%M')" 2>/dev/null && log "✅ Session memory committed"
  fi
  
  log "✅ Session-end complete"
}

# ── Full auto pipeline ──
auto() {
  log "🚀 Full auto memory pipeline starting..."
  daily
  log "🎉 Full pipeline complete"
}

# ── CLI ──
case "${1:-auto}" in
  auto|full)     auto ;;
  daily)         daily ;;
  hourly)        hourly ;;
  session)       session ;;
  status)        status ;;
  *)
    echo "Usage: $0 {auto|daily|hourly|session|status}"
    echo "  auto    — Full pipeline"
    echo "  daily   — Daily digest + consolidate + prune + index"
    echo "  hourly  — Light: index + prune"
    echo "  session — Session-end summary"
    echo "  status  — Show memory stats"
    exit 1
    ;;
esac
