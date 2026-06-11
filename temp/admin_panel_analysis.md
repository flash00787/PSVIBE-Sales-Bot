# PS VIBE Web Admin Panel 2.0 — Upgrade Analysis

**Date:** 2026-06-11 | **Phase 5, Item 4 — Analysis Only**

---

## 1. Current Architecture

| Layer | Technology | Location |
|-------|-----------|----------|
| **Frontend** | Vue 3 + TypeScript SPA (Vite, Pinia, Vue Router 4, Axios, Chart.js, Tailwind CSS) | `/root/psvibe-dashboard/` |
| **Backend API** | Python FastAPI (uvicorn) | `/root/psvibe_api_server/` |
| **Dashboard Routes** | FastAPI APIRouter at `/api/dashboard/*` | `/root/psvibe_api_server/dashboard_routes.py` (2,729 lines, ~55 endpoints) |
| **Database** | MySQL 8 (Docker: `psvibe-mysql`) | 42 tables in `psvibe_api` |
| **Auth** | JWT-based login | `/auth` endpoint, Pinia `useAuthStore()` |
| **Build Output** | Static SPA | `/root/psvibe_api_server/dashboard-dist/` |

---

## 2. Current Pages & Features Checklist

### 2.1 Existing Routes (22 total)

| Route | Title | Features | Data Table(s) |
|-------|-------|----------|---------------|
| `/` | Dashboard | Stats cards (bookings, players, revenue, members), console grid, today's schedule, revenue chart (7d) | `console_status`, `console_booking`, `members`, `sales_daily` |
| `/bookings` | Bookings | Search, status filter, edit status/notes, status badges | `console_booking` |
| `/members` | Members | Search by name/phone, list view, detail modal, edit (name/phone/tier), delete | `members` |
| `/sales-daily` | Sales Daily | Sales records | `sales_daily` |
| `/games` | Games | CRUD: game_title, genre, solo/multi, disc_count, final_status. Genre filter, status badges | `games_library` |
| `/topups` | TopUp Logs | **Read-only** log view, search by member_id, copy member_id | `topup_log` |
| `/opex` | OPEX | Operating expenses CRUD, summary | `opex` |
| `/food-menu` | Food Menu | Menu register | (menu-related tables) |
| `/stock-in` | Stock In | Record stock entries | `stock_in` |
| `/stock-out` | Stock Out | Record stock usage | `stock_out` |
| `/inventory` | Inventory | Stats cards (total, low, out, value), search/filter, CRUD, status badges (OK/Low/Out) | `inventory` |
| `/promotions` | Promotions | CRUD | `promotions` |
| `/coupons` | Coupons | Coupon management | `member_coupons` |
| `/finance-dashboard` | Financial Dashboard | Financial overview | - |
| `/finance` | Web Finance | Balance management | `finance_*` tables |
| `/pnl` | P&L Statement | Profit & Loss | - |
| `/balance-sheet` | Balance Sheet | Balance sheet | - |
| `/cashflow` | Cash Flow | Cash flow statements | - |
| `/profit-distribution` | Profit Distribution | Distribution calculations & records | `profit_distributions`, `profit_distribution_details` |
| `/dividends` | Dividends | Dividend management | `dividends` |
| `/capital-movements` | Capital Movements | Capital injections/ejections | `capital_movements` |
| `/shareholders` | Shareholders | Shareholder CRUD | `shareholders` |
| `/financial-report` | Old Reports | Legacy financial reports | - |

### 2.2 Feature Matrix by 2.0 Module

| Module | Existing | CRUD | Search/Filter | Detail View | Export | Alerts |
|--------|----------|------|---------------|-------------|--------|--------|
| **Members** | ✅ | Edit name/phone/tier only | By name/phone | Balance, spend, join date | ❌ | ❌ |
| **TopUp** | ✅ | ❌ Read-only log | By member_id only | ❌ | ❌ | ❌ |
| **Console Status** | Partial | Dashboard read-only grid + bookings | Booking status only | Booking modal | ❌ | ❌ |
| **Games** | ✅ | Full CRUD | By title, genre filter | Edit modal | ❌ | ❌ |
| **Inventory** | ✅ | Full CRUD | By item, category filter | Edit modal, stats | ❌ | Low/out badges |
| **Staff** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Attendance** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Salary** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 3. Database Tables Relevant to 2.0 (Already Exist, No API)

