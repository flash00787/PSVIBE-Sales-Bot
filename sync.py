#!/usr/bin/env python3
"""
PS VIBE — Google Sheets → MySQL Sync Script
============================================
Reads data from the PS VIBE Google Sheets workbook and upserts into
the MySQL psvibe_api database.

Sheets → Tables:
  Card_Wallet   → member_wallets   (member info, balance, tier, rate, spend)
  Console_Booking + Setting → console_status (live console occupancy)
  Game_Library  → games_library    (game catalog, genre, disc count)
  Setting       → staff_records    (staff names & base salaries)

Usage:
  python3 sync.py                  # sync all tables
  python3 sync.py --full           # full re-sync
  python3 sync.py --table member_wallets  # sync only one table
  python3 sync.py --full --table console_status

Author: OpenClaw Agent
Version: 1.0.0
"""

import sys
import os
import logging
import argparse
from datetime import datetime, timezone, timedelta

# ── Third-party imports ─────────────────────────────────────────────
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pymysql
from dotenv import load_dotenv

# ── Configure logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("psvibe-sync")

# ── Paths ───────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
SA_KEY_PATH   = os.path.join(BASE_DIR, "kora_drive_sa.json")
ENV_PATH      = "/root/Aung Chan Myint/Sales-Tele-Bot_refactored/.env"

# ── Myanmar Timezone (GMT+6:30) ─────────────────────────────────────
MMT = timezone(timedelta(hours=6, minutes=30))


# ══════════════════════════════════════════════════════════════════════
#  Connections
# ══════════════════════════════════════════════════════════════════════

def connect_sheets():
    """Authorise gspread with the service account and open the workbook."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SA_KEY_PATH, scope)
    gc = gspread.authorize(creds)

    # Load SHEET_ID from .env (or fall back to known default)
    load_dotenv(ENV_PATH)
    sheet_id = os.environ.get("SHEET_ID", "1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA")
    wb = gc.open_by_key(sheet_id)
    log.info("Connected to Google Sheets workbook (id=%s)", sheet_id[:20] + "...")
    return wb


def connect_mysql():
    """Connect to the local MySQL psvibe_api database."""
    conn = pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ.get("MYSQL_USER", "psvibe_user"),
        password=os.environ.get("MYSQL_PASSWORD", "PsVibe@User2024!"),
        database=os.environ.get("MYSQL_DB", "psvibe_api"),
        charset="utf8mb4",
        autocommit=False,
    )
    log.info("Connected to MySQL psvibe_api")
    return conn


# ══════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════

def _safe_int(v, default=0):
    try:
        return int(float(str(v).replace(",", "").strip() or 0))
    except (ValueError, TypeError):
        return default


def _safe_float(v, default=0.0):
    try:
        return float(str(v).replace(",", "").strip() or 0)
    except (ValueError, TypeError):
        return default


def _safe_str(v, default=""):
    return str(v).strip() if v else default


def _now_sql():
    """Return current Myanmar time as a SQL DATETIME string."""
    return datetime.now(MMT).strftime("%Y-%m-%d %H:%M:%S")


def _today_sheet_fmt():
    """Return today's date in the sheet format, e.g. '5/27/2026'."""
    now = datetime.now(MMT)
    return "{m}/{d}/{y}".format(m=now.month, d=now.day, y=now.year)


def update_sync_status(conn, sheet_name, rows_synced, status="ok"):
    """Upsert a row into sync_status tracking table."""
    sql = """
        INSERT INTO sync_status (sheet_name, last_sync_at, rows_synced, status)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            last_sync_at = VALUES(last_sync_at),
            rows_synced  = VALUES(rows_synced),
            status       = VALUES(status)
    """
    with conn.cursor() as cur:
        cur.execute(sql, (sheet_name, _now_sql(), rows_synced, status))
    conn.commit()
    log.info("sync_status: %s -> %s (%d rows)", sheet_name, status, rows_synced)


