# 🧠 Kora's Long-Term Memory
## 🚨 RULE #0 — MONGO DB FIRST (2026-07-05 Reinforced)

> **Boss's direct order — NEVER skip this again.**

```
╔══════════════════════════════════════════════════════════╗
║  Bug ရှာရင်/Code trace လုပ်ရင်/Endpoint စစ်ရင်:        ║
║  STEP 1: kora_memory.py trace "<name>"  ← MANDATORY   ║
║  STEP 2: kora_memory.py search "<query>"               ║
║  STEP 3: THEN grep/read/journalctl                      ║
╚══════════════════════════════════════════════════════════╝
```

**Violation = Boss's trust broken. 850K relations wasted. No excuses.**

## 🤖 Model Configuration (2026-07-05)

| Role | Model | Cost (Input/Output) |
|------|-------|:---:|
| **Default (Kora)** | `deepseek/v4-flash` | $0.28/$1.10 |
| **Coding/Complex** | `deepseek/v4-pro` | $0.55/$2.19 |
| **Fallback #1** | `google/gemini-2.5-flash` | $0.15/$0.60 |
| **Fallback #2** | `google/gemini-3.5-flash` | free |

**Rule:** Normal work → Flash (cheap, stable). Coding/analysis → Boss says "use pro" or sub-agents auto-use pro.

## 🏗️ Multi-Project Architecture (Phase 1-5 Complete — 2026-06-25)

Kora now manages **9 projects** with full coordination tool support.

### Project Registry: `/root/coordination/project_registry.json`
| Slug | Project | Services |
|------|---------|----------|
| psvibe | PS VIBE Gaming Lounge | 9 (8 systemd + 1 docker) |
| construction | Three Brothers Construction | 1 (docker) |
| yyo_wallet | YYO Personal Wallet | 1 (systemd) |
| acm_wallet | ACM Personal Wallet | 1 (systemd) |
| kora_voice | Kora Voice Assistant | 1 (systemd) |
| social_autoreply | Social Auto-Reply | 1 (systemd) |
| inventory_alerts | Inventory Alerts | 0 |
| sel_exchange | SEL Currency Exchange | 2 |
| kora_host_api | Kora Host API Bridge | 4 |

### Key Commands:
- `kora_status.py` — All projects health dashboard
- `onboard_project.py` — One-command new project setup
- `backup_manager.py` — Per-project backups
- `auto_healer.py --all` — Cross-project monitoring
- `project_utils.py detect "<message>"` — Auto-detect project from message

### Context Detection:
- Boss mentions project name/alias → Kora auto-detects
- Default: psvibe (backward compatible)
- All coordination tools support `--project <slug>`

---

## People

- **Boss:** Ko Aung Chan Myint (ကိုအောင်ချမ်းမြင့်) — Founder of PS VIBE - PS5 Gaming Lounge. Call him "Boss" or "အစ်ကို" internally.
- **Osmo:** Discord username `@kingkong00787` — helped set up PS VIBE Discord server.

## Business: PS VIBE - PS5 Gaming Lounge

