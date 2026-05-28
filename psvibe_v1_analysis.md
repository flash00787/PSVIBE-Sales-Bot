# PS VIBE Sales Bot — V1 Logic Analysis & API Audit

**Date:** 2026-05-27  
**V1 Path:** `/root/staging/monolithic_ref/main.py` (12,249 lines)  
**V2 Path:** `/root/staging/bot_src/` (modularized)  
**Status:** ✅ V1 imports successfully with all functions accessible

---

## 1. V1 Can Run Successfully?

**Yes — with caveats.** The module imports cleanly without errors. All top-level functions are accessible. However, full runtime requires:
- Valid `BOT_TOKEN` (Telegram Bot API)
- Valid Google Sheets credentials (`service_account.json`)
- Valid `SHEET_ID` environment variable
- Optional: `API_BASE_URL` + `API_KEY` for the Replit-compat API server
- Optional: `N8N_SESSION_WEBHOOK` / `N8N_BOOKING_WEBHOOK` for reminder scheduling

The `__name__ == "__main__"` block (line 12169) implements:
1. Kill all duplicate `python3 main.py` processes
2. Write PID lock to `/tmp/ps_vibe_bot.lock`
3. SIGTERM handler for clean shutdown
4. Start `keep_alive()` server (if available)
5. Infinite restart loop: `while True: main()` with 5s crash delay

---

## 2. All Top-Level Functions (V1)

> **262 functions** exported from `main.py`. Grouped by domain:

### Core Bot Setup
`main`, `error_handler`, `today_str`, `now_mmt`, `step_hdr`, `calc_duration`

### Main Menu
`show_main_menu`, `step_main_menu`, `show_admin_menu`

### Daily Sales Flow (7-step wizard)
`prompt_staff_select`, `step_staff_select`, `prompt_member`, `step_member`, `prompt_console`, `step_console`, `prompt_mins`, `step_mins`, `prompt_food_menu`, `step_food_menu`, `step_food_qty`, `prompt_confirm`, `step_confirm`, `step_sale_confirm`, `prompt_kpay`, `step_kpay`, `prompt_discount`, `step_discount`, `prompt_session_shortfall`, `step_session_shortfall`

### Member Management
`cmd_member_mgmt`, `show_mm_menu`, `step_mm_menu`, `prompt_mm_lookup`, `step_mm_lookup`, `cmd_newmember`, `prompt_nm_name`, `step_nm_name`, `prompt_nm_phone`, `step_nm_phone`, `prompt_nm_email`, `step_nm_email`, `prompt_nm_id`, `step_nm_id`, `prompt_nm_amt`, `step_nm_amt`, `prompt_nm_kpay`, `step_nm_kpay`, `prompt_nm_staff`, `step_nm_staff`, `step_nm_gift_pin`, `step_nm_confirm`, `cmd_topup`, `prompt_tu_member`, `step_tu_member`, `prompt_tu_amt`, `step_tu_amt`, `prompt_tu_kpay`, `step_tu_kpay`, `prompt_tu_confirm`, `step_tu_confirm`, `cmd_check_member`, `cmd_ranks`

### Google Sheets Data Fetchers
`fetch_members`, `fetch_member_data`, `fetch_member_phone`, `fetch_member_tier`, `fetch_member_total_spend`, `fetch_member_effective_rate`, `update_member_effective_rate`, `fetch_member_rank_from_sheet`, `fetch_wallet_mins`, `fetch_balance_mins`, `fetch_base_rate`, `fetch_new_member_defaults`, `fetch_rank_thresholds`, `fetch_rank_table_display`, `fetch_alltime_effective_rate`, `fetch_bonus_table`, `fetch_staff`, `fetch_base_salaries`, `fetch_attendance`, `fetch_games`, `fetch_game_library`, `fetch_console_games`, `fetch_console_status`, `fetch_console_multiplier`, `fetch_food_prices`, `fetch_food_costs`, `fetch_salary_advances`, `get_member_rank`, `display_rank`, `rank_emoji`, `build_member_rate_dict`, `build_rank_bonus_lines`, `get_bonus_mins`, `get_top_up_suggestion`, `ensure_sheet_headers`, `next_voucher`, `next_member_row_no`, `next_write_row`, `next_member_id`

