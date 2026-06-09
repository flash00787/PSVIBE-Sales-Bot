# PS VIBE — Logic Flow Cross Check (2026-05-29)

## 🏗️ Architecture Overview (Dual Data Path)

```
CUSTOMER (@psvibe_customer_service_bot)
  │  /balance /games /book /status
  ▼
┌──────────────────────┐
│ customer_bot/main.py │──→ 📊 Google Sheets (Staff File, Bot Analytics)
│ Booking Conversation │     (Direct access via service account)
└──────────────────────┘

STAFF (@ps_vibe_sales_bot)
  │  Daily Sales / Member Mgmt / Console / Booking / Stock
  ▼
┌──────────────────────────────────────────────────────────┐
│ bot/app.py (ConversationHandler — 40+ states)            │
│ ┌─────────────────────────────────────────────────────┐  │
│ │ bot/handlers/{sales,members,console,booking,...}    │  │
│ │ → Direct GSheet calls via bot/__init__.py (262 fns) │  │
│ │ → ⚠️ api_client.py (48 fns) — NOT used by handlers │  │
│ └─────────────────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ 📊 Google Sheets (PS VIBE - Staff File) — 27 Tabs        │
│ (SOURCE OF TRUTH for everything)                         │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ sync_service.py (Background thread every 300s)           │
│ Syncs: Card_Wallet→MySQL ✅                              │
│        Game_Library→MySQL ✅                              │
│        Console_Booking→MySQL ✅                           │
│        Setting→MySQL ✅                                   │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ 🐬 MySQL (Docker: psvibe-mysql:3306) — 21 Tables          │
│ Used by FastAPI as PRIMARY data source                    │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│ 🌐 FastAPI Server (0.0.0.0:8000) — 40+ Endpoints         │
│ Auth: X-API-Key header                                   │
│ Primary: MySQL | Fallback: GSheets                       │
│ Used by: api_client.py (but not the main bot)            │
└──────────────────────────────────────────────────────────┘
```

## 🔄 Sales Flow (Key Transaction)

```
1️⃣ Staff: "Daily Sales" နှိပ်
   → main_menu.py → prompt_member()
   → Direct GSheet: fetch_members() → member ရွေး

2️⃣ Staff: Console ရွေး, Game ရွေး, Duration ရွေး
   → sales.py → fetch_console_status() (GSheet)
   → fetch_console_games() (GSheet)
   → calc_duration()

3️⃣ Discount / Top-up ရှိရင်
   → fetch_wallet_mins() → Card_Wallet tab
   → fetch_balance_mins() → Column H

4️⃣ Sale Confirm → save_receipt_json()
   → Receipts tab မှာ သိမ်း
   → SQL INSERT INTO receipts

5️⃣ Booking → create_booking()
   → Console_Booking tab မှာ သိမ်း
   → INSERT INTO console_booking

6️⃣ Sync → 5min ကြာရင် sync_service
   → MySQL မှာ update
```

## ✅ Data Integrity Check

| Data Point | GSheet Tab | MySQL Table | Bot Uses | Status |
|-----------|-----------|-------------|----------|--------|
| Members | Card_Wallet (Col H) | members | ✅ direct GSheet | ✅ |
| Games | Game_Library | games_library | ✅ direct GSheet | ✅ |
| Console Status | Console_Games | console_status | ✅ direct GSheet | ✅ |
| Bookings | Console_Booking | console_booking | ✅ direct GSheet | ✅ |
| Settings | Setting | settings | ✅ direct GSheet | ✅ |
| Sales Daily | Sales_Daily | sales_daily | ✅ direct GSheet | ✅ |
| Staff | Dashboard (hidden) | staff_records | ✅ direct GSheet | ✅ |
| TopUp Log | TopUp_Log | topup_log | ✅ direct GSheet | ✅ |
| Attendance | Attendance_Log | attendance_log | ✅ direct GSheet | ✅ |
| Receipts | Receipts | receipts | ✅ direct GSheet + SQL | ✅ |

## ⚠️ Issues Found

1. **🔴 api_client.py vs direct GSheet** — Bot uses direct GSheet access for everything. API Client (48 functions) exists but not imported anywhere in the handlers. MySQL sync + FastAPI server are underutilized.

2. **🟡 Wallet Sheet Access** — Service account `user-408@ps-vibe-sales-tele-bot.iam.gserviceaccount.com` doesn't have access to Wallet Sheet `1mlc9AmhwIVCk7egJoQgX4ld6z9kpwciDegxYA8_BPRc`

3. **🟢 Stale backups cleaned** — 7 `*.bak*` files removed from `bot/` directory

## 🔧 Fix Applied
- `/api/health` — Missing return statement fixed (was returning `null`)
- Nova Host API — Binding changed from `127.0.0.1` to `0.0.0.0`
- 16+ backup files cleaned from API server directory

## 📝 Summary
**Data flow is correct but redundant.** Bot → GSheet is the direct work path. MySQL + FastAPI serve as backup/infrastructure layer with sync_service doing GSheet → MySQL every 5 min.

**Advantage:** GSheet failure → MySQL as backup
**API role:** Third-party integrations (mobile app, web dashboard)
**MySQL role:** Analytics (faster queries)
