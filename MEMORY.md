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

## 📌 Current Services (June 11, 18:00 UTC)
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

- **MEMORY.md truncation:** Session context loads ~11KB of ~40KB file. Keep MEMORY.md lean — use module files for details
- **Session cron jobs <60s cause takeover errors:** Minimum 5-min interval for lock operations
- **Session file bloat (446MB/500MB):** 1,305 session files; Gateway auto-prune handles this

---

## 📋 Recent Fix History (June 6-11)
| Date | Fix | File(s) |
|------|-----|---------|
| June 11 | Pending — Kora Dashboard: Logo favicon update | `kora_dashboard/index.html` |
| June 11 | Kora Dashboard v2 — 10 Features (Booking Schedule, Sales Chart, Member Lookup, Alerts, Food Stock, EOD Summary, Language Toggle, QR Share, Quick Commands, Auto-Refresh) | `kora_dashboard/*` |
| June 11 | Login refresh bug (API_BASE: absolute→relative) | `kora_dashboard/index.html` |
| June 11 | Web Commands → VPS execution | `kora_dashboard/*`, `vps_bridge.sh` |
| June 10 | Sales Daily lazy-load fix (Cloudflare n8n cache) | `dashboard-dist/*.js` (22 chunks) |

---

## 🤖 Kora Automation — Active Tools (June 11)
19 automation tools deployed: Smart Alerts, Auto Maintenance, Multi-Channel, Console Booking, Smart Reminder, Kora Dashboard (10 features, :9091), Research Agent, Auto-Reply, Git Backup, Memory Manager, Uptime Monitor, AI Bot Enhancer, BI Dashboard, Notification Center, Disaster Recovery, Knowledge Wiki (9 pages), Security Audit, i18n (75 keys MY/EN). See `memory/2026-06-11.md` for full details.

## 🧹 Session Cleanup (June 11)
- Freed 168 MB (855→687 MB), now 129 MB in session files (well below 500MB limit)
- 5 auto-protection layers in cleanup script; cleanup cron every 10 min

## ☁️ Cloudflare — Resolved (June 11)
- Account flagged for ID verification → Boss completed it, all sanctions lifted

## 📋 Pending — Boss Action Needed
1. **n8n Payment (€25.68)** — 2nd notice, subscription may expire
2. **GitHub Deploy Failing** — PSVIBE-API-Server master branch deploy workflow failing

## 🩺 Latest Heartbeat (June 11, 15:18 UTC)
- Health Monitor: 93.3/100 | Docker: 7/7 | Disk: 18% | RAM: 11Gi | Uptime: 14d+
- MEMORY.md: auto-trim cron active | Git backup: committed | Index: 1146 topics
- 0 stuck/pending agents | No critical alerts
- *Heavy optimization day — session files cleaned, MEMORY.md trimmed, Cloudflare resolved, 20+ Kora upgrades deployed.*

---

## 📋 June 12 — Summary

### 🔴 SSH Crisis: ISP-Level IP Blocking
- **IP 5.223.81.16 completely unreachable** from Boss's Myanmar ISP (ping fails, not just SSH ports)
- DPI detects SSH protocol on ANY port (22, 80, 443, 22222 all blocked)
- **Workaround:** Web SSH via `https://ps-vibe.com/shell/` (wssh + Cloudflare Tunnel) — working ✅
- **Pending:** Cloudflare Zero Trust → Tunnels → Public Hostnames config for `shell.ps-vibe.com`
- **Lesson:** ISP can block entire IP routing, not just ports; Cloudflare Tunnel + HTTPS bypasses it

