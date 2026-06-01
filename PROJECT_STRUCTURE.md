# PS VIBE — Project Code Structure

> ⚠️ **CRITICAL:** There are TWO separate repos! Sub-agents must check BOTH.

---

## 📦 Repository 1: Sales Bot (`/root/psvibe-sales-bot/`)
**GitHub:** `flash00787/PSVIBE-Sales-Bot`
**Services:**
- `psvibe-sale-bot.service` — Sales Bot (Telegram: @psvibe_sales_bot)
- `psvibe_customer_bot.service` — Customer Bot (Telegram: @psvibe_customer_bot)
- `psvibe-watchdog.service` — Service health watchdog
- `psvibe-wallet.service.bak` — Deprecated (Wallet Bot moved to separate setup)

### Bot Handlers (`bot/handlers/`)
| File | Purpose |
|------|---------|
| `admin.py` | Admin panel (manage staff, settings, view stats) |
| `admin_bookings.py` | Admin booking management |
| `attendance.py` | Staff attendance tracking |
| `booking.py` | Booking management (create, edit, cancel) |
| `booking_flow.py` | Seat/console booking conversation flow |
| `broadcast.py` | Broadcast messages to members/staff |
| `commands.py` | Command handlers (/start, /help, etc.) |
| `console.py` | Console status display |
| `console_mgmt.py` | Console management (add/remove consoles, games) |
| `discount.py` | Discount management |
| `finance.py` | Financial reports and summaries |
| `games.py` | Game library display and management |
| `ginst.py` | Game installation management |
| `help.py` | Help commands |
| `input_logger.py` | Input logging for debugging |
| `main_menu.py` | Main menu navigation |
| `members.py` | Member management (create, topup, edit member cards) |
| `notify.py` | Notification commands |
| `payroll.py` | Staff payroll management |
| `referral.py` | Referral program |
| `reports.py` | Report generation |
| `salary_adv.py` | Salary advance management |
| `sales.py` | Sales recording |
| `ssd_disc.py` | SSD/Disc game management |
| `stock.py` | Stock management |
| `stock_in.py` | Stock-in recording |
| `waitlist.py` | Waitlist for consoles |

### Bot Core (`bot/`)
| File | Purpose |
|------|---------|
| `main.py` | Bot entry point — handler registration, ConversationHandlers |
| `api_client.py` | **API communication layer** — all `_api_get/_api_post` calls to API server |
| `app.py` | Bot application config |
| `constants.py` | Constants (hours, rates, keyboard layouts) |
| `helpers.py` | Utility functions |
| `keep_alive.py` | Keep-alive for web servers |
| `report_generator.py` | PDF/HTML report generation |

### Bot Utils (`bot/utils/`)
| File | Purpose |
|------|---------|
| `api_client.py` | Alternative API client (HTTP requests to API server) |
| `time_utils.py` | Time conversion utilities |

### Customer Bot (`customer_bot/`) — SEPARATE Telegram bot
| File | Purpose |
|------|---------|
| `main.py` | Customer Bot entry point |
| `api.py` | **API communication layer** — `_api_get/_api_post` + **cached fetchers** (`_fetch_games`, `_fetch_members`, `_fetch_consoles`, `_fetch_config`, `_build_rate_lines`) |
| `booking.py` | Booking logic (slot checking, booking creation) |
| `booking_handlers.py` | Booking conversation flow (7+ ConversationHandler states) |
| `handlers.py` | Customer-facing command handlers (/book, /rate, /contact) |
| `ai.py` | AI chat integration |

### Other Bot Files
| File | Purpose |
|------|---------|
| `main.py` (root) | **Sales Bot main entry point** (runs telegram bot loop) |
| `tests/` | 33 pytest tests (booking, finance, main_menu, members, reports, sales, stock) |
| `migrations/` | Database migration scripts |
| `sqlite/` | SQLite database managers (legacy) |
| `temp/` | Temporary fix patches |

---

## 📦 Repository 2: API Server (`/root/psvibe_api_server/`)
**GitHub:** `flash00787/PSVIBE-API-Server`
**Service:** `psvibe-api.service` — FastAPI on port 8000

