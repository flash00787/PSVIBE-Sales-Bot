# Sales Bot Handler Audit — Complete ConversationHandler & Button Flow Report

**Date:** 2026-05-28  
**Bot:** `/root/psvibe-sale-bot` on VPS `5.223.81.16`  
**Architecture:** Single `ConversationHandler` in `bot/app.py` with ~120 states wired to handlers across 27 domain-split files.

---

## Syntax Verification

All 27 Python handler files pass `ast.parse()` syntax checks:
```
OK: __init__.py, admin.py, admin_bookings.py, attendance.py, booking.py,
    booking_flow.py, broadcast.py, commands.py, console.py, console_mgmt.py,
    discount.py, finance.py, games.py, ginst.py, help.py, main_menu.py,
    members.py, notify.py, payroll.py, referral.py, reports.py, salary_adv.py,
    sales.py, ssd_disc.py, stock.py, stock_in.py, waitlist.py
```

---

## Architecture Overview

The bot uses a **single monolithic `ConversationHandler`** defined in `bot/app.py` (not `main.py`). Each `bot/handlers/*.py` file defines only functions — no individual `ConversationHandler` instances. All state constants (e.g., `MAIN_MENU`, `MEMBER`, `CONSOLE`) and BTN_* button labels are defined in `bot/__init__.py`.

```python
# bot/app.py — structure
conv = ConversationHandler(
    entry_points=[...42 total entries...],
    states={...~120 states...},
    fallbacks=[...42 total fallbacks...]
)
app.add_handler(conv)
# + 9 global handlers (callback queries + message handlers at specific groups)
# + 41 standalone CommandHandlers (for cold starts when not in conversation)
```

---

## Entry Points (42 total)

### Navigation Commands
| Command | Handler | Source File |
|---------|---------|-------------|
| `/start` | `show_main_menu` | `main_menu.py` |
| `/menu` | `show_main_menu` | `main_menu.py` |
| `/cancel` | `cmd_cancel` | `commands.py` |
| `/help` | `cmd_help` | `help.py` |
| `/version` | `cmd_version` | `help.py` |

### Sales
| Command | Handler | Source File |
|---------|---------|-------------|
| `/sales` | `cmd_sales_direct` | `sales.py` |

### Members
| Command | Handler | Source File |
|---------|---------|-------------|
| `/member` | `cmd_member_mgmt` | `commands.py` |
| `/newmember` | `cmd_newmember` | `commands.py` |
| `/topup` | `cmd_topup` | `commands.py` |
| `/check` | `cmd_check_member` | `commands.py` |
| `/ranks` | `cmd_ranks` | `commands.py` |

### Reports
| Command | Handler | Source File |
|---------|---------|-------------|
| `/report` | `cmd_today_report` | `reports.py` |
| `/freport` | `cmd_financial_report` | `reports.py` |
| `/dailyreport` | `cmd_daily_report` | `reports.py` |
| `/weeklyreport` | `cmd_weekly_report` | `reports.py` |
| `/members` | `cmd_member_insights` | `reports.py` |
| `/broadcast` | `cmd_broadcast` | `broadcast.py` |
| `/kpi` | `cmd_kpi_cmd` | `payroll.py` |
| `/payroll` | `cmd_payroll_cmd` | `payroll.py` |
| `/setattend` | `cmd_setattend_cmd` | `attendance.py` |
| `/admin` | `cmd_admin` | `admin.py` |

### Booking Management
| Command | Handler | Source File |
|---------|---------|-------------|
| `/bookings` | `cmd_admin_bookings` | `admin_bookings.py` |
| `/waitlist` | `cmd_waitlist_mgmt` | `waitlist.py` |
| `/newbooking` | `cmd_staff_booking` | `booking_flow.py` |
| `/approve_NNN` | `cmd_approve_booking` | `admin_bookings.py` |
| `/reject_NNN` | `cmd_reject_booking` | `admin_bookings.py` |

### Stock
| Command | Handler | Source File |
|---------|---------|-------------|
| `/stock` | `cmd_stock_menu` | `stock.py` |
| `/stockin` | `cmd_stockin_direct` | `stock_in.py` |
| `/stockout` | `cmd_stockout_direct` | `stock.py` |
| `/inventory` | `cmd_inventory` | `reports.py` |
| `/stocktoday` | `cmd_stocktoday` | `reports.py` |
| `/console` | `cmd_console_status` | `console.py` |

---

## States & State Map (~120 states)

### Main Menu Navigation
| State Constant | Handler | Source | Purpose |
|----------------|---------|--------|---------|
| `MAIN_MENU` | `step_main_menu` | `main_menu.py` | Top-level menu routing |

### Member Management (`members.py` + `referral.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `MM_MENU` | `step_mm_menu` | Sub-menu: New Member, Top Up, Check, Ranks, Referral |
| `MM_LOOKUP` | `step_mm_lookup` | Member info lookup |

### First Purchase / New Member Flow (`members.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `NM_NAME` | `step_nm_name` | Customer name entry |
| `NM_PHONE` | `step_nm_phone` | Phone number entry |
| `NM_EMAIL` | `step_nm_email` | Email entry |
| `NM_ID` | `step_nm_id` | Member ID confirmation |
| `NM_AMT` | `step_nm_amt` | Purchase amount |
| `NM_GIFT_PIN` | `step_nm_gift_pin` | Gift card PIN |
| `NM_KPAY` | `step_nm_kpay` | KPay payment |
| `NM_REFERRAL` | `step_nm_referral` | Referral code |
| `NM_CONFIRM` | `step_nm_confirm` | Final confirm |

