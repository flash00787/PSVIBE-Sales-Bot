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

### Most Recent Lessons (2026-07-19)
| # | Lesson |
|:-:|--------|
| 194 | **Banning a customer bot user requires dual-layer blocking** — MUST update BOTH `BLOCKED_IDS` (handlers.py code-level check) AND `_blocked_user_filter` (main.py PTB framework-level filter at group=-1). The handlers.py check only catches code paths that explicitly call `_is_blocked()`, while main.py filter catches ALL messages at the framework level (runs before ConversationHandler). IMPORTANT: CallbackQuery flows (inline buttons) are NOT caught by MessageHandler filters — verify the bot uses ReplyKeyboardMarkup (text messages) instead, or add a separate CallbackQuery handler for blocked users. Handle inline button flows separately from message flows. |
| 170 | **`_remind_key` vs `remind_key` key mismatch** — `_remind_key()` (session_reminder.py) returned `f"{cid}|{chat_id}"` (no abs), while `remind_key()` (store) returned `f"{cid}|{abs(chat_id)}"`. This caused `sync_api_reminders_async()` dedup to fail for duplicate store entries with chat_id=0. Fix: add `abs()` to `_remind_key`. |
| 171 | **`extend-duration` API didn't sync bot's session_reminders.json** — Web dashboard duration change only updated MySQL, not the bot's persistent reminder store. Old `_remind_loop` kept running with stale end_t. Fix: API now updates session_reminders.json with new end_t when extend-duration is called. |

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

## Memory (2026-07-18) — COGS Audit + Deposit Restore Fix 🔧

### COGS & Food Profit Pipeline — Full Audit ✅
- **Food Revenue:** stock_out SUM(total) per month — correct ✅
- **COGS:** FIFO (stock_in cost matched to stock_out qty) — correct ✅
- **Food Profit:** 922,040 Ks (38.8% margin) for July 2026 ✅
- **Double-count check:** Release path vs Voucher path — zero dupes ✅
- **All sold items have stock_in matching** — zero "no_stock_in" items ✅
- **Inventory drift:** 1 unit only (MaMa, rounding artifact) ✅
- **Dashboard manual stock-out (9 entries):** all properly deduct from inventory ✅

### Deposit Restore on Reactivation — 4 Paths Fixed 🐛→✅
- **Problem:** Booking #1760 auto-cancelled at 12:15 MMT (5 min before 12:20 booking). deposit_status became 'forfeited'. Staff reactivated session but deposit stayed forfeited.
- **Fix 1:** `api_start_console_session()` — deposit restore after commit (console_routes.py:391)
- **Fix 2:** `api_sessions_start()` — deposit restore for linked bookings (console_routes.py:606)
- **Fix 3:** `api_booking_checkin()` — deposit restore on check-in (booking_routes.py:329)
- **Fix 4:** `api_update_booking_status()` — added cancelled→Active transition + deposit restore (booking_routes.py:832, 923)
- **Immediate:** Booking #1760 deposit restored from 'forfeited' → 'verified' manually
- **Lesson #192:** When adding forfeit/deposit logic to cancel flows, audit ALL reactivation paths to ensure deposit restoration.

## Memory (2026-07-17) — SEL Equity System + PS VIBE Return 🔄

### SEL Exchange - Equity/Shareholder System Built ✅
- **Shareholders (3):** Myat Ei, Shwe Eain Lin, Aung Chan Myint
- **Dynamic Share %** based on net capital (inject - eject) per shareholder
- **Inject THB** creates equity_tx + FIFO buy tx
- **Eject THB** creates equity_tx + FIFO sell tx (FIFO consumed)
- **Dividend MMK** auto-distributes by current share %
- **Dashboard:** New 📋 Equity tab with modals
- **DB:** 2 new tables (shareholders, equity_transactions)
- **API:** 8 new equity endpoints
- **Files:** db.py, app.py, dashboard/index.html, docs/EQUITY_API.md

### Key Lessons (#137-#192)
137. Advance eject must be recorded in cash_movements for ALL advances
138. Filter as workaround ≠ real fix
139. finance_advances + cash_movements eject = double-count once backfilled
140. Cash OPEX must be tracked as physical till outflow
141. Outline expiry checker must check data limit, not just time
142. SG Prometheus may not track all keys
143. Prometheus metrics must be cached (30s TTL)
144. Background pre-fetch > lazy fetch
145. Cloudflare 100s timeout + sync API call = crash
146. Google revokes leaked API keys — keep backup keys
147. GEMINI_API_KEY vs GOOGLE_API_KEY may differ
148. Coco docker-compose uses same API keys