# ══════════════════════════════════════════════════════════════════════
#  1. Card_Wallet -> member_wallets
# ══════════════════════════════════════════════════════════════════════
# Card_Wallet columns (0-indexed):
#   A=row_no  B=member_id  C=name     D=phone
#   E=lifetime_spend  F=ranking_net_spend  G=rank_tier  H=wallet_mins
#   I=?  J=?  K=reg_staff  L=effective_rate  M=email  N/O=reserved
#   P=birthday  Q=referral_code

def sync_member_wallets(wb, conn, full=False):
    """Sync Card_Wallet -> member_wallets (upsert on member_id)."""
    log.info("Syncing member_wallets...")
    try:
        sh = wb.worksheet("Card_Wallet")
    except gspread.WorksheetNotFound:
        log.error("Worksheet 'Card_Wallet' not found")
        update_sync_status(conn, "member_wallets", 0, "sheet_missing")
        return

    rows = sh.get_all_values()
    if len(rows) < 2:
        log.warning("Card_Wallet has no data rows")
        update_sync_status(conn, "member_wallets", 0, "empty")
        return

    sql = """
        INSERT INTO member_wallets
            (member_id, balance_mins, member_name, phone, effective_rate, tier, total_spend, last_updated)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            balance_mins   = VALUES(balance_mins),
            member_name    = VALUES(member_name),
            phone          = VALUES(phone),
            effective_rate = VALUES(effective_rate),
            tier           = VALUES(tier),
            total_spend    = VALUES(total_spend),
            last_updated   = VALUES(last_updated)
    """

    now = _now_sql()
    count = 0
    with conn.cursor() as cur:
        for row in rows[1:]:
            if not row or len(row) < 2:
                continue
            member_id = _safe_str(row[1])  # B
            if not member_id:
                continue

            name           = _safe_str(row[2])          # C
            phone          = _safe_str(row[3])          # D
            tier           = _safe_str(row[6])          # G
            balance_mins   = _safe_int(row[7])          # H
            effective_rate = _safe_float(row[11], 1.0)  # L
            total_spend    = _safe_float(row[5])        # F (ranking_net_spend)
            # Fall back to lifetime_spend (col E) if F is empty
            if total_spend == 0:
                total_spend = _safe_float(row[4])       # E

            # Clean member_id
            clean_mid = member_id.replace("MEM-", "").strip()

            cur.execute(sql, (
                clean_mid, balance_mins, name, phone, effective_rate,
                tier if tier else "Warrior", total_spend, now,
            ))
            count += 1

    conn.commit()
    log.info("member_wallets: %d rows upserted", count)
    update_sync_status(conn, "member_wallets", count, "ok")


# ══════════════════════════════════════════════════════════════════════
#  2. Console_Booking + Setting -> console_status
# ══════════════════════════════════════════════════════════════════════
# Setting columns (0-indexed): H=console_id (7), I=console_type (8), J=multiplier (9)
# Console_Booking columns (0-indexed):
#   A=booking_id  B=date  C=console_id  D=member_id
#   E=start_time  F=end_time  G=status  H=staff  I=notes