### Top Up Flow (`members.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `TU_MEMBER` | `step_tu_member` | Member selection |
| `TU_AMT` | `step_tu_amt` | Amount entry |
| `TU_KPAY` | `step_tu_kpay` | KPay amount |
| `TU_CONFIRM` | `step_tu_confirm` | Confirm & save |

### Daily Sales Flow (`sales.py` — core flow)
| State | Handler | Purpose |
|-------|---------|---------|
| `MEMBER` | `step_member` | Select/sell member (incl. search) |
| `CONSOLE` | `step_console` | Select console |
| `MINS` | `step_mins` | Enter play minutes |
| `ADJUST_TIME` | `step_adjust_time` | ±10 min time adjustment (session flows) |
| `FOOD_MENU` | `step_food_menu` | Food/drink selection |
| `FOOD_QTY` | `step_food_qty` | Food quantity |
| `CONFIRM_SUMMARY` | `step_confirm` | Review summary |
| `DISCOUNT` | `step_discount` | Discount entry |
| `PROMO_SELECT` | `step_promo_select` | Promotion selection |
| `BUNDLE_FOC` | `step_bundle_foc` | Bundle/FOC selection |
| `KPAY_AMT` | `step_kpay` | KPay amount |
| `SALE_CONFIRM` | `step_sale_confirm` | Final save |

### Session → Sales Bridge States (`sales.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `SESSION_SHORTFALL` | `step_session_shortfall` | Wallet insufficient — Top Up/Cash Down/Skip |
| `DS_MEMBER_IN_SESSION` | `step_ds_member_in_session` | Active member session conflict |
| `DS_CONSOLE_IN_SESSION` | `step_ds_console_in_session` | Active console session conflict |

### Console Menu (`console.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `CONSOLE_MENU` | `step_console_menu` | Console status, start/end session, game change |
| `END_SESSION_SELECT` | `step_end_session` | End active session |

### Console Booking (`booking.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `BOOK_LINK` | `step_book_link` | Link booking type |
| `BOOK_CONSOLE` | `step_book_console` | Console selection |
| `BOOK_MEMBER` | `step_book_member` | Member (or guest) selection |
| `BOOK_GAME` | `step_book_game` | Game selection |
| `BOOK_MINS` | `step_book_mins` | Duration / timer setup |
| `BOOK_DUP_WARN` | `step_book_dup_warn` | Duplicate session warning |

### Game Change for Active Session (`console.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `GAME_CHANGE_CONS` | `step_game_change_cons` | Select console |
| `GAME_CHANGE_GAME` | `step_game_change_game` | Select new game |

### Game Library (`games.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `GAME_MENU` | `step_game_menu` | View/Add/Del/Edit games |
| `GAME_ADD_TITLE` | `step_game_add_title` | Game title entry |
| `GAME_ADD_PLATFORM` | `step_game_add_platform` | Platform selection |
| `GAME_ADD_GENRE` | `step_game_add_genre` | Genre entry |
| `GAME_ADD_STATUS` | `step_game_add_status` | Status selection |
| `GAME_DEL_SELECT` | `step_game_del_select` | Delete game selection |
| `GAME_EDIT_SELECT` | `step_game_edit_select` | Edit game selection |
| `GAME_EDIT_FIELD` | `step_game_edit_field` | Edit field selection |
| `GAME_EDIT_VALUE` | `step_game_edit_value` | Edit value entry |

### Game Discs Record (`games.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `DISC_SELECT` | `step_disc_select` | Disc selection |
| `DISC_SET_QTY` | `step_disc_set_qty` | Set disc quantity |

### Console-Game Install (`ginst.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `GINST_MENU` | `step_ginst_menu` | View/Add/Del installs |
| `GINST_VIEW_CONS` | `step_ginst_view_cons` | View console installs |
| `GINST_ADD_CONS` | `step_ginst_add_cons` | Select console |
| `GINST_ADD_GAME` | `step_ginst_add_game` | Enter game name |
| `GINST_ADD_TYPE` | `step_ginst_add_type` | Install type (HDD/Disc/SSD) |
| `GINST_DEL_CONS` | `step_ginst_del_cons` | Select console to remove from |
| `GINST_DEL_GAME` | `step_ginst_del_game` | Select game to remove |

### External SSD Management (`ssd_disc.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `SSD_MENU` | `step_ssd_menu` | View/Add/Del/Transfer/Return |
| `SSD_VIEW_SSD` | `step_ssd_view` | View SSD contents |
| `SSD_ADD_SSD` | `step_ssd_add_ssd` | Select SSD |
| `SSD_ADD_GAME` | `step_ssd_add_game` | Game name |
| `SSD_ADD_TYPE` | `step_ssd_add_type` | Install type |
| `SSD_DEL_SSD` | `step_ssd_del_ssd` | Select SSD |
| `SSD_DEL_GAME` | `step_ssd_del_game` | Select game |
| `SSD_XFER_SSD` | `step_ssd_xfer_ssd` | Source SSD |
| `SSD_XFER_GAME` | `step_ssd_xfer_game` | Select game |
| `SSD_XFER_CONS` | `step_ssd_xfer_cons` | Target console |
| `SSD_RET_CONS` | `step_ssd_ret_cons` | Source console |
| `SSD_RET_GAME` | `step_ssd_ret_game` | Select game to return |

