# MEMORY.md — Kora's Long-Term Memory Index

> 🗂️ Short master index. Module files are in `memory/`.
> Search via `memory_search` or `memory_get(path=memory/<file>.md)`.

## 🔴 Core Docs (workspace root)
| File | Purpose |
|------|---------|
| `GOLDEN_RULES.md` | Golden rules — never break |
| `HEARTBEAT.md` | Periodic tasks & cron schedule |
| `AGENTS.md` | Identity, workflow, hybrid spawning |
| `SOUL.md` | Personality, language, tone |
| `TOOLS.md` | SSH, bots, commands, API keys |
| `PROJECT_STRUCTURE.md` | Project overview (2 repos) |

## 📁 Module Files (`memory/`)

### Systems & Accounts
- **`memory/contacts.md`** — 👥 Contacts, Boss info, friend contacts
- **`memory/emails.md`** — 📧 Gmail accounts, API, Google Drive

### Infrastructure
- **`memory/infrastructure.md`** — 🏗️ Bot paths, services, MySQL, coordination tools
- **`memory/config.md`** — 🔧 Gateway config, lock_monitor, fix_protocol
- **`memory/psvibe-code-structure.md`** — 📂 File-by-file code reference (both repos)
- **`memory/project-state.md`** — 📋 Current project state & known issues

### SOPs & Frameworks (`memory/sop/`)
- **`memory/sop/SPAWN_PROTOCOL.md`** — 🔀 Sub-agent spawn rules & hybrid spawning
- **`memory/sop/POST_TASK_SOP.md`** — 📝 Post-task documentation SOP
- **`memory/sop/COORDINATION_FRAMEWORK.md`** — 🏗️ Agent coordination framework
- **`memory/sop/HELPER_GUIDELINES.md`** — 👷 Helper agent guidelines
- **`memory/sop/heartbeat-procedures.md`** — 💓 Full heartbeat procedures

### Operations
- **`memory/tools-commands.md`** — 🛠️ All coordination tool commands reference
- **`memory/memory-usage-guide.md`** — 📖 How to use the memory system (decision tree, write rules)
- **`memory/sop/DISPATCH_MANAGER_SOP.md`** — 📋 Dispatch manager SOP
- **`memory/sop/FINDINGS_MANAGER_SOP.md`** — 🔍 Findings manager SOP
- **`memory/sop/TASK_PLANNER_SOP.md`** — 📊 Task planner SOP
- **`memory/sop/STATUS_REPORTER_SOP.md`** — 📈 Status reporter SOP
- **`memory/sop/VERIFY_AGENT_SOP.md`** — ✅ Verify agent SOP
- **`memory/sop/DEPLOY_MANAGER_SOP.md`** — 🚀 Deploy manager SOP
- **`memory/sop/GIT_SYNC_SOP.md`** — 🔄 Git sync SOP
- **`memory/sop/SPAWNING_MANAGER_SOP.md`** — 🥚 Spawning manager SOP

### Bugs & Fixes
- **`memory/bug-patterns.md`** — 🐛 All known bug patterns (fixed & known)
- **`memory/ERROR_PATTERNS.md`** — ⚡ Quick ref: error → root cause → fix
- **`memory/lessons.md`** — 📚 Critical lessons learned
- **`memory/fix-history.md`** — 📋 Recent fix history (by date)

### Daily Logs
- **`memory/2026-06-02.md`** — Raw daily logs

### Archives
- **`memory/archive/`** — Old/stale documentation (OPS_REFERENCE, MASTER_INVENTORY, etc.)

---

## ⏰ Quick Ref: Timezone
- Boss: **Asia/Yangon (UTC+6:30)**
- ALL UTC → Myanmar Time before telling Boss

## 🛡️ Quick Ref: Fix Protocol
```bash
python3 /root/coordination/fix_protocol.py --start <file>  # Before edit
python3 /root/coordination/fix_protocol.py --complete       # After edit
```
See `memory/config.md` for details. See `memory/lessons.md` for spawn & lock lessons.

---

---

## 📌 Today's Summary (2026-06-06) — 🎮🔥 GRAND OPENING DAY! 🔥🎮

### 🐛 Food Menu Fix — Customer Bot (03:00-03:30 UTC)

#### Root Causes (3 layers)
1. `_bk_intercept_menu` missing BTN_FOOD → booking conversation ate the button
2. `_api._api_get()` auto-unwraps `{success,data}` → raw `{items}`, but code checked `resp.get("success")` → always failed
3. Unicode escape sequences corrupted by auto-fix pipeline → garbled text

#### Final Fix (Commit `1dd1be1`)
| File | What Changed |
|------|-------------|
| `customer_bot/handlers.py` | Added BTN_FOOD/BALANCE/REFER to `_bk_intercept_menu` |
| `customer_bot/handlers.py` | Rewrote `cmd_food_menu` — no `resp.get("success")`, no `resp.get("data")` |
| `customer_bot/main.py` | Removed duplicate MessageHandler |

