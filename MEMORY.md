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
61. **transfer_out stored as negative in cash_movements** — `SUM(amount)` for `transfer_out` returns negative. Use `+ SUM(transfer_out)` (adding a negative = subtracting), NOT `- SUM(transfer_out)` which double-counts. (#61)
62. **Cashflow opener/closing should use cumulative queries** — Don't compute `closing = opener + monthly_sections` when cash_movements aren't captured in sections. Use the same cumulative SQL formula for both opener (up to `_start`) and closing (up to `_end`). Sections provide breakdown but may not sum to net_change. (#62)
37. **JS Date(YYYY-MM-DDTHH:MM:SS) is LOCAL time** — Without Z/timezone suffix, interpreted in browser timezone. Always append Z for UTC DB timestamps. (#37)
38. **Server-side filter > client-side** — For time-based filtering, MySQL NOW() - INTERVAL is more reliable than browser JS Date parsing. (#38)
56. **Vue pages need `<AppLayout>` wrapper** — Pages rendered via router-view don't auto-inherit sidebar/nav. Must wrap in `<AppLayout title="...">` component or sidebar disappears. (#56)
57. **Dashboard uses JWT not x-api-key** — Dashboard authenticates via `apiClient` (axios with Bearer token from localStorage), not raw `x-api-key` header. Use `apiClient.get()` not `fetch()` with manual headers. (#57)
58. **Rebook logic: same phone + date + game → Done** — When a cancelled booking has a matching Done booking by same user on same date for same game, it's a rebook (not a failure). Exclude from cancellation count to get accurate success rate. (#58)
59. **Console breakdown excludes empty console_id** — Some bookings (especially early ones) have no console assigned. `console_id != ''` filter causes mismatch between total booking count and console breakdown sum. Document this delta, don't "fix" it — it's by design. (#59)
60. **ALL timestamps MUST be MMT (UTC+6:30)** — MySQL server runs on UTC, so `NOW()` and `CURRENT_TIMESTAMP` return UTC. For DATETIME columns: use `DATE_ADD(NOW(), INTERVAL 390 MINUTE)` in defaults and INSERTs. For TIMESTAMP columns: convert to DATETIME or set session `time_zone='+06:30'`. Never store UTC without conversion. Boss doesn't want to see 7:08 AM when it's really 1:38 PM. Tables affected: food_cart, sales_daily (fixed Jun 29), plus 50+ TIMESTAMP columns across all tables. (#60)
61. **Double conversion trap — check all 3 layers** — Fixing timezone on INSERT (storing MMT) without removing conversion from SELECT & API causes double-conversion (data ends up +13hrs ahead). Always check: (a) INSERT query, (b) SELECT/WHERE/GROUP BY queries, (c) API response formatting. Migrate old rows BEFORE removing SELECT conversions. One fix = all 3 layers. (#61)  
62. **Function truncation during replacement** — When using Python scripts to replace functions, verify boundaries with exact marker (`async def next_func`) and check that the closing block (comment_kb, edit_message_text, error handling) is present. Missing closing code = silent hang with no error log. (#62)

*(Trimmed: keeping only 3 most recent lessons)*

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
- Cashflow: identified 2 bugs (month filter not applied ✅ fixed Jul 1, asset double-counting — still pending)
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
| Cashflow month filter not applied (Jun 26) | Medium | 🟢 Fixed Jul 1 |
| Cashflow asset deduction double-count (Jun 26) | Medium | 🟢 Fixed Jul 1 — cumulative queries + transfer_out sign fix |
| PNL m-param ignored; Balance Sheet no date filter (Jul 1) | High | 🟢 Fixed Jul 1 |
| BS Member Liability = 0 (Jul 1) | High | 🟢 Fixed Jul 1 — undefined `ym` variable |
| VPS health monitor unreachable (Jun 28) | Low | 🟡 Investigating |

## Working Preferences

- **Language:** Burmese primary, English for tech terms
- **Timezone:** Asia/Yangon (UTC+6:30) — always convert for Boss
- **Delegation:** Always delegate complex tasks to sub-agents. Never do manually what a helper can do.
- **Fix protocol:** `python3 /root/coordination/fix_protocol.py --start <file>` before any code fix
- **Post-fix documentation:** Run `auto_doc_updater.py` + update daily memory + MEMORY.md
- **📁 New project onboarding (2026-06-25):** Every new project MUST include: (1) `README.md` at project root, (2) `memory/projects/<slug>/state.md`, (3) Daily memory section, (4) MEMORY.md entry, (5) `auto_doc_updater.py` commit
- **Sub-agent timeout:** 300s default

63. **PyMySQL `%%` escape for literal `%`** — `DATE_FORMAT(col, '%Y-%m')` fails because PyMySQL's `cur.execute()` treats `%Y`, `%m` as format placeholders. Must escape as `%%Y`, `%%m` in SQL strings. (#63)
64. **Check existing scripts before building new features** — The no-show auto-cancel script and cron job already existed. Always grep/inspect crontab and scripts/ folder first before planning work. (#64)
65. **Dashboard timer change must sync 3 layers** — DB (done), API timer (`schedule_session_timer`), Bot state (`_SESSION_END_TIMES`). Missing any one → reminder fires at wrong time. (#65)
66. **MySQL queries: ALWAYS Python pymysql, NEVER shell quoting** — docker exec + bash heredocs with nested quotes fails silently (5+ failed attempts for one query today). Python pymysql handles all quoting automatically and is 3x faster. Pattern: `python3 -c 'import pymysql; ...'` for ALL MySQL queries. (#66)

## Memory (2026-07-02)

### July 2 Sprint — 6 Features Delivered
- Console Swap: staff permission + booking ID/phone/notes detail cards
- Timer Duration Change: Hybrid fix — API timer reschedule + Bot auto-sync from DB every reminder fire
- ConsoleTimer: Custom minutes input ("✏️ Custom mins..." + Enter key support)
- Business Overview: All-time cumulative dashboard (8 sections, new CumulativeStats.vue)
- Cancel Flow: Admin group notification on cancel + customer self-cancel reminder cleanup
- Confirmed existing: Customer Bot confirmation, No-show auto-cancel (cron), Food Menu import

### All-Time Numbers (Jul 2)
- Total Revenue: ~13.3M Ks (Gaming 12.3M + Food 1.05M + Topup 450K)
- Total Bookings: 1,053 | Unique Members: 19

### Key Files Changed
- Dashboard: AppLayout.vue, SwapView.vue, ConsoleTimer.vue, CumulativeStats.vue (NEW), router/index.ts
- API: dashboard_routes.py (+timer reschedule, +cumulative endpoint)
- Sales Bot: session_reminder.py (+_sync_duration_from_db), booking_flow.py (+admin notify)
- Customer Bot: handlers.py (+reminder cancel)

## Memory (2026-07-01)
## Memory (2026-06-29)
## Memory (2026-06-28)
## Memory (2026-06-27)
## Memory (2026-06-26)
## Memory (2026-06-25)
## Memory (2026-07-01)

### Financial Statement July Fixes — 8 Bugs Fixed ✅
- **Morning session (4 bugs):** PNL `m` param ignored → parse year/month from `m`, replace `mmt.year/month` hardcodes. Finance Balances + Balance Sheet had no date filters → added year/month query params + WHERE clauses. Cashflow missing total_inflows/outflows → added computed fields.
- **Afternoon session (4 bugs):** BS Member Liability always 0 → undefined `ym` variable silently caught by `except:` catching. Cashflow investing section cumulative (no month filter) → added WHERE on all 4 asset/advance queries. Cashflow closing wrong (-19M) → formula missed capital + injects; changed to cumulative SQL queries. Cashflow closing 30M too high → `transfer_out` stored negative, `-SUM()` double-subtracted → changed to `+SUM()`.
- **Verification:** June 2026 PNL 11.7M, Topup 450K; CF opening 300M → net -288.7M → closing 11.32M; BS Member Liability 256,500 Ks. July 2026 all zeros (correct — no data yet).
- **Files:** `dashboard_routes.py`, `patch_routes.py`

### Customer Bot Notification Audit — 7 Paths Audited, 7 Gaps Found 🔍
Full audit of all notification paths when a customer creates a booking via Customer Bot.

| # | Critical Gap | Severity |
|---|-------------|----------|
| 1 | **Customer receives NO confirmation after booking creation** — No "သင်၏ Booking ကို အတည်ပြုပြီးပါပြီ" message | 🔴 High |
| 2 | **No proactive no-show auto-cancel** — No background job auto-cancels bookings when time passes without checkin | 🔴 High |
| 3 | **Inconsistent admin notifications on cancel** — `cmd_cancel_booking` and `_do_cancel_booking` don't notify admin group | 🟡 Medium |
| 4 | **`_text_cancel_booking` doesn't cancel reminders** — Uses different endpoint that doesn't trigger reminder cancellation | 🟡 Medium |
| 5 | **`_sbk_advance_reminder` sends at 30 min, not 10 min** — Docstring says 10 min, code uses `timedelta(minutes=30)` | ⚠️ Low |
| 6 | **Hardcoded admin chat ID** — `_notify_booking_received` uses hardcoded `-1003686032747` instead of env var | ⚠️ Low |
| 7 | **Double reminder on approve** — Both n8n webhook AND `_sbk_advance_reminder` schedule 30-min reminders | ⚠️ Low |

### Ongoing Work
- Notification gaps #1-7 from audit above — Boss to prioritize which to fix
- VPS health monitor: unreachable status still investigating

