# PS VIBE — Project Code Structure

> ⚠️ **CRITICAL:** TWO repos! Sub-agents MUST check BOTH when investigating bugs.

---

## 📦 Repo 1: Sales Bot (`/root/psvibe-sales-bot/`)
- `psvibe-sale-bot.service` — Sales Bot (Telegram: @psvibe_sales_bot)
- `psvibe_customer_bot.service` — Customer Bot (Telegram: @psvibe_customer_bot)
- `psvibe-watchdog.service` — Health watchdog

## 📦 Repo 2: API Server (`/root/psvibe_api_server/`)
- `psvibe-api.service` — FastAPI on port 8000
- `sync_service.py` — GSheet → MySQL sync (cron 5min)

## 🗄️ Database
- **MySQL:** Docker `psvibe-mysql` (127.0.0.1:3306)
- **Database:** `psvibe_api` — 31 tables
- **Schema doc:** `DB_SCHEMA.md` (at `/root/psvibe-sales-bot/`)
- **Backup:** Daily 4AM cron → `/root/backups/mysql/` (7-day retention)

## 🌐 Architecture
```
Bot (python-telegram-bot) → API (:8000) → MySQL (primary) → gspread (cold fallback)
```
- **Public URL:** https://ps-vibe.com (Cloudflare tunnel → localhost:8000)

## 📋 Documentation Files (VPS)
| File | Location | Description |
|------|----------|-------------|
| `DB_SCHEMA.md` | `/root/psvibe-sales-bot/` | MySQL table schemas (31 tables) |
| `API_ENDPOINTS.md` | `/root/psvibe-sales-bot/` | FastAPI endpoint reference |
| `GRAND_OPENING_CHECKLIST.md` | `/root/psvibe-sales-bot/` | Grand opening prep (Jun 6) |
| `STAFF_RUNBOOK.md` | `/root/psvibe-sales-bot/` | Bot commands for staff |
| `DISASTER_RECOVERY.md` | `/root/psvibe-sales-bot/` | Emergency procedures |
| `psvibe-code-structure.md` | `memory/` | File-by-file code reference |
| `project-state.md` | `memory/` | Current state & known issues |
| `infrastructure.md` | `memory/` | Coordination tools & config |
| `sop/` (13 files) | `memory/sop/` | SOPs, frameworks, protocols |

## 🔧 Key Paths
| Path | Purpose |
|------|---------|
| `/root/psvibe-sales-bot/bot/` | Main bot handlers (30+ files) |
| `/root/psvibe-sales-bot/customer_bot/` | Customer-facing bot |
| `/root/psvibe-sales-bot/tests/` | pytest test suite (78 tests) |
| `/root/psvibe_api_server/routes/` | FastAPI route handlers |
| `/root/psvibe_api_server/dashboard-dist/` | Vue.js dashboard (built) |
| `/root/psvibe-dashboard/` | Dashboard source (Vue 3 + Vite) |
| `/root/coordination/` | Multi-project coordination tools |

## ⚠️ Known Issues
| Issue | Severity | Status |
|-------|----------|--------|
| Cashflow month filter not applied (Jun 26) | Medium | 🔴 Pending |
| Cashflow asset deduction double-count (Jun 26) | Medium | 🔴 Pending |
| Quality Gate mypy errors (2955 pre-existing) | Low | 🟡 Deferred |

## 📅 Recent Milestones
| Date | Milestone |
|------|-----------|
| Jun 28 | Food underscore Markdown bug fix + EOD report rewrite |
| Jun 27 | Staff salary system + customer notifications fix |
| Jun 26 | Dashboard UX overhaul (food orders, timeline, cashflow) |
| Jun 25 | ACM Wallet MySQL migration + SEL Exchange project built |
| Jun 22 | Console Timer + Booking system overhaul |
| Jun 15-16 | Discord bot (35 commands) + Finance system |
| Jun 6 | Grand Opening |

## 🏗️ Multi-Project Architecture
Kora manages **9 projects** via `/root/coordination/project_registry.json`:
`psvibe`, `construction`, `yyo_wallet`, `acm_wallet`, `kora_voice`, `social_autoreply`, `inventory_alerts`, `sel_exchange`, `kora_host_api`

See `memory/psvibe-code-structure.md` for file-by-file reference.
See `memory/infrastructure.md` for coordination tools & sub-agent config.
See `memory/project-state.md` for current state & known issues.
