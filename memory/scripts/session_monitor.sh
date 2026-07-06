#!/bin/bash
SESSIONS_DIR="/root/.openclaw/agents/main/sessions"
MAX_BYTES=$((500 * 1024 * 1024))
WARN_THRESHOLD=80

USED_BYTES=$(du -sb "$SESSIONS_DIR" 2>/dev/null | awk '{print $1}')
if [ -z "$USED_BYTES" ] || [ "$USED_BYTES" -eq 0 ]; then
  exit 0
fi

PCT=$((USED_BYTES * 100 / MAX_BYTES))

if [ "$PCT" -ge "$WARN_THRESHOLD" ]; then
  echo "⚠️ SESSION_WARN: ${PCT}% used ($((USED_BYTES/1024/1024))MB/$((MAX_BYTES/1024/1024))MB)"
  echo "ACTION: Clean old sessions or increase session.maintenance.maxDiskBytes"
else
  echo "SESSION_OK: ${PCT}% used ($((USED_BYTES/1024/1024))MB/$((MAX_BYTES/1024/1024))MB)"
fi