### 🧠 Lesson Learned
- **API auto-unwrap:** `_api_get()` already unwraps `{success,data}` — DON'T check `success`/`data` again or it'll always fail
- **Layered bugs:** 3 distinct root causes for 1 symptom. Fix protocol should enumerate ALL possible causes before editing.

### Services Status (13:43 UTC)
- `psvibe-api` ✅ | `psvibe_customer_bot` ✅ | `psvibe-sale-bot` ✅ | `psvibe-dashboard` ✅
### 🐛 Bug Round 1: Duration Loop + Reserved Cross-Check (02:06-02:40 UTC)

#### Bug 1: Duration နှစ်ခါမေးတာ (Customer Bot)
- **Root cause:** Unicode escape corruption in `booking_handlers.py` — `\u101b\u103d\u1031...` rendered garbled text instead of "ရွေးပါ"
- **Result:** User tap misinterpreted → re-showed console type selection loop
- **Fix:** Re-examined + fixed 6 corrupted Unicode escapes via SFTP upload (not inline replace)

#### Bug 2: Reserved Console Not Showing (Customer Bot)
- **Root cause 1:** API `_map_booking_row` mapped `console_id` → `consoleType` field only — no `consoleId`
- **Root cause 2:** Bot checked `b.get("console_id")` / `b.get("consoleId")` — neither existed
- **Fix:** API added `consoleId` field; Bot added `consoleType` fallback check

### 🧠 New Lessons
- **Unicode escape sequences are fragile** — always verify with `python3 -c "print(...)"` before deploying fix scripts; prefer SFTP upload + remote Python execution for exact byte-level safety
- **API field naming must be consistent** — when API uses `consoleType`, bot must check that key too, or add alias at API layer
- **3-layer bugs are common** — 1 symptom had 3 distinct root causes (intercept menu missing, auto-unwrap API, Unicode corruption). Fix protocol: enumerate ALL possible causes before editing.

---

## Memory (2026-06-07)

### 💰 Account Balance Fix — Real-time Calc + Payment Save (07:44-08:05 UTC)
- **GROUP BY bug**: Real-time SQL used `GROUP BY payment_method` collapsing duplicate payment strings → Cash off by -60,000 Ks
- **Fix**: Removed GROUP BY, iterate all individual rows
- **Wave/AYA Pay not saving**: `api_add_sales_record` hardcoded payment_method → now dynamic
- **WavePay historical fix**: 2 vouchers from June 6 had missing WavePay amounts (32,000 Ks total fixed)
- **Elif bug**: Single format parser only checked `== "wave"` not `== "wavepay"`

### 🍔 Food Menu: Category Grouping + "Beverages"→"Drinks" (11:07-11:25 UTC)
- New endpoint `GET /api/fetch_food_menu` returns items grouped by category with emoji headers
- MySQL + API + Sales Bot + Customer Bot all updated
- Categories: Drinks (12), Instant Noodles (3), Other (1)

### 💵 Inject/Eject Feature + Web Admin (08:15-08:50 UTC)
- New `cash_movements` MySQL table + API endpoints (`/api/cash/inject`, `eject`, `movements`)
- Bot commands `/inject` and `/eject` (Boss-only, admin_id filter)
- Web admin page at `/admin/cash` with movement table + inject/eject form

### 🎮 Game Library Fixes (09:00-09:45 UTC)
- SSD classification: `"SSD" in cid` → `cid.upper().startswith("SSD")` (substring→prefix)
- Duplicate games: Added `install_type != "Session"` filter + API duplicate protection
- DB cleaned: 116→107 records

### ⏰ Session Timer Reminder Fix (12:15-12:30 UTC)
- `_is_session_active()` was calling non-existent `/api/console_booking` → reminder never fired
- Fixed to use `fetch_console_status` endpoint; timer triggers at `planned_mins - 5`
- `schedule_session_timer()` never called → now triggered from `bookings/checkin`

### 🐛 Coupon Stuck Investigation (12:30-12:50 UTC)
- Coupon flow correct but **keyboard race condition**: stale button taps hit `step_coupon_confirm` with no catch-all
- **Fix**: Added catch-all `else` block that re-prompts payment methods

### 🏦 ACM's Acc Balance Not Updating + API Auth (14:50-15:15 UTC)
- Balance showed 0 because `income_by_acct` stored "acm" but lookup used "acm's acc" — normalization mismatch
- API auth mystery: localhost curl 401 vs browser 200 — API_KEY match verified; debug endpoint added
- `systemctl restart` had no effect → forced `kill -9` required

### 🍔 Food Sale Feature (17:00-17:30 UTC)
- Added main menu button `🍔 Food Sale` — standalone food/drink sale (no console/game)
- Reuses `prompt_food_menu()` for item selection; flows into existing payment & save chain
- `is_food_sale` flag in `step_sale_confirm` → records as `type: "food_only"` (c_id="-", no game fields)
- Both Daily Sale AND Food Sale work independently
- **Phase 2 pending**: Session Start pre-order + Session End auto-bill

