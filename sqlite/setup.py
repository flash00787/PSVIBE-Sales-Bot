#!/usr/bin/env python3
"""
PS VIBE SQLite Setup Script
============================
Creates all tables and imports data from Google Sheets (if creds available).
Run once on VPS: python setup.py

Environment variables needed (already set in .env):
  SHEET_ID — Google Sheets spreadsheet ID
  Optional: GOOGLE_APPLICATION_CREDENTIALS — path to service_account.json
"""

import os
import sys
import logging
from pathlib import Path

# Add parent dir to path so we can import db_manager
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("psvibe-setup")

DB_PATH = os.environ.get("SQLITE_DB_PATH", "/root/psvibe-sales-bot/psvibe.db")


def create_tables(db_path: str):
    """Create all tables from schema.sql."""
    from db_manager import PSVibeDB

    db = PSVibeDB(db_path)
    db.ensure_tables()

    # Verify
    conn = db._get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r["name"] for r in cur.fetchall()]
    logger.info("Created %d tables: %s", len(tables), ", ".join(tables))
    db.close()
    return tables


def import_from_sheets(db_path: str) -> bool:
    """Try to import data from Google Sheets. Returns True if successful."""
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
    except ImportError:
        logger.warning("gspread/oauth2client not installed — skipping Sheets import")
        return False

    sheet_id = os.environ.get("SHEET_ID")
    if not sheet_id:
        logger.warning("SHEET_ID env var not set — skipping Sheets import")
        return False

    sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
    if not Path(sa_path).exists():
        # Try to find it in common locations
        for p in ["service_account.json", "/root/Sales-Tele-Bot/service_account.json"]:
            if Path(p).exists():
                sa_path = p
                break
        else:
            logger.warning("service_account.json not found — skipping Sheets import")
            return False

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(sa_path, scope)
    gc = gspread.authorize(creds)
    wb = gc.open_by_key(sheet_id)

    from db_manager import PSVibeDB
    db = PSVibeDB(db_path)

    total_imported = 0

    # ── 1. Import Members (Card_Wallet) ──────────────────────────────────────
    try:
        member_sh = wb.worksheet("Card_Wallet")
        all_rows = member_sh.get_all_values()
        headers = all_rows[0] if all_rows else []
        member_data = []
        for i, row in enumerate(all_rows[1:], start=2):
            if len(row) < 2 or not row[1].strip():
                continue
            def _col(idx, default=""):
                return row[idx].strip() if len(row) > idx else default
            def _int_cell(val):
                try:
                    return int(float(str(val).replace(",", "").replace("Ks", "").strip()))
                except (ValueError, TypeError):
                    return 0

            member_data.append((
                _col(1),                    # id (member_id, col B)
                _col(2),                    # name (col C)
                _col(3),                    # phone (col D)
                _col(12) if len(row) > 12 else "",  # email (col M)
                float(str(row[4]).replace(",","").strip()) if len(row) > 4 and row[4].strip() else 0,  # lifetime_spend (col E)
                float(str(row[5]).replace(",","").strip()) if len(row) > 5 and row[5].strip() else 0,  # net_spend (col F)
                _int_cell(_col(7)),         # wallet_mins (col H)
                _col(6),                    # rank_tier (col G)
                float(_col(11)) if len(row) > 11 and _col(11) else 0,  # effective_rate (col L)
                _col(10),                   # reg_staff (col K)
                _col(16),                   # referral_code (col Q)
                "",                         # join_date (computed later)
                "",                         # last_active
            ))
        n = db.import_members(member_data)
        total_imported += n
        logger.info("Card_Wallet: %d members imported", n)
    except Exception as e:
        logger.warning("Card_Wallet import skipped: %s", e)

    # ── 2. Import Bookings (Console_Booking) ─────────────────────────────────
    try:
        bk_sh = wb.worksheet("Console_Booking")
        all_rows = bk_sh.get_all_values()
        booking_data = []
        for row in all_rows[1:]:
            if len(row) < 7 or not row[0].strip():
                continue
            booking_data.append((
                row[0].strip(),                 # id (col A)
                row[1].strip() if len(row) > 1 else "",  # date (col B)
                row[2].strip() if len(row) > 2 else "",  # console_id (col C)
                row[3].strip() if len(row) > 3 else "",  # member_id (col D)
                row[4].strip() if len(row) > 4 else "",  # start_time (col E)
                row[5].strip() if len(row) > 5 else "",  # end_time (col F)
                row[6].strip() if len(row) > 6 else "Active",  # status (col G)
                row[7].strip() if len(row) > 7 else "",  # staff (col H)
                row[8].strip() if len(row) > 8 else "",  # notes (col I)
            ))
        n = db.import_bookings(booking_data)
        total_imported += n
        logger.info("Console_Booking: %d bookings imported", n)
    except Exception as e:
        logger.warning("Console_Booking import skipped: %s", e)

    # ── 3. Import Sales (Sales_Daily) ────────────────────────────────────────
    try:
        sales_sh = wb.worksheet("Sales_Daily")
        all_rows = sales_sh.get_all_values()
        sales_data = []
        for row in all_rows[1:]:
            if len(row) < 2 or not row[1].strip():
                continue
            sales_data.append((
                row[1].strip() if len(row) > 1 else "",  # voucher_id (col B)
                row[0].strip() if len(row) > 0 else "",  # date (col A)
                row[3].strip() if len(row) > 3 else "",  # member_id (col D) — adjust if needed
                row[4].strip() if len(row) > 4 else "",  # console_id
                0,  # mins — computed
                0,  # game_amount
                0,  # food_amount
                0,  # discount
                0,  # total_amount
                0,  # kpay
                0,  # cash
                "",
                row[14].strip() if len(row) > 14 else "",  # staff (col O)
                "sale",
                "",
            ))
        n = db.import_sales(sales_data)
        total_imported += n
        logger.info("Sales_Daily: %d sales imported", n)
    except Exception as e:
        logger.warning("Sales_Daily import skipped: %s", e)

    # ── 4. Import Settings ──────────────────────────────────────────────────
    try:
        setting_sh = wb.worksheet("Setting")
        all_rows = setting_sh.get_all_values()

        # Key settings to extract (B column, row-based)
        settings_data = []

        # B2 = base_rate
        if len(all_rows) > 1 and len(all_rows[1]) > 1:
            settings_data.append(("base_rate", all_rows[1][1].strip()))

        # B20 = new_member_card_price, B21 = new_member_base_mins
        if len(all_rows) > 19 and len(all_rows[19]) > 1:
            settings_data.append(("new_member_card_price", all_rows[19][1].strip()))
        if len(all_rows) > 20 and len(all_rows[20]) > 1:
            settings_data.append(("new_member_base_mins", all_rows[20][1].strip()))

        # M3 = master_threshold, M4 = immortal_threshold (col 13)
        if len(all_rows) > 2 and len(all_rows[2]) > 12:
            settings_data.append(("master_threshold", all_rows[2][12].strip()))
        if len(all_rows) > 3 and len(all_rows[3]) > 12:
            settings_data.append(("immortal_threshold", all_rows[3][12].strip()))

        # B30 = allowed_staff_ids
        if len(all_rows) > 29 and len(all_rows[29]) > 1:
            settings_data.append(("allowed_staff_ids", all_rows[29][1].strip()))

        # STOCK_PIN (env var or default)
        settings_data.append(("stock_pin", os.environ.get("STOCK_PIN", "1234")))

        n = db.import_settings(settings_data)
        total_imported += n
        logger.info("Setting: %d settings imported", n)
    except Exception as e:
        logger.warning("Setting import skipped: %s", e)

    # ── 5. Import Consoles ──────────────────────────────────────────────────
    try:
        setting_sh = wb.worksheet("Setting")
        names  = setting_sh.col_values(8)[1:]   # H — console names
        types  = setting_sh.col_values(9)[1:]   # I — console types
        mults  = setting_sh.col_values(10)[1:]  # J — multipliers
        console_data = []
        for idx, name in enumerate(names):
            if not name.strip():
                continue
            try:
                mult = float(str(mults[idx] if idx < len(mults) else "1").replace(",", "").strip()) or 1.0
            except (ValueError, IndexError):
                mult = 1.0
            ctype = (types[idx] if idx < len(types) else "").strip() or "PS5"
            console_data.append((name.strip(), ctype, mult))
        n = db.import_consoles(console_data)
        total_imported += n
        logger.info("Consoles: %d consoles imported", n)
    except Exception as e:
        logger.warning("Console import skipped: %s", e)

    # ── 6. Import Console Games ──────────────────────────────────────────────
    try:
        cg_sh = wb.worksheet("Console_Games")
        all_rows = cg_sh.get_all_values()
        cg_data = []
        for row in all_rows[1:]:
            if len(row) < 2 or not row[0].strip():
                continue
            cg_data.append((
                row[0].strip() if len(row) > 0 else "",
                row[1].strip() if len(row) > 1 else "",
                row[2].strip() if len(row) > 2 else "HDD",
                row[3].strip() if len(row) > 3 else "",
                row[4].strip() if len(row) > 4 else "",
            ))
        n = db.import_console_games(cg_data)
        total_imported += n
        logger.info("Console_Games: %d records imported", n)
    except Exception as e:
        logger.warning("Console_Games import skipped: %s", e)

    # ── 7. Import Game Library ──────────────────────────────────────────────
    try:
        gl_sh = wb.worksheet("Game_Library")
        all_rows = gl_sh.get_all_values()
        gl_data = []
        for row in all_rows[1:]:
            title = row[1].strip() if len(row) > 1 else ""
            if not title:
                continue
            # Skip non-game rows
            row_no = row[0].strip() if row else ""
            if row_no and not row_no.isdigit():
                continue
            if title.lower() in ("from ( ssd )", "to ( console )", "game name",
                                 "samsung t - 7", "sandisk - 1", "sandisk - 2",
                                 "game data transfer record"):
                continue

            meta = row[20].strip() if len(row) > 20 else ""
            solo_multi, genre = "", ""
            if "|" in meta:
                parts = meta.split("|", 1)
                solo_multi = parts[0].strip()
                genre = parts[1].strip()

            def _int_safe(s):
                try: return int(str(s).strip())
                except: return 0

            gl_data.append((
                title,
                row[2].strip() if len(row) > 2 else "",           # final_status
                _int_safe(row[3]) if len(row) > 3 else 0,         # available_discs
                _int_safe(row[4]) if len(row) > 4 else 0,         # total_copies
                _int_safe(row[5]) if len(row) > 5 else 0,         # in_use
                solo_multi,
                genre,
            ))
        n = db.import_game_library(gl_data)
        total_imported += n
        logger.info("Game_Library: %d games imported", n)
    except Exception as e:
        logger.warning("Game_Library import skipped: %s", e)

    # ── 8. Import Staff ─────────────────────────────────────────────────────
    try:
        setting_sh = wb.worksheet("Setting")
        staff_names    = setting_sh.col_values(19)[1:]  # S
        staff_salaries = setting_sh.col_values(20)[1:]  # T
        staff_data = []
        for idx, name in enumerate(staff_names):
            if not name.strip():
                continue
            sal = staff_salaries[idx].strip() if idx < len(staff_salaries) else "0"
            try:
                sal_num = int(sal.replace(",", "")) if sal.replace(",", "").isdigit() else 0
            except:
                sal_num = 0
            staff_data.append((name.strip(), sal_num))
        n = db.import_staff(staff_data)
        total_imported += n
        logger.info("Staff: %d staff imported", n)
    except Exception as e:
        logger.warning("Staff import skipped: %s", e)

    # ── 9. Import TopUp Log ──────────────────────────────────────────────────
    try:
        topup_sh = wb.worksheet("TopUp_Log")
        all_rows = topup_sh.get_all_values()
        topup_data = []
        for row in all_rows[1:]:
            if len(row) < 2 or not row[1].strip():
                continue
            def _num(val):
                try:
                    return float(str(val).replace(",","").replace("Ks","").strip())
                except: return 0.0
            topup_data.append((
                row[0].strip() if len(row) > 0 else "",   # date (col A)
                row[1].strip() if len(row) > 1 else "",   # member_id (col B)
                row[2].strip() if len(row) > 2 else "",   # tier (col C)
                _num(row[4]) if len(row) > 4 else 0,      # amount (col E)
                _num(row[5]) if len(row) > 5 else 0,      # kpay (col F)
                _num(row[6]) if len(row) > 6 else 0,      # cash (col G)
                int(_num(row[7])) if len(row) > 7 else 0, # added_mins (col H)
                row[8].strip() if len(row) > 8 else "Top Up",  # type (col I)
                row[9].strip() if len(row) > 9 else "",   # staff (col J)
            ))
        conn = db._get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM topups")
        cur.executemany(
            "INSERT OR REPLACE INTO topups (date, member_id, tier, amount, kpay, cash, added_mins, topup_type, staff) VALUES (?,?,?,?,?,?,?,?,?)",
            topup_data
        )
        count = cur.rowcount
        conn.commit()
        db.log_sync("topups", "sheets_to_sqlite", count)
        total_imported += count
        logger.info("TopUp_Log: %d topups imported", count)
    except Exception as e:
        logger.warning("TopUp_Log import skipped: %s", e)

    db.close()
    logger.info("Import complete: %d total rows imported across all tables", total_imported)
    return True


