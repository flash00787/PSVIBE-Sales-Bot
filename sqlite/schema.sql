-- ============================================================================
-- PS VIBE SQLite Schema v1.0
-- Local read-mirror of Google Sheets data for fast cached reads
-- ============================================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Members — mirrors Card_Wallet sheet
CREATE TABLE IF NOT EXISTS members (
    id             TEXT PRIMARY KEY,              -- member_id e.g. PSV_A_001
    name           TEXT NOT NULL,                  -- member name
    phone          TEXT DEFAULT '',                -- phone number
    email          TEXT DEFAULT '',                -- email address
    lifetime_spend REAL DEFAULT 0,                -- col E: total lifetime spend
    net_spend      REAL DEFAULT 0,                -- col F: ranking net spend
    wallet_mins    INTEGER DEFAULT 0,             -- col H: current wallet balance (minutes)
    rank_tier      TEXT DEFAULT 'Warrior',         -- col G: rank tier
    effective_rate REAL DEFAULT 0,                -- col L: weighted average rate
    reg_staff      TEXT DEFAULT '',               -- col K: registering staff
    referral_code  TEXT DEFAULT '',               -- col Q: referral code
    join_date      TEXT DEFAULT '',               -- first seen date (computed)
    last_active    TEXT DEFAULT '',               -- last activity date
    notes          TEXT DEFAULT '',
    synced_at      TEXT DEFAULT (datetime('now')),
    sheet_row      INTEGER DEFAULT 0              -- original Sheet row number
);