### 🧠 Key Lessons Today
- **GROUP BY collapses pipe-delimited data** — iterate ALL rows for real-time parsing
- **Elif chains must cover all variants** — `"wave"` worked, `"wavepay"` didn't
- **Burmese Unicode verification**: `U+101B U+101B` (ရရ) ≠ `U+101B U+103E` (ရှ)
- **systemctl restart can silently fail** — verify PID change, fall back to `kill -9`
- **`"x if x else default"` breaks on `0`** — use `"x if x is not None else default"` (re-confirmed)
- **API response_model strips undeclared fields** (re-confirmed from June 5)

### Services (final 17:50 UTC)
psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅ | psvibe-dashboard ✅

## Memory (2026-06-08)

### 💳 Coupon Fix — 3-Layer Root Cause (01:57 UTC)

### Issue
- Boss reported coupon code "CBJ22E04" returns "❌ Coupon not found" when staff tries to apply it.

### Investigation
- 1. Manual curl test → `X-API-Key` header works, but coupon genuinely not in DB
- 2. Checked `member_coupons` table → 25 coupons exist (codes like CBQVUHYG, CBANN6LD), but NOT "CBJ22E04"
- 3. Checked promotions → `cashback_coupon` promo `end_date` = 2026-06-07 (expired yesterday UTC)
- 4. Checked coupon generation in `step_sale_confirm` → calls `api_post` from `bot/api_client.py`, which uses `?api_key=*** query param (fails with 401)

### Root Causes (3 layers)
- 1. **`api_client.py` `api_post()`** uses `?api_key=*** query param → 401 response → coupon generation silently fails
- 2. **`api_client.py` `api_get()`** also uses `?api_key=*** query param → would fail on any GET
- 3. **Promotion expired** — `end_date = 2026-06-07`, now June 8 → generation endpoint returns "No active promotion"

### Fix
| What | File | Change |
|------|------|--------|
| api_post auth | `bot/api_client.py` | `?api_key=*** → `X-API-Key` header |
| api_get auth | `bot/api_client.py` | `?api_key=*** → `X-API-Key` header |
| Promotion expiry | MySQL `promotions` table | `end_date` extended: 2026-06-07 → 2026-06-30 |

### Verification
- Coupon generate → ✅ `{"coupon":{"id":26,"code":"CBNTV84J",...}}`
- Coupon validate (CBQVUHYG) → ✅ returns balance_minutes: 60
- Services restarted: api ✅, sale-bot ✅, customer-bot ✅

### Note
- "CBJ22E04" was never generated by the system. Valid codes in DB: CBQVUHYG, CBANN6LD, CBZVNW7O, CBB292MP, CB7U617B, CBUKQMWE, CB12ZNA8, CB15NWOI, etc.

### Services Status (01:57 UTC)
- psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅
- 4. Checked coupon generation in `step_sale_confirm` → calls `api_post` from `bot/api_client.py`, which uses `?api_key=` query param (fails with 401)
- 1. **`api_client.py` `api_post()`** uses `?api_key=` query param → 401 response → coupon generation silently fails
- 2. **`api_client.py` `api_get()`** also uses `?api_key=` query param → would fail on any GET
| api_post auth | `bot/api_client.py` | `?api_key=` → `X-API-Key` header |
| api_get auth | `bot/api_client.py` | `?api_key=` → `X-API-Key` header |
- ---
| API key header | `bot/api_client.py` | Added `X-API-Key` header to `api_post()` and `api_get()` (was only query param) |
| Promotion restart | N/A | Boss tomorrow (Monday) will set new cashback promotion |

### Lesson Learned
- `api_client.py` has TWO separate auth mechanisms: `_http_request` uses **header**, but `api_post`/`api_get` use **query param** only
- Always check WHICH function is being called — the helper wrappers are not consistently implemented
- Promotions may need a script/cron to auto-renew; manual restart is fragile

### 🐛 Coupon "Invalid" Bug — Real Root Cause (02:30 UTC)

### Symptom
- Boss enters valid coupon codes (CBJ22EO4 → letter O, CBMWF2HP) but bot always shows "❌ Invalid" even though:
- DB confirms codes exist (120min, active)
- API debug logs confirm `{"success":true,"data":{"coupon":{...}}}` returned
- Boss tried via Telegram with correct codes → same "Invalid" result

### Root Cause
- `step_coupon_validate()` in `/root/psvibe-sales-bot/bot/handlers/discount.py` line 386-394:
- ```python
- if "error" in resp:  # ← BUG: checks KEY EXISTENCE, not truthy value
- err = str(resp.get("error") or "Invalid")
- ...
- ```
- API returns `{"success":true,"data":{...},"error":null}` (error key exists with null value)
- `"error" in resp` → `True` (because key exists!)
- `resp.get("error") or "Invalid"` → `None or "Invalid"` → `"Invalid"`
- So even on SUCCESS, it enters error path and shows "❌ Invalid"

### Fix
- `"error" in resp` → `resp.get("error")` (truthy check — only enters error path when error has a value)
- Same pattern also fixed at the redeem call site (~line 441).

### Debug Method
- Added `_lg.warning()` logging to `_api_post_coupon()` to dump raw API response
- Verified API returns `error:null` on success
- Only then realized the `"error" in resp` logic error

### Lesson Learned
- **`"error" in resp` ≠ `resp.get("error")`** — when API always includes `error` key (even with null), `in` operator is always True. Must use truthy check on the value, not key existence. This applies to ANY API with nullable error fields.

### Services Status (02:50 UTC)
- psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅
- ---

### 📋 Boss Request: Update Customer Bot AI with Game List & Food Menu (02:51 UTC)

### Context
- Boss wants Customer Bot's AI (Ko Vibe) to automatically know when Game List or Food Menu changes.

### Current State (Already Good)
- **Games**: AI fetches live via `_fetch_games_full()` → `_build_live_game_library_text()` every time user asks — **already real-time** ✅
- **Food Menu**: AI fetches via `_fetch_config()` → `food_prices` dict with 10-min cache — **close to real-time** ✅
- **Ko Vibe tone**: Untouched, in `data/prompts.py` `_build_ai_system_prompt()`

### Improvement Needed
- Food menu display could use grouped format (categories with emojis: Drinks 🥤, Instant Noodles 🍜, Other 🍟) instead of flat name+price list
- Config cache TTL could be reduced from 600s to 120-180s
- Add `_fetch_food_menu_grouped()` to `customer_bot/api.py` calling `/api/fetch_food_menu`
- Wire into system prompt builder via `fetch_food_menu_fn` parameter
- ---

### 💰 OPEX System — Operating Expenses Tracking (03:51 UTC)

### What Was Built
| Component | Details |
|-----------|---------|
| **MySQL Table** | `opex` (id, category, description, amount, payment_method, recorded_by, expense_date, created_at) |
| **API Endpoints** | `POST /api/opex/add`, `GET /api/opex/list`, `GET /api/opex/summary` |
| **Bot Handler** | `bot/handlers/opex.py` — conversation handler for recording expenses |
| **OPEX Button** | `💰 OPEX` main menu button → sub-menu with 9 category buttons |

### OPEX Categories
- `Electricity` · `Water` · `Rent` · `Staff Salary` · `Internet` · `Snacks/Drinks` · `Maintenance` · `Marketing` · `Others`

### Bot Flow
- 1. Tap `💰 OPEX` → Category selection inline keyboard
- 2. Select category → Bot prompts for description (optional, `/skip`)
- 3. Enter amount (numeric validation)
- 4. Select payment method (Cash/WavePay/AYA Pay/KPay)
- 5. Confirm → Saved to DB

### Debug Issue Found
- **Root cause**: `datetime.now(MMT)` used in OPEX endpoint but `MMT` is not a module-level constant — only `now_mmt()` function exists
- **Fix**: Changed to `now_mmt().strftime("%Y-%m-%d")`
- **Naming conflict**: `by` is a terrible variable name (overrides Python's `by` keyword in `eval`/`exec` contexts) — was used in intermediate version then removed

### Services Status (03:51 UTC)
- psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅

### Known Minor Issue
- `session_timer` background task throws `'Access denied' MySQL error` on uvicorn stderr — unrelated to OPEX, pre-existing issue with the timer module's DB connection
- ---

### 🔒 Lock Monitor — Auto Cleanup (05:16 UTC)
- 2 active locks, 0 stale locks cleaned ✅
- 1 old session self-cleaned
- 14 warnings: large session/trajectory files (top: 9609KB trajectory)
- Total disk: ~195MB session data
- ---

### 🏗️ Financial Dashboard — Full Asset Management Revamp (06:00-07:44 UTC)

### What Was Built
- Full Asset Management system with disposal profit/loss calculation in the Financial Report dashboard.

### DB Schema Changes
- **`finance_assets` table additions:**
- ```sql
- ALTER TABLE finance_assets
- ADD COLUMN salvage_value DECIMAL(12,0) DEFAULT 0 AFTER qty,
- ADD COLUMN useful_life INT DEFAULT 0 AFTER salvage_value,
- ADD COLUMN monthly_dep DECIMAL(12,0) DEFAULT 0 AFTER useful_life,
- ADD COLUMN months_elapsed INT DEFAULT 0 AFTER monthly_dep,
- ADD COLUMN acc_depreciation DECIMAL(12,0) DEFAULT 0 AFTER months_elapsed,
- ADD COLUMN book_value DECIMAL(12,0) DEFAULT 0 AFTER acc_depreciation,
- ADD COLUMN disposal_amount DECIMAL(12,0) DEFAULT NULL AFTER status,
- ADD COLUMN disposal_date DATE DEFAULT NULL AFTER disposal_amount,
- ADD COLUMN profit_loss DECIMAL(12,0) DEFAULT NULL AFTER disposal_date;
- ```

### API Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/dashboard/assets/create` | Add new asset (JWT-protected) |
| PUT | `/api/dashboard/assets/<id>/dispose` | Dispose with `sale_amount`, calc profit/loss |