### Console Management
`show_console_menu`, `step_console_menu`, `add_console_to_setting`, `remove_console_from_setting`, `get_consoles_from_setting`, `add_console_game`, `remove_console_game`, `delete_console_game`, `update_game_library_install`, `set_game_disc_count`, `get_console_games_sh`, `get_games_on_console`, `get_consoles_with_game`, `get_game_lib_sh`

### Console Booking
`cmd_staff_book_hub`, `cmd_staff_booking`, `cmd_confirmed_bookings`, `cmd_admin_bookings`, `cmd_approve_booking`, `cmd_reject_booking`, `create_booking`, `end_booking`, `cancel_booking`, `cb_booking_mgmt`, `cb_cancel_booking`, `cb_cancel_with_reason`, `cb_extend_timer`

### Session Management (Console-Game Install, SSD)
`launch_session_sale`, `prompt_end_session`, `step_end_session`, `step_session_shortfall`, `step_ds_member_in_session`, `step_ds_console_in_session`, `step_book_dup_warn`, `prompt_book_console`, `step_book_console`, `prompt_book_member`, `step_book_member`, `prompt_book_game`, `step_book_game`, `prompt_book_mins`, `step_book_mins`, `prompt_game_change_cons`, `step_game_change_cons`, `step_game_change_game`

### Game Library
`show_game_menu`, `step_game_menu`, `step_game_add_title`, `step_game_add_platform`, `step_game_add_genre`, `step_game_add_status`, `step_game_del_select`

### Console-Game Install
`show_ginst_menu`, `step_ginst_menu`, `step_ginst_add_cons`, `step_ginst_add_game`, `step_ginst_add_type`, `step_ginst_del_cons`, `step_ginst_del_game`, `step_ginst_view_cons`

### External SSD Management
`show_ssd_menu`, `step_ssd_menu`, `step_ssd_view`, `step_ssd_add_ssd`, `step_ssd_add_game`, `step_ssd_add_type`, `step_ssd_del_ssd`, `step_ssd_del_game`, `step_ssd_xfer_ssd`, `step_ssd_xfer_game`, `step_ssd_xfer_cons`, `step_ssd_ret_cons`, `step_ssd_ret_game`

### Stock/Inventory
`cmd_stock_menu`, `cmd_stockin_direct`, `cmd_stockout_direct`, `cmd_inventory`, `cmd_stocktoday`, `show_stock_menu`, `step_stock_menu`, `step_stock_item`, `step_stock_qty`, `step_stock_pin`, `show_si_items`, `step_si_item`, `step_si_qty`, `step_si_cost`, `show_si_cart`, `step_si_cart`, `step_si_pay`, `step_si_pay_split`, `step_si_confirm`, `show_stock_out_items`

### Console CRUD
`show_con_mgmt_menu`, `step_con_mgmt_menu`, `step_con_add_id`, `step_con_add_type`, `step_con_add_mult`, `step_con_del_select`

### Discount
`step_disc_select`, `step_disc_set_qty`

