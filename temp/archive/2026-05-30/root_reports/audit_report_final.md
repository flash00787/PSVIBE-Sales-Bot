# Audit Report: Booking/Stock/Other Handlers
**Generated:** 2026-05-28T20:35:09.583Z
**Source:** `/root/psvibe-sales-bot/bot/`

---

## 1. api_client.py — Available API Functions (48 total)

```
api_add_console_game
api_add_console_to_setting
api_build_member_rate_dict
api_cancel_booking
api_create_booking
api_end_booking
api_fetch_allowed_staff_ids
api_fetch_alltime_effective_rate
api_fetch_attendance
api_fetch_balance_mins
api_fetch_base_rate
api_fetch_base_salaries
api_fetch_bonus_table
api_fetch_console_games
api_fetch_console_multiplier
api_fetch_console_status
api_fetch_food_costs
api_fetch_food_prices
api_fetch_game_library
api_fetch_games
api_fetch_member_data
api_fetch_member_effective_rate
api_fetch_member_tier
api_fetch_members
api_fetch_new_member_defaults
api_fetch_promotions_cached
api_fetch_rank_table_display
api_fetch_rank_thresholds
api_fetch_referral_code
api_fetch_salary_advances
api_fetch_sheets_config
api_fetch_staff
api_fetch_staff_names
api_fetch_wallet_mins
api_get_consoles_with_game
api_get_games_on_console
api_health
api_next_member_id
api_next_member_row_no
api_next_voucher
api_remove_console_from_setting
api_remove_console_game
api_save_attendance
api_save_receipt_json
api_save_referral_code
api_set_game_disc_count
api_update_game_library_install
api_update_member_effective_rate
```

---

## 2. API Server Routes (FastAPI in /root/psvibe_api_server/app.py)

```
add_console_game
add_console_to_setting
analytics/console_usage
analytics/daily_sales
analytics/dashboard
analytics/dashboard?api_key={API_KEY}
analytics/member_activity
analytics/topups
analytics/weekly_trends
api/add_console_game
api/add_console_to_setting
api/analytics/console_usage
api/analytics/daily_sales
api/analytics/dashboard
api/analytics/member_activity
api/analytics/topups
api/analytics/weekly_trends
api/bookings
api/bookings/{booking_id}
api/bookings/search
api/bot-users/track
api/build_member_rate_dict
api/cancel_booking/{booking_id}
api/create_booking
api/dashboard
api/end_booking/{booking_id}
api/feedback/submit
api/fetch_allowed_staff_ids
api/fetch_alltime_effective_rate
api/fetch_attendance/{month_str}
api/fetch_balance_mins/{member_id}
api/fetch_base_rate
api/fetch_base_salaries
api/fetch_bonus_table
api/fetch_console_games
api/fetch_console_multiplier/{console_id}
api/fetch_console_status
api/fetch_food_costs
api/fetch_food_prices
api/fetch_game_library
api/fetch_games
api/fetch_member_data/{member_id}
api/fetch_member_effective_rate/{member_id}
api/fetch_member_tier/{member_id}
api/fetch_members
api/fetch_new_member_defaults
api/fetch_promotions_cached
api/fetch_rank_table_display
api/fetch_rank_thresholds
api/fetch_referral_code/{member_id}
api/fetch_salary_advances/{month_str}
api/fetch_staff
api/fetch_staff_names
api/fetch_wallet_mins/{member_id}
api/get_consoles_with_game
api/get_games_on_console/{console_id}
api/health
api/next_member_id
api/next_member_row_no
api/next_voucher
api/remove_console_from_setting/{console_id}
api/remove_console_game
api/save_attendance
api/save_receipt_json
api/save_referral_code
api/set_game_disc_count
api/sheets/config
api/sheets/log
api/update_game_library_install
api/update_member_effective_rate
bookings
bookings/{booking_id}
bookings/search
bot-users/track
build_member_rate_dict
cancel_booking/{booking_id}
create_booking
dashboard
end_booking/{booking_id}
feedback/submit
fetch_allowed_staff_ids
fetch_alltime_effective_rate
fetch_attendance/{month_str}
fetch_balance_mins/{member_id}
fetch_base_rate
fetch_base_salaries
fetch_bonus_table
fetch_console_games
fetch_console_multiplier/{console_id}
fetch_console_status
fetch_food_costs
fetch_food_prices
fetch_game_library
fetch_games
fetch_member_data/{member_id}
fetch_member_effective_rate/{member_id}
fetch_member_tier/{member_id}
fetch_members
fetch_new_member_defaults
fetch_promotions_cached
fetch_rank_table_display
fetch_rank_thresholds
fetch_referral_code/{member_id}
fetch_salary_advances/{month_str}
fetch_staff
fetch_staff_names
fetch_wallet_mins/{member_id}
get_consoles_with_game
get_games_on_console/{console_id}
health
next_member_id
next_member_row_no
next_voucher
remove_console_from_setting/{console_id}
remove_console_game
save_attendance
save_receipt_json
save_referral_code
set_game_disc_count
sheets/config
sheets/log
update_game_library_install
update_member_effective_rate
```