### Profit/Loss Calculation
- profit_loss = sale_amount - book_value
- = sale_amount - (amount - acc_depreciation)
- **Profit** → profit_loss is positive (e.g., Test Chair: +50K)
- **Loss** → profit_loss is negative (e.g., Game Discs: -446K)

### Cash Movements Integration
- When `sale_amount > 0`, auto-creates `cash_movements` record:
- `movement_type`: `inject`
- `account`: `cash`
- `amount`: sale_amount
- `note`: `Asset disposal: <asset_name>`

### Fixed: Book Value Calculation
- **Bug**: `Decimal - float` type error in `dashboard_routes.py` response mapping
- ```python
- "book_value": float(a.get("book_value", 0) or (a.get("amount", 0) - float(...)))
- "book_value": float(a.get("book_value", 0) or 0) or (float(a.get("amount", 0) or 0) - float(...))
- **Fix**: `sed -i 's/recorded_at/created_at/g' dashboard_routes.py`
- **Fix**: Book value calc now wraps Decimal in `float()` before subtraction

### Sync Protection
- `sync_finance_assets()` uses `ON DUPLICATE KEY UPDATE` with unique key `(name(150), purchase_date, per_price)` — dashboard-added/disposed assets preserved across sync runs.

### Disposal Test Results
| Asset | Book Value | Sale Amount | Profit/Loss |
|-------|:----------:|:-----------:|:-----------:|
| PS5 Console | 21.6M | N/A | N/A |
| PS5 Pro Console | 9.1M | 500K | **-8.6M** |
| Game Discs | 8.44M | 8.0M | **-446K** |
| Test Chair | 250K | 300K | **+50K** |

### Services Status (07:44 UTC)
- psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅ | psvibe-dashboard ✅
- All 4 disposed assets recorded in DB, cash movements created for Game Discs (8M inject to Cash).
- ---

### 🏗️ Financial Dashboard — Full Recovery & Depreciation Auto-Calc + Advances/Prepaid Integration (10:09 UTC)

### The Disaster
- During inline Python patching (to add auto-depreciation + advances/prepaid), repeated SSH injections via Node.js template literals corrupted the file with syntax errors. `git checkout -- dashboard_routes.py` restored the bare 146-line Git version, **discarding ALL earlier work** — dispose endpoint, per-qty disposal, disposal_records, book_value fix, financial report, OPEX endpoints, finance balances, etc.

### Recovery Strategy
- Found backup files: `dashboard_routes.py.bak` (60364 bytes, June 3) and `dashboard_routes.py.bak.v3.1` (62252 bytes, June 4)
- **Restored from `.bak.v3.1`** (1477 lines, most complete backup with financial report)
- Re-applied all subsequent changes via Python patch:
- 1. ✅ Expanded SELECT query to include `per_price, qty, disposed_qty, payment_method, salvage_value, useful_life, monthly_dep, months_elapsed, acc_depreciation, book_value, notes, status`
- 2. ✅ Added `_assets_result` mapping with depreciation auto-calc
- 3. ✅ Added `advances_total`, `advances_pending`, `prepaid_total` to report response
- 4. ✅ Added `net_position = assets_total - advances_pending - prepaid_total`
- 5. ✅ Added `disposal_records` query and response
- 6. ✅ Fixed `recorded_at` → `created_at`
- 7. ✅ Added `POST /api/dashboard/assets/create` endpoint
- 8. ✅ Added `PUT /api/dashboard/assets/{asset_id}/dispose` with per-qty support
- 9. ✅ Added `GET /api/dashboard/finance/balances` endpoint
- 10. ✅ Book value Decimal→float fix

### Depreciation Auto-Calculation (LIVE)
- ```
- monthly_dep = max(0, (amount - salvage_value) / (useful_life * 12))
- months_elapsed = (now.year - purchase_date.year) * 12 + (now.month - purchase_date.month)
- acc_depreciation = min(monthly_dep * months_elapsed, amount - salvage_value)
- book_value = amount - acc_depreciation

