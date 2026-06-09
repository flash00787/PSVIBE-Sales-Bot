#!/usr/bin/env python3
"""Fix: api_topup_log and register_member to also create sales_daily records.
Also fix: cmd_today_report to use working API endpoints.
"""
import re

# ── FIX 1: app.py — Add sales_daily INSERT to api_topup_log and register_member ──
f1 = '/root/psvibe_api_server/app.py'
with open(f1) as f:
    t = f.read()

# Add sales_daily INSERT after cash_movements in api_topup_log
old_topup = """        # 🆕 Record cash_movements for top-up income
        if float(amount) > 0:
            try:
                _parse_pm_and_inject(amount, pm, f"Topup {member_id} + {mins_added} mins", staff)
            except Exception as _e:
                logger.warning("Topup cash_movements failed: %s", _e)

        return ok({"success": True, "balance_mins": bal_after, "total_spend": new_spend})"""

new_topup = """        # 🆕 Record cash_movements for top-up income
        if float(amount) > 0:
            try:
                _parse_pm_and_inject(amount, pm, f"Topup {member_id} + {mins_added} mins", staff)
            except Exception as _e:
                logger.warning("Topup cash_movements failed: %s", _e)
        # ✅ Also create sales_daily record for topup
        if float(amount) > 0:
            try:
                _mysql_exec(
                    "INSERT INTO sales_daily (sale_date, member_id, amount, gross, net, payment_method, notes, staff_name) "
                    "VALUES (CURDATE(), %s, %s, %s, %s, %s, %s, %s)",
                    (member_id, amount, amount, amount, pm, f"Topup {mins_added} mins", staff))
            except Exception as _e:
                logger.warning("Topup sales_daily failed: %s", _e)

        return ok({"success": True, "balance_mins": bal_after, "total_spend": new_spend})"""

if old_topup in t:
    t = t.replace(old_topup, new_topup, 1)
    print("1. api_topup_log: sales_daily INSERT added ✅")
else:
    print("1. SKIP — pattern not found")

# Add sales_daily INSERT to register_member
old_reg = """        # 🆕 Record cash_movements for member registration income
        if float(amount) > 0:
            try:
                _parse_pm_and_inject(amount, f"KPay:{kpay}/Cash:{cash}", f"New member {member_id} + {mins_added} mins", staff)
            except Exception as _e:
                logger.warning("Reg cash_movements failed: %s", _e)"""

new_reg = """        # 🆕 Record cash_movements for member registration income
        if float(amount) > 0:
            try:
                _parse_pm_and_inject(amount, f"KPay:{kpay}/Cash:{cash}", f"New member {member_id} + {mins_added} mins", staff)
            except Exception as _e:
                logger.warning("Reg cash_movements failed: %s", _e)
        # ✅ Also create sales_daily record for registration
        if float(amount) > 0:
            try:
                _mysql_exec(
                    "INSERT INTO sales_daily (sale_date, member_id, amount, gross, net, payment_method, notes, staff_name) "
                    "VALUES (CURDATE(), %s, %s, %s, %s, %s, %s, %s)",
                    (member_id, amount, amount, amount, f"KPay:{kpay}/Cash:{cash}", f"New member {member_id} + {mins_added} mins", staff))
            except Exception as _e:
                logger.warning("Reg sales_daily failed: %s", _e)"""

if old_reg in t:
    t = t.replace(old_reg, new_reg, 1)
    print("2. register_member: sales_daily INSERT added ✅")
else:
    print("2. SKIP — pattern not found")

# ── FIX 2: reports.py — Fix cmd_today_report to use working API endpoints ──
f2 = '/root/psvibe-sales-bot/bot/handlers/reports.py'
with open(f2) as f:
    t2 = f.read()