### Finance Module
`cmd_finance`, `cmd_fin_pnl`, `cmd_fin_bs`, `cmd_fin_accts`, `cmd_fin_depr`, `cmd_fin_profit_share`, `cmd_finance_setup`, `show_finance_menu`, `step_finance_menu`, `cmd_financial_report`, `show_fin_report_menu`, `step_fin_report_menu`, `step_opex_cat`, `step_opex_desc`, `step_opex_amt`, `step_opex_acct`, `step_opex_pay`, `step_opex_confirm`, `step_asset_name`, `step_asset_cat`, `step_asset_date`, `step_asset_cost`, `step_asset_qty`, `step_asset_life`, `step_asset_salvage`, `step_asset_pay`, `step_asset_confirm`, `step_asset_dispose_sel`, `step_asset_dispose_date`, `step_asset_dispose_qty`, `step_asset_dispose_proceeds`, `step_asset_dispose_confirm`, `prompt_asset_name`, `prompt_asset_dispose_sel`, `step_prepaid_desc`, `step_prepaid_cat`, `step_prepaid_amt`, `step_prepaid_acct`, `step_prepaid_start`, `step_prepaid_end`, `step_prepaid_confirm`, `prompt_prepaid_desc`, `step_acct_trf_from`, `step_acct_trf_to`, `step_acct_trf_amt`, `step_acct_trf_note`, `step_acct_trf_confirm`, `prompt_acct_trf_from`, `step_pay_vendor`, `step_pay_desc`, `step_pay_amt`, `step_pay_due`, `step_pay_acct`, `step_pay_confirm`, `prompt_pay_vendor`, `step_rec_cust`, `step_rec_desc`, `step_rec_amt`, `step_rec_due`, `step_rec_acct`, `step_rec_confirm`, `prompt_rec_cust`, `step_cap_acct`, `step_cap_amt`, `step_cap_confirm`, `prompt_cap_acct`, `step_share_name`, `step_share_role`, `step_share_cap`, `step_share_own`, `step_share_confirm`, `show_shareholder_menu`, `step_shareholder_menu`, `prompt_share_name`, `step_pay_settle_list`, `step_pay_settle_acct`, `step_pay_settle_confirm`, `show_settle_list`, `step_rec_settle_list`, `step_rec_settle_acct`, `step_rec_settle_confirm`, `show_advpay_settle`, `step_advpay_party`, `step_advpay_desc`, `step_advpay_amt`, `step_advpay_acct`, `step_advpay_due`, `step_advpay_note`, `step_advpay_confirm`, `prompt_advpay_party`, `step_advpay_list`, `step_advpay_settle_confirm`

### Finance Sheet Getters
`get_opex_sh`, `get_assets_sh`, `get_prepaid_fin_sh`, `get_acct_trf_sh`, `get_payables_sh`, `get_receivables_sh`, `get_capital_sh`, `get_salary_adv_sh`, `get_advpay_sh`, `get_booking_sh`, `get_att_sh`, `get_console_games_sh`

### Finance Report Commands
`cmd_fin_pnl`, `cmd_fin_bs`, `cmd_fin_accts`, `cmd_fin_depr`, `cmd_fin_profit_share`, `cmd_finance_setup`, `cmd_financial_report`

### Admin
`cmd_admin`, `step_admin_pin`, `step_admin_menu`, `cmd_broadcast`, `cmd_kpi_cmd`, `cmd_payroll`, `cmd_payroll_cmd`, `cmd_setattend`, `cmd_setattend_cmd`, `cmd_today_report`, `cmd_version`, `cmd_help`, `cmd_cancel`, `cmd_finance`, `cmd_admin_bookings`, `cmd_admin_cashflow`, `cmd_admin_liability`, `cmd_admin_pnl`, `cmd_admin_sal_adv`, `cmd_sales_direct`, `cmd_topup`

### KPI / Payroll
`cmd_kpi_cmd`, `cmd_payroll_cmd`, `calc_monthly_payroll`, `calc_monthly_pnl`, `fetch_alltime_effective_rate`, `fetch_attendance`, `fetch_bonus_table`, `fetch_staff`, `fetch_base_salaries`

### Receipt System
`save_receipt_json`, `get_receipt_url`, `get_receipt_kb`, `RECEIPTS_DIR`

### Replit API (Internal)
`_replit_get`, `_replit_post`, `_replit_patch`, `_api_base`

---

## 3. Replit API References Found

The "Replit API" is actually a **custom Node.js Express API server** (`api_server.js`) that was originally built on Replit and now runs on the VPS. It acts as a caching proxy between the Telegram bot and Google Sheets.

### Key API Functions (V1 main.py)

| Line | Function | Endpoint Pattern | Purpose |
|------|----------|-----------------|---------|
| 8309 | `_replit_get(path)` | `{API_BASE_URL}/api/{path}` | GET with X-API-Key auth, 30s timeout |
| 8324 | `_replit_patch(path, body)` | `{API_BASE_URL}/api/{path}` | PATCH (JSON body), returns dict even on 409 |
| 8355 | `_replit_post(path, body)` | `{API_BASE_URL}/api/{path}` | POST (JSON body), 30s timeout |
| 1408 | `_api_base()` | — | Reads `API_BASE_URL` env var, strips trailing `/` |
| 1422 | `save_receipt_json()` | `{base}/api/receipt` | POST receipt data with `x-receipt-secret` + `X-API-Key` |

