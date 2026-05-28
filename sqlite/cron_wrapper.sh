#!/bin/bash
# Cron wrapper — sources .env before sync
cd /root/psvibe-sales-bot/sqlite
if [ -f /root/psvibe-sales-bot/.env ]; then
  export $(grep -v '^#' /root/psvibe-sales-bot/.env | grep -E 'SHEET_ID|GOOGLE_APPLICATION_CREDENTIALS' | xargs)
fi
[ -z "$GOOGLE_APPLICATION_CREDENTIALS" ] && export GOOGLE_APPLICATION_CREDENTIALS="/root/psvibe-sales-bot/service_account.json"
[ -z "$SQLITE_DB_PATH" ] && export SQLITE_DB_PATH="/root/psvibe-sales-bot/psvibe.db"
bash sync_cron.sh
