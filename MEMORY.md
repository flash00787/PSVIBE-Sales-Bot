# 🧠 Kora's Long-Term Memory

## 🏗️ Multi-Project Architecture (Phase 1-5 Complete — 2026-06-25)

Kora now manages **8 projects** with full coordination tool support.

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
- **Member balance:** Column H of Card_wallet Google Sheet (legacy) → MySQL `member_wallets` (primary)
- **Receipts:** Burmese footer text must be removed
- **Coupon codes:** Valid samples: CBQVUHYG, CBANN6LD, CBZVNW7O, CBB292MP, CB7U617B

## 🧠 Critical Lessons Learned (Cumulative)

### Python Patterns
### API & Database Patterns
### System Patterns
### Business Logic
33. **Charges are outgoing-only bank fees** — Buy/Payable has charges (we send money); Sell/Receivable has NO charges (customer pays us).
34. **Never include cleanup in test scripts** — caused 2 accidental data deletions; use backup restore instead.
35. **Save-and-restore dropdown selections** — when rebuilding select options via `innerHTML`, save `.value` first then restore after.

## Major Projects & Milestones

### Grand Opening (June 6, 2026)
- Data reset: All tables cleared except 4 confirmed bookings
- 10+ critical bugs fixed in 2 days leading up (coupon, wallet, booking, sales)
- All services active and stable

### Food Cart Feature (June 14)
- Phase 1 deployed: Staff can add food to active sessions via Console → Food Sale
- Food items auto-loaded into sale voucher at session end
- Phase 2 pending: Customer Bot self-ordering

### Finance System (June 15)
- PNL & Balance Sheet endpoints fixed (were broken stubs)
- Auto-depreciation script deployed (monthly cron, 1st of month)
- Auto-amortization for prepaid rent (monthly cron)

### Discord Bot (June 15-16)
- 35 slash commands across gaming, account, community, staff modules
- Auto-mod, birthday cron, LFG system, suggestion system
- Full integration with web dashboard feedback tab

### Suggestion System (June 17)
- Full pipeline: Discord → API → Dashboard
- Staff approve/reject with embed updates

### Console Timer & Booking System Overhaul (June 22)
- Console Timers page: live elapsed/remaining with 30s refresh, timer adjust dropdown
- Timeline AM/PM format + frozen console column
- No Timer support: "∞ Open End" display, 8hr conflict window
- Re-book cancelled bookings with date/time/duration modal
- Booking soft-delete (no physical deletions, 30-day cleanup)
- Auto-cancel disabled; manual-only end policy
- Customer Feedback dashboard page with stats, 14-day trend, full table

## ⚠️ Known Issues (Persistent)

| Issue | Severity | Status |
|-------|----------|--------|
| food-cart/release silent fail (stock_out) | — | ✅ Fixed Jun 23 |
| Move API start_time reset | — | ✅ Fixed Jun 23 |
| booking_id path game_amt=0 | — | ✅ Fixed Jun 23 |
| Customer Bot phone last-3-digits lookup | — | ✅ Fixed Jun 25 |
| Staff role couldn't access Members tab | — | ✅ Fixed Jun 25 |

## Working Preferences

- **Language:** Burmese primary, English for tech terms
- **Timezone:** Asia/Yangon (UTC+6:30) — always convert for Boss
- **Delegation:** Always delegate complex tasks to sub-agents. Never do manually what a helper can do.
- **Fix protocol:** `python3 /root/coordination/fix_protocol.py --start <file>` before any code fix
- **Post-fix documentation:** Run `auto_doc_updater.py` + update daily memory + MEMORY.md
- **📁 New project onboarding (2026-06-25):** Every new project MUST include: (1) `README.md` at project root, (2) `memory/projects/<slug>/state.md`, (3) Daily memory section, (4) MEMORY.md entry, (5) `auto_doc_updater.py` commit
- **Sub-agent timeout:** 300s default

## 🆕 June 23, 2026 — Major Bug Fixes & Features

### Critical Bug Fixes
3. **Feedback routed to admin group:** `chat_id.startsWith('-')` check added in `console.py` — skip notifications when target is a group, not individual user.
4. **No Timer (duration=0) comprehensive fix:**
   - Timeline bar: extended to NOW instead of 5% fixed width
   - Utilization: counts up to NOW for live stats
   - Timezone: removed `+ 6.5 * 3600000` — browser provides MMT natively
   - Conflict check: `_dur_end = 360 if duration_mins == 0 else duration_mins` at 5 locations