---

## 3. Replit Internal Functions (from bot __init__.py)

```
_replit_delete
_replit_get
_replit_post
```

---

## 4. BTN_* Constants (from bot __init__.py)

```
BTN_ADD_CONSOLE     = "➕ Console ထည့်"
BTN_ADD_GAME        = "➕ ဂိမ်းထည့်"
BTN_ADD_PAY   = "Add Payment Method"
BTN_ADMIN              = "🔧 Admin Panel"
BTN_ADMIN_ATTEND  = "📅 Attendance"
BTN_ADMIN_BOOK    = "📋 Pending Bookings"
BTN_ADMIN_CF      = "💵 Cash Flow"
BTN_ADMIN_LIB     = "💳 Card Liability"
BTN_ADMIN_PNL     = "📊 Monthly P&L"
BTN_ADMIN_SAL_ADV = "💸 Salary Advance"
BTN_ASSIGN_REFERRAL = "🎁 Referral Code သတ်မှတ်"
BTN_ATTEND_DONE = "✅ ပြီးပါပြီ"
BTN_ATTEND_SKIP = "⏭ Skip"
BTN_BACK         = "⬅️ ပြန်သွား"
BTN_BACK_MAIN    = "⬅️ Main Menu သို့ပြန်"
BTN_BOOK_PROCEED     = "⚠️ ဒါပဲ ဆက်ဖွင့်မည်"
BTN_CANCEL       = "❌ Cancel"
BTN_CANCEL_BOOKING   = "🚫 Cancel Booking"
BTN_CASH_DOWN        = "💵 Cash Down (ချက်ချင်းပေး)"
BTN_CHANGE_GAME  = "🔄 Game ပြောင်း"
BTN_CHECK_MEMBER   = "🔍 Check Member"
BTN_CLEAR_CART     = "🗑️ Clear Cart"
BTN_CONFIRM_ID     = "✅ Confirm ID"
BTN_CONFIRM_SAVE = "Confirm & Save"
BTN_CONSOLES        = "🕹️ Consoles"
BTN_CONSOLE_BOOK   = "📋 New Booking"
BTN_CONSOLE_INSTALL  = "🖥️ Console Install"
BTN_CONSOLE_STATUS = "🕹️ Console Status"
BTN_CON_MANAGE      = "⚙️ Console စီမံ"
BTN_DAILY_SALES  = "📝 Daily Sales"
BTN_DEL_CONSOLE     = "🗑️ Console ဖျက်"
BTN_DEL_GAME        = "🗑️ ဂိမ်းဖျက်"
BTN_DISC_RECORD  = "💿 Game Discs"
BTN_DONE         = "Done ✅"
BTN_EDIT_GAME    = "✏️ Edit Game"
BTN_END_SESSION     = "⏹️ Session ဆုံး"
BTN_FINANCE          = "💼 Finance"
BTN_FINANCIAL_REPORT   = "💹 Financial Report"
BTN_FIN_ACCTS        = "💰 Accounts"
BTN_FIN_ADVPAY       = "💵 Advance"
BTN_FIN_ASSET        = "🏢 Asset"
BTN_FIN_ASSET_DISPOSE = "🔄 Dispose Asset"
BTN_FIN_BACK         = "⬅️ Finance Menu"
BTN_FIN_BS           = "🏦 Balance Sheet"
BTN_FIN_CAPITAL      = "🏦 Capital"
BTN_FIN_DEPR         = "📉 Depreciation"
BTN_FIN_OPEX         = "📝 OPEX"
BTN_FIN_PAYABLE      = "📤 Payable"
BTN_FIN_PNL          = "📊 P&L Report"
BTN_FIN_PREPAID      = "📅 Prepaid"
BTN_FIN_PROFIT_SHARE = "💸 Profit Sharing"
BTN_FIN_RECEIVABLE   = "📥 Receivable"
BTN_FIN_REPORT       = "📊 Reports"
BTN_FIN_SETTLE_ADVPAY= "✅ Settle Adv"
BTN_FIN_SETTLE_PAY   = "✅ Settle Pay"
BTN_FIN_SETTLE_REC   = "✅ Settle Rec"
BTN_FIN_SETUP        = "⚙️ Sheet Setup"
BTN_FIN_SHAREHOLDER  = "👥 Partners"
BTN_FIN_TRANSFER     = "💸 Transfer"
BTN_FIRST_PURCHASE = "🆕 New Member"
BTN_GAME_LIB_MENU   = "🎮 Game Library"
BTN_GINST_ADD        = "➕ Install မှတ်သား"
BTN_GINST_DISC       = "💿 Disc"
BTN_GINST_HDD        = "💾 HDD (Internal)"
BTN_GINST_REMOVE     = "❌ Install ဖျက်"
BTN_GINST_SSD        = "🔌 Portable SSD"
BTN_GINST_VIEW       = "📋 ဘယ် Console မှာ ဘာ ရှိသလဲ"
BTN_INVENTORY_VIEW   = "📊 Inventory ကြည့်ရှု"
BTN_LIST_CONSOLE    = "📋 Console စာရင်း"
BTN_MANUAL_DISC      = "✏️ Manual Discount ရိုက်"
BTN_MEMBER_MGMT  = "💳 Member Management"
BTN_NEW_SALE     = "📝 New Sale"
BTN_NM_CUSTOM      = "✏️ Enter Different Amount"
BTN_NM_GIFT        = "🎁 Gift / Free Card"
BTN_NO_BACK         = "❌ No — ပြန်"
BTN_NO_MORE   = "No More Payments"
BTN_NO_RESELECT      = "❌ ပြန်ရွေး"
BTN_PAYROLL            = "💰 Payroll"
BTN_PAY_DONE  = "Payment Done"
BTN_PROMO_APPLY      = "🎁 Promotion ထည်သွင်း"
BTN_PROMO_REPORTS = "📊 Promo Reports"
BTN_SAVE         = "သိမ်းမည် ✅"
BTN_SBK_CONFIRMED    = "✅ Confirmed Bookings"
BTN_SBK_CONFIRM_BOOK = "✅ Booking ဖန်တီးမည်"
BTN_SBK_CUSTOM       = "✏️ ရက်ထည့်"
BTN_SBK_NEW          = "➕ New Booking"
BTN_SBK_SKIP_GAME    = "⏭ Game မထည့်"
BTN_SBK_SKIP_PHONE   = "⏭ Phone မထည့်"
BTN_SBK_TODAY        = "📅 ယနေ့"
BTN_SBK_TOMORROW     = "📅 မနက်ဖြန်"
BTN_SBK_WAITLIST     = "⏳ Waitlist"
BTN_SI_ADD         = "➕ Item ထပ်ထည့်"
BTN_SI_FINISH      = "💳 Payment & Save All"
BTN_SI_SPLIT     = "💰 ခွဲပေး (Cash + KPay)"
BTN_SKIP_DISC        = "⏩ Skip (Discount မထည့်)"
BTN_SKIP_EMAIL     = "⏩ Email မထည့်"
BTN_SKIP_GAME    = "⏭ ဂိမ်း မထည့်"
BTN_SKIP_PHONE     = "⏩ Skip"
BTN_SKIP_REFERRAL  = "⏩ Referral Code မထည့်"
BTN_SKIP_SALES       = "⏭ Skip (မမှတ်တမ်းတင်)"
BTN_SKIP_TIMER       = "⏭ Skip (Timer မလိုပါ)"
BTN_SSD_ADD      = "➕ SSD ထဲ ဂိမ်း ထည့်"
BTN_SSD_BLUE     = "Sandisk Extreme (Blue)"
BTN_SSD_GREY     = "Sandisk Extreme (Grey)"
BTN_SSD_MANAGE   = "📀 External SSD"
BTN_SSD_REMOVE   = "❌ SSD မှ ဂိမ်း ဖျက်"
BTN_SSD_RETURN   = "↩️ Console → SSD (Return)"
BTN_SSD_T1       = "Samsung T1 Shield"
BTN_SSD_TRANSFER = "🔄 SSD → Console (Transfer)"
BTN_SSD_VIEW     = "📋 SSD ထဲ ဘာ ရှိသလဲ"
BTN_STAFF_BOOK       = "📅 Customer Booking"
BTN_STAFF_KPI          = "📈 Staff KPI"
BTN_START_SESSION   = "▶️ Session စတင်"
BTN_STATUS_BOARD    = "📊 Status ကြည့်"
BTN_STOCK_IN_M       = "📥 Stock In (ဝယ်ယူ)"
BTN_STOCK_OUT        = "📦 Stock Out (ထုတ်ယူ)"
BTN_STOCK_UPDATE = "📦 Stock Update"
BTN_TODAY_REPORT = "📊 Today's Report"
BTN_TOPUP_SESSION    = "💳 Top Up ပြီး ဆက်"
BTN_TOP_UP         = "💰 Top Up"
BTN_VIEW_GAMES      = "📋 ဂိမ်းစာရင်း"
BTN_VIEW_RANKS     = "📋 Rank Bonuses"
BTN_WL_NOTIFY_NEXT   = "🔔 Next ကို Notify"
BTN_WL_REFRESH       = "🔄 Refresh"
BTN_WL_VIEW_ALL      = "📂 All Entries ကြည့်"
BTN_WL_VIEW_WAITING  = "📋 Waiting List ကြည့်"
BTN_YES          = "Yes ✅"
BTN_YES_END         = "✅ Yes — ဆုံးမည်"
BTN_YES_END_SESSION  = "✅ Session ကို End မည်"
```

