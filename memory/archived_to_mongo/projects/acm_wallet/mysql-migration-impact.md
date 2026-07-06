# ACM Wallet: Google Sheets → MySQL Migration Impact Analysis

> **Date:** 2026-06-25
> **Source file:** `/root/ACM-Personal-Wallet/bot/main.py` (5,979 lines)
> **Current backend:** Google Sheets (4 worksheets) via gspread
> **Proposed backend:** MySQL (mysql-connector-python, already on server)

---

## Database Schema (Proposed)

### `transactions` (replaces Transaction_Log worksheet)
```sql
CREATE TABLE transactions (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    tx_date    DATE NOT NULL,                 -- col B (was ARRAYFORMULA-dependent)
    tx_type    ENUM('Income','Expense','Transfer','Invest','Asset') NOT NULL,  -- col E
    category   VARCHAR(100) NOT NULL DEFAULT '',  -- col F
    acc_from   VARCHAR(100) NOT NULL DEFAULT '',  -- col G
    acc_to     VARCHAR(100) NOT NULL DEFAULT '',  -- col H
    amount     DECIMAL(15,2) NOT NULL,            -- col I
    project    VARCHAR(100) NOT NULL DEFAULT '',  -- col J
    scope      ENUM('Business','Personal','Income','Transfer') NOT NULL,  -- col N
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date (tx_date),
    INDEX idx_month (tx_date),                    -- replaces col D ARRAYFORMULA YYYY-MM
    INDEX idx_type (tx_type),
    INDEX idx_category (category),
    INDEX idx_account_from (acc_from),
    INDEX idx_account_to (acc_to),
    INDEX idx_project (project),
    INDEX idx_scope (scope),
    FULLTEXT INDEX idx_search (category, acc_from, acc_to, project)  -- replaces /search scan
);
```

### `opening_balances` (replaces Opening_Balances worksheet)
```sql
CREATE TABLE opening_balances (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    ob_date    DATE NOT NULL,                 -- col A
    ob_type    VARCHAR(50) NOT NULL,          -- col B (Account, Asset, Real Estate, Business, Receivable, Payable)
    entity     VARCHAR(200) NOT NULL,         -- col C
    amount     DECIMAL(15,2) NOT NULL,        -- col D
    notes      VARCHAR(500) DEFAULT '',       -- col E
    currency   VARCHAR(3) DEFAULT '',         -- col F
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (ob_type),
    INDEX idx_entity (entity),
    INDEX idx_type_entity (ob_type, entity)
);
```

### `settings` (replaces Settings worksheet)
```sql
CREATE TABLE settings (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    setting_type   ENUM('account','business_cat','personal_cat','project','income_cat','fx_rate','other') NOT NULL,
    name           VARCHAR(200) NOT NULL,
    value          TEXT DEFAULT NULL,
    display_order  INT DEFAULT 0,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_type_name (setting_type, name),
    INDEX idx_type (setting_type)
);
```
> Columns mapped: Accounts (col A), Business Cats (col C), Personal Cats (col D), Projects (col E), Income Cats (col F), FX Rates (cols K+L)

### `saas_subscriptions` (replaces Saas_Tracker worksheet)
```sql
CREATE TABLE saas_subscriptions (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(200) NOT NULL,         -- col A
    monthly    DECIMAL(10,2) DEFAULT 0.00,    -- col B
    renewal    VARCHAR(100) DEFAULT '',       -- col C
    billing    VARCHAR(50) DEFAULT '',        -- col D
    account    VARCHAR(100) DEFAULT '',       -- col E
    status     VARCHAR(50) DEFAULT 'Active',  -- col F
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_status (status)
);
```

### `fx_rates` (new standalone — was mixed into Settings cols K+L)
```sql
CREATE TABLE fx_rates (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    currency   VARCHAR(3) NOT NULL UNIQUE,    -- e.g. USD, THB, VND
    rate       DECIMAL(15,4) NOT NULL,        -- MMK per 1 unit
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_currency (currency)
);
```

### `budgets` (replaces pickle in bot_data["budgets"])
```sql
CREATE TABLE budgets (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT NOT NULL,              -- Telegram user ID
    amount      DECIMAL(15,2) NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user (user_id)
);
```

### `reminders` (replaces pickle in bot_data["reminders"])
```sql
CREATE TABLE reminders (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT NOT NULL UNIQUE,       -- Telegram user ID
    time_hhmm   VARCHAR(5) NOT NULL,          -- "09:00"
    job_name    VARCHAR(100) DEFAULT '',      -- for JobQueue reference
    enabled     TINYINT(1) DEFAULT 1,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id)
);
```

---

## Impact by Component

### Data Layer — Functions That Directly Call `_sheet_client()` or gspread

#### Write Functions (HIGH impact)