5. **Session Reminder System — 3-type complete fix:**
   - Type 1 (API timer gap): `schedule_session_timer` now called from 5 start-session paths; `_bot_has_persistent_reminder()` reads `session_reminders.json`
   - Type 2 (Telegram format): `parse_mode: "Markdown"` with HTML `<b>` tags → HTTP 400. Changed to `parse_mode: "HTML"` consistently.
   - Type 3 (event loop): `resume_active_timers()` at module load time had no event loop → moved to FastAPI `lifespan` handler.
6. **console_mgmt.py import failure:** Module-level `__getattr__` lazy loader failed at runtime. Added explicit `import asyncio` + `from bot import fetch_console_status`.
7. **Receipt template overhaul (v1→v3):** Thermal 80mm format, base64 logo (no static file mount), AYA Pay fix, Topup field fixes, WALLET BALANCE section.

### New Features
8. **Active Session Move API:** `POST /api/sessions/move` — transaction-safe console swap with FOR UPDATE row locking, timer reschedule, conflict check.
9. **End Session Confirm Step:** Inline keyboard confirm dialog prevents accidental session endings.

### New Critical Lessons
- **API 200 OK on error is misleading** — always check error response body, not just HTTP status. `error_response()` should use non-200 status codes.
- **Move API must preserve start_time** — use `_bk["start_time"]`, not `_now`. Resetting start_time breaks session duration calculation.
- **booking_id paths must still calculate game_amt** — `if booking_id: game_amt = 0` is wrong. Booking customers still need game_amt from play time.

## Memory (2026-06-19 — 2026-06-21)

*(Older memory entries trimmed — full history in git.)*