### ✅ Fixes Deployed
| Fix | Files |
|-----|-------|
| Game Library: 23 titles corrected in MySQL | `games_library` (41 rows), `console_games` (68 rows) |
| Dashboard Games: final_status → In Use/Available | `fix_games_library_status.py` |
| FAQ intercept disabled (wrong game count) | `customer_bot/handlers.py` (commented out) |
| Booking wallet skip (booking_id guard) | `sales.py` line 1677 |
| Session timer message_thread_id | `booking_flow.py`, `session_reminder_store.py`, `booking.py` |
| Booking game selection [:30] limit removed | `booking.py` lines 442 & 610 |
| Food Menu: Soft Drinks + Coffee categories | 5 files (Dashboard, Customer Bot, Sale Bot, API) |
| Account balances verified correct | All operating accounts match |
| Low stock alert: 30min → 4hr | `/var/spool/cron/crontabs/root` |
| Kora Smart-Reminder: thread ID → 125192 | `smart_reminder.js` |
| Git: Both repos committed, 0 uncommitted | Sales Bot (16 files), API Server (7 files) |

### 📌 New Lessons (June 12)
- **Dashboard JS only supports 4 final_status values:** Available, Damaged, Lost, In Use
- **games_library vs console_games** are independent tables — titles must match exactly
- **Booking customers skip wallet check** — they pay at booking time, not session-end
- **disc_count values are intentional** — never modify without Boss confirmation
- **Staff group Forum mode:** messages without `message_thread_id` go to General topic
- **IP unreachable ≠ port blocked:** when ping fails, it's routing/ISP filtering
- **Web SSH works when direct SSH doesn't:** Cloudflare Tunnel + HTTPS bypasses ISP filters

### 🔴 Pending (Boss Action Needed)
1. **CMD SSH** — Cloudflare Zero Trust → Tunnels → Public Hostnames for `shell.ps-vibe.com`
2. **100+ games discrepancy** — 41 in DB vs claimed 100+. Clarify if GSheet had non-game rows
3. **God of War Ragnarök encoding** — "Ã¶" vs "ö", only LIKE-matched, needs clean fix
4. **n8n payment (€25.68)** — 2nd notice received

### 🩺 Services (June 12, 15:30 UTC)
| Service | Status |
|---------|--------|
| psvibe-api | ✅ |
| psvibe-sale-bot | ✅ |
| psvibe_customer_bot | ✅ |
| psvibe-dashboard | ✅ (:9090) |
| kora-dashboard | ✅ (:9091) |
| cloudflared-tunnel | ✅ |
| wssh (web SSH) | ✅ (:8888) |
| Caddy | ✅ |
| n8n | ✅ |
| MySQL | ✅ |
| Health Monitor | 93.3/100 ✅ |

### 🧠 Critical Lessons (Running Archive)
1. FastAPI response_model silently strips undeclared fields
2. `bool(0) == False` → use `x if x is not None else default`
3. `async def` + missing `await` → coroutine passes type checks silently
4. Double fail masking: both API + GSheet broken simultaneously
5. Date format: always normalize to YYYY-MM-DD at API boundary
6. Slot conflict: API-level booking check prevents double-booking
7. Dashboard only supports 4 statuses: Available/Damaged/Lost/In Use
8. ISP can block entire IP routing; Cloudflare Tunnel + HTTPS bypasses it
9. Staff group Forum mode: always include message_thread_id

## 📌 June 13 — New Critical Lessons

10. **JS `<script>` block fragility** — A single syntax error (e.g., broken quoting in onclick) anywhere in a `<script>` block kills ALL JavaScript in that block, including unrelated functions like `doLogin()`. Always validate inline scripts carefully.
11. **PNL Food Revenue ≠ Console Multiplier** — Food revenue must come from `stock_out` table (items sold × unit_price), NOT from `gross-amount` (console multiplier). These are fundamentally different data sources. Mixing them corrupts both food and game margins.
12. **fail2ban is baseline security** — Was completely missing from VPS until audit discovered it. Every production server should have fail2ban running from day one.
13. **Cloudflare Tunnel path routing limitation** — `/kora/` path routes to localhost:8000 (API server) cannot also route to :9091 (Kora Dashboard). Solution: DNS CNAME record (`kora.ps-vibe.com`) for separate services behind same tunnel.

