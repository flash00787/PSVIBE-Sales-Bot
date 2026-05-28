#!/usr/bin/env bash
# ─────────────────────────────────────────────────────
#  PS Vibe Bot — VPS update script
#  Usage:  bash update_bot.sh
#  Run from:  ~/Sales-Tele-Bot/
# ─────────────────────────────────────────────────────

set -e

SECRET="${BOT_UPDATE_SECRET:-psvibe2026}"
API="https://sales-tele-bot.replit.app/api/sync?secret=${SECRET}"
TARGET="main.py"
BACKUP="${TARGET}.bak.$(date +%s)"

echo "📥 Downloading latest main.py from Replit..."
HTTP_CODE=$(curl -s -o /tmp/main_new.py -w "%{http_code}" \
  -H "x-bot-secret: ${SECRET}" "${API}")

if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ Download failed (HTTP ${HTTP_CODE}). Deploy latest version on Replit first."
  exit 1
fi

LINES=$(wc -l < /tmp/main_new.py)
if [ "$LINES" -lt 50 ]; then
  echo "❌ Downloaded file too small (${LINES} lines). Aborting."
  exit 1
fi

echo "💾 Backup: ${BACKUP}"
cp "${TARGET}" "${BACKUP}"
cp /tmp/main_new.py "${TARGET}"
echo "✅ main.py updated (${LINES} lines)"

echo "🔄 Restarting bot..."
screen -S sales-bot -X stuff "^C" 2>/dev/null || true
sleep 2
screen -S sales-bot -X stuff "./start_bot.sh\n"
echo "✅ Bot restarted in screen session 'sales-bot'"
echo ""
echo "Check logs:  screen -r sales-bot"
