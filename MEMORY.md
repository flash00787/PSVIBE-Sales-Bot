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
- **Staff Salary**: Auto-generate via `POST /salary/generate` — formula: base + transport + food_allowance + att_bonus + food_com + game_bonus − advances − leave_penalty
- **Member balance:** Column H of Card_wallet Google Sheet (legacy) → MySQL `member_wallets` (primary)
- **Receipts:** Burmese footer text must be removed
- **Coupon codes:** Valid samples: CBQVUHYG, CBANN6LD, CBZVNW7O, CBB292MP, CB7U617B

## 🧠 Critical Lessons Learned (Cumulative)

72. **Pydantic Optional[int] rejects empty string ""** — Before the function body even runs, Pydantic type coercion fails on empty strings for Optional[int] fields. Must add `@field_validator(mode="before")` to convert `""` → `None` for all Optional numeric/barcode fields. (#72)
73. **Logout: router.push + 401 interceptor = race condition** — When logout clears token and navigates, mounted pages still fire API calls → 401 → interceptor redirect → clash with in-progress navigation. Solution: interceptor skips 401 on /login path; logout uses full `window.location.href` for clean page reload. (#73)
74. **Old transactions need manual backfill after fix deployment** — Transactions created before a fix is deployed won't have the corrected data. Always check and backfill historical records after fixing payment/balance logic. (#74)

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
- See `memory/2026-06-27.md` for full details

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
5. **C2: Checkin Race Condition (Jul 3) 🐛→✅:** `SELECT ... FOR UPDATE` lock on `console_status` inside booking transaction.

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
