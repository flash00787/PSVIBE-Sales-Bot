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