### 3.1 `staff_records`
```sql
staff_id     INT PRI AUTO_INCREMENT
staff_name   VARCHAR(200) UNIQUE
base_salary  DECIMAL(12,2)
hourly_rate  DECIMAL(10,2)
role         VARCHAR(100)
is_active    TINYINT(1)
last_updated DATETIME
```

### 3.2 `attendance_log`
```sql
id           INT PRI AUTO_INCREMENT
staff_id     INT (FK → staff_records.staff_id)
check_in     DATETIME
check_out    DATETIME
hours_worked DECIMAL(5,2)
hourly_rate  DECIMAL(10,2)
daily_pay    DECIMAL(12,2)
date         DATE
status       VARCHAR(20)  -- 'checked_in', 'checked_out', etc.
notes        TEXT
created_at   TIMESTAMP
```

### 3.3 `salary_payroll`
```sql
id           INT PRI AUTO_INCREMENT
staff_name   VARCHAR(100)
base_salary  DECIMAL(10,2)
bonus        DECIMAL(10,2)
deductions   DECIMAL(10,2)
net_salary   DECIMAL(10,2)
pay_period   VARCHAR(50)
pay_date     DATE
status       VARCHAR(20)
notes        TEXT
created_at   TIMESTAMP
```

### 3.4 `salary_advance`
```sql
id              INT PRI AUTO_INCREMENT
staff_name      VARCHAR(100)
amount          DECIMAL(10,2)
advance_date    DATE
repayment_status VARCHAR(20)
notes           TEXT
created_at      TIMESTAMP
```

### 3.5 `console_status` (read-only via API — no CRUD)
```sql
console_id    VARCHAR(20) PRI
status        VARCHAR(50)
console_type  VARCHAR(50)
current_game  TEXT
current_member VARCHAR(100)
start_time    DATETIME
last_updated  DATETIME
```

### 3.6 `members` (limited API fields)
```sql
id              INT PRI AUTO_INCREMENT
member_id       VARCHAR(50) UNIQUE
name            VARCHAR(255)
phone           VARCHAR(50)
balance_minutes DECIMAL(10,2)  -- Exposed on member page, but API only exposes minimal fields
created_at      TIMESTAMP
updated_at      TIMESTAMP
```
> ⚠️ Members table lacks `tier`, `total_spend`, `join_date` columns — those come from Google Sheets or are computed. The dashboard_routes.py queries members and joins with topup/sales data. This should be clarified before 2.0.

### 3.7 `topup_log` (read-only via API)
```sql
id              INT PRI AUTO_INCREMENT
member_id       VARCHAR(50)
amount          DECIMAL(10,2)
mins_added      INT
topup_date      DATETIME
staff_name      VARCHAR(100)
payment_method  VARCHAR(50)
balance_before  DECIMAL(10,2)
balance_after   DECIMAL(10,2)
balance_mins_before INT
balance_mins_after  INT
notes           TEXT
created_at      TIMESTAMP
```

---

## 4. Current API Endpoints (dashboard_routes.py)

### 4.1 Summary by Module

| Module | Endpoints | Status |
|--------|-----------|--------|
| Dashboard Stats | `GET /stats`, `GET /consoles`, `GET /schedule`, `GET /revenue-trend` | ✅ |
| Bookings | `GET /bookings`, `GET/PUT/DELETE /bookings/{id}`, `DELETE /bookings/cleanup` | ✅ |
| Members | `GET /members`, `GET/PUT /members/{id}`, `GET /members/{id}/topups`, `DELETE /members/{id}` | Partial |
| Topups | `GET /topups` (read-only) | ❌ No POST |
| Games | `GET/POST /games`, `PUT/DELETE /games/{title}` | ✅ |
| Inventory | `GET/POST /inventory`, `PUT/DELETE /inventory/{id}` | ✅ |
| Stock In/Out | `GET/POST /stock-in`, `PUT/DELETE /stock-in/{id}`, `GET/POST /stock-out`, `DELETE /stock-out/{id}` | ✅ |
| Promotions | `GET/POST /promotions`, `PUT/DELETE /promotions/{id}` | ✅ |
| Coupons | `GET /coupons` | ✅ |
| Sales Daily | `GET /sales-daily` | ✅ |
| OPEX | `GET/POST /opex`, `GET /opex/summary`, `DELETE /opex/{id}` | ✅ |
| Finance | P&L, Balance Sheet, Cash Flow, Shareholders, Capital, Profit Distribution, Dividends, Assets | ✅ |
| **Staff** | ❌ **ZERO** | ❌ |
| **Attendance** | ❌ **ZERO** | ❌ |
| **Salary** | ❌ **ZERO** | ❌ |
| **Console CRUD** | ❌ **NONE** (only bookings, not console config) | ❌ |

