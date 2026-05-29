# bot/constants.py — All button labels and constants
#
# Extracted from bot/__init__.py to improve modularity.
# Imported back by __init__.py for 100% backward compatibility.
#   from bot.constants import *   # All BTN_*, NAV_ROW, category lists, etc.

import os

# ─────────────────────────────────────────
#  BUTTON LABELS
# ─────────────────────────────────────────
BTN_BACK         = "⬅️ ပြန်သွား"
BTN_BACK_MAIN    = "⬅️ Main Menu သို့ပြန်"
BTN_DONE         = "Done ✅"
BTN_YES          = "Yes ✅"
BTN_SAVE         = "သိမ်းမည် ✅"
BTN_NEW_SALE     = "📝 New Sale"
BTN_CANCEL       = "❌ Cancel"
BTN_CONFIRM_SAVE = "Confirm & Save"
BTN_PAY_DONE  = "Payment Done"
BTN_ADD_PAY   = "Add Payment Method"
BTN_NO_MORE   = "No More Payments"

# Attendance flow buttons
BTN_ATTEND_DONE = "✅ ပြီးပါပြီ"
BTN_ATTEND_SKIP = "⏭ Skip"

NAV_ROW = [BTN_BACK, BTN_CANCEL]   # appended to every wizard keyboard

# ── Finance Category Lists ──
OPEX_CATEGORIES = [
    "လစာ", "ငှားရမ်းခ", "မီတာခ", "အင်တာနက်",
    "ပြုပြင်စရိတ်", "ရုံးသုံးစရိတ်", "အခြား",
]
PAY_METHODS = ["Cash", "KPay", "WavePay", "Bank Transfer"]
ASSET_CATEGORIES = ["Furniture", "Equipment", "Electronics", "Vehicle", "Gaming Console", "Other"]
PREPAID_CATEGORIES = ["Rent", "Insurance", "Subscription", "Software License", "Other"]
FINANCE_ACCOUNTS = ["Cash", "KPay", "WavePay", "CB Bank", "AYA Bank", "Other"]
CAPITAL_ACCOUNTS = ["Cash", "KPay", "WavePay", "CB Bank", "AYA Bank", "Other"]
_SHARE_ROLES = ["Owner", "Partner", "Investor", "Staff"]