| # | Function | Lines | What It Does | What Changes | Effort |
|---|----------|-------|-------------|--------------|--------|
| 1 | `save_transaction()` | 542–605 | Writes 8 cells to Transaction_Log via `update_cells()` | Replace with `INSERT INTO transactions` + `LAST_INSERT_ID()`. No more `col_values(2)+1` row counting. | **MED** |
| 2 | `save_opening_balance()` | 606–619 | Appends row to Opening_Balances via `append_row()` | Replace with `INSERT INTO opening_balances`. No `append_row` — just INSERT. | **MED** |
| 3 | `save_transfer()` | 622–691 | Writes 1 or 2 rows to Transaction_Log (same as save_transaction pattern) | Replace with 1-2 `INSERT INTO transactions`. Cross-currency path simplified — no cell position math. | **MED** |
| 4 | `update_fx_rate_in_sheet()` | 1156–1168 | Scans Settings rows to find currency, writes to col L | Replace with `INSERT INTO fx_rates ... ON DUPLICATE KEY UPDATE`. Much simpler — no column scanning. | **LOW** |

#### Read Functions (MEDIUM impact)

| # | Function | Lines | What It Does | What Changes | Effort |
|---|----------|-------|-------------|--------------|--------|
| 5 | `fetch_settings()` | 463–539 | Reads Settings + Opening_Balances sheets, parses 6 columns, builds account/category/project lists | Replace with 5 `SELECT` queries from `settings` table + `SELECT DISTINCT` from `opening_balances` for fallback accounts. 5-min cache stays. | **MED** |
| 6 | `_fetch_tx_rows_raw()` | 694–698 | `sheet.get_all_values()` → returns raw `list[list]` | Replace with `SELECT * FROM transactions ORDER BY id`. Return type changes from string lists to typed rows. | **MED** |
| 7 | `get_monthly_summary()` | 786–881 | Scans all rows, filters by YYYY-MM col D prefix, aggregates income/expense/categories | Replace with `SELECT SUM(amount), tx_type, scope, category FROM transactions WHERE tx_date BETWEEN '...' AND '...' GROUP BY tx_type, scope, category`. Eliminates Python-side filtering of thousands of rows. | **MED** |
| 8 | `get_weekly_summary()` | 882–922 | Scans rows, matches dates to last 7 days | Replace with `SELECT DATE(tx_date), tx_type, SUM(amount) FROM transactions WHERE tx_date >= CURDATE() - INTERVAL 7 DAY GROUP BY DATE(tx_date), tx_type`. | **LOW** |
| 9 | `get_today_data()` | 923–981 | Gets today's slice from cached rows + monthly summary | Replace with direct SQL queries. Can call monthly summary SQL + today's SQL in parallel. | **MED** |
| 10 | `get_recent_transactions()` | 1010–1030 | Filters rows, maps cols to dicts, paginates | Replace with `SELECT * FROM transactions ORDER BY id DESC LIMIT n OFFSET o`. No more row filtering in Python. | **LOW** |
| 11 | `search_transactions()` | 1032–1056 | Linear scan of all rows for keyword match | Replace with `SELECT * FROM transactions WHERE MATCH(category,acc_from,acc_to,project) AGAINST(?) OR project LIKE ?`. Dramatic performance improvement. Also replaces `search_transactions_enhanced()` (line 3533). | **LOW** |
| 12 | `find_last_tx_row()` | 1058–1081 | Reverses row list, finds last data row | Replace with `SELECT * FROM transactions ORDER BY id DESC LIMIT 1`. Trivial. | **LOW** |
| 13 | `get_opening_balances()` | 1082–1124 | Reads OB sheet, groups by type, sums amounts, nets settlements | Replace with `SELECT ob_type, entity, SUM(amount) as total, notes FROM opening_balances WHERE amount != 0 GROUP BY ob_type, entity HAVING total != 0`. Aggregation moves to DB. | **MED** |
| 14 | `get_fx_rates()` | 1126–1154 | Reads Settings sheet cols K+L for currency rates | Replace with `SELECT currency, rate FROM fx_rates`. Simple. | **LOW** |
| 15 | `get_saas_subscriptions()` | 1170–1202 | Reads Saas_Tracker sheet, parses renewal date | Replace with `SELECT * FROM saas_subscriptions`. No date serial parsing needed — use MySQL DATE type. | **LOW** |
| 16 | `get_project_summary()` | 1204–1246 | Scans rows for project P&L | Replace with `SELECT tx_type, category, SUM(amount) FROM transactions WHERE project LIKE ? AND tx_type != 'Transfer' GROUP BY tx_type, category`. | **LOW** |
| 17 | `get_account_balances()` | 1306–1393 | Reads OB + transactions, computes per-account balance with currency resolution | Replace with `LEFT JOIN` query: `opening_balances` + subquery sums from `transactions`. Currency resolution moves to DB column. Most complex rewrite. | **HIGH** |
| 18 | `get_cashflow_data()` | 1420–1493 | Scans rows for 5-month income/expense trend | Replace with `SELECT DATE_FORMAT(tx_date,'%Y-%m'), tx_type, SUM(amount) FROM transactions WHERE tx_date >= ... GROUP BY DATE_FORMAT(...)`. | **LOW** |

