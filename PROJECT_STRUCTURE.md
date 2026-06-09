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

See `memory/psvibe-code-structure.md` for file-by-file reference.
See `memory/infrastructure.md` for coordination tools & sub-agent config.
See `memory/project-state.md` for current state & known issues.