### All API Call Sites

```
Line 961:   _replit_get("sheets/config")          — Config/console data
Line 3169:  _replit_get("sheets/inventory")       — Inventory levels
Line 3461:  _replit_get("sheets/inventory?nocache=1")
Line 3474:  _replit_post("waitlist/notify")       — Waitlist notification
Line 6350:  _replit_get("finance/pnl?m=...")      — Monthly P&L
Line 6417:  _replit_get("finance/balance-sheet")  — Balance sheet
Line 6462:  _replit_get("finance/accounts")       — Chart of accounts
Line 6493:  _replit_get("finance/depreciation?year=...")
Line 6519:  _replit_get("finance/profit-sharing?m=...")
Line 6564:  _replit_post("finance/setup-sheets")  — Initialize finance sheets
Line 7072:  _replit_get("sheets/pnl")             — P&L sheet data
Line 7148:  _replit_get("sheets/pnl")
Line 7223:  _replit_get("sheets/liability")       — Card liability
Line 7224:  _replit_get("sheets/pnl")
Line 7292:  _replit_get("sheets/consoles")        — Console status
Line 7340:  _replit_get("bookings?status=pending")
Line 7341:  _replit_get("bookings?status=confirmed")
Line 7389:  _replit_get("bookings?status=confirmed")
Line 7732:  _replit_post("bookings", payload)     — Create booking
Line 7769:  N8N_BOOKING_WEBHOOK (n8n)            — Booking reminder via n8n
Line 7888:  _replit_get(f"bookings?memberId=...")
Line 7929:  _replit_get("bookings?status=pending")
Line 8021:  _replit_get(f"bookings/{bk_id}")
Line 8027:  _replit_get("sheets/consoles")
Line 8067:  _replit_patch — patch booking status
Line 8399:  _replit_get("sheets/inventory")       — cmd_inventory
Line 8433:  _replit_get("sheets/stock-today")     — cmd_stocktoday
Line 8455:  _replit_get("sheets/report-data")     — Today's report
Line 8485:  _replit_get("sheets/staff-breakdown") — Staff KPI
Line 8535:  _replit_get("sheets/weekly-report")   — Weekly report
Line 8622:  _replit_get("bookings/broadcast-targets")
Line 8665:  _replit_get("sheets/report-data")     — Report repeat
Line 8686:  _replit_get("sheets/staff-breakdown") — Staff KPI repeat
Line 8734:  _replit_get("sheets/consoles")        — Console status repeat
Line 9208:  N8N_SESSION_WEBHOOK POST              — Session timer reminder
```

### API Server (api_server.js) — VPS-ported from Replit

**Location:** `/root/Sales-Tele-Bot/api_server/api_server.js`  
**Stack:** Express.js on VPS (was Flask/Express on Replit)  
**Key endpoints served:**
- `GET /api/sheets/config` → `fetchConfigData()`
- `GET /api/sheets/inventory` → `fetchInventoryData()`
- `GET /api/sheets/summary` → `fetchSummaryData()`
- `GET /api/sheets/stock-today` → `fetchStockTodayData()`
- `GET /api/sheets/report-data` → `[summary, stockToday, inventory]`
- `GET /api/sheets/staff-breakdown` → `fetchStaffBreakdownData()`
- `GET /api/sheets/consoles` → `fetchConsolesData()`
- `GET /api/sheets/pnl?m=YYYY-MM`
- `GET /api/finance/balance-sheet`
- `GET /api/finance/accounts`
- `GET /api/finance/depreciation?year=YYYY`
- `GET /api/finance/profit-sharing?m=YYYY-MM`
- `GET /api/bookings`
- `POST /api/bookings`
- `PATCH /api/bookings/:id`
- `POST /api/receipt` (with x-receipt-secret)
- `GET /api/receipt/:id`
- `POST /api/sheets/pnl/calculate`
- `POST /api/finance/setup-sheets`
- `GET /api/bookings/broadcast-targets`
- `GET /api/promotions/*`
- `GET /api/my-bookings?memberId=...`

The API server uses file-based locking (`_withBkLock`) for booking concurrency and Google Sheets API direct calls (via `googleapis`).

---