### Console CRUD (`console_mgmt.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `CON_MGMT_MENU` | `step_con_mgmt_menu` | Add/Del console |
| `CON_ADD_ID` | `step_con_add_id` | Console ID |
| `CON_ADD_TYPE` | `step_con_add_type` | Console type |
| `CON_ADD_MULT` | `step_con_add_mult` | Rate multiplier |
| `CON_DEL_SELECT` | `step_con_del_select` | Delete console |

### Staff Advance Booking (`booking_flow.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `SBK_CONSOLE` | `step_sbk_console` | Console selection |
| `SBK_CUST_NAME` | `step_sbk_cust_name` | Customer name |
| `SBK_DATE` | `step_sbk_date` | Date (today/tomorrow/custom) |
| `SBK_TIME` | `step_sbk_time` | Time slot |
| `SBK_DUR` | `step_sbk_dur` | Duration |
| `SBK_GAME` | `step_sbk_game` | Game selection |
| `SBK_CONFIRM` | `step_sbk_confirm` | Confirm booking |

### Stock Management
| State | Handler | Source | Purpose |
|-------|---------|--------|---------|
| `STOCK_PIN` | `step_stock_pin` | `stock.py` | PIN auth |
| `STOCK_MENU` | `step_stock_menu` | `stock.py` | Sub-menu |
| `STOCK_ITEM` | `step_stock_item` | `stock.py` | Item selection (stock out) |
| `STOCK_QTY` | `step_stock_qty` | `stock.py` | Quantity (stock out) |

### Stock In / Restock (`stock_in.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `SI_ITEM` | `step_si_item` | Item selection |
| `SI_QTY` | `step_si_qty` | Quantity |
| `SI_COST` | `step_si_cost` | Cost price |
| `SI_CART` | `step_si_cart` | Cart review |
| `SI_PAY` | `step_si_pay` | Payment method |
| `SI_PAY_SPLIT` | `step_si_pay_split` | Split payment (Cash+KPay) |
| `SI_CONFIRM` | `step_si_confirm` | Final confirm |

### Attendance (`attendance.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `ATTEND_STAFF` | `step_attend_staff` | Staff selection |
| `ATTEND_LEAVE` | `step_attend_leave` | Leave days |
| `ATTEND_LATE` | `step_attend_late` | Late count |
| `ATTEND_DEDUCT` | `step_attend_deduct` | Per-late deduction |

### Admin Panel (`admin.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `ADMIN_PIN` | `step_admin_pin` | PIN verification |
| `ADMIN_MENU` | `step_admin_menu` | Admin sub-menu |

### Salary Advance (`salary_adv.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `SAL_ADV_STAFF` | `step_sal_adv_staff` | Staff selection |
| `SAL_ADV_AMT` | `step_sal_adv_amt` | Amount |
| `SAL_ADV_PAY` | `step_sal_adv_pay` | Payment method |
| `SAL_ADV_CONFIRM` | `step_sal_adv_confirm` | Confirm |

### Waitlist (`waitlist.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `WL_MENU` | `step_wl_menu` | View/Notify/Refresh/Remove |

### Referral Code (`referral.py`)
| State | Handler | Purpose |
|-------|---------|---------|
| `REFERRAL_CODE` | `step_referral_code` | Referral code entry |

### Finance Module (`finance.py` — 50+ states)
| State | Handler | Purpose |
|-------|---------|---------|
| `FINANCE_MENU` | `step_finance_menu` | Finance sub-menu |

**OPEX:** `OPEX_CAT`, `OPEX_DESC`, `OPEX_AMT`, `OPEX_ACCT`, `OPEX_PAY`, `OPEX_CONFIRM`

**Assets:** `ASSET_NAME`, `ASSET_CAT`, `ASSET_DATE`, `ASSET_COST`, `ASSET_QTY`, `ASSET_LIFE`, `ASSET_SALVAGE`, `ASSET_PAY`, `ASSET_CONFIRM`

**Asset Disposal:** `ASSET_DISPOSE_SEL`, `ASSET_DISPOSE_DATE`, `ASSET_DISPOSE_QTY`, `ASSET_DISPOSE_PROCEEDS`, `ASSET_DISPOSE_CONFIRM`

**Prepaid Expenses:** `PREPAID_DESC`, `PREPAID_CAT`, `PREPAID_AMT`, `PREPAID_ACCT`, `PREPAID_START`, `PREPAID_END`, `PREPAID_CONFIRM`

**Account Transfers:** `ACCT_TRF_FROM`, `ACCT_TRF_TO`, `ACCT_TRF_AMT`, `ACCT_TRF_NOTE`, `ACCT_TRF_CONFIRM`

**Payables:** `PAY_VENDOR`, `PAY_DESC`, `PAY_AMT`, `PAY_DUE`, `PAY_ACCT`, `PAY_CONFIRM`, `PAY_SETTLE_LIST`, `PAY_SETTLE_ACCT`, `PAY_SETTLE_CONFIRM`

**Receivables:** `REC_CUST`, `REC_DESC`, `REC_AMT`, `REC_DUE`, `REC_ACCT`, `REC_CONFIRM`, `REC_SETTLE_LIST`, `REC_SETTLE_ACCT`, `REC_SETTLE_CONFIRM`

**Reports:** `FIN_REPORT_MENU`

**Capital:** `CAP_ACCT`, `CAP_AMT`, `CAP_CONFIRM`

**Shareholders:** `SHARE_NAME`, `SHARE_ROLE`, `SHARE_CAP`, `SHARE_OWN`, `SHARE_CONFIRM`

**Advance Payments:** `ADVPAY_PARTY`, `ADVPAY_DESC`, `ADVPAY_AMT`, `ADVPAY_ACCT`, `ADVPAY_DUE`, `ADVPAY_NOTE`, `ADVPAY_CONFIRM`, `ADVPAY_LIST`, `ADVPAY_SETTLE_CONFIRM`