# Main menu
BTN_DAILY_SALES  = "🛒 Daily Sales"
BTN_MEMBER_MGMT  = "💳 Member Management"
BTN_TODAY_REPORT = "📊 Today's Report"
BTN_STOCK_UPDATE = "📦 Stock Update"
BTN_STAFF_KPI          = "📈 Staff KPI"
BTN_PAYROLL            = "💰 Payroll"
BTN_FINANCIAL_REPORT   = "💹 Financial Report"
BTN_ADMIN              = "🔧 Admin Panel"
BTN_ADMIN_ATTEND  = "📅 Attendance"
BTN_ADMIN_PNL     = "📊 Monthly P&L"
BTN_ADMIN_CF      = "💵 Cash Flow"
BTN_ADMIN_LIB     = "💳 Card Liability"
BTN_ADMIN_BOOK    = "📋 Pending Bookings"
BTN_ADMIN_SAL_ADV = "💸 Salary Advance"
BTN_PROMO_REPORTS = "📊 Promo Reports"
BTN_CONSOLE_STATUS = "🕹️ Console Status"
BTN_CONSOLE_BOOK   = "📋 New Booking"
# Console Management submenu
BTN_CONSOLES        = "🕹️ Consoles"
BTN_START_SESSION   = "▶️ Session စတင်"
BTN_END_SESSION     = "⏹️ Session ဆုံး"
BTN_STATUS_BOARD    = "📊 Status ကြည့်"
BTN_GAME_LIB_MENU   = "🎮 Game Library"
BTN_CON_MANAGE      = "⚙️ Console စီမံ"
# Game Library
BTN_ADD_GAME        = "➕ ဂိမ်းထည့်"
BTN_VIEW_GAMES      = "📋 ဂိမ်းစာရင်း"
BTN_DEL_GAME        = "🗑️ ဂိမ်းဖျက်"
# Console CRUD
BTN_ADD_CONSOLE     = "➕ Console ထည့်"
BTN_LIST_CONSOLE    = "📋 Console စာရင်း"
BTN_DEL_CONSOLE     = "🗑️ Console ဖျက်"
# Confirm/End
BTN_YES_END         = "✅ Yes — ဆုံးမည်"
BTN_NO_BACK         = "❌ No — ပြန်"
BTN_SI_SPLIT     = "💰 ခွဲပေး (Cash + KPay)"
BTN_STOCK_OUT        = "📦 Stock Out (ထုတ်ယူ)"
BTN_STOCK_IN_M       = "📥 Stock In (ဝယ်ယူ)"
BTN_INVENTORY_VIEW   = "📊 Inventory ကြည့်ရှု"
BTN_SKIP_DISC        = "⏩ Skip (Discount မထည့်)"
BTN_PROMO_APPLY      = "🎁 Promotion ထည်သွင်း"
BTN_MANUAL_DISC      = "✏️ Manual Discount ရိုက်"
# Session → Daily Sales bridge
BTN_CASH_DOWN        = "💵 Cash Down (ချက်ချင်းပေး)"
BTN_TOPUP_SESSION    = "💳 Top Up ပြီး ဆက်"
BTN_SKIP_SALES       = "⏭ Skip (မမှတ်တမ်းတင်)"
BTN_YES_END_SESSION  = "✅ Session ကို End မည်"
BTN_NO_RESELECT      = "❌ ပြန်ရွေး"
BTN_BOOK_PROCEED     = "⚠️ ဒါပဲ ဆက်ဖွင့်မည်"
BTN_SKIP_TIMER       = "⏭ Skip (Timer မလိုပါ)"
BTN_STAFF_BOOK       = "📅 Customer Booking"
BTN_CANCEL_BOOKING   = "🚫 Cancel Booking"
BTN_SBK_TODAY        = "📅 ယနေ့"
BTN_SBK_TOMORROW     = "📅 မနက်ဖြန်"
BTN_SBK_CUSTOM       = "✏️ ရက်ထည့်"
BTN_SBK_SKIP_PHONE   = "⏭ Phone မထည့်"
BTN_SBK_SKIP_GAME    = "⏭ Game မထည့်"
BTN_SBK_CONFIRM_BOOK = "✅ Booking ဖန်တီးမည်"
BTN_SBK_NEW          = "➕ New Booking"
BTN_SBK_CONFIRMED    = "✅ Confirmed Bookings"
BTN_SBK_WAITLIST     = "⏳ Waitlist"
# Waitlist management buttons
BTN_WL_VIEW_WAITING  = "📋 Waiting List ကြည့်"
BTN_WL_VIEW_ALL      = "📂 All Entries ကြည့်"
BTN_WL_NOTIFY_NEXT   = "🔔 Next ကို Notify"
BTN_WL_REFRESH       = "🔄 Refresh"
BTN_CONSOLE_INSTALL  = "🖥️ Console Install"
BTN_GINST_VIEW       = "📋 ဘယ် Console မှာ ဘာ ရှိသလဲ"
BTN_GINST_ADD        = "➕ Install မှတ်သား"
BTN_GINST_REMOVE     = "❌ Install ဖျက်"
BTN_GINST_HDD        = "💾 HDD (Internal)"
BTN_GINST_DISC       = "💿 Disc"
BTN_GINST_SSD        = "🔌 Portable SSD"
# External SSD Management
BTN_SKIP_GAME    = "⏭ ဂိမ်း မထည့်"
BTN_CHANGE_GAME  = "🔄 Game ပြောင်း"
BTN_SSD_MANAGE   = "📀 External SSD"
BTN_SSD_VIEW     = "📋 SSD ထဲ ဘာ ရှိသလဲ"
BTN_SSD_ADD      = "➕ SSD ထဲ ဂိမ်း ထည့်"
BTN_SSD_REMOVE   = "❌ SSD မှ ဂိမ်း ဖျက်"
BTN_SSD_TRANSFER = "🔄 SSD → Console (Transfer)"
BTN_SSD_RETURN   = "↩️ Console → SSD (Return)"
BTN_SSD_T1       = "Samsung T1 Shield"
BTN_SSD_BLUE     = "Sandisk Extreme (Blue)"
BTN_SSD_GREY     = "Sandisk Extreme (Grey)"
# Game Discs Record
BTN_DISC_RECORD  = "💿 Game Discs"
BTN_EDIT_GAME    = "✏️ Edit Game"