## 4. API_BASE_URL Usage Pattern

```python
# Line 1408
def _api_base() -> str:
    return os.environ.get("API_BASE_URL", "").rstrip("/")
```

- Returns empty string if not configured → all API calls return `None` (graceful degradation)
- Used by `_replit_get()`, `_replit_post()`, `_replit_patch()`, `save_receipt_json()`, `get_receipt_url()`
- **Pattern:** All API access is optional — the bot can run without the API server (falls back to direct Google Sheets for some functions)
- API calls use `urllib.request` (stdlib), no external HTTP libraries

---

## 5. keep_alive Usage

```python
# Line 68-70 (V1 main.py)
try:
    from keep_alive import keep_alive
except ImportError:
    keep_alive = None

# Line 12231-12232 (V1 __name__ == "__main__")
if keep_alive:
    keep_alive()
```

The `keep_alive` module is a **Flask/HTTP server** that keeps the bot alive on Replit's free-tier hosting. On VPS:
- V1: Imported optionally; if it fails, `keep_alive = None` (bot still runs)
- V2: Same pattern — `from bot import keep_alive` in V2 `main.py`; `keep_alive()` called at startup
- **Not needed on VPS** (already has persistent hosting), but kept for compatibility

---

## 6. Google Sheets Column Mapping

### Sheet: Card_Wallet (member_sh)
- **Purpose:** Member database — wallet balances, rates, contact info
- **Columns (inferred from fetchers):**
  - A: Row #
  - B: Member ID (e.g., PSV_A_001)
  - C: Name
  - D: Phone
  - E: Email
  - F: Total Spend (cumulative)
  - G: Current Balance (wallet mins)
  - H: Effective Rate (calculated from spend/tier)
  - I: Rank/Tier
  - J: Referral Code
  - K: KPay number
  - L: Signup Date (by staff)

### Sheet: Sales_Daily (sales_sh)
- **Purpose:** Daily sales records (every transaction)
- **Columns (inferred):**
  - A: Voucher # (date-based)
  - B: Date (MM/DD/YYYY)
  - C: Staff
  - D: Member ID
  - E: Console ID
  - F: Duration (mins)
  - G: Game
  - H: Food items & qty
  - I: Subtotal
  - J: Discount
  - K: Final Amount
  - L: KPay Amount
  - M: Cash Amount
  - N: Wallet Deduct (mins)
  - O: Notes

### Sheet: Setting (setting_sh)
- **Purpose:** Configuration & console multipliers
- **Columns (inferred):**
  - A: Staff list (names or IDs)
  - B: Food prices (item → price mappings)
  - C: Base rate (default Ks/min)
  - D: New member defaults
  - E-F: Bonus table
  - G: Rank thresholds
  - H: Console IDs (column 8)
  - I: Console Types (column 9 — PS5/PS4/etc)
  - J: Console Multipliers (column 10)
  - K: Allowed staff IDs (auth whitelist)
  - L: Stock access PIN

### Sheet: Stock_Out (stock_sh)
- **Purpose:** Items taken from inventory (sales consumption)
- Columns: Date, Item, Qty, Staff, Notes

### Sheet: Stock_In (stock_in_sh)
- **Purpose:** Items purchased/restocked
- Columns: Date, Item, Qty, Unit Cost, Total Cost, Payment Method, Notes

### Sheet: TopUp_Log (topup_sh)
- **Purpose:** Member wallet top-up history
- Columns: Date, Member ID, Amount, KPay Ref, Notes

### Sheet: Inventory (inv_sh)
- **Purpose:** Current stock levels with valuation
- Columns: Item, Category, Qty, Unit, Unit Cost, Inventory Value (col G), Total Value (K1), Last Updated (L1)

### Sheet: Attendance_Log (get_att_sh)
- **Purpose:** Staff attendance tracking
- Created dynamically if missing
- Columns: Month, Staff, Leave_Days, Late_Count, Late_Deduct_Ks

### Sheet: Console_Booking (get_booking_sh)
- **Purpose:** Console reservation/booking system
- Created dynamically if missing
- Columns: BookingID, Date, ConsoleID, MemberID, StartTime, EndTime, Status, Staff, Notes

---

## 7. Conversation States Defined