---

## Fallbacks (42, same as entry points + `/finance`)

All entry point CommandHandlers are duplicated as fallbacks, plus `/finance` → `cmd_finance` (which is only in fallbacks, not entry points — this is worth noting).

---

## Global Handlers (9 total, registered outside ConversationHandler)

| Group | Handler Type | Pattern | Handler | Source |
|-------|-------------|---------|---------|--------|
| -999 | TypeHandler(Update) | All | `_auth_middleware` | `app.py` |
| -1 | MessageHandler | TEXT | `handle_custom_extend_reply` | `booking_flow.py` |
| 0 | CallbackQueryHandler | `^ext:` | `cb_extend_timer` | `booking.py` |
| 0 | CallbackQueryHandler | `^bkm:(approve\|reject):\d+$` | `cb_booking_mgmt` | `admin_bookings.py` |
| 0 | CallbackQueryHandler | `^wl:(notify\|remove):\d+$` | `cb_wl_action` | `waitlist.py` |
| 0 | CallbackQueryHandler | `^bkc:\d+$` | `cb_cancel_booking` | `booking_flow.py` |
| 0 | CallbackQueryHandler | `^bkcr:\d+:\w+$` | `cb_cancel_with_reason` | `booking_flow.py` |
| 0 | CallbackQueryHandler | `^bkarr:\d+$\|^bkns:\d+$` | `cb_booking_arrive` | `booking_flow.py` |
| 10 | MessageHandler | TEXT | `handle_cancel_note_input` | `booking_flow.py` |

---

## Navigation Flow Map

```
MAIN MENU
├── 📝 Daily Sales (BTN_DAILY_SALES / BTN_NEW_SALE)
│   └── Daily Sales Flow: MEMBER → CONSOLE → MINS → FOOD MENU → CONFIRM → DISCOUNT → KPAY → SALE_CONFIRM
│       ├── [Guest]: Rate × multiplier billing
│       └── [Member]: Wallet deduction
│           ├── Insufficient → SESSION_SHORTFALL (TopUp / CashDown / Skip)
│           └── Active session? → DS_MEMBER_IN_SESSION / DS_CONSOLE_IN_SESSION
│
├── 💳 Member Management (BTN_MEMBER_MGMT) → MM_MENU
│   ├── 🆕 New Member (BTN_FIRST_PURCHASE) → NM_NAME→NM_PHONE→...→NM_CONFIRM
│   ├── 💰 Top Up (BTN_TOP_UP) → TU_MEMBER→TU_AMT→TU_KPAY→TU_CONFIRM
│   ├── 🔍 Check Member (BTN_CHECK_MEMBER) → MM_LOOKUP
│   ├── 📋 Rank Bonuses (BTN_VIEW_RANKS)
│   └── 🎁 Referral Code (BTN_ASSIGN_REFERRAL) → REFERRAL_CODE
│
├── 🕹️ Consoles (BTN_CONSOLES) → CONSOLE_MENU
│   ├── 📊 Status ကြည့် (BTN_STATUS_BOARD)
│   ├── ▶️ Session စတင် (BTN_START_SESSION) → BOOK_CONSOLE→BOOK_MEMBER→BOOK_GAME→BOOK_MINS
│   ├── ⏹️ Session ဆုံး (BTN_END_SESSION) → END_SESSION_SELECT → Sales Flow
│   ├── 🔄 Game ပြောင်း (BTN_CHANGE_GAME) → GAME_CHANGE_CONS→GAME_CHANGE_GAME
│   ├── 🖥️ Console Install (BTN_CONSOLE_INSTALL) → GINST_MENU
│   │   ├── 📋 View Installs (BTN_GINST_VIEW)
│   │   ├── ➕ Add Install (BTN_GINST_ADD) → GINST_ADD_CONS→GAME→TYPE
│   │   └── ❌ Remove Install (BTN_GINST_REMOVE) → GINST_DEL_CONS→GAME
│   ├── 📀 External SSD (BTN_SSD_MANAGE) → SSD_MENU
│   │   ├── 📋 View (SSD_VIEW_SSD) | ➕ Add (SSD_ADD_SSD→GAME→TYPE)
│   │   ├── ❌ Remove (SSD_DEL_SSD→GAME)
│   │   ├── 🔄 Transfer (SSD_XFER_SSD→GAME→CONS)
│   │   └── ↩️ Return (SSD_RET_CONS→GAME)
│   └── ⚙️ Console စီမံ (BTN_CON_MANAGE) → CON_MGMT_MENU
│       ├── ➕ Add Console (CON_ADD_ID→TYPE→MULT)
│       └── 🗑️ Delete Console (CON_DEL_SELECT)
│
├── 📊 Today's Report (BTN_TODAY_REPORT)
│
├── 📅 Customer Booking (BTN_STAFF_BOOK) → BOOK_CONSOLE→CUST_NAME→DATE→TIME→DUR→GAME→CONFIRM
│   ├── ➕ New Booking (BTN_SBK_NEW)
│   ├── ✅ Confirmed Bookings (BTN_SBK_CONFIRMED)
│   └── ⏳ Waitlist (BTN_SBK_WAITLIST) → WL_MENU
│
├── 📊 Inventory (BTN_INVENTORY_VIEW)
│
├── 💹 Financial Report (BTN_FINANCIAL_REPORT)
│
├── 🎮 Game Library (BTN_GAME_LIB_MENU) → GAME_MENU
│   ├── 📋 View (BTN_VIEW_GAMES) | ➕ Add (BTN_ADD_GAME) → TITLE→PLATFORM→GENRE→STATUS
│   ├── 🗑️ Delete (BTN_DEL_GAME) → GAME_DEL_SELECT
│   ├── ✏️ Edit (BTN_EDIT_GAME) → GAME_EDIT_SELECT→FIELD→VALUE
│   └── 💿 Discs (BTN_DISC_RECORD) → DISC_SELECT→DISC_SET_QTY
│
└── 🔧 Admin Panel (BTN_ADMIN) → ADMIN_PIN → ADMIN_MENU
    ├── 📅 Attendance (BTN_ADMIN_ATTEND) → ATTEND_STAFF→LEAVE→LATE→DEDUCT
    ├── 📊 Monthly P&L (BTN_ADMIN_PNL)
    ├── 💵 Cash Flow (BTN_ADMIN_CF)
    ├── 💳 Card Liability (BTN_ADMIN_LIB)
    ├── 📋 Pending Bookings (BTN_ADMIN_BOOK)
    ├── 💸 Salary Advance (BTN_ADMIN_SAL_ADV) → STAFF→AMT→PAY→CONFIRM
    ├── 📊 Promo Reports (BTN_PROMO_REPORTS)
    ├── 📦 Stock Update (BTN_STOCK_UPDATE) → STOCK_PIN → STOCK_MENU
    │   ├── 📦 Stock Out (BTN_STOCK_OUT) → STOCK_ITEM→STOCK_QTY
    │   ├── 📥 Stock In (BTN_STOCK_IN_M) → SI_ITEM→QTY→COST→CART→PAY→CONFIRM
    │   └── 📊 Inventory View (BTN_INVENTORY_VIEW)
    ├── 📈 Staff KPI (BTN_STAFF_KPI)
    ├── 💰 Payroll (BTN_PAYROLL)
    └── 💼 Finance (BTN_FINANCE) → FINANCE_MENU
        ├── OPEX (20+ states), Assets (15+), Prepaid (7)
        ├── Transfers (5), Payables (9), Receivables (9)
        ├── Capital (3), Shareholders (5)
        ├── Advance Payments (9)
        └── Reports, P&L, Balance Sheet, Depreciation, Setup
```