## 📌 Pending Issues (June 13, 15:30 UTC)
3. **Kora Dashboard URL**: `kora.ps-vibe.com` needs DNS CNAME record at Cloudflare
4. **Wallet rate**: `effective_rate` = 1.00 for all members (might need Boss to confirm intended pricing)

## 🩺 Services (June 13, 15:30 UTC)
| Service | Status |
|---------|--------|
| psvibe-api | ✅ |
| psvibe-sale-bot | ✅ |
| psvibe_customer_bot | ✅ |
| psvibe-dashboard (:9090) | ✅ |
| kora-dashboard (:9091) | ✅ |
| cloudflared-tunnel | ✅ |
| wssh (web SSH :8888) | ✅ |
| Caddy | ✅ |
| n8n | ✅ |
| MySQL | ✅ |
| fail2ban | ✅ (NEW) |
| Daily Auto-Backup | ✅ (NEW: cron 0 2 * * *) |
| Health Monitor | ~93/100 ✅ |

---

## 📋 June 14 — Summary

### Fixes Deployed (6 total)
| # | Fix | File(s) | Root Cause |
|---|-----|---------|------------|
| 1 | Booking Flow — Member Keyboard Hang | `sales.py` line 1491, 2541 | `fetch_members_async` wrapper overridden by alias; needed `[m["id"] for m in result]` mapping |
| 2 | "No telegram_chat_id, skip notification" | `app.py` line 1517→1601 | Orphaned `@app.post` decorator on wrong function |
| 3 | Food Sale — Stock Map Rebuild Failed | `api_client.py` | `_psvibe_get_async` imported in 3 places but never defined |
| 4 | Booking Extend — `message_thread_id` undefined | `booking_flow.py` | Missing parameter in `_do_extend()` + `persist_reminder()` |
| 5 | `name 'os' is not defined` | `notify.py` | `_check_low_balance_alert` used `os` module without import |
| 6 | Ovaltine Cookies — Case-Sensitive Match | `sales.py` | `step_food_menu` used exact dict key lookup; "Ovaltine cookies" ≠ "Ovaltine Cookies" |

### 🔍 Investigation: `_remind_loop` Never Fires (Known Bug — Not Fixed)
- Logs confirm task is created via `load_and_restore()` but **never executes**
- Zero `_extend_timer_kb` calls logged all day for any console
- Hypotheses: `asyncio.sleep(initial_delay)` never completes / task cancelled / negative delay
- **Mitigation:** Staff using "No Timer" (`mins=0`) for recent sessions
- **Deferred:** Needs debug logging inside `_remind_loop`

### 📌 New Lessons (June 14)
14. **Case-insensitive matching for user input** — Dictionary key lookups on user-typed text must be case-insensitive. Normalize to consistent case at system boundary or use case-insensitive matching.
15. **Decorator placement is critical** — `@app.post("/path")` on the wrong function silently routes requests to the wrong handler. Always verify decorator → function mapping after edits.
16. **Async imports must be defined, not just imported** — Importing a function name doesn't create it. Always verify the source file actually defines what downstream files import.

### Pre-existing Warnings (Non-Blocking)
- `inv_sh = None` — K1 inventory Google Sheets update always fails silently
- `fetch_balance_mins/-` 404 — Empty member_id when checking Guest wallet

### 🩺 Services (June 14, 15:30 UTC)
| Service | Status |
|---------|--------|
| psvibe-api | ✅ |
| psvibe-sale-bot | ✅ |
| psvibe_customer_bot | ✅ |
| cloudflared-tunnel | ✅ |
| Caddy | ✅ |
| n8n | ✅ |
| MySQL | ✅ |
| fail2ban | ✅ |
| Health Monitor | ~91.6/100 ✅ |

---

## 📋 June 15 — Summary

