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

## Memory (2026-07-14) — VPN Admin Lock Deadlock Fix 🔧

### Reentrant Lock Deadlock — Root Cause Fix ✅
- **Problem:** `_form_idempotency_lock` (threading.Lock) caused deadlock when POST `/create` handler called `self.send_html(render_keys(...))` INSIDE `with _form_idempotency_lock:` block. `render_keys()` also acquires same lock → reentrant deadlock. 10 handler threads stuck in `futex_wait_queue`.
- **Fix 1:** Changed `_form_idempotency_lock` to `threading.RLock()`
- **Fix 2:** Moved `self.send_html(render_keys(...))` OUTSIDE all lock blocks in both Handler (port 9356) and AgentOnlyHandler (port 9357)
- **Fix 3:** Same pattern fixed for `_admin_create_lock` and `_agent_create_lock` — `render_keys()` called while rate-limit lock held
- **Locations:** 5 total across 2 handler classes
- **Verification:** 5 concurrent requests → 287-373ms each, 0 deadlocked threads, 3 normal threads only
- **File:** `/opt/outline-web/server.py`
- **Lesson:** #163

## Memory (2026-07-10) — VPN UI Fixes + Server Performance Overhaul 🔧

### Expired Display Fix — VPN Admin UI (Osmo) 🐛→✅
- **Bug:** Data-limit expired keys (`is_active=0` but `expires_at` unchanged/future) showed `"-5d ago"` → fixed to show `"🔴 Revoked"`
- **File:** `/opt/outline-web/server.py` (~line 1398)

### Server Performance Fix — ThreadingHTTPServer 🚀
- **Problem:** Python `HTTPServer` single-threaded → Cloudflare 504 → "this site can't be reached"
- **Fix:** `HTTPServer` → `ThreadingHTTPServer` (Python 3.7+ native, per-request threads)
- **Result:** Admin page 1.4s→0.2s (cached), key create no longer blocks

### Server Performance Fix #2 — Async Backup 🚀
- **Problem:** `backup_before_write()` called `subprocess.run(timeout=30)` synchronously, called TWICE per Xray operation → blocked HTTP up to 30s
- **Fix:** Background thread via `_do_backup()`, returns <1ms
- **Result:** Admin page 1.4s→0.15s, Key create ~1.5s (non-blocking)

### OpenRouter Gemini Configured ✅
- `auth-profiles.json`: Added `openrouter:default` provider
- `gateway.systemd.env`: Added `OPENROUTER_API_KEY`
- Model: `openrouter/google/gemini-2.5-flash-lite` for image analysis

### New Lessons (#149-#151)
| # | Lesson |
|:-:|--------|
| 149 | **Data-limit expired keys may have future expires_at** — Handle negative `(now - exp).days` with "Revoked" label. |
| 150 | **Single-threaded HTTP server blocks all requests** — Use `ThreadingHTTPServer` for concurrent capacity. |
| 151 | **Backup subprocess.run blocks HTTP response** — Always background subprocess calls in HTTP handlers. |

### Key Files Modified
| File | Change |
|------|--------|
| `/opt/outline-web/server.py` | Expired display fix, ThreadingHTTPServer, async backup |
| `auth-profiles.json` | OpenRouter Gemini provider added |
| `gateway.systemd.env` | OPENROUTER_API_KEY added |

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

## Memory (2026-06-03)

