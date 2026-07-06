#!/bin/bash
# Auto-cleanup sessions when >80% limit reached
SESSIONS_DIR="/root/.openclaw/agents/main/sessions"
MAX_BYTES=$((500 * 1024 * 1024))
WARN_THRESHOLD=80
CLEAN_THRESHOLD=85

USED=$(du -sb "$SESSIONS_DIR" 2>/dev/null | awk '{print $1}')
if [ -z "$USED" ] || [ "$USED" -eq 0 ]; then exit 0; fi

PCT=$((USED * 100 / MAX_BYTES))

if [ "$PCT" -ge "$CLEAN_THRESHOLD" ]; then
  echo "CLEANING: ${PCT}% used — removing trajectories >24h"
  find "$SESSIONS_DIR" -name "*.trajectory.jsonl" -mtime +1 -delete 2>/dev/null
  find "$SESSIONS_DIR" -name "*.jsonl" -mtime +1 ! -name "*.trajectory*" -delete 2>/dev/null
  echo "CLEAN_DONE"
elif [ "$PCT" -ge "$WARN_THRESHOLD" ]; then
  echo "WARN_ONLY: ${PCT}% used — no cleanup needed yet"
else
  echo "OK: ${PCT}% used"
fi