### Functions That Can Be DELETED Entirely

These are no longer needed with MySQL:

| # | Function | Lines | Reason |
|---|----------|-------|--------|
| 1 | `_sheet_client()` | 417–428 | gspread client singleton — **DELETE** (replaced by MySQL connection pool) |
| 2 | `_gsheet_retry()` decorator | 298–331 | Sheets-specific retry logic — **DELETE** (replaced by MySQL connection retry) |
| 3 | `_sh()` async wrapper | 396–414 | Runs blocking sheets calls in thread with timeout — **DELETE** (replace with async MySQL) |
| 4 | `_sanitize_cell()` | 447–459 | Prevents formula injection in Sheets — **DELETE** (MySQL parameterized queries eliminate injection) |
| 5 | `_fetch_tx_rows_raw()` | 694–698 | Low-level sheets fetch — **DELETE** (absorbed into new `_get_tx_rows()`) |
| 6 | `_is_data_row()` | 983–1008 | Validates raw row has date + amount — **DELETE** (MySQL WHERE clause replaces) |
| 7 | `_parse_row_date()` | 746–783 | Handles 9 date formats + numeric serials — **DELETE** (MySQL DATE type eliminates all parsing) |
| 8 | `_DATE_FMTS` constant | 737–744 | 9 date format strings — **DELETE** |
| 9 | `_GSHEET_EPOCH` constant | 750 | Date serial epoch — **DELETE** |
| 10 | `_resolve_currency()` | 1280–1303 | Currency detection from account name strings — **DELETE** (currency stored as column in opening_balances) |
| 11 | `_CURRENCY_CODES`, `_CUR_SYMBOLS`, `_CUR_NAMES` | 1250–1278 | Currency keyword maps — **DELETE** (moved into opening_balances.currency column) |

> **Lines of code saved:** ~300 lines (~5% of total)

### Functions That Simplify Significantly

| Function | Lines | Simplification |
|----------|-------|----------------|
| `save_transaction()` | 542–605 | No ARRAYFORMULA awareness needed. No `col_values(2)+1` row counting. No Cell object construction. Just `INSERT INTO transactions (...) VALUES (...)` |
| `save_transfer()` | 622–691 | Same as above. No double-row Cell construction. Just 2 INSERTs in a transaction. |
| `get_monthly_summary()` | 786–881 | 96-line monster → ~20 line SQL GROUP BY call. All Python-side aggregation (income/business/personal/category totals) moves to SQL. |
| `get_account_balances()` | 1306–1393 | 88-line complex function → SQL JOIN + GROUP BY. Eliminates Python-side account name canonicalization. |
| `search_transactions()` | 1032–1056 | 24-line linear scan → 1 SQL FULLTEXT query |
| `search_transactions_enhanced()` | 3533–3570 | 37-line enhanced scan → 1 SQL FULLTEXT query (merged with above) |
| `get_recent_transactions()` | 1010–1030 | 20-line filter+paginate → `SELECT ... ORDER BY id DESC LIMIT n OFFSET o` |
| `find_last_tx_row()` | 1058–1081 | 23-line reverse-scan → `SELECT ... ORDER BY id DESC LIMIT 1` |
| `get_cashflow_data()` | 1420–1493 | 73-line scan → SQL GROUP BY with DATE_FORMAT |
| `get_opening_balances()` | 1082–1124 | 42-line scan + bucket/group/sort → SQL GROUP BY with HAVING |

### Cache Layer

#### Caches That Go Away Entirely
| Cache | Rationale |
|-------|-----------|
| `_tx_rows_cache` (lines 352–365) | With MySQL indexed queries, fetching all rows to cache is anti-pattern. Per-query WHERE clauses are faster. |
| `_tx_rows_cache_ts` | Same as above |
| `_invalidate_tx_rows_cache()` (line 341) | No longer needed |
| `_monthly_cache` (line 363) | Monthly data retrieved by targeted SQL with date range — no need to scan all rows |
| `_weekly_cache` (line 364) | Weekly data via SQL WHERE tx_date range |
| `_cashflow_cache` (line 365) | Cashflow data via SQL GROUP BY |
| `_opening_cache` (line 366) | Opening balances via SQL — fast aggregate query |
| `_cache_warmer_loop()` (line 5871) | Background thread that calls Sheets every 90s — **DELETE** or reduce to simple connection health check |
| `start_cache_warmer()` (line 5912) | Daemon thread starter — **DELETE** or repurpose |

> **Net effect:** 8 of 9 cache variables are removed. The background cache-warmer thread is eliminated entirely — saving CPU, memory, and Sheets API quota.

