# Infrastructure Scan — 2026-06-02 13:03 UTC

## Summary
- **Host:** VPS 5.223.81.16 | Debian 12 | kernel 6.8.0-117 | uptime 5d 22h
- **Resources:** 15GB RAM (6.0G used, 9.2G avail), 150GB disk (24G used, 17%), load avg 1.29
- **Systemd services:** 9/9 running ✅
- **Docker containers:** 7/7 running ✅
- **Coordination tools:** 90 files at `/root/coordination/`, 10/11 critical scripts present
- **Quality Score:** 90/100 🟢 EXCELLENT (quick mode)
- **Issues found:** 6 (see below)

## System Health
| Metric | Value |
|--------|-------|
| Uptime | 5 days, 22:54 |
| CPU load | 1.29 / 0.90 / 0.78 |
| RAM | 6.0G / 15G (40%) |
| Disk | 24G / 150G (17%) |
| Swap | 0 (none configured) |

---

## Coordination Tools Inventory

### 11 Critical Scripts
| Script | Status | Lines | Notes |
|--------|--------|-------|-------|
| `fix_protocol.py` | ✅ PRESENT | 243 | Auto-commit safety |
| `workflow_engine.py` | ✅ PRESENT | 676 | 4 pipelines + rollback |
| `quality_gate.py` | ✅ PRESENT | 227 | Score: 90/100 |
| `batch_coordinator.py` | ✅ PRESENT | 1,217 | 11 hybrid batch commands |
| `health_monitor.py` | ❌ MISSING | — | Replaced by `kora_health_monitor.py` (326 lines) |
| `auto_doc_updater.py` | ✅ PRESENT | 115 | Post-fix docs updater |
| `tool_orchestrator.py` | ✅ PRESENT | 207 | 6-tool dependency runner |
| `check_alerts.py` | ✅ PRESENT | 13 | Health alert checker |
| `notifier.py` | ✅ PRESENT | 666 | Telegram notification module |
| `task_bridge.py` | ✅ PRESENT | 212 | Task bridge |
| `dashboard.py` | ✅ PRESENT | 198 | Web UI (port 9090) |

### Additional Notable Tools
| Tool | Lines | Purpose |
|------|-------|---------|
| `flow_analyzer.py` | 732 | State machine analysis |
| `arch_mapper.py` | 771 | Dependency graph (Mermaid/DOT) |
| `enhanced_validator.py` | 1,067 | Async/handler validation |
| `kora_health_monitor.py` | 326 | Health monitor (replaces health_monitor.py) |
| `auto_fix_monitor.py` | 386 | Auto-fix monitoring |
| `service_watchdog.py` | 206 | Auto-heal watchdog daemon |
| `fix_safety.py` | 675 | Fix safety checks |
| `queue_manager.py` | 368 | Task queuing |
| `timeout_auto_split.py` | 477 | Timeout handler |
| `fix_lock.py` | 193 | Fix locking |
| `deploy_manager.py` | 567 | Deployment manager |
| `verify_agent.py` | 424 | Verification agent |
| `spawning_manager.py` | 300 | Spawning manager |
| `lock_manager.py` | 162 | Lock management |
| `status_board.py` | 81 | Status board |

**Total coordination directory: 90 files** (including .md docs, JSON state, logs, plans, snapshots, backups)

### Quality Gate Detail
- **Mode:** quick
- **Score:** 90/100 (90%) 🟢 EXCELLENT
- **Timestamp:** 2026-06-02T13:04:51 UTC
- **Alerts:** 2 active — `weekly_import_scan_2026-06-01_080001.json`, `latest_scan_summary.json` (low-priority scan artifacts)
- **No print statements detected** ✅
- **No bare excepts detected** ✅

---

## Service Health

### Systemd Services (9 running)

| Service | Status | Uptime | Memory | PID |
|---------|--------|--------|--------|-----|
| `psvibe-sale-bot` | ✅ active (running) | 48 min | 58.4M | 2630999 |
| `psvibe_customer_bot` | ✅ active (running) | 46 min | 71.9M | 2631315 |
| `psvibe-api` | ✅ active (running) | 48 min | 49.1M | 2630996 |
| `cloudflared-tunnel` | ✅ active (running) | 2 days | 17.4M | 1803894 |
| `psvibe-watchdog` | ✅ active (running) | 2 days | 6.0M | 1892241 |
| `kora-host-api` | ✅ active (running) | 2 days | 9.8M | 1891745 |
| `psvibe-dashboard` | ✅ active (running) | 2 days | 10.1M | 1911371 |
| `acm-personal-wallet` | ✅ active (running) | 4 days | 75.8M | 412599 |
| `yyo-personal-wallet` | ✅ active (running) | 4 days | 88.1M | 424554 |

⚠️ **Note:** PS VIBE bots were restarted ~48 min ago (12:16-12:18 UTC), suggesting a recent deployment or restart event. Cloudflared, watchdog, kora-host-api, and dashboard have been stable for 2+ days.

### Docker Containers (7 running)

| Container | Image | Status | Ports |
|-----------|-------|--------|-------|
| `construction_bot` | construction-bot-bot | Up 5h | — |
| `oc-coco` | openclaw:latest (ghcr) | Up 4d (healthy) | 3003→3000 |
| `openclaw-openclaw-gateway-1` | openclaw:local | Up 5h (healthy) | 18789-18790 |
| `psvibe-mysql` | mysql:8.0 | Up 4d | 127.0.0.1:3306 |
| `aungchanmyint-caddy-1` | caddy:latest | Up 2d | 80, 443 |
| `aungchanmyint-n8n-1` | n8n:latest | Up 5d | 127.0.0.1:5678 |
| `oc-nova` | openclaw:latest (ghcr) | Up 3h (healthy) | 3002→3000 |