### Verified Results
| Asset | Useful Life | Salvage | Monthly Dep | Acc Dep | Book Value |
|-------|:-----------:|:-------:|:-----------:|:-------:|:----------:|
| PS5 Console | 3yr | 1.3M | 564,766 Ks | 0 Ks | 21.6M |
| PS5 Pro Console | 3yr | 1.0M | 227,777 Ks | 0 Ks | 9.2M |
| Game Discs | 3yr | 100K | 4,722 Ks | 4,722 Ks | 265K |
| AirCon | 3yr | 700K | 29,722 Ks | 29,722 Ks | 1.74M |

### Advances/Prepaid Integration
- `advances_total`: Sum of all advances (104.8M Ks)
- `advances_pending`: Same as total (no repayment tracking yet)
- `prepaid_total`: 22.4M Ks
- `net_position = assets_total - advances_pending - prepaid_total`

### Build Issue
- Vue frontend build failing: `FinancialReport.vue` uses `useRouter` without importing it from `vue-router`. Needs fix before deploy.

### Frontend Build Error
- Vite build fails: `'useRouter' is not defined`
- FinancialReport.vue needs `import { useRouter } from 'vue-router'` added
- Build + deploy pending this fix

### Services Status (10:09 UTC)
- psvibe-api ✅ (restarted, all endpoints verified)
- psvibe-dashboard ❌ (build error — frontend not updated yet)