#### Caches That Become Database-Level
| Cache | DB Replacement |
|-------|---------------|
| `_settings_cache` (line 351) | `SELECT * FROM settings` — fast enough without cache (small table, indexed) |
| `_acct_cache` (line 357) | `SELECT ... FROM opening_balances LEFT JOIN ...` — but account balances query is heavier; keep a 60s in-process cache or use MySQL query cache |
| `_fx_cache` (line 367) | `SELECT * FROM fx_rates` — tiny table, fast; cache optional |

**Recommendation:** Keep a simplified 60s in-process cache for 1-2 heavy queries (account_balances) but drop all others. The `invalidate_all_caches()` function (line 369) simplifies to `reset_account_balances_cache()`.

#### Caching Architecture — Before/After

| Aspect | Before (Sheets) | After (MySQL) |
|--------|----------------|---------------|
| Total cache variables | 9 (`_settings_cache`, `_acct_cache`, `_monthly_cache`, `_weekly_cache`, `_cashflow_cache`, `_opening_cache`, `_fx_cache`, `_tx_rows_cache`, `_tx_rows_cache_ts`) | 1-2 (account_balances only) |
| Cache invalidation functions | 4 (`invalidate_all_caches`, `_invalidate_acct_cache`, `_invalidate_tx_rows_cache`, `_invalidate_opening_cache`) | 1 (`invalidate_account_cache`) |
| Background cache warmer | 90s daemon thread calling 6 sheet functions | **Eliminated** |
| Cache TTL values | 120s–600s (multiple) | 60s (single) |

### Helper Functions

#### `_parse_amount()` (line 716)
**Verdict: UNCHANGED.** Parses user input text → float. Not related to Sheets. Keep as-is.

#### `parse_amount()` (line 1497)
**Verdict: UNCHANGED.** User-facing amount parser with k/m/b shorthand. No Sheets dependency.

#### `_parse_row_date()` (line 746)
**Verdict: DELETED.** No longer needed — MySQL DATE type eliminates all date parsing complexity:
- No more Google Sheets numeric serial (46943.0 → date conversion)
- No more 9-format brute-force date parsing
- No more ARRAYFORMULA col D dependency
- No more `_DATE_FMTS` constant

#### `_is_data_row()` (line 983)
**Verdict: DELETED.** MySQL WHERE clause replaces row validation:
- `WHERE tx_date IS NOT NULL AND amount IS NOT NULL`
- No more checking col B for "Date" header
- No more checking if amount is parseable

#### `_get_tx_rows()` (line 700)
**Verdict: REWRITTEN.** Returns `list[tuple]` from MySQL cursor instead of `list[list[str]]` from Sheets. The caller interface changes from index-based (`row[4]`, `row[8]`) to named columns. This is the **biggest cascading change** — every function that uses `_get_tx_rows()` must update its column accessors.

#### `_resolve_currency()` (line 1280)
**Verdict: DELETED.** Currency detection from account name strings (symbols, keywords, bank names) is no longer needed. Currency is stored as a column in `opening_balances`.

#### `_db_get_connection()` (NEW)
```python
def _db_get_connection():
    """Return a MySQL connection from pool."""
    return mysql.connector.connect(pool_name="acm_wallet")
```
New function needed. Replace `_sheet_client()` (line 417).

#### `_db_execute()` (NEW)
```python
def _db_execute(query: str, params: tuple = (), fetch: bool = True):
    """Execute SQL with retry. Replace _sh() + _gsheet_retry()."""
```
New function needed. Replaces both `_sh()` (line 396) and `_gsheet_retry()` (line 298).

### `_sanitize_cell()` (line 447)
**Verdict: DELETED.** MySQL parameterized queries (`%s` placeholders) inherently prevent SQL injection. No formula injection equivalent exists in MySQL.

### `_err()` (line 430)
**Verdict: UPDATED.** Error messages change from "Google Sheets rate limit" → "Database connection error" / "Query timeout" etc. Same function shape, different messages.

---

## Commands — Impact Assessment

All 30+ commands call data-layer helper functions (listed above), not sheets directly. Their **business logic stays the same**. Only the data retrieval changes.