-- Console Bookings — mirrors Console_Booking sheet
CREATE TABLE IF NOT EXISTS bookings (
    id             TEXT PRIMARY KEY,              -- booking_id e.g. BK-20260526-C01-1430
    date           TEXT NOT NULL,                  -- M/D/YYYY
    console_id     TEXT NOT NULL,                  -- e.g. C - 01
    member_id      TEXT DEFAULT '',               -- member_id or 'Guest'
    start_time     TEXT NOT NULL,                  -- HH:MM
    end_time       TEXT DEFAULT '',               -- HH:MM (planned or actual end)
    status         TEXT NOT NULL DEFAULT 'Active'
                   CHECK(status IN ('Active','Done','Cancelled','Scheduled')),
    staff          TEXT DEFAULT '',
    notes          TEXT DEFAULT '',               -- game name, etc.
    synced_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings(date);
CREATE INDEX IF NOT EXISTS idx_bookings_console ON bookings(console_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);

-- Sales — mirrors Sales_Daily sheet
CREATE TABLE IF NOT EXISTS sales (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    voucher_id     TEXT NOT NULL,                  -- e.g. V-001
    date           TEXT NOT NULL,                  -- M/D/YYYY
    member_id      TEXT DEFAULT '',             --
    console_id     TEXT DEFAULT '',
    mins           INTEGER DEFAULT 0,
    game_amount    REAL DEFAULT 0,
    food_amount    REAL DEFAULT 0,
    discount       REAL DEFAULT 0,
    total_amount   REAL DEFAULT 0,
    kpay           REAL DEFAULT 0,
    cash           REAL DEFAULT 0,
    payment_method TEXT DEFAULT '',
    staff          TEXT DEFAULT '',
    type           TEXT DEFAULT 'sale'
                   CHECK(type IN ('sale','topup','service','other')),
    notes          TEXT DEFAULT '',
    synced_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date);
CREATE INDEX IF NOT EXISTS idx_sales_member ON sales(member_id);

-- TopUp Log — mirrors TopUp_Log sheet
CREATE TABLE IF NOT EXISTS topups (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    date           TEXT NOT NULL,
    member_id      TEXT NOT NULL,
    tier           TEXT DEFAULT '',
    amount         REAL DEFAULT 0,
    kpay           REAL DEFAULT 0,
    cash           REAL DEFAULT 0,
    added_mins     INTEGER DEFAULT 0,
    topup_type     TEXT DEFAULT 'Top Up',
    staff          TEXT DEFAULT '',
    synced_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_topups_date ON topups(date);
CREATE INDEX IF NOT EXISTS idx_topups_member ON topups(member_id);

-- Settings — mirrors Setting sheet key-value pairs
CREATE TABLE IF NOT EXISTS settings (
    key            TEXT PRIMARY KEY,
    value          TEXT NOT NULL,
    updated_at     TEXT DEFAULT (datetime('now'))
);

-- Consoles — mirrors Setting!H:J
CREATE TABLE IF NOT EXISTS consoles (
    id             TEXT PRIMARY KEY,              -- e.g. C - 01
    console_type   TEXT DEFAULT 'PS5',            -- e.g. PS5, PS5 Pro
    multiplier     REAL DEFAULT 1.0,
    synced_at      TEXT DEFAULT (datetime('now'))
);

-- Console Games — mirrors Console_Games sheet
CREATE TABLE IF NOT EXISTS console_games (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    console_id     TEXT NOT NULL,
    game_title     TEXT NOT NULL,
    install_type   TEXT DEFAULT 'HDD',            -- HDD / Disc / SSD / Session
    date           TEXT DEFAULT '',
    notes          TEXT DEFAULT '',
    synced_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cg_console ON console_games(console_id);
CREATE INDEX IF NOT EXISTS idx_cg_game ON console_games(game_title);

-- Game Library — mirrors Game_Library sheet
CREATE TABLE IF NOT EXISTS game_library (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    row_no         INTEGER DEFAULT 0,            -- A: sequential number
    title          TEXT NOT NULL,
    final_status   TEXT DEFAULT '',              -- C: e.g. "Not Installed", console list
    available_discs INTEGER DEFAULT 0,           -- D
    total_copies   INTEGER DEFAULT 0,            -- E
    in_use         INTEGER DEFAULT 0,            -- F
    solo_multi     TEXT DEFAULT '',              -- from col U metadata
    genre          TEXT DEFAULT '',               -- from col U metadata
    synced_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_gl_title ON game_library(title);

-- Console-Game mapping (pivot from Game_Library checkboxes G-S)
CREATE TABLE IF NOT EXISTS game_console_map (
    console_id     TEXT NOT NULL,
    game_title     TEXT NOT NULL,
    PRIMARY KEY (console_id, game_title)
);
CREATE INDEX IF NOT EXISTS idx_gcm_console ON game_console_map(console_id);

-- Stock Out — mirrors Stock_Out sheet
CREATE TABLE IF NOT EXISTS stock_out (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    date           TEXT NOT NULL,
    item           TEXT NOT NULL,
    qty            INTEGER DEFAULT 0,
    unit           TEXT DEFAULT '',
    staff          TEXT DEFAULT '',
    notes          TEXT DEFAULT '',
    synced_at      TEXT DEFAULT (datetime('now'))
);

-- Inventory — mirrors Inventory sheet
CREATE TABLE IF NOT EXISTS inventory (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    item           TEXT NOT NULL,
    qty            INTEGER DEFAULT 0,
    unit           TEXT DEFAULT '',
    unit_cost      REAL DEFAULT 0,
    total_cost     REAL DEFAULT 0,
    last_updated   TEXT DEFAULT '',
    synced_at      TEXT DEFAULT (datetime('now'))
);

-- Staff — mirrors Setting!S:T
CREATE TABLE IF NOT EXISTS staff (
    name           TEXT PRIMARY KEY,
    base_salary    REAL DEFAULT 0,
    synced_at      TEXT DEFAULT (datetime('now'))
);

-- Attendance — mirrors Attendance_Log sheet
CREATE TABLE IF NOT EXISTS attendance (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    month          TEXT NOT NULL,
    staff_name     TEXT NOT NULL,
    leave_days     INTEGER DEFAULT 0,
    late_count     INTEGER DEFAULT 0,
    deduct_per_late INTEGER DEFAULT 500,
    synced_at      TEXT DEFAULT (datetime('now'))
);

-- ============================================================================
-- SYNC & UTILITY TABLES
-- ============================================================================

-- Sync log for tracking import/export operations
CREATE TABLE IF NOT EXISTS sync_log (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name     TEXT NOT NULL,
    direction      TEXT NOT NULL
                   CHECK(direction IN ('sheets_to_sqlite','sqlite_to_sheets')),
    rows_affected  INTEGER DEFAULT 0,
    status         TEXT NOT NULL DEFAULT 'success'
                   CHECK(status IN ('success','failed','partial')),
    error          TEXT DEFAULT '',
    synced_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sync_log_table ON sync_log(table_name);

-- Cache metadata for version tracking
CREATE TABLE IF NOT EXISTS cache_meta (
    key            TEXT PRIMARY KEY,              -- e.g. 'members_last_sync'
    value          TEXT NOT NULL,                  -- timestamp or version string
    updated_at     TEXT DEFAULT (datetime('now'))
);


-- ============================================================================
-- v1.1 — Performance Optimizations (added 2026-05-26)
-- ============================================================================

-- Composite & Covering Indexes
CREATE INDEX IF NOT EXISTS idx_bookings_date_console ON bookings(date, console_id);
CREATE INDEX IF NOT EXISTS idx_sales_staff_date ON sales(staff, date);
CREATE INDEX IF NOT EXISTS idx_sales_member_date ON sales(member_id, date);
CREATE INDEX IF NOT EXISTS idx_topups_member_date ON topups(member_id, date);
CREATE INDEX IF NOT EXISTS idx_members_mins ON members(wallet_mins);
CREATE INDEX IF NOT EXISTS idx_members_name ON members(name);
CREATE INDEX IF NOT EXISTS idx_gl_genre ON game_library(genre);

-- Performance Pragmas
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=-8000;
PRAGMA temp_store=MEMORY;
PRAGMA mmap_size=268435456;

-- Useful Views
CREATE VIEW IF NOT EXISTS v_member_balance AS
  SELECT id, name, phone, wallet_mins, rank_tier, lifetime_spend, effective_rate
  FROM members ORDER BY wallet_mins DESC;

CREATE VIEW IF NOT EXISTS v_daily_sales AS
  SELECT date, COUNT(*) as tx_count, SUM(total_amount) as total_revenue,
         SUM(mins) as total_mins, SUM(kpay) as total_kpay, SUM(cash) as total_cash
  FROM sales GROUP BY date ORDER BY date DESC;

CREATE VIEW IF NOT EXISTS v_active_bookings AS
  SELECT b.*, m.name as member_name
  FROM bookings b LEFT JOIN members m ON b.member_id = m.id
  WHERE b.status IN ('Active', 'Scheduled')
  ORDER BY b.date, b.start_time;
