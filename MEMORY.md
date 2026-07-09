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

*(Trimmed: oldest fix history removed — keeping only 5 most recent fixes)*


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
*(Trimmed: lessons 85-108 removed — kept in Critical Lessons cumulative section)*

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

---

## Memory (2026-07-09) — 8 Bugs Fixed, 6 Lessons Learned 🔥

### Critical Fixes — Advance Payment System + Cash Flow Overhaul 🐛→✅

1. **Advance Payment System — Backfilled Eject + Removed Double-Count (3 bugs):** Backfilled 7 advance eject entries (104.8M) into cash_movements. Removed `advance settled` filter from get_finance_balances(). Expanded `_start` from June 1 → April 1. Added cash opening balance inject (42,100 Ks). Balance Sheet KBZ = 1,793,306 ✅. (#137-139)

2. **Cashflow Opening Formula — finance_advances Double-Count 🐛→✅:** Cashflow opening/closing SQL was subtracting finance_advances (104.8M) AND cash_movements eject (104.8M). Removed finance_advances from both SQL queries. Opening: -93.4M → 11.4M ✅.

3. **Cash OPEX Not Tracked in Till System 🐛→✅:** 935,400 Ks of OPEX paid with Cash was not in cash_movements. Added opex query to till endpoints. 7 daily_till records backfilled.

### VPN System Fixes 🐛→✅
4. **VPN UI Fixes — Recent Keys, Data Usage, Sub-tab Layout (3 bugs):** `{key_rows}` placeholder `.replace()` missing; Data Usage values shown for expired keys; sub-tab nav moved below Payment Summary per Osmo feedback.

5. **Outline VPN Expiry Checker — Data Limit Auto-Expiry 🐛→✅:** Previously only checked `expires_at < NOW()`. Added Phase 2: Prometheus data usage vs `data_limit_bytes`. Test_Trial_0001 (12.9GB/10GB = 129%) auto-expired ✅. (#141-142)

### Feature Deployed
- **Till OPEX Breakdown:** Added `cash_opex_total` + `cash_opex_items` to till API; TillManager.vue shows OPEX breakdown with red negative amounts.

### Key Files Modified
- `finance_routes.py` (lines 297, 406-412, 428-429, 692-694, 756, 819, 946, 1407-1408, 1579-1580)
- `TillManager.vue`, `server.py` (VPN), `expiry_checker.py` (VPN)

### New Lessons (#137-#142)
137. Advance eject must be recorded in cash_movements for ALL advances
138. Filter as workaround ≠ real fix — always fix data, not the filter
139. finance_advances + cash_movements eject = double-count once backfilled
140. Cash OPEX must be tracked as physical till outflow separately
141. Outline expiry checker must check data limit, not just time
142. SG Prometheus may not track all keys — manual verification may be needed

### Backup
- `/opt/outline-web/backups/pre-agent-system-20260708_060348/`

### VPN Admin Speed Optimization — Metrics Cache + Pre-fetch 🐛→✅
- **Problem:** Admin page load 20-40s (4 Prometheus API calls per key, TH server SSH 15s timeout). Cloudflare 100s timeout crashes the page.
- **Fix (3-layer):** Layer 1: Timeout reduction 10-15s → 3s; Layer 2: Global `_metrics_cache` 30s TTL; Layer 3: Background `_prefetch_loop()` every 25s keeps cache fresh. First load now ≤0.5s.
- **File:** `/opt/outline-web/server.py`

### Test Agent Cleanup 🐛→✅
- Deleted `demo_agent` + `test007` + 10 keys (3 Outline + 7 Xray). DB backed up.

### Google Gemini API Key Leaked — 3 Updates 🐛→✅
- **Problem:** Google flagged `AIzaSyC8ute_...` / `AIzaSyDOh_u9...` as leaked → 403 errors. Affected memory_search (Gemini embeddings), image analysis, oc-coco container.
- **Fix:** Replaced in 4 files: `auth-profiles.json`, gateway `.env`, `gateway.systemd.env`, `coco/docker-compose.yml`. Restarted coco container.
- **Files:** `/root/.openclaw/workspace/configs/coco/auth-profiles.json`, `/root/openclaw-gateway/.env`, `/etc/systemd/system/openclaw-gateway.service.d/gateway.systemd.env`, `/opt/coco/docker-compose.yml`

### Outline Web Crash on Expire/Delete 🐛→✅
- **Problem:** Expire/delete/revoke handlers called Outline API synchronously → Cloudflare 504 timeout → "this site can't be reached".
- **Fix:** Moved all Outline API DELETE calls to `threading.Thread(daemon=True)` in 4 handlers.
- **File:** `/opt/outline-web/server.py`

### New Lessons (#143-#148)
| # | Lesson |
|:-:|--------|
| 143 | **Prometheus metrics must be cached** — Per-key Prometheus on every page load is too slow. 30s TTL cache safe for gradually-changing metrics. |
| 144 | **Background pre-fetch > lazy fetch** — Pre-warm cache at 25s intervals (TTL=30s) ensures instant page loads. |
| 145 | **Cloudflare 100s timeout + sync API call = crash** — Always move Outline API calls to background threads in HTTPServer architecture. |
| 146 | **Google revokes leaked API keys** — Once flagged, key returns 403. Keep backup keys. |
| 147 | **GEMINI_API_KEY vs GOOGLE_API_KEY may differ** — Always test both with `curl` against Google API. |
| 148 | **Coco docker-compose uses same API keys** — Must update both gateway `.env` AND coco `docker-compose.yml` + restart container. |

### 🐛 Bugs Fixed Today (12 total)
| # | Bug | Severity |
|:-:|-----|:--------:|
| 1 | VPN UI — Recent Keys not showing | Medium |
| 2 | VPN UI — Layout order wrong | Low |
| 3 | Advance eject missing (104.8M) | Critical |
| 4 | Cashflow negative (-93.4M) | Critical |
| 5 | Cash OPEX not tracked | High |
| 6 | Expiry Checker no data-limit check | High |
| 7 | VPN Admin page 20-40s load | Critical |
| 8 | VPN Admin page crash on expire/delete | Critical |
| 9 | Test agent cleanup | Low |
| 10 | Google API key leaked (gateway) | Critical |
| 11 | Google API key leaked (coco) | Critical |
| 12 | Google API key leaked (old auth-profiles) | Medium |

### 🆕 Features Deployed
- Till OPEX Breakdown (Vue frontend + API)
- Metrics cache + pre-fetch for VPN admin (3-layer optimization)

### 🔑 Key Files Modified Today
| File | Purpose |
|------|---------|
| `finance_routes.py` | Advance eject, cashflow, cash OPEX fixes |
| `TillManager.vue` | OPEX breakdown UI |
| `server.py` (VPN) | Metrics cache, pre-fetch thread, expire/delete background |
| `expiry_checker.py` (VPN) | Data-limit auto-expiry |
| `auth-profiles.json` | Leaked Google key replaced |
| `gateway .env / systemd.env` | Leaked Google key replaced |
| `coco/docker-compose.yml` | Leaked Google key replaced |

### 🏗️ Infrastructure State (End of Day)
| Port | Service | Status |
|:----:|---------|:------:|
| 443 | Xray REALITY VPN | ✅ |
| 80 | Caddy (Docker) | ✅ |
| 995 | Outline Shadowsocks | ✅ |
| 8000 | PS VIBE API | ✅ |
| 8010 | AKT Clothing Shop API | ✅ |
| 9356 | Outline Admin UI | ✅ (fast now) |
| 9357 | Agent Portal | ✅ |
| — | oc-coco | ✅ (restarted with new key) |