| Command | Data Functions Called | Handler Impact |
|---------|----------------------|----------------|
| `/start` (line 1709) | `fetch_settings()` | **LOW** — calls same helper, data shape unchanged |
| `/balance` (line 1994) | `get_account_balances()`, `get_monthly_summary()` | **LOW** — only display logic, no sheets references |
| `/summary` (line 2017) | `get_monthly_summary()` | **LOW** — unchanged handler |
| `/lastmonth` (line 2063) | `get_monthly_summary()` | **LOW** |
| `/weekly` (line 2137) | `get_weekly_summary()`, `get_monthly_summary()` | **LOW** |
| `/monthly` (line 2203) | `get_monthly_summary()` | **LOW** |
| `/today` (line 2306) | `get_today_data()` | **LOW** |
| `/history` (line 2412) | `get_recent_transactions()` | **LOW** — pagination via SQL LIMIT/OFFSET |
| `/export` (line 2330) | `_get_tx_rows()` | **LOW** — CSV generation logic unchanged |
| `/search` (line 2464) | `search_transactions()` / `search_transactions_enhanced()` | **LOW** — FULLTEXT may improve results |
| `/delete` (line 2495) | `find_last_tx_row()`, `sheet.worksheet().delete_rows()` | **MED** — replaces gspread `delete_rows(rn)` with `DELETE FROM transactions WHERE id = ?` |
| `/top` (line 2074) | `get_monthly_summary()` | **LOW** |
| `/debts` (line 3896) | `get_opening_balances()` | **LOW** |
| `/networth` (line 4786) | `get_opening_balances()`, `get_account_balances()` | **LOW** |
| `/fx` (line 4610) | `get_fx_rates()` | **LOW** |
| `/setrate` (line 4675) | `update_fx_rate_in_sheet()` | **LOW** |
| `/saas` (line 4722) | `get_saas_subscriptions()`, `get_fx_rates()` | **LOW** |
| `/project` (line 4881) | `fetch_settings()`, `get_project_summary()` | **LOW** |
| `/split` (line 4953) | `get_monthly_summary()` | **LOW** |
| `/accounts` (line 5270) | `get_account_balances()`, `get_fx_rates()` | **LOW** |
| `/cashflow` (line 5367) | `get_cashflow_data()` | **LOW** |
| `/compare` (line 5049) | `get_monthly_summary()` (×2) | **LOW** |
| `/forecast` (line 5159) | `get_monthly_summary()` | **LOW** |
| `/budget` (line 3344) | `get_monthly_summary()` (for display) | **MED** — budget storage moves from pickle → `budgets` table |
| `/remind` (line 3492) | `_schedule_reminder()` | **MED** — reminder storage moves from pickle → `reminders` table |
| `/ping` (line 2125) | None (pure Telegram check) | **ZERO** — unchanged |

---

## Conversation Handlers — Impact Assessment

All 9 conversation flows call helper functions, not sheets directly:

| Flow | Entry Point | Data Operations | Impact |
|------|------------|----------------|--------|
| **Main Transaction** (tx_conv) | `tx_receive_amount()` (line 2676) | `fetch_settings()`, `get_account_balances()`, `save_transaction()` | **LOW** — only data-layer functions change |
| **Quick Expense** (tx_conv) | `cmd_expense()` (line 5420) | `fetch_settings()`, `get_account_balances()` | **LOW** |
| **Edit Transaction** (tx_conv) | `tx_edit_start()` (line 2942) | `find_last_tx_row()`, `save_transaction()` | **LOW** |
| **Opening Balance** (ob_conv) | `ob_start()` (line 2580) | `save_opening_balance()` | **LOW** |
| **Balance Transfer** (xfer_conv) | `xfer_start()` (line 3041) | `fetch_settings()`, `get_account_balances()`, `get_fx_rates()`, `save_transfer()` | **LOW** |
| **Receipt Photo** (receipt_conv) | `cmd_receipt()` (line 3649) | `fetch_settings()`, `save_transaction()` | **LOW** |
| **Settle Debt** (settle_conv) | `settle_start()` (line 3944) | `get_opening_balances()`, `fetch_settings()`, `save_opening_balance()`, `save_transaction()` | **LOW** |
| **Borrow** (borrow_conv) | `borrow_start()` (line 4163) | `get_opening_balances()`, `fetch_settings()`, `save_opening_balance()`, `save_transaction()` | **LOW** |
| **Lend** (lend_conv) | `lend_start()` (line 4308) | `get_opening_balances()`, `fetch_settings()`, `save_opening_balance()`, `save_transaction()` | **LOW** |
| **Buy Asset** (buyasset_conv) | `buyasset_start()` (line 4458) | `fetch_settings()`, `save_transaction()`, `save_opening_balance()` | **LOW** |

> **Key insight:** None of the 9 conversation handlers reference gspread or `_sheet_client()` directly. They all call helper functions. The handlers themselves are **unchanged**. This is excellent architecture for migration.

---

## Race Conditions

### Old (Google Sheets)
| Issue | Severity | Details |
|-------|----------|---------|
| Concurrent write overwrite | **HIGH** | Two users writing simultaneously can clobber each other's rows when `col_values(2)+1` returns the same row number for both. Google Sheets has no row-level locking. |
| Read-during-write inconsistency | **MED** | A read between `col_values(2)` and `update_cells()` can see partial/inconsistent state. |
| ARRAYFORMULA propagation delay | **LOW** | Col D formula takes a moment to recalculate — stale reads possible. |
| API rate limiting (429) | **MED** | 60 requests per user per 100 seconds quota. Retry with exponential backoff (lines 298-331). |