**V1 defines 167 states** (`range(167)`, line 818):

### State Groups:
1. **Main Menu (1):** MAIN_MENU (0)
2. **Daily Sales Flow (8):** MEMBER, CONSOLE, MINS, FOOD_MENU, FOOD_QTY, CONFIRM_SUMMARY, DISCOUNT, KPAY_AMT, SALE_CONFIRM
3. **Member Management (1+2):** MM_MENU, MM_LOOKUP
4. **First Purchase/New Member (9):** NM_NAME, NM_PHONE, NM_EMAIL, NM_ID, NM_AMT, NM_KPAY, NM_CONFIRM, NM_GIFT_PIN, NM_STAFF
5. **Top Up (4):** TU_MEMBER, TU_AMT, TU_KPAY, TU_CONFIRM
6. **Stock (6):** STOCK_PIN, STOCK_MENU, STOCK_ITEM, STOCK_QTY, STAFF_SELECT
7. **Stock In/Restock (7):** SI_ITEM, SI_QTY, SI_COST, SI_CART, SI_PAY, SI_PAY_SPLIT, SI_CONFIRM
8. **Attendance (4):** ATTEND_STAFF, ATTEND_LEAVE, ATTEND_LATE, ATTEND_DEDUCT
9. **Admin (2):** ADMIN_PIN, ADMIN_MENU
10. **Salary Advance (4):** SAL_ADV_STAFF, SAL_ADV_AMT, SAL_ADV_PAY, SAL_ADV_CONFIRM
11. **Console Booking (2+3):** BOOK_CONSOLE, BOOK_MEMBER, BOOK_DUP_WARN, BOOK_GAME, BOOK_MINS
12. **Console (3):** CONSOLE_MENU, END_SESSION_SELECT, CON_MGMT_MENU (+ CON_ADD_ID, CON_ADD_TYPE, CON_ADD_MULT, CON_DEL_SELECT)
13. **Game Library (5):** GAME_MENU, GAME_ADD_TITLE, GAME_ADD_PLATFORM, GAME_ADD_GENRE, GAME_ADD_STATUS, GAME_DEL_SELECT
14. **Console-Game Install (8):** GINST_MENU, GINST_VIEW_CONS, GINST_ADD_CONS, GINST_ADD_GAME, GINST_ADD_TYPE, GINST_DEL_CONS, GINST_DEL_GAME
15. **SSD Management (13):** SSD_MENU, SSD_VIEW_SSD, SSD_ADD_SSD, SSD_ADD_GAME, SSD_ADD_TYPE, SSD_DEL_SSD, SSD_DEL_GAME, SSD_XFER_SSD, SSD_XFER_GAME, SSD_XFER_CONS, SSD_RET_CONS, SSD_RET_GAME
16. **Discount (2):** DISC_SELECT, DISC_SET_QTY
17. **Session Bridge (3):** SESSION_SHORTFALL, DS_MEMBER_IN_SESSION, DS_CONSOLE_IN_SESSION
18. **Game Change (2):** GAME_CHANGE_CONS, GAME_CHANGE_GAME
19. **Staff Booking/Advance (7):** SBK_CONSOLE, SBK_CUST_NAME, SBK_DATE, SBK_TIME, SBK_DUR, SBK_GAME, SBK_CONFIRM
20. **Finance Module (20+):** FINANCE_MENU, OPEX_CAT, OPEX_DESC, OPEX_AMT, OPEX_ACCT, OPEX_PAY, OPEX_CONFIRM, ASSET_NAME, ASSET_CAT, ASSET_DATE, ASSET_COST, ASSET_QTY, ASSET_LIFE, ASSET_SALVAGE, ASSET_PAY, ASSET_CONFIRM, ASSET_DISPOSE_SEL, ASSET_DISPOSE_DATE, ASSET_DISPOSE_QTY, ASSET_DISPOSE_PROCEEDS, ASSET_DISPOSE_CONFIRM, PREPAID_DESC, PREPAID_CAT, PREPAID_AMT, PREPAID_ACCT, PREPAID_START, PREPAID_END, PREPAID_CONFIRM, ACCT_TRF_FROM, ACCT_TRF_TO, ACCT_TRF_AMT, ACCT_TRF_NOTE, ACCT_TRF_CONFIRM, PAY_VENDOR, PAY_DESC, PAY_AMT, PAY_DUE, PAY_ACCT, PAY_CONFIRM, REC_CUST, REC_DESC, REC_AMT, REC_DUE, REC_ACCT, REC_CONFIRM, FIN_REPORT_MENU
21. **Capital/Shareholders (7):** CAP_ACCT, CAP_AMT, CAP_CONFIRM, SHARE_NAME, SHARE_ROLE, SHARE_CAP, SHARE_OWN, SHARE_CONFIRM
22. **Settle Flows (6):** PAY_SETTLE_LIST, PAY_SETTLE_ACCT, PAY_SETTLE_CONFIRM, REC_SETTLE_LIST, REC_SETTLE_ACCT, REC_SETTLE_CONFIRM
23. **Advance Payment (8):** ADVPAY_PARTY, ADVPAY_DESC, ADVPAY_AMT, ADVPAY_ACCT, ADVPAY_DUE, ADVPAY_NOTE, ADVPAY_CONFIRM, ADVPAY_LIST, ADVPAY_SETTLE_CONFIRM

