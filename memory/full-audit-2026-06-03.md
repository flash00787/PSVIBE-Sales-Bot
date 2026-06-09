# 🔍 PS VIBE — Full System Audit (2026-06-03)

## Architecture
```
Sale Bot ──➤ API (:8000, API Key Auth) ──➤ MySQL (primary)
Customer Bot ──➤ API (:8000, API Key Auth) ──➤ MySQL
Dashboard (Vue.js) ──➤ API (:8000, JWT Auth) ──➤ MySQL
                        ↓
                 GSheets ⬅️ (Fallback Only / Some Direct Writes)
```

## Services Status
| Service | Status |
|---------|--------|
| psvibe-sale-bot | ✅ Active (PID 3182899) |
| psvibe_customer_bot | ✅ Active |
| psvibe-api | ✅ Active |
| psvibe-watchdog | ✅ Active |
| psvibe-sync | ❌ Inactive (not critical) |
| MySQL (Docker) | ✅ Healthy |
| Dashboard Dist | ✅ Built & Deployed |

## API Endpoints

### Main API (app.py) — 72 Endpoints
- System (3): health, mysql/health, mysql/status
- Members (9): fetch, data, tier, wallet, balance, register, deduct, rate, referral
- Consoles (4): status, add/remove console_game, add/remove_to_setting
- Bookings (7): create, end, list, cancel, checkin, customer create
- Games (8): fetch, library, console_games, add/edit/delete, disc_count, install
- Settings (5): base_rate, console_multiplier, new_member_defaults, rank, bonus
- Staff (4): list, names, attendance, salaries
- Coupons (4): generate, list, validate, redeem
- Promotions (2): cached, active
- Food (3): prices, costs, stock-out
- Finance (4): OPEX, assets, payables, prepaid (via bot)
- Utility (3): voucher, member_id, member_row
- Logging (2): sheets/log, bot-users/track

### Dashboard Routes (dashboard_routes.py) — 33 Endpoints
- GET /stats, /consoles, /schedule, /revenue-trend
- GET /members (with tier), DELETE /members/{id}
- GET /food-stock, /promotions-active
- GET /sales-daily (with summary), /financial-report (full)
- GET+DELETE /stock-in, /stock-out
- Auth endpoints: /login, /refresh, /me

## GSheets Still Used Directly
| GSheet | Access Type | Critical? |
|--------|-------------|-----------|
| Sales_Daily | _LazyWorksheet (DIRECT WRITE) | 🔴 CRITICAL |
| Stock_In | _LazyWorksheet (DIRECT WRITE) | 🔴 CRITICAL |
| Stock_Out | _LazyWorksheet (fallback) | 🟡 |
| Setting | _LazyWorksheet + _replit_get | 🟡 |
| Card_Wallet | _LazyWorksheet (fallback) | 🟢 |
| TopUp_Log | _LazyWorksheet (direct) | 🟡 |
| Inventory | _LazyWorksheet (direct) | 🟡 |
| Input_Log | _LazyWorksheet (direct) | 🟢 |
| Console_Booking | get_booking_sh() (fallback) | 🟢 |
| Game_Library | get_game_lib_sh() (fallback) | 🟢 |
| Console_Games | get_console_games_sh() (fallback) | 🟢 |
| Attendance_Log | get_att_sh() (direct) | 🟡 |
| Salary_Advance | get_salary_adv_sh() (direct) | 🟡 |

## All 11 Fix Items — Status

| # | Issue | Status | How |
|---|-------|--------|-----|
| 1 | Sale Daily: Remove fake promotions | ✅ | Filter inactive/expired in fetch_promotions_cached() |
| 2 | Member 90K text spam + stuck confirm | ✅ | Removed duplicate text, fixed auto-confirm flow |
| 3 | Consoles: Session Start/End broken | ✅ | Fixed SyntaxError (duplicate except block) |
| 4 | Customer Booking: wrong counts + pending not showing | ✅ | Fixed URL encoding in _api_call_async() |
| 5 | Console Install incorrect | ✅ | Fixed type selection flow (was hardcoded HDD) |
| 6 | Game list: numbers only, not clickable | ✅ | Fixed empty labels, direct list with Edit Game |
| 7 | Main Menu: Remove Commands + Fin Report | ✅ | Removed BTN_FINANCIAL_REPORT and BTN_HELP |
| 8 | Consoles: SSD + Game Library direct | ✅ | Added BTN_SSD_MANAGE, direct game list + Edit |
| 9 | Coupon stuck at confirm in Sale Daily | ✅ | Fixed Markdown parse error in step_coupon_confirm |
| 10 | C09/C10 multiplier ×1.2 not applied | ✅ | Hardcoded fallback in fetch_console_multiplier() |
| 11 | Web Dashboard upgrade | ✅ | Stats fixed, tiers fixed, delete btns, Sale Daily + Fin Report views, 6 new API routes, rebuilt |