### Info
- **Tagline:** "Play The Game. Share The VIBE!"
- **Hours:** 9:00 AM - 9:00 PM daily
- **Address:** Yangon, Myanmar
- **Opened:** June 6, 2026 (Saturday) 🎮
- **Socials:** [Facebook](https://www.facebook.com/ps5gamecenter) | [TikTok](https://www.tiktok.com/@ps.vibe.game.cent)
- **Discord:** Guild ID 1516119712411422942 | [Invite](https://discord.gg/EXEF7phbZF)

### Infrastructure (bot-server-01: 5.223.81.16)
| Service | Purpose |
|---------|---------|
| psvibe-api | Main API server (port 8000) |
| psvibe-sale-bot | Staff sale/booking bot |
| psvibe_customer_bot | Customer-facing bot |
| psvibe-dashboard | Vue web dashboard (:9090) |
| kora-dashboard | Kora admin dashboard (:9091) |
| psvibe-discord-bot | Discord bot (35 commands) |
| MySQL | Primary database |
| cloudflared-tunnel | Cloudflare Tunnel |
| Caddy | Reverse proxy |
| n8n | Workflow automation |

### Key Operations
- **Staff Salary System (June 27)**: Full payroll auto-generation with leave tracking, shop-wide food commission (PNL formula), game bonus tiers (1500/1800/2000hr), attendance rules. See `memory/2026-06-27.md` for full details.
- **Staff Salary**: Auto-generate via `POST /salary/generate` — formula: base + transport + food_allowance + att_bonus + food_com + game_bonus − advances − leave_penalty
- **Member balance:** Column H of Card_wallet Google Sheet (legacy) → MySQL `member_wallets` (primary)
- **Receipts:** Burmese footer text must be removed
- **Coupon codes:** Valid samples: CBQVUHYG, CBANN6LD, CBZVNW7O, CBB292MP, CB7U617B

## 🧠 Critical Lessons Learned (Cumulative)

96. **SESSION_TOKEN must be static** — Random session token names per restart break all existing cookies. Use a fixed name and persistent file storage. (#96)
97. **Sessions must persist to disk** — In-memory SESSION_STORE is lost on every server restart. JSON file preserves sessions across restarts. (#97)
98. **Auth check must come after public path handlers** — Login page, static files, and QR codes must be served BEFORE auth check, otherwise infinite redirect loops occur. (#98)
99. **Cloudflare caches even dynamic pages** — Without explicit `no-store` headers, Cloudflare caches error pages. Always set `Cache-Control: no-store, no-cache` on auth-required pages. (#99)
100. **Double-click protection on form buttons** — Laggy connections cause duplicate form submissions. Use `onclick="this.disabled=true"` on Create/Submit buttons. (#100)

*(Trimmed: keeping only 3 most recent lessons)*

## Major Projects & Milestones

### Console Timer & Booking System Overhaul (June 22)
- Console Timers page: live elapsed/remaining with 30s refresh, timer adjust dropdown
- Timeline AM/PM format + frozen console column
- No Timer support: "∞ Open End" display, 8hr conflict window
- Booking soft-delete, auto-cancel disabled; manual-only end policy

### Dashboard UX & Timeline Overhaul (June 26)
- Food Orders: timezone fix (UTC→MMT), sorting by Active-first + recency
- Timeline: lane-based stacking rejected → tap-to-select popup approach (final)
- See `memory/2026-06-26.md` for full details

### Staff Salary System & Customer Notifications (June 27)
- Salary: full payroll auto-generation with leave tracking, PNL FIFO COGS, game bonus tiers
- Customer Noti: fixed staff Check-In & Staff Booking flows

### Financial Statement July Fixes — 8 Bugs Fixed ✅
- PNL `m` param + Finance Balances + Balance Sheet date filters + Cashflow cumulative fixes
- BS Member Liability undefined `ym` variable + transfer_out sign fix
- **Verification:** June 2026 PNL 11.7M, Topup 450K; CF opening 300M → closing 11.32M
- **Files:** `dashboard_routes.py`, `patch_routes.py`

## ⚠️ Known Issues (Persistent)

| Issue | Severity | Status |
|-------|----------|--------|
| VPS health monitor unreachable (Jun 28) | Low | 🟡 Investigating |

## Working Preferences

- **Language:** Burmese primary, English for tech terms
- **Timezone:** Asia/Yangon (UTC+6:30) — always convert for Boss
- **Delegation:** Always delegate complex tasks to sub-agents. Never do manually what a helper can do.
- **Fix protocol:** `python3 /root/coordination/fix_protocol.py --start <file>` before any code fix
- **Post-fix documentation:** Run `auto_doc_updater.py` + update daily memory + MEMORY.md
- **📁 New project onboarding:** Every new project MUST include: (1) `README.md`, (2) `memory/projects/<slug>/state.md`, (3) Daily memory, (4) MEMORY.md entry, (5) `auto_doc_updater.py` commit
- **Sub-agent timeout:** 300s default

66. **MySQL queries: ALWAYS Python pymysql, NEVER shell quoting** — docker exec + bash heredocs with nested quotes fails silently. Python pymysql handles all quoting automatically and is 3x faster. Pattern: `python3 -c 'import pymysql; ...'` for ALL MySQL queries. (#66)

## Memory (2026-07-03)

### Critical Fixes — 4 Race Condition & Error Handling Bugs Fixed ✅
- **C2: Checkin Race Condition** — Added `SELECT ... FOR UPDATE` lock on `console_status` inside booking transaction
- **L1: Dead GSheet Code** — Created `_GsheetRemoved` singleton; GSheet stubs now raise `RuntimeError` instead of `None`
- **H8: Empty member_id** — 4-level fallback: payload memberId → phone → telegram_chat_id → customer_bot_users → auto-create
- **M5: ConsoleStatusError** — `fetch_console_status()` now raises `ConsoleStatusError` instead of returning `[]` on API failure
- Key lessons: #67-70 (sub-agent verification, MongoDB debugging, pymysql over shell, Telegram markdown escape)
- Files: booking_routes.py, gsheet_stubs.py, console.py

## Memory (2026-07-04)

### New Project: AKT Clothing Shop ERP (BKK Fashion Shop) 👕
- **Path:** `/opt/kora-projects/akt_clothing/code/`
- **Stack:** FastAPI + Vue 3 + SQLite | **Links:** `/akt-clothing-shop/`

### Critical Fixes Delivered
1. **Account Balance — payment_transactions Not Recorded 🐛→✅:** `record_payment_transaction()` name lookup mismatch ("Cash"→"Cash Register", "Bank Transfer"→"Bank Account"). Added mapping + type fallback. Backfilled historical.
2. **Add Product — Empty String Crash 🐛→✅:** Pydantic `Optional[int]` rejected `""`. Added `@field_validator` converting `""` → `None`.
3. **Logout Glitch 🐛→✅:** `router.push("/login")` + mounted-page API calls → 401 interceptor race. Fixed: skip 401 on /login; logout uses `window.location.href`.
4. **SSD Return — Game Auto Re-add 🐛→✅:** PS VIBE `step_ssd_ret_game` now re-adds game to source SSD after removing from console.

*(Trimmed: keeping only 5 most recent fixes)*

### Features Added
- Logo + Favicon (BKK), product image upload, UX improvements (optional labels, red *, larger buttons)

### New Lessons
71. **Payment method labels ≠ account names** — Always add name mapping layer or account_type fallback for payment_transactions. (#71)
72. **Pydantic Optional[int] rejects empty string ""** — Must use `@field_validator(mode="before")` to convert `""` → `None`. (#72)
73. **Logout: router.push + 401 interceptor = race condition** — Skip 401 on /login; use `window.location.href` for clean logout. (#73)
74. **Old transactions need manual backfill after fix deployment** — Always check and backfill historical records after fixing payment/balance logic. (#74)

### Code Graph Maintenance
- MongoDB code graph full rebuild: 7,858 entities, 103K relations (weekly maintenance)

## Memory (2026-07-05)

### Critical Fixes
1. **Caddy 502 Bad Gateway 🐛→✅:** UFW DENY rule on port 8000 blocked Docker bridge traffic (172.17.0.0/16). DROP rule was inserted before ACCEPT rule causing order mismatch with Docker iptables. Fix: removed UFW DENY for internal service ports (8000/9090/9091). Cloudflare Tunnel restored to direct API routing afterward.

### Infrastructure Hardening
2. **VPS Security Hardening 🛡️:** SSH port reverted from 80/443 back to 22 (ports 80/443 needed by Caddy). UFW configured with 12 common attack ports blocked. fail2ban expanded to 4 jails (sshd, caddy, nginx, custom). HSTS + security headers active via Caddy. All services validated healthy post-hardening.

### New Lessons
76. **Gateway kill loop = model timeout trigger** — When primary model API hangs (DeepSeek V4 Pro 180s timeout), OpenClaw health monitor sends SIGTERM → restart → next cron job hits same timeout → another SIGTERM. Fix: switch default model to stable alternative (V4 Flash). Always check provider stability before blaming infrastructure. (#76)

77. **MongoDB Rule #0 reinforced by Boss** — Bug hunting / code tracing / endpoint debugging → `kora_memory.py trace` BEFORE any grep or file read. No exceptions. Violation count will be tracked. (#77)

## Memory (2026-07-06)

### Critical Fixes — System Stability Overhaul ✅

1. **Subagent V4 Pro Timeout Cascade 🐛→✅:** Subagent model was deepseek/deepseek-v4-pro (180s+ timeout). Changed to V4 Flash as primary, V4 Pro as fallback. (#80)
2. **Session DB 450MB/500MB (89%) 🐛→✅:** 7,337 session files filling up. Cleaned 2,424 files → 282MB. pruneAfter 7d→3d, archive 2d→1d. (#79)

### Preventive Safeguards Installed 🛡️
- **session-usage-monitor** (every 1h): Alerts if sessions DB >80%
- **cron-health-checker** (every 6h): Detects stuck/error cron jobs
- **session pruning**: 3d retention, 1d archive (auto-maintain)
- **subagent model lock**: V4 Flash primary enforced

### New Lessons
80. **V4 Pro subagent timeout blocks main session** — Subagent model MUST be V4 Flash (stable 500-700ms) with V4 Pro as fallback only. (#80)
81. **Gateway restart cuts conversation thread** — Always warn Boss before applying changes that need restart. (#81)

## Memory (2026-07-06)

### Critical Fix — Balance Sheet 102.5M Gap ✅
- **Problem:** KBZ Bank cash balance excluded all "Advance settled" injects (102.5M) from calculation, while the same amount wasn't in retained earnings either. Auto-balancer was silently inflating retained earnings to compensate.
- **Fix:** Removed `AND note NOT LIKE '%Advance settled%'` from inject query; added `advance_recovery_reserve` (102.5M) as separate equity line in `finance_routes.py`. Auto-balancer threshold: only adjusts gaps < 50K; gaps ≥ 50K log warning and skip.
- **Patch fix:** Fixed duplicate `api_finance_balance_sheet` function in `patch_routes.py` (route pointed to empty one, returning null).
- **Files:** finance_routes.py, patch_routes.py
- **Verified:** KBZ Bank: 104,293,306 Ks (advance settled 102.5M included ✅) | Retained Earnings: -13,597,554 Ks (not inflated ✅) | Advance Recovery Reserve: 102,500,000 Ks (separate equity ✅) | Residual gap: 152,313 Ks (0.04%) — transparent, left visible.

### New Lessons
78. **Advance settled injects must be accounted as equity, not cash exclusion** — Removing advance settled records from cash queries hides 102.5M from both cash balance AND retained earnings simultaneously. Create a separate equity line (`advance_recovery_reserve`) and let cash queries include all records. Auto-balancer should warn, not silently fix large gaps. (#78)

---

## Memory (2026-07-07) — Major VPN System Build Day 🔥

### AKT Clothing Shop — SPA Route & Cloudflare Fixes 🔧
- **SPA Route Order Bug 🐛→✅:** Generic catch-all `@app.get('/{full_path:path}')` registered BEFORE AKT-specific route. Fixed: moved AKT catch-all first. FastAPI matches first-registered route. (#85)
- **Product Image URL Cloudflare Fix 🐛→✅:** Upload endpoint returned `/uploads/products/{filename}` but Cloudflare path prefix required `/akt-clothing-shop/uploads/products/{filename}`. (#86)
- **Cloudflare DNS Records Issue (⚠️ Ongoing):** `ps-vibe.com` stopped resolving — Cloudflare tunnel remote config version 10 lost route.

### Outline VPN → Xray REALITY Migration (Sessions 2-7)
- **Port 443 redirect (Outline):** iptables DNAT to Shadowsocks port 995 as initial DPI bypass.
- **Xray REALITY installed (v26.3.27):** VLESS+REALITY protocol, port 443, target `8.8.8.8:443`/`dns.google`. Replaced Outline as primary VPN. (#90)
- **Xray Web UI built:** Integrated into `outline-web` Python server (port 9356) — Xray key CRUD + QR code generation + expiry management.
- **7 fix sessions:** Fixed mobile session loss (persistent file-based sessions), Cloudflare cache poisoning, white-on-white light theme CSS bug, mobile button double-submit, backslash escape breakage from binary replacement.
- **Final state:** 12 active VPN keys (11 Xray + 1 Outline), 4-tab web UI (Dashboard/Xray/Outline/Analytics), persistent sessions across restarts.

### New Lessons (#85-#108)
85. FastAPI route ORDER matters — generic catch-alls after specific path handlers
86. Cloudflare Tunnel proxies HTTP/HTTPS only — VPN IP never hidden
87. iptables DNAT works when Docker owns a port with no service listening
88. Ubuntu 24.04+: `netfilter-persistent`, not `iptables-persistent`
89. iptables comment syntax: `-m comment --comment "label"` BEFORE jump target
90. REALITY target must be simple TLS endpoint (e.g., `8.8.8.8`)
91. Xray, Outline DNAT, Docker Caddy cannot share port 443
92. QR codes in HTML: `data:image/png;base64` + `|safe` filter
93. Xray SIGHUP reload for config changes
94. QR image endpoint must be auth-free for mobile cookie consistency
95. Mobile POST→redirect fragility — use GET links instead
96. SESSION_TOKEN must be static, not random per restart
97. Sessions must persist to disk (JSON file)
98. Auth check must come after public path handlers
99. Cloudflare caches even dynamic pages — set `no-store` headers
100. Double-click protection on form buttons
101. Single invalid CSS property kills entire rule block (silent)
102. Cache-busting timestamp must be request-time, not boot-time
103. Light theme needs solid hardcoded colors, not variable stacks
104. `this.disabled=true` on submit buttons blocks mobile form submission
105. Binary replacement of Python source can break backslash escapes
106. `confirm()` inside f-string onclick: use HTML entities or different quotes
107. `this.form.submit()` in onclick on `type="submit"` causes double-submission
108. CSS light theme: solid hardcoded colors, no backdrop-filter/glassmorphism

### Infrastructure State (End of Day)
| Port | Service |
|:----:|---------|
| 443 | Xray REALITY (primary VPN) |
| 80 | Caddy (Docker) |
| 995 | Outline Shadowsocks (fallback) |
| 8000 | PS VIBE API |
| 8010 | AKT Clothing Shop API |
| 9356 | VPN Web UI (Xray + Outline mgmt) |

### Known Issues
| Issue | Severity | Status |
|-------|----------|--------|
| Cloudflare DNS records for ps-vibe.com | 🔴 | User needs to check dashboard |
| AKT product image not displaying in edit form | 🟡 | Bug logged |

---

## Memory (2026-07-08) — VPN Agent System Phase 1 🔥

### VPN Agent System — Phase 1 Complete
- **Agent Portal (Port 9357):** Agent-only server with full isolation from admin routes. Caddy subdomain `agent.outline.ps-vibe.com` → port 9357 (DNS pending). Fallback `/agent/*` path working.
- **Agent Features:** Login/Logout (hashed password, JSON sessions), Dashboard (stats, pricing, key creation), Key Creation (Xray only, per-rank limits, trial caps, duration pricing), Commission Auto-Record (20% flat, pending on creation), Sing-box Config Generator, QR Code Generator.
- **Admin UI (Port 9356):** New Agents tab with inline pricing editor and commissions table.
- **Database:** New tables `agents`, `pricing`, `commissions`, `agent_logs`. VPN keys migrated with `agent_id`, `auto_rotate` columns.

### Agent Ranks & Pricing
- **Ranks:** Basic (50 keys/3 trial), Silver (100/10), Gold (200/25), Diamond (unlimited)
- **Pricing:** 3d (free trial), 30d (5,000 Ks), 90d (15,000 Ks), 180d (30,000 Ks), 1yr (50,000 Ks)
- **Test Agent:** `demo_agent` / `testagent123` (Gold rank)

### Mobile Crash Debugging — Critical Lessons
| # | Lesson |
|:-:|--------|
| 109 | **Xray restart blocks HTTP response** — `os.system()` with `&` still blocks. Fix: `subprocess.Popen()`. |
| 110 | **Xray config save must be background thread** — `threading.Thread(daemon=True)` for non-blocking HTTP response. |
| 111 | **`btn.disabled=true` on onsubmit blocks mobile browsers** — Use `data-submitted` flag + CSS only. |
| 112 | **Cloudflare + mobile + POST = fragile** — Content-Length + flush + fast response (<200ms) essential. |

### Open Issues
- Mobile "this site can't be reached" — user not yet confirmed fix (6 fixes applied)
- Cloudflare DNS for `agent.outline.ps-vibe.com` — user deferred

### Infrastructure State
| Port | Service |
|:----:|---------|
| 9356 | Admin server (full) |
| 9357 | Agent-only server |
| 443 | Xray REALITY |
| 995 | Outline Shadowsocks (fallback) |
- **Backup:** `/opt/outline-web/backups/pre-agent-system-20260708_060348/`

---

## Memory (2026-07-09) — VPN UI Fixes + Advance System Audit 🔧

### Advance Payment System — Root Cause Fix ✅
- **Problem:** 7 advance payments (104.8M) were recorded in `finance_advances` but NEVER recorded as `cash_movements` eject. Only the settlement injects (102.5M) were recorded → KBZ Bank overstated by 102.5M.
- **Fix 1:** Backfilled 7 missing eject entries in `cash_movements` for KBZ Bank (104.8M total)
- **Fix 2:** Removed advance settled filter from `get_finance_balances()` (was excluding 102.5M inject as a workaround)
- **Fix 3:** Removed `ded_advances` from KBZ capital deduction in both `get_finance_balances()` and `get_balance_sheet()` — pending advances (2.3M) were being double-deducted after backfill
- **Files:** `finance_routes.py` — lines ~406-412 (filter removed), ~428-429 (ded_adv disabled), ~694-696 (BS ded_adv disabled)
- **DB:** 7 INSERTs into `cash_movements` (KBZ Bank, eject, 104.8M)
- **Verified:** KBZ balance 1,793,306 (correct) — advance net -2.3M (all settled advances cancel with eject, only pending remains)

### New Lessons
| # | Lesson |
|:-:|--------|
| 137 | **Advance eject must be recorded** — finance_advances + inject entries without eject entries overstate bank balance.
| 138 | **ded_adv = double-count after backfill** — Once eject entries exist for all advances, pending advance deduction causes double-counting.
| 139 | **Filter as workaround ≠ fix** — The advance settled filter was a workaround for missing eject data. Always fix the data, not the filter.

## Memory (2026-07-09) — VPN UI Fixes (Osmo Feedback) 🔧

### 3 Bugs Fixed ✅
1. **Recent Keys မပေါ်တာ 🐛→✅:** `{key_rows}` placeholder `.replace()` မေ့နေ။ Agent keys page empty. Fix: added `.replace("{key_rows}", key_rows)`.
2. **Outline Keys Data Usage Added ✅:** Agent + Admin keys listing တွင် **Usage** column အသစ်။ Outline → progress bar (green/yellow/red), Xray → "—".
3. **Sub-tab Layout ပြင်ဆင် ✅:** Osmo request — Xray/Outline sub-tab nav ကို Payment Summary အောက်ကို ရွှေ့။

### New Layout Order
`Header Card → Stat Grid → 💳 Payment Summary → [☪ Xray] [👻 Outline] → Create Form → Recent Keys`

### New Lessons (#134-#136)
| # | Lesson |
|:-:|--------|
| 134 | **Payment Summary > Sub-tab Nav** — Users expect financial summary above protocol tabs.
| 135 | **`{placeholder}` replace must be verified** — new template pages need .replace() check.
| 136 | **Data usage display differs by protocol** — Outline = progress bar, Xray = "—" (no tracking).

### MongoDB Updated ✅
- Fix entry: VPN UI Fixes — Recent Keys, Data Usage, Sub-tab Layout
- Lesson entry: Osmo VPN UI Feedback — Layout Order & Data Display Standards
- Daily memory auto-exported
- auto_doc_updater.py committed
