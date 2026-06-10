#!/bin/bash
# Resolve active alerts in /root/coordination/findings/
ARCHIVE_DIR="/root/coordination/findings/archive/resolved_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ARCHIVE_DIR"

cd /root/coordination/findings/

for f in \
  service_alert.json \
  arch_data.json \
  cron_health.json \
  v_fix-pending-bookings.json \
  latest_scan_summary.json \
  ; do
  if [ -f "$f" ]; then
    mv "$f" "$ARCHIVE_DIR/"
    echo "Resolved: $f"
  fi
done

# Wildcard files
for f in weekly_import_scan_*.json fix_pending_bookings_*.json; do
  if [ -f "$f" ]; then
    mv "$f" "$ARCHIVE_DIR/"
    echo "Resolved: $f"
  fi
done

echo "Archive created: $ARCHIVE_DIR"
ls -la "$ARCHIVE_DIR/"