### Infrastructure State (End of July 9)
| Port | Service | Status |
|:----:|---------|:------:|
| 443 | Xray REALITY VPN | ✅ |
| 80 | Caddy (Docker) | ✅ |
| 995 | Outline Shadowsocks | ✅ |
| 8000 | PS VIBE API | ✅ |
| 8010 | AKT Clothing Shop API | ✅ |
| 9356 | Outline Admin UI | ✅ (fast now) |
| 9357 | Agent Portal | ✅ |

---

## Memory (2026-07-18) — Stock Out Pipeline Fix + COGS Verification 🔧

### Stock Out / Hold Pipeline Fix — 5 Issues Resolved ✅
- **Fix:** Stock out pipeline had 5 issues (stock_out, stock_hold, food_cart) — all resolved. Verified at 2026-07-18 04:58 UTC.
- **Files:** patch_routes.py
- **Status:** Verified ✅

### COGS & Food Profit Logic — Full Pipeline Verified ✅
- **Audit:** Full pipeline audit of COGS and food profit logic completed. All items verified with zero discrepancies.

### Stock Out / Hold Full Flow Audit 🔍
- **Scope:** Complete audit of stock_out, stock_hold, and food_cart integration
- **Status:** Open — findings documented in MongoDB

### New Lesson (#193)
| # | Lesson |
|:-:|--------|
| 193 | **Stock-out pipeline audit must verify both release AND voucher paths** — two separate code paths can diverge, creating phantom inventory. Always cross-check COGS against both paths. |

---

## Memory (2026-07-18) — Bugs: Briefing Prediction + Response Spike

### BUG (3)
- `[open [low]]` **Prediction: Morning Briefing — 2026-07-18 (စနေနေ့) (×2)**
  *auto-bug* | `id:f996bc4a, id:71fbcbe4`
  > **Bug detected:** Prediction text for morning briefing duplicated/auto-generated. Low severity, cosmetic.

- `[open [warning]]` **[WARNING] Response Time Spike — 1109.7ms (18.7× baseline 59.4ms)**
  *auto-bug* | `id:08a15936`
  > **Bug detected:** Response time 1109.7ms vs 59.4ms baseline. Monitor for recurrence.

### New Lessons
| # | Lesson |
|:-:|--------|
| — | No new lessons from bugs — both are auto-generated monitor alerts. |

---

## Memory (2026-07-19) — Ko Toe Ban & English Group TTS Fix 🔧

### 🎙️ English With Kora — TTS Voice Auto-Generate Fix
- **Problem:** Group session was responding with text corrections only, no TTS voice audio
- **Root Cause:** AGENTS.md didn't have TTS instructions — group auto-responder skipped `tts` tool
- **Fix:** Added `## 🎙️ English With Kora Group — TTS Voice Rules` to AGENTS.md
- **Status:** ✅ Fixed

### 🚫 Ko Toe (8806200022) — Permanent Ban
- **Background:** Booking #1862 (C-09, 19:00-03:00) and #1864 (C-10, 20:00-04:00) — both cancelled with history of 6 cancellations (Jul 8-19)
- **Ban Applied:** 3-layer blocking (handlers.py BLOCKED_IDS + main.py _blocked_user_filter + DB is_active=0)
- **Lesson #194:** Dual-layer blocking required — PTB framework filter (group=-1) catches ALL message types before ConversationHandler

### New Lessons
| # | Lesson |
|:-:|--------|
| 194 | **Banning a customer bot user requires dual-layer blocking** — MUST update BOTH `BLOCKED_IDS` (handlers.py code-level check) AND `_blocked_user_filter` (main.py PTB framework-level filter at group=-1). IMPORTANT: CallbackQuery flows are NOT caught by MessageHandler filters — verify bot uses ReplyKeyboardMarkup (text messages), or add a separate CallbackQuery handler for blocked users. |

## Memory (2026-07-16)

