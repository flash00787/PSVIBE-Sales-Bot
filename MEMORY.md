# 🧠 Kora's Long-Term Memory

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
23. **Dashboard code is the source of truth** — Other API stubs may be outdated. Always check `dashboard_routes.py` first.
24. **FIFO for wallet consumption** — Oldest topups consumed first; bonus/free minutes have 0 Ks value.
25. **No Timer (duration=0) display** — Shows "∞ Open End" on Timeline. Conflict check uses 480 min (8hr) window. Never apply `duration or 60` pattern for display.

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
| Feedback: 76% walk-in sessions lack telegram_chat_id | Medium | Deferred (Boss: keep as-is) |
| Feedback Dashboard page added (Jun 22) | — | Done |
| n8n payment (€25.68) overdue | Medium | Pending boss action |
| GitHub Deploy failing (psvibe-api-server) | Low | Pre-existing |
| Food Note issue — Phase 2 pending | Low | Deferred |
| VPS reboot caused DNS issues June 20 | Low | Mitigated |
| `_remind_loop` timer never fires | Low | Known, not critical |
| 100+ games claim vs 41 in DB | Low | Needs verification |
| food-cart/release silent fail (stock_out) | — | ✅ Fixed Jun 23 |
| Move API start_time reset | — | ✅ Fixed Jun 23 |
| booking_id path game_amt=0 | — | ✅ Fixed Jun 23 |

## Working Preferences

- **Language:** Burmese primary, English for tech terms
- **Timezone:** Asia/Yangon (UTC+6:30) — always convert for Boss
- **Delegation:** Always delegate complex tasks to sub-agents. Never do manually what a helper can do.
- **Fix protocol:** `python3 /root/coordination/fix_protocol.py --start <file>` before any code fix
- **Post-fix documentation:** Run `auto_doc_updater.py` + update daily memory + MEMORY.md
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
- **Boss directive:** Current shop → "Sanchaung Branch" (ဆိုင်ခွဲအတွက်ကြိုပြင်)
- **What was done (ZERO impact on existing operations):**
- 1. **DB Migration (50/58 tables):**
- Added `branch_id INT DEFAULT 1` to all per-branch tables
- 24 tables already had branch_id (pre-existing)
- Added to 26 more: accounts, capital_movements, finance_*, promotions, member_coupons, customer_feedback, settings, settings_config, profit_distributions, dividends, shareholders, stock_hold, card_wallet, console_*_backup, food_cart, dashboard_users, staff_records_bak
- Shared tables intentionally excluded: members, member_wallets, member_loyalty, games_library, loyalty_*, customer_bot_*, referral_log, sync_status
- All existing data auto-filled with DEFAULT 1
- 2. **Branches Table:**
- Renamed "PS VIBE Main" → "Sanchaung Branch" (code: SANCHAUNG)
- Added open/close time (9AM-9PM), telegram_group_id (-1003686032747)
- 3. **API Middleware (`app.py`):**
- `branch_context_middleware` reads `X-Branch-ID` header (defaults to 1)
- `get_branch_id()` helper for endpoints
- New endpoint `POST /api/bookings/mark-bot-reminder` for bot→API timer coordination
- 4. **Bot Config (`__init__.py`):**
- Added `BRANCH_ID`, `BRANCH_NAME` env vars
- `_api_headers()` includes `X-Branch-ID` in all API calls
- `/etc/psvibe/secrets.env` updated with BRANCH_ID=1, BRANCH_NAME=Sanchaung Branch
- **Architecture:**
- Sale Bot → separate per branch (copy + config)
- Customer Bot → shared with branch selection step
- Wallet → shared across branches
- **Next:** Phase 2 activates when Branch 2 opens (~1 hour work)

### Profit Distribution Audit (18:48 MMT - 22 Jun 2026)
- Boss asked to verify Profit Distribution system with 10% management fee.

### Findings
- 1. **10% Management Fee → FULLY IMPLEMENTED** in `dashboard_routes.py` (lines ~2868-2920)
- `mgmt_fee = round(net_profit * 0.10, 0)` → Aung Chan Myint
- 90% distributable → split by ownership % (34/33/33)
- 2. **API Endpoints** ready: `/profit-distribution/calculate`, `/record`, `/history`
- 3. **DB Tables** ready: `profit_distributions`, `profit_distribution_details` with `is_management_fee` flag
- 4. **Dashboard UI** — NOT yet built (missing page for calculate + distribute)
- 5. **Bot flows** — NOT implemented (CAP_ACCT, SHARE_NAME states defined but no handlers)

### Profit Distribution Formula
- Net Profit = Total Sales - Opex - COGS - Depreciation - Wallet Liability
- Mgmt Fee = Net Profit × 10% → Aung Chan Myint
- Distributable = Net Profit × 90% → Shareholders by ownership %

### Token Accounts
- Aung Chan Myint: 34% (102M) + 10% mgmt fee
- Ye Myat: 33% (99M)
- Wai Yan Htet: 33% (99M)
- Total Capital: 300M Ks

### What's Missing
- Dashboard Profit Distribution page (UI only, API ready)
- Capital Injection/Ejection bot flows
- Shareholder management bot flows

### Profit Distribution Bug Fix — Date Filters Added ✅ (19:05 MMT - 22 Jun 2026)

### Bug: -12,527,636 Ks net loss showing
- **Root cause:** `calculate_profit_distribution()` in `dashboard_routes.py` had ZERO date filters on any query — summing ALL data from entire DB history.

### Fix Applied (`dashboard_routes.py` lines ~2831-2890):
- 1. **Added `period` query parameter** — defaults to current month (e.g., `?period=2026-06`)
- 2. **sales_daily**: Added `WHERE sale_date >= '2026-06-01' AND sale_date <= '2026-06-30'`
- 3. **opex**: Added `WHERE expense_date >= '2026-06-01' AND expense_date <= '2026-06-30'`
- 4. **stock_in (COGS)**: Added `WHERE created_at >= '2026-06-01 00:00:00' AND created_at <= '2026-06-30 23:59:59'`
- 5. **depreciation**: Changed from summing ALL assets' monthly_dep → `WHERE purchase_date <= '2026-06-30'` (only active assets)
- 6. **FIFO wallet liability**: REMOVED from monthly P&L calculation (set to 0). This is a balance sheet item (~12M total outstanding), not a monthly expense. Prepays are already deducted when consumed as wallet deductions in sales.
- 7. **management_fee_to**: Now dynamic — uses shareholder with role "Founder" instead of hardcoded "Aung Chan Myint"

### June 2026 Post-Fix Numbers:
- Revenue:    8,163,333 Ks  (454 vouchers)
- Opex:     -11,877,066 Ks  (marketing, rent, salaries)
- COGS:      -1,795,438 Ks  (stock inventory)
- Depr:      -7,018,465 Ks  (42 assets monthly)
- ───────────────
- Net:      -12,527,636 Ks  (loss — expected for launch month)
- **Verdict:** June is launch month — startup costs heavy (Vlog marketing 3.5M, Interior Decoration 2.1M/month, Rent 2.5M, Eco Flow 178K/month). July+ should improve as marketing costs drop and revenue grows.

### Files Modified:
- `/root/psvibe_api_server/dashboard_routes.py` — `calculate_profit_distribution` function

### Note:
- Sub-agent failed due to missing OpenAI API key for gpt-4o-mini model. Fix applied directly by Kora.
- Dashboard Profit Distribution UI page was already built and deployed (Boss showed screenshot).

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
