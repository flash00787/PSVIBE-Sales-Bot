# 🧠 Kora's Long-Term Memory
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

### Key Operations (General)
- **Staff Salary**: Auto-generate via `POST /salary/generate` — formula: base + transport + food_allowance + att_bonus + food_com + game_bonus − advances − leave_penalty

### Key Operations (General)
- **Member balance:** Column H of Card_wallet Google Sheet (legacy) → MySQL `member_wallets` (primary)
- **Receipts:** Burmese footer text must be removed
- **Coupon codes:** Valid samples: CBQVUHYG, CBANN6LD, CBZVNW7O, CBB292MP, CB7U617B

## 🧠 Critical Lessons Learned (Cumulative)

### Python Patterns
### API & Database Patterns
### System Patterns
28. **Never edit minified Vue build output directly** — Always edit source `.vue` files and rebuild. Single-character name conflicts break entire components. Project: `/root/psvibe-dashboard/`. (#28)
29. **Vite builds replace all hashes** — Every rebuild generates new content hash filenames. Old files must be cleaned to avoid stale cached versions. (#29)
30. **JS object key sorting trap** — String keys that look like integers (e.g., "848") are sorted numerically by V8, not by insertion order. `.reverse()` on `Object.values()` doesn't reverse insertion order when keys are numeric strings. (#30)
31. **Lane stacking is wrong UX for timeline overlaps** — Boss prefers natural overlap + tap-to-select popup. Don't force lane splitting; it makes blocks too small. (#31)
32. **`window` object not available in Vue `<template>`** — Must use computed properties or method-returned style objects instead of inline `window.innerWidth` references. (#32)
33. **SQLite FOREIGN KEY enforcement** — Must enable `PRAGMA foreign_keys = ON` per connection; not default. (#33)
34. **FastAPI query params vs path params** — Path params auto-convert types; query params are strings. Must validate/convert manually. (#34)
35. **CORS middleware ordering** — Must be added BEFORE route registration in FastAPI; order matters. (#35)
36. **FIFO matching complexity** — Multi-currency FIFO with charges requires careful tracking of remaining quantities per lot. Test thoroughly with partial sales. (#36)
37. **JS Date(YYYY-MM-DDTHH:MM:SS) is LOCAL time** — Without Z/timezone suffix, interpreted in browser timezone. Always append Z for UTC DB timestamps. (#37)
38. **Server-side filter > client-side** — For time-based filtering, MySQL NOW() - INTERVAL is more reliable than browser JS Date parsing. (#38)

### Business Logic
44. **`unwrap_response()` changes response structure** — Functions consuming API responses must NOT access `.data` again after unwrap. Use `data.get("bookings", [])` not `data.get("data", {}).get("bookings", [])`.
45. **`import X as Y` aliasing** — `import urllib.request as _urllib` means `_urllib` IS the module. Call `_urllib.urlopen()` not `_urllib.request.urlopen()`.
46. **Never duplicate financial calculation logic** — two endpoints, two different results (KBZ Bank: -30.2M vs -27.8M). Shared function eliminates divergence. Financial numbers must ALWAYS come from a single source of truth.

47. **Leave policy — any leave = forfeit attendance** — Boss clarified: attendance bonus is binary (present → full, absent → 0), not prorated. Extra penalty only applied when >2 days. (#47)
48. **Food profit = reuse PNL logic** — don't recalculate from sales_daily alone. PNL already has stock_out revenue + FIFO COGS = net profit. Same formula for salary commission. (#48)
49. **Rename carefully — check all code paths** — `food_charges`→`food_allowance` changed meaning from deduction to addition. Must update: SELECT query, variable names, deductions→additions, frontend labels, form fields. (#49)
50. **Gmail OAuth tokens expire** — refresh_token can be revoked after time. Need re-auth flow. Device flow not supported for "installed" type — use desktop redirect flow with Boss clicking link. (#50)

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

### Dashboard UX & Timeline Overhaul (June 26)
- Food Orders: timezone fix (UTC→MMT via CONVERT_TZ), sorting by Active-first + recency
- Sale Daily: added Time column between Date and Console
- Timeline: lane-based stacking rejected → tap-to-select popup approach (final)
- Cashflow: identified 2 bugs (month filter not applied, asset double-counting) — pending fix
- Key lessons: #28-32 (minified JS edits, Vite hashes, JS key sorting, lane stacking UX, window in templates)
- See `memory/2026-06-26.md` for full details

### Staff Salary System & Customer Notifications (June 27)
- Salary: full payroll auto-generation with leave tracking, shop-wide food commission (PNL FIFO COGS), game bonus tiers (1500/1800/2000hr), attendance rules per Boss policy
- Customer Noti: fixed staff Check-In & Staff Booking flows missing `_notify_customer()` calls
- Cancelled bookings: 2-hour timeline filter with server-side MySQL + frontend JS double-layer
- Gmail: OAuth token refreshed, salary structure emails sent to 2 staff
- Key lessons: #37-38 (JS Date parsing, server-side time filters), #47-50 (leave policy, food PNL reuse, rename checks, Gmail OAuth expiry)

## ⚠️ Known Issues (Persistent)

| Issue | Severity | Status |
|-------|----------|--------|
| Cashflow month filter not applied (Jun 26) | Medium | 🔴 Pending |
| Cashflow asset deduction double-count (Jun 26) | Medium | 🔴 Pending |
| VPS health monitor unreachable (Jun 28) | Low | 🟡 Investigating |

## Working Preferences

- **Language:** Burmese primary, English for tech terms
- **Timezone:** Asia/Yangon (UTC+6:30) — always convert for Boss
- **Delegation:** Always delegate complex tasks to sub-agents. Never do manually what a helper can do.
- **Fix protocol:** `python3 /root/coordination/fix_protocol.py --start <file>` before any code fix
- **Post-fix documentation:** Run `auto_doc_updater.py` + update daily memory + MEMORY.md
- **📁 New project onboarding (2026-06-25):** Every new project MUST include: (1) `README.md` at project root, (2) `memory/projects/<slug>/state.md`, (3) Daily memory section, (4) MEMORY.md entry, (5) `auto_doc_updater.py` commit
- **Sub-agent timeout:** 300s default

## 🆕 June 23, 2026 — Major Bug Fixes & Features

*(10+ fixes condensed — see git for full details. Key: food_cart_release stock_out fix, Move API start_time preservation, End Session confirm step, game_amt for booking_id paths, receipt template v3, Session Reminder 3-type fix, console_mgmt imports, Move Console menu layout.)*

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

### Key Technical Notes *(fixes #11-16 condensed)*
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

## Memory (2026-06-28)

### Sales Bot — Food Underscore Markdown Bug (3 Screens Fixed)
- **Bug:** Food item `လျှာဂျွမ်းထိုး_ဟော့ဟော့` had `_` interpreted as Markdown italic → `Can't parse entities` crash
- **Fix:** `_md_escape()` function in sales.py escapes `_`, `*`, `` ` ``, `[` — applied to **all 3 screens**: prompt_food_menu, step_food_qty, step_food_menu, prompt_confirm, _show_payment_review (Review), step_sale_confirm (Receipt)
- **Lesson:** Every screen that renders user content with `parse_mode="Markdown"` must escape. Apply at display time, not at storage time.

### Web Dashboard Booking Notifications — Missing
- **Bug:** Web dashboard uses `PUT /api/dashboard/bookings/{id}` which had NO notification code. Sales bot uses `PATCH /api/bookings/{id}/status` which HAS notification.
- **Fix:** Added customer notification (confirm/cancel) to dashboard PUT endpoint using `_send_telegram_customer()` via threading.Thread
- **Lesson:** Two endpoints for same action = divergence risk. Both need same side effects.

### Customer Bot — User Block System
- **Implement:** `BLOCKED_IDS` set + `_is_blocked()` check in cmd_start, cmd_menu, handle_menu_buttons
- **MessageHandler filter:** `filters.User(user_id=X) | filters.User(user_id=Y)` with group=-1
- **Block message:** "🚫 Access Denied — Contact Admin: @psvibeofficial"
- **Blocked:** 7158675982 (Unoman66/BK#1121), 8383666570 (BK#1122)
- **⚠️ Note:** CallbackQueryHandler does NOT accept filters — used in-handler checks instead

### EOD Report — Complete Rewrite
- **Bug:** `docker exec psvibe-mysql mysql` auth failed (password `!` → shell issues + host mismatch)
- **Fix:** Replaced with pymysql direct connect (`127.0.0.1`, same as API server)
- **English format:** All Burmese labels → English (per Boss)
- **Payment methods fix:** `GROUP BY SUBSTRING_INDEX(payment_method, ':', 1)` — previously grouping by `Cash:20000` instead of just `Cash`
- **Members table:** `members` (1 record, stale) → `member_wallets` (8 records, actual)
- **Cron:** `30 13 * * *` (8 PM MMT) → `30 15 * * *` (10 PM MMT)

### New Lessons
- **#51: docker exec mysql auth pitfalls** — Container internal MySQL client connects as different host (`127.0.0.1`) which may not match user privileges. Use pymysql from host instead.
- **#52: CallbackQueryHandler ≠ MessageHandler** — CallbackQueryHandler does NOT accept filters as constructor arg. Must use in-handler checks for blocking users.
- **#53: GROUP BY raw strings is wrong** — `GROUP BY payment_method` when column stores `Cash:20000` creates separate groups per amount. Use `SUBSTRING_INDEX()` to extract the method name.
- **#54: Two endpoints, same action = divergence** — `PUT /dashboard/bookings/{id}` and `PATCH /api/bookings/{id}/status` both update booking status but only one had notifications. Always check ALL paths.
- **#55: Check ALL tables after migration** — `members` table had 1 record after migration; `member_wallets` had 8 (correct). Don't assume legacy table names still have data.