- Bug 4.7: Duplicate check fixed (added `rejected` to excluded statuses)
- Gateway DNS: Added fallback DNS (Hetzner + Cloudflare) to Docker daemon + agent compose files
- SSH Incident: NEVER touch ssh.socket.d (GOLDEN RULE #12)
- June 22 Improvements: Shutdown handlers, staging env, field_utils.py, type hints — all complete ✅

## Memory (2026-06-22)

### 26. Phase 1 Branch Architecture — Silent Prep ✅ (18:00 MMT)
- Added `branch_id INT DEFAULT 1` to 50 tables, API middleware reads `X-Branch-ID` header, bot config updated. Sale Bot per-branch, Customer Bot shared w/ branch selection, Wallet shared. Phase 2 ready when Branch 2 opens.

### Profit Distribution Audit ✅ (18:48 MMT - 22 Jun 2026)
- 10% mgmt fee fully implemented in `dashboard_routes.py`; API + DB tables ready. Token: Aung Chan Myint 34%+mgmt, Ye Myat 33%, Wai Yan Htet 33% (300M Ks total). Dashboard UI + bot flows pending.

### Profit Distribution Bug Fix — Date Filters ✅ (19:05 MMT - 22 Jun 2026)
- Added `period` param + date WHERE clauses to `calculate_profit_distribution()` (sales, opex, COGS, depreciation). Removed FIFO wallet liability from P&L (balance sheet item). June net: -12.5M Ks (expected for launch month).

## Memory (2026-06-23)

### Phase 2 Multi-Branch Audit
- Full audit of all bots + dashboard + API for multi-branch readiness
- **Critical gap found:** `api_client.py` in Sale Bot & Customer Bot don't send `X-Branch-ID` header
- API `get_branch_id()` middleware is ready but endpoints don't filter by branch_id
- Dashboard `client.ts` has no branch header support
- Dashboard branch selector UI not built
- Plan: Fix api_client → API endpoints → Dashboard → Deploy Sale Bot copy for Branch 2

### SSD Name Update
- Updated `console_name` in `console_games` table:
- SSD-T1 → "Samsung T1 Shield"
- SSD-Blue → "SanDisk - Light Green"
- SSD-Grey → "SanDisk - Orange"
- Now matches Sale Bot names for consistency

### Profit Distribution Fix (Complete from Jun 22)
- Profit Distribution now 100% aligned with Monthly PNL (-7,781,303 Ks for June)
- Key fix: PNL-matching logic (same revenue breakdown, stock FIFO for COGS, exclusive depreciation)
- Excluded FIFO wallet liability from monthly P&L (balance sheet item, not monthly expense)

### Major System Fixes & Features (Jun 23 Session)



### Key Technical Notes
- **Server:** VPS `5.223.81.16`, SSH key `/root/.ssh/id_boss`
- **API server:** `/root/psvibe_api_server/`, service: `psvibe-api`
- **Dashboard:** `/root/psvibe-dashboard/`, built to `/root/psvibe_api_server/dashboard-dist/`
- **Sale Bot:** `/root/psvibe-sales-bot/`, reminder store: `/root/psvibe-sales-bot/data/session_reminders.json`
- **MySQL:** Docker `psvibe-mysql`, user `psvibe_user`, DB `psvibe_api`
- **Receipt JSON:** `/root/psvibe-sales-bot/bot/receipts/{voucher_id}.json`
- **API key:** `JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ`
- **MySQL password:** `PsVibe@2026_Rotated!`
- **Multiple backups preserved** in `app.py.bak-*`, `console.py.bak-*`, `TimelineView.vue.bak-*`, `receipt_template.html.bak-*`

### Additional Fixes (Jun 23 late session)

### 11. console_mgmt.py — Missing Import Fix
- **Bug:** `NameError: name 'fetch_console_status' is not defined` when pressing "🔄 Move Console"
- **Root cause:** `console_mgmt.py` relied on module-level `__getattr__` lazy loader but it failed at runtime
- **Fix:** Added explicit imports at top of file:
- import asyncio
- from bot import fetch_console_status
- Restarted bot service, confirmed running (PID 1843415)

### 12. End Session — Confirm Step Added
- **Issue:** C-05 session ended prematurely (50 min instead of 120 min) — staff accidentally hit End Session
- **Fix:** Added inline keyboard confirm step in End Session flow
- **New flow:** Console Selection → Confirm dialog (shows console, member, start time, elapsed) → Yes/No buttons
- "No" returns to console menu; "Yes" proceeds to end session + open sales voucher
- Prevents accidental session endings from misclicks or menu exploration

### Food Order Stock Out Bug (Jun 23 final session)

### 13. Move Console + End Session — Game Minutes Fix
- **Bug:** console move လုပ်ပြီး session end ရင် game minutes voucher ထဲ မပါလာ
- **Root cause:** `sales.py` line 1787: `if booking_id: game_amt = 0` — booking_id ရှိရင် game_amt zero လုပ်တာ
- Move-then-end flow မှာ booking_id မရှိတော့လို့ game_amt တွက်မိ — ဒါက Move Console ရဲ့ side effect
- **Fix:** booking_id path မှာလည်း `game_amt = round((total_mins * base_rate * multiplier) / 60)` တွက်ခိုင်း
- **Verified:** logs show `confirm_summary: game_amt_in_context=167` ✅

### 14. 🐛 CRITICAL: Food Cart Stock Out Silent Fail
- **Bug:** Food order items sale voucher ထွက်ပေမယ့် stock out history မှာ မပေါ်
- **Root cause:** `patch_routes.py` → `food_cart_release()` function ထဲက `_mc` (MySQL connector) variable က NameError!
- food_cart_release: name '_mc' is not defined
- **Why silent:** `from app import *` က underscore-prefixed names (`_mc`, `_MYSQL_CFG`) auto-export မလုပ်ဘူး
- **Why 200 OK:** try/except က error ဖမ်းပြီး `error_response` ပြန်ပေမယ့် HTTP code 200 ပြန်နေ
- **Impact:** Food cart items ရဲ့ stock_out records တစ်ခုမှ DB ထဲ မရေးဘူး — inventory က တကယ်ကျမသွား
- **Fix:** `food_cart_release()` function ထဲမှာ local import ထည့်:
- from app import _mc, _MYSQL_CFG, _mysql_get_setting
- API PID 1900814 (restarted)
- **Additionally:** `_sale_bg()` logs တွေ ထည့်ပြီး — item တစ်ခုစီရဲ့ `from_cart` flag နဲ့ skip/process status log လုပ်ခိုင်း

### 15. Console Management Menu Layout Fix
- **Removed:** `BTN_CHANGE_GAME` button (Boss: "Game ပြောင်းက ဖြုတ်ထားလိုက်ဦးမယ်")
- **Removed:** "⚙️ Console စီမံ" submenu from main menu
- **Added:** `🔄 Move Console` directly in Console Management main menu
- **Fixed:** function name mismatch `show_console_mgmt_menu` → `show_con_mgmt_menu`
- **Fixed:** `__getattr__` lazy loader → explicit imports for ALL constants + utility functions in `console_mgmt.py`
- **Current keyboard:**
- 🟢 Start  ⏹️ Session ဆုံး  🔄 Move Console  📊 Status
- 🍔 Food Order  📀 Install  📀 External SSD  🎮 Game Library  🔙 Back

### 16. Move API start_time Preserved
- **Bug:** `POST /api/sessions/move` resetting `start_time` to current time
- **Fix:** Changed `_now` → `_bk["start_time"]` in app.py line 2631 — preserves original session start time

### Updated Service State
| Service | PID | Status |
|---------|-----|--------|
| psvibe-api | 1900814 | ✅ Running |
| psvibe-sale-bot | 1843415 | ✅ Running |

## Memory (2026-06-25)

### ACM Wallet — Google Sheets → MySQL Migration Complete ✅
- Full cutover: `main.py` 5,979→5,197 lines (-782), zero functional Sheets code remaining
- DB `acm_wallet`: 7 tables, 147 tx, 44 OB, 56 settings migrated
- Backend: MySQL-only, all read/write via `db.py` (437 lines)
- Cleanup: gspread removed, `_SHEETS_TIMEOUT`→`_DB_TIMEOUT`, `service_account.json` deleted, mysqldump cron added
- Service: `acm-personal-wallet` ✅ active

### PS VIBE Web — Staff Role → Members Tab ✅
- `dashboard-dist/assets/index-B6C8MOLE.js`: Router meta `roles:["admin","staff"]` + sidebar `ie` array

### 🐛 Customer Bot — Phone Last-3-Digits Lookup Fix ✅
- **Bug:** API `fetch_members` now returns full objects (MySQL) but bot expected flat IDs
- **Fix:** `customer_bot/api.py` — detect format, build directly from API response (1 call vs 1+N)
- **Fix:** `customer_bot/booking_handlers.py` — balance key chain: `wallet_mins`→`balance_mins`→`balance`
- **Performance:** 1 API call instead of 1+N per booking flow

### New Lessons
- **#26: API format changes after migration** — When API returns different format, check ALL consumers
- **#27: Minified JS edits** — Use Python string replace for precision, not sed; always backup first

### Updated Service State
| Service | PID | Status |
|---------|-----|--------|
| psvibe-api | 1900814 | ✅ Running |
| psvibe-sale-bot | 1843415 | ✅ Running |
| psvibe-customer-bot | 2267555 | ✅ Running |
| acm-personal-wallet | (auto) | ✅ Running |

### SEL Currency Exchange — Full Project Built (Baht ↔ MMK) ✅
- **Stack:** FastAPI (port 8001), SQLite, Telegram Bot, Web Dashboard
- **Location:** `/opt/kora-projects/sel_exchange/`
- **Dashboard:** `ps-vibe.com/currency-exchange` with login (HMAC-SHA256 auth)
- **4 Tabs:** Overview | Receivable & Payable | Inventory | People & Accounts
- **15 API endpoints** including PNL (FIFO), FIFO inventory, multi-payment lines
- **FIFO PNL:** Full FIFO matching with effective rates (buy+charges, sell-charges)
- **Charges separation:** Bank charges tracked per payment line, excluded from supplier debt
- **Auto-backup:** Hourly cron to `/opt/kora-projects/sel_exchange/backups/`
- Current config: 4 accounts (Cash/Bank MMK, Cash/Bank THB), 5 contacts (2 suppliers, 3 customers)

### New Lessons (continued)
- **#33-35:** See \## Critical Lessons Learned above

## Memory (2026-06-27)

### Cancelled Bookings 2-Hour Timeline Filter
- **Added** cancelled_at DATETIME column to console_booking (was missing)
- **Backfilled** 175 existing cancelled bookings with cancelled_at = created_at
- **3 API cancel endpoints** now set cancelled_at = NOW()
- **Server-side filter**: cancelled_at >= NOW() - INTERVAL 2 HOUR in MySQL query
- **Frontend UTC fix**: new Date(cancelledAt.replace(' ', 'T') + 'Z') — Z suffix forces UTC
- **Double-layer**: API + JS both filter (defense-in-depth)

### New Lessons
- **#37: JS Date(YYYY-MM-DDTHH:MM:SS) is LOCAL time** — without Z/timezone suffix, interpreted in browser timezone. Always append Z for UTC DB timestamps.
- **#38: Server-side filter > client-side** — for time-based filtering, MySQL NOW() - INTERVAL is more reliable than browser JS Date parsing.