---

## Issues Found

### 🔴 CRITICAL — None Found
All ConversationHandler state functions, entry point handlers, and fallback handlers have their corresponding function definitions in the handler modules. No missing handler functions.

### 🟡 WARNING — Design Inconsistencies

**1. Standalone Fallback Handlers Use Different Function Names Than ConversationHandler Entry Points**

In `bot/app.py`, the standalone fallback `CommandHandler` for-loop uses different function names than the equivalent entry in the main `ConversationHandler`:

| Command | Conv Handler | Standalone Fallback | Notes |
|---------|-------------|---------------------|-------|
| `/kpi` | `cmd_kpi_cmd` (payroll.py:229) | `cmd_staff_kpi` (broadcast.py:82) | Sends different content! Conv uses PIN gate; standalone shows full KPI report |
| `/payroll` | `cmd_payroll_cmd` (payroll.py:225) | `cmd_payroll` (payroll.py:160) | Conv uses PIN gate; standalone shows payroll directly |
| `/setattend` | `cmd_setattend_cmd` (attendance.py:13) | `cmd_setattend` (attendance.py:17) | Same file but different wrappers |

**Impact:** When a user is OUTSIDE the ConversationHandler (fresh `/start` not yet triggered), `/kpi`, `/payroll`, and `/setattend` call different functions that SKIP the PIN authentication wall. This means cold invocations bypass security for KPI and payroll.

**2. `/finance` Only in Standalone Fallbacks, Not in Entry Points**

The `/finance` command is registered as a standalone fallback (`cmd_finance`) but NOT as a ConversationHandler entry point. This means `/finance` works for cold starts but would not work during an active conversation flow.

**3. Bot Database Shows Entry Points Correctly**

The BTN_ constants listed in `__init__.py` `__all__` match all the constants defined. But the `STOCK_ACCESS_PIN`, `CUSTOMER_BOT_TOKEN`, `STAFF_NOTIFY_CHAT`, `N8N_SESSION_WEBHOOK`, `N8N_BOOKING_WEBHOOK` are listed in `__all__` alongside state constants — these are config values, not state constants, but they're mixed in.

### 🟢 INFO — Architecture Notes

**1. Single Massive ConversationHandler**
All ~120 states are in a single `ConversationHandler`. This is manageable but makes it difficult to add new features without touching `app.py`. Consider splitting into sub-conversations using `ConversationHandler` nesting.

**2. No `__all__` / explicit exports in handler files**
All handler files use wildcard imports in `__init__.py` (`from .admin import *`), which means any public name from any handler file is accessible. This works because of the giant `__all__` in `bot/__init__.py`, but makes it hard to trace which functions come from which file.

**3. Duplicate Import in sales.py Line 1**
`sales.py` has `from bot import now_mmt` on line 1 BEFORE the module docstring on line 3. This is technically valid Python but unusual — the import is placed above the docstring.

---

## Button Label Map (`BTN_*` → Label Text)

All BTN_* constants are defined in `bot/__init__.py` (lines 1227–1414).