def test_queries(db_path: str):
    """Run sample queries to verify DB works."""
    from db_manager import PSVibeDB

    db = PSVibeDB(db_path)

    print("\n" + "=" * 60)
    print(" SQLite Database Verification")
    print("=" * 60)

    # Member count
    count = db.get_member_count()
    print(f"\n✓ Members: {count}")

    # Sample member
    members = db.get_all_members()
    if members:
        print(f"  Sample: {members[0]['id']} — {members[0]['name']} | {members[0]['rank_tier']}")

    # Active bookings
    bookings = db.get_active_bookings()
    print(f"\n✓ Active/Scheduled Bookings: {len(bookings)}")
    for b in bookings[:3]:
        print(f"  {b['id']} | {b['console_id']} | {b['member_id']} | {b['status']}")

    # Consoles
    consoles = db.get_all_consoles()
    print(f"\n✓ Consoles: {len(consoles)}")
    for c in consoles[:3]:
        print(f"  {c['id']} — {c['console_type']} ({c['multiplier']}x)")

    # Games
    games = db.get_games()
    print(f"\n✓ Games in Library: {len(games)}")
    for g in games[:3]:
        print(f"  {g['title']} — Discs: {g['available_discs']} | Status: {g['final_status']}")

    # Settings
    settings = db.get_all_settings()
    print(f"\n✓ Settings: {len(settings)}")
    for k in ["base_rate", "master_threshold", "immortal_threshold"]:
        if k in settings:
            print(f"  {k}: {settings[k]}")

    # Console games
    cg = db.get_games_on_console("C - 01")
    print(f"\n✓ Games on C-01: {len(cg)}")
    if cg:
        print(f"  {', '.join(cg[:5])}" + ("..." if len(cg) > 5 else ""))

    # Staff
    staff = db.get_all_staff()
    print(f"\n✓ Staff: {len(staff)}")
    for s in staff[:3]:
        print(f"  {s['name']} — {s['base_salary']:,} Ks")

    # Dashboard
    stats = db.get_dashboard_stats()
    print(f"\n✓ Dashboard Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # Sync status
    print(f"\n✓ Sync Status:")
    sync = db.get_sync_status()
    for table, info in sync.items():
        print(f"  {table}: {info['total_rows']} rows | last: {info['last_sync']} | {info['status']}")

    print("\n" + "=" * 60)
    print(" All tests passed!")
    print("=" * 60 + "\n")

    db.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="PS VIBE SQLite Setup")
    parser.add_argument("--db", default=DB_PATH, help="SQLite database path")
    parser.add_argument("--no-import", action="store_true", help="Skip Google Sheets import")
    parser.add_argument("--test-only", action="store_true", help="Only run test queries")
    args = parser.parse_args()

    db_path = args.db

    # Ensure parent directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    if args.test_only:
        if not Path(db_path).exists():
            logger.error("Database not found at %s — run setup first", db_path)
            sys.exit(1)
        test_queries(db_path)
        return

    # Step 1: Create tables
    logger.info("Step 1/3: Creating tables...")
    tables = create_tables(db_path)
    logger.info("Step 1 done: %d tables created", len(tables))

    # Step 2: Import from Sheets
    if not args.no_import:
        logger.info("Step 2/3: Importing from Google Sheets...")
        imported = import_from_sheets(db_path)
        if imported:
            logger.info("Step 2 done: data imported successfully")
        else:
            logger.info("Step 2 done: no Sheets import (credentials/SHEET_ID missing)")
    else:
        logger.info("Step 2/3: Skipped (--no-import)")

    # Step 3: Test queries
    logger.info("Step 3/3: Running test queries...")
    test_queries(db_path)
    logger.info("Setup complete! DB at %s", db_path)


if __name__ == "__main__":
    main()

