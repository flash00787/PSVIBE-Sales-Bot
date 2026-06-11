# PS VIBE Multi-Branch Support — Analysis & Implementation Plan
**Date:** 2026-06-11  
**Status:** ANALYSIS ONLY (Phase 5, Item 5)  
**Author:** Kora AI Agent

---

## Executive Summary

PS VIBE currently operates as a **single-location** system with 42 MySQL tables, a FastAPI server, two Telegram bots (Sales Bot + Customer Bot), and a Vue 3 dashboard. Multi-Branch Support means enabling the same system to manage **2+ physical locations**, each with its own inventories, consoles, staff, bookings, and sales — while keeping certain data (members, promotions, games library, finance chart of accounts) shared across branches.

**Key insight:** The data model has zero branch awareness today. Every query assumes one store. Enabling multi-branch means adding `branch_id` to ~24 tables, modifying ~100+ API endpoints, both bots, and the dashboard. A phased approach with a **MVP (Branch 1 + Branch 2)** is strongly recommended.

---

## 1. Database Table Classification

### 1.1 Branch Tables (new `branches` table)

```sql
CREATE TABLE branches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,              -- e.g., "PS VIBE Sanchaung"
    code VARCHAR(20) NOT NULL UNIQUE,         -- e.g., "SCH" (for API/token refs)
    address TEXT,
    phone VARCHAR(50),
    is_active TINYINT(1) DEFAULT 1,
    open_time TIME DEFAULT '10:00:00',
    close_time TIME DEFAULT '22:00:00',
    telegram_group_id VARCHAR(50),            -- Staff group chat ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 1.2 Per-Branch Tables (need `branch_id` FK)

Each of these tables represents resources that belong to a specific physical location:

| # | Table | Current Row Count (est.) | Reasoning |
|---|-------|--------------------------|-----------|
| 1 | `console_status` | ~10-20 | Each branch has its own consoles |
| 2 | `console_booking` | ~50-200/day | Bookings occur at a specific branch |
| 3 | `console_games` | ~50-100 | Games installed per-console, per-branch |
| 4 | `staff_records` | ~5-15 | Staff work at specific branches |
| 5 | `attendance_log` | ~5-20/day | Attendance is per-branch |
| 6 | `inventory` | ~20-50 | Each branch has its own stock |
| 7 | `stock_in` | ~10-50/month | Stock received at a specific branch |
| 8 | `stock_out` | ~10-50/month | Stock sold/used at a branch |
| 9 | `sales_daily` | ~10-50/day | Sales happen at a branch |
| 10 | `receipts` | ~10-50/day | Receipts issued at a branch |
| 11 | `topup_log` | ~10-50/day | Top-ups processed at a branch |
| 12 | `opex` | ~5-20/month | Operating expenses per branch |
| 13 | `cash_movements` | ~5-20/month | Cash in/out per branch |
| 14 | `cash_transfers` | ~1-5/month | Transfers between branch accounts |
| 15 | `promotions_log` | ~5-20/month | Promo redemptions at a branch |
| 16 | `salary_advance` | ~1-5/month | Staff advances (staff → branch) |
| 17 | `salary_payroll` | ~5-15/month | Payroll per branch |
| 18 | `finance_opex_log` | ~5-10/month | OPEX line items per branch |
| 19 | `asset_disposals` | ~1-5/year | Asset disposal at a branch |
| 20 | `referral_log` | ~5-30/month | Referrals happen at a branch |

### 1.3 Global/Shared Tables (NO branch_id needed)

These tables represent company-wide entities shared across all branches:

| # | Table | Reasoning |
|---|-------|-----------|
| 1 | `members` | Members are global — can visit any branch |
| 2 | `member_wallets` | Wallet balances are global (member-level) |
| 3 | `member_coupons` | Coupons are member-level, redeemable anywhere |
| 4 | `card_wallet` | Card-based wallet (member-level) |
| 5 | `games_library` | Master game catalog, shared across branches |
| 6 | `promotions` | Company-wide promotions |
| 7 | `settings` | Global system settings |
| 8 | `settings_config` | Global configuration keys |
| 9 | `accounts` | Chart of accounts (financial) |
| 10 | `shareholders` | Company shareholders |
| 11 | `capital_movements` | Capital injections/ejections |
| 12 | `profit_distributions` | Dividend distributions |
| 13 | `profit_distribution_details` | Dividend allocation details |
| 14 | `dividends` | Dividend payouts |
| 15 | `finance_assets` | Company assets (depreciation) |
| 16 | `finance_payables` | Company payables |
| 17 | `finance_receivables` | Company receivables |
| 18 | `finance_prepaid` | Prepaid expenses |
| 19 | `prepaid_amortization` | Amortization schedule |
| 20 | `sync_status` | Google Sheets sync tracking |
| 21 | `branches` | NEW — the branches themselves |
| 22 | `console_games_backup` | Backup table (follows console_games) |
| 23 | `games_library_backup` | Backup table (follows games_library) |
| 24 | `staff_records_bak` | Backup table (follows staff_records) |

### 1.4 Ambiguous/Borderline Tables

| Table | Recommendation | Rationale |
|-------|---------------|-----------|
| `accounts` | Global but may need per-branch sub-accounts | E.g., "Cash-SCH", "Cash-HLED" |
| `finance_assets` | Global with `branch_id` optional | Asset physically at a branch |

---

## 2. Migration Plan

### Phase 0: Prerequisites (1-2 days)

```
Estimated effort: Low
Risk: Low
```

1. **Create `branches` table** with initial row for existing branch (id=1, code="MAIN")
2. **Create database backup** (full mysqldump)
3. **Add `branch_id` column** to all 20 per-branch tables:
   ```sql
   ALTER TABLE console_status ADD COLUMN branch_id INT DEFAULT 1;
   ALTER TABLE console_booking ADD COLUMN branch_id INT DEFAULT 1;
   -- ... etc for all 20 tables
   ```
4. **Add foreign key constraints** (soft, NOT enforced initially):
   ```sql
   ALTER TABLE console_status ADD INDEX idx_branch (branch_id);
   -- Don't add FK constraints yet — let the app enforce it
   ```
5. **Add `branch_id` to console_status PK**:
   ```sql
   ALTER TABLE console_status DROP PRIMARY KEY;
   ALTER TABLE console_status ADD PRIMARY KEY (console_id, branch_id);
   ```
   ⚠️ **CRITICAL:** `console_status` uses `console_id` as VARCHAR PK. Each branch may have the same console_id ("PS5-01"). The PK must become `(console_id, branch_id)`.

6. **Seed `settings_config`** with branch-aware defaults:
   ```sql
   INSERT INTO settings_config (config_key, config_value, config_type, category)
   VALUES ('default_branch_id', '1', 'int', 'branch');
   ```

### Phase 1: DB Migration + API Read Layer (3-5 days)

```
Estimated effort: Medium
Risk: Medium
```

1. **Run all ALTER TABLE statements** on a staging copy first, then production
2. **Add `branch_id` to existing data** — all current rows get `branch_id = 1`
3. **Update FastAPI models.py** — add `branch_id` to Pydantic request/response models
4. **Update ALL API queries** to include `branch_id` filter:
   - GET endpoints: add `WHERE branch_id = %s` to every query
   - POST endpoints: accept and store `branch_id`
   - Default behavior: if no branch specified, use branch_id from auth context or default
5. **Add branch-aware middleware** to FastAPI:
   ```python
   # Inject branch_id from auth token or query param
   @app.middleware("http")
   async def branch_middleware(request, call_next):
       branch_id = request.headers.get("X-Branch-ID", 1)
       request.state.branch_id = int(branch_id)
       ...
   ```
6. **Update auth.py** — staff tokens carry a default branch_id
7. **API endpoints to create/modify**:
   - `GET /api/branches` — list all branches
   - `GET /api/branches/{id}` — branch details
   - `POST /api/branches` — create new branch
   - `PUT /api/branches/{id}` — update branch
   - `GET /api/dashboard/stats?branch_id=X` — branch-filtered stats
   - `GET /api/dashboard/consoles?branch_id=X` — branch-filtered consoles

### Phase 2: Bot Code Changes (4-6 days)

```
Estimated effort: HIGH
Risk: HIGH — bots are critical path
```

#### 2A. Sales Bot (Staff Bot)

**Changes needed:**

1. **Staff login/setup** — staff belongs to a branch:
   - Add `branch_id` to `staff_records` (already planned)
   - When staff starts bot, load their branch context
   - Store `branch_id` in `context.user_data["branch_id"]`

2. **Branch selector for multi-branch staff** (admin users):
   - New menu item: "🔄 ဆိုင်ပြောင်းမည်" (Switch Branch)
   - Only visible if staff has access to multiple branches
   - Persist selection in `context.user_data`

3. **Update all API calls** to pass `branch_id`:
   - `api_client.py`: add `branch_id` parameter to all calls
   - `_api_call()`: include `X-Branch-ID` header or query param
   - Every handler that calls the API: pass current branch context

4. **Update handlers** (most impactful changes):
   - `booking.py`: console list filtered by branch, bookings scoped by branch
   - `sales.py`: sales/discounts only for current branch
   - `members.py`: top-up records scoped by branch (member lookup still global)
   - `opex.py`: expenses per branch
   - `stock.py` / `stock_in.py`: inventory per branch
   - `reports.py`: financial reports per branch (with "All Branches" option)
   - `console_mgmt.py`: console management per branch
   - `payroll.py`: staff and attendance per branch
   - `attendance.py`: check-in/out per branch
   - `main_menu.py`: add branch indicator in menu header

5. **New branch-aware responses:**
   - Staff bot header: `"PS VIBE — Sanchaung Branch 📍"`
   - Reports: branch name in report title
   - Cross-branch booking: NOT allowed in MVP

#### 2B. Customer Bot

**Changes needed:**

1. **Branch selection during booking:**
   - Step 0 of booking flow: "Which branch?"
   - Show branch list with addresses
   - Customer remembers their preferred branch

2. **Console listing** — only show consoles at selected branch
3. **Branch-aware status** — `/status` shows consoles at a branch
4. **Branch-aware waitlist** — waitlist is per-branch

5. **No branch required for:**
   - `/balance` — wallet is global
   - `/myid` — member ID is global
   - `/promotions` — promotions are global
   - `/games` — game library is global
   - `/refer` — referrals are global

### Phase 3: Dashboard Changes (5-7 days)

```
Estimated effort: HIGH
Risk: Medium — UI changes are extensive but well-scoped
```

#### 3A. New Vue Components/Features

1. **Branch Selector Component** (global, in AppLayout.vue header):
   - Dropdown with all branches
   - "All Branches" option for admins
   - Persisted in localStorage + Pinia store

2. **Branch Management View:**
   - New route: `/branches`
   - CRUD for branches
   - Set open/close times, address, phone

#### 3B. Store Changes (Pinia)

1. **New `branchStore`**:
   ```typescript
   // stores/branch.ts
   interface BranchState {
     branches: Branch[];
     selectedBranchId: number | 'all';
   }
   ```

2. **Update `dashboardStore`**:
   - All API calls include `branch_id` parameter
   - Stats filtered by selected branch

#### 3C. View Changes (every view needs branch filter)

**Views that need `branch_id` parameter:**

| View | Change |
|------|--------|
| `DashboardView.vue` | Stats cards per-branch filter |
| `ConsoleManagement.vue` | Console list scoped to branch |
| `BookingsManagement.vue` | Bookings scoped to branch |
| `SaleDaily.vue` | Sales scoped to branch |
| `MembersManagement.vue` | Member search global, but top-up/sales history branch-filtered |
| `StaffManagement.vue` | Staff scoped to branch |
| `StaffAttendance.vue` | Attendance scoped to branch |
| `TopUpLogs.vue` | Top-up history branch-filtered |
| `Inventory.vue` | Per-branch inventory |
| `StockIn.vue` | Per-branch stock-in records |
| `StockOut.vue` | Per-branch stock-out records |
| `OPEX.vue` | Per-branch OPEX |
| `CashFlowView.vue` | Per-branch cash movements |
| `FinancialReport.vue` | Multi-branch consolidated + per-branch |
| `PNLView.vue` | Per-branch P&L + consolidated |
| `BalanceSheetView.vue` | Consolidated only (accounts are global) |
| `Promotions.vue` | Global (no branch filter needed) |
| `GamesLibrary.vue` | Global (no branch filter needed) |
| `ShareholdersView.vue` | Global (no branch filter needed) |
| `DividendsView.vue` | Global |
| `ProfitDistributionView.vue` | Global |
| `CapitalMovementsView.vue` | Global |
| `Coupons.vue` | Global (member-level) |

#### 3D. API Client Changes (TypeScript)

```typescript
// api/client.ts
const apiClient = axios.create({...});