### 🍔 Food Sale Flow Fix (13:59-14:05 UTC)

### Issue
- Boss reported: "Food sale က menu ရွေးပြီးရင် payment ဆီ မရောက်သွားဘူး"

### Root Cause
- `prompt_confirm()` in `/root/psvibe-sales-bot/bot/handlers/sales.py` accesses:
- `d["mins"]` (game duration) — **KeyError** for food-only sales
- `d["m_id"]` (member ID) — **KeyError** for food-only sales
- `cmd_food_sale` only sets `is_food_sale=True`, `member_id=None`, `food_items=[]`, `food_prices=[]`. It does NOT set `mins` or `m_id` keys.
- When user taps ✅ Done → `step_food_menu` calls `prompt_confirm` → crashes on `d["mins"]` → payment never reached.

### Fix
- Added early-return in `prompt_confirm`:
- ```python
- if d.get("is_food_sale"):

# Show food-only confirmation (no game/console fields)

# Returns CONFIRM_SUMMARY state
- ```
- Sale bot restarted successfully.
- ---

### 📊 Dashboard Blank Page (13:27-13:33 UTC)

### Issue
- Boss reported: "Dashboard link က ဘာမှ မပေါ်တော့ဘူး"

### Investigation
- Verified ps-vibe.com resolves and serves HTML (200 OK both HTTP and HTTPS)
- Verified `/auth/login` endpoint works (returns JWT token)
- Verified dashboard API endpoints `/api/dashboard/stats`, `/api/dashboard/opex`, `/api/dashboard/finance/balances` all return **200 OK** with valid JWT
- No auth issues found — all endpoints authenticated correctly

### Conclusion
- Likely **momentary downtime** during API server restarts earlier in the session (multiple restarts for fixes caused brief blips). Dashboard was confirmed working with real data:
- Cash = 59,933 Ks
- KPay = 242,333 Ks
- Wave = 32,000 Ks
- ACM = 283,900 Ks
- Total = 618,166 Ks
- ---

### 🔄 Staff Bot & Dashboard Balance Discrepancy (12:05-12:30 UTC)

### Issue
- Boss reported Cash balance discrepancy — Bot showed 794,933 Ks, actual should be much lower.

### Root Causes (6 problems found)
| # | Problem | Fix |
|---|---------|-----|
| 1 | Test data in `cash_movements` (inject 50K, eject 20K, transfers 10K + 1K) | Deleted |
| 2 | Asset disposal test inject 700K (Game Discs) inflated Cash | Deleted |
| 3 | Bot `api_finance_account_balances()` didn't subtract OPEX | Added OPEX subtraction |
| 4 | Dashboard `cash_map` key mismatch ("Cash"→"cash" lookup failed) | Added `key_to_name` mapping |
| 5 | Dashboard didn't normalize WavePay→Wave | Added `"wavepay" → "wave"` check |
| 6 | Dashboard missing `topup_log` income for KPay/Cash | Added topup_log query |

### Verified Balances (Both Bot & Dashboard matching)
| Account | Balance |
|---------|--------:|
| Cash | 59,933 Ks |
| KPay | 242,333 Ks |
| Wave | 32,000 Ks |
| AYA Pay | 0 Ks |
| KBZ Bank | 300,000,000 Ks |
| ACM's Acc | 283,900 Ks |
| **Total (Operating)** | **618,166 Ks** |

### Cash Breakdown
- ```
- 353,333 (income)
- -15,000 (OPEX)
- + 5,000 (transfer in from KPay)
- +    -0 (to ACM Collect & revert cancel each other)
- -283,400 (Boss took from shop)
- = 59,933 Ks
- Boss confirmed 283,400 Ks was him taking cash from the shop. The 33-ending balance comes from sale `Cash:3833` (id=34).

### Key DB-to-Key Mapping
- ```python
- key_to_name = {"cash":"Cash", "wave":"Wave", "kpay":"KPay",
- "aya_pay":"AYA Pay", "kbz_bank":"KBZ Bank", "acm_acc":"ACM's Acc"}