### Navigation Buttons
| Constant | Label |
|----------|-------|
| `BTN_BACK` | "⬅️ ပြန်သွား" |
| `BTN_BACK_MAIN` | "⬅️ Main Menu သို့ပြန်" |
| `BTN_DONE` | "Done ✅" |
| `BTN_YES` | "Yes ✅" |
| `BTN_SAVE` | "သိမ်းမည် ✅" |
| `BTN_CANCEL` | "❌ Cancel" |
| `BTN_CONFIRM_SAVE` | "✅ Confirm & Save" |
| `BTN_CLEAR_CART` | "🗑️ Clear Cart" |
| `NAV_ROW` | `[BTN_BACK, BTN_CANCEL]` |

### Main Menu Buttons
| Constant | Label |
|----------|-------|
| `BTN_DAILY_SALES` | "📝 Daily Sales" |
| `BTN_NEW_SALE` | "📝 New Sale" |
| `BTN_MEMBER_MGMT` | "💳 Member Management" |
| `BTN_CONSOLES` | "🕹️ Consoles" |
| `BTN_TODAY_REPORT` | "📊 Today's Report" |
| `BTN_STAFF_BOOK` | "📅 Customer Booking" |
| `BTN_INVENTORY_VIEW` | "📊 Inventory ကြည့်ရှု" |
| `BTN_FINANCIAL_REPORT` | "💹 Financial Report" |
| `BTN_ADMIN` | "🔧 Admin Panel" |

### Console Menu Buttons
| Constant | Label |
|----------|-------|
| `BTN_CONSOLE_STATUS` | "🕹️ Console Status" |
| `BTN_CONSOLE_BOOK` | "📋 New Booking" |
| `BTN_START_SESSION` | "▶️ Session စတင်" |
| `BTN_END_SESSION` | "⏹️ Session ဆုံး" |
| `BTN_STATUS_BOARD` | "📊 Status ကြည့်" |
| `BTN_GAME_LIB_MENU` | "🎮 Game Library" |
| `BTN_CON_MANAGE` | "⚙️ Console စီမံ" |
| `BTN_CONSOLE_INSTALL` | "🖥️ Console Install" |
| `BTN_SKIP_GAME` | "⏭ ဂိမ်း မထည့်" |
| `BTN_CHANGE_GAME` | "🔄 Game ပြောင်း" |

### Session Management Buttons
| Constant | Label |
|----------|-------|
| `BTN_YES_END` | "✅ Yes — ဆုံးမည်" |
| `BTN_NO_BACK` | "❌ No — ပြန်" |
| `BTN_YES_END_SESSION` | "✅ Session ကို End မည်" |
| `BTN_NO_RESELECT` | "❌ ပြန်ရွေး" |
| `BTN_BOOK_PROCEED` | "⚠️ ဒါပဲ ဆက်ဖွင့်မည်" |
| `BTN_SKIP_TIMER` | "⏭ Skip (Timer မလိုပါ)" |
| `BTN_CANCEL_BOOKING` | "🚫 Cancel Booking" |

### Shortfall / Payment Buttons
| Constant | Label |
|----------|-------|
| `BTN_CASH_DOWN` | "💵 Cash Down (ချက်ချင်းပေး)" |
| `BTN_TOPUP_SESSION` | "💳 Top Up ပြီး ဆက်" |
| `BTN_SKIP_SALES` | "⏭ Skip (မမှတ်တမ်းတင်)" |

### Stock Buttons
| Constant | Label |
|----------|-------|
| `BTN_STOCK_UPDATE` | "📦 Stock Update" |
| `BTN_STOCK_OUT` | "📦 Stock Out (ထုတ်ယူ)" |
| `BTN_STOCK_IN_M` | "📥 Stock In (ဝယ်ယူ)" |
| `BTN_SI_SPLIT` | "💰 ခွဲပေး (Cash + KPay)" |
| `BTN_SI_ADD` | "➕ Item ထပ်ထည့်" |
| `BTN_SI_FINISH` | "💳 Payment & Save All" |

### Discount / Promo Buttons
| Constant | Label |
|----------|-------|
| `BTN_SKIP_DISC` | "⏩ Skip (Discount မထည့်)" |
| `BTN_PROMO_APPLY` | "🎁 Promotion ထည်သွင်း" |
| `BTN_MANUAL_DISC` | "✏️ Manual Discount ရိုက်" |

### Booking Buttons
| Constant | Label |
|----------|-------|
| `BTN_SBK_TODAY` | "📅 ယနေ့" |
| `BTN_SBK_TOMORROW` | "📅 မနက်ဖြန်" |
| `BTN_SBK_CUSTOM` | "✏️ ရက်ထည့်" |
| `BTN_SBK_SKIP_PHONE` | "⏭ Phone မထည့်" |
| `BTN_SBK_SKIP_GAME` | "⏭ Game မထည့်" |
| `BTN_SBK_CONFIRM_BOOK` | "✅ Booking ဖန်တီးမည်" |
| `BTN_SBK_NEW` | "➕ New Booking" |
| `BTN_SBK_CONFIRMED` | "✅ Confirmed Bookings" |
| `BTN_SBK_WAITLIST` | "⏳ Waitlist" |

### Game Library Buttons
| Constant | Label |
|----------|-------|
| `BTN_ADD_GAME` | "➕ ဂိမ်းထည့်" |
| `BTN_VIEW_GAMES` | "📋 ဂိမ်းစာရင်း" |
| `BTN_DEL_GAME` | "🗑️ ဂိမ်းဖျက်" |
| `BTN_EDIT_GAME` | "✏️ Edit Game" |
| `BTN_DISC_RECORD` | "💿 Game Discs" |

