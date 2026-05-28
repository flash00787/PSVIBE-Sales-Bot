# PS VIBE V2 — Logic & Concept Reference
**Date:** 2026-05-27  
**Source:** V2 Refactored Bot Codebase Analysis

---

## 🏗️ Architecture Overview

**3-Layer Structure:**

```
┌──────────────────────────────────────────────────┐
│  🎭 HANDLER LAYER (28 files, ~12,000 lines)      │
│  sales.py  members.py  booking.py  finance.py ... │
│  → UI logic, user interaction flow               │
├──────────────────────────────────────────────────┤
│  🔧 CORE ENGINE (bot/__init__.py, 2,084 lines)    │
│  → Sheet auth, fetch functions, state defs       │
├──────────────────────────────────────────────────┤
│  🚀 ENTRY POINT (bot/app.py, 465 lines)           │
│  → Auth middleware + ConversationHandler          │
└──────────────────────────────────────────────────┘
```

**Total:** 29 Python files | 14,403 lines | 428 functions

---

## 📁 File Breakdown

| File | Lines | Funcs | Purpose |
|------|-------|-------|---------|
| **bot/__init__.py** | 2,084 | 83 | Core engine: Sheet auth, gspread wrappers, fetch functions, helpers |
| **bot/app.py** | 465 | 2 | Bot entry point + ConversationHandler (183 states) |
| **finance.py** | 2,560 | 106 | Finance: OPEX, Assets, Prepaid, P&L, Balance Sheet, Payables |
| **sales.py** | 1,273 | 25 | Daily Sales flow (member → console → mins → pay → save) |
| **members.py** | 1,137 | 33 | Member mgmt: New member, Top-up, Check, Ranks, Referral |
| **booking.py** | 1,077 | 24 | Console booking system |
| **booking_flow.py** | 725 | 17 | Booking reminders, n8n webhooks |
| **admin.py** | 538 | 12 | Admin panel: PIN, attendance setup |
| **ssd_disc.py** | 451 | 16 | External SSD management |
| **discount.py** | 435 | 5 | Promotions & discounts |
| **games.py** | 409 | 10 | Game library CRUD |
| **console.py** | 339 | 8 | Console status |
| **reports.py** | 339 | 5 | Reports (today, weekly, financial) |
| **stock.py / stock_in.py** | 524 | 20 | Stock management |
| **waitlist.py** | 275 | 8 | Waitlist system |
| **admin_bookings.py** | 236 | 5 | Approve/reject bookings |
| **payroll.py** | 232 | 4 | Payroll & KPI |
| **attendance.py** | 171 | 8 | Staff attendance |
| **console_mgmt.py** | 147 | 6 | Console add/delete |
| **broadcast.py** | 143 | 2 | Broadcast to staff |
| **referral.py** | 135 | 2 | Referral codes |
| **salary_adv.py** | 125 | 4 | Salary advance |
| **main_menu.py** | 114 | 2 | Main menu + button routing |
| **commands.py** | 42 | 6 | /start, /cancel, /help, /version |
| **handler init** | 37 | 0 | Re-exports all handler modules + `from bot import *` |

---

## 🔄 Data Flow

### Core Concept
Handler modules call shared functions from `bot/__init__.py` via `from bot import *`.

```
User button tap 
    → app.py ConversationHandler 
    → main_menu.py step_main_menu() 
    → sales.py prompt_member() 
    → bot/__init__.py fetch_members() 
    → gspread → Google Sheets
```

### Dual Data Path

**Path A — gspread (primary, direct):**
```python
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
gc = gspread.authorize(creds)
wb = gc.open_by_key(os.environ["SHEET_ID"])
sales_sh = wb.worksheet("Sales_Daily")
```
- Retry wrapper (429/500/503 → 3 retries, exponential backoff)
- Cached reads (10-min TTL for games, 30-sec TTL for bookings)
- `asyncio.to_thread()` for background writes

**Path B — Replit API (secondary, legacy):**
```python
_replit_get("sheets/inventory")
_replit_post("waitlist/notify", {...})
```
- Falls back silently (returns None) if API server offline
- Being replaced by gspread

---

## 🎯 ConversationHandler State Machine

Single handler with 183 states, 33 flow sections:

```
MAIN_MENU (0) 
  ├─🛒 Daily Sales → MEMBER → CONSOLE → MINS → FOOD → CONFIRM → KPAY → SALE_CONFIRM ✅
  ├─👥 Members     → MM_MENU → NM_NAME / TU_MEMBER / MM_LOOKUP
  ├─🕹️ Consoles    → CONSOLE_MENU → GAME_MENU / GINST / SSD / END_SESSION
  ├─📋 Today Report → cmd_today_report()
  ├─📅 Booking     → SBK_CONSOLE → SBK_DATE → SBK_DUR → ...
  ├─📦 Inventory   → STOCK_PIN → STOCK_MENU → ...
  └─💰 Financial   → FINANCE_MENU → OPEX/ASSET/PREPAID/REPORT
```