**Resource note:** The OpenClaw gateway container is using 108% CPU and 2.45GB RAM (16%) — this is the container I'm running in, which is expected for an active session.

---

## Git Repo Status

### PS VIBE Sales Bot (`/root/psvibe-sales-bot/`)
- **GitHub:** `flash00787/PSVIBE-Sales-Bot`
- **Status:** ✅ **CLEAN** — no uncommitted changes
- **Latest commits (top 5):**
  1. `941d0a5` — feat: booking-console status link
  2. `6e3c556` — fix: admin booking confirm → notify customer
  3. `3c094b5` — [auto] commit pending admin_bookings changes
  4. `ec453a8` — [auto] 2026-06-02 09:30 UTC
  5. `2e8fb8a` — [auto] 2026-06-02 09:00 UTC
- **Disk:** 1,040 KB (109 .py files)

### PS VIBE API Server (`/root/psvibe_api_server/`)
- **GitHub:** `flash00787/PSVIBE-API-Server`
- **Status:** ⚠️ **DIRTY** — modified files + untracked files
- **Modified tracked:**
  - `app.py` (main file, 61KB)
  - `patch_routes.py`
  - `receipt_template.html`
  - `sync_service.py`
- **Untracked:**
  - `app.py.pre_fix_20260602`
  - `patch_routes.py.pre_fix_20260602`
  - `server.log.1.gz`
  - `sync_console_mults.py`
- **Latest commits:**
  1. `af0b6dc` — fix: API key mismatch fixes (Jun 2)
  2. `4dcb714` — fix: member balance reads from stale MySQL (Jun 1)
  3. `98cee1c` — [auto] 2026-06-01: uncommitted API server changes
  4. `53846d6` — pre-finance-migration
  5. `0052cba` — ci: add GitHub Actions auto-deploy workflow
- **Backup bloat:** 14+ `.bak` files totaling ~1.2MB (app.py.bak.*)

### Construction Bot (`/opt/construction-bot/`)
- **Status:** 🔴 **HEAVILY DIRTY** — many modified files
- Modified: `bot.js`, `.gitignore`, `Dockerfile`, `docker-compose.yml`, `package.json`, etc.
- Untracked: `.env`, `patches/`, `bot.js.bak2`, `package-lock.json`, etc.
- Disk: 848 KB

### YYO Personal Wallet (`/opt/yyo-personal-wallet/`)
- **Status:** ⚠️ **DIRTY** — modified tracked files (artifacts/api-server/*)
- Modified: `.agents/`, `.gitignore`, `.npmrc`, `.replit`, artifacts config
- Disk: 308 KB

---

## Infrastructure Doc Accuracy

File: `/home/node/.openclaw/workspace/memory/infrastructure.md`

| Claim | Actual | Match? |
|-------|--------|--------|
| 25+ coordination tools at `/root/coordination/` | 90 files total | ✅ (underestimate, actual more) |
| Fix Protocol 120+ lines | 243 lines | ✅ |
| Workflow Engine 330+ lines | 676 lines | ✅ (underestimated) |
| Batch Coordinator v2 1200 lines | 1,217 lines | ✅ |
| Tool Orchestrator 207 lines | 207 lines | ✅ |
| Quality Gate "unified score 0-100" | 90/100 | ⚠️ No current score documented |
| Dashboard "Web UI port 9090" | Active psvibe-dashboard service | ✅ |
| MySQL Docker `psvibe-mysql` | Running on 127.0.0.1:3306 | ✅ |
| Cloudflare Tunnel | Active, 2 days uptime | ✅ |

**Missing from doc:**
- ❌ `kora_health_monitor.py` (replaces health_monitor.py)
- ❌ `kora-host-api.service` — Kora Host API Bridge
- ❌ `psvibe-dashboard.service` — Dashboard service
- ❌ `acm-personal-wallet.service` — ACM's Personal Wallet Bot
- ❌ `yyo-personal-wallet.service` — YYO Wallet Bot
- ❌ Docker: construction_bot, n8n, caddy, oc-coco, oc-nova
- ❌ Construction Bot at `/opt/construction-bot/`
- ❌ Quality Gate current score (90/100)

---

## Recommendations

### 🔴 Critical
1. **Commit & push API server changes** — `/root/psvibe_api_server/` has uncommitted modifications to critical files (`app.py`, `patch_routes.py`, `sync_service.py`). Risk of losing work.
2. **Clean up .bak backups in API server** — 14+ backup files (~1.2MB) clutter the repo root. Move to `backups/` or `.gitignore`.

### 🟡 Medium
3. **Document missing services** — Update `memory/infrastructure.md` with `kora-host-api`, `psvibe-dashboard`, `acm-personal-wallet`, `yyo-personal-wallet`, and all Docker containers.
4. **Recent bot restart** — Both PS VIBE bots restarted ~48 min ago. Investigate cause (deploy? crash-recovery?).
5. **Construction Bot git hygiene** — `/opt/construction-bot/` has extensive uncommitted changes. Review and commit or reset.

### 🟢 Low
6. **Quality gate alerts** — 2 active alerts from weekly import scan; verify they're expected artifacts, not real issues.
7. **Swap warning** — No swap configured on host with 15GB RAM. Consider adding swap for memory safety margin.
8. **Update doc with current Quality Gate score** (90/100).
