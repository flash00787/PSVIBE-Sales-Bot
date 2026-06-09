# Add now_mmt and other needed helpers to handlers/__init__.py
# These won't cause circular imports because handlers/__init__.py 
# doesn't import from bot/__init__.py

path = '/root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py'
with open(path) as f:
    content = f.read()

# Append shared helpers at the end
helpers = '''

# ========== Shared helpers for all handler files ==========
import datetime
import pytz

def now_mmt():
    """Get current time in Asia/Yangon timezone (UTC+6:30)."""
    return datetime.datetime.now(pytz.timezone('Asia/Yangon')).strftime('%H:%M')

# Shared constants (used across handler files)
BTN_DAILY_SALES = "🛒 Daily Sales"
BTN_NEW_SALE = "🆕 New Sale"
BTN_MEMBER_MGMT = "👥 Member Management"
BTN_CONSOLES = "🕹️ Consoles"
BTN_TODAY_REPORT = "📋 Today Report"
BTN_STAFF_BOOK = "📅 Customer Booking"
BTN_INVENTORY_VIEW = "📦 View Inventory"
BTN_FINANCIAL_REPORT = "💰 Financial Report"
BTN_ADMIN = "⚙️ Admin Panel"
BTN_GAMES = "🎮 Games"
BTN_STOCK_MGMT = "📊 Stock Management"
BTN_DISC_MGMT = "🏷️ Discount Management"
BTN_SSD_DISC = "🔄 SSD Discount"
BTN_FOOD_SETUP = "🍽️ Food Setup"
BTN_ATTEND_DONE = "✅ ပြီးပါပြီ"
BTN_ATTEND_NEXT = "➡️ နောက် Staff"
BTN_ATTEND_SKIP = "⏩ Skip (0)"
STOCK_ACCESS_PIN = "1423"
ADMIN_PIN = "1423"
'''

with open(path, 'a') as f:
    f.write(helpers)

print('DONE: Added shared helpers to handlers/__init__.py')