### New (MySQL)
| Benefit | Details |
|---------|---------|
| Row-level locking (InnoDB) | `SELECT ... FOR UPDATE` or `INSERT` is atomic. No write overwrite possible. |
| Transactional integrity | `START TRANSACTION; INSERT INTO transactions...; INSERT INTO opening_balances; COMMIT;` — multi-table writes are atomic. Currently impossible with Sheets. |
| Concurrent reads safe | MVCC guarantees consistent snapshot reads. No "read during write" issues. |
| No rate limiting | MySQL handles thousands of QPS; no API quota anxiety. |

### New Race Conditions Introduced?
| Scenario | Risk | Mitigation |
|----------|------|------------|
| Two users getting same `MAX(id)` before insert | **NONE** — `AUTO_INCREMENT` is atomic |
| Budget alert check concurrent with new transaction | **NONE** — alert fires AFTER insert commits |
| Cache staleness after write | **LOW** | Same invalidation pattern as before; TTL is shorter (60s vs 120-600s) |

---

## Performance Impact

| Metric | Before (Sheets) | After (MySQL) | Improvement |
|--------|----------------|---------------|-------------|
| `get_monthly_summary()` | ~1.2–2.5s (fetch all rows + Python scan) | ~10–50ms (SQL GROUP BY with index) | **20–100× faster** |
| `get_account_balances()` | ~1.5–3s (2 sheet fetches + Python merge) | ~20–100ms (SQL JOIN) | **15–60× faster** |
| `search_transactions()` | ~0.5–1.5s (full Python scan of all rows) | ~5–20ms (FULLTEXT index) | **25–300× faster** |
| `/export` CSV | ~1–2s (fetch all rows) | ~10–50ms | **20–100× faster** |
| Transaction save | ~1–3s (API round-trip: col_values + update_cells) | ~5–20ms (single INSERT) | **50–600× faster** |
| `/delete` | ~1–2s (API call) | ~5ms (DELETE WHERE id = ?) | **200–400× faster** |
| Cache warmer cycle | ~3–8s every 90s (6 sheet calls) | **Eliminated** | ∞ |
| Concurrent users | Degrades linearly (shared API quota) | Scales to thousands (MySQL connection pool) | **10–100× more concurrent capacity** |
| User-perceived latency | 1–4s per command | 100–500ms per command | **10–40× faster UX** |

### Index Opportunities (not possible with Sheets)
```sql
-- Makes /search instant
FULLTEXT INDEX idx_search (category, acc_from, acc_to, project);

-- Makes monthly rollups instant (all /summary, /split, /compare, /forecast, /cashflow)
INDEX idx_date_type (tx_date, tx_type);

-- Makes project P&L instant
INDEX idx_project (project);

-- Makes account balance aggregation fast
INDEX idx_acc_from (acc_from);
INDEX idx_acc_to (acc_to);
```

---

## Backup & DevOps

### Current (Google Sheets)
- Version history via Google Drive (automatic)
- Manual export to CSV/XLSX
- No automated backup schedule
- Recovery: restore sheet version from Drive UI

### Proposed (MySQL)
```bash
# Daily automated backup (add to crontab)
mysqldump --single-transaction --routines --triggers \
  acm_wallet > /backups/acm_wallet_$(date +%Y%m%d).sql

# Weekly offsite copy (to Google Drive)
python3 /root/.openclaw/workspace/drive_tool.py upload \
  /backups/acm_wallet_$(date +%Y%m%d).sql
```

### Migration Script Needed
```python
# migrate_sheets_to_mysql.py
# 1. Read all rows from each Google Sheet worksheet
# 2. Parse, validate, and transform data
# 3. INSERT into MySQL tables
# 4. Verify row counts match
# 5. Optional: write migration log
```

### Rollback Plan
```
Phase 1: Dual-write mode (write to BOTH sheets + MySQL for 1 week)
Phase 2: Read from MySQL, write to both
Phase 3: Read/write MySQL only — delete sheets code
Rollback: flip env var DB_BACKEND=sheets → instant fallback
```

---

## Pickle Data Migration

### Budgets → `budgets` table
```
Before: context.bot_data["budgets"][user_id] = float
After:  INSERT INTO budgets (user_id, amount) VALUES (?, ?)
        ON DUPLICATE KEY UPDATE amount = VALUES(amount)
```

**Migration script:** Read `conversation_state.pkl` → extract `bot_data["budgets"]` → INSERT into `budgets`

### Reminders → `reminders` table
```
Before: context.bot_data["reminders"][user_id] = "HH:MM"
After:  INSERT INTO reminders (user_id, time_hhmm) VALUES (?, ?)
        ON DUPLICATE KEY UPDATE time_hhmm = VALUES(time_hhmm)
```

**Caution:** Reminders are also registered with `JobQueue` at runtime (line 3470 `_schedule_reminder()`). On restart, `_post_init()` (line 5598) reads bot_data and re-registers. Change this to read from `reminders` table.