apiClient.interceptors.request.use(config => {
  const branchStore = useBranchStore();
  if (branchStore.selectedBranchId !== 'all') {
    config.headers['X-Branch-ID'] = branchStore.selectedBranchId;
  }
  return config;
});
```

### Phase 4: Telegram Bot Deep Integration (3-4 days)

```
Estimated effort: Medium-High
Risk: Medium
```

1. **Staff bot — cross-branch notifications:**
   - Staff in Branch A should NOT see Branch B bookings by default
   - Admin users can toggle "All Branches" view
   - Session reminders scoped to branch

2. **Staff bot — branch-aware reports:**
   - "Today Report" shows selected branch
   - Financial reports support per-branch + consolidated

3. **Customer bot — smart branch selection:**
   - If customer has booking history at a branch, default to that branch
   - Otherwise ask which branch on first booking

4. **Multi-bot per branch (future consideration):**
   - Could run separate bot instances per branch
   - **NOT recommended for MVP** — single bots with branch context are simpler

### Phase 5: Testing & Rollout (3-5 days)

```
Estimated effort: Medium
Risk: High during rollout
```

1. **Create Branch 2** (PS VIBE Hledan or similar)
2. **Test all flows:**
   - Staff login → branch selection → all operations
   - Customer booking with branch selection
   - Dashboard with branch filter
   - Cross-branch: member visits both branches
3. **Data verification:**
   - Confirm Branch 2 data is isolated
   - Confirm member data is shared correctly
4. **Rollback plan:**
   - Keep all `branch_id` defaults at 1
   - If rollback needed, remove branch_id columns from queries (not DB)

---

## 3. Complexity Assessment

### Quick Wins (Low Complexity, High Impact)

| Task | Effort | Why Quick |
|------|--------|-----------|
| Create `branches` table | 1 hour | Simple schema |
| Add `branch_id` to all 20 tables | 2 hours | Batch ALTER TABLE |
| Seed default branch | 15 min | One INSERT |
| API middleware for branch header | 2 hours | One middleware function |
| Branch selector in dashboard header | 3 hours | One Vue component |

### Medium Complexity

| Task | Effort | Notes |
|------|--------|-------|
| Update GET endpoints with WHERE branch_id | 3-4 days | ~60 endpoints, mechanical work |
| Update POST endpoints to store branch_id | 2-3 days | ~40 endpoints |
| Dashboard view branch filters | 3-4 days | ~15 views need updates |
| Bot API client changes | 1-2 days | One file, all calls affected |

### High Complexity (Needs Careful Design)

| Task | Effort | Notes |
|------|--------|-------|
| `console_status` PK change (composite key) | 1-2 days | Can't have duplicate console_ids across branches; PK must be (console_id, branch_id) |
| Staff bot — all handlers branch-aware | 3-4 days | ~15 handler files, each has queries/API calls |
| Customer bot — branch selection in booking flow | 2-3 days | ConversationHandler states need new step |
| P&L and financial reports — consolidated + per-branch | 3-4 days | Accounting logic needs branch dimension |
| Cross-branch member flow | 1-2 days | Member top-up at Branch A, used at Branch B |

### Total Estimated Timeline

| Phase | Working Days | Calendar Days (with testing) |
|-------|-------------|------------------------------|
| Phase 0: Prerequisites | 1-2 | 2-3 |
| Phase 1: DB + API Read | 3-5 | 5-7 |
| Phase 2: Bot Changes | 4-6 | 7-10 |
| Phase 3: Dashboard | 5-7 | 8-10 |
| Phase 4: Deep Integration | 3-4 | 5-7 |
| Phase 5: Testing/Rollout | 3-5 | 5-7 |
| **TOTAL** | **19-29 working days** | **4-6 calendar weeks** |

---

## 4. Minimum Viable Product (MVP) Definition

### What "Multi-Branch Ready" Really Means (MVP)

**MVP Scope — Do These First:**

1. ✅ **Database:** `branches` table + `branch_id` on all per-branch tables
2. ✅ **API:** All endpoints accept `branch_id` (default=1 for backward compat)
3. ✅ **Staff Bot:** Branch selector in menu + filtered data per branch
4. ✅ **Customer Bot:** Branch selection at booking start
5. ✅ **Dashboard:** Branch dropdown in header + data filtered by selection

**MVP Does NOT Include (Phase 2):**

- ❌ Cross-branch transfers (inventory, cash)
- ❌ Multi-branch consolidated financial reports
- ❌ Branch-specific pricing/promotions
- ❌ Branch-specific game libraries
- ❌ Separate Telegram bots per branch
- ❌ Staff permissions per branch (staff works at Branch A only)
- ❌ Branch open/close hours enforcement

### MVP Success Criteria

1. Staff at Branch A logs in → sees only Branch A consoles, bookings, sales
2. Staff admin switches to Branch B → sees Branch B data
3. Customer books at Branch B → booking recorded with branch_id=2
4. Dashboard shows Branch A data by default, filterable to Branch B
5. Member data (wallet, coupons) visible across branches
6. Existing single-branch operations continue working (branch_id=1 default)

---

## 5. Key Design Decisions

### 5.1 Console ID Strategy

**Option A: Branch-prefixed console IDs** (Recommended)
- Console ID format: `{BRANCH_CODE}-{TYPE}-{NUM}`
- Example: `SCH-PS5-01`, `HLD-PS5-01`
- Pro: No PK change needed for console_status
- Con: Console names change, all references need update

**Option B: Composite PK `(console_id, branch_id)`**
- Keep console IDs as-is (`PS5-01`)
- Make console_status PK composite
- Pro: Console IDs don't change
- Con: Every join/query on console_status needs both columns

**Recommendation:** Option B for data purity, but Option A is simpler to implement. **Use Option A for MVP** — rename consoles with branch prefix. This avoids the composite PK complexity.

### 5.2 Staff Branch Assignment

- Staff assigned to **one primary branch** (branch_id in staff_records)
- Admin staff can switch branches
- Staff attendance is always at assigned branch
- **Future:** staff can work at multiple branches (many-to-many)

### 5.3 Member Global Identity

- `member_id` is global (same ID across all branches)
- Wallet balance is global
- Booking/top-up history is branch-scoped
- Cross-branch loyalty: member spends at Branch A counts toward tier

### 5.4 Financial Reporting

- Chart of accounts (`accounts`) is global
- But cash accounts may have **sub-ledgers per branch**:
  - `Cash-on-Hand` → `Cash-SCH`, `Cash-HLD`
  - Or use `cash_movements` with `branch_id` filter
- P&L can be per-branch or consolidated
- Balance Sheet is always consolidated

---

## 6. Code Files Impact Summary

### API Server (Python/FastAPI) — ~15 files touched

| File | Changes |
|------|---------|
| `app.py` | Branch middleware, new branch routes, pass branch_id to all queries |
| `dashboard_routes.py` | Accept branch_id param, filter all queries |
| `models.py` | Add Branch Pydantic model, add branch_id to request models |
| `auth.py` | Staff token carries default branch_id |
| `config.py` | Add DEFAULT_BRANCH_ID |
| `db_client.py` | Branch-aware connection context |
| `mysql_db.py` | Branch-aware query builder |
| `analytics.py` | Branch-filtered analytics |
| `fifo_wallet.py` | No change (global) |
| `inventory_fifo.py` | Branch-scoped inventory |
| `stock_fifo.py` | Branch-scoped stock |
| `session_timer.py` | Branch-scoped timers |
| `dashboard_bot.py` | Branch-aware bot commands |
| **All 100+ endpoints** | Add branch_id parameter/header |

### Sale Bot (Python) — ~20 files touched

| File | Changes |
|------|---------|
| `bot/api_client.py` | Add branch_id to all API calls |
| `bot/handlers/main_menu.py` | Branch selector in menu |
| `bot/handlers/booking.py` | Branch-filtered console/booking |
| `bot/handlers/sales.py` | Branch-scoped sales |
| `bot/handlers/members.py` | Branch filter on top-up |
| `bot/handlers/opex.py` | Branch-scoped expenses |
| `bot/handlers/stock.py` | Branch-scoped stock |
| `bot/handlers/stock_in.py` | Branch-scoped stock-in |
| `bot/handlers/reports.py` | Branch-selectable reports |
| `bot/handlers/console_mgmt.py` | Branch-scoped consoles |
| `bot/handlers/console.py` | Branch awareness |
| `bot/handlers/payroll.py` | Branch-scoped payroll |
| `bot/handlers/attendance.py` | Branch-scoped attendance |
| `bot/handlers/staff_attendance_handler.py` | Branch-scoped |
| `bot/handlers/waitlist.py` | Branch-scoped waitlist |

### Customer Bot (Python) — ~5 files touched

| File | Changes |
|------|---------|
| `customer_bot/main.py` | Branch selection step in booking conversation |
| `customer_bot/handlers.py` | Branch-aware console status, booking |
| `customer_bot/booking_handlers.py` | Branch selection step, branch-filtered consoles |
| `customer_bot/booking.py` | Pass branch_id to API |
| `customer_bot/api.py` | Add branch_id to API calls |

### Dashboard (Vue 3/TypeScript) — ~25 files touched

| File | Changes |
|------|---------|
| `src/stores/branch.ts` | **NEW** — branch state management |
| `src/stores/dashboard.ts` | Branch-aware data fetching |
| `src/stores/auth.ts` | Branch context from auth |
| `src/api/client.ts` | Branch header interceptor |
| `src/api/dashboard.ts` | Branch-aware API calls |
| `src/App.vue` | Branch selector in header |
| `src/components/AppLayout.vue` | Branch selector + indicator |
| **~20 views** | Branch filter parameter |

---

## 7. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Breaking existing single-branch flow | HIGH | Medium | Default branch_id=1, thorough backward compat testing |
| Console ID conflicts across branches | MEDIUM | High | Use branch-prefixed console naming convention |
| Bot handler spaghetti (complexity explosion) | HIGH | High | Start with middleware approach, not per-handler if/else |
| API response time degradation | MEDIUM | Low | Add composite index (branch_id, primary_key) on all tables |
| Staff confusion during transition | MEDIUM | High | Phase rollout — add branch selector silently, default stays "Main" |
| Data corruption (cross-branch writes) | HIGH | Low | Enforce branch_id at API middleware level, never trust client |

---

## 8. Recommended Implementation Order

**Week 1:** Phase 0 (prerequisites) + Phase 1 start (DB migration)
- Create branches table, add branch_id columns, seed data
- Add branch middleware to API

**Week 2:** Phase 1 (complete) + Phase 2 (bot API client)
- Finish all API endpoint updates
- Update bot api_client.py
- Test basic bot operations with branch_id

**Week 3:** Phase 2 (bot handlers) + Phase 3 (dashboard data layer)
- Update all bot handlers
- Create branchStore, update API client
- Dashboard views start getting branch filter

**Week 4-5:** Phase 3 (complete) + Phase 4 (deep integration)
- Finish all dashboard views
- Cross-branch notifications
- Financial report consolidation

**Week 6:** Phase 5 (testing + rollout)
- Create Branch 2
- Full system test
- Go live with both branches

---

## 9. Appendix: Migration SQL Template

```sql
-- ============================================================
-- PS VIBE Multi-Branch Migration — Phase 0
-- ============================================================

