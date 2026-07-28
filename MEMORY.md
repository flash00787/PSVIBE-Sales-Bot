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
| **OpenRouter (fixer)** | `Claude Sonnet 4` | pay-per-use |

**Rule:** Normal work → Flash (cheap, stable). Coding/analysis → Boss says "use pro" or sub-agents auto-use pro.

**🚫 Claude (OpenRouter) Rule (2026-07-26):** OpenRouter key (`sk-or-...`) က Claude Sonnet 4 ကို သုံးတယ်။ **Claude model ကို မသုံးခင် Boss approve ယူရမယ်** — last resort fixer အနေနဲ့ပဲ သုံးပြီး Boss ခွင့်ပြုချက်မပါဘဲ မသုံးရ။

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

### Most Recent Lessons (2026-07-27)
| # | Lesson |
|:-:|--------|
| 208 | **_mysql_exec typo — deposit restore silently crashed** — `dashboard_routes.py:353` used `_mysql_exec` (not imported) instead of `_mysql_execute`. Deposit forfeit restore on rebook (cancelled→confirmed) threw NameError silently. Booking status changed successfully but deposit stayed forfeited. 3 bookings (BK#2083, 2084, 1898) affected, 13,000 Ks stuck. Fixed: s/_mysql_exec/_mysql_execute/. |
| 207 | **Validation script cumulative comparison** — PNL endpoint with no params defaults to June 2026 (single month). When comparing BS Retained (all-time) vs PNL, must SUM all months explicitly using `?year=&month=` params. Don't trust "Cumulative" label on data that's only a single month. |
| 201 | **Pending 15min deposit timeout** — Pending bookings without deposit auto-cancel after 15 min, freeing time slots. The available-slots query checks `status NOT IN ('cancelled','done','rejected')`, so pending WITHOUT deposit was blocking slots. Refs were cancelled and status changed to 'cancelled'. Runs alongside existing no-show cron. |
| 206 | **PNL Discount bug — `SUM(gross - net)` includes deposit redemption** — Inflated discounts by 1.06M Ks. Fixed: use `SUM(discount)` column instead. Changed in finance_routes.py (balance endpoint line 509, PNL endpoint lines 540, 546). |
| 200 | **cancelled_at NULL → timeline showing endlessly** — 67 bookings had `cancelled_at = NULL` from old cancellations. Front-end 2-hour filter fell through to end_time fallback which incorrectly compared against today's wall clock. Fix: backfill with created_at, and hide bookings with no cancelled_at and no forfeited deposit. |
| 199 | **Telegram cross-bot file_id incompatibility** — File IDs generated by one bot (CUSTOMER_BOT_TOKEN) cannot be used to sendPhoto with another bot (BOT_TOKEN). Always use the originating bot's token to forward media. |


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





## Memory (2026-07-18)

### BUG (5)
- *auto-bug* | `id:f996bc4a`
- *auto-bug* | `id:71fbcbe4`
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
- *deposit, forfeit, booking, reactivation, fix* | `id:890e7a74`
- > Fixed 2026-07-18 06:06 UTC

### AUDIT (2)
- `[open [medium]]` **Stock Out / Hold Full Flow Audit**
- *stock_out, stock_hold, audit, food_cart* | `id:b60c5d19`
- > Audit 2026-07-18 05:00 UTC
- *cogs, food_profit, pnl, finance, audit* | `id:cdde07c2`
- > Verified 2026-07-18 05:16 UTC

## Memory (2026-07-19)

### BUG (6)
- *auto-bug* | `id:6a6783c5`
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



---



---



---



---

## Memory (2026-07-24) — Major Fixes Day 🔧

### 🔧 Fixes Deployed (11 Items)
| # | Fix | Key Detail |
|:-:|-----|-----------|
| 1 | **Timeline 429 Rate Limit** | 16 parallel API calls → 1 call + JS `.filter()` |
| 2 | **BranchStore 401** | `axios.get()` → `apiClient.get()` (JWT Bearer) |
| 3 | **Deposit Refund System 🆕** | `POST /api/bookings/{id}/refund`, 1hr rule, cash_movements eject |
| 4 | **Booking #1969 Yaboku Refund** | cash_movements #484/+9,000 → #487/-9,000 |
| 5 | **Deposit SS Forwarding — Cross-bot file_id** | Use CUSTOMER_BOT_TOKEN for sendPhoto |
| 6 | **New Booking & Deposit Group** | `DEPOSIT_NOTIFY_CHAT=-1003611548363` |
| 7 | **cancelled_at Backfill** | 67 bookings → backfilled with created_at |
| 8 | **Refund Button UI** | Timeline modal + Bookings Management |
| 9 | **Cancel → Auto-forfeit Deposit** | deposit_status='forfeited' on cancel |
| 10 | **Pending 15min Deposit Timeout** | Auto-cancel pending w/o deposit after 15min |
| 11 | **Refund Auto-tagging [Refund]** | Note format for easy querying |

### 📚 New Lessons (#195–#201)
| # | Lesson |
|:-:|--------|
| 195 | **429 Rate Limit from 16 parallel API calls** — Combine + client-side filter |
| 196 | **Refund ≠ Forfeited** — Three deposit states: paid, forfeited, refunded |
| 197 | **Refund 1hr rule** — Booking မတိုင်ခင် 1hr အလိုအထိသာ |
| 198 | **Separate notification channels** — Deposit ops in dedicated group |
| 199 | **Cross-bot file_id** — Telegram file_ids are bot-specific |
| 200 | **cancelled_at NULL** — Backfill + front-end must handle missing timestamps |
| 201 | **Pending deposit 15min timeout** — Auto-cancel & slot free |

### 🚀 Build Hash Timeline
| Bundle | Hashes | Change |
|:-------|:------:|:-------|
| TimelineView | 6 versions | Refund btn, auto-forfeit, time check, pending filter, cancelled_at fix, refunded hidden |
| BookingsManagement | 1 version | Refund btn + sort + search |

### New Lessons
| # | Lesson |
|:-:|--------|
| — | No new lessons (cosmetic/stale alerts) |

### New Lessons

### New Lessons (Jul 21-23)
| # | Lesson |
|:-:|--------|
| — | No new lessons — all auto-bugs (cosmetic predictions + response spike warnings) |