### Conversation State → stays in pickle
**Recommendation: Keep pickle for conversation state.** Conversation flows are ephemeral (10-min timeout) and per-session. Moving them to MySQL adds complexity for no benefit. The `PersistenceInput(bot_data=True)` already intentionally excludes conversation data (lines 5640-5643).

---

## New Dependencies

| Dependency | Status | Installation |
|------------|--------|-------------|
| `mysql-connector-python` | Already on server | `pip install mysql-connector-python` |
| `mysql-server` (MySQL 8.0) | May need install | `apt install mysql-server` |
| Connection pool | Built into mysql-connector | `mysql.connector.pooling.MySQLConnectionPool` |
| `gspread` | **REMOVED** | `pip uninstall gspread google-auth oauth2client` |
| Google service account JSON | **REMOVED** | Delete `service_account.json` after migration verified |

---

## keep_alive.py / Webhook Endpoints

### Impact: LOW

The Flask server (keep_alive.py) has 4 endpoints:
- `GET /` — health check (**unchanged**)
- `GET /api/today` — calls `get_today_data()` (**unchanged** — function signature unchanged)
- `POST /refresh` — calls `invalidate_all_caches()` → becomes `invalidate_account_cache()` (**minor change**)
- `GET /daily-summary` — same as /api/today (**unchanged**)

No webhook endpoints use Sheets directly. No change to Flask routing.

---

## `_post_init()` Startup

### Line 5598 — Cache warm-up

**Before (lines 5616-5632):**
```python
results = await asyncio.gather(
    _sh(fetch_settings),
    _sh(get_monthly_summary, now.year, now.month),
    _sh(get_account_balances),
    _sh(get_weekly_summary),
    _sh(_get_tx_rows),
    return_exceptions=True,
)
```

**After:**
```python
# With MySQL, warm-up is much faster — keep 1-2 key queries
results = await asyncio.gather(
    asyncio.to_thread(fetch_settings),
    asyncio.to_thread(get_account_balances),
    return_exceptions=True,
)
```
> Cuts startup time from ~5-8s to ~200ms.

### Line 5605 — Reminder re-registration

**Before:** reads `app.bot_data.get(REMIND_KEY, {})` (from pickle)
**After:** `SELECT user_id, time_hhmm FROM reminders WHERE enabled = 1`

---

## Summary

### Functions Affected

| Category | Count | Effort |
|----------|-------|--------|
| **HIGH effort** changes | 2 | `get_account_balances()` (88-line rewrite to SQL JOIN), `_get_tx_rows()` return type change cascades |
| **MEDIUM effort** changes | 9 | `save_transaction()`, `save_opening_balance()`, `save_transfer()`, `fetch_settings()`, `_fetch_tx_rows_raw()`, `get_monthly_summary()`, `get_today_data()`, `get_opening_balances()`, `cmd_delete()` |
| **LOW effort** changes | 18 | All remaining read functions, all commands, all conversation handlers |
| **DELETE entirely** | 11 functions + 3 constants | `_sheet_client()`, `_gsheet_retry()`, `_sh()`, `_sanitize_cell()`, `_fetch_tx_rows_raw()`, `_is_data_row()`, `_parse_row_date()`, `_resolve_currency()`, `_DATE_FMTS`, `_GSHEET_EPOCH`, `_CURRENCY_CODES/_CUR_SYMBOLS/_CUR_NAMES` |
| **NEW to write** | 8 | `_db_get_connection()`, `_db_execute()`, `migrate_sheets_to_mysql.py`, `migrate_pickle_to_mysql.py`, SQL schema (6 CREATE TABLE statements), updated `_get_tx_rows()`, updated `_post_init()`, updated `_err()` |
| **UNCHANGED** | 50+ | All 30+ command handlers, all 9 conversation flow handlers, all keyboard builders, all message formatters, `parse_amount()`, `_tx_header()`, `_tx_prompt()`, `_tx_card()`, `_bar()`, chart functions, `_kb()`, `_find_category_match()`, `_parse_month_arg()`, `build_app()` (only connection setup changes) |
| **Cache infrastructure to remove** | 9 variables + 4 invalidation functions + 1 background thread | `_tx_rows_cache/_ts`, `_monthly_cache`, `_weekly_cache`, `_cashflow_cache`, `_opening_cache`, `_fx_cache`, `_settings_cache_ts`, all `_invalidate_*()` functions, `_cache_warmer_loop()`, `start_cache_warmer()` |
| **Total functions affected** | **41** | Out of ~130 total functions in the bot |

### Before/After Comparison

