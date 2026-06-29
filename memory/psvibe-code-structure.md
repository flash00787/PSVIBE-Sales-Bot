# 📂 PS VIBE — Code Structure Reference

> **CRITICAL:** TWO repos! Sub-agents MUST check BOTH.

---

## Repository 1: Sales Bot (`/root/psvibe-sales-bot/`)
**GitHub:** `flash00787/PSVIBE-Sales-Bot`

### Bot Core (`bot/`)
| File | Purpose |
|------|---------|
| `main.py` | Bot entry point — handler registration, ConversationHandlers |
| `api_client.py` | **API communication layer** — all `_api_get/_api_post` calls |
| `app.py` | Bot application config |
| `constants.py` | Constants (hours, rates, keyboard layouts) |
| `helpers.py` | Utility functions |
| `keep_alive.py` | Keep-alive for web servers |
| `report_generator.py` | PDF/HTML report generation |

### Bot Handlers (`bot/handlers/`)
| File | Purpose |
|------|---------|
| `admin.py` | Admin panel |
| `admin_bookings.py` | Admin booking management (confirm/cancel) |
| `attendance.py` | Staff attendance tracking |
| `booking.py` | Booking management (create, edit, cancel) |
| `booking_flow.py` | Seat/console booking conversation flow |
| `broadcast.py` | Broadcast messages to members/staff |
| `commands.py` | Command handlers (/start, /help) |
| `console.py` | Console status display |
| `console_mgmt.py` | Console management (add/remove) |
| `discount.py` | Discount management |
| `finance.py` | Financial reports |
| `games.py` | Game library display |
| `main_menu.py` | Main menu navigation |
| `members.py` | Member management (create, topup, edit) |
| `notify.py` | Notification commands |
| `payroll.py` | Staff payroll |
| `reports.py` | Report generation |
| `sales.py` | Sales recording |
| `stock.py` | Stock management |

### Customer Bot (`customer_bot/`)
| File | Purpose |
|------|---------|
| `main.py` | Customer Bot entry point |
| `api.py` | API communication + cached fetchers |
| `booking.py` | Booking logic (slot checking, creation) |
| `booking_handlers.py` | Booking ConversationFlow (7+ states) |
| `handlers.py` | Customer commands (/book, /rate, /contact) |
| `ai.py` | AI chat integration |

## Repository 2: API Server (`/root/psvibe_api_server/`)
**GitHub:** `flash00787/PSVIBE-API-Server`

| File | Purpose |
|------|---------|
| `app.py` | Main API server (~2200 lines) — all endpoints |
| `config.py` | Env config loading |
| `mysql_db.py` | MySQL connection (pymysql, pool) |
| `sheets_client.py` | GSheets client (gspread wrapper) |
| `analytics.py` | BI dashboard analytics |
| `sync_service.py` | GSheet → MySQL sync (cron 5min) |

### Dashboard Pages (`/root/psvibe-dashboard/src/views/`)
| File | Purpose |
|------|---------|
| `DashboardView.vue` | Main overview dashboard |
| `BookingsView.vue` | Booking management |
| `TimelineView.vue` | Console timeline |
| `FeedbackView.vue` | Customer feedback |
| `CustomerBotSuccess.vue` | **Customer Bot booking success rate** (Jun 29) — KPI cards, all users table, rebook-adjusted metrics |
| `Coupons.vue` | Coupon management |
| `TopUpLogs.vue` | Top-up logs |
| `FoodStockView.vue` | Food inventory (multi-tab) |
| `FinancialReport.vue` | PNL + Balance Sheet |

## Architecture
```
Bot → API (:8000) → MySQL (primary) → GSheet (fallback)
```
> Key: sheets/config still GSheets (not MySQL). Most other endpoints MySQL-backed.