### V2 New States (NOT in V1):
- `NM_REFERRAL` — New member referral step
- `BOOK_LINK` — Booking link generation
- `PROMO_SELECT` — Promotion selection
- `BUNDLE_FOC` — Bundle/FOC handling
- `REFERRAL_CODE` — Referral code assignment
- `GAME_EDIT_SELECT`, `GAME_EDIT_FIELD`, `GAME_EDIT_VALUE` — Edit existing games
- `ADJUST_TIME` — Time adjustment for sessions
- `WL_MENU` — Waitlist management menu
- `BTN_SBK_WAITLIST` — Staff booking waitlist option

---

## 8. Sqlite DB Status in V2

**Location:** `/root/staging/bot_src/sqlite/`  
**Status:** ✅ Fully implemented and working  

### Files:
| File | Size | Purpose |
|------|------|---------|
| `db_manager.py` | 22 KB | Core DB class (`PSVibeDB`) — thread-safe with WAL mode |
| `schema.sql` | 10.5 KB | Full DDL for all tables |
| `setup.py` | 19.8 KB | Schema creation + Google Sheets data import |
| `cron_wrapper.sh` | 492 B | Cron job wrapper |
| `sync_cron.sh` | 5.5 KB | Sync script (cron-driven) |
| `sync.log` | 16 KB | Recent sync activity |

### 15 Database Tables (schema.sql):
1. `members` — Cached member data from Card_Wallet
2. `bookings` — Console booking records
3. `sales` — Sales transaction records
4. `topups` — Wallet top-up history
5. `settings` — Configuration key-value pairs
6. `consoles` — Console inventory
7. `console_games` — Game installs per console
8. `game_library` — Master game catalog
9. `game_console_map` — Many-to-many mapping
10. `stock_out` — Stock consumption records
11. `inventory` — Current stock levels
12. `staff` — Staff roster
13. `attendance` — Staff attendance records
14. `sync_log` — Synchronization audit trail
15. `cache_meta` — Cache freshness/version metadata

### Key Features:
- **Thread-local connections** with `threading.local()` for 10+ concurrent users
- **WAL journal mode** for concurrent reads
- **5-second busy timeout** — no lock contention
- **Thread-safe locking** (`threading.Lock()`) for write operations
- Member search with LIKE matching
- Setup imports from Google Sheets directly (via gspread)

---

## 9. V1 vs V2 Key Differences

### Architecture

| Aspect | V1 (monolithic) | V2 (modular) |
|--------|-----------------|--------------|
| Structure | 1 file, 12,249 lines | 30+ files in `bot/` + `bot/handlers/` |
| Main logic | `main.py` = everything | `bot/__init__.py` (2,022 lines) + `bot/handlers/*.py` |
| App setup | Inline in `main.py` | `bot/app.py` (465 lines) |
| Handlers | All inline | Split into 27 handler files |
| States | 167 (`range(167)`) | More (added NM_REFERRAL, BOOK_LINK, WL_MENU, etc.) |

