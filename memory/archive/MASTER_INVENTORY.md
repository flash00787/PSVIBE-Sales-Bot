# 🏭 MAIN VPS MASTER INVENTORY — Cross-Referenced & Validated

> **Server:** 5.223.81.16 (openClawAgent)  
> **Date:** 2026-05-28 16:09 UTC  
> **Uptime:** 1 day, 1:59 | **Load:** 1.28, 0.93, 0.65  
> **Disk:** 150G total, 31G used (22%)  
> **RAM:** 15Gi total, 4.3Gi used, 10Gi available  
> **Python:** 3.12.3 (system & venv)

---

## 📦 1. ACTIVE SERVICES (systemd)

| Service | Status | Directory | Binary | Bot Username |
|---|---|---|---|---|
| `psvibe-sale-bot` | ✅ running | `/root/psvibe-sales-bot` | `./main.py` (shebang) | Main sales bot |
| `psvibe_customer_bot` | ⚠️ running (restart=6) | `/root/psvibe-sales-bot` | `/root/venv/bin/python3 customer_bot/main.py` | `@psvibe_customer_service_bot` |
| `psvibe-api` | ✅ running | `/root/psvibe_api_server` | `../venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000` | API Server |
| `yyo-personal-wallet` | ✅ running | `/opt/yyo-personal-wallet/bot` → `/root/YYO-Personal-Wallet` | `../venv/bin/python3 main.py` | YYO Wallet Bot |
| `acm-personal-wallet` | ✅ running | `/root/ACM-Personal-Wallet/bot` | `../venv/bin/python main.py` | ACM Wallet Bot |

### Inactive / Backup only:
| Service | Status | Directory |
|---|---|---|
| `psvibe-wallet.service.bak` | ❌ (backup file, .bak extension) | n/a |

---

## 🐳 2. DOCKER CONTAINERS

| Container | Image | Ports | Status |
|---|---|---|---|
| `psvibe-mysql` | `mysql:8.0` | `127.0.0.1:3306` | ✅ Up 3h |
| `construction_bot` | `construction-bot-bot` (local build) | — | ✅ Up 39m |
| `oc-coco` | `ghcr.io/openclaw/openclaw:latest` | `0.0.0.0:3003→3000` | ✅ Healthy |
| `oc-nova` | `ghcr.io/openclaw/openclaw:latest` | `0.0.0.0:3002→3000` | ✅ Healthy |
| `openclaw-gateway-1` | `openclaw:local` | `0.0.0.0:18789-18790` | ✅ Up 2h |
| `openclaw-cli-1` | `openclaw:local` | — | ✅ Up 2h |
| `aungchanmyint-caddy-1` | `caddy:latest` | `0.0.0.0:80, 0.0.0.0:443` | ✅ Up 8h |
| `aungchanmyint-n8n-1` | `n8nio/n8n:latest` | `127.0.0.1:5678` | ✅ Up 8h |

---

## 🗂️ 3. COMPLETE DIRECTORY MAP

### `/root/` — Key Directories