---

## 5. Handler-by-Handler Analysis


### 📁 handlers/booking.py (1089 lines)

**5.1 — api_* calls made (0 unique):**

None found.

**5.2 — _replit_* calls (bypasses api_client.py):**

- `_replit_get()` — lines: 18, 66, 67, 114, 607

**5.4 — Direct gspread/sheet calls (DEPRECATED):**

None found ✅

**5.5 — BTN_* Constants Referenced (15 unique):**

- `BTN_BACK`
- `BTN_BACK_MAIN`
- `BTN_BOOK_PROCEED`
- `BTN_CANCEL`
- `BTN_NO_RESELECT`
- `BTN_SBK_CONFIRMED`
- `BTN_SBK_CONFIRM_BOOK`
- `BTN_SBK_CUSTOM`
- `BTN_SBK_NEW`
- `BTN_SBK_SKIP_GAME`
- `BTN_SBK_SKIP_PHONE`
- `BTN_SBK_WAITLIST`
- `BTN_SKIP_GAME`
- `BTN_SKIP_TIMER`
- `BTN_SSD_TRANSFER`

**5.6 — Endpoint Cross-Reference (API Client vs Server):**



### 📁 handlers/booking_flow.py (745 lines)

**5.1 — api_* calls made (1 unique):**

- ❌ `api_base()` — lines: 257