---

## 5. What's Missing for "2.0" Requirements

### 5.1 🆕 Staff Management (COMPLETELY NEW)

**Current State:** DB has `staff_records`, `attendance_log`, `salary_payroll`, `salary_advance` tables. ZERO API endpoints. ZERO Vue pages.

**Needed:**
- `GET /api/dashboard/staff` — list all staff with search
- `POST /api/dashboard/staff` — create staff
- `PUT /api/dashboard/staff/{id}` — update staff
- `DELETE /api/dashboard/staff/{id}` — deactivate staff
- `GET /api/dashboard/staff/{id}/attendance` — attendance history
- `POST /api/dashboard/attendance/check-in` — clock in
- `POST /api/dashboard/attendance/check-out` — clock out
- `GET /api/dashboard/attendance` — attendance log with filters
- `GET /api/dashboard/salary` — payroll list with filters
- `POST /api/dashboard/salary` — create payroll record
- `GET /api/dashboard/salary/advances` — salary advances list
- `POST /api/dashboard/salary/advances` — record advance

**Vue Components Needed:**
- `StaffManagement.vue` — CRUD table, search, active/inactive filter
- `StaffAttendance.vue` — time clock, attendance log with date filter
- `StaffSalary.vue` — payroll history, advances, payment tracking

### 5.2 🔧 Member Management Enhancement

**Current State:** Basic CRUD. Detail modal shows: member_id, phone, tier, balance_minutes, total_spend.

**Missing:**
- **Wallet/Transaction History Tab** — Currently API has `GET /members/{id}/topups` but the frontend only shows it in the member detail modal without a full history view
- **Manual Wallet Adjustment** — No way to add/remove balance from admin panel
- **Comprehensive Filters** — No filter by tier, join date range, spend range
- **Bulk Actions** — No export, no bulk tier change

**API Needed:**
- `PUT /api/dashboard/members/{id}/wallet` — adjust wallet balance minutes
- `GET /api/dashboard/members/{id}/transactions` — full transaction history (topups + deductions + adjustments)

### 5.3 💰 Topup Management Enhancement

**Current State:** Read-only log. Search by member_id only.

**Missing:**
- **Manual Topup Form** — POST endpoint exists implicitly through other parts (Telegram bot does topups) but no dashboard API or UI
- **Date Range Filter** — No date picker
- **Payment Method Filter** — No filter
- **Staff Filter** — No filter
- **Export to CSV** — Not implemented

**API Needed:**
- `POST /api/dashboard/topups` — manual topup (increase member balance)
- Add date range query params to existing `GET /topups`
- Add payment_method, staff_name filter params

### 5.4 🎮 Console Management Enhancement

**Current State:** Dashboard shows read-only console grid. Bookings page manages bookings but there's NO way to edit console config (console_type, pricing, etc.).

**Missing:**
- **Console CRUD** — Add/remove/edit consoles
- **Console Type/Pricing** — Set console type (PS4/PS5), hourly rate, flat rate, membership rates
- **Console Status Override** — Manually set offline/maintenance
- **Pricing Configuration** — Console pricing tiers

**API Needed:**
- `GET /api/dashboard/consoles/detail` — full console details with pricing
- `PUT /api/dashboard/consoles/{id}` — update console config (type, pricing, status)
- `POST /api/dashboard/consoles` — add new console

### 5.5 📦 Inventory Management Enhancement

**Current State:** Has good basic CRUD + stats cards. Stock in/out workflows exist.

