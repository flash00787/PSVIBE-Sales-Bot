# 📋 PS VIBE — Project State

> Current state of PS VIBE - PS5 Gaming Lounge system.
> Tagline: "Play The Game. Share The VIBE!"

---

## ✅ Recently Completed (2026-06-19 → 2026-06-20 — 43+ fixes)

### 2026-06-20 — Sale Bot + Customer Bot Fixes

### 2026-06-29 — Customer Bot Booking Success Rate (New Feature)
| # | Feature | Status |
|---|---------|--------|
| 37 | **Customer Bot Success Rate API** — `GET /api/bot-users/booking-success-rate` with rebook logic | ✅ |
| 38 | **Customer Bot Success Dashboard** — `/bot-success` page with 6 KPI cards, all users table, 11 columns | ✅ |
| 39 | **First Ever Done Date Found** — June 13, 2026 (phone 09764375834, C-03, 90min, Any game) | ✅ |
| 40 | **Date filter presets** — Jun 21+ (first surge) / Jun 25+ (post-bind-fix) / All Time | ✅ |

### 2026-06-20 — Sale Bot + Customer Bot Fixes (continued)
| # | Feature | Status |
|---|---------|--------|
| 27 | **Pending booking time slot holding** — verified 3-layer conflict detection | ✅ |
| 28 | **Sale Bot Approve crash** — `consoles_with_game` variable scope | ✅ |
| 29 | **Sale Bot Reject crash** — `bk_info` variable scope | ✅ |
| 30 | **Reject reason feature** — prompt + card update + customer notify | ✅ |
| 31 | **Reject state persistence** — `user_data`→`bot_data` for ConversationHandler | ✅ |
| 32 | **Customer Bot duration conflict** — max duration + redirect to duration step | ✅ |
| 33 | **Customer Bot auto-assign v3** — empty available + ValueError handler | ✅ |
| 34 | **Customer Bot text polish** — natural Burmese with next booking time | ✅ |
| 35 | **Text polish script miss** — `return 0` at L493 with comment not replaced | ✅ |
| 36 | **Rejected bookings duplicate warning** — added `rejected` to inactive filter | ✅ |

### 2026-06-03 → 2026-06-19 (26 fixes)
| # | Feature | Status |
|---|---------|--------|
| 1 | **Sales Daily stuck** — `await` fix + double-unwrap fix + dict guard | ✅ |
| 2 | **Food Menu empty** — `food_costs` MySQL update (16 items) | ✅ |
| 3 | **Customer Bot My Booking** — cancelled booking filter + welcome banner | ✅ |
| 4 | **Dashboard sidebar** — AppLayout wrapper all 6 views | ✅ |
| 5 | **Dashboard data** — JWT auth + Food Stock dedup + Promotions dedup | ✅ |
| 6 | **Dashboard Food Stock Split** — 4 pages (Menu Reg, Stock In/Out, Inventory) | ✅ |
| 7 | **Menu Register save** — `rowcount`→`lastrowid`, hardcoded filter | ✅ |
| 8 | **Stock In payment** — payment_method, paid_by, staff_name fields | ✅ |
| 9 | **Gift balance 1200→600** — removed redundant api_add_topup | ✅ |
| 10 | **90k purchase spam** — MAX_SESSION_MINS=1440 limit | ✅ |
| 11 | **Booking timeout** — auto-cancel + Telegram notify + expired display | ✅ |
| 12 | **Console Status** — `"consoles"`→`"console"` in list_keywords (TRUE root cause) | ✅ |
| 13 | **Console Status simplified** — status only (no all-games list) | ✅ |
| 14 | **Game Library v2** — pagination (8/page) + search + tap-for-details | ✅ |
| 15 | **Game Library cleaned** — batch import/export bugs (ginst/ssd_disc/games) | ✅ |
| 16 | **Sale Completion** — coupon code generation + stock/wallet deduction APIs | ✅ |
| 17 | **Food Data Path** — category 'Food'→'Beverages' + alias fix | ✅ |
| 18 | **Session Start/End** — missing import fixes (4 functions) | ✅ |
| 19 | **Bot Menu restructure** — removed Add/Delete/Discs/SSD from bot | ✅ |
| 20 | **Console Install moved** — under Consoles menu | ✅ |
| 21 | **Session Start/End fixes** — wrong API endpoint `"bookings"`→`"create_booking"` (root cause) | ✅ |
| 22 | **Coupon code generating** — `console_status` update fixed via correct endpoint | ✅ |
| 23 | **Wallet balance deducting** — flow restored via correct session-end sequence | ✅ |
| 24 | **Sale Daily + Promotion confirm stuck** — `coupon_line` extracted before `user_data.clear()` | ✅ |
| 25 | **New Member payment flow** — all payment methods available (no auto-KPay) | ✅ |
| 26 | **Game Library consoles** — filtered by `inst_type='installed'` | ✅ |
| 27 | **Duplicate C-01 console** — SQL subquery + Python dedup + ended stale booking | ✅ |
| 28 | **Console Status wrong time/game** — MMT time, game from notes | ✅ |
| 29 | **Coupon Dashboard page** — `/api/dashboard/coupons` + `Coupons.vue` + route | ✅ |
| 30 | **TopUp Logs Dashboard page** — `/api/dashboard/topups` + `TopUpLogs.vue` + route | ✅ |
| 31 | **Grand Opening Data Reset** — all test data cleared, 3 real members kept | ✅ |
| 32 | **C-09/C-10 Multiplier 1.2x** — API endpoint was looking for individual keys, fixed to parse JSON blob | ✅ |
| 33 | **Customer Bot Food Menu** — `_bk_intercept_menu` BTN_FOOD missing + API unwrap logic + Unicode corruption | ✅ |
| 34 | **Waitlist Auto-Notify on Cancel (Phase 3.7)** — Cancel booking → auto notify first waitlisted customer via Telegram | ✅ |
| 35 | **H1: Approve Overlap Lock** — `FOR UPDATE` lock on overlap check (app.py L1415), prevents double-approve | ✅ |
| 36 | **C1: Console Start-Session Lock** — `console_status` check moved inside transaction with `FOR UPDATE` (app.py L1882) | ✅ |
| 37 | **H2: Walk-in Warning** — Active booking → 409 BLOCK; Pending/Confirmed → ⚠️ WARNING only (Bot shows staff warning) | ✅ |