-- 1. Create branches table
CREATE TABLE branches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) NOT NULL UNIQUE,
    address TEXT,
    phone VARCHAR(50),
    is_active TINYINT(1) DEFAULT 1,
    open_time TIME DEFAULT '10:00:00',
    close_time TIME DEFAULT '22:00:00',
    telegram_group_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. Seed default branch
INSERT INTO branches (id, name, code, address) 
VALUES (1, 'PS VIBE Main', 'MAIN', 'Current Location');

-- 3. Add branch_id to all per-branch tables
ALTER TABLE console_status ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE console_booking ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE console_games ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE staff_records ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE attendance_log ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE inventory ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE stock_in ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE stock_out ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE sales_daily ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE receipts ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE topup_log ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE opex ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE cash_movements ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE cash_transfers ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE promotions_log ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE salary_advance ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE salary_payroll ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE finance_opex_log ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE asset_disposals ADD COLUMN branch_id INT NOT NULL DEFAULT 1;
ALTER TABLE referral_log ADD COLUMN branch_id INT NOT NULL DEFAULT 1;

-- 4. Add indexes for performance
CREATE INDEX idx_console_status_branch ON console_status(branch_id);
CREATE INDEX idx_console_booking_branch ON console_booking(branch_id);
CREATE INDEX idx_sales_daily_branch ON sales_daily(branch_id);
CREATE INDEX idx_topup_log_branch ON topup_log(branch_id);
CREATE INDEX idx_opex_branch ON opex(branch_id);
CREATE INDEX idx_attendance_log_branch ON attendance_log(branch_id);
CREATE INDEX idx_inventory_branch ON inventory(branch_id);

-- 5. Console ID convention for Branch 2 (future)
-- Branch 1 consoles: PS5-01, PS5-02, ...
-- Branch 2 consoles: B2-PS5-01, B2-PS5-02, ...
-- OR keep IDs same but differentiate by branch_id column
-- RECOMMENDED: If using branch-prefix, rename existing consoles:
-- UPDATE console_status SET console_id = CONCAT('MAIN-', console_id) WHERE branch_id = 1;
```

---

**END OF ANALYSIS — No code has been modified. This is a read-only planning document.**