### 🔧 Fixes Deployed (8 total)
| # | Fix | File(s) | Root Cause |
|---|-----|---------|------------|
| 1 | Morning Health Summary showing 0s | `lib/ssh_vps.js` | MySQL password warning merged into stdout via `2>&1` → parsed as column headers |
| 2 | Food Cart POST — `int.strip()` crash | `patch_routes.py` L1328 | `booking_id` from MySQL is int; `.strip()` only works on strings |
| 3 | Coupon gen blocking voucher (v2) | `sales.py` L1310, 1792 | `await asyncio.to_thread()` still blocking; wrapped in `create_task()` |
| 4 | Stale API on port 5001 | n/a | Old process from before patch_routes changes still running |
| 5 | Indentation error in coupon fix | `sales.py` | Fix script used 8-space indent; original is 4-space |
| 6 | Food Note / End Session booking_id not found | `console.py` L225, 355 | `_map_booking_row` maps `console_id` → `consoleType`; code looked for `consoleId` |
| 7 | **PNL API — Broken Stub** | `patch_routes.py` L665-720 | Stub returned +1.5M fake profit; replaced with real dashboard logic → -15.2M LOSS ✅ |
| 8 | **Balance Sheet API — Broken Stub** | `patch_routes.py` L724-755 | Stub showed 427K assets (real: 279M); replaced with full dashboard BS logic ✅ |

### 🏗️ Finance Infrastructure
- **Auto-Depreciation:** Created `/root/scripts/auto_depreciate.py` — monthly cron (1st, 2:30 UTC)
- **Catch-up:** 12 of 39 assets had `acc_depreciation=0` → fixed; total now 10,257,830 Ks ✅
- **Balance Sheet verified:** A = L + E @ 279,445,881 Ks ✅
- **PNL verified:** June YTD = -15,163,987 Ks LOSS ✅

### 🧠 5 New Lessons (June 15)
- **17.** `%%Y-%%m` doesn't work with `mysql.connector` — uses `%s` params, not printf-style `%%`
- **18.** Depreciation convention: from purchase month (inclusive), first month gets full depreciation
- **19.** Dashboard code is source of truth — `patch_routes.py` stubs were outdated prototypes
- **20.** `sales_daily.net = amount + food` — food IS baked into net; subtract food_rev for pure game revenue
- **21.** Auto-depreciation cron must NOT use LockMonitor — simple 1-minute operation, non-peak hours

### 📌 Pending (Boss Action Needed)
1. **n8n payment (€25.68)** — 2nd notice, subscription may expire
2. **GitHub Deploy failing** — psvibe-api-server master branch
3. **100+ games discrepancy** — 41 in DB vs claimed 100+
4. **Food Note issue** — Boss said "ဆက်လုပ်ပါ", awaiting further instruction

### 🩺 Services (June 15, 15:30 UTC)
| Service | Status |
|---------|--------|
| psvibe-api | ✅ |
| psvibe-sale-bot | ✅ |
| psvibe_customer_bot | ✅ |
| psvibe-dashboard | ✅ |
| kora-dashboard | ✅ |
| cloudflared-tunnel | ✅ |
| Caddy | ✅ |
| n8n | ✅ |
| MySQL | ✅ |
| fail2ban | ✅ |
| Health Monitor | ~91/100 ✅ |

### 🧠 Critical Lessons Archive (continued)
- 17. **`%%Y-%%m` ≠ `mysql.connector` params** — `mysql.connector.execute()` uses `%s` style, not printf `%%`
- 18. **Depreciation from purchase month (inclusive)** — first month = full month depreciation
- 19. **Dashboard code is source of truth** — always check `dashboard_routes.py` before other endpoints
- 20. **`sales_daily.net` includes food** — food revenue baked into `net`; subtract for pure game revenue
- 21. **Auto-depreciation cron = no LockMonitor** — simple 1-min op, non-peak hours only