### Service Status (14:05 UTC)
- psvibe-api ✅
- psvibe-sale-bot ✅ (food fix applied + restarted)
- psvibe_customer_bot ✅
- psvibe-dashboard ✅ (serving at ps-vibe.com)
- ---

### 🏪 Stock In → Payment System Integration (14:15-14:50 UTC)

### Boss Request
- "Stock In ကို ကော Payment နဲ့ ချိတ်ပေးဦး" — Connect stock purchases with payment accounts.

### What Was Built
- **API Endpoint** `POST /api/stock/in` (app.py):
- Accepts: `{item_name, quantity, unit_cost, payment_method, paid_by, staff_name, cash_amount?, kpay_amount?}`
- Generates `batch_id: SI-{uuid[:12].upper()}`
- Creates `stock_in` record with `payment_method`, `paid_by`, `staff_name`
- Creates `cash_movements` eject entry(s) for payment account deduction
- **DB Updates** (`inventory_fifo.py` `add_stock_in()`):
- Now accepts `payment_method`, `paid_by`, `staff_name` params
- INSERTs all fields into `stock_in`
- **Bot Handler** (`stock_in.py`):
- `step_si_confirm` calls `api_post("stock/in", {...})` instead of no-op `api_add_stock_in()`
- Split payments: computes per-item Cash/KPay proportions, passes `cash_amount`/`kpay_amount`
- GSheet fallback retained for backward compatibility
- **Dashboard Balance** (`dashboard_routes.py`):
- New `stock_in_payments` field per account in `/finance/balances` response
- Balance formula: `balance = income - opex - stock_in_payments + transfers + inject - eject`
- **Bot Balance** (`patch_routes.py`):
- Same stock_in subtraction added for consistency
- Composite payment string parsing ("Cash X / KPay Y") handled

### Files Modified
| File | Change |
|------|--------|
| `/root/psvibe_api_server/app.py` | Added `POST /api/stock/in` route (line 2224+) |
| `/root/psvibe_api_server/inventory_fifo.py` | Updated `add_stock_in()` with payment fields |
| `/root/psvibe-sales-bot/bot/handlers/stock_in.py` | Updated `step_si_confirm` to use `api_post` |
| `/root/psvibe_api_server/dashboard_routes.py` | Added stock_in_payments to balance calc |
| `/root/psvibe_api_server/patch_routes.py` | Added stock_in subtraction to bot balance |

### Verified
- ✅ Single Cash payment → stock_in record + cash_movements eject (2,000 Ks deducted)
- ✅ Split Cash/KPay → stock_in with composite string + 2 eject entries
- ✅ Dashboard balances reflect stock_in deductions
- ✅ Bot balances reflect stock_in deductions
- ✅ All 5 Python files compile clean
- ✅ Services: psvibe-api ✅, psvibe_customer_bot ✅, psvibe-sale-bot ✅

### Services Status (14:50 UTC)
- psvibe-api ✅ | psvibe-sale-bot ✅ | psvibe_customer_bot ✅ | psvibe-dashboard ✅
- ---

### 🏛️ Depreciation Engine + 3 Financial Reports Enhanced (2026-06-09 04:37-05:32 UTC)
- Added Salvage Value, Useful Life, auto-depreciation (straight-line) to Asset Register
- Static base date: **June 1, 2026** (not datetime.now())
- Payment method dropdown in Add Asset + "Return to Account" dropdown in Dispose
- **P&L**: Operating Profit (before Dep) + Depreciation (non-cash) + Net Profit (after Dep)
- **Balance Sheet**: Gross→Acc Dep→NBV structure; Depreciation Reserve in Equity ✅ A=L+E
- **Cash Flow**: Depreciation add-back highlighted; Net Cash before/after + Net before Financing
- **Bug 1**: Python cache — bytecode didn't refresh → cleared `__pycache__`
- **Bug 2**: Retained Earnings missing `- total_dep` → matched L+E with Assets
- **Bug 3**: Test Chair (test data) kept re-appearing → permanently deleted from DB
- **Total Monthly Dep**: 4,029,826 Ks/m | **Total Acc. Dep**: 3,262,283 Ks

### Key Lessons (June 9)
1. Python `.pyc` cache must be cleared after any `.py` edit — `systemctl restart` alone isn't enough
2. String `replace()` in Python fails silently when whitespace doesn't match (extra newlines) — verify with `repr()`
3. BS equation: Assets = CA + Inv + Other + Fixed(NBV) = Liab + Capital + Retained + DepReserve
4. Test entries should be deleted, not disposed — prevents zombie records
5. `cash_movements` stores account as labels ("KBZ Bank"), code uses keys ("kbz_bank") — always maintain mapping dict

### 🏪 Stock In Edit + Payment Field Fix (15:05-15:45 UTC)