### BUG (24)
- *auto-bug* | `id:67c41636`
- *auto-bug* | `id:db092f5f`
- *auto-bug* | `id:3336a88d`
- *auto-bug* | `id:ac04a78e`
- *auto-bug* | `id:ed11a741`
- *auto-bug* | `id:aa2a5445`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 42 times**
- *auto-bug* | `id:56f4ca90`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 42 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 8 times**
- *auto-bug* | `id:a4d2f318`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 8 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 57 times**
- *auto-bug* | `id:3692d7d1`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 57 times
- *auto-bug* | `id:3ad1a86e`
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-16 (ကြာသပတေးနေ့)
- *auto-bug* | `id:4d45cf3d`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-16 (ကြာသပတေးနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:3d975344`
- *auto-bug* | `id:ef200892`
- *auto-bug* | `id:6e5ced2f`
- *auto-bug* | `id:6c2128e6`
- *auto-bug* | `id:a06758e5`
- *auto-bug* | `id:5d01b4ca`
- *auto-bug* | `id:8f292bd6`
- *auto-bug* | `id:e7ecb19d`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 17 times**
- *auto-bug* | `id:63355302`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 17 times
- *auto-bug* | `id:f5215a18`
- *auto-bug* | `id:ec1e4062`
- *auto-bug* | `id:3c4baf9b`
- *auto-bug* | `id:979b2f06`

## Memory (2026-07-17)

### BUG (2)
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-17 (သောကြာနေ့)
- *auto-bug* | `id:ac1a0b45`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-17 (သောကြာနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:c1d5448c`

## Memory (2026-07-18)

### BUG (5)
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-18 (စနေနေ့)
- *auto-bug* | `id:f996bc4a`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-18 (စနေနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:71fbcbe4`
- `[open [warning]]` **[WARNING] response_spike: Response time 1109.7ms is 18.7x baseline (59.4ms)**
- *auto-bug* | `id:08a15936`
- > **Bug detected:** [WARNING] response_spike: Response time 1109.7ms is 18.7x baseline (59.4ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 608.9ms is 9.4x baseline (65.1ms)**
- *auto-bug* | `id:28ede372`
- > **Bug detected:** [WARNING] response_spike: Response time 608.9ms is 9.4x baseline (65.1ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 619.9ms is 14.0x baseline (44.2ms)**
- *auto-bug* | `id:526db242`
- > **Bug detected:** [WARNING] response_spike: Response time 619.9ms is 14.0x baseline (44.2ms)

### FIX (3)
- `[verified [medium]]` **Stock Out / Hold Pipeline Fix — 5 Issues Resolved**
- *stock_out, stock_hold, food_cart, sales_bot, fix* | `id:cdc03453`
- > Fixed 2026-07-18 04:58 UTC
- `[fixed [high]]` **Deposit restore on forfeited booking reactivation**
- *deposit, forfeit, restore, auto-cancel, booking* | `id:18411e2c`
- > Fixed 4 endpoints to restore deposit_status='verified' when a booking with forfeited deposit is reactivated (started, checked-in, or status changed to Active). Files: console_routes.py (api_start_cons
- `[fixed [medium]]` **Deposit Restore on Reactivation — 4 Paths Fixed**
- *deposit, forfeit, booking, reactivation, fix* | `id:890e7a74`
- > Fixed 2026-07-18 06:06 UTC

### AUDIT (2)
- `[open [medium]]` **Stock Out / Hold Full Flow Audit**
- *stock_out, stock_hold, audit, food_cart* | `id:b60c5d19`
- > Audit 2026-07-18 05:00 UTC
- `[verified [low]]` **COGS & Food Profit Logic — Full Pipeline Verified ✅**
- *cogs, food_profit, pnl, finance, audit* | `id:cdde07c2`
- > Verified 2026-07-18 05:16 UTC

## Memory (2026-07-19)

### BUG (6)
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-19 (တနင်္ဂနွေနေ့)
- *auto-bug* | `id:6a6783c5`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-19 (တနင်္ဂနွေနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:43a157c5`
- `[open [warning]]` **[WARNING] response_spike: Response time 697.4ms is 18.7x baseline (37.2ms)**
- *auto-bug* | `id:04ffd682`
- > **Bug detected:** [WARNING] response_spike: Response time 697.4ms is 18.7x baseline (37.2ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 705.9ms is 13.4x baseline (52.7ms)**
- *auto-bug* | `id:069bd827`
- > **Bug detected:** [WARNING] response_spike: Response time 705.9ms is 13.4x baseline (52.7ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 2402.4ms is 13.6x baseline (177.0ms)**
- *auto-bug* | `id:29171c4f`
- > **Bug detected:** [WARNING] response_spike: Response time 2402.4ms is 13.6x baseline (177.0ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 2445.5ms is 23.8x baseline (102.8ms)**
- *auto-bug* | `id:1768ea22`
- > **Bug detected:** [WARNING] response_spike: Response time 2445.5ms is 23.8x baseline (102.8ms)

## Memory (2026-07-20)

### Morning Health
- Time: 08:04 MMT (01:34 UTC)
- Yesterday sales: 672,000 MMK (42 transactions)
- Active members: 13
- Consoles: 10 free, 0 occupied
- System healthy, Docker all ✅
- Today bookings: 0

### Tasks
- VPS connection issue detected — check when Boss arrives at office