### Core Files
| File | Purpose |
|------|---------|
| `app.py` | **Main API server** (~2200 lines). All endpoints: members, bookings, games, consoles, topup, config, analytics |
| `config.py` | Environment config loading (secrets, API_KEY, MYSQL) |
| `mysql_db.py` | MySQL connection module (pymysql, connection pool) |
| `sheets_client.py` | Google Sheets client (gspread wrapper, caching) |
| `analytics.py` | BI dashboard analytics functions |
| `dashboard_bot.py` | Dashboard bot integration |
| `db_client.py` | Database client (legacy, part of migration) |
| `models.py` | Data models |

### Critical API Endpoints (app.py ~2200 lines)
| Endpoint | MySQL | Purpose |
|----------|-------|---------|
| `/api/fetch_games` | ✅ MySQL | Game library with disc counts + console status |
| `/api/fetch_members` | ✅ MySQL | Member list with tier calc |
| `/api/fetch_member_data/{id}` | ✅ MySQL | Single member details + wallet |
| `/api/fetch_console_status` | ✅ MySQL | Console list with status (Free/Busy) |
| `/api/sheets/config` | ⚠️ GSheets+Cache | **NOT MySQL yet** — settings, rates, multipliers (60s cache) |
| `/api/fetch_console_games` | ✅ MySQL | Game-console assignments (1000+ rows) |
| `/api/create_booking` | ✅ MySQL | Create new booking |
| `/api/bookings` | ✅ MySQL | Search/cancel bookings |
| `/api/members/topup` | ✅ MySQL | Member topup (minute addition) |
| `/api/analytics/daily_sales` | ✅ MySQL | Daily sales KPIs |

### Sync & Migration
| File | Purpose |
|------|---------|
| `sync_service.py` | **GSheet → MySQL sync** (background sync every 5 min via cron) |
| `run_sync.sh` | Sync wrapper (loads env vars, calls sync_service.py with venv python) |
| `sync_settings_to_mysql.py` | Settings tab → MySQL sync |
| `gsheet_to_mysql.py` | Legacy migration script |
| `phase5_migrate.py` | Phase 5 MySQL migration |
| `phase5_patch.py` | Phase 5 patches |
| `patch_routes.py` | Route patches applied at startup |
| `patch_app.py` | App patches |
| `fix_sheets_config.py` | Fix sheets config utility |
| `insert_config_helper.py` | Config insert helper |
| `fix_mysql_stock.py` | Fix MySQL stock data |

### MySQL (`psvibe-mysql` Docker container)
| Table | Sync Source | Rows |
|-------|-------------|------|
| `games_library` | Game_Library sheet | ~37 |
| `console_status` | Console_Booking sheet | ~10 |
| `console_games` | Console_Games sheet | ~1010 |
| `staff_records` | Settings sheet (staff) | ~16 |
| `member_wallets` | Card_Wallet sheet | ~300+ |
| `topup_log` | TopUp_Log sheet | tracks topups |
| `sales_daily` | Sales_Daily sheet | daily sales |

### Architecture: Bot → API → MySQL/GSheet
```
Sales Bot ──→ API Server (:8000) ──→ MySQL (primary)
    │              │                     ↑
    │              └──→ GSheet (fallback)─┘
    │
Customer Bot ──→ API Server (:8000) ──→ MySQL (primary)
    │                                     ↑
    └──→ sheets/config (still GSheets!)───┘
```

---

