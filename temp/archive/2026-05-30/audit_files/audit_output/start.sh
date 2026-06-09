#!/bin/bash
export NODE_ENV=production
export PORT=8080
export SPREADSHEET_ID=1KQJts74A-uxoyBPXA2bCazNc5j4bIphgSCB9ooKF86I
export GOOGLE_APPLICATION_CREDENTIALS=/opt/agri-bot/.google-sa.json
# TELEGRAM_BOT_TOKEN and SESSION_SECRET are injected into .secrets file at deploy
set -a; source /opt/agri-bot/.secrets; set +a
exec node /opt/agri-bot/dist/index.mjs