State routing: each `step_*` function returns next state → next message hits that state's handler → flow continues until `ConversationHandler.END` or `show_main_menu()`.

---

## ⚙️ Cache Mechanism

```python
_BK_ROWS: None;  _BK_TS: 0;  _BK_TTL: 30    # 30 sec (bookings)
_GAME_ROWS: None; _GAME_TS: 0; _GAME_TTL: 600  # 10 min (games)
_STAFF_CACHE: None; _STAFF_TS: 0; _STAFF_TTL: 300  # 5 min (staff)
_MEMBER_CACHE: []; _MEMBER_TS: 0              # members
_CFG_CACHE: {};  _CFG_TS: 0;  _CFG_TTL: 300   # 5 min (config)
_PROMO_CACHE: []; _PROMO_TS: 0; _PROMO_TTL: 600  # 10 min (promos)
```

- `_bg_cache_refresh()` refreshes every 5 min in background
- `_prewarm_caches()` runs at startup

---

## 🛒 Daily Sales Flow (Complete)

```
1. 🛒 Daily Sales button → step_main_menu()
   → next_voucher() + prompt_member()
   
2. 👤 Select Member → step_member()
   → fetch_wallet_mins() + _check_member_in_session()
   → Guest: skip session check
   
3. 🕹️ Select Console → step_console()
   → _check_console_in_session()
   → VALID_CONSOLES validation
   
4. ⏱️ Select Mins → step_mins()
   → calc: base_rate × console_multiplier
   → wallet balance check
   → optional: time adjustment (±10 min)
   
5. 🍔 Food Menu → step_food_menu() → step_food_qty()
   → fetch_food_prices() / fetch_food_costs()
   
6. 📋 Review Summary → step_confirm()
   → Member flow: wallet deduct vs cash down
   → Guest flow: pure cash (rate × mult × mins)
   → Shortfall: redirect to cash down prompt
   
7. 💳 Payment → step_kpay()
   → KPay / Cash / KPay+Cash split
   
8. ✅ Confirm → step_sale_confirm()
   → _sale_bg() background write:
      • Sales_Daily sheet (A-O columns)
      • Stock_Out sheet (food items)
      • Inventory total update
      • Member wallet (bonus mins)
      • Promotions_Log (via _replit_post)
      • Booking mark completed (via _replit_patch)
      • Waitlist notify (via _replit_post)
      • n8n session/webhook reminders
      • Receipt JSON save
```

---

## 🔑 Key Design Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| **State Machine** | Telegram ConversationHandler | 183 states, 33 flow sections |
| **Background Task** | `asyncio.create_task()` | `_sale_bg()` for non-blocking writes |
| **Retry Decorator** | `@_sheets_retry` | Auto-retry 429/500/503 with backoff |
| **Cache + TTL** | Global vars with timestamps | 6 caches with 30s-10min TTL |
| **Export via __all__** | Namespace control | Sheet vars + Replit funcs + BTNs |
| **Domain Separation** | One handler per business domain | sales.py, members.py, booking.py |
| **Auth Middleware** | Group=-999 TypeHandler | Blocks unauthorized Telegram users |
| **Error Handler** | Global `error_handler` | Catches unhandled exceptions |

---

## V1 vs V2 Comparison

| Aspect | V1 (Monolithic) | V2 (Refactored) |
|--------|-----------------|-----------------|
| Files | 1 (main.py) | 29 .py files |
| Lines | 12,249 | 14,403 |
| Functions | ~400 | 428 |
| Sheet Access | Replit API (`_replit_get`) | gspread direct |
| Data Path | HTTP → API server → Sheets | Direct gspread |
| Cache | Minimal | 7 caches with TTL |
| Error Handling | Basic | Retry wrapper + logging |
| Structure | Sequential in 1 file | Domain-split modules |

---

## ✅ Fixed `__all__` Exports

All underscore-prefixed names that handlers need via `from bot import *`:

| Name | Type | Used By |
|------|------|---------|
| `_replit_get` | function | sales.py (inventory cache) |
| `_replit_post` | function | sales.py (promotions, waitlist) |
| `_replit_patch` | function | sales.py, booking_flow.py, admin_bookings.py |
| `_replit_delete` | function | waitlist.py |
| `_BROADCAST_ADMIN_IDS` | constant | broadcast.py |
| `_int` | function | payroll.py, admin.py |
| `_pin_then` | function | payroll.py, attendance.py, finance.py, admin.py |
| `_BIZ_START` | constant | finance.py (depreciation calc) |
| `sales_sh` | Worksheet | sales.py, admin.py, payroll.py |
| `stock_sh` | Worksheet | sales.py, stock.py, admin.py |
| `member_sh` | Worksheet | sales.py, members.py, referral.py |
| `setting_sh` | Worksheet | admin.py |
| `inv_sh` | Worksheet | stock.py |
| `topup_sh` | Worksheet | members.py, payroll.py, admin.py |
| `stock_in_sh` | Worksheet | admin.py, stock_in.py |
| `wb` | Spreadsheet | (rare) |
| `gc` | gspread.Client | (rare) |