```
/root/
├── psvibe-sales-bot/         ⭐ MAIN BOT (psvibe-sale-bot + customer_bot)
│   ├── main.py               → Sales bot entry point
│   ├── bot/                   → Core bot module
│   │   ├── __init__.py        → Main bot logic (2416 lines)
│   │   ├── handlers/          → Command handlers
│   │   └── utils/             → Utilities (time_utils, etc.)
│   ├── customer_bot/          → Customer service bot
│   │   ├── main.py            → Entry point
│   │   ├── handlers.py        → 37,818 bytes
│   │   ├── ai.py              → AI features (22,370 bytes)
│   │   ├── api.py             → API client (19,069 bytes)
│   │   └── data/              → Prompts, data files
│   ├── .env                   → 20 lines (non-secret config)
│   └── (NO git remote!)
│
├── psvibe-sale-bot/           ⚠️ DUPLICATE? (note: "sale" vs "sales")
│   ├── bot/                   → Partial copy
│   └── .env                   → 780 bytes
│
├── psvibe_api_server/         ⭐ API Server (FastAPI/Uvicorn)
│   ├── app.py                 → Main API app
│   ├── venv/                  → Own virtualenv
│   ├── service_account.json   → Google Sheets auth
│   └── (NO git remote!)
│
├── psvibe_fix_coordination/   → Coordination fix directory
├── YYO-Personal-Wallet/       ⭐ YYO Wallet Bot (#1)
│   ├── bot/main.py            → Wallet bot entry
│   ├── venv/                  → Own virtualenv
│   └── Git: flash00787/Personal-Wallet-Tele-Bot (main)
│       └── Latest: 0a9648b feat: add /buyasset command
│
├── ACM-Personal-Wallet/       ⭐ ACM Wallet Bot (#2)
│   ├── bot/main.py            → Wallet bot entry
│   ├── venv/                  → Own virtualenv
│   └── Git: flash00787/Personal-Wallet-Tele-Bot (main)
│       └── Latest: 353905f fix: /reset cmd
│
├── "Aung Chan Myint"/         → ACM project files (n8n, Caddy, etc.)
├── venv/                      ⭐ SHARED VENV (psvibe-sales-bot + customer_bot)
│   └── bin/python3 → /usr/bin/python3 (3.12.3)
│   └── Key packages: python-telegram-bot 22.7, gspread 6.2.1,
│       Flask 3.1.3, google-auth 2.53.0, aiohttp 3.13.5
├── openclaw/                  → OpenClaw source (uid 1000)
├── .openclaw/                 → OpenClaw data (uid 1000)
├── staging/                   → Staging deployment area
├── scripts/                   → Utility scripts
│   └── construction-bot-manager.sh → linked as /usr/local/bin/cb-manager
├── backups/                   → Backup directory
├── audit_*/                   → Audit reports (15 files)
├── sync-service/              → Sync service config
├── api-server/                → (uid 1000) Another API server?
├── agent_output/              → Agent task outputs
└── token_search_*.txt/sh      → Token search utilities
```

### `/opt/` — External Deployments

```
/opt/
├── construction-bot/          ⭐ Construction Bot (Docker, Node.js)
│   └── Git: flash00787/three_brothers_construction (main)
│       └── Latest: fae5a4f deploy: update bot.js from Replit
├── openclaw/                  → OpenClaw deployment
│   ├── coco/                  → Coco agent instance (port 3003)
│   ├── nova/                  → Nova agent instance (port 3002)
│   ├── yyo-personal-wallet/   → Nova's copy of wallet bot
│   └── docker-compose.yml
├── yyo-personal-wallet → /root/YYO-Personal-Wallet (symlink)
└── containerd/                → Container runtime
```

---

## 🔗 4. SYMLINKS & CLI TOOLS

| Link | Target | Purpose |
|---|---|---|
| `/opt/yyo-personal-wallet` | `/root/YYO-Personal-Wallet` | Service path |
| `/usr/local/bin/cb-manager` | `/root/scripts/construction-bot-manager.sh` | Construction bot CLI |
| `/usr/local/bin/nova-wallet` | Script (2026 bytes) | Nova wallet CLI tool |
| `/root/venv/bin/python` | `python3` | Default python |
| `/root/venv/bin/python3` | `/usr/bin/python3` | System Python 3.12.3 |

---

## 🧩 5. CROSS-REFERENCE: IMPORT CHAIN

### Sales Bot Entry (`main.py`)
```
from bot import main, keep_alive, ensure_sheet_headers
```

### Bot `__init__.py` Imports (line 2416)
```python
from bot.handlers import *  # noqa: F401,F403,E402
```
Loads: `gspread`, `asyncio`, `logging`, `fcntl`, `signal`, `concurrent.futures`, etc.

