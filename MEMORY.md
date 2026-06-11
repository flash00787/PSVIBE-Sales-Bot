# MEMORY.md — Kora's Long-Term Memory Index

> 🗂️ Short master index. Detailed history → module files in `memory/`.
> Search via `memory_search` or `memory_get(path=memory/<file>.md)`.

## 🔴 Core Docs (workspace root)
| File | Purpose |
|------|---------|
| `GOLDEN_RULES.md` | Golden rules — never break |
| `HEARTBEAT.md` | Periodic tasks & cron schedule |
| `AGENTS.md` | Identity, workflow, hybrid spawning |
| `SOUL.md` | Personality, language, tone |
| `TOOLS.md` | SSH, bots, commands, API keys |
| `PROJECT_STRUCTURE.md` | Project overview (2 repos) |

## 📁 Module Files (`memory/`)

### Systems & Accounts
- **`memory/contacts.md`** — 👥 Contacts, Boss info, friend contacts
- **`memory/emails.md`** — 📧 Gmail accounts, API, Google Drive

### Infrastructure
- **`memory/infrastructure.md`** — 🏗️ Bot paths, services, MySQL, coordination tools
- **`memory/config.md`** — 🔧 Gateway config, lock_monitor, fix_protocol
- **`memory/psvibe-code-structure.md`** — 📂 File-by-file code reference (both repos)
- **`memory/project-state.md`** — 📋 Current project state & known issues

### SOPs & Frameworks (`memory/sop/`)
- **`memory/sop/SPAWN_PROTOCOL.md`** — 🔀 Sub-agent spawn rules & hybrid spawning
- **`memory/sop/POST_TASK_SOP.md`** — 📝 Post-task documentation SOP
- **`memory/sop/COORDINATION_FRAMEWORK.md`** — 🏗️ Agent coordination framework
- **`memory/sop/HELPER_GUIDELINES.md`** — 👷 Helper agent guidelines
- **`memory/sop/heartbeat-procedures.md`** — 💓 Full heartbeat procedures
- **`memory/sop/DISPATCH_MANAGER_SOP.md`** — 📋 Dispatch manager SOP
- **`memory/sop/FINDINGS_MANAGER_SOP.md`** — 🔍 Findings manager SOP
- **`memory/sop/TASK_PLANNER_SOP.md`** — 📊 Task planner SOP
- **`memory/sop/STATUS_REPORTER_SOP.md`** — 📈 Status reporter SOP
- **`memory/sop/VERIFY_AGENT_SOP.md`** — ✅ Verify agent SOP
- **`memory/sop/DEPLOY_MANAGER_SOP.md`** — 🚀 Deploy manager SOP
- **`memory/sop/GIT_SYNC_SOP.md`** — 🔄 Git sync SOP
- **`memory/sop/SPAWNING_MANAGER_SOP.md`** — 🥚 Spawning manager SOP

### Operations
- **`memory/tools-commands.md`** — 🛠️ All coordination tool commands reference
- **`memory/memory-usage-guide.md`** — 📖 How to use the memory system (decision tree, write rules)

### Memory Automation (Phase 3)
- **`memory/session_summary.py`** — Session end auto-summary
- **`memory/memory_index.py`** — Topic search index (1,146 topics)
- **`memory/priority_engine.py`** — P0-P3 priority classifier
- **`memory/memory_pruner.py`** — Dedup & prune (target ~20KB MEMORY.md)
- **`memory/daily_digest.py`** — Daily digest generator
- **`memory/git_backup.py`** — Memory git auto-backup
- **`memory/knowledge_graph.py`** — Entity relationship graph (54 nodes)

### Bugs, Fixes & Lessons
- **`memory/bug-patterns.md`** — 🐛 All known bug patterns (fixed & known)
- **`memory/ERROR_PATTERNS.md`** — ⚡ Quick ref: error → root cause → fix
- **`memory/lessons.md`** — 📚 Critical lessons learned
- **`memory/fix-history.md`** — 📋 Recent fix history (by date)

### Daily Logs
- **`memory/2026-06-02.md`** through **`memory/2026-06-11.md`** — Raw daily logs
- **`memory/archive/`** — Old/stale documentation

