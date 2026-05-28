#!/usr/bin/env python3
"""
PS VIBE SQLite Database Manager
================================
Local read-mirror of Google Sheets data.
Provides fast cached access for 10 concurrent users without hitting Sheets API.
"""

import os
import sqlite3
import logging
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# Myanmar Timezone (GMT+6:30)
MMT = timezone(timedelta(hours=6, minutes=30))

logger = logging.getLogger(__name__)


class PSVibeDB:
    """
    SQLite read-mirror for PS VIBE Google Sheets data.

    Usage:
        db = PSVibeDB("/root/Sales-Tele-Bot_refactored/psvibe.db")
        member = db.get_member("PSV_A_001")
        bookings = db.get_active_bookings()
        db.close()
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()
        self._lock = threading.Lock()

    # ── Connection Management ────────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        """Get a thread-local connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=5000")
            self._local.conn = conn
        return self._local.conn

    def _cursor(self):
        return self._get_conn().cursor()

    def close(self):
        """Close all thread-local connections."""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None

    # ── Schema Setup ─────────────────────────────────────────────────────────

    def ensure_tables(self):
        """Create all tables from schema.sql if they don't exist."""
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            sql = schema_path.read_text(encoding="utf-8")
            conn = self._get_conn()
            conn.executescript(sql)
            conn.commit()
            logger.info("Schema tables ensured")
        else:
            logger.error("schema.sql not found at %s", schema_path)

    # ── Member Access ────────────────────────────────────────────────────────

    def get_member(self, member_id: str) -> Optional[dict]:
        """Get a single member by ID."""
        cur = self._cursor()
        cur.execute(
            "SELECT * FROM members WHERE id = ?",
            (member_id.strip(),)
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def search_member(self, query: str) -> list[dict]:
        """Search members by ID, name, or phone (LIKE match)."""
        q = f"%{query.strip()}%"
        cur = self._cursor()
        cur.execute(
            """SELECT * FROM members
               WHERE id LIKE ? OR name LIKE ? OR phone LIKE ?
               ORDER BY name LIMIT 20""",
            (q, q, q)
        )
        return [dict(r) for r in cur.fetchall()]

    def get_all_members(self) -> list[dict]:
        """Return all members as list of dicts (for caching)."""
        cur = self._cursor()
        cur.execute("SELECT * FROM members ORDER BY name")
        return [dict(r) for r in cur.fetchall()]

    def get_members_by_rank(self, rank: str) -> list[dict]:
        """Get all members of a specific rank tier."""
        cur = self._cursor()
        cur.execute("SELECT * FROM members WHERE rank_tier = ? ORDER BY name", (rank,))
        return [dict(r) for r in cur.fetchall()]

    def get_member_count(self) -> int:
        cur = self._cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM members")
        return cur.fetchone()["cnt"]

    # ── Booking Access ───────────────────────────────────────────────────────

    def get_booking(self, booking_id: str) -> Optional[dict]:
        cur = self._cursor()
        cur.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_active_bookings(self, date: str = None) -> list[dict]:
        """Get all Active/Scheduled bookings, optionally filtered by date."""
        if date:
            cur = self._cursor()
            cur.execute(
                "SELECT * FROM bookings WHERE status IN ('Active','Scheduled') AND date = ? ORDER BY start_time",
                (date,)
            )
        else:
            cur = self._cursor()
            cur.execute(
                "SELECT * FROM bookings WHERE status IN ('Active','Scheduled') ORDER BY date, start_time"
            )
        return [dict(r) for r in cur.fetchall()]

    def get_booking_for_console(self, console_id: str, date: str = None) -> Optional[dict]:
        """Get active booking on a specific console."""
        if date:
            cur = self._cursor()
            cur.execute(
                """SELECT * FROM bookings
                   WHERE console_id = ? AND status = 'Active'
                   AND date = ? LIMIT 1""",
                (console_id, date)
            )
        else:
            cur = self._cursor()
            cur.execute(
                """SELECT * FROM bookings
                   WHERE console_id = ? AND status = 'Active'
                   LIMIT 1""",
                (console_id,)
            )
        row = cur.fetchone()
        return dict(row) if row else None

    def get_booking_status(self, console_id: str, date: str = None) -> str:
        """Return 'Active', 'Free', or 'Scheduled' for a console."""
        bk = self.get_booking_for_console(console_id, date)
        if bk:
            return bk["status"]
        # Check for scheduled
        if date:
            cur = self._cursor()
            cur.execute(
                "SELECT status FROM bookings WHERE console_id = ? AND date = ? AND status = 'Scheduled' LIMIT 1",
                (console_id, date)
            )
            if cur.fetchone():
                return "Scheduled"
        return "Free"

    # ── Sales Access ─────────────────────────────────────────────────────────

    def get_sales_by_date(self, date: str) -> list[dict]:
        cur = self._cursor()
        cur.execute("SELECT * FROM sales WHERE date = ? ORDER BY id", (date,))
        return [dict(r) for r in cur.fetchall()]

    def get_sales_by_member(self, member_id: str, limit: int = 50) -> list[dict]:
        cur = self._cursor()
        cur.execute(
            "SELECT * FROM sales WHERE member_id = ? ORDER BY date DESC, id DESC LIMIT ?",
            (member_id, limit)
        )
        return [dict(r) for r in cur.fetchall()]

    def get_daily_total(self, date: str) -> dict:
        """Return daily sales summary."""
        cur = self._cursor()
        cur.execute(
            """SELECT COUNT(*) as tx_count, COALESCE(SUM(total_amount),0) as total_revenue,
                      COALESCE(SUM(cash),0) as total_cash, COALESCE(SUM(kpay),0) as total_kpay
               FROM sales WHERE date = ?""",
            (date,)
        )
        row = cur.fetchone()
        return dict(row) if row and row["tx_count"] > 0 else {
            "tx_count": 0, "total_revenue": 0, "total_cash": 0, "total_kpay": 0
        }

    # ── TopUp Access ─────────────────────────────────────────────────────────

    def get_topups_by_member(self, member_id: str, limit: int = 20) -> list[dict]:
        cur = self._cursor()
        cur.execute(
            "SELECT * FROM topups WHERE member_id = ? ORDER BY date DESC, id DESC LIMIT ?",
            (member_id, limit)
        )
        return [dict(r) for r in cur.fetchall()]

    def get_topup_total(self, member_id: str) -> float:
        """Total top-up amount for a member."""
        cur = self._cursor()
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) as total FROM topups WHERE member_id = ?",
            (member_id,)
        )
        return cur.fetchone()["total"]

    # ── Settings Access ──────────────────────────────────────────────────────

    def get_setting(self, key: str, default: str = "") -> str:
        cur = self._cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row["value"] if row else default

    def get_all_settings(self) -> dict:
        cur = self._cursor()
        cur.execute("SELECT key, value FROM settings")
        return {r["key"]: r["value"] for r in cur.fetchall()}

    # ── Console Access ───────────────────────────────────────────────────────

    def get_console(self, console_id: str) -> Optional[dict]:
        cur = self._cursor()
        cur.execute("SELECT * FROM consoles WHERE id = ?", (console_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_all_consoles(self) -> list[dict]:
        cur = self._cursor()
        cur.execute("SELECT * FROM consoles ORDER BY id")
        return [dict(r) for r in cur.fetchall()]

    # ── Console Games Access ─────────────────────────────────────────────────

    def get_games_on_console(self, console_id: str) -> list[str]:
        cur = self._cursor()
        cur.execute(
            "SELECT game_title FROM console_games WHERE console_id = ? ORDER BY game_title",
            (console_id,)
        )
        return [r["game_title"] for r in cur.fetchall()]

    def get_consoles_with_game(self, game_title: str) -> list[str]:
        cur = self._cursor()
        cur.execute(
            "SELECT console_id FROM console_games WHERE game_title = ? ORDER BY console_id",
            (game_title,)
        )
        return [r["console_id"] for r in cur.fetchall()]

    # ── Game Library Access ──────────────────────────────────────────────────

    def get_games(self, status_filter: str = None) -> list[dict]:
        if status_filter:
            cur = self._cursor()
            cur.execute(
                "SELECT * FROM game_library WHERE final_status LIKE ? ORDER BY title",
                (f"%{status_filter}%",)
            )
        else:
            cur = self._cursor()
            cur.execute("SELECT * FROM game_library ORDER BY title")
        return [dict(r) for r in cur.fetchall()]

    def get_game(self, title: str) -> Optional[dict]:
        cur = self._cursor()
        cur.execute("SELECT * FROM game_library WHERE title = ?", (title.strip(),))
        row = cur.fetchone()
        return dict(row) if row else None

    # ── Staff Access ─────────────────────────────────────────────────────────

    def get_staff(self, name: str) -> Optional[dict]:
        cur = self._cursor()
        cur.execute("SELECT * FROM staff WHERE name = ?", (name,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_all_staff(self) -> list[dict]:
        cur = self._cursor()
        cur.execute("SELECT * FROM staff ORDER BY name")
        return [dict(r) for r in cur.fetchall()]

    # ── Sync Operations ──────────────────────────────────────────────────────

    def log_sync(self, table_name: str, direction: str, rows: int,
                 status: str = "success", error: str = ""):
        """Record a sync operation in sync_log."""
        cur = self._cursor()
        cur.execute(
            """INSERT INTO sync_log (table_name, direction, rows_affected, status, error)
               VALUES (?, ?, ?, ?, ?)""",
            (table_name, direction, rows, status, error)
        )
        self._get_conn().commit()

    def get_last_sync(self, table_name: str) -> Optional[str]:
        """Get timestamp of last successful sync for a table."""
        cur = self._cursor()
        cur.execute(
            """SELECT synced_at FROM sync_log
               WHERE table_name = ? AND status = 'success' AND direction = 'sheets_to_sqlite'
               ORDER BY synced_at DESC LIMIT 1""",
            (table_name,)
        )
        row = cur.fetchone()
        return row["synced_at"] if row else None

    def get_sync_status(self) -> dict:
        """Return summary of last sync for all tables."""
        cur = self._cursor()
        cur.execute("""
            SELECT table_name, MAX(synced_at) as last_sync, direction, status,
                   SUM(rows_affected) as total_rows
            FROM sync_log
            GROUP BY table_name
            ORDER BY table_name
        """)
        return {r["table_name"]: {
            "last_sync": r["last_sync"], "direction": r["direction"],
            "status": r["status"], "total_rows": r["total_rows"]
        } for r in cur.fetchall()}

    # ── Bulk Import ──────────────────────────────────────────────────────────

    def import_members(self, rows: list[dict]) -> int:
        """Import members from Google Sheets data. Returns count."""
        conn = self._get_conn()
        count = 0
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM members")
            cur.executemany(
                """INSERT OR REPLACE INTO members
                   (id, name, phone, email, lifetime_spend, net_spend, wallet_mins,
                    rank_tier, effective_rate, reg_staff, referral_code, join_date, last_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows
            )
            count = cur.rowcount
            conn.commit()
            self.log_sync("members", "sheets_to_sqlite", count)
            logger.info("Imported %d members", count)
        except Exception as e:
            conn.rollback()
            self.log_sync("members", "sheets_to_sqlite", 0, "failed", str(e))
            logger.error("Failed to import members: %s", e)
        return count

    def import_bookings(self, rows: list[dict]) -> int:
        """Import bookings from Google Sheets. Returns count."""
        conn = self._get_conn()
        count = 0
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM bookings")
            cur.executemany(
                """INSERT OR REPLACE INTO bookings
                   (id, date, console_id, member_id, start_time, end_time, status, staff, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows
            )
            count = cur.rowcount
            conn.commit()
            self.log_sync("bookings", "sheets_to_sqlite", count)
            logger.info("Imported %d bookings", count)
        except Exception as e:
            conn.rollback()
            self.log_sync("bookings", "sheets_to_sqlite", 0, "failed", str(e))
            logger.error("Failed to import bookings: %s", e)
        return count

    def import_sales(self, rows: list[dict]) -> int:
        conn = self._get_conn()
        count = 0
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM sales")
            cur.executemany(
                """INSERT OR REPLACE INTO sales
                   (voucher_id, date, member_id, console_id, mins, game_amount, food_amount,
                    discount, total_amount, kpay, cash, payment_method, staff, type, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows
            )
            count = cur.rowcount
            conn.commit()
            self.log_sync("sales", "sheets_to_sqlite", count)
            logger.info("Imported %d sales records", count)
        except Exception as e:
            conn.rollback()
            self.log_sync("sales", "sheets_to_sqlite", 0, "failed", str(e))
            logger.error("Failed to import sales: %s", e)
        return count

    def import_settings(self, rows: list[tuple]) -> int:
        """Import settings as (key, value) tuples. Returns count."""
        conn = self._get_conn()
        count = 0
        try:
            cur = conn.cursor()
            cur.executemany(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                rows
            )
            count = cur.rowcount
            conn.commit()
            self.log_sync("settings", "sheets_to_sqlite", count)
            logger.info("Imported %d settings", count)
        except Exception as e:
            conn.rollback()
            self.log_sync("settings", "sheets_to_sqlite", 0, "failed", str(e))
            logger.error("Failed to import settings: %s", e)
        return count

    def import_consoles(self, rows: list[dict]) -> int:
        conn = self._get_conn()
        count = 0
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM consoles")
            cur.executemany(
                "INSERT OR REPLACE INTO consoles (id, console_type, multiplier) VALUES (?, ?, ?)",
                rows
            )
            count = cur.rowcount
            conn.commit()
            self.log_sync("consoles", "sheets_to_sqlite", count)
            logger.info("Imported %d consoles", count)
        except Exception as e:
            conn.rollback()
            self.log_sync("consoles", "sheets_to_sqlite", 0, "failed", str(e))
            logger.error("Failed to import consoles: %s", e)
        return count

    def import_console_games(self, rows: list[dict]) -> int:
        conn = self._get_conn()
        count = 0
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM console_games")
            cur.executemany(
                """INSERT OR REPLACE INTO console_games
                   (console_id, game_title, install_type, date, notes)
                   VALUES (?, ?, ?, ?, ?)""",
                rows
            )
            count = cur.rowcount
            conn.commit()
            self.log_sync("console_games", "sheets_to_sqlite", count)
            logger.info("Imported %d console-game records", count)
        except Exception as e:
            conn.rollback()
            self.log_sync("console_games", "sheets_to_sqlite", 0, "failed", str(e))
            logger.error("Failed to import console_games: %s", e)
        return count

    def import_game_library(self, rows: list[dict]) -> int:
        conn = self._get_conn()
        count = 0
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM game_library")
            cur.executemany(
                """INSERT OR REPLACE INTO game_library
                   (title, final_status, available_discs, total_copies, in_use, solo_multi, genre)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                rows
            )
            count = cur.rowcount
            conn.commit()
            self.log_sync("game_library", "sheets_to_sqlite", count)
            logger.info("Imported %d games", count)
        except Exception as e:
            conn.rollback()
            self.log_sync("game_library", "sheets_to_sqlite", 0, "failed", str(e))
            logger.error("Failed to import game_library: %s", e)
        return count

    def import_staff(self, rows: list[dict]) -> int:
        conn = self._get_conn()
        count = 0
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM staff")
            cur.executemany(
                "INSERT OR REPLACE INTO staff (name, base_salary) VALUES (?, ?)",
                rows
            )
            count = cur.rowcount
            conn.commit()
            self.log_sync("staff", "sheets_to_sqlite", count)
            logger.info("Imported %d staff", count)
        except Exception as e:
            conn.rollback()
            self.log_sync("staff", "sheets_to_sqlite", 0, "failed", str(e))
            logger.error("Failed to import staff: %s", e)
        return count

    # ── Dashboard / Reporting Queries ────────────────────────────────────────

    def get_dashboard_stats(self) -> dict:
        """Return key dashboard metrics."""
        cur = self._cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM members")
        total_members = cur.fetchone()["cnt"]

        cur.execute("SELECT COALESCE(SUM(wallet_mins),0) as total FROM members")
        total_wallet = cur.fetchone()["total"]

        cur.execute(
            """SELECT COUNT(*) as cnt FROM bookings
               WHERE status = 'Active' AND date = date('now','+6 hours 30 minutes')"""
        )
        active_sessions = cur.fetchone()

        return {
            "total_members": total_members,
            "total_wallet_mins": total_wallet,
            "active_sessions": active_sessions["cnt"] if active_sessions else 0,
        }