### Customer Bot Import Chain
```
customer_bot/main.py
  → customer_bot/handlers.py
    → customer_bot/data/prompts.py
      → bot.utils.time_utils (cross-module import!)
        → bot/__init__.py  (triggers full bot load)
          → bot/handlers/__init__.py
            → bot/handlers/admin.py  ← SYNTAX ERROR!
```

### Handler Internal Imports
- `bot/handlers/commands.py` → `from bot.handlers import *`
- `bot/handlers/help.py` → `from bot.handlers import *`
- `bot/handlers/main_menu.py` → `from bot.handlers import *`
- `bot/handlers/sales.py` → `from bot.handlers.stock import update_inv_total_k1`
- `bot/handlers/stock_in.py` → `from bot.handlers.stock import update_inv_total_k1`

---

## 🐛 6. ISSUES FOUND (Cross-Referenced)

### 🔴 CRITICAL — Syntax Errors Block Customer Bot
**Files affected:**
1. **`bot/handlers/waitlist.py` line 260** — stray `except Exception as e:` with no prior `try:`
2. **`bot/handlers/admin.py` line 126** — stray `else:` with no prior `if`/`try:`

**Impact:** The customer bot CRASHES on every restart (restart counter = 6). The import chain `customer_bot → bot.utils.time_utils → bot/__init__.py → handlers/__init__.py → admin.py` triggers compilation of the broken files.

**Note:** The sales bot (`psvibe-sale-bot.service`) may not hit these because it imports `from bot import main` which may use a different import path that skips the broken files at startup. This needs verification.

### 🟡 WARNING — `psvibe-sale-bot` vs `psvibe-sales-bot`
Two directories exist:
- `/root/psvibe-sales-bot/` — the MAIN bot (with `s`, 8 dirs) — this is the active one
- `/root/psvibe-sale-bot/` — duplicate/partial (without `s`, 3 dirs) — has only `bot/` subdir and `.env`

The systemd service `psvibe-sale-bot.service` points to `/root/psvibe-sales-bot` (the main one). The `psvibe-sale-bot` dir appears to be a leftover or staging area.

### 🟡 WARNING — No Git Remotes on Key Repos
- `/root/psvibe-sales-bot` — NO git remote (detached)
- `/root/psvibe_api_server` — NO git remote (detached)
- This means changes can't be pushed/pulled without manually adding remotes.

### 🟢 OK — Secrets Centralized
Secrets live in `/etc/psvibe/secrets.env` (36 lines, chmod 600). All psvibe services use `EnvironmentFile=/etc/psvibe/secrets.env`.

---

## 🔌 7. NETWORK PORTS

| Port | Service | Binding | Type |
|---|---|---|---|
| 80 | Caddy (ACM) | 0.0.0.0 | HTTP |
| 443 | Caddy (ACM) | 0.0.0.0 | HTTPS |
| 3306 | MySQL 8.0 | 127.0.0.1 | Database |
| 5678 | n8n (ACM) | 127.0.0.1 | Workflow |
| 8000 | PS VIBE API (uvicorn) | 0.0.0.0 | REST API |
| 3002 | OpenClaw Nova | 0.0.0.0 | Agent |
| 3003 | OpenClaw Coco | 0.0.0.0 | Agent |
| 18789-18790 | OpenClaw Gateway | 0.0.0.0 | Control |

---

## ⏰ 8. CRON JOBS

| Schedule | Command | Purpose |
|---|---|---|
| `30 15 * * *` (10 PM MMT) | `python3 send_daily_report.py` | Daily sales report |
| `*/5 * * * *` | `/root/scripts/clean-coco-processing.sh` | Coco processing cleanup |
| `*/5 * * * *` | `/root/scripts/check-coco-telegram.sh` | Coco Telegram health check |

---

## 📊 9. SERVICE DEPENDENCY MAP