---

## ⏰ Quick Ref: Timezone
- Boss: **Asia/Yangon (UTC+6:30)**
- ALL UTC → Myanmar Time before telling Boss

## 🛡️ Quick Ref: Fix Protocol
```bash
python3 /root/coordination/fix_protocol.py --start <file>  # Before edit
python3 /root/coordination/fix_protocol.py --complete       # After edit
```
See `memory/config.md` for details. See `memory/lessons.md` for spawn & lock lessons.

---

## 📌 Current Services (June 11, 13:30 UTC)
| Service | Status |
|---------|--------|
| psvibe-api | ✅ |
| psvibe-sale-bot | ✅ |
| psvibe_customer_bot | ✅ |
| psvibe-dashboard | ✅ |
| Caddy (nginx proxy) | ✅ |
| n8n | ✅ |
| MySQL | ✅ |
| cloudflared-tunnel | ✅ |
| Kora Dashboard | ✅ |
| Health Monitor | 93.3 / 100 ✅ |

---

## 🧪 Critical Lessons Archive

### API & Code Patterns
- **API auto-unwrap:** `_api_get()` unwraps `{success,data}` → DON'T check `resp.get("success")` or `resp.get("data")` again
- **`"error" in resp` ≠ `resp.get("error")`:** When API returns `error:null` key, `in` operator is always True. Use truthy check.
- **API response_model strips undeclared fields** (confirmed multiple times)
- **`x if x else default` breaks on `0`** — use `x if x is not None else default`
- **Two auth mechanisms in api_client.py:** `_http_request` uses X-API-Key header; `api_post`/`api_get` were using query param only (fixed June 8)
- **Python `.pyc` cache stale after edit:** Must clear `__pycache__` then restart
- **String replace() fails silently on whitespace mismatch:** Verify with `repr()`
- **sed + Python strings = disaster:** Use `str.replace()` instead
- **Elif chains must cover all variants:** `"wave"` ≠ `"wavepay"`
- **PyMySQL `%` in LIKE:** `LIKE 'Topup%'` → format string error. Use `CONCAT('Topup', CHAR(37))`
- **3 simultaneous records = triple-count:** topup creates topup_log + cash_movements inject + sales_daily
- **nearest-50 rounding:** `round(x/50)*50`

### Booking System
- **3-layer bugs are common:** 1 symptom often has 3+ root causes (intercept menu missing, auto-unwrap API, Unicode corruption)
- **Unicode escape sequences are fragile:** Always verify with `python3 -c "print(...)"` before deploying
- **Burmese Unicode verification:** `U+101B U+101B` (ရရ) ≠ `U+101B U+103E` (ရှ)

### Infrastructure
- **systemctl/systemd unavailable on VPS:** Uvicorn via nohup; restart with `pkill -HUP -f 'uvicorn'`
- **systemctl restart can silently fail:** Verify PID change, fallback `kill -9`
- **JWT expires on API restart:** Users must re-login
- **Session cron jobs <60s cause takeover errors:** Minimum 5-min interval for lock operations
- **Session file bloat (446MB/500MB):** 1,305 session files; Gateway auto-prune handles this
- **Vite lazy chunk import mismatch:** Renaming main JS alone isn't enough — all 22+ lazy imports must be updated

### Financial
- **BS equation:** Assets = L+E always. Depreciation Reserve goes in Equity
- **Cash Flow closing = Web Finance:** Must use identical income allocation per account
- **Inject exclusion = retained formula adjustment:** When excluding injects from assets, add to retained or BS breaks
- **Topup = deferred liability, not revenue:** Only wallet_consumed is recognized revenue
- **test entries → delete, don't dispose:** Prevents zombie records
- **cash_movements stores labels, code uses keys:** Maintain mapping dict (`"kbz_bank"` → `"KBZ Bank"`)

### Memory System
- **"Stay quiet" rules NEVER apply to Boss messages:** Only heartbeat/outreach
- **Boss messages = ALWAYS respond:** No quiet hours for incoming messages
- **MEMORY.md truncation:** Session context loads ~11KB of ~40KB file. Keep MEMORY.md lean — use module files for details

---