# ── Finance module buttons ──
BTN_FINANCE          = "💼 Finance"
BTN_FIN_OPEX         = "📝 OPEX"
BTN_FIN_ASSET        = "🏢 Asset"
BTN_FIN_PREPAID      = "📅 Prepaid"
BTN_FIN_TRANSFER     = "💸 Transfer"
BTN_FIN_PAYABLE      = "📤 Payable"
BTN_FIN_RECEIVABLE   = "📥 Receivable"
BTN_FIN_REPORT       = "📊 Reports"
BTN_FIN_SETUP        = "⚙️ Sheet Setup"
BTN_FIN_PNL          = "📊 P&L Report"
BTN_FIN_BS           = "🏦 Balance Sheet"
BTN_FIN_ACCTS        = "💰 Accounts"
BTN_FIN_DEPR         = "📉 Depreciation"
BTN_FIN_ASSET_DISPOSE = "🔄 Dispose Asset"
BTN_FIN_PROFIT_SHARE = "💸 Profit Sharing"
BTN_FIN_CAPITAL      = "🏦 Capital"
BTN_FIN_SHAREHOLDER  = "👥 Partners"
BTN_FIN_SETTLE_PAY   = "✅ Settle Pay"
BTN_FIN_SETTLE_REC   = "✅ Settle Rec"
BTN_FIN_ADVPAY       = "💵 Advance"
BTN_FIN_SETTLE_ADVPAY= "✅ Settle Adv"
BTN_FIN_BACK         = "⬅️ Finance Menu"

# ── SSD names (duplicated for clarity with BTN_SSD_* above) ──
SSD_NAMES: dict[str, str] = {
    "SSD-T1":   "Samsung T1 Shield",
    "SSD-Blue": "Sandisk Extreme (Blue)",
    "SSD-Grey": "Sandisk Extreme (Grey)",
}
SSD_BTN_TO_ID: dict[str, str] = {v: k for k, v in SSD_NAMES.items()}

# ── Environment-based config constants ──
STOCK_ACCESS_PIN    = os.environ["STOCK_PIN"]
CUSTOMER_BOT_TOKEN  = os.environ.get("CUSTOMER_BOT_TOKEN", "")
STAFF_NOTIFY_CHAT   = os.environ.get("STAFF_NOTIFY_CHAT", "")   # group chat ID for booking notifications
# Comma-separated Telegram user IDs allowed to use /broadcast (e.g. "12345678,87654321")
_BROADCAST_ADMIN_IDS: set[str] = {
    s.strip() for s in os.environ.get("ADMIN_USER_IDS", "").split(",") if s.strip()
}

# n8n Phase 2 — Session reminder webhook (restart-proof timer)
# Test URL  : https://psvibe.app.n8n.cloud/webhook-test/session-reminder
# Production : https://psvibe.app.n8n.cloud/webhook/session-reminder
N8N_SESSION_WEBHOOK  = os.environ.get("N8N_SESSION_WEBHOOK", "")
N8N_BOOKING_WEBHOOK  = os.environ.get("N8N_BOOKING_WEBHOOK", "")

# Member Management sub-menu
BTN_FIRST_PURCHASE = "🆕 New Member"
BTN_TOP_UP         = "💰 Top Up"
BTN_CHECK_MEMBER   = "🔍 Check Member"
BTN_VIEW_RANKS     = "📋 Rank Bonuses"
BTN_ASSIGN_REFERRAL = "🎁 Referral Code သတ်မှတ်"
BTN_CONFIRM_ID     = "✅ Confirm ID"
BTN_NM_CUSTOM      = "✏️ Enter Different Amount"
BTN_NM_GIFT        = "🎁 Gift / Free Card"
BTN_SKIP_PHONE     = "⏩ Skip"
BTN_SKIP_EMAIL     = "⏩ Email မထည့်"
BTN_SKIP_REFERRAL  = "⏩ Referral Code မထည့်"
BTN_CLEAR_CART     = "🗑️ Clear Cart"
BTN_SI_ADD         = "➕ Item ထပ်ထည့်"
BTN_SI_FINISH      = "💳 Payment & Save All"

# ── Rank emojis ──
RANK_EMOJI = {"Warrior": "⚔️", "Master": "🏅", "Immortal": "💎"}