### Console Management Buttons
| Constant | Label |
|----------|-------|
| `BTN_ADD_CONSOLE` | "➕ Console ထည့်" |
| `BTN_LIST_CONSOLE` | "📋 Console စာရင်း" |
| `BTN_DEL_CONSOLE` | "🗑️ Console ဖျက်" |

### GINST Buttons
| Constant | Label |
|----------|-------|
| `BTN_GINST_VIEW` | "📋 ဘယ် Console မှာ ဘာ ရှိသလဲ" |
| `BTN_GINST_ADD` | "➕ Install မှတ်သား" |
| `BTN_GINST_REMOVE` | "❌ Install ဖျက်" |
| `BTN_GINST_HDD` | "💾 HDD (Internal)" |
| `BTN_GINST_DISC` | "💿 Disc" |
| `BTN_GINST_SSD` | "🔌 Portable SSD" |

### SSD Buttons
| Constant | Label |
|----------|-------|
| `BTN_SSD_MANAGE` | "📀 External SSD" |
| `BTN_SSD_VIEW` | "📋 SSD ထဲ ဘာ ရှိသလဲ" |
| `BTN_SSD_ADD` | "➕ SSD ထဲ ဂိမ်း ထည့်" |
| `BTN_SSD_REMOVE` | "❌ SSD မှ ဂိမ်း ဖျက်" |
| `BTN_SSD_TRANSFER` | "🔄 SSD → Console (Transfer)" |
| `BTN_SSD_RETURN` | "↩️ Console → SSD (Return)" |
| `BTN_SSD_T1` | "Samsung T1 Shield" |
| `BTN_SSD_BLUE` | "Sandisk Extreme (Blue)" |
| `BTN_SSD_GREY` | "Sandisk Extreme (Grey)" |

### Admin Panel Buttons
| Constant | Label |
|----------|-------|
| `BTN_ADMIN_ATTEND` | "📅 Attendance" |
| `BTN_ADMIN_PNL` | "📊 Monthly P&L" |
| `BTN_ADMIN_CF` | "💵 Cash Flow" |
| `BTN_ADMIN_LIB` | "💳 Card Liability" |
| `BTN_ADMIN_BOOK` | "📋 Pending Bookings" |
| `BTN_ADMIN_SAL_ADV` | "💸 Salary Advance" |
| `BTN_PROMO_REPORTS` | "📊 Promo Reports" |
| `BTN_STAFF_KPI` | "📈 Staff KPI" |
| `BTN_PAYROLL` | "💰 Payroll" |
| `BTN_STOCK_UPDATE` | "📦 Stock Update" |
| `BTN_FINANCE` | "💼 Finance" |

### Waitlist Buttons
| Constant | Label |
|----------|-------|
| `BTN_WL_VIEW_WAITING` | "📋 Waiting List ကြည့်" |
| `BTN_WL_VIEW_ALL` | "📂 All Entries ကြည့်" |
| `BTN_WL_NOTIFY_NEXT` | "🔔 Next ကို Notify" |
| `BTN_WL_REFRESH` | "🔄 Refresh" |

### Member Management Buttons
| Constant | Label |
|----------|-------|
| `BTN_FIRST_PURCHASE` | "🆕 New Member" |
| `BTN_TOP_UP` | "💰 Top Up" |
| `BTN_CHECK_MEMBER` | "🔍 Check Member" |
| `BTN_VIEW_RANKS` | "📋 Rank Bonuses" |
| `BTN_ASSIGN_REFERRAL` | "🎁 Referral Code သတ်မှတ်" |
| `BTN_CONFIRM_ID` | "✅ Confirm ID" |
| `BTN_NM_CUSTOM` | "✏️ Enter Different Amount" |
| `BTN_NM_GIFT` | "🎁 Gift / Free Card" |
| `BTN_SKIP_PHONE` | "⏩ Skip" |
| `BTN_SKIP_EMAIL` | "⏩ Email မထည့်" |
| `BTN_SKIP_REFERRAL` | "⏩ Referral Code မထည့်" |

### Finance Buttons
| Constant | Label |
|----------|-------|
| `BTN_FIN_OPEX` | "📝 OPEX" |
| `BTN_FIN_ASSET` | "🏢 Asset" |
| `BTN_FIN_PREPAID` | "📅 Prepaid" |
| `BTN_FIN_TRANSFER` | "💸 Transfer" |
| `BTN_FIN_PAYABLE` | "📤 Payable" |
| `BTN_FIN_RECEIVABLE` | "📥 Receivable" |
| `BTN_FIN_REPORT` | "📊 Reports" |
| `BTN_FIN_SETUP` | "⚙️ Sheet Setup" |
| `BTN_FIN_PNL` | "📊 P&L Report" |
| `BTN_FIN_BS` | "🏦 Balance Sheet" |
| `BTN_FIN_ACCTS` | "💰 Accounts" |
| `BTN_FIN_DEPR` | "📉 Depreciation" |
| `BTN_FIN_ASSET_DISPOSE` | "🔄 Dispose Asset" |
| `BTN_FIN_PROFIT_SHARE` | "💸 Profit Sharing" |
| `BTN_FIN_CAPITAL` | "🏦 Capital" |
| `BTN_FIN_SHAREHOLDER` | "👥 Partners" |
| `BTN_FIN_SETTLE_PAY` | "✅ Settle Pay" |
| `BTN_FIN_SETTLE_REC` | "✅ Settle Rec" |
| `BTN_FIN_ADVPAY` | "💵 Advance" |
| `BTN_FIN_SETTLE_ADVPAY` | "✅ Settle Adv" |
| `BTN_FIN_BACK` | "⬅️ Finance Menu" |

