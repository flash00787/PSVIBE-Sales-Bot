# PS VIBE Sales Bot — MySQL Sync & Security Audit

**Date:** 2026-05-28 12:04 UTC  
**Server:** `5.223.81.16` (root)  
**Audited by:** OpenClaw Subagent

---

## 1. Architecture Overview

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  Sales Bot (8080)    │────▶│  API Server (8000)   │────▶│  MySQL (Docker)     │
│  /root/psvibe-sale-  │     │  /root/psvibe_api_   │     │  psvibe-mysql:8.0   │
│  bot/bot/main.py     │     │  server/app.py       │     │  0.0.0.0:3306 ⚠️     │
│  (SQLite read cache)  │     │  (FastAPI + uvicorn) │     │                     │
└─────────────────────┘     └──────────────────────┘     └─────────────────────┘
                                      │
                                      ▼
                             ┌──────────────────────┐
                             │  Google Sheets       │
                             │  (source of truth)   │
                             └──────────────────────┘
```

- **Sales Bot** uses SQLite as a local read cache (`/root/psvibe-sale-bot/sqlite/db_manager.py`)
- **API Server** (`/root/psvibe_api_server/app.py`) is the bridge: it syncs Google Sheets → MySQL and serves REST endpoints
- **MySQL** (Docker `psvibe-mysql:8.0`) stores sync'd sheet data: `console_status`, `games_library`, `member_wallets`, `staff_records`

---

## 2. MySQL Sync Status

| Metric | Value | Rating |
|--------|-------|--------|
| MySQL Container | **Running** (`psvibe-mysql:8.0`) | ✅ Healthy |
| Sync Service | **Running** | ✅ |
| Last Sync | 2026-05-28 18:31 MMT (~30 min ago) | ✅ Recent |

### Sheet Sync Detail

| Sheet Name | Rows Synced | Last Sync (MMT) | Status |
|------------|-------------|-----------------|--------|
| `console_status` | 10 | 2026-05-28 18:31:31 | ✅ ok |
| `games_library` | 37 | 2026-05-28 18:31:30 | ✅ ok |
| `member_wallets` | 3 | 2026-05-28 18:31:29 | ✅ ok |
| `staff_records` | 2 | 2026-05-28 18:31:31 | ✅ ok |

### Members
```
PSV_A_000
PSV_A_001
PSV_A_002
```
(3 members total)

### Health Check
```json
{"success":true,"data":{"mysql":true,"sync_running":true}}
```

**Verdict:** MySQL sync is functioning correctly. All 4 sheets are syncing on schedule, no errors.

---

## 3. Security Posture

### 🔴 Critical Issues

#### 3.1 MySQL Port 3306 Exposed to the Internet
```
Status: CRITICAL — IMMEDIATE ACTION REQUIRED
```

- MySQL Docker container is bound to **`0.0.0.0:3306`** (all network interfaces)
- UFW firewall has **NO rule blocking port 3306**
- Docker's own iptables rule: `ACCEPT 0.0.0.0/0 → 172.17.0.2:3306` (accepts from anywhere)
- **Verified externally reachable:** `nc -zv 5.223.81.16 3306` succeeded

This means anyone on the internet can attempt to connect to MySQL and brute-force credentials. This is the #1 security risk on this server.

**Fix:**
```bash
# Option A: Block with UFW (also add to iptables since Docker bypasses UFW)
iptables -I DOCKER-USER -p tcp --dport 3306 -j DROP
iptables -I DOCKER-USER -p tcp --dport 3306 -s 172.17.0.0/16 -j ACCEPT   # allow internal docker network
iptables -I DOCKER-USER -p tcp --dport 3306 -s 127.0.0.1 -j ACCEPT