## 📋 Recent Fix History (June 6-11)
| Date | Fix | File(s) |
|------|-----|---------|
| June 11 | Pending — Kora Dashboard: Logo favicon update | `kora_dashboard/index.html` |
| June 11 | Kora Dashboard v2 — 10 Features (Booking Schedule, Sales Chart, Member Lookup, Alerts, Food Stock, EOD Summary, Language Toggle, QR Share, Quick Commands, Auto-Refresh) | `kora_dashboard/*` |
| June 11 | Login refresh bug (API_BASE: absolute→relative) | `kora_dashboard/index.html` |
| June 11 | Web Commands → VPS execution | `kora_dashboard/*`, `vps_bridge.sh` |
| June 10 | Sales Daily lazy-load fix (Cloudflare n8n cache) | `dashboard-dist/*.js` (22 chunks) |
| June 10 | Prepaid Rent Amortization + auto-cron | `/root/scripts/auto_amortize.py` |
| June 10 | Cash Flow finalized | `dashboard_routes.py` |
| June 10 | Shareholders setup (3 ppl, 300M) | `dashboard_routes.py`, `StockIn.vue` |
| June 10 | KPay triple-count fix → Bot=Web=BS match | `dashboard_routes.py`, `patch_routes.py` |
| June 9 | KPay triple-count → Bot=Web match | `dashboard_routes.py`, `patch_routes.py` |
| June 9 | Depreciation Engine + P&L/BS/CF + Rent | `dashboard_routes.py` |
| June 9 | Stock In Edit + Payment fix + KBZ backdate | `dashboard_routes.py`, `StockIn.vue` |
| June 9 | Notification Fixes (Cancel + 10-min reminder) | `booking_flow.py`, `auto_cancel_no_shows.py` |
| June 9 | Financial Statements — 3 pages + BS balanced | `dashboard_routes.py` |
| June 8 | Coupon Invalid bug (`"error" in resp` fix) | `bot/handlers/discount.py` |
| June 8 | OPEX System built (9 categories) | `app.py`, `opex.py` |
| June 8 | Financial Dashboard recovery (git disaster) | `dashboard_routes.py` (restored from `.bak.v3.1`) |
| June 8 | Food Sale flow fix (KeyError mins/m_id) | `bot/handlers/sales.py` |
| June 8 | Stock In → Payment integration | `app.py`, `stock_in.py`, `dashboard_routes.py` |
| June 7 | Account Balance discrepancy (Cash 6-layer fix) | `dashboard_routes.py`, `patch_routes.py` |
| June 7 | Food Menu Category Grouping | `app.py`, `api.py`, bot handlers |
| June 7 | Inject/Eject Feature + Web Admin | `app.py`, `patch_routes.py`, bot handlers |
| June 7 | Game Library fixes (SSD prefix, dupes) | `app.py`, DB cleanup |
| June 7 | Session Timer Reminder fix | `booking_handlers.py`, `scheduler.py` |
| June 7 | Food Sale Feature | `sales.py`, `food.py` |
| June 6 | Food Menu Fix (3-layer: intercept + auto-unwrap + Unicode) | `customer_bot/handlers.py`, `main.py` |
| June 6 | Duration Loop + Reserved Cross-Check | `booking_handlers.py`, `api_client.py` |

---

## 🤖 Kora Dashboard (June 11)
Built at `/root/.openclaw/workspace/kora_dashboard/` — served via API: `https://ps-vibe.com/kora/`

**10 Features:**
1. 📅 Real Booking Schedule (9AM-9PM timeline, color-coded)
2. 💰 Real Sales Chart (7-day Canvas bar chart)
3. 🔍 Member Quick Lookup (search + wallet balance)
4. ⚠️ Smart Alerts Panel (health alerts)
5. 📦 Food Stock Status (menu + stock levels)
6. 📊 End-of-Day Summary (today's panel)
7. 🌐 Language Toggle (MY/EN)
8. 🔗 QR Share Dashboard Link
9. ⚡ Quick Commands (Health, Docker, Uptime, Backups)
10. 🔄 Auto-Refresh every 60s

**Favicon:** Blue Cross logo (from `logo-icon.png`), served via `/favicon.svg`