### BUG (3)
- `[fixed [critical]]` **Sub-Agent 1: fix_sales_rates_coupon ✅**
- *sub-agent, console* | `id:24968fef`
- > - **Issue 1**: Promotions filtered — inactive/expired promos removed from Sale Daily display - **Issue 9**: Coupon stuck at confirm step in Sale Daily — fixed broken Markdown string in discount.py
- `[fixed [low]]` **Sub-Agent 2: fix_members_bookings ✅**
- *api, sub-agent, booking* | `id:24968ff0`
- > - **Issue 2**: Member 90K default payment — removed duplicate separator text, fixed auto-confirm flow - **Issue 4**: Booking counts incorrect — fixed URL encoding bug in api_client.py _api_call_async(
- `[fixed [low]]` **Sub-Agent 3: fix_consoles_games_ssd ✅**
- *sub-agent, console* | `id:24968ff1`
- > - **Issue 3**: Session Start/End — fixed duplicate except block (SyntaxError) in console.py - **Issue 5**: Console Install — fixed type selection flow in ginst.py (was hardcoded HDD)

### FIX (3)
- `[fixed [high]]` **Major Fixes: 11 Items — All Complete ✅**
- *needs-review* | `id:24968fee`
- `[fixed [low]]` **Sub-Agent 4: fix_web_dashboard ✅**
- *dashboard, api, finance, sub-agent, console* | `id:24968ff2`
- > - Dashboard data fixed (stats, consoles, schedule, revenue-trend) - Member card tiers fixed (mapping platinum/gold/silver/bronze with toLowerCase)
- `[fixed]` **V2 Fixes (Round 2)**
- *dashboard, booking, finance, sql* | `id:24968ff4`
- > All 10 issues re-fixed and verified.  - 7 DB indexes added

### AUDIT (1)
- `[open]` **Full Audit Completed**
- *needs-review* | `id:24968ff3`
- > See final report for architecture, endpoints, GSheets usage analysis

### GENERAL (1)
- `[open [critical]]` **Grand Opening Countdown: June 6 (3 days away!)**
- *needs-review* | `id:24968fed`

## Memory (2026-06-04)

### FIX (2)
- `[open]` **Heartbeat 16:37 UTC — 2026-06-04**
- *api, vps, console, timezone* | `id:24968ff5`
- > **Health Monitor:** 94.5/100 ✅ - All 4 services active ✅
- `[open [critical]]` **Heartbeat 20:07 UTC (03:37 MMT)**
- *api, customer-bot, docker, sql, console* | `id:24968ff6`
- > - All services active: API, bot, customer bot - Docker healthy: mysql, nova, coco, gateway, construction_bot

## Memory (2026-06-05)

### BUG (6)
- `[open [high]]` **Major Bug Hunt - Phase 3 (13:00-15:20 UTC)**
- *timezone* | `id:24968ff7`
- `[open [low]]` **Known Issues**
- *api* | `id:24968ffb`
- > - `_check_low_balance_alert` has `name 'os' is not defined` — minor, doesn't block flow - API `sales/record` returning `success=false` from bot — root cause still unclear but error msgs now visible
- `[open [low]]` **Phase 3.5 — Booking Flow Fixes (16:00-17:00 UTC)**
- *sql, api, booking, timezone* | `id:24969000`
- > #### 7. Booking HTTP 500 — Date Format Mismatch 🔥 (16:40 UTC) - **Symptom:** Sale Bot creates booking → API returns HTTP 500
- `[open]` **Files Modified (Final Inventory)**
- *console, sales-bot, imports, api, booking* | `id:24969002`
- > - `/root/psvibe_api_server/app.py` — `deduct_mins` + `GenericResponse` import + date format parsing + auto-confirm staff bookings + slot conflict check - `/root/psvibe_api_server/models.py` — `error:
- `[open [low]]` **Known Remaining Issues (Post-Grand-Opening)**
- *sql, api, booking* | `id:24969003`
- > - `_check_low_balance_alert` has `name 'os' is not defined` — non-blocking, alert silently fails - GSheet fallback `sales/record` path — secondary path, API/MySQL primary path now working
- `[open [low]]` **Phase 4 — Booking Flow Reorder (17:00-18:30 UTC)**
- *console, booking, timezone, customer-bot* | `id:24969004`
- > #### 11. Booking Flow Skip Bug (Name/Phone/Console skipped) 🔥 - **Root cause:** `cmd_staff_booking` returned `SBK_DATE` which mapped to `step_sbk_date` (PHONE handler), not the date handler. Also, aft

### FIX (9)
- `[fixed]` **Issues Found & Fixed**
- *api, vps* | `id:24968ff8`
- > #### 1. Coupon API Field Name Mismatch 🔥 - **Root cause:** Added coupon API call but used `cd.get("coupon_code")` and `cd.get("coupon_mins")` — API response uses `code` and `minutes`
- `[open]` **Services**
- *api, customer-bot* | `id:24968ff9`
- > - `psvibe-api` — ✅ active (restarted multiple times) - `psvibe-sale-bot` — ✅ active (restarted)
- `[open]` **Files Modified**
- *api, sales-bot, console* | `id:24968ffa`
- > - `/root/psvibe_api_server/app.py` — added `deduct_mins = req.get("deduct_mins")` - `/root/psvibe_api_server/models.py` — added `error: Optional[str]` to GenericResponse
- `[fixed [critical]]` **Grand Opening**
- *console* | `id:24968ffc`
- > - **Tomorrow:** June 6, 2026 (Saturday) 🎮🔥 - All critical path bugs fixed (coupon, wallet, sale record, console selection)
- `[open]` **Files Modified (Final Session Inventory)**
- *api, sales-bot, console, booking* | `id:24968ffe`
- `[open [low]]` **Known Remaining Issues (Non-Blocking)**
- *sql, api* | `id:24968fff`
- > - `_check_low_balance_alert` has `name 'os' is not defined` — minor, alert just silently fails - GSheet fallback `sales/record` path — still needs test but API (MySQL) path now fixed
- `[open]` **Services (Final State)**
- *api, customer-bot* | `id:24969001`
- > - `psvibe-api` — ✅ active - `psvibe-sale-bot` — ✅ active
- `[open]` **Services (Final State 19:09 UTC)**
- *api, customer-bot, timezone* | `id:24969008`
- `[fixed [critical]]` **Grand Opening — TOMORROW June 6, 2026 (Saturday) 🎮🔥🎉**
- *api, console, sql, reminder, booking* | `id:24969009`
- > - **All critical path bugs fixed and data reset complete:**   - ✅ Coupon generation

### LESSON (3)
- `[open [critical]]` **🧠 Critical Lessons Learned**
- *sql, api* | `id:24968ffd`
- > 1. **FastAPI response_model silently strips undeclared fields** — always audit response models against actual return shapes 2. **`bool(0) == False`** — `"x if x else default"` pattern breaks on `0`; u
- `[open]` **Phase 5 — Grand Opening Data Reset (18:31 UTC)**
- *console, booking, timezone* | `id:24969005`
- > #### 13. Data Reset (18:31 UTC) - **Cleared tables:** `stock_in`, `member_coupons`, `topup_log`, `sales_daily`, `receipts`, `promotions_log`, `stock_out`, `attendance_log`, `members`, `member_wallets`
- `[open [critical]]` **🧠 Critical Lessons Learned (Complete)**
- *sql, api* | `id:24969007`

### FEATURE (1)
- `[open]` **Phase 6 — Features (18:37-19:09 UTC)**
- *customer-bot, console, booking, timezone* | `id:24969006`
- > #### 14. Console Status Board: Reserved (🟡) Status (18:37 UTC) - **Request:** Show "Reserved" (🟡) for confirmed bookings 2 hours before the booking time

## Memory (2026-06-06)

### BUG (3)
- `[open]` **🐛 Bug Round 02:06-02:40 UTC (08:36-09:10 Myanmar Time)**
- *customer-bot, console, timezone* | `id:2496900b`
- > #### Bug 1: Duration နှစ်ခါမေးတာ (Customer Bot) - **Symptoms:** After selecting PS5/PS5 Pro/Any, the bot asks about duration twice in a loop
- `[open [low]]` **Logs**
- *vps, timezone* | `id:2496900c`
- > - VPS Monitor Alert Check at 02:01 UTC → NO ALERTS (all services active, health OK) - Note: Monitoring cron jobs may be stale (last entries from May 27 — ~10 days old)
- `[open]` **🐛 Bug Round: Food Menu Not Working (03:00-03:30 UTC / 09:30-10:00 Myanmar Time)**
- *timezone* | `id:2496900d`

### FIX (2)
- `[open]` **The Problem**
- *customer-bot, timezone* | `id:2496900e`
- > Customer Bot "🍕 Food Menu" button was not showing any items. Multiple fix attempts.
- `[open]` **Post-Fix Status (13:43 UTC)**
- *dashboard, api, customer-bot, timezone* | `id:2496900f`
- > - All 4 services active: `psvibe-api`, `psvibe_customer_bot`, `psvibe-sale-bot`, `psvibe-dashboard` - Food Menu is working (need Boss to re-test)

### GENERAL (1)
- `[open]` **🎮 Grand Opening Day! 🔥 Day of Grand Opening**
- *needs-review* | `id:2496900a`

## Memory (2026-06-07)

### FIX (1)
- `[fixed]` **🐛 api_client.py Fix Summary (18:17 UTC)**
- *api, sql, timezone* | `id:24969010`
- > - `api_post()` in api_client.py changed from `?api_key=` query param to `X-API-Key` header - `api_get()` in api_client.py also fixed

## Memory (2026-06-08)

### BUG (3)
- `[fixed]` **💰 Account Balance Fix (07:44-08:05 UTC)**
- *timezone, finance* | `id:24969013`
- > - **GROUP BY bug**: collapsed payment strings → Cash off by -60,000 Ks. Fixed: removed GROUP BY, iterate all rows. - **Wave/AYA Pay not saving**: hardcoded payment_method → dynamic
- `[open]` **🏦 ACM's Acc + API Auth (14:50-15:15 UTC)**
- *api, timezone, vps* | `id:24969019`
- > - Normalization mismatch: `"acm"` in DB vs `"acm's acc"` in code - `systemctl restart` silent failure → `kill -9`
- `[open]` **📦 Asset Duplicate Cleanup (18:20 UTC)**
- *sql, timezone* | `id:24969022`
- > - Deleted **25 duplicate asset rows** (all had `per_price=NULL`) - Before: 54 rows → After: 29 rows (all clean, unique)

### FIX (9)
- `[open]` **🔄 FIFO Wallet Calculator Integrated (17:50 UTC)**
- *dashboard, api, sql, timezone* | `id:24969011`
- > - **Built** `/root/psvibe_api_server/fifo_wallet.py` — FIFO (oldest topups consumed first) - **Added** `POST /api/member/wallet/update` endpoint for real-time wallet deduction
- `[open]` **🎮 Game Library Fixes (09:00-09:45 UTC)**
- *api, timezone* | `id:24969016`
- > - SSD: substring→prefix `cid.upper().startswith("SSD")` - Duplicate games: `install_type != "Session"` + API protection
- `[fixed]` **⏰ Session Timer Reminder Fix (12:15-12:30 UTC)**
- *console, reminder, api, timezone* | `id:24969017`
- > - `_is_session_active()` was calling non-existent endpoint → fixed to `fetch_console_status`
- `[open]` **🐛 Coupon Stuck Fix (12:30-12:50 UTC)**
- *timezone* | `id:24969018`
- > - Keyboard race condition on stale button taps → added catch-all `else` in `step_coupon_confirm`
- `[open [critical]]` **🏪 Stock In Edit + Payment Fix (15:05-15:45 UTC)**
- *sql, api, dashboard, timezone* | `id:2496901b`
- > - PyMySQL `LIKE '%/%'` conflict → `CONCAT('%', '/', '%')` - 35 backdated stock_in records → KBZ Bank
- `[open]` **🔄 Multiple Balance Fixes**
- *sql, finance* | `id:2496901c`
- > - **Asset query**: `SUM(amount)`→`SUM(per_price*qty)` (820M→126M) - **KBZ Bank deductions**: Assets 126.6M + Advances 104.8M + Prepaid 22.4M
- `[open]` **Services Status (17:55 UTC)**
- *api, customer-bot, timezone* | `id:24969020`
- > - psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅
- `[open]` **⏳ Pending: Finance Dashboard Fix (18:30 UTC)**
- *dashboard, finance, timezone* | `id:24969023`
- > - Boss reported: "Finance Dashboard မှားနေသေးတယ် + Category မစုံသေးဘူး" - Frontend rebuilt & deployed but issue persists — waiting for Boss to specify exact mismatch (balances vs display format vs cat
- `[open]` **Services (18:30 UTC)**
- *api, customer-bot, timezone* | `id:24969024`

### LESSON (1)
- `[open]` **🧠 Key Lessons**
- *sql, vps* | `id:2496901f`
- > - GROUP BY collapses pipe-delimited data → iterate all rows - Elif chains must cover ALL variants (`"wave"` ≠ `"wavepay"`)

### FEATURE (2)
- `[open]` **🍔 Food Menu Grouping (11:07-11:25 UTC)**
- *sql, api, sales-bot, customer-bot, timezone* | `id:24969014`
- > - New endpoint `GET /api/fetch_food_menu` — categories with emoji headers - MySQL + API + Sales Bot + Customer Bot updated
- `[open]` **🍔 Food Sale Feature (17:00-17:30 UTC)**
- *console, timezone* | `id:2496901a`
- > - Standalone `🍔 Food Sale` button (no console/game) - `is_food_sale` flag → records `type: "food_only"`

### DECISION (1)
- `[open]` **💵 Inject/Eject + Web Admin (08:15-08:50 UTC)**
- *api, sql, timezone* | `id:24969015`
- > - `cash_movements` table + `/api/cash/inject|eject|movements` - Bot `/inject` `/eject` (Boss-only) + `/admin/cash` web page

### AUDIT (1)
- `[open [critical]]` **📊 Revenue Breakdown (final verified)**
- ** | `id:2496901d`
- > - Game: 557,666 Ks | Food: 66,000 Ks | Topup: 90,000 Ks - Discount: 114,833 Ks | Liability: 81,000 Ks | Total Income: 713,666 Ks

### GENERAL (3)
- `[open]` **Earlier Today (June 8) — Tasks before FIFO**
- *needs-review* | `id:24969012`
- `[open]` **🗑️ Google Sheet Sync Removed**
- *sql* | `id:2496901e`
- > - `sync_member_wallets()` 2216 chars deleted - GSheet fallback replaced with logging
- `[open]` **🗑️ GSheet Sync Completely Removed (18:09 UTC)**
- *dashboard, api, finance, sql, console* | `id:24969021`
- > - **All 6 remaining sync functions deleted** from `sync_service.py` — `sync_games_library`, `sync_console_status`, `sync_staff_records`, `sync_settings_config`, `sync_finance_opex`, `sync_finance_asse

## Memory (2026-06-09)

### FIX (6)
- `[fixed]` **✅ Done**
- *needs-review* | `id:24969026`
- `[fixed [low]]` **Cash Flow Statement (✅ Complete)**
- *api, finance, console* | `id:24969027`
- > - Opening = **300M** (initial KBZ capital) - Operating: sales 889K + topup income - opex 7.05M - stock 733K = **-6.9M**
- `[open [low]]` **Key Fixes**
- *api, finance* | `id:24969028`
- > 1. **Capital Withdrawals removed** — eject was stock payment, not withdrawal 2. **ACM's Acc is a business account** — just separate cash box, not owner transfer
- `[fixed]` **Prepaid Rent Amortization (✅ Done)**
- *sql, finance* | `id:24969029`
- > - Created `prepaid_amortization` table - 22,425,000 Ks = Rental Fee for 9 months (June 1 → Feb 28)
- `[open]` **🏗️ Financial Dashboard Deployed (19:44 UTC)**
- *dashboard, api, finance, timezone* | `id:2496902b`
- > - Created FinanceDashboardView.vue with unified P&L + BS + CF view - Added route `/finance-dashboard` to router
- `[fixed]` **✅ YTD + Revenue Trend features completed (20:15 UTC)**
- *dashboard, api, timezone* | `id:2496902e`
- > - YTD: Added `ytd=true` param to PNL endpoint → returns Jan-to-month data - Revenue Trend: Added `/api/dashboard/financial/revenue-trend` returning monthly game + food revenue for the year

### LESSON (1)
- `[open [low]]` **Lessons Learned**
- *finance* | `id:2496902a`
- > - cash_movements raw balance (304M) ≠ actual financial position — it only tracks internal transfers - Web Finance and Cash Flow must use **identical income allocation** to match

### FEATURE (1)
- `[open]` **After memory flush: YTD + Revenue Trend work (20:10 UTC)**
- *dashboard, api, console, memory, timezone* | `id:2496902c`
- > - Moving on to build YTD Reports and Revenue Trend Graph features # YTD + Revenue Trend placeholder

### GENERAL (2)
- `[open]` **🕐 Time**
- *timezone* | `id:24969025`
- > UTC 17:30-19:30 | Myanmar 00:00-02:00 (June 10)
- `[open]` **Exec approach: checking PNL endpoint**
- *api* | `id:2496902d`

## Memory (2026-06-10)

### BUG (4)
- `[open]` **Root Cause**
- *imports, dashboard* | `id:24969030`
- > Dashboard is a Vue SPA with **lazy-loaded components**. The main JS was renamed to `.v2.js` (cache busting), but ALL lazy chunks still imported from `"./index-DDJXoolO.js"` (original path). Cloudflare
- `[open]` **TODO for Morning**
- ** | `id:24969038`
- > - Find gameplay for 4 poster-only games (try different alphacoders slugs) - Find posters for 4 empty/unreleased games (may just not exist yet)
- `[open]` **🎯 Data For Game Menu — FINAL RESULT (19:30 UTC+)**
- *timezone* | `id:24969039`
- > **37/41 games have BOTH Poster + Gameplay** 🔥 **4/41 empty** (all unreleased: Basketball 2026, Expedition 33, FIFA 2026, Little Nightmare 3)
- `[open]` **Empty (unreleased)**
- *needs-review* | `id:2496903d`
- > Basketball 2026, Expedition 33, FIFA 2026, Little Nightmare 3

### FIX (3)
- `[open]` **🎯 Sales Daily Lazy-Load Fix (07:02-07:08 UTC)**
- *timezone* | `id:2496902f`
- `[open]` **Fix**
- *imports* | `id:24969031`
- > - Updated ALL 22 lazy-loaded chunks to import from `./index-DDJXoolO.v2.js` instead - Also overwrote the original `index-DDJXoolO.js` with correct content (for safety)
- `[open]` **Final Result (37/41 games populated)**
- ** | `id:24969035`
- > - **33 games**: ✅ Poster (Steam Library 1200x1800 box art) + Gameplay (Steam screenshots) - **4 games**: ✅ Poster only (Assassin's Creed Shadows, Astro Bot, INVINCIBLE VS, Spider-Man 2)

### LESSON (1)
- `[open [high]]` **Key Lessons**
- *console* | `id:24969037`
- > - **Steam Library images** are portrait/poster style (600x900 → 1200x1800 @2x) — exactly what Boss wanted - **Steam screenshots** are actual gameplay highlights at 1920x1080 — perfect for "gameplay hi

### DECISION (1)
- `[open]` **Now Boss only needs to hard-refresh (Ctrl+F5 or Incognito)**
- *needs-review* | `id:24969033`

### GENERAL (6)
- `[open]` **All Related Files**
- *imports* | `id:24969032`
- > - Main JS: `index-DDJXoolO.v2.js` (HTML ref) - All lazy chunks: import from `./index-DDJXoolO.v2.js`
- `[open]` **🖼️ Data For Game Menu — Poster + Gameplay Project (18:00-19:30 UTC)**
- *timezone* | `id:24969034`
- `[open [high]]` **Sources Used**
- *api, console* | `id:24969036`
- > 1. **Steam Library Art (1200x1800 portrait)** — Best for poster-style box art. Direct CDN: `https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900_2x.jpg` 2. **Steam Screenshots API** —
- `[open]` **Sources**
- *api, console* | `id:2496903a`
- > - **Posters:** Steam CDN `cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900_2x.jpg` — 1200x1800 portrait/box-art style - **Gameplay:** Steam API `store.steampowered.com/api/appdetails?appi
- `[open]` **Games with Poster+Gameplay**
- ** | `id:2496903b`
- > GTA 5, Tekken 8, Devil May Cry 5, Mortal Kombat, Elden Ring, Horizon Forbidden West,  Red Dead Redemption 2, God of War Ragnarok, Witcher 3, Batman Arkham Knight, Hades,
- `[open]` **Games with Poster only**
- *needs-review* | `id:2496903c`
- > None (all 37 got gameplay in final pass)

## Memory (2026-06-11)

### BUG (2)
- `[open]` **Geo-blocking Issue**
- *vps* | `id:2496903f`
- > - VPS (Singapore, 5.223.81.16) blocked by iBet789 geo-filter - Cloudflare WARP failed (not Myanmar IP)
- `[open]` **Other Changes**
- ** | `id:24969041`
- > - Smart Alert System cron: **30 min → 1 day** (Boss said too spammy) - Boss wants to fix SSH issue tomorrow morning

### FIX (2)
- `[fixed]` **iBet789 Bot Progress**
- *dashboard* | `id:2496903e`
- > - Bot code built and deployed at `/opt/ibet789-bot/` - Systemd service `ibet789-bot` created (currently waiting for VPN)
- `[open]` **Pending for Tomorrow (June 12)**
- *console, vps* | `id:24969042`
- > 1. **⛔ SSH Fix**: Boss needs to use Hetzner Console → open Web Console → login → run:    ```bash

### FEATURE (1)
- `[open]` **Termux Proxy Attempt**
- *vps* | `id:24969040`
- > - Boss installed Termux on phone - SSH key shared: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIImD9p7oVNxsKsWItSGXOxIXyr7KbCtzTAoAsQPH04Ea u0_a558@localhost`

## Memory (2026-06-12)

### FIX (1)
- `[fixed]` **iBet789 Bot — Auth Fixed! ✅ (June 12, 18:06 UTC)**
- *dashboard, timezone, finance* | `id:24969043`
- > - Auth bug (number vs string comparison) fixed — Bot now correctly accepts Boss's commands - Boss tested and got response: "No Balance Found"

## Memory (2026-06-13)

### BUG (8)
- `[open]` **Customer Bot Users — Member Enrichment**
- *sql, customer-bot, api* | `id:24969045`
- > Per Boss request: when a Customer Bot user is also a PS VIBE member, auto-populate their member details.
- `[open]` **🔴 Bug: Booking Cancel → No Staff Notification**
- *api, customer-bot, sales-bot, console, booking* | `id:24969047`
- > - **Root cause:** API cancel endpoint (`app.py` `api_booking_cancel`) only notifies customer via Customer Bot — has NO code to notify staff/admin group - Customer notification already existed (Telegra
- `[open]` **🕹️ Game Library — Solo/Multi Classification**
- *sql* | `id:2496904c`
- > - Classified all 41 games in `games_library` table via SQL: Solo(23), Multi(13), Both(5) - **Games changed to Solo:** 19 titles (Action games, Platformers, Souls-like, etc.)
- `[open]` **🧹 Customer Bot Game Library — Display Overhaul**
- *customer-bot, console* | `id:2496904e`
- > - Changed `cmd_game_library`: replaced PS5/PS4 platform grouping with Solo/Multi/Both grouping - **Old:** Grouped by platform (PS5: 37 titles, PS4: 4 titles) — poor organization since 90% are PS5-only
- `[open]` **🔴 Bug: `_session_end_notify()` hitting 404**
- *api, customer-bot, sales-bot, feedback, booking* | `id:24969050`
- > - **Root cause:** The sales bot calls `POST /session-end-notify` but this endpoint was **completely missing** from `app.py` - Created full `POST /api/session-end-notify` endpoint in `app.py`:
- `[open]` **Session VII (~19:00-19:24 UTC — Dashboard Bug Fix)**
- *dashboard, timezone* | `id:24969053`
- `[open]` **🐛 Fixed: Kora Dashboard Users Tab Column Misalignment**
- *dashboard, sql, finance* | `id:24969054`
- > - **Bug:** User reported column header/data mismatch in Users tab; other tabs stuck on "Loading..." - **Root cause:** `renderUserTable()` rendered only **7 `<td>` elements** but header had **11 `<th>`
- `[open]` **📋 Pending (Boss Action Needed)**
- *api, vps* | `id:24969057`
- > 1. **Cloudflare DNS:** Add CNAME for `kora.ps-vibe.com` → `tunnel-endpoint` for subdomain access 2. **n8n Payment (€25.68):** 2nd notice received, subscription may expire

### FIX (7)
- `[fixed]` **✅ 10-Minute-Before Staff Notification**
- *console, feedback, reminder, booking, sales-bot* | `id:24969048`
- > - Added `check_and_notify_staff_10min()` function to `booking_reminder.py` - Checks bookings starting in 8-14 min window (covers 15-min cron gap)
- `[open]` **⭐ Feedback & Rating System**
- *sql, feedback, customer-bot, console, api* | `id:24969049`
- > - Boss asked about adding feedback/rating for customers - **Found:** Customer Bot ALREADY has `cmd_feedback` with inline rating buttons (1-5 ⭐) + comment prompt
- `[open]` **Current State**
- *sql, api, customer-bot, dashboard* | `id:2496904a`
- > | Service | Status | |---------|:------:|
- `[open]` **📚 Genre Classification**
- ** | `id:2496904d`
- > - Updated genres for all 41 games: Action Adventure(9), Fighting(6), Action RPG(5), Sports(4), Action(2), Platformer(2), Co-op(2), Horror(2), Survival Horror(2), Strategy(1), RPG(1), Hack and Slash(1)
- `[fixed]` **✅ Services Status (after Session VI)**
- *api, customer-bot, dashboard* | `id:24969052`
- `[open]` **🔧 Fix Applied:**
- *feedback, vps, dashboard* | `id:24969055`
- > 1. Restored clean git version (`853297a`) — removed file corruption (duplicated renderUserTable) 2. Applied git checkout `b17c442` — latest clean commit (has Feedback tab)
- `[fixed]` **✅ Final Service Status**
- *api, feedback, customer-bot, dashboard* | `id:24969056`
- > | Service | Status | Notes | |---------|:------:|-------|

### FEATURE (3)
- `[open]` **⭐ Kora Dashboard Feedback Tab**
- *console, vps, feedback, dashboard, sql* | `id:24969051`
- > - Added "⭐ Feedback" tab to Kora Dashboard (`index.html`):   - Stats row: Total Reviews, Avg Rating (out of 5), Positive % (4-5⭐), Negative % (1-3⭐)
- `[open]` **🌐 Social Links Added to Customer Bot**
- *memory, customer-bot* | `id:24969059`
- > - **Contact section (`cmd_contact`):** Added "🌐 Social Links" sub-section with:   - 📘 Facebook Page: https://www.facebook.com/ps5gamecenter
- `[open]` **🧠 New Lessons (June 13)**
- *api* | `id:2496905a`
- > 1. **JS `<script>` block fragility:** A single syntax error in any inline `onclick` or template literal within a `<script>` block kills ALL JavaScript in that block. Always validate carefully. 2. **Fa

### DECISION (1)
- `[open [low]]` **🧹 Food Menu Reposition**
- *booking* | `id:2496904f`
- > - Moved `BTN_FOOD` button up to row 3: `[BTN_FOOD, BTN_RATE]` (right below `[BTN_MYBOOKINGS, BTN_GAMES]`) - This is a temporary measure until Boss approves main menu restructuring plan

### GENERAL (4)
- `[open]` **Session IV (~15:50-16:30 UTC — Customer Bot Member Enrichment)**
- *customer-bot, timezone* | `id:24969044`
- `[open]` **Session V (~16:30-18:30 UTC — Booking Notifications & Feedback System)**
- *feedback, booking, timezone* | `id:24969046`
- `[open]` **Session VI (~18:30-19:00 UTC — Kora Dashboard: Game Library & Cleanup Tasks)**
- *dashboard, timezone* | `id:2496904b`
- `[open]` **Session VIII (~19:47-19:51 UTC — Social Links: FB + TikTok in Customer Bot)**
- *customer-bot, timezone* | `id:24969058`

## Memory (2026-06-14)

### BUG (9)
- `[open]` **Pre-existing (Warning-level, Not Blocking)**
- ** | `id:24969061`
- > - **`inv_sh` = None** — K1 inventory Google Sheets update always fails silently (try/except catches it) - **`fetch_balance_mins/-` 404** — Empty member_id when checking Guest wallet
- `[open]` **Services Status**
- *sql, customer-bot, api* | `id:24969062`
- > All active throughout the day: psvibe-sale-bot, psvibe_customer_bot, psvibe-api, cloudflared-tunnel, Caddy, n8n, MySQL, fail2ban, Health Monitor (~91.6/100)
- `[open]` **Investigation: `_remind_loop` Never Fires (Known Pre-existing Bug)**
- *console* | `id:24969065`
- > - **Status:** Investigated but not fixed. Root cause inconclusive. - Logs confirm `_remind_loop` task is created via `load_and_restore()` but **never executes** `_extend_timer_kb()` or `sendMessage`
- `[open [low]]` **Files Modified:**
- *api, console, sales-bot, customer-bot* | `id:2496906a`
- > | File | Changes | |------|---------|
- `[open]` **Boss Reports (Ongoing Issues — 18:22-18:42 UTC)**
- *needs-review, timezone* | `id:24969074`
- `[open]` **Issue A: "Voucher ထဲမှာ မပါလာဘူး" + "Game play mins တွေပါ ပျောက်သွားတယ်"**
- *imports, booking* | `id:24969075`
- > - Food items not appearing in voucher - Game minutes also disappear
- `[open]` **Issue B: "Session တခု end လိုက်ရင် ကျန်တဲ့ session တွေပါ start time ကို food sal**
- *api, booking* | `id:24969076`
- > - Ending one session resets other active sessions' start times + food orders - **Hypothesis:** `context.user_data` shared per staff chat — `launch_session_sale` overwrites user_data for one session, c
- `[open]` **Issue C: "Sale voucher ဖွင့်တာလည်း အရမ်းကြာနေတုန်းပဲ့"**
- *needs-review* | `id:24969077`
- > - **Already fixed** — see Fix 10 above. Non-blocking coupon gen should resolve.
- `[open]` **Heartbeat (18:42 UTC)**
- *imports, timezone* | `id:24969079`
- > - All services running after final restart - Fixes 8-10 deployed (import error, dead code, coupon blocking)

### FIX (14)
- `[open]` **Fixes Deployed Today**
- *needs-review* | `id:2496905b`
- `[open [low]]` **Fix 1: Booking Flow — Member Keyboard Hang**
- *api, console, booking* | `id:2496905c`
- > - **Error:** `Can't parse keyboard button: can't find field 'text'` when selecting console - **Root cause (2 layers):**
- `[open]` **Fix 2: "No telegram_chat_id, skip notification"**
- *api, console* | `id:2496905d`
- > - **Root cause:** `app.py` line 1517 had `@app.post("/api/consoles/start-session")` orphaned — decorated `api_session_end_notify` instead of `api_start_console_session` - **Fix:** Moved decorator to l
- `[open]` **Fix 3: Food Sale — Stock Map Rebuild Failed**
- *api, imports* | `id:2496905e`
- > - **Error:** `name '_psvibe_get_async' is not defined` - **Root cause:** Function never existed in `api_client.py` — was imported in 3 places in `sales.py` but never defined
- `[open [low]]` **Fix 4: Booking Extend — `message_thread_id is not defined`**
- *booking, reminder, sql* | `id:2496905f`
- > - **File:** `bot/handlers/booking_flow.py` - **Root cause:** `_do_extend()` called `persist_reminder(..., message_thread_id)` but `message_thread_id` wasn't a parameter
- `[open [low]]` **Fix 5: `name 'os' is not defined`**
- *imports, reminder* | `id:24969060`
- > - **File:** `bot/handlers/notify.py` - **Root cause:** `_check_low_balance_alert` used `os` module but never imported it
- `[open [low]]` **Fix 6: Ovaltine Cookies — Case-Sensitive Match Error**
- *api* | `id:24969064`
- > - **Error:** "Ovaltine cookies" (lowercase) chosen from food menu but `if choice not in prices:` failed because database has "Ovaltine Cookies" (capital C) - **Root cause:** `step_food_menu` used exac
- `[open]` **Fix 7 (NEW): Food Cart Feature — Session Food Orders (17:44 UTC)**
- *timezone, console* | `id:24969067`
- > **Request:** Customers need to order food during gaming sessions, payment at session end. **Design:** Boss approved Phase 1 → Phase 2 approach. Phase 1 done today.
- `[open]` **Services Restarted:**
- *api, customer-bot* | `id:2496906b`
- > - psvibe-api ✅ (food-cart routes) - psvibe-sale-bot ✅ (new handler functions)
- `[open]` **API Verified:**
- *api, console* | `id:2496906c`
- > - POST /api/food-cart: CREATE ✅ - GET /api/food-cart/B001: SELECT (unfulfilled only) ✅
- `[open [critical]]` **Fix 8: Import Path Error — `cmd_session_food_order` (18:20 UTC)**
- *imports, api, console, timezone* | `id:24969071`
- > **Error:** "Food Sale" button shows active consoles → staff picks console → bot shows game list (wrong menu) / crashes **Root cause:** `cmd_session_food_order` (sales.py line 145) imports `_psvibe_get
- `[open]` **Fix 9: BTN_CLEAR_CART Dead Code (18:20 UTC)**
- *timezone, customer-bot* | `id:24969072`
- > **Error:** BTN_CLEAR_CART handler never triggers **Root cause:** In `step_food_menu`, when `session_food_order` flag is set and user clicks Done, the code hits `return await prompt_confirm(...)` BEFOR
- `[open [low]]` **Fix 10: Coupon Generation Blocking — Voucher Slow to Open (18:34 UTC)**
- *api, console, timezone* | `id:24969073`
- > **Error:** Sale voucher opening still very slow (Boss confirms) **Root cause:** `step_end_session` in `console.py` line 370 has `await asyncio.to_thread(api_post, "coupons/generate", ...)` — this BLOC
- `[open [low]]` **Summary Statistics (End of Day)**
- *booking, api, console, reminder* | `id:24969078`
- > | Metric | Value | |--------|-------|

### FEATURE (2)
- `[open]` **Heartbeat (17:44 UTC) — During Food Cart Feature Development**
- *api, customer-bot, sql, timezone* | `id:2496906f`
- > - All services running: psvibe-sale-bot, psvibe_customer_bot, psvibe-api, cloudflared-tunnel, Caddy, n8n, MySQL, fail2ban - Food Cart Feature freshly deployed
- `[open]` **Heartbeat (17:44 UTC) — Quick Health Check**
- *api, timezone* | `id:24969070`
- > All services nominal. Food Cart Feature freshly deployed and API-verified. # June 14, 2026 — Daily Log

### AUDIT (1)
- `[open]` **Tests Done:**
- *sql, api* | `id:2496906d`
- > - POST → GET → DELETE cycle verified on all food_cart API endpoints - SQL query verified both create and fulfill timestamps correct

### GENERAL (5)
- `[open]` **Heartbeats**
- ** | `id:24969063`
- > Multiple heartbeats throughout the day. All clear. Known old notification (yyo-personal-wallet, June 11) still present. # June 14, 2026 — Daily Log
- `[open]` **# June 14, 2026 — Daily Log (cont.)**
- *needs-review* | `id:24969066`
- `[open]` **What was built:**
- *sql, api, booking* | `id:24969068`
- > #### 1. MySQL `food_cart` Table ```sql
- `[open [low]]` **Flow:**
- *console, booking* | `id:24969069`
- > ``` Console → [🍔 Food Sale] → Pick console → Food Menu → Items → Done
- `[open]` **Pending (Phase 2 — Future):**
- *customer-bot* | `id:2496906e`
- > - Customer Bot direct ordering (customers order from their own chat) - Customer Notifications when food arrives

## Memory (2026-06-15)

### BUG (4)
- `[open]` **Fix 5: Food Note & End Session booking_id not found (bug fix)**
- *api, console, booking* | `id:24969084`
- > - **Root cause:** `console.py` booking lookups used `_b.get("consoleId")` but API `_map_booking_row` maps `console_id` → `consoleType`. Never found any booking → booking_id="" → food note "No booking_
- `[open [low]]` **Pending Items**
- *api, vps* | `id:2496908a`
- > 1. **Food Note issue** — Boss asked "ဆက်လုပ်ပါ" which could mean continue on this. Awaiting further instruction. 2. **n8n payment (€25.68)** — 2nd notice, subscribe may expire
- `[open]` **Bug: PNL Depreciation Wrong (6,995,548 vs correct 3,078,949)**
- *sql, console* | `id:2496908d`
- > **Problem:** PNL depreciation was `SUM(monthly_dep)` for ALL 39 assets. But 12 assets (Interior Decoration 98.6M, PS5 Console ×8 21.6M, Sofa ×10 14.4M, CCTV, Inverter, Battery, SPC Flooring, etc.) wer
- `[open]` **Known Issue**
- *needs-review* | `id:24969099`
- > - Daily sales report cron failed (timed out) — needs investigation

### FIX (22)
- `[open]` **🐛 Fix: Morning Health Summary MySQL Query Bug**
- *sql, vps* | `id:2496907a`
- > **Root cause:** `lib/ssh_vps.js` → `mysqlQuery()` used `2>&1` to merge stderr into stdout. MySQL password warning (`"mysql: [Warning] Using a password on the command line interface can be insecure."`)
- `[fixed [critical]]` **✅ Services Status (June 15, 02:32 UTC)**
- *needs-review, timezone* | `id:2496907b`
- > All services healthy. No critical alerts.
- `[open]` **🐛 June 15 — Fixes Applied (02:42 UTC)**
- *needs-review, timezone* | `id:2496907c`
- `[open]` **Fix 1: POST /api/food-cart `AttributeError: 'int' object has no attribute 'strip**
- *sql, api, booking* | `id:2496907d`
- > - **Root cause:** `booking_id` from MySQL is an integer, but API tried `.strip()` on it directly - **Fix:** `str(body.get(...)).strip()` — convert to string first
- `[open]` **Fix 2: Coupon generation still blocking voucher**
- *api, sales-bot* | `id:2496907e`
- > - **Root cause:** Both `step_sale_confirm` (~line 1310) and `launch_session_sale` (~line 1790) used `await asyncio.to_thread(api_post, "coupons/generate", ...)` — BLOCKING - **Fix:** Wrapped in nested
- `[open]` **Fix 3: Old API server on port 5001 (stale code without food-cart endpoints)**
- *api, vps* | `id:2496907f`
- > - **Root cause:** Systemd starts API on port 8000, but old process on port 5001 was still running (started before patch_routes changes) - **Fix:** Killed old PID 1410543 (port 5001)
- `[open]` **Fix 4: Indentation error in coupon fix (first attempt failed)**
- ** | `id:24969080`
- > - **Root cause:** Fix script used 8-space indent but original code used 4-space - **Fix:** Corrected to 4-space indent; sale bot now starts successfully
- `[open]` **Already Fixed (previous session):**
- *sql* | `id:24969081`
- > - Morning Health Summary MySQL query bug (warning line filtered)
- `[fixed]` **✅ Services Restarted**
- *api* | `id:24969082`
- > | Service | Status | |---------|--------|
- `[open]` **🏗️ Finance Fixes — PNL, Balance Sheet & Auto-Depreciation**
- *finance* | `id:24969085`
- `[open]` **Problems Found & Fixed**
- *api, finance, dashboard* | `id:24969086`
- > #### 1. `/api/finance/pnl` — Broken Stub ❌ → ✅ **Broken stub** in `patch_routes.py` L665-720 had:
- `[open]` **Balance Sheet After Fix (June 2026)**
- *api, finance* | `id:24969087`
- > ``` Total Assets:      279,445,881 Ks
- `[open]` **Scripts & Files Created/Modified**
- *dashboard* | `id:24969088`
- > | File | Action | Notes | |------|--------|-------|
- `[open]` **Services Status (June 15, 08:37 UTC)**
- *api, dashboard, sql, customer-bot, timezone* | `id:2496908b`
- `[open]` **🐛 June 15 (PM Session) — PNL Depreciation Fix + Daily Sales Verification**
- *needs-review* | `id:2496908c`
- `[open]` **PNL vs Daily Sales Data — Verification**
- ** | `id:2496908e`
- > Manually verified PNL revenue against raw DB data:
- `[open]` **BS Retained Earnings — Remaining Issue**
- *finance* | `id:2496908f`
- > After the PNL fix:
- `[open]` **🎮 PS VIBE Discord Bot — Deployed (June 15, ~16:55 UTC)**
- *timezone, vps* | `id:24969091`
- > Boss: Osmo (@kingkong00787) က Discord Server လုပ်ချင်တာမို့ Kora က Bot အပြည့်အစုံ ရေးပြီး Deploy လုပ်ပေးခဲ့တယ်။
- `[fixed]` **✅ Completed**
- *console, finance, vps* | `id:24969092`
- > - Bot Application: "PS VIBE Bot" (ID: 1516120408393515081) - 7 Slash Commands Registered: `/balance`, `/games`, `/slots`, `/promo`, `/hours`, `/menu`, `/help`
- `[open]` **⚠️ Pending (Boss Action Needed)**
- *vps* | `id:24969093`
- > 1. **Enable Privileged Intents** in Discord Developer Portal → Bot → Privileged Gateway Intents:    - ✅ Or ❌ Server Members Intent (for welcome DM on new member join)
- `[open]` **Fixes & Updates**
- ** | `id:24969096`
- > 1. **`/hours` fixed**: Was showing wrong hours → corrected to "9:00 AM - 9:00 PM All Days" ✅ 2. **Permanent invite link**: Created never-expire link `https://discord.gg/EXEF7phbZF` ✅
- `[open]` **Bot Status**
- *timezone* | `id:24969098`
- > - **Active** ✅ (systemd service, auto-restart) - **PID**: Last restarted ~18:52 UTC

### LESSON (2)
- `[open]` **5 Lessons Learned (June 15)**
- *sql, dashboard* | `id:24969089`
- > 1. **`%%Y-%%m` pattern doesn't work with `mysql.connector`**: The `_mysql_query` wrapper uses `mysql.connector` which uses `%s` parameter style. `%%` is NOT processed like `printf` — must pass format
- `[open]` **Lesson Learned**
- ** | `id:24969090`
- > 22. **PNL depreciation must filter by purchase_date**: Include only assets that were purchased BEFORE the current month's start. New assets don't accrue depreciation until the month after purchase.

### GENERAL (4)
- `[open [low]]` **📌 Pending**
- *customer-bot* | `id:24969083`
- > - Boss to test Phase 1 Food Cart flow end-to-end - Phase 2 (future): Customer Bot self-ordering
- `[open]` **Discord Bot — Server Setup Completed**
- *console, vps* | `id:24969094`
- > - **Channels Created:** 20 channels across 5 categories (Announcements, General, Game Hub, Events, Voice) - **Roles Created:** Owner, Admin, Moderator, VIP Member, Member
- `[open]` **🎮 Discord Bot — Session Continuation (June 15, ~18:43-19:10 UTC)**
- *needs-review, timezone* | `id:24969095`
- `[open]` **Current Commands — 21 Total**
- ** | `id:24969097`
- > | Public 🌐 | Private 🔒 | |-----------|-----------|

## Memory (2026-06-16)

### BUG (1)
- `[open [low]]` **⚠️ Pending Items**
- ** | `id:2496909f`
- > - `BIRTHDAY_FILE` error and `getLevel` error seen in old process logs (pre-restart) — current process is clean - Some unhandled interaction warnings (non-blocking, cosmetic)

### FIX (4)
- `[fixed]` **✅ New Modules Created (6 files in `/root/psvibe-discord-bot/modules/`)**
- *api, sql, imports, finance* | `id:2496909b`
- > | Module | File | Size | Description | |--------|------|------|-------------|
- `[fixed]` **✅ Core Files Updated**
- *imports, api* | `id:2496909c`
- > - `deploy-commands.js` — 27 → 35 commands (+8 new) - `bot.js` — Imports all modules, routes commands, hooks into events
- `[fixed]` **✅ Commands Deployed + Bot Restarted**
- *vps* | `id:2496909d`
- > - 35 commands registered via `node deploy-commands.js` ✅ - `systemctl restart psvibe-discord-bot` ✅
- `[open]` **🔧 Bot Running Status (20:45 UTC)**
- *timezone* | `id:249690a0`
- > - ✅ PS VIBE Bot — active (pid 147161, 60.5MB mem) - ✅ 35 commands registered

### FEATURE (2)
- `[open]` **🎮 Discord Bot V3 — Full Feature Upgrade (20:00-20:45 UTC)**
- *needs-review, timezone* | `id:2496909a`
- `[open]` **Bot Analytics Tab Added to Kora Dashboard**
- *booking, dashboard, sql* | `id:249690a1`
- > - Tab button + content panel added to `/root/.openclaw/workspace/kora_dashboard/index.html` - 6 stats cards, user segments, top commands, peak hours panels

### GENERAL (1)
- `[open]` **📊 Complete Command List (35 Total)**
- *booking, console, finance* | `id:2496909e`
- > ``` 🎮 Gaming:       /games /slots /promo /rank-tiers /tournament

## Memory (2026-06-17)

### BUG (2)
- `[open [critical]]` **SSH Test**
- *vps* | `id:249690a4`
- > ``` ssh root@5.223.81.16:22 → Connection refused
- `[open]` **Phase 1-3 Full Verification & Bug Fixes (05:00 UTC)**
- *needs-review, timezone* | `id:249690ad`

### FIX (8)
- `[open [critical]]` **🔴 VPS DOWN — 5.223.81.16 SSH Connection Refused**
- *vps, timezone* | `id:249690a2`
- > **Time detected:** 19:31 UTC (02:01 AM Myanmar Time) **Status:** ❌ UNRESOLVED
- `[open]` **Disaster Recovery Backup Failure (5/6 items failed)**
- *api, sql, dashboard, vps* | `id:249690a3`
- > All 5 remote-dependent items failed with `ECONNREFUSED 5.223.81.16:22`: - ❌ MySQL Database
- `[open]` **Services Restarted**
- *api* | `id:249690a8`
- > - `psvibe-discord-bot` ✅ - `psvibe-api` ✅
- *api, dashboard* | `id:249690a9`
- > - `/root/psvibe-discord-bot/bot.js`, `deploy-commands.js`, `suggestions.json` - `/root/psvibe_api_server/app.py`
- `[fixed]` **Phase 3.7 — Waitlist Auto-Notify on Booking Cancel ✅ (04:35 UTC)**
- *booking, timezone, reminder* | `id:249690aa`
- `[open]` **Verification**
- *api, console, booking* | `id:249690ac`
- > - Syntax check: ✅ Both files pass - API restart: ✅ Active
- `[open [critical]]` **Verification Results**
- *needs-review* | `id:249690ae`
- > | ✅ Pass | ၁၂ ချက် | | ⚠️ Partial → Fixed | ၃ ချက် |
- `[open]` **3 Fixes Applied**
- *sql, reminder, console, api, booking* | `id:249690af`
- > - **P3.3 Booking Conflicts SQL:** `time_slot` → `start_time` in SQL query (app.py line 4150) - **P1.1 Index:** Created `idx_date_console_time(booking_date, console_id, start_time)`, dropped old incomp

### DECISION (1)
- `[open]` **Key Design Decisions**
- *booking, customer-bot, console, sql* | `id:249690ab`
- > - Waitlist lives in `console_booking` with `status='Waiting'` (no separate table) - Uses `asyncio.create_task()` fire-and-forget — cancel NEVER fails due to waitlist

### AUDIT (1)
- `[open]` **What Was Done**
- ** | `id:249690a7`
- > #### 1. Discord Bot — Staff Review Commands (`/root/psvibe-discord-bot/bot.js`) Converted the `/suggest` command from a simple input to subcommand-based:

### GENERAL (2)
- `[open]` **Action Taken**
- *memory, reminder* | `id:249690a5`
- > - [ ] Set morning reminder to notify Boss at 8:30 AM Myanmar Time - [ ] Logged in daily memory
- `[open]` **Suggestion System — Full Integration (Discord + Web Dashboard)**
- *dashboard* | `id:249690a6`

## Memory (2026-06-18)

### BUG (3)
- `[open]` **Bug 1: Cancel မရတာ**
- *api, booking* | `id:249690b2`
- > **Root Cause:** `PATCH /api/bookings/{id}/status` (app.py L1400) - `WHERE status='pending'` hardcoded. Confirmed bookings ကို cancel လုပ်ချင်ရင် row affected=0 → "Booking already processed" 409 error.
- `[open [low]]` **Bug 2: Cancel လုပ်ရင် Data "?" ပဲပြတာ**
- *api, sales-bot, booking* | `id:249690b3`
- > **Root Cause:** `_do_cancel_booking()` (booking_flow.py) က PATCH response (`{booking_id, status}` only) ကို display + customer notification အတွက်သုံး → fields အားလုံး ? ဖြစ်.
- `[open]` **Broadcast System Fix + Customer Bot Broadcast (17:22 UTC / 23:52 MMT)**
- *booking, api, customer-bot, timezone* | `id:249690b4`
- > **Request:** Customer Bot ကနေ bot user အားလုံးကို broadcast ပို့လို့ရမလား

### FIX (2)
- `[open]` **Heartbeat Checks (14:37 MMT)**
- *memory, vps, timezone* | `id:249690b0`
- > - Health monitor: overall 53.5 (false positives on path mismatches for AGENTS.md/SOUL.md, VPS unreachable) - Heartbeat routine: 12 tasks OK, 0 pending, 0 stuck
- `[open]` **Cancel Confirmed Booking Fix + Display Data Fix (16:46-16:56 UTC / 23:16-23:26 M**
- *booking, timezone* | `id:249690b1`

## Memory (2026-06-19)

### GENERAL (1)
- `[open]` **Heartbeat Check (13:08 MMT)**
- *memory, vps, timezone* | `id:249690b5`
- > - Health monitor: overall 53.5 (mostly false positives - core files exist, VPS reachable) - Heartbeat routine: 12 tasks OK, 0 pending, 0 stuck

## Memory (2026-06-20)

### BUG (3)
- `[open]` **Bug 4.7: Duplicate Check Falsely Triggers on Rejected Bookings (20:17 UTC)**
- *booking, customer-bot, timezone* | `id:249690b6`
- > - **Issue:** Boss testing duration conflict → "Duplicate Booking Detected!" appears instead of max_dur message - **Root cause:** Boss's Telegram account (tg=6296803251) had BK#707 (rejected, 09:00-10:
- `[open]` **Gateway Restart DNS Failures**
- *api, timezone, customer-bot* | `id:249690b8`
- > - Gateway restarted at 21:06 UTC — DNS resolution failed for all providers - `EAI_AGAIN` errors on api.deepseek.com, generativelanguage.googleapis.com
- `[open [critical]]` **SSH Port 22 Incident — Post-Mortem**
- *vps, console* | `id:249690ba`
- > - June 11: Kora's helper created `/etc/systemd/system/ssh.socket.d/extra-ports.conf` - Resulted in ssh.socket crash → ALL SSH down → VPS inaccessible

### FIX (1)
- `[open]` **Preventive Fixes Applied**
- *docker* | `id:249690b9`
- > - Docker daemon.json — Added fallback DNS (Hetzner 185.12.64.2/.1 + Cloudflare 1.1.1.1) - Agent docker-compose (Nova/CoCo/GayZoeLay) — Added dns section

### AUDIT (1)
- `[open]` **Gateway DNS Prevention + SSH Incident Review (21:06-21:25 UTC)**
- *needs-review, timezone* | `id:249690b7`

## Memory (2026-06-21)

### FIX (3)
- `[open [critical]]` **Remaining 3 items + Fix #4 completed**
- *sql, customer-bot, console, docker, api* | `id:249690bc`
- > | # | Item | Detail | |---|------|--------|
- `[open [critical]]` **Files Modified**
- *api, sales-bot, imports, customer-bot* | `id:249690be`
- > - `/root/psvibe-sales-bot/bot/app.py` — shutdown handler (Fix #4) - `/root/psvibe-sales-bot/customer_bot/main.py` — shutdown handler (Fix #4)
- `[fixed]` **All 12 + 1 Items Complete ✅**
- *needs-review* | `id:249690bf`

### GENERAL (2)
- `[open]` **June 22 — System Improvements Completion (9:30 AM MMT)**
- *needs-review, timezone* | `id:249690bb`
- `[open]` **Files Created**
- *sql, api, docker* | `id:249690bd`
- > - `/root/psvibe_api_server/field_utils.py` — response normalization utility - `/root/psvibe_api_server/staging/schema.sql` — staging DB schema

## Memory (2026-06-22)

### BUG (3)
- `[open [low]]` **What's Missing**
- *api, dashboard, finance* | `id:249690c5`
- > - Dashboard Profit Distribution page (UI only, API ready) - Capital Injection/Ejection bot flows
- `[fixed]` **Profit Distribution Bug Fix — Date Filters Added ✅ (19:05 MMT - 22 Jun 2026)**
- *needs-review, timezone, finance* | `id:249690c6`
- `[open]` **Bug: -12,527,636 Ks net loss showing**
- *dashboard, sql* | `id:249690c7`
- > **Root cause:** `calculate_profit_distribution()` in `dashboard_routes.py` had ZERO date filters on any query — summing ALL data from entire DB history.

### FIX (4)
- `[fixed]` **26. Phase 1 Branch Architecture — Silent Prep ✅ (18:00 MMT)**
- *finance, api, feedback, timezone* | `id:249690c0`
- > **Boss directive:** Current shop → "Sanchaung Branch" (ဆိုင်ခွဲအတွက်ကြိုပြင်)
- `[open]` **Fix Applied (`dashboard_routes.py` lines ~2831-2890):**
- *dashboard, sql* | `id:249690c8`
- > 1. **Added `period` query parameter** — defaults to current month (e.g., `?period=2026-06`) 2. **sales_daily**: Added `WHERE sale_date >= '2026-06-01' AND sale_date <= '2026-06-30'`
- `[open]` **June 2026 Post-Fix Numbers:**
- ** | `id:249690c9`
- > ``` Revenue:    8,163,333 Ks  (454 vouchers)
- `[open]` **Note:**
- *api, dashboard, sub-agent, finance* | `id:249690cb`
- > - Sub-agent failed due to missing OpenAI API key for gpt-4o-mini model. Fix applied directly by Kora. - Dashboard Profit Distribution UI page was already built and deployed (Boss showed screenshot).

### FEATURE (1)
- `[open]` **Findings**
- *api, dashboard, finance* | `id:249690c2`
- > 1. **10% Management Fee → FULLY IMPLEMENTED** in `dashboard_routes.py` (lines ~2868-2920)    - `mgmt_fee = round(net_profit * 0.10, 0)` → Aung Chan Myint

### AUDIT (1)
- `[open]` **Profit Distribution Audit (18:48 MMT - 22 Jun 2026)**
- *needs-review, timezone, finance* | `id:249690c1`
- > Boss asked to verify Profit Distribution system with 10% management fee.

### GENERAL (3)
- `[open]` **Profit Distribution Formula**
- *finance* | `id:249690c3`
- > ``` Net Profit = Total Sales - Opex - COGS - Depreciation - Wallet Liability
- `[open]` **Token Accounts**
- *api* | `id:249690c4`
- > ``` Aung Chan Myint: 34% (102M) + 10% mgmt fee
- `[open]` **Files Modified:**
- *api, dashboard* | `id:249690ca`
- > - `/root/psvibe_api_server/dashboard_routes.py` — `calculate_profit_distribution` function

## Memory (2026-06-23)

### BUG (9)
- `[open]` **2. Code Bug: start-session Checked-In Fix**
- *api* | `id:249690d1`
- > - **Bug:** `start-session` API only queried `status='confirmed'`, missing `checked_in` - **Fix:** Changed to `status IN ('confirmed','checked_in')` in `/root/psvibe_api_server/app.py`
- `[open]` **3. Code Bug: Auto-Checkin Overlap False Positive**
- *booking* | `id:249690d2`
- > - **Bug:** Overlap check caught auto-checkin booking as conflict - **Fix:** Added conditional `if bk:`/`else:` block to skip self-check in overlap logic
- `[open]` **4. Code Bug: Feedback Sent to Admin Group**
- *feedback, console* | `id:249690d3`
- > - **Bug:** Feedback/rating messages sent to Admin Group (chat_id starts with `-`) instead of customers - **Fix:** Added chat_id check in `console.py` lines 31 and 424 — skip when `chat_id.startsWith('
- `[open]` **11. console_mgmt.py — Missing Import Fix**
- *imports, console* | `id:249690dc`
- > - **Bug:** `NameError: name 'fetch_console_status' is not defined` when pressing "🔄 Move Console" - **Root cause:** `console_mgmt.py` relied on module-level `__getattr__` lazy loader but it failed at
- `[open [low]]` **12. End Session — Confirm Step Added**
- *console* | `id:249690dd`
- > - **Issue:** C-05 session ended prematurely (50 min instead of 120 min) — staff accidentally hit End Session - **Fix:** Added inline keyboard confirm step in End Session flow
- `[open]` **Food Order Stock Out Bug (Jun 23 final session)**
- *needs-review* | `id:249690de`
- `[open [low]]` **13. Move Console + End Session — Game Minutes Fix**
- *console, booking* | `id:249690df`
- > - **Bug:** console move လုပ်ပြီး session end ရင် game minutes voucher ထဲ မပါလာ - **Root cause:** `sales.py` line 1787: `if booking_id: game_amt = 0` — booking_id ရှိရင် game_amt zero လုပ်တာ
- `[open [critical]]` **14. 🐛 CRITICAL: Food Cart Stock Out Silent Fail**
- *sql, imports* | `id:249690e0`
- > - **Bug:** Food order items sale voucher ထွက်ပေမယ့် stock out history မှာ မပေါ် - **Root cause:** `patch_routes.py` → `food_cart_release()` function ထဲက `_mc` (MySQL connector) variable က NameError!
- `[open]` **16. Move API start_time Preserved**
- *api* | `id:249690e2`
- > - **Bug:** `POST /api/sessions/move` resetting `start_time` to current time - **Fix:** Changed `_now` → `_bk["start_time"]` in app.py line 2631 — preserves original session start time

### FIX (8)
- `[open [critical]]` **Profit Distribution Fix (Complete from Jun 22)**
- *finance* | `id:249690ce`
- > - Profit Distribution now 100% aligned with Monthly PNL (-7,781,303 Ks for June) - Key fix: PNL-matching logic (same revenue breakdown, stock FIFO for COGS, exclusive depreciation)
- `[open [high]]` **Major System Fixes & Features (Jun 23 Session)**
- *needs-review* | `id:249690cf`
- `[open]` **6. No Timer (duration=0) Session Fixes**
- *timezone* | `id:249690d5`
- > - **Timeline bar:** Extended to NOW instead of 5% fixed width - **Utilization stats:** No Timer sessions count up to NOW for live utilization
- `[open]` **7. Receipt Template Overhaul**
- *finance* | `id:249690d6`
- > - **v1 (Thermal format):** 80mm width, B&W, monospace font, print-optimized (`@page { size: 80mm }`) - PS VIBE logo embedded as base64 (2,648 bytes) — no static file mount needed
- `[open [low]]` **8. Session Reminder System — Complete Fix**
- *reminder, imports, api, customer-bot* | `id:249690d7`
- > #### Type 1: API Timer Scheduling Gap - **Root cause:** Bot's `_remind_loop` only ran in manual sale flow; API `session_timer` skipped sessions with non-empty `telegram_chat_id`
- `[open]` **Additional Fixes (Jun 23 late session)**
- *needs-review* | `id:249690db`
- `[open]` **15. Console Management Menu Layout Fix**
- *imports, console* | `id:249690e1`
- > - **Removed:** `BTN_CHANGE_GAME` button (Boss: "Game ပြောင်းက ဖြုတ်ထားလိုက်ဦးမယ်") - **Removed:** "⚙️ Console စီမံ" submenu from main menu
- `[open]` **Updated Service State**
- *api* | `id:249690e3`
- > | Service | PID | Status | |---------|-----|--------|

### FEATURE (1)
- `[open]` **9. New Feature: Active Session Move API**
- *api, console, booking* | `id:249690d8`
- > - **Endpoint:** `POST /api/sessions/move` - **Payload:** `{ "booking_id": 855, "to_console_id": "C-03" }`

### AUDIT (1)
- `[open [critical]]` **Phase 2 Multi-Branch Audit**
- *api, customer-bot, dashboard* | `id:249690cc`
- > - Full audit of all bots + dashboard + API for multi-branch readiness - **Critical gap found:** `api_client.py` in Sale Bot & Customer Bot don't send `X-Branch-ID` header

### GENERAL (5)
- `[open]` **SSD Name Update**
- *console, sql* | `id:249690cd`
- > - Updated `console_name` in `console_games` table:   - SSD-T1 → "Samsung T1 Shield"
- `[open]` **1. Booking Management**
- *booking* | `id:249690d0`
- > - BK#842: moved to C-09, time 12:15→14:15, then start updated to 12:20 with 180min - BK#836: moved from C-09 to C-10, session Active at 12:00 with 120min
- `[open]` **5. Inventory Reconciliation**
- *needs-review* | `id:249690d4`
- > - 5 items had mismatches between DB and Google Sheets - All 44 items now fully synchronized
- `[open]` **10. Session Timer Status (as of session end)**
- *booking, console, timezone* | `id:249690d9`
- > | Booking | Console | End (MMT) | Timer | |---------|---------|-----------|-------|
- `[open]` **Key Technical Notes**
- *sql, reminder, docker, sales-bot, dashboard* | `id:249690da`
- > - **Server:** VPS `5.223.81.16`, SSH key `/root/.ssh/id_boss` - **API server:** `/root/psvibe_api_server/`, service: `psvibe-api`

## Memory (2026-06-24)

### BUG (5)
- `[open]` **Receipt Template Print Clarity Fix**
- *api* | `id:249690e4`
- > - **Issue:** Receipt HTML font too small (11px) — print output blurry/unclear - **File:** `/root/psvibe_api_server/receipt_template.html`
- `[open]` **🐛 Bug Fix: Session End — Game Minutes Missing When Food Orders Present**
- *needs-review* | `id:249690e5`
- *console, api* | `id:249690e6`
- > `cmd_session_food_order()` in `sales.py` sets `session_food_order: True` and `is_food_sale: True` in context. When staff later ends the session via `step_end_confirm()` in `console.py`, `launch_sessio
- `[open]` **Balance Sheet Imbalance (102.65M gap)**
- *dashboard, finance* | `id:249690ea`
- > **Root Cause:** Settled advance recovery inject (102.5M) is in KBZ Bank cash balance but NOT reflected in retained earnings. The retained earnings formula only uses `sales_daily net + wallet_consumed
- `[open [low]]` **Cash Flow Reconciliation**
- *finance* | `id:249690eb`
- > **Root Cause:** `net_change = net_op + net_inv` didn't include internal account transfers (transfer_in/transfer_out). The closing balance (`total_bal` from per-account loop) WAS correct, but displayed

### FIX (4)
- `[open]` **Fix Applied (2 locations)**
- *sales-bot, console* | `id:249690e7`
- > 1. **`/root/psvibe-sales-bot/bot/handlers/sales.py`** — `launch_session_sale()`: Clear `session_food_order`, `is_food_sale`, `last_food` before `context.user_data.update()` 2. **`/root/psvibe-sales-bo
- `[open [low]]` **🧮 Balance Sheet & Cash Flow Fixes**
- *needs-review, finance* | `id:249690e9`
- `[open [low]]` **Files Modified**
- *api, dashboard, finance* | `id:249690ec`
- > - `/root/psvibe_api_server/dashboard_routes.py` — balance sheet retained earnings + auto-balancer + cash flow net_change - `/root/psvibe_api_server/patch_routes.py` — same balance sheet fixes
- `[open [low]]` **Key Numbers (Post-Fix)**
- *api* | `id:249690ed`

### GENERAL (1)
- *needs-review, vps* | `id:249690e8`
- > - `psvibe-sale-bot` (systemctl)

## Memory (2026-06-25)

### BUG (10)
- `[open]` **Summary**
- *sql, dashboard, customer-bot, booking* | `id:249690ee`
- > Multi-project session: ACM Wallet MySQL migration completed, PS VIBE dashboard staff permission, customer bot booking bug fix.
- `[open]` **Changes**
- *dashboard* | `id:249690f4`
- > | File | Change | |------|--------|
- `[open [low]]` **Bug**
- *booking* | `id:249690f7`
- > Customer Booking flow: "Member Card ရှိတယ်" → ဖုန်းနောက်ဆုံး ၃ လုံးရိုက် → **member ရှာမတွေ့**
- *sql, customer-bot, api* | `id:249690f8`
- > After MySQL migration, `api_fetch_members` endpoint now returns **full member objects** (`[{id, name, phone, ...}]`) instead of **flat ID list** (`["PSV-001", ...]`). Customer Bot's `_fetch_members()`
- `[open [low]]` **Investigation Result**
- *api, console, booking* | `id:24969109`
- > Staff Booking flow on C-03 → `step_book_checkin_bind` called **`POST /api/update_booking`** (endpoint doesn't exist → HTTP 405). But `_api_call_async` catches HTTPError and returns dict instead of rai
- `[fixed]` **9. C05 Bug Fix — Booking Creation Overwrites Active Console ✅**
- *api, console, booking* | `id:2496910f`
- > - **Root cause:** `POST /api/bookings` had direct `UPDATE console_status SET status='Reserved'` bypassing `_sync_console_status()` - **Fix:** Removed direct UPDATE inside transaction; added `_sync_con
- `[open]` **DB Changes**
- *sql* | `id:24969115`
- > - `payments` table already had `from_account_id` and `to_account_id` columns - Cleaned up 2 test payment accounts
- `[open]` **Section 18: SEL Exchange — Payment & PNL Overhaul (17:00-17:56)**
- *needs-review* | `id:2496911d`
- `[open [critical]]` **Payment Breakdown — Account Reset Bug Fixed**
- ** | `id:2496911f`
- > - **Bug:** `loadAcctsIntoPaySelects()` used `.innerHTML = opts` on ALL `.pay-acct` selects, wiping previous selections - **Fix:** Save current selections before rebuild, restore after
- *dashboard* | `id:24969125`
- > - `/opt/kora-projects/sel_exchange/code/db.py` — FIFO PNL, charges separation, position with effective rate - `/opt/kora-projects/sel_exchange/dashboard/index.html` — Payment line refactor, R/P multi-

### FIX (24)
- `[fixed]` **1. ACM Wallet — MySQL Migration Complete ✅**
- *sql* | `id:249690ef`
- `[open]` **Phase 1-3 Done**
- *sql* | `id:249690f0`
- > - Database `acm_wallet` created with 7 tables - Data migrated: 147 transactions, 44 opening balances, 56 settings
- `[fixed]` **2. PS VIBE Web — Staff Role → Members Tab Permission ✅**
- *needs-review* | `id:249690f3`
- `[fixed]` **3. 🐛 Customer Bot — Phone Last-3-Digits Member Lookup Fix ✅**
- *customer-bot* | `id:249690f6`
- `[open]` **Fix (2 files)**
- *booking, api, customer-bot, finance* | `id:249690f9`
- > | File | Change | |------|--------|
- `[fixed]` **4. PS VIBE — Data Digest System ✅**
- *timezone* | `id:249690fb`
- > - `digest_engine.py` + `digest_routes.py` + `digest_cron.sh` built - Registered in app.py, daily cron at midnight MMT
- `[open]` **Key Files Modified**
- *booking, customer-bot, sales-bot, sql, dashboard* | `id:249690fc`
- > | File | What | |------|------|
- `[fixed [low]]` **Verdict: Manual End — NOT Auto-End ✅**
- *booking, console, timezone* | `id:249690ff`
- > Sale Bot logs confirm full manual end-session flow ran: - `08:45:32 UTC` (15:15 MMT): `end_booking` called via Console Management → Session End
- `[open]` **6. 🐛 C05 — Booking Creation Overwrites Active Console Status ⚠️ (NOT YET FIXED)**
- *console, booking* | `id:24969101`
- `[open]` **Fix Plan**
- *console, booking* | `id:24969104`
- > Replace direct `UPDATE console_status SET status='Reserved'` with `_sync_console_status(console_id)` which properly checks for Active bookings first: 1. Active booking found → keep Active ✅
- `[fixed]` **7. SEL Currency Exchange — Project Built ✅**
- *api, sql, finance, customer-bot* | `id:24969106`
- > - Full project under `/opt/kora-projects/sel_exchange/code/` - SQLite DB, FastAPI (port 8001), Telegram bot with raw HTTP polling
- `[fixed]` **8. Booking #974 Disappearance — Root Cause & Fixes ✅ (17:00 MMT)**
- *booking, timezone* | `id:24969108`
- `[open]` **Fix 1: Dead API Endpoint (HTTP 405)**
- *api, sales-bot, console, booking* | `id:2496910a`
- > - **File:** `/root/psvibe-sales-bot/bot/handlers/booking.py` line 1213 - **Before:** `_psvibe_post_async("update_booking", {"id": bk_id, "status": "Active", "console_id": cid})`
- `[open]` **Fix 2: _sync_console_status — NOW() (UTC) → now_mmt()**
- *api, console, sql, timezone, vps* | `id:2496910b`
- > - **File:** `/root/psvibe_api_server/app.py` lines 96-158 - **Before:** SQL used `NOW()` (MySQL server UTC) to compare against `start_time` (stored as MMT) → ~6.5hr mismatch
- `[open]` **Fix 3: Booking → Active: start_time NOW() → MMT**
- *booking, api, timezone* | `id:2496910c`
- > - **File:** `/root/psvibe_api_server/app.py` line 1623 - **Before:** `start_time=NOW()` in `PATCH /api/bookings/{id}/status` when status→Active
- `[open]` **Fix 4-5: Dashboard Edit Booking — Template v() Removal**
- *api, dashboard, booking* | `id:2496910e`
- > - **File:** `/root/psvibe_api_server/dashboard-dist/assets/BookingsManagement-BbqxMmPA.js` - **Fix 4:** `,if(o.value.booking_date...` → `,o.value.booking_date...` (stray `if` after removing `v()){` wr
- `[fixed]` **10. Booking Confirm + Console Change Overlap Fix ✅**
- *api, console, booking* | `id:24969110`
- > - `PATCH /api/bookings/{booking_id}/status` overlap check was using old `_bk["console_id"]` instead of requested `consoleId` - Fixed to check against requested console ID
- `[fixed]` **12. Staff Role — Sale Daily Summary Hide ✅**
- *sql* | `id:24969112`
- > - `SaleDaily-DwsI1xIx.js`: After data fetch, checks `localStorage` user role → if `staff`, sets summary to null - Summary cards hidden for staff; records table still visible
- `[fixed [low]]` **13. Sale Bot Access ✅**
- *sql, customer-bot* | `id:24969113`
- > - Added Telegram user ID `7421933787` to `allowed_staff_ids` in MySQL `settings_config` - Bot restarted → PID 2304716
- `[fixed]` **14. SEL Exchange — Account ↔ Payment Binding ✅**
- *needs-review* | `id:24969114`
- `[fixed]` **15. SEL Exchange — Contact Type (Supplier/Customer) ✅**
- *needs-review* | `id:24969118`
- `[fixed]` **16. SEL Exchange — Dashboard Full Rebuild ✅**
- *api, dashboard* | `id:2496911a`
- > - Previous dashboard was corrupted by string escaping errors - Restored from backup and rebuilt cleanly
- `[fixed]` **17. SEL Exchange — API Key + Account Setup ✅**
- *api* | `id:2496911b`
- > - Fixed `.env`: literal `API_KEY=***` → `API_KEY=sel-exchange-2026` - Created 4 payment accounts: Cash MMK (#1), Cash THB (#2), Bank MMK (#3), Bank THB (#4)
- *api* | `id:2496911c`

### LESSON (2)
- `[open]` **Lessons Learned**
- *api, console, booking* | `id:24969107`
- > - **#26: API format changes after migration** — When API returns different format, check ALL consumers - **#27: Minified JS edits** — Use Python string replace for precision, not sed; always backup fi
- `[open]` **Key Lessons**
- ** | `id:24969124`
- > 32. **FIFO requires correct chronological order** — use `ORDER BY tx_date ASC, created_at ASC, id ASC` 33. **Charges are bank fees, not supplier payments** — exclude from `paid_amount` but include in

### FEATURE (9)
- `[open]` **Post-Migration Cleanup**
- *sql* | `id:249690f1`
- > - gspread + google-auth removed from requirements.txt - `_SHEETS_TIMEOUT` → `_DB_TIMEOUT` renamed
- `[open]` **Root Cause Found — `POST /api/bookings` at app.py line ~2845**
- *api, console, booking* | `id:24969102`
- > When a new CONFIRMED booking starts within 60 minutes, the endpoint **directly overwrites** `console_status` to `Reserved` WITHOUT checking if there's an Active session:
- `[open]` **New Lessons**
- *api, sql, timezone, dashboard* | `id:2496910d`
- > - **#29: HTTP error handling asymmetry** — `_api_call_async` returns error dict for 4xx (no exception) but `_psvibe_post_async` catches Exception → callers never know API failed. Check if response has
- `[fixed]` **11. Dashboard Edit Booking Time Feature (#51) ✅**
- *dashboard, booking* | `id:24969111`
- > - Frontend: Removed `v()){` condition from save — all bookings now editable - Backend: Added auto `end_time` calculation when `start_time` or `duration` changes
- `[open [critical]]` **Web Dashboard**
- *dashboard* | `id:24969116`
- > - Payment form: Added Account dropdown (fetched via `GET /payment-accounts`) - Payment posts include `from_account_id`
- `[open]` **API**
- *api* | `id:24969119`
- > - `CounterpartyCreate` Pydantic model: Added `cp_type` field - `db.py` `counterparty_create()`: Accepts and stores `cp_type`
- `[open]` **Payment Line Type Removed**
- *sql* | `id:2496911e`
- > - Removed Type (Debit/Credit) column from buy/sell payment lines - All payments now auto-debit
- `[open [critical]]` **R/P Record Payment — Multi-Line Payment Breakdown**
- *api, finance* | `id:24969120`
- > - Converted R/P modal from single form to multi-line payment breakdown - New layout: Account | Amount | Charges per line, + Add Line button
- `[open]` **PNL — FIFO Implementation**
- ** | `id:24969122`
- > - **Before:** Average buy rate × realized THB → inaccurate - **After:** Full FIFO (First In, First Out) matching

### AUDIT (1)
- `[open]` **Affected Code**
- *api, customer-bot, booking* | `id:24969105`
- > - `/root/psvibe_api_server/app.py`, line ~2845 (`POST /api/bookings`, customer bot booking creation) - Same pattern may exist in staff booking creation path — need to audit

### GENERAL (13)
- `[open]` **Key Files**
- *memory* | `id:249690f2`
- > - `/root/ACM-Personal-Wallet/bot/main.py` (5,197 lines) - `/root/ACM-Personal-Wallet/bot/db.py` (437 lines)
- `[open]` **Result**
- *dashboard* | `id:249690f5`
- > Staff role can now see and access Members tab in web dashboard.
- `[open]` **Bonus**
- *api* | `id:249690fa`
- > Member fetch speed improved: 1 API call instead of 1 list + 7 detail calls.
- `[verified]` **5. 🔍 C06 — "Session End မနှိပ်ဘဲ Free" Investigation**
- *needs-review* | `id:249690fd`
- `[open]` **Boss Report**
- *console* | `id:249690fe`
- > C-06 console became Free without staff pressing "End Session" button.
- `[open [low]]` **Evidence**
- *api, reminder, booking* | `id:24969100`
- > - `session_timer.py`: Only sends reminders, does NOT auto-end - `booking_flow.py _remind_loop`: Text explicitly says "Session auto-end မဖြစ်ပါ"
- `[open]` **Timeline**
- *booking, timezone* | `id:24969103`
- > | Time (MMT) | Event | |------------|-------|
- `[open]` **Bot**
- *api* | `id:24969117`
- > - After payment amount: Shows account list, asks for Account ID - Payment includes `from_account_id` in API call
- `[open]` **Charges Separated from Payment**
- *api, finance* | `id:24969121`
- > - `paid_amount` = SUM(amount) only (NOT including charges) - Transfer charges are bank fees, not payment toward supplier/customer
- `[open]` **PNL Result (June 2026, current data)**
- ** | `id:24969123`
- > - Buy#1: 10,000B @ 125.00 + 300 chg = 125.03/B (FIRST buy) - Buy#2: 20,000B @ 122.00 + 0 chg = 122.00/B (SECOND buy)
- `[open]` **Section 19: SEL — Charges Only for Outgoing (18:00-18:08)**
- *needs-review* | `id:24969126`
- `[open]` **Charges = Buy/Payable Only**
- ** | `id:24969127`
- > - Sell = income (customer pays us) → no bank charges - Buy = outgoing (we pay supplier) → bank charges apply
- `[open]` **PNL Result (corrected, no sell charges)**
- ** | `id:24969128`

## Memory (2026-06-26)

### BUG (4)
- `[open]` **Bugs Found (2)**
- *sql, finance, api, console* | `id:2496912b`
- > **Bug #1 — Month Filter Not Applied:** - `year` and `month` params accepted but never used in any SQL query
- `[open [low]]` **Status**
- *api, dashboard* | `id:2496912c`
- > - Awaiting Boss confirmation to fix both bugs - Cashflow endpoint path: `/root/psvibe_api_server/dashboard_routes.py` line 2674-2835
- `[open]` **Boss Multi-Requests**
- *booking, api, sql, timezone* | `id:2496912e`
- > 1. **C-04 Food Orders web မှာ မပေါ်** — API returns data but frontend sorting bug hides it 2. **Session Food Orders time format မှား** — UTC instead of MMT
- `[open]` **Timeline Lane Stacking v2 — REJECTED by Boss**
- *feedback, booking* | `id:24969134`
- > **Problem with v1:** Stacked blocks too small to read (14px each for 3 overlapping bookings)

### FIX (3)
- `[open]` **Fixes Applied**
- *console, api, timezone, dashboard, sql* | `id:2496912f`
- > #### 1. Food Orders Timezone (Dashboard Routes) - `dashboard_routes.py` food-orders endpoint: Added `CONVERT_TZ(created_at, '+00:00', '+06:30')` for `created_at`, `fulfilled_at`, `start_time` → MMT
- `[open]` **Timeline — Final Version: Popup Approach**
- *dashboard* | `id:24969135`
- > #### 1. Reverted to Original Layout - `git restore` `TimelineView.vue` — removed all lane stacking code
- `[open]` **Build Output (v2 — Final)**
- *api, dashboard, vps* | `id:24969136`
- > - Timeline: `TimelineView-DavfNzpo.js` - Index: `index-C3XMjgqb.js`

### LESSON (2)
- `[open]` **Key Lessons Learned**
- *dashboard* | `id:24969130`
- > **#28: Never edit minified Vue build output directly** — Always edit the source `.vue` files and rebuild. Single-character name conflicts can break the entire component. The project is at `/root/psvib
- `[open]` **New Lessons Learned**
- *dashboard* | `id:24969137`
- > **#31: Lane stacking is wrong UX for this use case** — Boss prefers natural overlap + tap-to-select popup. Don't force lane splitting; it makes blocks too small regardless of dynamic height adjustment

### FEATURE (2)
- `[open]` **Build Output**
- *memory* | `id:24969132`
- > - Timeline: `TimelineView-B20y_Ri9.js` - FoodOrders: `FoodOrders-CkMvAyQJ.js`
- `[open]` **Build Output (v1)**
- ** | `id:24969133`

### AUDIT (1)
- `[open [low]]` **Investigation**
- *api, dashboard, finance* | `id:2496912a`
- > - Checked `/api/dashboard/financial/cashflow` endpoint (dashboard_routes.py line 2674) - Endpoint returns data ok — closing balance ~81.9M (not zero)

### GENERAL (3)
- `[open [low]]` **Boss Request**
- *needs-review* | `id:24969129`
- > Web cashflow summary data တွေက 0 တွေ ဖြစ်နေတယ် — check
- `[open [low]]` **Files Read**
- *api, finance, memory, dashboard* | `id:2496912d`
- > - `/root/psvibe_api_server/dashboard_routes.py` (cashflow endpoint, lines 2674-2844+) - `/root/psvibe_api_server/dashboard_routes.py` (finance/balances endpoint, lines 2114-2194)
- *api, dashboard, sql* | `id:24969131`
- > - `/root/psvibe-dashboard/src/views/TimelineView.vue` — lane stacking + mobile targets - `/root/psvibe-dashboard/src/views/FoodOrders.vue` — sort Active first + recency

## Memory (2026-06-27)

### BUG (4)
- `[open [low]]` **DB Schema Changes**
- *sql* | `id:2496913b`
- > - `staff_records.food_charges` → renamed to **`food_allowance`** (changed from deduction to addition) - `staff_records.attendance_bonus` → updated to **50,000** for all staff
- `[open [critical]]` **Frontend Changes (`StaffSalary.vue`)**
- *sql, dashboard* | `id:24969141`
- > 1. **Auto-Generate Payroll** panel — updated formula description 2. **Leave Management** panel — "+ Record Leave" with staff dropdown, date picker, reason; leave table with ✕ delete
- `[open [critical]]` **Backend Changes (`dashboard_routes.py`)**
- *dashboard, sql, finance* | `id:24969142`
- > - `POST /salary/generate` — full rewrite: shop-wide food profit (FIFO COGS), leave policy, game bonus tiers - `POST /salary` — simplified: looks up auto-generated net_salary, records payment
- `[open [high]]` **Files Modified**
- *api, dashboard* | `id:24969145`
- > - `/root/psvibe_api_server/dashboard_routes.py` — major changes to salary sections - `/root/psvibe-dashboard/src/views/StaffSalary.vue` — full rebuild with leave + simplified forms

### LESSON (1)
- ** | `id:24969139`
- > Boss requested complete staff salary system: leave tracking, payroll auto-generation, food commission, game bonus, attendance rules, and email notifications to staff.

### FEATURE (3)
- `[open]` **New DB Tables**
- *needs-review* | `id:2496913a`
- > - **`staff_leave`**: staff_id, leave_date, reason, created_at — tracks leave days per staff
- `[open]` **New API Endpoints (`dashboard_routes.py`)**
- *api, dashboard* | `id:2496913c`
- > | Endpoint | Method | Purpose | |----------|--------|---------|
- `[open [low]]` **New Lessons**
- *finance* | `id:24969146`
- > - **#47: Leave penalty is binary + tiered**: attendance bonus forfeited on ANY leave; >2d adds 15K/extra day penalty - **#48: Food profit = PNL-style**: existing PNL already has correct food profit ca

### GENERAL (7)
- `[open]` **Staff Salary System — Full Overhaul (16:45-19:00 UTC / 23:15-01:30 MMT)**
- *needs-review, timezone* | `id:24969138`
- `[open [low]]` **Salary Formula (Final)**
- *finance* | `id:2496913d`
- > ``` Net Pay = Basic Salary
- `[open]` **Leave Policy**
- ** | `id:2496913e`
- > | Leave Days | Attendance Bonus | Penalty | |-----------|-----------------|---------|
- `[open]` **Food Commission — Shop-Wide**
- *finance* | `id:2496913f`
- > - **Revenue** = `SUM(total) FROM stock_out` (actual items sold) - **COGS** = `stock_fifo.calc_fifo()` (FIFO inventory cost)
- `[open [high]]` **Game Bonus — Shop-Wide Tiers**
- ** | `id:24969140`
- > | Shop Play Hours | Bonus | |----------------|-------|
- `[open]` **Email Notifications**
- *api* | `id:24969143`
- > - Sent salary structure explanation to Eaindray & Min Myat Naing via Gmail API - Gmail OAuth token refreshed (was expired, re-authorized with gmail.send + gmail.readonly scopes)
- `[open]` **Test Data**
- *finance* | `id:24969144`
- > - 3 staff: Ko Khant, Eaindray, Min Myat Naing - Eaindray: 3 leave days (June 12, 16, 22)

## Memory (2026-06-28)

### BUG (6)
- `[open [critical]]` **Actions Taken**
- *memory, vps, sql* | `id:24969148`
- > #### MEMORY.md Updates - Updated project count: 8 → 9 (added `sel_exchange`)
- `[open [medium]]` **Current Known Issues**
- *vps* | `id:24969149`
- > | Issue | Severity | Status | |-------|----------|--------|
- `[open]` **Investigation**
- *timezone* | `id:2496914d`
- > Found 2 notification sources sending directly to Boss (6296803251):
- `[open [critical]]` **Root Cause**
- ** | `id:24969150`
- > Same Markdown underscore bug in 2 more places. Food item `လျှာဂျွမ်းထိုး_ဟော့ဟော့` had `_` interpreted as Markdown italic, breaking `parse_mode="Markdown"`: 1. `_show_payment_review()` line 1220 — Rev
- `[open [low]]` **Boss Follow-up: Admin contact → @psvibeofficial**
- *needs-review* | `id:24969154`
- > Changed all block messages from `@kingkong00787` → `@psvibeofficial` (4 locations total)
- `[open]` **Boss Request 2: Payment methods wrong**
- *needs-review* | `id:2496915c`
- > "Payment methods ကမှားနေသလိုပဲ့"

### FIX (6)
- *sales-bot* | `id:2496914e`
- > **1. Inventory Alerts** (`/opt/inventory_alerts/inventory_alerts.js`): - `runDailySummary()`: `alertBoss(msg)` → `alertStaff(msg)`
- `[open]` **Fix Applied**
- *sql* | `id:2496914f`
- > **`/root/.openclaw/workspace/biz_intel.js`**: - All 4 SQL queries: `CURDATE()` → `CURDATE() - INTERVAL 1 DAY`
- `[open]` **Boss Request 2: EOD Report fix — data all zeros + change time to 10 PM**
- *needs-review, timezone* | `id:24969155`
- > "PS VIBE Admin ထဲ ပို့တဲ့ report က data မှားနေတယ် 8pm MMT အစား 10pm နဲ့ ပြောင်းပေးပါ"
- `[open]` **Fix Applied (Complete Rewrite)**
- *sql, sales-bot, docker* | `id:24969156`
- > **`/root/psvibe-sales-bot/scripts/eod_report.py`**: - Replaced `docker exec mysql` with `pymysql` direct connect
- *api, customer-bot* | `id:24969159`
- > - `psvibe-sale-bot` ✅ - `psvibe-customer-bot` ✅
- *sql* | `id:2496915d`
- > - Query: `GROUP BY SUBSTRING_INDEX(payment_method, ':', 1)` → extracts method name - Also fixed: `members` table → `member_wallets` table (1 vs 8 records)

### LESSON (1)
- `[open]` **Lesson**
- ** | `id:2496914c`
- > - ALWAYS mirror existing templates when sending repeating emails. Boss noticed the format mismatch immediately.

### FEATURE (2)
- `[open]` **Implementation**
- *sales-bot, customer-bot* | `id:24969153`
- > **`/root/psvibe-sales-bot/customer_bot/main.py`**: - Added `BLOCKED_IDS` set + `BlockedUsersFilter` class
- `[open]` **Docs Update**
- *memory* | `id:2496915e`
- > - MEMORY.md: Added session summary + 5 new lessons (#51-#55) - Daily memory: This section appended

### GENERAL (9)
- `[open]` **Boss Request**
- *needs-review* | `id:24969147`
- > "Docs update တွေလုပ်ပါ" — comprehensive documentation refresh
- *memory* | `id:2496914a`
- > - `/root/.openclaw/workspace/MEMORY.md` — major update - `/root/.openclaw/workspace/memory/2026-06-28.md` — created
- `[open [low]]` **Actions**
- *sql* | `id:2496914b`
- > - Updated staff_records.email for Ko Khant in MySQL - Re-sent salary structure email using correct format (matching Eaindray & Min Myat Naing template)
- `[open [low]]` **Boss Follow-up: Web dashboard booking confirm/cancel noti not arriving**
- *dashboard, booking* | `id:24969151`
- > "Web က နေ booking confirm / cancel က noti မရောက်တော့ ပြန်ဘူး — Code တွေ က ဖျက်မိနေတာလား"
- `[open]` **Boss Request 1: Block BK#1121 & BK#1122 customers**
- *customer-bot* | `id:24969152`
- > Block telegram IDs `7158675982` (Unoman66) and `8383666570` (Phone 09691339153) from customer bot.
- `[open]` **Cron Update**
- *needs-review, timezone* | `id:24969157`
- > ``` Before: 30 13 * * *  (8:00 PM MMT)
- `[open]` **Test Results**
- *console* | `id:24969158`
- > - Script ran manually, sent to Admin Group successfully - Data: 42 txns, 7.0 သိန်း, 3/10 consoles active, 2 members
- `[open]` **Boss Request 1: English language only**
- *needs-review* | `id:2496915a`
- > "Eng Language နဲ့ပဲ့ ပြန်ပြင်ရေးပေးလိုက်ပါ"
- `[open]` **Action**
- ** | `id:2496915b`
- > Converted entire Burmese report block to English: - Title: "ယနေ့ အရောင်းအစီရင်ခံစာ" → "Daily Sales Report"

## Memory (2026-06-29)

### BUG (16)
- `[open]` **Bug Fixes During Build**
- *api, sql, dashboard* | `id:24969164`
- > - **Sidebar disappearing:** `AppLayout` wrapper was missing in `CustomerBotSuccess.vue` — fixed - **Auth mismatch:** Vue was using `useAuthStore` apiKey → switched to `apiClient` with JWT Bearer
- *timezone, sql, vps* | `id:2496916b`
- > MySQL server timezone is SYSTEM=UTC. All `NOW()`, `CURRENT_TIMESTAMP` return UTC.
- `[open [critical]]` **Critical Bug Fix: Payment Method Parsing**
- *sql* | `id:24969175`
- > - **Bug:** SQL `WHERE payment_method = 'Cash'` never matched because column stores `Cash:10000` or `KPay:0|Cash:10000` (pipe-separated split payments) - **Fix:** Fetch all sales_daily rows, parse `pay
- `[open [critical]]` **Payment Method Parsing Bug (CRITICAL)**
- *sql* | `id:2496917c`
- > - **Bug:** `payment_method = 'Cash'` exact match never found because column stores `Cash:10000`, `KPay:31000|Cash:20000|WavePay:17000` - **Fix:** Fetch all rows, parse in Python: split by `|` for mult
- `[open]` **Cash Movement Integration**
- *sql* | `id:2496917d`
- > - Sources: `cash_movements` table (eject, transfer_out, transfer_in, inject) - **transfer_out amounts are NEGATIVE** in DB — must use `ABS(amount)` in SQL queries
- `[open]` **API: `GET /api/dashboard/reconciliation?date=YYYY-MM-DD`**
- *api, console, dashboard* | `id:24969182`
- > - Matches Done sessions ↔ sales_daily by console_id + date + time proximity - Returns: matched_pairs, missing_sales, orphan_sales, all_matched
- `[open [low]]` **Vue Page: ReconciliationView.vue at `/reconciliation`**
- *booking, console, sql, dashboard* | `id:24969183`
- > - 3 summary cards: Done Sessions, Sales Records, Matched - Missing Sales section (red): booking_id, console, time, mins, staff, amount
- `[open]` **Root Cause: Two Separate Handler Files**
- *customer-bot* | `id:24969187`
- > - Sale Bot: `bot/handlers/games.py` → `_build_game_list_text()` / `show_game_menu()` - **Customer Bot:** `customer_bot/handlers.py` → `cmd_game_library()` (line 565)
- `[open]` **UTC→MMT Timestamp Migration — food_cart & sales_daily**
- *dashboard, sql, timezone* | `id:2496918a`
- > - food_cart: `created_at` + `updated_at` migrated (+390 min to existing rows) - sales_daily: `sale_time` column changed from TIMESTAMP to DATETIME (to prevent auto-UTC conversion)
- `[open]` **Double Set (Overlap) Investigation**
- *console* | `id:2496918c`
- > - C-06: #1137 (15:30-16:29, 57min) ↔ #1141 (15:42-16:49, 59min) — **47min overlap** - C-09: #954 (13:47-14:46, 51min) ↔ #1127 (12:22-14:11, 36min) — **24min overlap**
- `[open [low]]` **Restaurant Sales Access for Staff**
- *api, dashboard* | `id:2496918e`
- > - `staffOnlyPaths` in AppLayout.vue: added `/till`, `/reconciliation`, `/members` - Router meta: changed `role: "admin"` → `roles: ["admin", "staff"]` for till, reconciliation, members routes
- `[open [high]]` **SEL Currency Exchange — Major Bug Fixes & Feature Improvements (17:40 - 19:00 UT**
- *needs-review, timezone* | `id:24969190`
- `[open]` **Context: Boss switched to SEL Exchange project for the evening session**
- *needs-review* | `id:24969191`
- `[open]` **4. SE KBZ Balance Bug — Root Cause Analysis & Fix**
- *api, finance* | `id:24969195`
- > - **Timeline:**   - Jun 27: Boss set opening balance 52,146,456 (API `PATCH /api/accounts/6/balance`)
- `[open]` **6. PATCH Balance Update (Account Balance Fix)**
- *finance* | `id:24969197`
- > - **Bug:** Editing a payment's account didn't update account balances - **Fix:** Added reversal logic in `update_payment`:
- `[open]` **7. Edit Form — Preserve Unedited Account Field**
- ** | `id:24969198`
- > - **Bug:** New single-account edit form only sent the relevant field, clearing the other to NULL - **Fix:** `submitPayEdit` now always sends BOTH `from_account_id` and `to_account_id`:

### FIX (13)
- `[open]` **Key Dates Discovered**
- *customer-bot, booking* | `id:24969162`
- > - **June 6, 2026:** First Customer Bot booking (Ko Pyae, C-09, cancelled) - **June 13, 2026:** First Done booking (phone 09764375834, C-03, 90min)
- `[open [low]]` **Health Monitor Fix (00:05 - 01:06 UTC)**
- *memory, timezone* | `id:24969167`
- > - **Root Cause:** `kora_health_monitor.py` hardcoded workspace path as `/home/node/.openclaw/workspace` but actual workspace is `/root/.openclaw/workspace/` - **Fix:** Changed 3 occurrences of workspa
- `[open]` **Timezone Crisis — UTC → MMT Fix (08:12 - 08:36 UTC)**
- *timezone* | `id:2496916a`
- *api, console, sql, timezone* | `id:2496916d`
- > | Table | Column | Fix | |-------|--------|-----|
- `[open]` **Reminder Button Fix**
- *reminder* | `id:2496916e`
- > - Removed "✅ ပြီးပြီ (End မည်)" button from reminder keyboard - Replaced with "⏹️ Sale Bot → Session End" (doesn't end session, redirects staff)
- `[open]` **June 29 Cross-Check Results**
- ** | `id:24969171`
- > | Sessions | Vouchers | ✅ Matched | ❌ Missing | ❌ Orphan | |----------|----------|-----------|-----------|----------|
- `[open [critical]]` **File Changes Today**
- *dashboard, api* | `id:24969184`
- *customer-bot* | `id:24969188`
- > - Rewrote `cmd_game_library()` in `customer_bot/handlers.py` - Added ✅ Installed / 📀 Disc Available / ⚪ Other status grouping
- `[open]` **Customer Feedback Time Fix**
- *api, timezone, feedback, dashboard* | `id:2496918b`
- > - DB: `customer_feedback.created_at` existing rows +390 min, DEFAULT updated to MMT NOW() - Vue: `FeedbackView.vue` — both `fmtDate()` and `formatDay()` had double timezone conversion
- `[open]` **1. THB Account Display in Transactions**
- *api, dashboard, sql* | `id:24969192`
- > - **Problem:** Recent transactions didn't show which THB account received/sent the baht - **Fix:** Added `thb_account_name` JOIN to `db.py tx_list()` and `app.py GET /api/transactions/{id}`
- `[open]` **2. Payment History — Display & Edit Fixes**
- *sql* | `id:24969193`
- > - **Problem:** Table showed both `from_account` and `to_account` columns when only one is relevant, and `payment_type` was not displayed - **Fix:** Merged From/To into single "Account" column with con
- `[open]` **3. Tab State Persistence**
- ** | `id:24969194`
- > - **Problem:** Page reload always returned to Overview tab - **Fix:** `switchTab()` saves current tab to `localStorage`, initial load reads from there
- `[open]` **5. All Account Field Routing Fixed (4 locations)**
- *dashboard* | `id:24969196`
- > | Location | Before | After | |----------|--------|-------|

### LESSON (7)
- *api, dashboard, console, booking* | `id:24969166`
- > - **#56: API endpoint needs AppLayout wrapper** — Vue pages rendered via router-view don't auto-inherit sidebar; must wrap in `<AppLayout>` component - **#57: Dashboard uses JWT not x-api-key** — Dash
- `[open]` **Additional Fixes**
- *memory* | `id:24969168`
- > - **SOP check:** Health monitor now also checks `memory/sop/` subdirectory (was only checking `memory/` root) - **ERROR_PATTERNS.md:** Created with all lessons #28-55 extracted from MEMORY.md
- `[open]` **Boss Standing Instruction**
- *memory, timezone* | `id:2496916f`
- > > "နောက်ပိုင်း time နဲ့ ပတ်သက်တာတွေ အကုန် MMT ပြောင်းဖို့ မှတ်ထားလိုက်ပါ" > ALL future timestamps MUST be in MMT (UTC+6:30). Never UTC.
- `[open]` **Lessons**
- *reminder* | `id:24969172`
- > - **#61: Reminder End button removed** to prevent bypassing Sale Bot voucher generation - **#62: Reconciliation detects future issues** — 3/8 sessions (37.5%) had no corresponding sale, showing the pr
- `[open]` **Lessons Learned (#61-65)**
- *reminder* | `id:24969185`
- > - **#61: Reminder End button removed** — bypassed Sale Bot voucher generation - **#62: Payment method NOT simple string** — value is `Cash:10000` or `KPay:0|Cash:10000`. Never use `= 'Cash'`. Must par
- *api, customer-bot* | `id:24969189`
- > - **#66: Customer Bot has OWN handlers** — `customer_bot/handlers.py` is completely separate from `bot/handlers/games.py`. The two bots share `bot/__init__.py` for common functions and `bot/api_client
- `[open]` **Post-Task Documentation**
- *api, sales-bot, memory, dashboard* | `id:2496918f`
- > - `auto_doc_updater.py` ran with full summary - MEMORY.md: lessons #60-65 added

### FEATURE (9)
- `[open]` **Customer Bot Booking Success Rate — Full Feature (07:00 - 08:00 UTC)**
- *booking, customer-bot, timezone* | `id:2496915f`
- `[open [critical]]` **New API Endpoint**
- *booking, api, console, customer-bot, sql* | `id:24969160`
- > - `GET /api/bot-users/booking-success-rate` with `since` query param (default: 2026-06-02) - Returns: totals (by status), daily_trend (14 days), weekly_trend (4 weeks), console_breakdown (C-01~C10), t
- `[open]` **New Dashboard Page**
- *booking, console, dashboard, api, sql* | `id:24969161`
- > - **File:** `CustomerBotSuccess.vue` at `/bot-success` route - Sidebar: "Bot Success 📊" under Bookings section (admin only)
- *sql, api, dashboard* | `id:24969165`
- > - `/root/psvibe_api_server/app.py` — New endpoint + rebook SQL logic - `/root/psvibe-dashboard/src/views/CustomerBotSuccess.vue` — New page
- `[open]` **Daily Till Manager — Full Feature (09:00 - 10:30 UTC)**
- *needs-review, timezone* | `id:24969179`
- `[open]` **Staff Permissions**
- *api, dashboard* | `id:24969181`
- > - Added `/till`, `/reconciliation`, `/members` to `staffOnlyPaths` in AppLayout.vue - API endpoints use `get_current_user` (any authenticated role) — no admin-only blocks
- `[open]` **Game Added**
- *api, sql* | `id:2496918d`
- > - "LEGO BATMAN: Legacy Of the Darknight" — Action Adventure, Solo, Available, 1 disc - Inserted into `games_library` table via API
- `[open]` **9. Auto-Settle (±3,000 MMK)**
- *api, dashboard, finance* | `id:2496919a`
- > - **Feature:** When payment amount is within ±3,000 of outstanding balance, auto-settle as fully paid - **Implementation:**
- `[open [critical]]` **10. PNL Breakdown Display**
- *finance* | `id:2496919b`
- > - **Before:** Single number + compact detail line - **After:** Full breakdown with 5 lines:

### AUDIT (3)
- `[open]` **Audit Results (Jun 21+)**
- ** | `id:24969163`
- `[open]` **Today's Till Data (DB Verified)**
- ** | `id:24969178`
- > ``` Opening: 50,000 | Cash Sales: 98,500 | KPay: 77,500 | WavePay: 0 | AYA: 0
- `[open [critical]]` **Vue Page: TillManager.vue — Redesigned**
- *sql, dashboard* | `id:24969180`
- > - 4-step numbered flow: ① Open → ② Sales (4 cards) → ③ Expected (full breakdown) → ④ Close - 4 payment method cards: Cash 💵, KPay 📱, WavePay 🌊, AYA Pay 🏦

### GENERAL (13)
- *docker, memory* | `id:24969169`
- > - All 9 projects healthy (20+ services across systemd + Docker) - 7 Docker containers all healthy
- `[open]` **Incidents**
- *booking, reminder, console, timezone* | `id:2496916c`
- > 1. **C-03 accidental End** from Reminder → restored booking + console_status 2. **console_status.start_time** showed 07:08 AM instead of 1:38 PM (UTC vs MMT)
- `[open]` **Remaining Work**
- *timezone* | `id:24969170`
- > - 50+ TIMESTAMP columns across other tables still display UTC (not yet migrated) - Priority: attendance_log, topup_log, stock_in, stock_out, receipts, promotions_log
- `[open]` **Daily Till Manager — Redesigned (≈09:30 UTC)**
- *needs-review, timezone* | `id:24969173`
- `[open [low]]` **UI Overhaul**
- *sql, finance* | `id:24969174`
- > - **Before:** 2-column grid, forms mixed, small numbers, confusing layout - **After:** Clean 4-step numbered flow
- `[open]` **4 Payment Methods**
- ** | `id:24969176`
- > - 💵 Cash: 98,500 Ks (today) - 📱 KPay: 77,500 Ks (today)
- `[open]` **Expected Amount Formula (PENDING Boss Confirmation)**
- ** | `id:24969177`
- > - Current: `Expected = Opening + Cash Only` (148,500) - Boss says "Expected မှားနေတယ်" — possibly wants all methods included (Cash+KPay+WavePay+AYA = 226,000)
- `[open]` **DB Table: `daily_till`**
- *sql* | `id:2496917a`
- > 16 columns: id, branch_id, till_date (unique), opening_balance, closing_balance, cash_sales_total, kpay_sales_total, expected_closing, actual_cash_counted,
- `[open]` **API Endpoints**
- *api, dashboard* | `id:2496917b`
- > - `GET /api/dashboard/till/today` — auto-creates till record, calculates live sales + cash movements, updates expected_closing - `POST /api/dashboard/till/open` — set opening_balance, mark status='ope
- `[open]` **Expected Formula (Final)**
- ** | `id:2496917e`
- > ``` Expected = Opening + Cash Sales + Transfer In + Inject − Eject − Transfer Out
- `[open]` **Today (Jun 29) Till State**
- ** | `id:2496917f`
- > | Field | Amount | |-------|--------|
- `[open]` **Customer Bot Game Library — Display Improvement (13:30 UTC)**
- *customer-bot, timezone* | `id:24969186`
- `[open]` **8. Buy/Sell Form Validation**
- ** | `id:24969199`
- > - **THB Account** — mandatory (alert + block save) - **Supplier/Customer** — mandatory (alert + block save)

## Memory (2026-06-30)

### BUG (4)
- `[open]` **SEL Currency Exchange — Contact Edit + Duplicate Check (08:59 - 09:03 UTC)**
- *needs-review, timezone* | `id:2496919c`
- *api, dashboard, customer-bot* | `id:2496919d`
- > 1. **db.py** — Added `counterparty_update(cid, name, phone, notes, cp_type)` and `counterparty_get_by_name(name)` functions 2. **app.py** — Added `CounterpartyUpdate` model, `PATCH /api/counterparties
- *memory, dashboard* | `id:249691a0`
- > - `/opt/kora-projects/sel_exchange/code/db.py` (lines ~177-189) - `/opt/kora-projects/sel_exchange/code/app.py` (lines ~154-222)
- `[open]` **SEL Exchange — OPEX Tab (09:35–09:40 UTC)**
- *api, dashboard, sql, timezone, finance* | `id:249691a1`
- > - Added `opex` table to `code/db.py` (init_db + CRUD functions: opex_list, opex_create, opex_update, opex_delete, opex_summary) - Added OPEX API endpoints to `code/app.py`: GET/POST/PATCH/DELETE `/api

### FIX (2)
- `[open]` **Bug Fixed During Implementation**
- ** | `id:2496919e`
- > - `execute()` in db.py returns `lastrowid` (0 for UPDATEs), causing `counterparty_update` to always return False - Fixed by using `get_conn()` directly with `cur.rowcount > 0` instead of `execute()`
- `[open]` **Tests Passed**
- ** | `id:2496919f`
- > - ✅ PATCH existing contact → Updated - ✅ PATCH non-existent → 404

## Memory (2026-07-01)

### BUG (16)
- ** | `id:249691a4`
- > `now_mmt()` year/month was hardcoded in queries instead of using user-selected month. July 1 တွင် `now_mmt()` July ဖြစ်သွားတော့ data မရှိ → အကုန်သုညပြ။
- `[open [low]]` **Root Causes Found**
- ** | `id:249691aa`
- > | # | Bug | Root Cause | Fix | |---|-----|-----------|-----|
- `[open [critical]]` **Notification Gap Fixes (5 gaps fixed)**
- *customer-bot, reminder, booking* | `id:249691b6`
- > | Gap | Fix | File | |-----|-----|------|
- `[open]` **Security Fixes (Issues #1-13)**
- *sql, dashboard, api, booking* | `id:249691b8`
- > - #1-4: Credential cleanup — Discord token, API key, MySQL password, MySQL root → env vars only - #5: 28+ bare `except:` → `except Exception as e` + logging
- `[open]` **Cleanup (Issues #21-24)**
- *api* | `id:249691ba`
- > - #21-24: Patch files archived to `/root/psvibe_api_server/archive/` (7 files + README), GSheet legacy references removed
- `[open]` **Architecture (Issues #25-28)**
- *sql, api* | `id:249691bb`
- > - #25: Discord MySQL tables created (4 schemas) - #26: GSheet fallback removed
- `[open]` **Documentation (Issues #45-49)**
- *needs-review* | `id:249691bd`
- > - README.md, SCHEMA.md, constants.py, CHANGELOG.md, setup.sh created
- `[open]` **D2: Double Session Reminder Bug**
- *reminder, console* | `id:249691bf`
- > **Root cause:** `_bot_has_persistent_reminder` key mismatch — lookup used `C-01|customer_tg_id` but storage used `C-01|admin_group_id`. Different chat IDs for same console → dedup never matched.
- `[open]` **Cash Transfer Fix**
- *sql, imports* | `id:249691c0`
- > **Bug:** `/admin/transfer` → `name '_mysql_exec' is not defined`
- `[open [critical]]` **Deferred (PLANNED — requires downtime)**
- *booking, reminder, imports, dashboard, api* | `id:249691cd`
- > | Item | Risk | Reason | |------|------|--------|
- `[open [critical]]` **Post-Split Fixes**
- *api, imports, booking* | `id:249691d3`
- > - **Critical bug found:** `member_routes.py` had duplicate `@app.middleware("http")` decorators → `NameError: name 'app' is not defined`. Removed decorator lines (middleware functions remain in app.py
- `[open [low]]` **Services**
- *api, customer-bot* | `id:249691d5`
- > - All 5 services running (psvibe-api, psvibe-sale-bot, psvibe_customer_bot, psvibe-attendance, psvibe-discord-bot) - API: 221 endpoints registered, health 200
- `[open [critical]]` **Remaining 6 Test Failures (Non-Critical)**
- *finance, console, dashboard, api* | `id:249691d8`
- > - 3 are skeleton stubs (reports.py) vs real endpoints in patch_routes.py - 2 are finance route path mismatches (dashboards vs standalone)
- `[open [critical]]` **Boss Report: `re` error on /reconciliation, `os` error on /bot-success**
- *finance, imports, console, api* | `id:249691dd`
- > | Bug | Missing Import | File | Impact | |-----|---------------|------|--------|
- `[open]` **Bot API OPEX — BROKEN (Extra Bug Found During Fix)**
- *sql, timezone, api* | `id:249691df`
- > The `/api/opex/*` endpoints in `routes/admin_sales_routes.py` used wrong function names: | Broken | Fixed |
- `[open]` **#71: Bot API endpoints in split files may use wrong function names**
- *imports, api, sql, dashboard, timezone* | `id:249691e1`
- > When splitting route code from `app.py`/`dashboard_routes.py`, function names may differ between source and destination modules: - `mysql_query` vs `_mysql_query` (public vs private import convention)

### FIX (23)
- `[open]` **Bugs Found & Fixed (4 bugs)**
- *finance, api, sql, dashboard, timezone* | `id:249691a5`
- > | # | Bug | File | Fix | |---|-----|------|-----|
- `[open [low]]` **Verification**
- *console* | `id:249691a6`
- > - June 2026 → Console Rental: 11,720,366 Ks, Topup: 450,000 Ks ✅ - July 2026 → All zeros (no data yet) ✅
- *api, dashboard* | `id:249691a7`
- > - `/root/psvibe_api_server/patch_routes.py` - `/root/psvibe_api_server/dashboard_routes.py`
- `[open]` **Post-Fix**
- *memory, api, vps* | `id:249691a8`
- > - Service restarted: `sudo systemctl restart psvibe-api` - MEMORY.md known issues updated
- `[open [low]]` **Still Pending**
- *needs-review* | `id:249691a9`
- > - ~~Cashflow asset deduction double-counting (Bug #2 from Jun 26)~~ → **Fixed Jul 1 round 2**
- *reminder, booking* | `id:249691ad`
- > | Path | Notifies Customer? | Notifies Admin? | Reminder Scheduled? | Gaps | |------|--------------------|--------------------|----------------------|------|
- `[open]` **Path 1: Customer Creates Booking (via Customer Bot)**
- *customer-bot, booking* | `id:249691ae`
- > - **Customer receives confirmation:** ❌ **NO.** No "သင်၏ Booking ကို အတည်ပြုပြီးပါပြီ" message. - **Admin group notified:** ✅ **Yes.** `_notify_booking_received()` sends to hardcoded chat ID `-1003686
- `[open]` **Path 2: Staff Approves → Customer Notified**
- *reminder* | `id:249691af`
- > - **Customer notification:** ✅ **YES.** Sends confirmation message. - **Admin notification:** ✅ **YES.** Inline card edited.
- `[open]` **Path 3: Staff Rejects → Customer Notified**
- *reminder* | `id:249691b0`
- > - **Customer notification:** ✅ **YES.** Sends rejection message. - **Reminders cancelled:** ✅ **YES.**
- `[open]` **Path 4: Staff Cancels → Customer Notified**
- ** | `id:249691b1`
- > - **Customer notification:** ✅ **YES.** Sends cancellation message. - **Admin notification:** ❌ **NO separate admin group notification.** Only inline card edited.
- `[open]` **Path 5: Customer Self-Cancels → Customer Notified**
- *reminder, booking* | `id:249691b2`
- > - **`_text_cancel_booking()`:** ✅ Customer notified, ✅ Admin notified, ❌ Reminders NOT cancelled. - **`cmd_cancel_booking()`:** ✅ Customer notified, ❌ Admin NOT notified, ✅ Reminders cancelled.
- `[open [critical]]` **Path 6: Auto-Cancel / Expired / No-Show**
- *api, booking* | `id:249691b3`
- > - **Customer notification (API cancel):** ✅ **YES.** (if `telegram_chat_id`) - **Admin notification:** ❌ **NO.**
- `[open]` **Path 7: Booking Checkin**
- *booking* | `id:249691b4`
- > - **Admin notification:** ✅ **YES.** Sends "✅ Customer Checked In!" - **Customer notification:** ✅ **YES.** Sends "🎉 Welcome to PS VIBE!"
- `[open]` **Code Quality (Issues #14-20)**
- *imports, console* | `id:249691b9`
- > - #14: Dead code documented - #15: 7 DB indexes added (`idx_status_start`, `idx_console_status`, `idx_phone_date`, etc.)
- `[open]` **Regression Fixes**
- *api, sales-bot* | `id:249691be`
- > - **Pagination regression in Sales Bot**: `api_fetch_members_async` broke after Fix #28 — API returns `{"members": [...], "total": N}` dict instead of list. Fixed by extracting `result["members"]` and
- `[open]` **Key Decisions**
- *api, reminder, console* | `id:249691c2`
- > - `_remind_loop` max 10 fires (50 min overdue soft cap) - Dedup key fix: console_id prefix match (ignores chat_id mismatch between bot and API)
- `[open [low]]` **Files Modified This Session**
- *dashboard, imports, reminder, booking* | `id:249691c3`
- > - `patch_routes.py` (lazy import restore, notification dedup) - `session_reminder_store.py` (dedup key fix)
- `[open]` **Actions Taken**
- *sql, console* | `id:249691c5`
- > **Deleted files (9):** - `sheets_client.py` — Main GSheet client (205 lines)
- `[open]` **Completed**
- *sql, api* | `id:249691cc`
- > | Item | Status | |------|--------|
- `[open]` **Key Lessons Today**
- *sql, imports, sub-agent, api* | `id:249691d9`
- > - **#61:** `transfer_out` in cash_movements stored as negative → `+ SUM()` not `- SUM()` - **#62:** Use cumulative SQL for opener/closing, not formula with section sums
- `[open [low]]` **TODOs for Next Session**
- *reminder, dashboard, api* | `id:249691da`
- > - Fix 6 remaining test failures (minor — route path alignment) - Rebuild dashboard + deploy
- *sql, api, vps* | `id:249691dc`
- > - Restored `next_member_id` and `next_member_row_no` endpoints in `routes/admin_sales_routes.py` (use MySQL to get next member ID/row number) - Server restarted, 19/19 tests pass, both endpoints retur
- `[open]` **Post-Fix Verification**
- ** | `id:249691e3`
- > - 19/19 tests PASS ✅ - `/reconciliation` → 200 (no more `re` error) ✅

### LESSON (3)
- ** | `id:249691ab`
- > - **#61:** `transfer_out` in `cash_movements` stored as **negative** — use `+ SUM(transfer_out)` not `- SUM(transfer_out)` - **#62:** Don't use formula `closing = opener + sections` when sections are
- `[open [low]]` **Phase 2: booking_flow.py Split**
- *imports, reminder, booking* | `id:249691d0`
- > - **1107 → 700 lines** + new `session_reminder.py` (460 lines) - All imports backward compatible via re-export pattern
- *needs-review* | `id:249691e0`

### FEATURE (6)
- `[open]` **Sales Daily Improvements**
- *dashboard* | `id:249691c1`
- > 1. **Default to current month** — Backend: when no date/period provided, filter to current month (was: `WHERE 1=1` — all data) 2. **Today/Yesterday quick buttons** — Frontend: added 📅 Today and 📅 Yest
- `[open]` **Phase 2: API Server Cleanup**
- *imports, api, console, sql, vps* | `id:249691c7`
- > - New clean endpoints: /api/config, /api/consoles, /api/stock/*, /api/reports/*, /api/staff/*, /api/promotions, /api/log/ai-interaction - Deleted: sheets_client.py, sync_console_mults.py, sync_setting
- `[open]` **Phase 3: Bot Callers**
- *api, customer-bot* | `id:249691c8`
- > - Sale Bot: 15 references updated (all /api/sheets/* → new paths) - Customer Bot: 2 references updated (config, log)
- `[open]` **New Files Created**
- *api* | `id:249691ce`
- > - /root/psvibe_api_server/CODING_STANDARDS.md - /root/psvibe_api_server/tests/conftest.py
- `[open]` **Phase 1: Test Suite Expansion + Type Hints**
- *finance, sql, api* | `id:249691cf`
- > - **Tests:** 9 → 19 tests (test_finance.py 5 tests, test_endpoints.py 4 tests, pytest.ini config) - **Type hints added to 5 files:** config.py, auth.py, mysql_db.py, session_timer.py, inventory_fifo.p
- `[open]` **#72: Top-level imports must be replicated in split modules**
- *imports, api* | `id:249691e2`
- > `app.py` had `import re`, `import os`, `import json` at module level. Any function using `re.search()`, `os.environ.get()`, `json.loads()` that gets moved to a route module needs the import added to t

### AUDIT (5)
- `[open]` **Memory (2026-07-01) - Customer Bot Notification Audit**
- *memory, sub-agent, customer-bot, booking* | `id:249691ac`
- > **Date:** 2026-07-01 **Auditor:** Kora (sub-agent)
- `[open]` **Security Hardening (Issues #34-39)**
- *needs-review* | `id:249691bc`
- > - CORS tightened, auth audit completed, token logging redacted
- `[open]` **Audit Findings**
- *sql, api, booking* | `id:249691c4`
- > - All 14 `/api/sheets/*` endpoints were ALREADY MySQL-based — only had legacy names - Real GSheet dependency: `sheets_client.py` (205 lines of gspread code) + `service_account.json`
- `[open]` **Phase 1: Audit**
- *sql, sub-agent, api* | `id:249691c6`
- > - Sub-agent traced all 14 /api/sheets/* endpoints — ALL already MySQL-based - sheets_client.py (205 lines) + service_account.json were the only real GSheet dependency
- `[open]` **Audit**
- *api, dashboard* | `id:249691db`
- > - Backup app.py + patch_routes.py → 139 API paths extracted - Current OpenAPI → 261 paths (includes dashboard endpoints)

### GENERAL (13)
- *needs-review* | `id:249691a2`
- > "Financial statement တွေ july ရောက်တော့ မှားနေတယ်"
- *api, dashboard, sub-agent, finance* | `id:249691a3`
- > Spawned sub-agent to investigate all financial statement endpoints: - `/api/sheets/pnl?m=2026-06`
- `[open [critical]]` **Critical Gaps Summary**
- *booking, customer-bot, reminder* | `id:249691b5`
- > 1.  **❌ Customer receives NO confirmation after booking creation** — Customer bot does not send "သင်၏ Booking ကို လက်ခံပြီးပါပြီ" after form submission. 2.  **❌ No proactive no-show auto-cancel** — No
- `[open]` **Remind Loop Cap**
- ** | `id:249691b7`
- > - `_remind_loop` now auto-stops after 10 fires (50 min overdue) to prevent infinite spam - Sends final warning message before stopping
- `[open]` **Phase 4: Uninstall**
- *needs-review* | `id:249691c9`
- > - gspread 6.2.1, oauth2client 4.1.3, google-auth-oauthlib 1.4.0 — all removed
- `[open]` **Phase 5: Gap #6**
- *sql* | `id:249691ca`
- > - Hardcoded admin chat ID -1003686032747 → env var STAFF_NOTIFY_CHAT - admin ID in SQL filter parameterized via env var
- `[open]` **Phase 6: Final Cleanup**
- *api* | `id:249691cb`
- > - 3 dead files deleted (check_sheets_access.py + 2 archive) - /api/sheets/* references in codebase: ZERO
- `[open]` **Phase 3: dashboard_routes.py Split**
- *booking, finance, dashboard, api* | `id:249691d1`
- > - **6596 → 5 files:**   - `dashboard_routes.py` (2811 remaining — core bookings/members/analytics)
- `[open]` **Phase 4: app.py Split (BIG ONE)**
- *booking, console, api* | `id:249691d2`
- > - **5365 → 618 lines (88.5% reduction)** 🔥 - **16 route modules** created:
- `[open [low]]` **Final Architecture (13,068 → ~4,129 lines, 68% lighter)**
- *dashboard, booking* | `id:249691d4`
- > | File | Before | After | |------|--------|-------|
- `[open]` **Backups**
- *api, sales-bot* | `id:249691d6`
- > - `/root/psvibe_api_server/backups/sprint-20260701/` - `/root/psvibe-sales-bot/backups/sprint-20260701/`
- `[open]` **Files Created Today (cumulative)**
- *reminder, finance, api* | `id:249691d7`
- > - **16 route modules** (routes/*) - **2 support modules** (helpers.py, deps.py)
- `[open]` **Dashboard OPEX — Monthly Default**
- *api, dashboard* | `id:249691de`
- > - `GET /api/dashboard/opex` — Was: date_from/date_to empty → ALL data. Now: empty → current month auto-filter - `GET /api/dashboard/opex/summary` — Same: now defaults to current month

## Memory (2026-07-02)

### BUG (11)
- `[fixed]` **8. Feedback Star Selection Hangs — Missing edit_message_text ✅**
- *feedback* | `id:249691eb`
- > **Bug:** Star ရွေးလိုက်ရင် bot ရပ်သွားတယ်။ `answerCallbackQuery` ပဲလုပ်ပြီး message update မဖြစ်ဘူး။ **Root Cause:** `cb_feedback_rating` function မှာ `thank_msg` build ပြီးတာနဲ့ function ရပ်သွားတယ် —
- `[fixed]` **9. Feedback Time Double Conversion (7:14 PM → 12:44 PM) ✅**
- *api, feedback, dashboard* | `id:249691ec`
- > **Bug:** Feedback created_at က `7:14 PM` ပြနေတယ် — တကယ့်အချိန်က `12:44 PM` MMT ဖြစ်သင့်။ **Root Cause:** **Double Conversion** —
- `[fixed]` **Transfer Page Account Balances Not Displaying ✅**
- *finance, sub-agent, dashboard, imports, api* | `id:249691f0`
- > **Bug:** `/admin/transfer` page — account balances empty (no data shown) **Root Cause:** Sub-agent moved `get_finance_balances` function from `dashboard_routes.py` to `routes/finance_routes.py` but `p
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-03 (သောကြာနေ့)
- ━━━━━━━━━━━━━━━**
- *auto-bug* | `id:676f67a4`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-03 (သောကြာနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:1fd93d19`
- *auto-bug* | `id:fd0e8f44`
- *auto-bug* | `id:1a543ffb`
- *auto-bug* | `id:bb4ad7f4`
- *auto-bug* | `id:524a1264`
- *auto-bug* | `id:fd325a38`
- *auto-bug* | `id:3be6946f`

### FIX (6)
- `[open]` **Console Swap — Staff Permission + Detail Cards**
- *api, dashboard, console, booking* | `id:249691e4`
- > - Added `/swap` to `staffOnlyPaths` in AppLayout.vue (staff couldn't see it) - Added booking ID, phone, notes display on confirmed booking cards in SwapView.vue
- `[open]` **Timer Duration Change — Reminder Conflict Hybrid Fix**
- *reminder, console, dashboard, api, booking* | `id:249691e5`
- > **Root cause:** `PUT /bookings/{id}/timer` only updated DB, never touched reminder systems. - **API fix:** `dashboard_adjust_timer()` now calls `session_timer.schedule_session_timer()` to cancel old A
- `[open [low]]` **Cancel Flow Fixes**
- *customer-bot, reminder, booking* | `id:249691e7`
- > - `_do_cancel_booking` (booking_flow.py): Added admin group notification via STAFF_NOTIFY_CHAT - `_text_cancel_booking` (customer_bot/handlers.py): Added `_cancel_advance_reminder` call (was missing)
- `[open]` **Lesson Learned — ⚠️ Timezone Fix Pattern**
- *api, timezone* | `id:249691ed`
- > - **Single source of truth:** Either store UTC + convert on read, OR store MMT + never convert. Never mix. - When fixing timezone: **check ALL three layers** — INSERT, SELECT, API response
- `[fixed]` **verify_subagent_output.py — Auto-Verification Script ✅**
- *sql, imports, sub-agent, api* | `id:249691f1`
- > **Built:** `/root/coordination/verify_subagent_output.py` — 4-layer verification for all sub-agent code output: 1. **Syntax Check** — `py_compile` on all modified files
- `[fixed [low]]` **Integration test: verified Kora↔MongoDB**
- *auto-fix* | `id:23964186`
- > **Fix applied:** Integration test: verified Kora↔MongoDB

### LESSON (2)
- `[open]` **Business Overview — All-Time Cumulative Dashboard**
- *sql, api, console, dashboard* | `id:249691e6`
- > - New endpoint: `GET /api/dashboard/cumulative` with 8 data sections - New page: `/cumulative` → `CumulativeStats.vue`
- `[open]` **Docs Update Status**
- *memory, timezone* | `id:249691ee`
- > - [x] Daily memory (2026-07-02.md) — 2 sessions, 9 fixes documented - [x] auto_doc_updater.py — commit #179

### AUDIT (1)
- `[open]` **Audit Findings (things already working)**
- *customer-bot, reminder, imports, api, booking* | `id:249691e8`
- > - Customer Bot DOES send confirmation after booking (screenshot verified) - No-show auto-cancel: cron runs `POST /api/bookings/auto-cancel-no-show` every 5 min (15-min grace)

### GENERAL (4)
- *api, dashboard, console, booking* | `id:249691e9`
- > - `/root/psvibe-dashboard/src/components/AppLayout.vue` — sidebar nav items + staffOnlyPaths - `/root/psvibe-dashboard/src/views/SwapView.vue` — confirmed bookings detail cards
- *sql, api, dashboard* | `id:249691ea`
- > - **#63:** PyMySQL `cur.execute()` treats `%Y`, `%m` etc as format placeholders — escape as `%%Y`, `%%m` in `DATE_FORMAT` calls - **#64:** Always check if a script/service already exists before planni
- `[open]` **⏰ Cron: Stale Checkin Cleanup (21:00 MMT)**
- *api, booking* | `id:249691ef`
- > - API: POST /api/cleanup/stale-checkins (dry_run=false) - Result: No stale check-ins found, 0 bookings cancelled
- `[open]` **Earlier Fixes (from summary — Session 3-4 gaps)**
- *api, imports, customer-bot, booking* | `id:249691f2`
- > - **`/bot-success` status case mismatch** — `'Done'→'done'`, `'Active'→'active'` (9 locations in `botuser_routes.py`) - **Customer Bot member lookup** — `_fetch_members()` needed double unwrap: API re

## Memory (2026-07-03)

### BUG (4)
- *auto-bug* | `id:e8176dc2`
- *auto-bug* | `id:b19f4c65`
- `[open [warning]]` **[WARNING] response_spike: Response time 688.5ms is 13.0x baseline (52.8ms)**
- *auto-bug* | `id:7e286d25`
- > **Bug detected:** [WARNING] response_spike: Response time 688.5ms is 13.0x baseline (52.8ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 1300.7ms is 32.8x baseline (39.6ms)**
- *auto-bug* | `id:103eba1a`
- > **Bug detected:** [WARNING] response_spike: Response time 1300.7ms is 32.8x baseline (39.6ms)

### FIX (4)
- `[fixed [critical]]` **C2: Checkin Race Condition — FOR UPDATE Lock on console_status**
- *api, booking, race-condition, console* | `id:b80ea98f`
- > Bug: Two concurrent checkins on same console could both become Active. Root cause: no FOR UPDATE lock. Fix: Added SELECT ... FOR UPDATE on console_status inside existing transaction at booking_routes.
- `[fixed [low]]` **L1: Dead GSheet Code — _GsheetRemoved Singleton**
- *sales-bot, gsheet, error-handling* | `id:78f8054e`
- > Bug: GSheet stubs returned None, callers crashed with AttributeError. Fix: Created _GsheetRemoved singleton class mimicking gspread interface. Stubs now return RuntimeError('GSheet backend has been re
- `[fixed [high]]` **H8: Empty member_id — 4-Level Fallback Resolution**
- *api, booking, member, analytics* | `id:1802e5e4`
- > Bug: member_id resolved to empty string when phone→member lookup failed, breaking analytics. Fix: Added 4-level fallback (payload memberId → phone → telegram_chat_id → customer_bot_users → auto-create
- `[fixed [medium]]` **M5: ConsoleStatusError for API-Down — Stop Silent 'No Free Consoles'**
- *sales-bot, api, error-handling, console* | `id:3d7ab1d1`
- > Bug: fetch_console_status() returned [] on API failure, callers showed 'no free consoles' misleadingly. Fix: Defined ConsoleStatusError custom exception, changed return [] to raise ConsoleStatusError.

### LESSON (3)
- `[open [high]]` **Auto-Verify After Every Sub-Agent Task**
- *sub-agent, verification, workflow* | `id:724e4d2b`
- > ## Lesson #68\nAlways run verify_subagent_output.py after every sub-agent code change.\n\n### Why\nSub-agents make 3 common mistakes:\n1. Import chain breaks (function moved, imports not updated)\n2.
- `[open [high]]` **#69: MongoDB Query First — grep Second**
- *workflow, memory, debugging, best-practice* | `id:36904086`
- > ## Lesson #69\nAlways query MongoDB (kora_memory.py search/trace) BEFORE grep/read when debugging.\n\n### Why\n1. Code Graph (7,840 entities, 103K relations) can instantly show which functions depend
- `[open [medium]]` **#70: Telegram Markdown — Always Escape User Data**
- *telegram, markdown, escape, bot, bug-pattern* | `id:531febe9`
- > ## Lesson #70\nAll dynamic text (member names, game names, custom input) displayed with parse_mode='Markdown' MUST be escaped.\n\n### Root Cause\nTelegram Markdown treats _ * [ ] ( ) ~ python\ndef _es

## Memory (2026-07-04)

### BUG (6)
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-04 (စနေနေ့)
- ━━━━━━━━━━━━━━━━━━**
- *auto-bug* | `id:8a8cc91b`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-04 (စနေနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:38526a80`
- `[open [warning]]` **[WARNING] response_spike: Response time 584.2ms is 18.4x baseline (31.7ms)**
- *auto-bug* | `id:6d92fce0`
- > **Bug detected:** [WARNING] response_spike: Response time 584.2ms is 18.4x baseline (31.7ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 584.8ms is 22.5x baseline (26.0ms)**
- *auto-bug* | `id:1276e160`
- > **Bug detected:** [WARNING] response_spike: Response time 584.8ms is 22.5x baseline (26.0ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 1107.2ms is 4.2x baseline (262.1ms)**
- *auto-bug* | `id:cd61d1d3`
- > **Bug detected:** [WARNING] response_spike: Response time 1107.2ms is 4.2x baseline (262.1ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 1103.6ms is 7.1x baseline (156.4ms)**
- *auto-bug* | `id:aadecf9d`
- > **Bug detected:** [WARNING] response_spike: Response time 1103.6ms is 7.1x baseline (156.4ms)

### FIX (1)
- `[fixed [critical]]` **SSD Return — Game Auto Re-add to Source SSD**
- *ssd, console, games, return, bugfix* | `id:c756a297`
- > step_ssd_ret_game: SSD Return လုပ်တဲ့အခါ game ကို console မှဖျက်ပြီး source SSD (notes field: From Samsung T1 Shield → SSD-T1) ထဲ auto ပြန်ထည့်ပေးမယ်။ Previously game tracking ထဲက လုံးဝပျောက်သွားတာ။ A

## Memory (2026-07-05)

### BUG (6)
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-05 (တနင်္ဂနွေနေ့)
- ━━━━━━━━━━━━**
- *auto-bug* | `id:ec00aa6a`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-05 (တနင်္ဂနွေနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:84e4de0c`
- `[fixed [critical]]` **Caddy 502 — Docker cant reach host:8000 (UFW order bug)**
- ** | `id:f18a212b`
- > Root cause: UFW DENY rule on port 8000 blocked Docker bridge traffic (172.17.0.0/16). DROP rule was before ACCEPT rule causing order mismatch. Fix: removed UFW DENY for internal service ports (8000/90
- `[open [warning]]` **[WARNING] response_spike: Response time 522.7ms is 10.0x baseline (52.4ms)**
- *auto-bug* | `id:c70a3f71`
- > **Bug detected:** [WARNING] response_spike: Response time 522.7ms is 10.0x baseline (52.4ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 832.4ms is 22.5x baseline (37.0ms)**
- *auto-bug* | `id:dca3c252`
- > **Bug detected:** [WARNING] response_spike: Response time 832.4ms is 22.5x baseline (37.0ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 813.7ms is 22.2x baseline (36.6ms)**
- *auto-bug* | `id:a13760e5`
- > **Bug detected:** [WARNING] response_spike: Response time 813.7ms is 22.2x baseline (36.6ms)

### FIX (1)
- `[open [high]]` **VPS Security Hardening — SSH/Caddy/UFW/Fail2ban**
- ** | `id:e0718eb7`
- > SSH ports 80/443 freed for Caddy. UFW configured with 12 ports blocked. fail2ban 4 jails. HSTS + security headers active. Cloudflare Tunnel restored to direct API routing after Caddy 502 debugging.

## Memory (2026-07-06)

### BUG (2)
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-06 (တနင်္လာနေ့)
- ━━━━━━━━━━━━━━**
- *auto-bug* | `id:2dea955b`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-06 (တနင်္လာနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:6843911a`

### LESSON (1)
- `[archived [low]]` **Kora Bug Patterns Reference**
- *bug, pattern, reference, archive* | `id:d89498a9`
- > # 🐛 Bug Patterns — PS VIBE Sales Bot

### AUDIT (15)
- `[archived [low]]` **Booking Session Separation Plan**
- *booking, plan, archive* | `id:ea14a2d2`
- > # Booking vs Session — Error-Proof Implementation Plan > **Version:** 2.0 — Error-Proof Edition
- `[archived [low]]` **Legacy ARCHIVE.md — Comprehensive Memory Archive**
- *archive, legacy* | `id:9f21e4fd`
- > # Archived Memory Entries *Archived: 2026-06-09 05:49 UTC*
- `[archived [low]]` **ACM Wallet MySQL Migration Impact Analysis**
- *acm_wallet, migration, archive* | `id:e58ea2b3`
- > # ACM Wallet: Google Sheets → MySQL Migration Impact Analysis
- `[archived [low]]` **Multi-Project Architecture Analysis (Jun 2026)**
- *architecture, analysis, archive* | `id:dd4787dc`
- > # Kora Multi-Project Architecture Analysis > **Date:** 2026-06-25 02:15 UTC
- `[archived [low]]` **Booking Features Implementation Plan**
- *booking, plan, archive* | `id:ef2b97e7`
- > # PS VIBE Booking System — Feature Implementation Plan
- `[archived [low]]` **Booking Audit Deep Round 2**
- *booking, audit, archive* | `id:ca2429e9`
- > # 🔍 PS VIBE Booking Flow — Deep Audit Round 2
- `[archived [low]]` **PS VIBE Comprehensive System Scan**
- *psvibe, scan, archive* | `id:940e5c52`
- > # PS VIBE — Comprehensive Project Scan **Date:** 2026-07-01 | **Scanner:** Kora Subagent (DeepSeek V4 Pro)
- `[archived [low]]` **Booking Upgrade Audit**
- *booking, upgrade, audit, archive* | `id:c5befd94`
- > # PS VIBE Booking System — Comprehensive Audit & Upgrade Plan
- `[archived [low]]` **Admin Group Notification Audit**
- *notification, audit, archive* | `id:bfb29849`
- > # Admin Group Notification Audit — Comprehensive Report
- `[archived [low]]` **Booking Session Separation Audit**
- *booking, session, audit, archive* | `id:62216a01`
- > # Booking vs Session — Separation Audit > **Generated:** 2026-07-01 | **Author:** Kora Subagent
- `[archived [low]]` **Booking System Audit — June 19**
- *booking, system, audit, archive* | `id:77c6a261`
- > # PS VIBE Booking System — Full Audit Report **Date:** 2026-06-19
- `[archived [low]]` **Booking Audit Complete Report**
- *booking, audit, complete, archive* | `id:ff47582a`
- > # 🔍 PS VIBE Booking Flow — Complete Audit
- `[archived [low]]` **Customer Bot Notification Audit**
- *customer_bot, notification, audit, archive* | `id:21cf58fb`
- > # PS VIBE Customer Bot — Booking Notification Audit
- `[archived [low]]` **GSheet Removal Audit**
- *gsheet, removal, audit, archive* | `id:6a4fd934`
- > # GSheet Removal Audit — /api/sheets/* Endpoints
- `[archived [low]]` **Booking Timeslot Audit**
- *booking, timeslot, audit, archive* | `id:6f586e0f`
- > # Booking Time & Slot System — Production Deep Audit

### GENERAL (4)
- `[archived [low]]` **Coordination Framework SOP**
- *sop, coordination, framework, archive* | `id:58556447`
- > # 🔗 Sub-agent Coordination Framework (v2.0) ## မချိုးဖောက်ရ — ဒါက Red Line
- `[archived [low]]` **Helper Guidelines SOP**
- *sop, helper, guidelines, archive* | `id:186c44ce`
- > # 🛡️ Helper Agents — Master ALLOW / DON'T ALLOW Guidelines v1.0 ## တိကျသော ခွင့်ပြုချက်များနှင့် တားမြစ်ချက်များ
- `[archived [low]]` **Spawning Manager SOP**
- *sop, spawning, manager, archive* | `id:cd3530ba`
- > # 🚀 Spawning Manager Agent — SOP v1.0 ## Standard Operating Procedure & Boundaries
- `[archived [low]]` **Spawn Protocol SOP**
- *sop, spawn, protocol, archive* | `id:acc01ae0`
- > # Kora Spawn Protocol — Quick Reference

## Memory (2026-07-07)

### BUG (4)
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-07 (အင်္ဂါနေ့)
- *auto-bug* | `id:f261cd8d`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-07 (အင်္ဂါနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:86064a17`
- `[open [warning]]` **[WARNING] response_spike: Response time 662.6ms is 19.0x baseline (34.9ms)**
- *auto-bug* | `id:833320a8`
- > **Bug detected:** [WARNING] response_spike: Response time 662.6ms is 19.0x baseline (34.9ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 656.5ms is 13.6x baseline (48.1ms)**
- *auto-bug* | `id:09b49649`
- > **Bug detected:** [WARNING] response_spike: Response time 656.5ms is 13.6x baseline (48.1ms)

### FEATURE (1)
- `[verified]` **Three Brothers Construction Accounting Bot**
- *construction, accounting, bot, docker* | `id:128d7bf0`
- > Three Brothers Construction accounting bot running on Docker at /opt/construction-bot/. Telegram bot @three_brothers_accounting_bot. PNL and ledger tracking for construction materials. Deployed as Doc

## Memory (2026-07-08)

### BUG (5)
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-08 (ဗုဒ္ဓဟူးနေ့)
- ━━━━━━━━━━━━━**
- *auto-bug* | `id:bfae3fa6`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-08 (ဗုဒ္ဓဟူးနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:9b006f0e`
- `[open [warning]]` **[WARNING] response_spike: Response time 1054.0ms is 34.0x baseline (31.0ms)**
- *auto-bug* | `id:094f13fb`
- > **Bug detected:** [WARNING] response_spike: Response time 1054.0ms is 34.0x baseline (31.0ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 94.6ms is 4.3x baseline (22.1ms)**
- *auto-bug* | `id:b0260994`
- > **Bug detected:** [WARNING] response_spike: Response time 94.6ms is 4.3x baseline (22.1ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 94.9ms is 4.0x baseline (23.8ms)**
- *auto-bug* | `id:c912bb8d`
- > **Bug detected:** [WARNING] response_spike: Response time 94.9ms is 4.0x baseline (23.8ms)

## Memory (2026-07-09)

### BUG (4)
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-09 (ကြာသပတေးနေ့)
- *auto-bug* | `id:67bac9d7`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-09 (ကြာသပတေးနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:a1d95742`
- `[open [warning]]` **[WARNING] response_spike: Response time 578.0ms is 22.1x baseline (26.2ms)**
- *auto-bug* | `id:88a255bb`
- > **Bug detected:** [WARNING] response_spike: Response time 578.0ms is 22.1x baseline (26.2ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 615.1ms is 23.5x baseline (26.2ms)**
- *auto-bug* | `id:80364e93`
- > **Bug detected:** [WARNING] response_spike: Response time 615.1ms is 23.5x baseline (26.2ms)

### FIX (1)
- `[fixed [medium]]` **VPN UI Fixes — Recent Keys, Data Usage, Sub-tab Layout (2026-07-09)**
- *vpn, outline, xray, ui, osmo* | `id:fa240e68`
- > ### Fix 1: Recent Keys မပေါ်တာ 🐛→✅ **Root Cause:** `{key_rows}` placeholder ကို render မှာ `.replace()` မလုပ်မေ့နေ။ Agent keys page က key table empty ဖြစ်နေ။

### LESSON (1)
- `[verified [low]]` **Osmo VPN UI Feedback — Layout Order & Data Display Standards**
- *lesson, vpn, outline, xray, ui* | `id:a2ebdb06`
- > #134 — VPN UI Layout Order Matter: Payment Summary > Sub-tab Nav Osmo requested sub-tab nav (Xray/Outline) be moved below Payment Summary cards.

## Memory (2026-07-10)

### BUG (11)
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-10 (သောကြာနေ့)
- *auto-bug* | `id:f811baa6`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-10 (သောကြာနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:6e4f951e`
- `[open [warning]]` **[WARNING] response_spike: Response time 639.6ms is 5.8x baseline (110.2ms)**
- *auto-bug* | `id:279820bc`
- > **Bug detected:** [WARNING] response_spike: Response time 639.6ms is 5.8x baseline (110.2ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 608.7ms is 18.7x baseline (32.6ms)**
- *auto-bug* | `id:54b61bbe`
- > **Bug detected:** [WARNING] response_spike: Response time 608.7ms is 18.7x baseline (32.6ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 603.1ms is 13.7x baseline (44.0ms)**
- *auto-bug* | `id:d4536043`
- > **Bug detected:** [WARNING] response_spike: Response time 603.1ms is 13.7x baseline (44.0ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 587.4ms is 11.0x baseline (53.4ms)**
- *auto-bug* | `id:1f3c843c`
- > **Bug detected:** [WARNING] response_spike: Response time 587.4ms is 11.0x baseline (53.4ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 586.1ms is 9.3x baseline (63.3ms)**
- *auto-bug* | `id:30cebfb9`
- > **Bug detected:** [WARNING] response_spike: Response time 586.1ms is 9.3x baseline (63.3ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 665.3ms is 11.0x baseline (60.5ms)**
- *auto-bug* | `id:f3356fe7`
- > **Bug detected:** [WARNING] response_spike: Response time 665.3ms is 11.0x baseline (60.5ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 648.2ms is 9.5x baseline (68.3ms)**
- *auto-bug* | `id:47f7c1d9`
- > **Bug detected:** [WARNING] response_spike: Response time 648.2ms is 9.5x baseline (68.3ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 1333.9ms is 27.1x baseline (49.2ms)**
- *auto-bug* | `id:f408ed4a`
- > **Bug detected:** [WARNING] response_spike: Response time 1333.9ms is 27.1x baseline (49.2ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 1316.7ms is 26.8x baseline (49.2ms)**
- *auto-bug* | `id:3589b160`
- > **Bug detected:** [WARNING] response_spike: Response time 1316.7ms is 26.8x baseline (49.2ms)

## Memory (2026-07-11)

### BUG (13)
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-11 (စနေနေ့)
- *auto-bug* | `id:1b435096`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-11 (စနေနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:0c1e6214`
- `[open [warning]]` **[WARNING] response_spike: Response time 1221.5ms is 9.8x baseline (124.5ms)**
- *auto-bug* | `id:1b491bea`
- > **Bug detected:** [WARNING] response_spike: Response time 1221.5ms is 9.8x baseline (124.5ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 1217.7ms is 16.3x baseline (74.6ms)**
- *auto-bug* | `id:a1cefa99`
- > **Bug detected:** [WARNING] response_spike: Response time 1217.7ms is 16.3x baseline (74.6ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 1112.2ms is 8.6x baseline (129.6ms)**
- *auto-bug* | `id:11cade74`
- > **Bug detected:** [WARNING] response_spike: Response time 1112.2ms is 8.6x baseline (129.6ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 1117.4ms is 7.0x baseline (159.5ms)**
- *auto-bug* | `id:582d89a8`
- > **Bug detected:** [WARNING] response_spike: Response time 1117.4ms is 7.0x baseline (159.5ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 571.9ms is 5.1x baseline (112.4ms)**
- *auto-bug* | `id:35f646d8`
- > **Bug detected:** [WARNING] response_spike: Response time 571.9ms is 5.1x baseline (112.4ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 573.3ms is 5.5x baseline (104.9ms)**
- *auto-bug* | `id:fc204cbe`
- > **Bug detected:** [WARNING] response_spike: Response time 573.3ms is 5.5x baseline (104.9ms)
- `[fixed [high]]` **Outline VPN Thread Deadlock — Server Unresponsive**
- *outline, vpn, deadlock, threading* | `id:54b56b5d`
- > outline-web.service had 17 threads stuck in futex_wait_queue. Root cause: _form_idempotency_lock contention when render_keys() is called concurrently. Multiple requests holding locks while waiting for
- `[fixed [medium]]` **Slow Dashboard — Per-key Prometheus Queries**
- *outline, vpn, performance, prometheus* | `id:0a7b2391`
- > get_key_metrics() queried Prometheus once per active Outline key via docker exec shadowbox curl (7 keys × 300ms = 2.1s). Fix: Added batch_get_metrics() — single Prometheus query sum(shadowsocks_data_b
- `[fixed [medium]]` **ERR_CONNECTION_CLOSED on Key Delete/Expire/Renew**
- *outline, vpn, cloudflare, timeout* | `id:2de3f64c`
- > After key operations, server rendered full dashboard (1.2s) before responding. Cloudflare closed connection → ERR_CONNECTION_CLOSED. Fix: Changed delete/expire/renew handlers to use 302 redirect (8ms)
- `[open]` **Outline VPN: Pagination scoped to current sub-tab**
- *outline-vpn, pagination, js, fixed* | `id:a684dcc6`
- > paginate(), resetPagination(), and searchKeys() were using document.querySelectorAll(".key-page-item") which selected ALL key-page-item divs from ALL tabs (Xray Active + Expired + Outline). This cause
- `[open]` **Outline VPN: Rename handler changed to 302 redirect**
- *outline-vpn, rename, redirect, fixed* | `id:25261815`
- > Rename handler used send_html(render_keys(...)) which rendered full dashboard (~1.2s for 62 keys). Cloudflare 100s timeout caused ERR_CONNECTION_CLOSED. Fix: Changed to send_redirect_admin() returning

### FIX (1)
- `[open]` **Outline VPN: searchKeys clears to current page (not page 1)**
- *outline-vpn, search, keys* | `id:f72c6a25`
- > When search was cleared (f.length === 0) the searchKeys function reset display to items[0-19] (page 1). Fix: Now reads cur-page hidden input and restores display to current page. No more jumping to pa

### FEATURE (1)
- `[open]` **Construction Bot - Expense Tracking**
- *construction, bot, expense* | `id:9a2d6ed4`
- > Tracks construction project expenses via Telegram. Categories: materials, labor, transport, utilities. Uses SQLite database. Deployed via Docker container on bot-server-01.

### GENERAL (12)
- `[open]` **do_POST /rename handler**
- *outline-vpn, rename, handler* | `id:aafc2dfe`
- > Rename key handler in Outline VPN web server. Located in do_POST() at path "/rename" in /opt/outline-web/server.py line ~4541. Flow: rate limiter check → backup_before_write() → validate_name() → upda
- `[open]` **do_POST /delete handler**
- *outline-vpn, delete, handler* | `id:2aa4e986`
- > Delete key handler. Located in do_POST() at path "/delete" in /opt/outline-web/server.py line ~4502. Flow: backup_before_write() → idempotency guard (checks if already deleted) → Outline API DELETE →
- `[open]` **do_POST /renew handler**
- *outline-vpn, renew, handler* | `id:e44695e8`
- > Renew key handler. Located in do_POST() at path "/renew" in /opt/outline-web/server.py line ~4624. Xray path: keep same UUID, reactivate_key_in_db() + re-add to Xray config. Outline path: create new O
- `[open]` **do_POST /expire handler**
- *outline-vpn, expire, handler* | `id:fe134c85`
- > Expire key handler. Located in do_POST() at path "/expire" in /opt/outline-web/server.py line ~4586. Flow: backup_before_write() → Outline API DELETE for Outline keys → mark_key_expired() in DB (is_ac
- `[open]` **Kora Host API Bridge - Overview**
- *kora-host-api, infrastructure, bridge* | `id:0dd892da`
- > Kora Host API Bridge connects multiple services across hosts. Provides: (1) Agent portal on port 9357, (2) Cloudflare tunnel management, (3) Outline admin proxy on port 9356, (4) Cross-host API routin
- `[open]` **Three Brothers Construction - Accounting Bot**
- *construction, bot, telegram* | `id:eee982ee`
- > Telegram bot @three_brothers_accounting_bot running in Docker at /opt/construction-bot/. Handles construction project accounting, expense tracking, and financial reporting. Docker-based deployment.
- `[open]` **AKT Clothing Shop ERP - Overview**
- *akt-clothing, erp, inventory* | `id:92b92c99`
- > AKT Clothing Shop ERP system running on port 8010. API-based inventory and sales management. Currently basic setup with product management and sales tracking capabilities.
- `[open]` **YYO Personal Wallet Bot - Overview**
- *yyo-wallet, bot, finance* | `id:c9c5dcaa`
- > Personal finance tracking bot. Systemd service: yyo-personal-wallet. Code at /opt/yyo-personal-wallet/. Tracks income, expenses, and provides financial summaries via Telegram.
- `[open]` **PS VIBE Social Media Auto-Reply - Overview**
- *social-autoreply, social-media, automation* | `id:7fc28896`
- > Automated social media reply system for PS VIBE. Manages auto-responses on Facebook, TikTok, and Discord. Systemd service. Handles common customer inquiries automatically.
- `[open]` **PS VIBE Inventory Alerts - Overview**
- *inventory, alerts, monitoring* | `id:2de5c81d`
- > Inventory monitoring and alert system for PS VIBE. Tracks stock levels, low-stock warnings, and auto-notifications. Currently in setup phase.
- `[open]` **VPN Manager (Outline + Xray REALITY) - Overview**
- *vpn-manager, outline, xray, reality* | `id:63683cd7`
- > VPN Manager system providing Outline Shadowsocks (port 995) and Xray REALITY (port 443/993) VPN services. Admin UI at outline.ps-vibe.com (port 9356). 58 keys (51 Xray + 7 Outline), capacity 500. Mana
- `[open]` **Kora Voice Assistant - Overview**
- *kora-voice, assistant, voice* | `id:0c5326df`
- > Voice-enabled assistant for PS VIBE operations. Systemd service: kora-voice.service. Integrates with Kora core for voice-based queries and commands.

## Memory (2026-07-12)

### BUG (6)
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-12 (တနင်္ဂနွေနေ့)
- *auto-bug* | `id:0ed7ea9c`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-12 (တနင်္ဂနွေနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:688aacf9`
- `[open [warning]]` **[WARNING] response_spike: Response time 2710.6ms is 11.9x baseline (228.0ms)**
- *auto-bug* | `id:dead8498`
- > **Bug detected:** [WARNING] response_spike: Response time 2710.6ms is 11.9x baseline (228.0ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 2729.4ms is 21.2x baseline (128.7ms)**
- *auto-bug* | `id:472c3e50`
- > **Bug detected:** [WARNING] response_spike: Response time 2729.4ms is 21.2x baseline (128.7ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 1404.2ms is 11.7x baseline (120.1ms)**
- *auto-bug* | `id:9ada0150`
- > **Bug detected:** [WARNING] response_spike: Response time 1404.2ms is 11.7x baseline (120.1ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 1407.1ms is 19.4x baseline (72.5ms)**
- *auto-bug* | `id:ec0a103c`
- > **Bug detected:** [WARNING] response_spike: Response time 1407.1ms is 19.4x baseline (72.5ms)

### AUDIT (1)
- `[open]` **Weekly Code Quality Scan - PS VIBE Sales Bot**
- *weekly, scan, clean, psvibe* | `id:e286d1aa`
- > Date: 2026-07-12 01:30 UTC Type: Weekly Code Quality Scan

## Memory (2026-07-13)

### BUG (5)
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-13 (တနင်္လာနေ့)
- *auto-bug* | `id:056cbe7a`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-13 (တနင်္လာနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:f85ea436`
- `[open [warning]]` **[WARNING] response_spike: Response time 628.3ms is 16.8x baseline (37.3ms)**
- *auto-bug* | `id:cc09159d`
- > **Bug detected:** [WARNING] response_spike: Response time 628.3ms is 16.8x baseline (37.3ms)
- `[open [warning]]` **[WARNING] response_spike: Response time 612.0ms is 11.5x baseline (53.3ms)**
- *auto-bug* | `id:c820cb34`
- > **Bug detected:** [WARNING] response_spike: Response time 612.0ms is 11.5x baseline (53.3ms)
- `[open]` **Wallet insufficient check skipped for member bookings**
- *wallet, booking_id, shortfall, session_end* | `id:7f6eee6b`
- > launch_session_sale had if booking_id: block that set wallet_mins=None for ALL bookings (guest+member), skipping wallet check for members. Fixed by adding if not is_guest: check inside booking_id bloc

### FIX (4)
- `[fixed [high]]` **Outline VPN Key Create timeout — Full render → 302 redirect**
- *outline, vpn, xray, key-create, cloudflare* | `id:9e1566fd`
- > Xray & Outline key CREATE handlers used send_html(render_keys(...)) (1-2s) instead of send_redirect_admin(...) (~8ms). Cloudflare returned 526/524 errors. Fixed by switching both to redirect (Lesson #
- `[fixed [high]]` **Referral Code System — Circular Import + GSheet→API Migration**
- *psvibe, referral, circular-import, gsheet, api* | `id:eb087841`
- > 3 fixed issues: (1) BTN_ASSIGN_REFERRAL NameError — added lazy wrappers show_mm_menu, prompt_mm_lookup, prompt_referral_code in bot/__init__.py. (2) save_referral_code used GSheet only — migrated to A
- `[fixed [low]]` **Game selection: BTN_NOT_SURE changed & moved to top**
- *psvibe, customer-bot, game-selection, booking* | `id:7e6e9b30`
- > Changed BTN_NOT_SURE from '🤷 မရွေးတတ်ပါ' to '🏪 ဆိုင်ရောက်မှ ရွေးမယ်' and moved from bottom to top of game list keyboard. Updated both booking_handlers.py and handlers.py. Restarted psvibe-customer-bot
- `[fixed [low]]` **Garbled Unicode footer in deposit verify notification**
- *psvibe, deposit, notification, telegram, unicode* | `id:0bde51d0`
- > Removed garbled Burmese text '📲 Booking ခိလ ရေရာက်းထားပဲ့နှင့် ရှင့် ကိုဆက်သန္ဓိရားပါ။' from deposit verify Telegram notification in api_deposit_verify. File: booking_routes.py lines 2264-2266. Restar

### LESSON (1)
- `[open]` **Referral Code: Circular import + GSheet→API + fetch_members dict unwrap**
- *lesson, referral, circular-import, gsheet, api* | `id:fd5110f7`
- > #158: Circular imports solved by lazy wrappers in bot/__init__.py — any function in handler A called by handler B needs _get_handler() wrapper + explicit import. #159: GSheet is fully deprecated — sav

## Memory (2026-07-14)

### BUG (23)
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-14 (အင်္ဂါနေ့)
- *auto-bug* | `id:706a063b`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-14 (အင်္ဂါနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:ebb321a3`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 15 times**
- *auto-bug* | `id:8f327a92`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 15 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 48 times**
- *auto-bug* | `id:bedc3c1e`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 48 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 98 times**
- *auto-bug* | `id:c710b520`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 98 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 50 times**
- *auto-bug* | `id:da014ad4`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 50 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 97 times**
- *auto-bug* | `id:2dc58b0d`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 97 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 49 times**
- *auto-bug* | `id:eef90208`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 49 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 12 times**
- *auto-bug* | `id:cefba446`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 12 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 31 times**
- *auto-bug* | `id:c17fd072`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 31 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 55 times**
- *auto-bug* | `id:bafd03c7`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 55 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 58 times**
- *auto-bug* | `id:001be0d5`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 58 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 77 times**
- *auto-bug* | `id:e3c18816`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 77 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 145 times**
- *auto-bug* | `id:e12a223a`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 145 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 47 times**
- *auto-bug* | `id:61aca5c3`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 47 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 34 times**
- *auto-bug* | `id:9ba6db57`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 34 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 192 times**
- *auto-bug* | `id:d8881ead`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 192 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 40 times**
- *auto-bug* | `id:6297f0ae`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 40 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 41 times**
- *auto-bug* | `id:143bcd20`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 41 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 46 times**
- *auto-bug* | `id:8cd7ceea`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 46 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 53 times**
- *auto-bug* | `id:f46747be`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 53 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 99 times**
- *auto-bug* | `id:fe3dd831`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 99 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 44 times**
- *auto-bug* | `id:e5ae8d0d`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 44 times

## Memory (2026-07-15)

### BUG (70)
- *auto-bug* | `id:2cfd8d0c`
- *auto-bug* | `id:1b9810cc`
- *auto-bug* | `id:5252fec7`
- *auto-bug* | `id:44cd4871`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 144 times**
- *auto-bug* | `id:b1873559`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 144 times
- *auto-bug* | `id:156147d0`
- *auto-bug* | `id:c140bd4b`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 93 times**
- *auto-bug* | `id:da17d370`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 93 times
- `[open [low]]` **Prediction: 🌅 **Kora Morning Briefing** — 2026-07-15 (ဗုဒ္ဓဟူးနေ့)
- *auto-bug* | `id:ecc4c786`
- > **Bug detected:** Prediction: 🌅 **Kora Morning Briefing** — 2026-07-15 (ဗုဒ္ဓဟူးနေ့) ━━━━━━━━━━━━━━━━━━━━━━
- *auto-bug* | `id:501d540f`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 148 times**
- *auto-bug* | `id:f25bffb6`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 148 times
- *auto-bug* | `id:d46e4a6a`
- *auto-bug* | `id:55282bbf`
- *auto-bug* | `id:fb8dd67f`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 100 times**
- *auto-bug* | `id:b31d070e`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 100 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 95 times**
- *auto-bug* | `id:2a701601`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 95 times
- *auto-bug* | `id:dddf4cd3`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 6 times**
- *auto-bug* | `id:4224a998`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 6 times
- *auto-bug* | `id:adc5a960`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 60 times**
- *auto-bug* | `id:0cc5fdd8`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 60 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 193 times**
- *auto-bug* | `id:dfe9d645`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 193 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 9 times**
- *auto-bug* | `id:808d2ede`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 9 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 96 times**
- *auto-bug* | `id:e22adfa0`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 96 times
- *auto-bug* | `id:cb05f087`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 14 times**
- *auto-bug* | `id:93cc58fc`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 14 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 146 times**
- *auto-bug* | `id:960d7653`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 146 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 110 times**
- *auto-bug* | `id:09c86bcb`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 110 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 22 times**
- *auto-bug* | `id:56214119`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 22 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 23 times**
- *auto-bug* | `id:c08e7aff`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 23 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 94 times**
- *auto-bug* | `id:b055fbb7`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 94 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 130 times**
- *auto-bug* | `id:be8ca25d`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 130 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 147 times**
- *auto-bug* | `id:0d737dee`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 147 times
- *auto-bug* | `id:9478c340`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 195 times**
- *auto-bug* | `id:ee5d69e8`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 195 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 150 times**
- *auto-bug* | `id:dc6a7312`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 150 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 198 times**
- *auto-bug* | `id:0f32d5b1`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 198 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 21 times**
- *auto-bug* | `id:11664731`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 21 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 24 times**
- *auto-bug* | `id:82b8c8d4`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 24 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 25 times**
- *auto-bug* | `id:fc5a5303`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 25 times
- *auto-bug* | `id:6c7b07e5`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 45 times**
- *auto-bug* | `id:ba40cc4c`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 45 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 10 times**
- *auto-bug* | `id:78820e4d`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 10 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 61 times**
- *auto-bug* | `id:7df2618d`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 61 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 38 times**
- *auto-bug* | `id:1a378483`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 38 times
- *auto-bug* | `id:04a1d026`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 43 times**
- *auto-bug* | `id:f4f8eeca`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 43 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 243 times**
- *auto-bug* | `id:62e75de4`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 243 times
- *auto-bug* | `id:bf85050a`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 194 times**
- *auto-bug* | `id:8d4c1ccd`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 194 times
- *auto-bug* | `id:1d2b1031`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 143 times**
- *auto-bug* | `id:026f2e5c`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 143 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 75 times**
- *auto-bug* | `id:bef1ec5e`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 75 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 76 times**
- *auto-bug* | `id:a1cc5eaa`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 76 times
- *auto-bug* | `id:8e061d3e`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 92 times**
- *auto-bug* | `id:70b6a981`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 92 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 141 times**
- *auto-bug* | `id:d1649a86`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 141 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 189 times**
- *auto-bug* | `id:56584b88`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 189 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 237 times**
- *auto-bug* | `id:d741a6b9`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 237 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 284 times**
- *auto-bug* | `id:1414afc9`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 284 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 64 times**
- *auto-bug* | `id:63bc67c9`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 64 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 66 times**
- *auto-bug* | `id:981e351e`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 66 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 70 times**
- *auto-bug* | `id:b9a2393b`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 70 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 28 times**
- *auto-bug* | `id:6a6f942e`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 28 times
- *auto-bug* | `id:a25c70ac`
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 63 times**
- *auto-bug* | `id:eeefef7b`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 63 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 71 times**
- *auto-bug* | `id:e03c86c2`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 71 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 27 times**
- *auto-bug* | `id:7ffa5142`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 27 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 197 times**
- *auto-bug* | `id:dfb5c675`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 197 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 200 times**
- *auto-bug* | `id:c42f2377`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 200 times
- `[open [warning]]` **[WARNING] frequent_restarts: Service restarted 91 times**
- *auto-bug* | `id:5e168149`
- > **Bug detected:** [WARNING] frequent_restarts: Service restarted 91 times

### FIX (7)
- `[verified [critical]]` **Reentrant lock deadlock in VPN admin - lock held across render_keys()**
- *vpn, deadlock, threading, lock* | `id:65e41857`
- > 5 locations fixed: _form_idempotency_lock changed to RLock. send_html(render_keys/agent_dashboard) moved outside _form_idempotency_lock, _admin_create_lock, and _agent_create_lock blocks in both Handl
- `[fixed]` **Outline VPN Dashboard perf fix + data sync**
- *outline, vpn, performance, async* | `id:41b0c7ec`
- > Fixed: 1) Batched device_limit query (78→1 DB conn per render). 2) Async key create name/data-limit (non-blocking threads). 3) Deleted corrupt key(id='name') from SG Outline API. 4) Removed 2 stale Xr
- `[verified [high]]` **Deposit pre-redeem must NOT change status**
- *deposit, booking, pre-redeem, sales* | `id:70f1c223`
- > Pre-redeem endpoint was setting deposit_status to 'redeemed' prematurely, causing /api/sales/record to skip deduction. Fix: removed status change from pre-redeem endpoint, leave deposit_status as 'ver
- `[verified [medium]]` **Payment_method must show deposit method in sales_daily**
- *deposit, payment_method, sales_daily, display* | `id:b57a3a51`
- > Sales_daily payment_method only showed session-end collection method (e.g. Cash:5000) but not the original deposit payment method (KPay:3500). Fix: prepend deposit method with '(dep)' label to payment
- `[verified [critical]]` **Bot payment collection now deducts verified deposit from net payable**
- *deposit, collection, payment, bot* | `id:11c5829f`
- > All payment steps (prompt_kpay, step_pay_method, step_pay_amount, _show_payment_review, prompt_confirm, step_sale_confirm) now deduct verified deposit from displayed net payable. Staff only collects r
- `[verified [high]]` **Auto-cancel cron: skip active bookings from forfeit**
- *deposit, auto-cancel, cron, forfeit* | `id:4c741088`
- > Auto-cancel cron was forfeiting deposits for bookings that had already been checked in. Fix: added 'AND cs.id IS NULL' to SQL SELECT so bookings with console_sessions rows are never auto-cancelled or
- `[verified [medium]]` **Cash movements backfill for 9 deposit bookings (Jul 12-15)**
- *deposit, cash_movements, backfill, reconciliation* | `id:6b809518`
- > Session-end payment collections were never recorded in cash_movements, only deposit injects. Backfilled 147,850 Ks across 9 bookings: Cash +84,350, KPay +63,500, WavePay ±29,000 (refunded). Sales_dail

### LESSON (1)
- `[archived [medium]]` **Lesson #164-167: Deposit lifecycle rules**
- *lessons, deposit, lifecycle* | `id:545f62ed`
- > 164: Pre-redeem must NOT change deposit_status — Leave as 'verified' for sales record to handle deduction.\n165: Payment_method must show deposit method — Finance needs to know original deposit method

## Memory (2026-07-16)

### BUG (19)
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