# Option B: Recreate container binding only to 127.0.0.1
# (requires updating connection strings to use 127.0.0.1)
```

#### 3.2 MySQL Passwords Visible in Docker Inspect
```
Status: CRITICAL — Credential leak vector
```

MySQL credentials are exposed to anyone with Docker access:
```
MYSQL_ROOT_PASSWORD: PsVibe@MySQL2024!
MYSQL_PASSWORD:      PsVibe@User2024!
```

`docker inspect psvibe-mysql` reveals these in plain text. Any user in the `docker` group can read them.

**Fix:** Use Docker secrets or an env-file with restricted permissions. At minimum, ensure only root is in the `docker` group.

---

### 🟡 Needs Work

#### 3.3 `service_account.json` — World-Readable
```
-rw-r--r-- 1 root root 2376 /root/psvibe-sale-bot/service_account.json
```
- Permissions: **644** — any local user can read the Google service account key
- Contains: `private_key`, `client_email`, `project_id`
- Client email: `user-408@ps-vibe-sales-tele-bot.iam.gserviceaccount.com`

**Fix:** `chmod 600 /root/psvibe-sale-bot/service_account.json`

#### 3.4 Python Files — World-Writable
```
-rw-rw-rw- 1 root root 22130 /root/psvibe_api_server/analytics.py
-rw-rw-rw- 1 root root 14678 /root/psvibe_api_server/dashboard_bot.py
```
- Permissions: **666** — any user can modify these files
- This is a code injection risk: an attacker who gains any local access could inject malicious code that executes on the next restart

**Fix:** `chmod 644` (or `640`) on all `.py` files in `/root/psvibe_api_server/`

#### 3.5 API Server Listening on `0.0.0.0:8000`
```
LISTEN 0 2048 0.0.0.0:8000 ... uvicorn
```
- UFW does restrict port 8000 to Docker networks only (172.17.0.0/16, 172.18.0.0/16, 172.20.0.0/16)
- However, binding to 0.0.0.0 instead of 127.0.0.1 means if UFW is ever disabled or misconfigured, the API becomes publicly accessible
- CORS allows `*` (all origins)

**Fix:** Bind uvicorn to `127.0.0.1` if only local/Docker clients need access, or restrict via Caddy reverse proxy instead.

---

### ✅ Good

| Item | Details | Rating |
|------|---------|--------|
| `.env` permissions | `-rw-------` (600) — only root | ✅ Good |
| `secrets.env` permissions | `-rw-------` (600) — only root | ✅ Good |
| `secret.json` | **Not found** — no legacy secret file | ✅ Good |
| Secrets in `.env` | Only non-secret operational config; secrets in `/etc/psvibe/secrets.env` | ✅ Good |
| API Key Auth | All endpoints require `?api_key=` or `X-API-Key` header | ✅ Good |
| No hardcoded passwords in code | MySQL creds only in secrets.env | ✅ Good |
| UFW Firewall Active | Default deny incoming, only 22/80/443 open to world | ✅ Good |
| SSH | Key-based auth only (port 22) | ✅ Good |
| Caddy Reverse Proxy | Ports 80/443 via Docker (likely Caddy) | ✅ Good |

---

## 4. Open Ports Summary

| Port | Process | Exposure | Risk |
|------|---------|----------|------|
| 22 | SSH (sshd) | Internet | ✅ Key-auth only |
| 80 | Docker (Caddy) | Internet | ✅ Reverse proxy |
| 443 | Docker (Caddy) | Internet | ✅ Reverse proxy |
| **3306** | **MySQL Docker** | **⚠️ Internet** | **🔴 CRITICAL** |
| 5678 | Docker proxy | 127.0.0.1 only | ✅ Local only |
| 8000 | Uvicorn API | Docker networks | 🟡 Needs monitoring |
| 8080 | Python3 (Sales Bot) | 0.0.0.0 (no UFW rule!) | 🟡 Check if needed |
| 3002 | Docker proxy | 0.0.0.0 | Unknown service |
| 18789-18790 | Docker proxy | 0.0.0.0 | Unknown services |

**⚠️ Port 8080** also has no UFW rule — needs verification whether it's intentional.

---

## 5. API Server Code Location

The API server runs from a **separate directory** from the sales bot:

```
/root/psvibe_api_server/
├── app.py              (71,910 bytes — main FastAPI app, 97+ endpoints)
├── analytics.py        (22,130 bytes — ⚠️ world-writable)
├── config.py           (1,736 bytes — all config imports)
├── dashboard_bot.py    (14,678 bytes — ⚠️ world-writable)
├── db_client.py        (15,510 bytes — MySQL client)
├── models.py           (469 bytes — SQLAlchemy models)
├── sheets_client.py    (7,335 bytes — Google Sheets client)
├── sync_service.py     (31,861 bytes — sync orchestrator)
├── requirements.txt    (105 bytes)
└── venv/               (Python 3.12 virtualenv)
```

Run command: `/root/psvibe_api_server/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000`

The sales bot is at `/root/psvibe-sale-bot/`:
```
/root/psvibe-sale-bot/
├── main.py             (entry point, port 8080)
├── app.py              (secondary app)
├── bot/
│   ├── __init__.py     (bot core)
│   ├── app.py          (bot's own Flask app?)
│   ├── api_client.py   (calls API server at 8000)
│   ├── keep_alive.py   (Flask keepalive server)
│   └── handlers/       (Telegram handlers)
├── sqlite/
│   ├── db_manager.py   (SQLite read-cache, not MySQL)
│   └── setup.py
└── customer_bot/
    └── main.py         (separate customer-facing bot)
```

---

## 6. Recommendations (Priority Order)

| # | Action | Priority | Effort |
|---|--------|----------|--------|
| 1 | **Block MySQL port 3306 from internet** with iptables/UFW | 🔴 CRITICAL | 5 min |
| 2 | **Rotate MySQL passwords** (they're in Docker inspect + exposed to internet) | 🔴 CRITICAL | 15 min |
| 3 | Fix `service_account.json` to `chmod 600` | 🟡 HIGH | 1 min |
| 4 | Fix `analytics.py` and `dashboard_bot.py` to `chmod 644` | 🟡 HIGH | 1 min |
| 5 | Bind MySQL Docker to `127.0.0.1:3306` instead of `0.0.0.0` | 🟡 HIGH | 10 min |
| 6 | Review port 8080 and 3002 exposure | 🟡 MEDIUM | 15 min |
| 7 | Bind uvicorn to `127.0.0.1` if only local clients need it | 🟡 MEDIUM | 5 min |
| 8 | Review unknown Docker services on ports 3002, 18789, 18790 | 🟢 LOW | 10 min |

---

## 7. Quick Fix Commands (Copy-Paste)

```bash
# 1. Block MySQL from internet (iptables — survives until reboot)
iptables -I DOCKER-USER 1 -p tcp --dport 3306 ! -s 127.0.0.1 -j DROP
# To persist: install iptables-persistent or add to /etc/rc.local

# 2. Fix file permissions
chmod 600 /root/psvibe-sale-bot/service_account.json
chmod 644 /root/psvibe_api_server/analytics.py
chmod 644 /root/psvibe_api_server/dashboard_bot.py

# 3. Verify MySQL is blocked
nc -zv 5.223.81.16 3306   # Should now fail
```

---

*Audit complete. The MySQL sync infrastructure is healthy, but the MySQL port exposure is a critical vulnerability that should be addressed immediately.*