**5.4 — Direct gspread/sheet calls (DEPRECATED):**

None found ✅

**5.5 — BTN_* Constants Referenced (1 unique):**

- `BTN_BACK_MAIN`

**5.6 — Endpoint Cross-Reference (API Client vs Server):**



### 📁 handlers/stock.py (243 lines)

**5.1 — api_* calls made (0 unique):**

None found.

**5.2 — _replit_* calls (bypasses api_client.py):**

- `_replit_get()` — lines: 119, 216

**5.4 — Direct gspread/sheet calls (DEPRECATED):**

- ❌ **Line 14:** `DEPRECATED: direct gspread write — should use API endpoint when available."""`
- ❌ **Line 197:** `logging.warning("DEPRECATED: direct gspread write in step_stock_qty — should use API endpoint")`
- ❌ **Line 198:** `stock_sh.append_row(`

**5.5 — BTN_* Constants Referenced (4 unique):**

- `BTN_BACK_MAIN`
- `BTN_INVENTORY_VIEW`
- `BTN_STOCK_IN_M`
- `BTN_STOCK_OUT`

**5.6 — Endpoint Cross-Reference (API Client vs Server):**



### 📁 handlers/stock_in.py (292 lines)

**5.1 — api_* calls made (0 unique):**

None found.

**5.4 — Direct gspread/sheet calls (DEPRECATED):**