def sync_console_status(wb, conn, full=False):
    """Sync live console status from Setting (console IDs) + Console_Booking (active sessions)."""
    log.info("Syncing console_status...")

    # Step 1: Get all console IDs from Setting column H
    try:
        setting_sh = wb.worksheet("Setting")
        console_ids = [v.strip() for v in setting_sh.col_values(8)[1:] if v.strip()]
    except gspread.WorksheetNotFound:
        log.error("Worksheet 'Setting' not found")
        update_sync_status(conn, "console_status", 0, "sheet_missing")
        return

    if not console_ids:
        log.warning("No console IDs found in Setting column H")
        update_sync_status(conn, "console_status", 0, "empty")
        return

    # Step 2: Get today's active bookings from Console_Booking
    try:
        booking_sh = wb.worksheet("Console_Booking")
        booking_rows = booking_sh.get_all_values()
    except gspread.WorksheetNotFound:
        booking_rows = []

    today = _today_sheet_fmt()
    active_map = {}  # console_id -> {member, start_time, game}
    for row in booking_rows[1:]:
        if len(row) < 7:
            continue
        bk_date   = _safe_str(row[1])
        bk_cid    = _safe_str(row[2])
        bk_member = _safe_str(row[3])
        bk_start  = _safe_str(row[4])
        bk_status = _safe_str(row[6])
        bk_notes  = _safe_str(row[8]) if len(row) > 8 else ""

        if bk_date == today and bk_status in ("Active", "Scheduled"):
            active_map[bk_cid] = {
                "member": bk_member,
                "start":  bk_start,
                "game":   bk_notes,
            }

    # Step 3: Upsert into MySQL
    now = _now_sql()
    count = 0

    sql = """
        INSERT INTO console_status
            (console_id, status, current_game, current_member, start_time, last_updated)
        VALUES
            (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            status         = VALUES(status),
            current_game   = VALUES(current_game),
            current_member = VALUES(current_member),
            start_time     = VALUES(start_time),
            last_updated   = VALUES(last_updated)
    """

    with conn.cursor() as cur:
        for cid in console_ids:
            active = active_map.get(cid)
            if active:
                # Parse HH:MM start time into datetime
                start_dt = None
                if active["start"]:
                    try:
                        parts = active["start"].split(":")
                        h, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
                        start_dt = datetime.now(MMT).replace(
                            hour=h, minute=m, second=0, microsecond=0
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    except (ValueError, IndexError):
                        pass

                cur.execute(sql, (
                    cid, "Occupied",
                    active["game"] or None,
                    active["member"] or "Guest",
                    start_dt or now,
                    now,
                ))
            else:
                cur.execute(sql, (
                    cid, "Free", None, None, None, now,
                ))
            count += 1

    conn.commit()
    log.info("console_status: %d rows upserted", count)
    update_sync_status(conn, "console_status", count, "ok")


# ══════════════════════════════════════════════════════════════════════
#  3. Game_Library -> games_library
# ══════════════════════════════════════════════════════════════════════
# Game_Library columns (0-indexed):
#   A=No  B=Game Name  C=Final Status  D=Available Discs  E=In Use
#   F..T=console checkboxes  U=Installed_On (meta: "solo_multi|genre")

def sync_games_library(wb, conn, full=False):
    """Sync Game_Library -> games_library (upsert on game_title)."""
    log.info("Syncing games_library...")
    try:
        sh = wb.worksheet("Game_Library")
    except gspread.WorksheetNotFound:
        log.error("Worksheet 'Game_Library' not found")
        update_sync_status(conn, "games_library", 0, "sheet_missing")
        return

    rows = sh.get_all_values()
    if len(rows) < 2:
        log.warning("Game_Library has no data rows")
        update_sync_status(conn, "games_library", 0, "empty")
        return

    # Skip metadata/header rows
    SKIP_TITLES = {
        "from ( ssd )", "to ( console )", "game name",
        "samsung t - 7", "sandisk - 1", "sandisk - 2",
        "game data transfer record"
    }

    now = _now_sql()
    count = 0

    sql = """
        INSERT INTO games_library
            (game_title, genre, disc_count, last_updated)
        VALUES
            (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            genre        = VALUES(genre),
            disc_count   = VALUES(disc_count),
            last_updated = VALUES(last_updated)
    """

    with conn.cursor() as cur:
        for row in rows[1:]:
            if not row:
                continue
            title  = _safe_str(row[1]) if len(row) > 1 else ""   # column B
            row_no = _safe_str(row[0]) if len(row) > 0 else ""   # column A

            # Filter out header/metadata rows
            if not title:
                continue
            if row_no and not row_no.isdigit():
                continue
            if title.lower() in SKIP_TITLES:
                continue

            disc_count = _safe_int(row[3]) if len(row) > 3 else 0  # column D

            # Extract genre from column U (Installed_On meta)
            meta = _safe_str(row[20]) if len(row) > 20 else ""
            genre = ""
            if "|" in meta:
                parts = meta.split("|", 1)
                # First part = solo_multi, second = genre
                genre = parts[1].strip() if len(parts) > 1 else ""

            cur.execute(sql, (title, genre or None, disc_count, now))
            count += 1

    conn.commit()
    log.info("games_library: %d rows upserted", count)
    update_sync_status(conn, "games_library", count, "ok")


# ══════════════════════════════════════════════════════════════════════
#  4. Setting (Staff) -> staff_records
# ══════════════════════════════════════════════════════════════════════
# Setting columns (0-indexed): S=staff_name (18), T=base_salary (19)

def sync_staff_records(wb, conn, full=False):
    """Sync staff from Setting columns S:T -> staff_records (upsert on staff_name)."""
    log.info("Syncing staff_records...")
    try:
        sh = wb.worksheet("Setting")
    except gspread.WorksheetNotFound:
        log.error("Worksheet 'Setting' not found")
        update_sync_status(conn, "staff_records", 0, "sheet_missing")
        return

    # Read staff names (column S = col 19, 0-indexed: 18)
    names    = sh.col_values(19)[1:]   # skip header
    salaries = sh.col_values(20)[1:]   # column T = col 20

    now = _now_sql()
    count = 0

    sql_select = "SELECT staff_id FROM staff_records WHERE staff_name = %s"
    sql_insert = """
        INSERT INTO staff_records
            (staff_name, base_salary, role, is_active, last_updated)
        VALUES
            (%s, %s, %s, %s, %s)
    """
    sql_update = """
        UPDATE staff_records
        SET base_salary = %s, last_updated = %s, role = %s, is_active = %s
        WHERE staff_name = %s
    """

    with conn.cursor() as cur:
        for i, name in enumerate(names):
            name = name.strip()
            if not name:
                continue

            sal_str = salaries[i].strip() if i < len(salaries) else "0"
            # Parse salary: remove commas, check if numeric
            sal_clean = sal_str.replace(",", "")
            try:
                salary = float(sal_clean) if sal_clean else 0.0
            except ValueError:
                salary = 0.0

            # Check if exists
            cur.execute(sql_select, (name,))
            existing = cur.fetchone()
            if existing:
                cur.execute(sql_update, (salary, now, None, 1, name))
            else:
                cur.execute(sql_insert, (name, salary or 0.0, None, 1, now))
            count += 1

    conn.commit()
    log.info("staff_records: %d rows upserted", count)
    update_sync_status(conn, "staff_records", count, "ok")


# ══════════════════════════════════════════════════════════════════════
#  Main / CLI
# ══════════════════════════════════════════════════════════════════════

SYNC_TABLES = {
    "member_wallets": sync_member_wallets,
    "console_status": sync_console_status,
    "games_library":  sync_games_library,
    "staff_records":  sync_staff_records,
}


def main():
    parser = argparse.ArgumentParser(
        description="PS VIBE - Google Sheets to MySQL Sync"
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Full re-sync (syncs all rows, not just recent changes)"
    )
    parser.add_argument(
        "--table", type=str, metavar="TABLE_NAME",
        help="Sync only a single table: " + ", ".join(SYNC_TABLES.keys())
    )
    args = parser.parse_args()

    log.info("=" * 60)
    log.info("PS VIBE Sync - Starting (mode=%s)", "full" if args.full else "incremental")
    log.info("=" * 60)

    # Connect
    wb   = connect_sheets()
    conn = connect_mysql()

    exit_code = 0
    try:
        if args.table:
            # Sync single table
            table = args.table.lower()
            if table not in SYNC_TABLES:
                log.error("Unknown table '%s'. Valid: %s", table, ", ".join(SYNC_TABLES.keys()))
                sys.exit(2)
            SYNC_TABLES[table](wb, conn, full=args.full)
        else:
            # Sync all tables in order
            for name, sync_fn in SYNC_TABLES.items():
                try:
                    sync_fn(wb, conn, full=args.full)
                except Exception as e:
                    log.error("FAILED to sync %s: %s", name, e, exc_info=True)
                    update_sync_status(conn, name, 0, "error")
                    exit_code = 1

    finally:
        conn.close()
        log.info("MySQL connection closed.")

    log.info("=" * 60)
    log.info("Sync complete (exit=%d)", exit_code)
    log.info("=" * 60)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
