"""
PS VIBE V2 — Database Core Module
SQLite connection pool, table initialization, and schema management.
"""

import os
import sqlite3
import threading
import logging
from pathlib import Path

logger = logging.getLogger("psvibe.db")

_DB_PATH = os.environ.get("BOT_DB_PATH", "/root/Sales-Tele-Bot_refactored/bot_data.db")
_SA_JSON = "/root/Sales-Tele-Bot_refactored/service_account.json"
_SHEET_ID = os.environ.get("SHEET_ID", "1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA")

# ── Thread-local connection pool ─────────────────────────────────────────────
_local = threading.local()

def _get_conn() -> sqlite3.Connection:
    """Get thread-local SQLite connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA cache_size=-8000")
        conn.execute("PRAGMA synchronous=NORMAL")
        _local.conn = conn
    return _local.conn

def _cursor():
    return _get_conn().cursor()

def close_conn():
    """Close thread-local connection."""
    if hasattr(_local, "conn") and _local.conn:
        _local.conn.close()
        _local.conn = None

# ── Schema ───────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS config_cache (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS booking_cache (
    booking_id TEXT PRIMARY KEY,
    data_json TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS receipt_store (
    voucher_id TEXT PRIMARY KEY,
    data_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory_cache (
    item_name TEXT PRIMARY KEY,
    data_json TEXT,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_booking_cache_cached ON booking_cache(cached_at);
CREATE INDEX IF NOT EXISTS idx_receipt_store_created ON receipt_store(created_at);
"""

def init_db():
    """Create all tables if they don't exist."""
    conn = _get_conn()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    logger.info("Database initialized at %s", _DB_PATH)

# ── Google Sheets Auth ──────────────────────────────────────────────────────

_gc = None
_wb = None

def _get_gc():
    global _gc
    if _gc is None:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(_SA_JSON, scope)
        _gc = gspread.authorize(creds)
    return _gc

def _get_wb():
    global _wb
    if _wb is None:
        _wb = _get_gc().open_by_key(_SHEET_ID)
    return _wb

def get_sheet(name: str):
    """Get a worksheet by name, creating it if needed."""
    return _get_wb().worksheet(name)

def get_sheet_safe(name: str, rows: int = 1000, cols: int = 10, headers: list = None):
    """Get or create a worksheet."""
    try:
        return _get_wb().worksheet(name)
    except Exception:
        sh = _get_wb().add_worksheet(name, rows=rows, cols=cols)
        if headers:
            sh.update("A1", [headers], value_input_option="USER_ENTERED")
        return sh

# ── Cache Helpers ────────────────────────────────────────────────────────────

def cache_get(table: str, key_col: str, key: str) -> str | None:
    """Get cached JSON string from SQLite."""
    cur = _cursor()
    cur.execute(f"SELECT data_json FROM {table} WHERE {key_col} = ?", (key,))
    row = cur.fetchone()
    return row["data_json"] if row else None

def cache_set(table: str, key_col: str, key: str, value: str, upsert_cols: str = ""):
    """Upsert cache entry."""
    conn = _get_conn()
    extra_cols = ""
    extra_vals = ""
    if upsert_cols:
        extra_cols = ", " + upsert_cols
        extra_vals = ", excluded." + ", excluded.".join(upsert_cols.split(", "))
    conn.execute(
        f"INSERT INTO {table} ({key_col}, data_json{extra_cols}) VALUES (?, ?{', ?' * (len(upsert_cols.split(',')) if upsert_cols else 0)}) "
        f"ON CONFLICT({key_col}) DO UPDATE SET data_json = excluded.data_json"
        f"{extra_vals}",
        (key, value),
    )
    conn.commit()

def cache_config_get(key: str) -> str | None:
    """Get cached config value."""
    cur = _cursor()
    cur.execute("SELECT value FROM config_cache WHERE key = ?", (key,))
    row = cur.fetchone()
    return row["value"] if row else None

def cache_config_set(key: str, value: str):
    """Set cached config value."""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO config_cache (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
        (key, value),
    )
    conn.commit()

# Initialize on import
try:
    init_db()
except Exception as e:
    logger.warning("DB init warning (may already be initialized): %s", e)
