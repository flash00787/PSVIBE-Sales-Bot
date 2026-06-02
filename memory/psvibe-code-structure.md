# PS VIBE — Project Code Structure

> ⚠️ **CRITICAL:** There are TWO separate repos! Sub-agents must check BOTH.

---

## Repository 1: Sales Bot (/root/psvibe-sales-bot/)
**GitHub:** flash00787/PSVIBE-Sales-Bot
**Services:**
- psvibe-sale-bot.service — Sales Bot (Telegram: @psvibe_sales_bot)
- psvibe_customer_bot.service — Customer Bot (Telegram: @psvibe_customer_bot)
- psvibe-watchdog.service — Service health watchdog
- psvibe-wallet.service.bak — Deprecated (Wallet Bot moved to separate setup)

## Repository 2: API Server (/root/psvibe_api_server/)
**GitHub:** flash00787/PSVIBE-API-Server
**Service:** psvibe-api.service — FastAPI on port 8000

### Core Files
| File | Lines | Purpose |
|------|-------|---------|
| app.py | 1267 | Main API server. Core endpoints: members, bookings, games, consoles, topup, receipts, config, analytics |
| patch_routes.py | 920 | Additional API routes: sheets data, finance/accounting, stock, waitlist, promotions |
| patch-app.py | 299 | Analytics routes: daily_sales, topups, dashboard, weekly_trends |
| sync_service.py | 1238 | MySQL to Google Sheets sync service |
| phase5_migrate.py | 1607 | Phase 5 database migration scripts |
| patch_app.py | 1166 | Legacy app patch file |
| analytics.py | 598 | BI dashboard analytics functions |
| fix_mysql_stock.py | 610 | Stock fix migration scripts |
| db_client.py | 426 | Database client (legacy) |
| dashboard_bot.py | 373 | Dashboard bot integration |
| sheets_client.py | 292 | Google Sheets client (gspread wrapper, caching) |
| fix_sheets_config.py | 205 | Sheets config fix/migration |
| inventory_fifo.py | 138 | Inventory FIFO calculations |
| gsheet_to_mysql.py | 113 | Google Sheets to MySQL migration |
| config.py | — | Environment config loading (secrets, API_KEY, MYSQL) |
| mysql_db.py | — | MySQL connection module (pymysql, connection pool) |
| models.py | — | Data models |

### API Route Sources
| File | Routes | Description |
|------|--------|-------------|
| app.py | 50+ endpoints | Core CRUD: members, bookings, games, consoles, topups, receipts, system |
| patch_routes.py | 25+ endpoints | Sheets data, finance/accounting, stock, waitlist, promotions, bookings |
| patch-app.py | 9 endpoints | Analytics endpoints (daily_sales, topups, dashboard, weekly_trends) |

**Full route list:** See API_ENDPOINTS.md

---

## Documentation Inventory

| File | Description |
|------|-------------|
| API_ENDPOINTS.md | Complete API route reference with request/response details |
| DB_SCHEMA.md | MySQL database schema (tables, columns, types) |
| DISASTER_RECOVERY.md | Disaster recovery procedures and backup instructions |
| GRAND_OPENING_CHECKLIST.md | Grand opening preparation checklist |
| STAFF_RUNBOOK.md | Staff operations runbook |
| V2_STATE.md | V2 migration status tracking |
| PROJECT_STRUCTURE.md | Legacy structure doc (this supersedes it) |
| .env.example | Environment variable template (redacted secrets) |

---

## Related Repositories
| Repo | Location | Service |
|------|----------|---------|
| PSVIBE-Sales-Bot | /root/psvibe-sales-bot/ | Sales bot + Customer bot |
| PSVIBE-API-Server | /root/psvibe_api_server/ | FastAPI backend |
| YYO Personal Wallet Bot | /opt/yyo-personal-wallet/ | Wallet bot (separate) |
| Construction Bot | /opt/construction-bot/ | Accounting bot (Docker) |