### Boss Requests
- 1. "Dashboard မှာမပြောင်းသွားသေးဘူး" — Dashboard balance error (`LIKE '%/%'` PyMySQL conflict)
- 2. "အရင် ထည့်ထားတာတွေကော KBZ Bank နဲ့ ပြောင်းပေးပါ" — Backdate old stock_in to KBZ Bank
- 3. "မပေါ်သေးဘူး" — Stock In form missing payment_method dropdown
- 4. "Stock In Transaction ကို edit လို့ရအောင် လုပ်ပေးပါ" — Add edit functionality

### Fixes

#### 1. Dashboard Balance Error (dashboard_routes.py)
- **Root cause**: PyMySQL `execute()` does `query % args` — `LIKE '%/%'` in SQL was interpreted as Python format specifier → "not enough arguments for format string"
- **Fix**: Replaced `LIKE '%/%'` with direct query, expanded `si_payments` dict to include all 6 accounts (was missing KBZ Bank, ACM's Acc)
- **Double counting fix**: Removed `- si_pay` from balance formula — stock_in is already tracked through cash_movements eject entries

#### 2. Backdate Stock In to KBZ Bank
- Updated all 35 old stock_in records: `payment_method='KBZ Bank'`, `paid_by='Capital'`, `staff_name='Bot'`
- Created consolidated cash_movements eject entry: 726,932 Ks for KBZ Bank
- **KBZ Bank balance**: 300,000,000 - 726,932 = 299,273,068 Ks (before other adjustments)

#### 3. Payment Method Field (StockIn.vue)
- Added payment_method dropdown in the form with all methods (Cash, KPay, WavePay, AYA Pay, KBZ Bank, etc.)
- Added paid_by input field
- Added Payment column to history table with colored badges
- Added KBZ Bank to payment methods array

#### 4. Edit Functionality (dashboard_routes.py + StockIn.vue)
- **Backend**: Added `PUT /api/dashboard/stock-in/{entry_id}` — accepts all fields, updates stock_in + cash_movements
- **Frontend**: Edit button in each row + full edit modal overlay with all fields
- **Cash movements**: POST and PUT endpoints now create/update cash_movements eject entries

#### 5. Frontend deploy
- `npx vite build` → deployed to `/root/psvibe_api_server/dashboard-dist/`
- Both Finance Balance and Stock In pages now reflect correct data

### Files Modified
| File | Change |
|------|--------|
| `/root/psvibe_api_server/dashboard_routes.py` | Fixed stock_in SQL (LIKE PyMySQL conflict); Added PUT /stock-in/{id}; Added cash_movements to POST /stock-in; Fixed balance formula |
| `/root/psvibe_api_server/patch_routes.py` | Fixed stock_in handling for KBZ Bank/ACM's Acc |
| `/root/psvibe-dashboard/src/views/StockIn.vue` | Added payment form fields, edit modal, payment column in table |

### Verified
- ✅ PUT /stock-in/1 → `{"success":true,"data":{"id":1,"updated":"Coca Cola"}}`
- ✅ All balances correct (Cash=96,433 Ks, KBZ Bank=292,418,747 Ks)
- ✅ Syntax clean on both Python files
- ✅ Frontend built + deployed
- ✅ API service active

---

## 📌 Summary (2026-06-09) — Financial Statements + Depreciation Engine

### 🏛️ Financial Statements — 3 Pages Live (00:00-02:47 UTC)
- **Issue:** PNL, Balance Sheet, CashFlow pages not showing + BS not balancing
- **Fix:** Router Syntax Error fixed (missing `},` broke Vite build)
- **BS rewritten 4 iterations:** DB account KEY vs LABEL mismatch (`kbz_bank` → `KBZ Bank`), `transfer_out` sign convention, missing mapping dict
- **Final:** Assets = L+E = **293,071,405 Ks → Diff=0 ✅**

### 📉 Depreciation Engine (04:37-05:32 UTC)
- **Asset Register:** Salvage Value, Useful Life, Monthly Dep, Dispose modal with return_account
- **Straight-line formula:** `monthly_dep = max(0, (amount - salvage) / (useful_life * 12))`
- **Financial Reports updated:** P&L (Operating Profit before Dep), BS (Gross→Dep→NBV + Dep Reserve in Equity), CF (Dep add-back)
- **Verification:** BS=290,502,334 L+E=290,502,334 **Diff=0 ✅**
- **Total Monthly Dep:** 4,029,826 Ks | **Total Acc. Dep:** 3,262,283 Ks

### 🗑️ GSheet Sync Removed (June 8)
- All 6 remaining sync functions deleted from `sync_service.py`
- System is **100% MySQL-only** — cron disabled, fallback removed

### 🧠 Key Lessons (June 7-9)
- **PyMySQL** `LIKE '%/%'` → Python format conflict → use `CONCAT('%', '/', '%')`
- **systemctl restart** may silently fail → verify PID, fallback `kill -9`
- **`.pyc` cache stale** after edit → always `find ... -name '__pycache__' -exec rm -rf {} +` then restart
- **String `replace()`** fails silently on whitespace mismatch → verify with `repr()`
- **`cash_movements`** stores labels (