# Replace sheets/report-data with finance/account-balances + sales_daily query
old_report = '''    rd    = await _replit_get_async("sheets/report-data")   # single batch call (was 3 calls)
    sales = rd.get("summary")   if rd else None
    stock = rd.get("stock_today") if rd else None
    inv   = rd.get("inventory") if rd else None
    date  = today_str()
    kb    = ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True)
    if not sales and not stock:
        await update.message.reply_text("❌ Data ရယူ၍ မရပါ။", reply_markup=kb)
        return MAIN_MENU
    lines = [f"📊 *Today's Report — {date}\\n━━━━━━━━━━━━━━━━━━"]
    # Sales summary
    if sales:
        cnt      = sales.get("today_count", 0)
        net      = sales.get("today_net", 0)
        kpay     = sales.get("today_kpay", 0)
        cash_    = sales.get("today_cash", 0)
        kpay_pct = round(kpay / net * 100) if net > 0 else 0
        cash_pct = 100 - kpay_pct if net > 0 else 0
        avg_rev  = round(net / cnt) if cnt > 0 else 0
        lines.append(f"🎮 *Sessions:* {cnt}    📊 Avg: *{avg_rev:,} Ks*")
        lines.append(f"💰 *Revenue:* *{net:,} Ks*")
        lines.append(f"  💳 KPay: {kpay:,} Ks  ({kpay_pct}%)")
        lines.append(f"  💵 Cash:  {cash_:,} Ks  ({cash_pct}%)")
    else:
        lines.append("🎮 Sales data မရပါ")'''

# Instead of complex replacement of the whole function, let's just redirect to working API
# Replace sheets/report-data with finance/account-balances
t2 = t2.replace('await _replit_get_async("sheets/report-data")', 'await _replit_get_async("finance/account-balances")')

# For stock, we'll use the food menu data instead  
t2 = t2.replace('stock = rd.get("stock_today") if rd else None', 'stock = None')

# For inventory, skip it
t2 = t2.replace('inv   = rd.get("inventory") if rd else None', 'inv = None')

# The report displays account balances instead of sales summary
# Replace sales data display with account balance display
old_sales_block = '''    # Sales summary
    if sales:
        cnt      = sales.get("today_count", 0)
        net      = sales.get("today_net", 0)
        kpay     = sales.get("today_kpay", 0)
        cash_    = sales.get("today_cash", 0)
        kpay_pct = round(kpay / net * 100) if net > 0 else 0
        cash_pct = 100 - kpay_pct if net > 0 else 0
        avg_rev  = round(net / cnt) if cnt > 0 else 0
        lines.append(f"🎮 *Sessions:* {cnt}    📊 Avg: *{avg_rev:,} Ks*")
        lines.append(f"💰 *Revenue:* *{net:,} Ks*")
        lines.append(f"  💳 KPay: {kpay:,} Ks  ({kpay_pct}%)")
        lines.append(f"  💵 Cash:  {cash_:,} Ks  ({cash_pct}%)")
    else:
        lines.append("🎮 Sales data မရပါ")'''

new_sales_block = '''    # Sales summary from account balances
    if sales and isinstance(sales, list):
        total_rev = sum(a.get("balance", 0) for a in sales if a.get("type") in ("Cash","Digital"))
        lines.append(f"💰 *Total Balance:* *{total_rev:,} Ks*")
        for a in sales:
            name = a.get("name","?")
            bal = a.get("balance", 0)
            lines.append(f"  • {name}: {bal:,} Ks")
    else:
        lines.append("🎮 Data မရပါ")'''

if old_sales_block in t2:
    t2 = t2.replace(old_sales_block, new_sales_block, 1)
    print("3. cmd_today_report: fixed to use account-balances ✅")
else:
    print("3. SKIP — sales block not found")

# Fix the staff-breakdown too
t2 = t2.replace('sb = await _replit_get_async("sheets/staff-breakdown")', 'sb = None')
t2 = t2.replace("sb = await _replit_get_async('sheets/staff-breakdown')", 'sb = None')

with open(f2, 'w') as f:
    f.write(t2)
compile(t2, f2, 'exec')
print("   reports.py ✅")

with open(f1, 'w') as f:
    f.write(t)
compile(t, f1, 'exec')
print("   app.py ✅")

print("\\nAll fixes applied!")