## 🐳 Docker Containers
| Container | Purpose |
|-----------|---------|
| `psvibe-mysql` | MySQL 8.0 database (port 3306) |
| `aungchanmyint-caddy-1` | Caddy web server (port 80→443, reverse proxy to API + dashboard) |
| `chrome-puppeteer` | Chrome headless for receipt generation |
| `construction_bot` | Three Brothers Construction bot |
| `aungchanmyint-n8n-1` | n8n workflow automation |
| `oc-coco` | OpenClaw CoCo agent |
| `oc-nova` | OpenClaw Nova agent (Ye Yint Oo's assistant) |
| `openclaw-openclaw-cli-1` | OpenClaw CLI (unhealthy health check but running) |
| `openclaw-openclaw-gateway-1` | OpenClaw Gateway (local mode) |

---

## ⚙️ Services (systemd)
| Service | Type | Purpose |
|---------|------|---------|
| `psvibe-api.service` | FastAPI | REST API on port 8000 (uvicorn) |
| `psvibe-sale-bot.service` | Python | Sales Telegram bot |
| `psvibe_customer_bot.service` | Python | Customer Telegram bot |
| `psvibe-watchdog.service` | Health | Monitors 3 services, auto-restarts |
| `cloudflared-tunnel.service` | Tunnel | Cloudflare tunnel (ps-vibe.com → localhost:80) |

---

## 🛠️ Coordination Tools (`/root/coordination/`) — 45+ Python scripts

### Analysis Tools
| Tool | Lines | Purpose |
|------|-------|---------|
| `flow_analyzer.py` | 742 | State machine analysis |
| `arch_mapper.py` | 754 | Module dependency graph |
| `enhanced_validator.py` | 996 | Async pattern / code scanning |
| `import_scanner.py` | 112 | Import validation |
| `quality_gate.py` | 227 | Unified quality score (0-100) |

### Fix & Verification
| Tool | Lines | Purpose |
|------|-------|---------|
| `fix_protocol.py` | 120 | **MANDATORY** pre/post fix safety (snapshot → compile → rollback) |
| `fix_safety.py` | 89 | Pre-fix backup + post-fix verify |
| `verify_agent.py` | 155 | Post-fix validation with auto-rollback |
| `auto_verify.py` | 155 | Automatic verification pipeline |
| `fix_lock.py` | — | File locking for parallel fix safety |

### Workflow & Batch
| Tool | Lines | Purpose |
|------|-------|---------|
| `workflow_engine.py` | 330+ | 4 pipelines: quality, full-audit, safe-fix, auto-deploy |
| `batch_coordinator.py` | 1200 | 11 commands: plan/dispatch/status/merge/rollback |
| `task_bridge.py` | 185 | Sub-agent ↔ Engine bridge |
| `queue_manager.py` | — | Priority queue + dead-letter |
| `timeout_auto_split.py` | 517 | Auto-split long-running agents |
| `deploy_manager.py` | — | Full deploy pipeline |

### Monitoring & Status
| Tool | Purpose |
|------|---------|
| `status_reporter.py` | Quick health check |
| `status_board.py` | Real-time JSON snapshot |
| `health_dashboard.py` | Comprehensive dashboard |
| `dashboard.py` | Web UI (port 9090) |
| `service_watchdog.py` | Auto-restart stuck services |
| `cron_health.py` | Cron job monitoring |
| `auto_healer.py` | Service watchdog (3 failures → restart) |
| `check_alerts.py` | Health alert checking |

### Documentation & Git
| Tool | Purpose |
|------|---------|
| `auto_doc_updater.py` | Auto-update KNOWN_BUG_PATTERNS + git commit |
| `auto_git_sync.py` | Auto-commit (dry-run every 6h) |
| `git_sync_agent.py` | Git sync for sub-agents |
| `notifier.py` | Pipeline event notifications |
| `findings_manager.py` | Merge findings across agents |
| `dispatch_manager.py` | Dispatch pending findings to fix agents |

---

## 🔄 Data Flow

```
Google Sheets (source of truth)
    │
    ├── sync_service.py (cron every 5 min)
    │       ↓
    │   MySQL (psvibe-mysql)
    │       │
    │       ↓
    │   API Server (:8000)
    │       │
    │       ├── Sales Bot ←→ API ←→ MySQL
    │       └── Customer Bot ←→ API ←→ MySQL (most endpoints)
    │                            ↕  (sheets/config still → GSheets)
    │
    └── Direct GSheets fallback (if MySQL fails or endpoint not migrated)
```

---

## 🧪 Tests
- **33 tests** at `/root/psvibe-sales-bot/tests/`
- Run with: `python3 -m pytest tests/`
- Coverage: booking, finance, main_menu, members, reports, sales, stock

---

## ☁️ Cloudflare
- **Tunnel:** `cloudflared-tunnel.service` → `ps-vibe.com` → localhost:80
- **Dashboard:** `https://ps-vibe.com/dashboard/` (Caddy reverse proxy :80→:9090)
- **API:** `ps-vibe.com` → Cloudflare → Caddy → API (:8000) — all encrypted

---

## 📋 Bug History
See `ERROR_PATTERNS.md` for full bug chronology (35+ documented bugs with root cause analysis).
