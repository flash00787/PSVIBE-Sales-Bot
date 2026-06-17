#!/bin/bash
# Kora Workspace Auto-Backup to Google Drive
# Runs daily via cron
LOG="/var/log/kora_drive_backup.log"
DATE=$(date -u +%Y-%m-%d)
WORKSPACE="/root/.openclaw/workspace"
DRIVE_TOOL="$WORKSPACE/drive_tool.py"

echo "[$(date)] Starting Kora backup..." >> "$LOG"

# Create dated backup folder
FOLDER_ID=$(python3 "$DRIVE_TOOL" mkdir "Kora_Backup_$DATE" 2>&1 | grep "ID:" | awk '{print $2}')
if [ -z "$FOLDER_ID" ]; then
    echo "[$(date)] ❌ Failed to create folder" >> "$LOG"
    exit 1
fi
echo "[$(date)] Created folder: $FOLDER_ID" >> "$LOG"

# Create tarball
TARBALL="/tmp/kora_backup_$DATE.tar.gz"
cd "$WORKSPACE" && tar -czf "$TARBALL" *.md memory/*.md memory/*.json memory/sop/*.md 2>/dev/null

# Upload tarball
python3 "$DRIVE_TOOL" upload "$TARBALL" --folder-id "$FOLDER_ID" >> "$LOG" 2>&1

# Upload key individual files
for f in MEMORY.md SOUL.md AGENTS.md GOLDEN_RULES.md TOOLS.md HEARTBEAT.md IDENTITY.md USER.md; do
    python3 "$DRIVE_TOOL" upload "$WORKSPACE/$f" --folder-id "$FOLDER_ID" >> "$LOG" 2>&1
done

# Cleanup
rm -f "$TARBALL"

echo "[$(date)] ✅ Backup complete" >> "$LOG"