**Missing:**
- **Alerts/Notifications** — Low stock alerts on dashboard (data is there, just needs UI alert)
- **Reorder Suggestions** — Auto-suggest reorder quantities based on usage patterns
- **Export** — No CSV export

**Minor API additions:**
- `GET /api/dashboard/inventory/alerts` — items below reorder level

---

## 6. New Vue Components Needed

### 6.1 New Pages (6 new .vue files)

| File | Purpose | Priority |
|------|---------|----------|
| `src/views/StaffManagement.vue` | Staff CRUD (name, role, base_salary, hourly_rate, active toggle) | 🔴 Critical |
| `src/views/StaffAttendance.vue` | Attendance check-in/out, log with date filter, hours worked summary | 🔴 Critical |
| `src/views/StaffSalary.vue` | Payroll history, create payroll, advances tracking, payment status | 🔴 Critical |
| `src/views/TopUpManagement.vue` | **Enhanced** TopUp page: manual topup form + log with date/payment/staff filters | 🟡 High |
| `src/views/ConsoleManagement.vue` | Console CRUD: add/edit console, set type/pricing, override status | 🟡 High |
| `src/views/MemberDetail.vue` | **New dedicated** member detail page with wallet history tab | 🟢 Medium |

### 6.2 Modified Pages (3 .vue files)

| File | Changes |
|------|---------|
| `src/views/MembersManagement.vue` | Add filter by tier, date; add wallet adjustment; link to full detail page |
| `src/views/TopUpLogs.vue` | Add date range picker, payment method filter, staff filter, export CSV |
| `src/views/Inventory.vue` | Add low-stock alert banner, export button |

### 6.3 Router Additions

```typescript
// New routes to add:
{ path: "/staff", name: "staff", component: StaffManagement, meta: { requiresAuth: true, title: "Staff" } },
{ path: "/staff/attendance", name: "staff-attendance", component: StaffAttendance, meta: { requiresAuth: true, title: "Attendance" } },
{ path: "/staff/salary", name: "staff-salary", component: StaffSalary, meta: { requiresAuth: true, title: "Salary" } },
{ path: "/consoles/manage", name: "console-manage", component: ConsoleManagement, meta: { requiresAuth: true, title: "Console Management" } },
{ path: "/members/:id", name: "member-detail", component: MemberDetail, meta: { requiresAuth: true, title: "Member Detail" } },
```

### 6.4 Sidebar Navigation Changes

Add new section in `AppLayout.vue`:
```typescript
{
  label: 'Staff',
  icon: '...',
  children: [
    { path: '/staff', label: 'Staff List' },
    { path: '/staff/attendance', label: 'Attendance' },
    { path: '/staff/salary', label: 'Salary' },
  ],
},
{ path: '/consoles/manage', label: 'Consoles', icon: '...' },
```

---

## 7. New API Endpoints Needed

### 7.1 Staff Module (NEW — ~12 endpoints)

```python
# Staff CRUD
@router.get("/staff")                    # List staff (search, active filter)
@router.post("/staff")                   # Create staff
@router.put("/staff/{staff_id}")         # Update staff
@router.delete("/staff/{staff_id}")      # Deactivate staff

# Attendance
@router.get("/attendance")               # List attendance logs (date range, staff filter)
@router.post("/attendance/check-in")     # Clock in
@router.post("/attendance/check-out")    # Clock out
@router.get("/staff/{staff_id}/attendance")  # Staff-specific attendance

# Salary/Payroll
@router.get("/salary")                   # Payroll list (date range, staff filter)
@router.post("/salary")                  # Create payroll record
@router.get("/salary/advances")          # Salary advances list
@router.post("/salary/advances")         # Record salary advance
```

### 7.2 Console Management (NEW — ~3 endpoints)

```python
@router.get("/consoles/detail")          # Full console list with pricing info
@router.put("/consoles/{console_id}")    # Update console config (type, status, pricing)
@router.post("/consoles")                # Add new console
```

### 7.3 TopUp Enhancement (MODIFY — ~1-2 endpoints)

```python
@router.post("/topups")                  # Manual topup (currently only GET exists)
# MODIFY: @router.get("/topups") add date_from, date_to, payment_method, staff_name params
```

