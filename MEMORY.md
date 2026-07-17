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

### Most Recent Lessons (2026-07-16)
| # | Lesson |
|:-:|--------|
| 169 | **fire_count reset mid-loop sends bogus fire=0 message** — `_sync_duration_from_db()` was called AFTER `fire_count+=1` but BEFORE sending the message. Duration change reset `fire_count=0`, causing overdue calculation `(0-2)*5 = -10 min`. Fix: move sync BEFORE increment, recalculate fire_count from remaining time. |
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

## Recent Memory (2026-07-09 to 2026-07-10)

---

## Memory (2026-07-09) — Advance Payment Root Cause + VPN UI Fixes 🔧

### Advance Payment System — Root Cause Fix ✅
- **Problem:** 7 advance payments (104.8M) recorded in `finance_advances` but NEVER recorded as `cash_movements` eject. Only settlement injects (102.5M) recorded → KBZ Bank overstated by 102.5M.
- **Fix 1:** Backfilled 7 missing eject entries in `cash_movements` for KBZ Bank (104.8M total)
- **Fix 2:** Removed advance settled filter from `get_finance_balances()`
- **Fix 3:** Removed `ded_advances` from KBZ capital deduction in both balance functions
- **Files:** `finance_routes.py`
- **DB:** 7 INSERTs into `cash_movements` (KBZ Bank, eject, 104.8M)

