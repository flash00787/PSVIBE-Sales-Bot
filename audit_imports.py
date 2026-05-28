import sys
sys.path.insert(0, '/root/psvibe-sales-bot')
import importlib, traceback

modules = [
    'bot', 'bot.handlers', 'bot.utils', 'customer_bot', 'customer_bot.data',
    'bot.api_client', 'bot.handlers.commands', 'bot.handlers.admin',
    'bot.handlers.booking_flow', 'bot.handlers.main_menu',
    'bot.handlers.members', 'bot.handlers.sales', 'bot.handlers.stock',
    'bot.handlers.finance', 'bot.handlers.waitlist', 'bot.handlers.attendance',
    'bot.handlers.payroll', 'bot.handlers.referral', 'bot.handlers.reports',
    'bot.handlers.broadcast', 'bot.handlers.notify',
    'bot.handlers.games', 'bot.handlers.help', 'bot.handlers.discount',
    'bot.handlers.console', 'bot.handlers.console_mgmt',
    'bot.handlers.ginst', 'bot.handlers.ssd_disc', 'bot.handlers.salary_adv',
    'bot.handlers.admin_bookings', 'bot.handlers.booking',
    'bot.handlers.stock_in', 'bot.keep_alive', 'bot.report_generator',
    'customer_bot.handlers', 'customer_bot.ai', 'customer_bot.api',
    'customer_bot.booking', 'customer_bot.booking_handlers',
    'main', 'send_daily_report', 'sqlite.db_manager', 'sqlite.setup',
    'check_sheets_access'
]

for m in modules:
    try:
        importlib.import_module(m)
        print(f'OK: {m}')
    except Exception:
        print(f'FAIL: {m} -> {traceback.format_exc().strip().split(chr(10))[-1]}')