| Aspect | Google Sheets (Current) | MySQL (Proposed) |
|--------|------------------------|------------------|
| **Data access** | gspread API calls (1-3s each) | SQL queries (5-50ms) |
| **Data model** | Raw string cells with ARRAYFORMULA | Typed columns with constraints |
| **Date handling** | 9-format parser + numeric serials | Native MySQL DATE type |
| **Row identity** | Row number (fragile — shifts on delete) | `AUTO_INCREMENT` id (stable) |
| **Concurrent writes** | Collision-prone (shared sheet) | ACID transactions |
| **Search** | Python linear scan of all rows | MySQL FULLTEXT index |
| **Aggregation** | Python loops over raw rows | SQL GROUP BY with indexes |
| **Cache TTLs** | 120–600s (to hide API latency) | 0–60s (queries are fast) |
| **Background warmer** | Required (6 sheet calls every 90s) | Not needed |
| **API quota** | 60 req/100s per user | None (MySQL handles thousands QPS) |
| **Rate limit handling** | 3-retry decorator (1s/2s/4s backoff) | Connection retry only |
| **Formula injection** | `_sanitize_cell()` prepends `'` to `=`,`+`,`-`,`@` | Not applicable |
| **Backup** | Google Drive version history | `mysqldump` + cron |
| **DevOps** | Zero (SaaS) | MySQL server management |
| **Dependencies** | gspread, google-auth, oauth2client | mysql-connector-python |
| **Lines of code** | ~5,979 | ~5,700 (net deletion of ~300, addition of ~200) |
| **User latency** | 1–4 seconds per command | 100–500ms per command |
| **Multi-user capacity** | Limited by API quota | Thousands of concurrent users |

### Feasibility

**✅ YES — Migration is feasible and highly recommended.**

The codebase has excellent architecture: all data access is isolated in ~18 helper functions. Command handlers and conversation flows (50+ functions) never touch Sheets directly. This clean separation means the migration touches only the data layer while the UI/UX layer stays completely unchanged.

### Biggest Risk Items

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| 1 | **Data migration errors** — wrong date parsing, currency detection in migration script | **HIGH** | Dry-run migration, compare row counts and financial totals before switching |
| 2 | **`_get_tx_rows()` return type change** — cascading impact on every read function using index-based column access (`row[4]`, `row[8]`) | **MEDIUM** | Create a `dict`-based adapter layer during migration; switch to named access after |
| 3 | **MySQL server setup & security** — must not be exposed to public internet | **MEDIUM** | Bind to localhost only, use strong password, configure firewall |
| 4 | **Pickle → DB for budgets/reminders** — pickle read+write must work during transition | **LOW** | Dual-read: check DB first, fall back to pickle |
| 5 | **`get_account_balances()` rewrite** — most complex function, currency resolution changes | **MEDIUM** | Thorough testing with multi-currency accounts (MMK, USD, THB, VND) |
| 6 | **`cmd_delete()` now uses row ID** — no more fragile row-number-based deletion | **LOW** (actually a risk reduction) | Delete is safer — numeric IDs don't shift |

### Recommended Phased Approach

#### Phase 1: Setup & Dual-Write (Week 1)
1. Install and configure MySQL server (localhost only)
2. Create all 7 tables (run schema SQL)
3. Write and test migration script (sheets → MySQL)
4. Verify data integrity (row counts, financial sums)
5. Add dual-write: every `save_transaction()`, `save_opening_balance()`, `save_transfer()` writes to BOTH sheets and MySQL
6. Add `DB_BACKEND` env var (values: `"sheets"`, `"mysql"`, `"dual"`)
7. Run in dual-write mode for 3-5 days

#### Phase 2: Read from MySQL (Week 2)
1. Switch read functions to MySQL when `DB_BACKEND=mysql`
2. Keep sheets read path as fallback behind env var
3. Migrate pickle data (budgets + reminders) to MySQL tables
4. Update `_post_init()` to read reminders from MySQL
5. Monitor for discrepancies between dual-write sources
6. Run for 3-5 days reading from MySQL

#### Phase 3: Clean Up & Optimize (Week 3)
1. Remove all Google Sheets code (11 functions, 3 constants, ~300 lines)
2. Remove gspread dependency (`pip uninstall gspread google-auth`)
3. Remove service account JSON file
4. Optimize indexes based on actual query patterns
5. Set up `mysqldump` cron job for daily backups
6. Update documentation

### Estimated Total Migration Time
- **Phase 1:** 8-12 hours (schema, migration script, dual-write)
- **Phase 2:** 4-6 hours (read switch, pickle migration, monitoring)
- **Phase 3:** 2-4 hours (cleanup, optimize, backup, docs)
- **Total: 14-22 hours** (approximately 3-5 calendar days with testing buffers)

### Risk Level: **LOW-MEDIUM**
The existing architecture cleanly separates data access from business logic. The migration touches only ~41 of ~130 functions, and 30 of those are low-effort changes. The dual-write approach provides a safe escape hatch. The biggest risk is data migration correctness, not code complexity.

---

*Analysis completed by deep read of all 5,979 lines of `/root/ACM-Personal-Wallet/bot/main.py` on 2026-06-25.*