### VPN UI Fixes (Osmo) 🐛→✅
1. **Recent Keys မပေါ်တာ:** `{key_rows}` placeholder `.replace()` မေ့နေ။ Fix: added `.replace()`.
2. **Outline Keys Data Usage Added:** Usage column with progress bar (Outline) / "—" (Xray).
3. **Sub-tab Layout moved:** Payment Summary above Xray/Outline sub-tabs.
4. **Outline VPN Expiry Checker — Data Limit Auto-Expiry:** Added Prometheus data usage vs `data_limit_bytes` check. (#141-142)

### Cash Flow & OPEX Fixes 🔧
- Cashflow opening formula: removed `finance_advances` double-count from SQL (opening: -93.4M → 11.4M ✅)
- Cash OPEX (935,400 Ks) backfilled: added opex query to till endpoints, 7 daily_till records backfilled

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

### Key Lessons (#137-#148)
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

## Memory (2026-07-11) — Outline VPN Thread Deadlock + Performance Fixes 🔧

### Outline VPN Thread Deadlock — Root Cause Fix ✅
- **Problem:** outline-web.service had 17 threads stuck in `futex_wait_queue`. Root cause: `_form_idempotency_lock` contention when `render_keys()` called concurrently. Multiple requests holding locks while waiting for Prometheus queries.
- **Fix:** Replaced threaded handler logic with async/non-blocking approach for `render_keys()`

### Slow Dashboard — Per-key Prometheus Queries 🚀
- **Problem:** `get_key_metrics()` queried Prometheus once per active Outline key via `docker exec shadowbox curl` (7 keys × 300ms = 2.1s). Remake page loading slow.
- **Fix:** Added `batch_get_metrics()` — single Prometheus query `sum(shadowsocks_data_` to collect all key metrics in one call.

### ERR_CONNECTION_CLOSED on Key Delete/Expire/Renew 🐛→✅
- **Problem:** After key operations, server rendered full dashboard (1.2s) before responding. Cloudflare closed connection → `ERR_CONNECTION_CLOSED`
- **Fix:** Changed delete/expire/renew handlers to use 302 redirect (8ms) instead of full page render.

### New Lessons (#152-#155)
| # | Lesson |
|:-:|--------|
| 152 | **Thread locks + concurrent HTTP + Prometheus = deadlock** — Never hold form idempotency locks across slow I/O (Prometheus queries). Batch or cache metrics. |
| 153 | **Prometheus queries per-key are slow** — Use `sum()` aggregator for single-query batch metrics instead of N individual queries. |
| 154 | **Post-mutation redirect beats full render** — After write operations (delete/expire), 302 redirect ~8ms vs full dashboard render ~1.2s. Avoid Cloudflare 100s timeout.
155 | **POST mutating handlers → 302 redirect** — Rename handler used `send_html(render_keys(...))` (~1.2s). Changed to `send_redirect_admin()` (~8ms). All POST handlers that mutate data must use redirect, never full page render. |


---

## Memory (2026-07-12) — AKT Clothing Bugs + Gemini Audit + Deposit Design 🔧

### Bugs Fixed: AKT Clothing Payment System (Osmo) 🐛→✅
1. **Double-Negation Bug:** Purchase payment passed negative `paid_amount` → `_record_payment_transaction_mongo()` applied `-amount` again → balance INCREASED instead of decreased (#153)
2. **Missing Account Dropdown:** Single-payment purchase form had no account selection — fixed: added payment account dropdown (#154)
3. **Edit Purchase Not Recording Transactions:** `delete_many()` used wrong field names (`ref_type`/`ref_id` vs `reference_type`/`reference_id`); frontend didn't send `payment_breakdown` on single-payment edit (#155)
4. **R/P Pay Supplier — Redundant Method:** Had both Payment Method dropdown AND Transfer Account dropdown — replaced with single accounts list (#156)

### Gemini API Key (AIzaSy…CM2E) Cost Investigation 🔍
- **Who used it:** OpenClaw Gateway (fallback from backup config before Jul 9) + Customer Bot `ai.py`
- **Action:** Removed CM2E from `/etc/psvibe/secrets.env`, restarted customer bot
- **Lesson:** Google revokes leaked keys — always audit which services use which keys (#147-148)

### Deposit Flow Design (PS VIBE) 📋
- Deposit = **30%** of session fee (was 50%)
- Methods: KPay / WavePay / AYA Pay
- Lifecycle: `none → pending → paid → verified → redeemed/refunded/forfeited`
- 5 API endpoints designed, plan to start at 8pm MMT

### VPN Redirect Fix 🔧
- Outline `/admin` route → redirect to `/login` (root page)
- Agent Portal `/agent` → redirect to `/agent/login`

### Weekly Code Quality Scan ✅
- PS VIBE Sales Bot scanned and cleaned (Jul 12, 01:30 UTC)
- No critical issues found

### Key Lesson (#157)
157. Payment account dropdown replaces payment method dropdown — account name + type (cash/bank/mobile_wallet) contains all needed info to derive method


---

## Memory (2026-07-13) — Wallet Check Skip Fix 🔧

### Bug Fixed: Wallet Insufficient Check Skipped for Member Bookings 🐛→✅
- **Problem:** `launch_session_sale` in `sales.py` had an `if booking_id:` block that unconditionally set `wallet_mins=None` for ALL bookings (guest + member), skipping the wallet balance check entirely for members.
- **Root cause:** The booking_id block was a guest-specific optimization (guests have no wallet) but was applied to all booking flows regardless of membership status.
- **Fix:** Added `if not is_guest:` check inside the booking_id block so members still get their wallet balance checked.
- **Importance:** Without this fix, members could book sessions even with insufficient wallet balance — leading to unpaid sessions and balance tracking issues.

### New Lesson (#158)
| # | Lesson |
|:-:|--------|
| 158 | **Booking flows must differentiate guest vs member** — Guest-specific optimizations (like skipping wallet checks) must be guarded by `if not is_guest:`. A blanket `if booking_id:` block accidentally skips critical validation for all members. |

### Deposit Deduction Verified ✅ (Jul 13, 19:00 UTC)
- Full flow traced end-to-end: 3 session-end callers all pass `booking_id` to `launch_session_sale`
- 6 bookings redeemed today (BK#1618-BK#1646), all correctly deducted
- BK#1614 (test) and BK#1650 (test) deleted from MySQL

### Outline VPN Key Create Timeout Fixed 🐛→✅ (Jul 13, 19:23 UTC)
- **Root Cause:** Xray/Outline key CREATE handlers rendered full dashboard (1-2s) instead of 302 redirect (~8ms). Cloudflare returned 526/524 errors.
- **Fix:** Changed both Xray and Outline CREATE handlers from `send_html(render_keys(...))` to `send_redirect_admin(...)` — Lesson #155 applied to CREATE (was previously only on delete/expire/renew)

### Referral Code Fixes 🐛→✅
3 issues fixed:
1. **BTN_ASSIGN_REFERRAL circular import** — Added lazy wrappers (`show_mm_menu`, `prompt_mm_lookup`, `prompt_referral_code`) in `bot/__init__.py` + imports in `members.py`/`referral.py`
2. **save_referral_code GSheet→API** — `bot/__init__.py` now uses API with 409 conflict check; GSheet path removed from `referral.py`
3. **fetch_members() dict vs string list** — API returns `{"members": [{id, name, ...}], total, ...}` but callers expected string list. Fixed by extracting `id` strings from `result["members"]`.
- **Files:** `bot/__init__.py`, `members.py`, `referral.py`, `member_routes.py`
- **Lessons:** #158 (guest/member), #159 (circular import wrappers), #160 (GSheet deprecated)

### Game Selection Button Changed 🐛→✅ (Jul 13, 19:40 UTC)
- **Text:** `"🤷 မရွေးတတ်ပါ"` → `"🏪 ဆိုင်ရောက်မှ ရွေးမယ်"`
- **Position:** Moved from bottom of game list to TOP
- **Files:** `customer_bot/booking_handlers.py`, `customer_bot/handlers.py`
- **Service:** `psvibe-customer-bot` restarted

### Garbled Unicode Removed from Deposit Verify Notification 🐛→✅ (Jul 13, 19:44 UTC)
- **Removed:** `"📲 Booking ခိလ ရေရာက်းထားပဲ့နှင့် ရှင့် ကိုဆက်သန္ဓိရားပါ။"`
- **Cause:** Buried Unicode escape sequences encoding garbled Burmese text
- **File:** `booking_routes.py:2264-2266`
- **Service:** `psvibe-api` restarted

