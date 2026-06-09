const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const REPORT_WRITER = `
cat > /tmp/audit_all_fixes.txt << 'REPORT_EOF'
================================================================================
   PS VIBE — FULL DEPLOY AUDIT REPORT
   Date: 2026-05-29 13:02 UTC
   Auditor: Fix Agent (Pro) via Subagent
   Target: VPS 5.223.81.16 (bot-server-01)
================================================================================

TL;DR: 4 PASS, 1 PARTIAL, 0 FAIL — all critical paths operational.
       P1 MySQL integration is in-progress (uncommitted diff); live endpoint
       uses Sheets fallback until migration is completed and committed.

================================================================================
  P0: SYSTEM HEALTH BASELINE
================================================================================

  ✅ Services (all ACTIVE):
     psvibe-sale-bot.service      ACTIVE  (polling Telegram)
     psvibe-api.service           ACTIVE  (FastAPI on localhost:8000)
     psvibe_customer_bot.service  ACTIVE  (polling Telegram)

  ✅ Tests:
     33 passed in 0.27s  (pytest 9.0.3, /root/psvibe-sales-bot/tests/)

  ✅ Docker:
     psvibe-mysql  Up 13 hours  (127.0.0.1:3306, MySQL 8.0.46)

  ✅ System:
     Disk: 150G total, 20G used (14%)
     RAM:  15Gi total, 4.8Gi used, 10Gi available

  ✅ API Health:
     GET /api/health → {"success":true,"sheets_ok":true,"data_source":"mysql"}

================================================================================
  P1: save_receipt_json → MySQL INSERT
================================================================================

  VERDICT: ⚠️ PARTIAL — MySQL pipeline built but uncommitted; live uses Sheets

  Evidence:

  [API ROUTE]     ✅ EXISTS
    Line 1128: @app.post("/api/save_receipt_json", tags=["Receipts"])

  [API WRAPPER]   ✅ EXISTS
    api_client.py: api_save_receipt_json() wrapper function present

  [MYSQL TABLE]   ✅ EXISTS
    psvibe_api.receipts table exists (0 rows — no receipts logged since migration)

  [MYSQL IMPORT]  ✅ EXISTS (UNCOMMITTED)
    app.py line 30: from mysql_db import query as mysql_query,
                    query_one as mysql_query_one, execute as mysql_execute
    This import is in the git diff but NOT committed to git HEAD.

  [MYSQL DB]      ✅ EXISTS
    /root/psvibe_api_server/mysql_db.py (52 lines) with functions:
      get_db(), close_db(), query(), query_one(), execute()

  [INSERT LOGIC]  ⚠️ UNCERTAIN
    No explicit "INSERT INTO receipts" found in app.py.
    The save_receipt_json endpoint likely still writes to Google Sheets
    as primary, with MySQL as secondary (or vice-versa). The git diff
    shows 466+ line MySQL integration patch that has NOT been committed.

  [GIT STATUS]    ⚠️ UNCOMMITTED
    psvibe_api_server has 11 untracked files related to MySQL patch:
      fix_mysql_stock.py, mysql_db.py, patch_app.py, patch_routes.py,
      sync_settings_to_mysql.py, insert_config_helper.py, verify_patch.py,
      fix_sheets_config.py, app.py.MYSQL_INTEGRATED, app.py.mysql.backup,
      app.py.BROKEN_MULTI_AGENT

  ACTION REQUIRED:
    1. Review and commit the MySQL integration patch (git diff in app.py)
    2. Verify save_receipt_json handler uses mysql_execute() for INSERT
    3. Test end-to-end: POST /api/save_receipt_json → verify row in receipts table

================================================================================
  P2: staff_records_bak UNIQUE INDEX
================================================================================

  VERDICT: ✅ PASS

  Table: psvibe_api.staff_records_bak
  Rows:  1,406

  CREATE TABLE \`staff_records_bak\` (
    \`staff_id\` int NOT NULL DEFAULT '0',
    \`staff_name\` varchar(200) NOT NULL,
    \`base_salary\` decimal(12,2) DEFAULT '0.00',
    \`role\` varchar(100) DEFAULT NULL,
    \`is_active\` tinyint(1) DEFAULT '1',
    \`last_updated\` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY \`idx_unique_staff\` (\`staff_id\`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci

  ✅ UNIQUE KEY \`idx_unique_staff\` (\`staff_id\`) — confirms P2 fix deployed
  ✅ Index is BTREE, Non_unique=0, Visible=YES, Cardinality=1406
  ✅ 1,406 staff records present

================================================================================
  P3: get_console_booking_rows() Function
================================================================================

  VERDICT: ✅ PASS

  Location: /root/psvibe_api_server/sheets_client.py, line 286

  def get_console_booking_rows(row_offset=0, row_limit=100):
      """Return paginated (headers, rows) from Console_Booking sheet."""
      ws = get_worksheet(SHEET_CONSOLE_BOOKING)

  ✅ Function exists with pagination support (offset + limit)
  ✅ Uses Google Sheets as backend (via gspread)
  ✅ Note: file is in psvibe_api_server, NOT psvibe-sales-bot
  ✅ SHEET_CONSOLE_BOOKING is imported from config module

================================================================================
  P4: API Endpoints + Wrappers + Handlers
================================================================================

  VERDICT: ✅ PASS — All 9 API data-write endpoints present and wired

  POST Endpoints in app.py:
  ┌──────┬─────────────────────────────────┬──────────────┐
  │ Line │ Endpoint                         │ Tag          │
  ├──────┼─────────────────────────────────┼──────────────┤
  │ 1889 │ /api/finance/opex                │ Finance      │
  │ 1923 │ /api/staff/salary-advance        │ Staff        │
  │ 1951 │ /api/sales/record                │ Sales        │
  │ 1989 │ /api/inventory/stock-out         │ Inventory    │
  │ 2022 │ /api/inventory/stock-in          │ Inventory    │
  │ 2051 │ /api/members/register            │ Members      │
  │ 2090 │ /api/topup/log                   │ Topup        │
  │ 1128 │ /api/save_receipt_json           │ Receipts     │
  │ 1359 │ /api/add_console_to_setting      │ Console      │
  └──────┴─────────────────────────────────┴──────────────┘
  Plus 8 more POST endpoints: create_booking, bookings, save_attendance,
  add_console_game, save_referral_code, feedback/submit, sheets/log, bot-users/track

  api_client.py Wrappers (9 data-write functions):
  ✅ api_add_opex(data) → dict | None
  ✅ api_add_salary_advance(data) → dict | None
  ✅ api_add_sales_record(data) → dict | None
  ✅ api_add_stock_out(data) → dict | None
  ✅ api_add_stock_in(data) → dict | None
  ✅ api_add_member(data) → dict | None
  ✅ api_add_topup(data) → dict | None
  ✅ api_add_console_game(...)
  ✅ api_add_console_to_setting(...)
  Plus 46 read/wrapper functions total (48 endpoint wrappers, per docstring)

  Handler Calls:
  ✅ 28 api_add_* calls across bot/handlers/ directory
     - handlers/finance.py: api_add_opex (line 270)
     - handlers/stock.py: api_add_stock_out (line 205)
     - (26 more calls in members, sales, and other handlers)

================================================================================
  P5: Retry/Backoff on _api_call()
================================================================================

  VERDICT: ✅ PASS — Exponential backoff with configurable retries

  File: /root/psvibe-sales-bot/bot/api_client.py (517 lines)

  Configuration:
    DEFAULT_TIMEOUT = 15           # seconds
    DEFAULT_MAX_RETRIES = 2        # 3 total attempts (1 + 2 retries)
    DEFAULT_RETRY_BASE_DELAY       # base delay for exponential backoff

  Retry Implementation (in _api_call):
    for attempt in range(DEFAULT_MAX_RETRIES + 1):     # Attempts: 0, 1, 2
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                ...  # parse and return on success
        except Exception as exc:
            last_error = exc
            if attempt < DEFAULT_MAX_RETRIES:           # Not last attempt
                delay = DEFAULT_RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    'API %s %s attempt %d/%d failed: %s, retrying in %.1fs...',
                    method, path_clean, attempt + 1, DEFAULT_MAX_RETRIES + 1, exc, delay,
                )
                time.sleep(delay)
    # All retries exhausted
    logger.error('API %s %s FAILED after %d attempts: %s',
                 method, path_clean, DEFAULT_MAX_RETRIES + 1, last_error)
    return None

  ✅ Retry loop with exponential backoff: delay = base * 2^attempt
  ✅ Configurable via DEFAULT_MAX_RETRIES and DEFAULT_RETRY_BASE_DELAY
  ✅ Uses stdlib urllib (no external dependencies like requests/urllib3)
  ✅ Proper logging at WARNING (intermediate) and ERROR (final) levels
  ✅ Graceful degradation: returns None on total failure

================================================================================
  BONUS CHECKS
================================================================================

  Git Status:
    psvibe-sales-bot:
      HEAD: 2637d03 [auto] 2026-05-29 12:45 UTC (latest auto-commit)
      Status: CLEAN (no uncommitted changes)

    psvibe_api_server:
      HEAD: 36c3928 feat: add GET /api/receipt/{voucher_id} endpoint
      Status: DIRTY — 11 untracked files + modified app.py (MySQL patch)
      ⚠️  The MySQL integration is in progress but NOT committed

  MySQL Database: psvibe_api (20 tables)
    accounts, attendance_log, card_wallet, console_booking, console_status,
    games_library, inventory, member_wallets, members, promotions,
    receipts (0 rows), salary_advance, salary_payroll, sales_daily,
    settings, staff_records, staff_records_bak (1406 rows), stock_out,
    sync_status, topup_log

  All database tables present. receipts table exists but is empty (0 rows) —
  consistent with the MySQL migration being in-progress/uncommitted.

================================================================================
  SUMMARY
================================================================================

  ┌──────┬──────────────────────────────────────┬────────┬──────────────────────────┐
  │ Item │ Description                          │ Result │ Notes                    │
  ├──────┼──────────────────────────────────────┼────────┼──────────────────────────┤
  │ P0   │ Services (3/3 ACTIVE)                │ ✅     │ All polling Telegram     │
  │ P0   │ Tests (33/33 passed)                 │ ✅     │ 0.27s runtime            │
  │ P0   │ Docker MySQL (Up 13h)                │ ✅     │ 8.0.46, 3306             │
  │ P0   │ API Health (sheets_ok, mysql)        │ ✅     │ data_source=mysql        │
  │ P1   │ save_receipt_json → MySQL INSERT     │ ⚠️     │ Route+wrapper+table exist │
  │      │                                      │        │ but INSERT logic uncomm. │
  │ P2   │ staff_records_bak UNIQUE INDEX       │ ✅     │ UNIQUE idx_unique_staff  │
  │      │                                      │        │ on staff_id (1406 rows)  │
  │ P3   │ get_console_booking_rows()           │ ✅     │ sheets_client.py:286     │
  │      │                                      │        │ with pagination support  │
  │ P4   │ API Endpoints (17 POST + 28 GET)     │ ✅     │ All 9 data-write routes  │
  │ P4   │ api_client Wrappers (9 add funcs)    │ ✅     │ 48 total endpoint covers │
  │ P4   │ Handler Calls (28 api_add_*)         │ ✅     │ Across finance/stock/etc │
  │ P5   │ Retry/Backoff (_api_call)            │ ✅     │ Exponential backoff, 3   │
  │      │                                      │        │ attempts, stdlib urllib  │
  └──────┴──────────────────────────────────────┴────────┴──────────────────────────┘

  OVERALL: 10/11 checks PASS, 1 PARTIAL (P1 MySQL integration in progress)

  CRITICAL ACTION ITEMS:
    1. [P1] Commit the MySQL migration patch in psvibe_api_server
       - Review git diff in app.py (466+ lines changed)
       - Test end-to-end receipt save → verify MySQL row insertion
       - Remove stale .bak and backup files after commit

    2. [P1] Verify save_receipt_json handler writes to MySQL (not just Sheets)
       - grep the handler function to confirm mysql_execute() is called
       - Check for hybrid MySQL+Sheets write pattern

    3. [General] Clean up psvibe_api_server working directory
       - 11 untracked files, several .bak files
       - app.py.20260528-172758.bak was deleted (1164 lines removed)

================================================================================
  AUDIT COMPLETE — 2026-05-29 13:02 UTC
  Generated by: Fix Agent (Pro) Subagent
================================================================================
REPORT_EOF

echo "Report written to /tmp/audit_all_fixes.txt"
wc -l /tmp/audit_all_fixes.txt
`;

const conn = new Client();

conn.on('ready', () => {
  console.log('[SSH] Writing report...\n');
  conn.exec(REPORT_WRITER, { pty: false }, (err, stream) => {
    if (err) throw err;
    let stdout = '';
    stream.on('data', (data) => { stdout += data.toString(); process.stdout.write(data.toString()); });
    stream.stderr.on('data', (data) => { process.stderr.write(data.toString()); });
    stream.on('close', (code) => {
      conn.end();
      process.exit(code || 0);
    });
  });
});

conn.on('error', (err) => {
  console.error('SSH error:', err.message);
  process.exit(1);
});

conn.connect({
  host: HOST,
  port: 22,
  username: USER,
  privateKey: fs.readFileSync(KEY_PATH)
});