---

## Handler-to-File Mapping Summary

| Handler File | Functions Exported | Conversation Flow(s) |
|-------------|-------------------|---------------------|
| `admin.py` | `cmd_admin`, `step_admin_pin`, `step_admin_menu`, `show_admin_menu` | Admin PIN gate + sub-menu |
| `admin_bookings.py` | `cmd_admin_bookings`, `cmd_approve_booking`, `cmd_reject_booking`, `cb_booking_mgmt` | Booking approval/rejection |
| `attendance.py` | `cmd_setattend`, `cmd_setattend_cmd`, `step_attend_*` | Attendance recording wizard |
| `booking.py` | `step_book_*`, `cb_extend_timer`, `start_session` | Console booking + session start |
| `booking_flow.py` | `cmd_staff_booking`, `cmd_cancel_booking`, `cb_cancel_booking`, `cb_cancel_with_reason`, `cb_booking_arrive`, `handle_cancel_note_input`, `handle_custom_extend_reply`, `step_sbk_*` | Staff advance booking + cancel/arrive/no-show |
| `broadcast.py` | `cmd_broadcast`, `cmd_staff_kpi` | Staff KPI display |
| `commands.py` | `cmd_cancel`, `cmd_topup`, `cmd_member_mgmt`, `cmd_check_member`, `cmd_newmember`, `cmd_ranks` | Command shortcuts |
| `console.py` | `show_console_menu`, `step_console_menu`, `step_end_session`, `step_game_change_*`, `cmd_console_status` | Console status + session end + game change |
| `console_mgmt.py` | `step_con_*`, `show_con_mgmt_menu` | Console CRUD |
| `discount.py` | `prompt_discount`, `step_discount`, `step_promo_select`, `step_bundle_foc` | Discount/promo during sale |
| `finance.py` | `cmd_finance`, `cmd_finance_setup`, `step_finance_menu`, `show_fin_*`, `step_opex_*`, `step_asset_*`, `step_prepaid_*`, `step_acct_trf_*`, `step_pay_*`, `step_rec_*`, `step_cap_*`, `step_share_*`, `step_advpay_*` | Full finance module (~50 functions) |
| `games.py` | `show_game_menu`, `cmd_game_lib_view`, `step_game_*`, `step_disc_*` | Game library CRUD + discs |
| `ginst.py` | `show_ginst_menu`, `step_ginst_*` | Console game install records |
| `help.py` | `cmd_help`, `cmd_version`, `error_handler` | Help/version commands, error handler |
| `main_menu.py` | `show_main_menu`, `step_main_menu` | Main menu entry + routing |
| `members.py` | `show_mm_menu`, `step_mm_*`, `step_nm_*`, `step_tu_*`, `prompt_tu_member`, `show_rank_info`, etc. | Member management + new member + top up |
| `notify.py` | `_notify_customer`, `get_customer_chat_id`, `_check_low_balance_alert` | Utility functions (no conv states) |
| `payroll.py` | `cmd_payroll`, `cmd_payroll_cmd`, `cmd_kpi_cmd` | Payroll calculation + KPI PIN gate |
| `referral.py` | `step_referral_code` | Referral code assignment |
| `reports.py` | `cmd_today_report`, `cmd_financial_report`, `cmd_daily_report`, `cmd_weekly_report`, `cmd_member_insights`, `cmd_inventory`, `cmd_stocktoday` | All reports |
| `salary_adv.py` | `step_sal_adv_*` | Salary advance recording |
| `sales.py` | `prompt_member`, `step_member`, `step_console`, `step_mins`, `step_adjust_time`, `step_food_menu`, `step_food_qty`, `step_confirm`, `step_kpay`, `step_sale_confirm`, `cmd_sales_direct`, `launch_session_sale`, `step_session_shortfall`, `step_ds_member_in_session`, `step_ds_console_in_session`, `prompt_session_shortfall` | Core daily sales flow (most complex module) |
| `ssd_disc.py` | `show_ssd_menu`, `step_ssd_*` | External SSD management |
| `stock.py` | `cmd_stock_menu`, `cmd_stockout_direct`, `step_stock_pin`, `step_stock_menu`, `step_stock_item`, `step_stock_qty` | Stock out + stock menu |
| `stock_in.py` | `cmd_stockin_direct`, `step_si_*` | Stock in / restock |
| `waitlist.py` | `cmd_waitlist_mgmt`, `step_wl_menu`, `cb_wl_action` | Waitlist management |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Handler files | 27 |
| Total states in ConversationHandler | ~120 |
| Entry points | 42 |
| Fallbacks | 42 |
| Global handlers (outside conv) | 9 (1 auth + 7 callback + 1 message) |
| Standalone CommandHandlers | 41 |
| BTN_* constants defined | ~100 |
| Finance module states | 50+ |
| Syntax errors | 0 ✅ |
| Missing handler functions | 0 ✅ |
| Design inconsistencies | 3 ⚠️ |

---

## Recommendation Priorities

1. **HIGH:** Fix the standalone fallback mismatch for `/kpi`, `/payroll`, `/setattend` — these bypass PIN security in cold-start scenarios
2. **MEDIUM:** Add `/finance` to ConversationHandler entry points (currently only in standalone fallbacks)
3. **LOW:** Move `from bot import now_mmt` in `sales.py` to after the docstring
4. **NICE-TO-HAVE:** Split the monolithic ConversationHandler into nested sub-conversations for maintainability
5. **NICE-TO-HAVE:** Add explicit `__all__` to each handler module instead of wildcard re-exports