### 7.4 Member Enhancement (ADD — ~1 endpoint)

```python
@router.put("/members/{member_id}/wallet")  # Adjust wallet balance (add/subtract minutes)
@router.get("/members/{member_id}/transactions")  # Full transaction history
```

### 7.5 Inventory Alert (NEW — ~1 endpoint)

```python
@router.get("/inventory/alerts")         # Items below reorder level
```

**Total new/modified endpoints: ~20 new + ~3 modified**

---

## 8. Suggested Implementation Order

### Phase 1: Staff Management (Highest Priority — ENTIRELY NEW)
1. **Backend:** Create staff, attendance, salary API endpoints in `dashboard_routes.py`
2. **Frontend:** Create `StaffManagement.vue` (CRUD table)
3. **Frontend:** Create `StaffAttendance.vue` (check-in/out + log)
4. **Frontend:** Create `StaffSalary.vue` (payroll + advances)
5. **Integration:** Add sidebar navigation, router entries

### Phase 2: TopUp & Member Enhancement
1. **Backend:** Add `POST /topups` for manual topup
2. **Backend:** Add date/payment/staff filter params to `GET /topups`
3. **Backend:** Add `PUT /members/{id}/wallet` and transactions endpoint
4. **Frontend:** Enhance `TopUpLogs.vue` → rename to `TopUpManagement.vue` with manual topup form + enhanced filters
5. **Frontend:** Create `MemberDetail.vue` with wallet tab

### Phase 3: Console Management
1. **Backend:** Add console CRUD endpoints
2. **Frontend:** Create `ConsoleManagement.vue`
3. **Integration:** Add sidebar entry

### Phase 4: Inventory Alerts & Polish
1. **Backend:** Add inventory alerts endpoint
2. **Frontend:** Add alert banners to DashboardView, Inventory page
3. **Frontend:** Add CSV export buttons where missing

---

## 9. Technical Notes & Risks

### 9.1 Members Table — Incomplete Schema
The `members` table has only: `id, member_id, name, phone, balance_minutes, created_at, updated_at`. Fields like `tier`, `total_spend`, `join_date` used in the frontend are likely computed or sourced from elsewhere (Telegram bot, Google Sheets). Before enhancing the member module, confirm the data source for:
- `tier` — stored where? May be in `member_wallets` table or computed
- `total_spend` — likely computed from `topup_log` or `sales_daily` 
- `join_date` — may be in `members.created_at`

### 9.2 DB Foreign Keys
`attendance_log.staff_id` → `staff_records.staff_id` (FK relationship)
`salary_payroll.staff_name` and `salary_advance.staff_name` use `VARCHAR` not INT FK — consider consistency

### 9.3 Authentication
All new endpoints should use `user: dict = Depends(get_current_user)` for JWT auth — already available.

### 9.4 Dashboard Dist Build
After changes: `cd /root/psvibe-dashboard && npm run build` → deploys to `/root/psvibe_api_server/dashboard-dist/`

### 9.5 No Backend Framework Changes Needed
FastAPI + existing `dashboard_routes.py` pattern is used. Staff/attendance/salary endpoints follow the same pattern used by members, inventory, etc. — just use `_mysql_query()`, `_mysql_execute()`, `_mysql_query_one()` helpers.

---

## 10. Summary

| Category | Count | Notes |
|----------|-------|-------|
| Existing pages | 22 | Full finance, inventory, bookings, games, members |
| New pages needed | 6 | Staff(3), TopUp(enhanced), Console(manage), MemberDetail |
| Modified pages | 3 | MembersManagement, TopUpLogs, Inventory |
| New API endpoints | ~20 | Staff: 12, Console: 3, TopUp: 1, Member: 1, Inventory: 1 |
| Modified API endpoints | ~3 | Topups GET (filters), Members GET (filters), Wallet PUT |
| DB tables already exist | 4 | staff_records, attendance_log, salary_payroll, salary_advance |
| New DB tables needed | 0 | All tables exist — just need API endpoints |
| Estimated effort | Medium-Large | ~20 endpoints + ~6 new Vue pages + ~3 page modifications |

**The single biggest gap is Staff Management** — the database is fully provisioned but there are zero API endpoints and zero UI pages. This should be implemented first.
