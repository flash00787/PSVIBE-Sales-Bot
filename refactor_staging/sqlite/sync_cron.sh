#!/bin/bash
# ============================================================================
# PS VIBE SQLite Sync Cron Script
# Runs every 5 minutes from crontab to refresh SQLite from Google Sheets
# ============================================================================
# Crontab entry:
#   */5 * * * * /root/Sales-Tele-Bot_refactored/sqlite/sync_cron.sh >> /root/Sales-Tele-Bot_refactored/sqlite/sync.log 2>&1
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DB_PATH="${SQLITE_DB_PATH:-$PROJECT_DIR/psvibe.db}"
LOCK_FILE="/tmp/psvibe_sync.lock"
LOG_FILE="$SCRIPT_DIR/sync.log"

# Source .env if exists
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# ── Lock to prevent overlapping runs ─────────────────────────────────────────
exec 200>"$LOCK_FILE"
flock -n 200 || {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARN] Sync already running — skipping"
    exit 0
}

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$1] $2" | tee -a "$LOG_FILE"
}

log "INFO" "Sync started"

# ── Check prerequisites ──────────────────────────────────────────────────────
if [ ! -f "$DB_PATH" ]; then
    log "WARN" "Database not found at $DB_PATH — running initial setup"
    python3 "$SCRIPT_DIR/setup.py" --db "$DB_PATH"
    log "INFO" "Initial setup complete"
    exit 0
fi

# ── Run incremental sync ─────────────────────────────────────────────────────
cd "$SCRIPT_DIR"

# Quick sync: only refresh frequently-changed tables
python3 -c "
import os, sys, logging
sys.path.insert(0, '$SCRIPT_DIR')
from db_manager import PSVibeDB

logging.basicConfig(level=logging.INFO)
db = PSVibeDB('$DB_PATH')

# Only sync if we have Sheet access
sheet_id = os.environ.get('SHEET_ID')
sa_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'service_account.json')
if not sheet_id or not __import__('pathlib').Path(sa_path).exists():
    logging.info('No Sheets access — sync skipped')
    sys.exit(0)

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(sa_path, scope)
gc = gspread.authorize(creds)
wb = gc.open_by_key(sheet_id)

# 1. Sync bookings (most frequently changed)
try:
    bk_sh = wb.worksheet('Console_Booking')
    all_rows = bk_sh.get_all_values()
    conn = db._get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM bookings')
    for row in all_rows[1:]:
        if len(row) < 7 or not row[0].strip():
            continue
        cur.execute(
            'INSERT OR REPLACE INTO bookings (id, date, console_id, member_id, start_time, end_time, status, staff, notes) VALUES (?,?,?,?,?,?,?,?,?)',
            (row[0].strip(), row[1].strip() if len(row) > 1 else '',
             row[2].strip() if len(row) > 2 else '', row[3].strip() if len(row) > 3 else '',
             row[4].strip() if len(row) > 4 else '', row[5].strip() if len(row) > 5 else '',
             row[6].strip() if len(row) > 6 else 'Active',
             row[7].strip() if len(row) > 7 else '', row[8].strip() if len(row) > 8 else '')
        )
    count = cur.rowcount
    conn.commit()
    db.log_sync('bookings', 'sheets_to_sqlite', count)
    logging.info('Bookings synced: %d rows', count)
except Exception as e:
    logging.warning('Bookings sync failed: %s', e)

# 2. Sync members (less frequently — wallet mins change)
try:
    member_sh = wb.worksheet('Card_Wallet')
    all_rows = member_sh.get_all_values()
    conn = db._get_conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM members')
    for row in all_rows[1:]:
        if len(row) < 2 or not row[1].strip():
            continue
        cur.execute(
            '''INSERT OR REPLACE INTO members
               (id, name, phone, email, lifetime_spend, net_spend, wallet_mins,
                rank_tier, effective_rate, reg_staff, referral_code)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (
                row[1].strip(), row[2].strip() if len(row) > 2 else '',
                row[3].strip() if len(row) > 3 else '', row[12].strip() if len(row) > 12 else '',
                float(str(row[4]).replace(',','').strip()) if len(row) > 4 and row[4].strip() else 0,
                float(str(row[5]).replace(',','').strip()) if len(row) > 5 and row[5].strip() else 0,
                int(float(str(row[7]).replace(',','').strip())) if len(row) > 7 and row[7].strip().replace(',','').replace('-','').isdigit() else 0,
                row[6].strip() if len(row) > 6 else 'Warrior',
                float(row[11].strip()) if len(row) > 11 and row[11].strip() else 0,
                row[10].strip() if len(row) > 10 else '',
                row[16].strip() if len(row) > 16 else '',
            )
        )
    count = cur.rowcount
    conn.commit()
    db.log_sync('members', 'sheets_to_sqlite', count)
    logging.info('Members synced: %d rows', count)
except Exception as e:
    logging.warning('Members sync failed: %s', e)

db.close()
" 2>&1 | tee -a "$LOG_FILE"

log "INFO" "Sync complete"

# Release lock
flock -u 200