### New V2 Features
1. **Auth Middleware** (app.py line ~40): `_auth_middleware` checks `fetch_allowed_staff_ids()` — blocks unauthorized users at group=-999
2. **Caching Layer** (`_load_cfg`, `_load_members`, `_bg_cache_refresh`): Auto-refreshes config + member data on a background timer
3. **Sqlite Database** — read-mirror for fast access without Sheets API
4. **Promotion System** — `PROMO_SELECT`, `BUNDLE_FOC` states
5. **Referral System** — `NM_REFERRAL`, `REFERRAL_CODE` states
6. **Waitlist Management** — `WL_MENU`, `cmd_waitlist_mgmt`
7. **Game Editing** — `GAME_EDIT_SELECT`, `GAME_EDIT_FIELD`, `GAME_EDIT_VALUE`
8. **BotState enum** — proper enum for user_data keys
9. **Type annotations** — V2 uses `list[dict]` etc., V1 uses raw `list`
10. **V2 bot/__init__.py `__all__`** — massive export list (500+ names) explicitly declaring all public API

### V2 Handler Files (27 files):
```
admin.py (23.6K)      admin_bookings.py (10.6K)  attendance.py (8K)
booking.py (45.9K)     booking_flow.py (34.4K)    broadcast.py (5.8K)
commands.py (1.7K)     console.py (14.7K)         console_mgmt.py (6.7K)
discount.py (19.3K)    finance.py (115.3K!)       games.py (18.4K)
ginst.py (10.9K)       help.py (4K)               main_menu.py (4K)
members.py (49.9K)     notify.py (2.9K)           payroll.py (10K)
referral.py (5.8K)     reports.py (15.6K)         salary_adv.py (5.4K)
sales.py (57.7K)       ssd_disc.py (21.5K)        stock.py (10.2K)
stock_in.py (12.8K)    waitlist.py (12.4K)
```

Total V2 handler code: ~530 KB across 27 files — roughly equivalent to the V1 monolith.

### V1/V2 Identical Components:
- Google Sheets auth & worksheet setup (lines 96-111 in V1 ≈ V2 lines 110-120 in `__init__.py`)
- Retry wrapper pattern (identical: `_sheets_retry`, same retry codes/max/backoff)
- Button labels (identical set with V2 adding new ones)
- State definitions (V2 has same core + adds ~10 new states)
- Entry points in ConversationHandler (identical)
- `__name__ == "__main__"` block (identical — PID lock, duplicate kill, keep_alive, infinite restart loop)

---

## 10. N8N Webhook Integration

**Line 793-797 (V1):**
```python
N8N_SESSION_WEBHOOK  = os.environ.get("N8N_SESSION_WEBHOOK", "")
N8N_BOOKING_WEBHOOK  = os.environ.get("N8N_BOOKING_WEBHOOK", "")
# Test:  https://psvibe.app.n8n.cloud/webhook-test/session-reminder
# Prod:  https://psvibe.app.n8n.cloud/webhook/session-reminder
```

- **Purpose:** n8n webhooks fire session/booking reminders to staff
- **Usage:** `launch_session_sale()` (line ~9208) — POSTs a timer payload; non-blocking fire-and-forget
- **V2:** Same pattern, exported via `__all__` in `bot/__init__.py`

---

## 11. Summary

| Question | Answer |
|----------|--------|
| V1 can run successfully? | ✅ Yes — module imports, all functions accessible |
| Total V1 functions | ~262 top-level callable functions |
| Replit API base | Custom Node.js Express server (`api_server.js`) — not actual Replit |
| API call pattern | `urllib.request` with `X-API-Key` header, graceful None fallback |
| API endpoints used | ~30 unique endpoints (sheets, bookings, finance, receipts) |
| Google Sheets | 8 worksheets (Card_Wallet, Sales_Daily, Setting, Stock_Out, Stock_In, TopUp_Log, Inventory, dynamic: Attendance_Log, Console_Booking) |
| Conversation states | 167 in V1, ~177+ in V2 |
| Sqlite in V2 | ✅ 15 tables, thread-safe, WAL mode, cron-synced |
| V2 modularization | 27 handler files, auth middleware, caching layer, promotion/referral/waitlist systems added |
| keep_alive | Optional Flask server (Replit compatibility), still referenced in V2 |