- ❌ **Line 251:** `logging.warning("DEPRECATED: direct gspread write in step_si_confirm — should use API endpoint")`
- ❌ **Line 252:** `stock_in_sh.append_row(`

**5.5 — BTN_* Constants Referenced (5 unique):**

- `BTN_BACK_MAIN`
- `BTN_CONFIRM_SAVE`
- `BTN_SI_ADD`
- `BTN_SI_FINISH`
- `BTN_SI_SPLIT`

**5.6 — Endpoint Cross-Reference (API Client vs Server):**



### 📁 handlers/referral.py (138 lines)

**5.1 — api_* calls made (0 unique):**

None found.

**5.4 — Direct gspread/sheet calls (DEPRECATED):**

None found ✅

**5.5 — BTN_* Constants Referenced (3 unique):**

- `BTN_BACK`
- `BTN_BACK_MAIN`
- `BTN_CANCEL`

**5.6 — Endpoint Cross-Reference (API Client vs Server):**



### 📁 handlers/discount.py (438 lines)

**5.1 — api_* calls made (0 unique):**

None found.

**5.4 — Direct gspread/sheet calls (DEPRECATED):**

None found ✅

**5.5 — BTN_* Constants Referenced (5 unique):**

- `BTN_BACK`
- `BTN_CANCEL`
- `BTN_MANUAL_DISC`
- `BTN_PROMO_APPLY`
- `BTN_SKIP_DISC`

**5.6 — Endpoint Cross-Reference (API Client vs Server):**



### 📁 handlers/waitlist.py (286 lines)

**5.1 — api_* calls made (0 unique):**

None found.

**5.2 — _replit_* calls (bypasses api_client.py):**

- `_replit_get()` — lines: 19

**5.4 — Direct gspread/sheet calls (DEPRECATED):**

None found ✅

**5.5 — BTN_* Constants Referenced (5 unique):**

- `BTN_BACK_MAIN`
- `BTN_WL_NOTIFY_NEXT`
- `BTN_WL_REFRESH`
- `BTN_WL_VIEW_ALL`
- `BTN_WL_VIEW_WAITING`

**5.6 — Endpoint Cross-Reference (API Client vs Server):**



### 📁 handlers/attendance.py (174 lines)

**5.1 — api_* calls made (0 unique):**

None found.

**5.4 — Direct gspread/sheet calls (DEPRECATED):**

None found ✅

**5.5 — BTN_* Constants Referenced (3 unique):**

- `BTN_ATTEND_DONE`
- `BTN_ATTEND_SKIP`
- `BTN_CANCEL`

**5.6 — Endpoint Cross-Reference (API Client vs Server):**