### ✅ Recently Resolved (2026-06-21)

## 🐛 Known Issues
| Issue | Priority | Status |
|-------|----------|--------|
| Pending bookings display bug (details not showing) | HIGH | Open |
| MySQL-GSheet sync — DELETE not synced | MED | Known |
| sheets/config still GSheets (not MySQL) | MED | Migration pending |
| Issue | Status |
|-------|--------|
| Session Start → Booking Link prompt (never worked) | ✅ Fixed (4 bugs) |
| Checked-in bookings not appearing in link list | ✅ Fixed |
| Customer names showing "Guest" instead of real names | ✅ Fixed |
| Reject reason text input not working in Sale Bot | ✅ Fixed |
| Timeline auto-confirm for staff bookings | ✅ Fixed |
| Timeline game dropdown (was plain text) | ✅ Fixed |

## 🗓️ Upcoming
- **Grand Opening:** 06 June 2026 (Saturday) 🎉 ✅ **Completed**
- **Opening Hours:** 9 AM - 9 PM (daily)
- **Staff Training:** 04 June 2026 ✅ Completed

## 🏗️ Architecture (Updated)
```
Sales Bot ──→ API Server (:8000) ──→ MySQL (primary) ──→ Web Dashboard
    │              │                     ↑
    │              └──→ GSheet (fallback)┘
    │
Customer Bot ──→ API Server (:8000) ──→ MySQL (primary)
```

**New:** Web Dashboard now handles Game CRUD + Disc/SSD management (removed from bot)

- **2 Repos:** Bot = `/root/psvibe-sales-bot/`, API = `/root/psvibe_api_server/`
- **Dashboard:** Vue 3 + TypeScript at `/root/psvibe-dashboard/` → builds to `/root/psvibe_api_server/dashboard-dist/`
- **URL:** `psvibemm.com`
- **3 Services:** `psvibe-sale-bot` | `psvibe_customer_bot` | `psvibe-api`
- **MySQL:** Docker `psvibe-mysql` (:3306), DB: `psvibe_api`
- **Cloudflare:** `ps-vibe.com` → Cloudflare tunnel → localhost:8000

## 🔧 Coordination Tools
All at `/root/coordination/` — 45+ scripts.

## ✅ New: Daily Till Manager (June 29)

### DB
- `daily_till` — 16 columns, date-unique, branch-scoped
- Tracks: opening_balance, cash/kpay sales, expected_closing, actual_cash_counted, variance, status

### API
- `GET/POST /api/dashboard/till/today|open|close|history`
- Payment method parsing handles split format: `Cash:10000|KPay:0|WavePay:17000`
- Cash movements integrated: eject (stock expenses), transfer_out (Cash→KPay/Bank), transfer_in, inject
- **transfer_out amounts are NEGATIVE** — uses `ABS(amount)` in SQL

### Vue
- `/till` — 4-step flow: ① Open → ② Sales (4 cards) → ③ Expected (breakdown) → ④ Close
- 4 payment methods: Cash, KPay, WavePay, AYA Pay
- Live variance preview on close

## ✅ New: Session ↔ Sales Reconciliation (June 29)

### API
- `GET /api/dashboard/reconciliation?date=YYYY-MM-DD`
- Cross-checks Done sessions vs sales_daily, flags orphans on both sides
- Excludes food-only from orphan_sales

### Vue
- `/reconciliation` — Summary cards + Missing Sales (red) + Orphan Sales (yellow) + All Matched table
- Date selector, 120s auto-refresh

## ✅ Staff Permissions Extended (June 29)
- `/till`, `/reconciliation`, `/members` now visible to staff role
- Sidebar filter updated in AppLayout.vue

## ⚠️ Known Issues
- **50+ TIMESTAMP columns** across other tables still store UTC (not yet migrated to MMT)
- Priority tables: attendance_log, topup_log, stock_in, stock_out, receipts, promotions_log