```
┌─────────────────────────────────────────────────┐
│  psvibe-mysql (Docker, 127.0.0.1:3306)          │
└────────────┬────────────────────────────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌───────────┐   ┌──────────────┐
│psvibe-api │   │psvibe-sale-  │
│  :8000    │   │bot (main.py) │
└─────┬─────┘   └──────┬───────┘
      │                │
      │         ┌──────┴───────┐
      │         ▼              ▼
      │   ┌───────────┐  ┌──────────┐
      │   │ bot/      │  │customer_ │
      │   │ handlers/ │  │bot/main  │
      │   └───────────┘  └──────────┘
      │                       │
      │              imports bot.utils
      │              → triggers full bot import
      │              → SYNTAX ERROR ⚠️
      ▼
┌─────────────────┐
│ Google Sheets   │
│ (gspread)       │
└─────────────────┘

Independent bots:
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ yyo-personal-    │  │ acm-personal-    │  │ construction_bot │
│ wallet :systemd  │  │ wallet :systemd  │  │ :docker (Node)   │
│ /opt → /root/YYO │  │ /root/ACM-PW/    │  │ /opt/construct.. │
└──────────────────┘  └──────────────────┘  └──────────────────┘

Agent instances (Docker):
┌──────────┐  ┌──────────┐  ┌──────────────────┐
│ oc-nova  │  │ oc-coco  │  │ openclaw-gateway │
│ :3002    │  │ :3003    │  │ :18789-18790     │
└──────────┘  └──────────┘  └──────────────────┘
```

---

## 📝 10. KEY ENVIRONMENT FILES

| File | Lines | Notes |
|---|---|---|
| `/etc/psvibe/secrets.env` | 36 | Centralized secrets (600 perms) |
| `/root/psvibe-sales-bot/.env` | 20 | Non-secret operational config |
| `/opt/construction-bot/.env` | 5 | Bot token exposed in file ⚠️ |
| `/root/YYO-Personal-Wallet/.env` | — | Empty or missing |
| `/root/ACM-Personal-Wallet/.env` | — | Empty or missing |

---

## 🏷️ 11. GIT REMOTES SUMMARY

| Project | Remote | Branch | Latest Commit |
|---|---|---|---|
| YYO-Personal-Wallet | `flash00787/Personal-Wallet-Tele-Bot` | main | `0a9648b` /buyasset |
| ACM-Personal-Wallet | `flash00787/Personal-Wallet-Tele-Bot` | main | `353905f` /reset fix |
| construction-bot | `flash00787/three_brothers_construction` | main | `fae5a4f` deploy |
| psvibe-sales-bot | **NONE** | — | — |
| psvibe_api_server | **NONE** | — | — |

---

## ✅ VALIDATION SUMMARY

| Check | Result |
|---|---|
| Service count (5 files, 4 running) | ✅ Correct (`.bak` file is backup) |
| Customer bot crashes | 🔴 Syntax errors in admin.py + waitlist.py |
| Directory naming (sale vs sales) | 🟡 Two dirs; `psvibe-sales-bot` is active |
| Git tracking on core project | 🟡 Missing on sales-bot + api-server |
| Python syntax health | 🔴 FAILED — 2 files with broken try/except |
| Disk space | ✅ 22% used |
| Memory | ✅ 10Gi available |
| Port conflicts | ✅ No conflicts |
| Secrets exposure | 🟡 Construction bot token in `.env` |
| Systemd config correctness | ✅ All services properly configured |

---

## 🛠️ RECOMMENDED ACTIONS

1. **Fix syntax errors in `admin.py:126` and `waitlist.py:260`** — these crash the customer bot on restart
2. **Add git remotes** to psvibe-sales-bot and psvibe_api_server
3. **Clean up** duplicate `/root/psvibe-sale-bot/` directory (stale partial copy)
4. **Move construction bot token** out of `.env` to a secrets file or Docker secrets

---

*Generated by Agent 5/5 — Cross-reference & Validate — 2026-05-28T16:09Z*