### 📁 handlers/broadcast.py (145 lines)

**5.1 — api_* calls made (0 unique):**

None found.

**5.4 — Direct gspread/sheet calls (DEPRECATED):**

- ❌ **Line 102:** `sb = await asyncio.to_thread(_replit_get, "sheets/staff-breakdown")   # API cache (was direct gspread call)`

**5.5 — BTN_* Constants Referenced (1 unique):**

- `BTN_BACK_MAIN`

**5.6 — Endpoint Cross-Reference (API Client vs Server):**



### 📁 handlers/notify.py (74 lines)

**5.1 — api_* calls made (0 unique):**

None found.

**5.2 — _replit_* calls (bypasses api_client.py):**

- `_replit_get()` — lines: 38

**5.4 — Direct gspread/sheet calls (DEPRECATED):**

None found ✅

**5.5 — BTN_* Constants Referenced (0 unique):**

None found.

**5.6 — Endpoint Cross-Reference (API Client vs Server):**



### 📁 handlers/games.py (412 lines)

**5.1 — api_* calls made (0 unique):**

None found.

**5.4 — Direct gspread/sheet calls (DEPRECATED):**

- ❌ **Line 363:** `sh.update_cell(row_num, 21, meta)   # col U = index 21`
- ❌ **Line 393:** `sh.delete_rows(target["row"])`

**5.5 — BTN_* Constants Referenced (10 unique):**

- `BTN_ADD_GAME`
- `BTN_BACK`
- `BTN_BACK_MAIN`
- `BTN_CANCEL`
- `BTN_CONSOLE_INSTALL`
- `BTN_DEL_GAME`
- `BTN_DISC_RECORD`
- `BTN_EDIT_GAME`
- `BTN_SSD_MANAGE`
- `BTN_VIEW_GAMES`

**5.6 — Endpoint Cross-Reference (API Client vs Server):**



### 📁 handlers/ssd_disc.py (459 lines)

**5.1 — api_* calls made (0 unique):**

None found.

**5.4 — Direct gspread/sheet calls (DEPRECATED):**

None found ✅

**5.5 — BTN_* Constants Referenced (13 unique):**

- `BTN_BACK`
- `BTN_BACK_MAIN`
- `BTN_GINST_DISC`
- `BTN_GINST_HDD`
- `BTN_GINST_SSD`
- `BTN_SSD_ADD`
- `BTN_SSD_BLUE`
- `BTN_SSD_GREY`
- `BTN_SSD_REMOVE`
- `BTN_SSD_RETURN`
- `BTN_SSD_T1`
- `BTN_SSD_TRANSFER`
- `BTN_SSD_VIEW`

**5.6 — Endpoint Cross-Reference (API Client vs Server):**


---

## Summary Table

| Handler | Lines | api* calls | Missing API funcs | Gspread refs | BTN refs | Direct _api_call |
|---------|------:|-----------:|------------------:|-------------:|---------:|-----------------:|
| handlers/booking.py | 1089 | 0 | 0 | 0 | 15 | 0 |
| handlers/booking_flow.py | 745 | 1 | 1 | 0 | 1 | 0 |
| handlers/stock.py | 243 | 0 | 0 | 3 | 4 | 0 |
| handlers/stock_in.py | 292 | 0 | 0 | 2 | 5 | 0 |
| handlers/referral.py | 138 | 0 | 0 | 0 | 3 | 0 |
| handlers/discount.py | 438 | 0 | 0 | 0 | 5 | 0 |
| handlers/waitlist.py | 286 | 0 | 0 | 0 | 5 | 0 |
| handlers/attendance.py | 174 | 0 | 0 | 0 | 3 | 0 |
| handlers/broadcast.py | 145 | 0 | 0 | 1 | 1 | 0 |
| handlers/notify.py | 74 | 0 | 0 | 0 | 0 | 0 |
| handlers/games.py | 412 | 0 | 0 | 2 | 10 | 0 |
| handlers/ssd_disc.py | 459 | 0 | 0 | 0 | 13 | 0 |

---

*Audit complete.*
