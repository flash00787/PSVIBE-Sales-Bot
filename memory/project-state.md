# 📋 PS VIBE — Project State

> Current state of PS VIBE - PS5 Gaming Lounge system.
> Tagline: "Play The Game. Share The VIBE!"

---

## ✅ Recently Completed (2026-06-03 → 2026-06-04 — 31+ fixes)

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

## 🐛 Known Issues
| Issue | Priority | Status |
|-------|----------|--------|
| Pending bookings display bug (details not showing) | HIGH | Open |
| MySQL-GSheet sync — DELETE not synced | MED | Known |
| sheets/config still GSheets (not MySQL) | MED | Migration pending |

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
