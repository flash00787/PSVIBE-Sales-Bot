#!/usr/bin/env python3
"""Fix P&L double-counting: remove topup_rev from total_revenue, exclude topup sales_daily from game_rev.
Only wallet_consumed (FIFO) counts as topup-derived revenue.
"""
f = '/root/psvibe_api_server/dashboard_routes.py'
with open(f) as fh:
    t = fh.read()

# Fix P&L: exclude topup sales_daily records from game_rev
old_rev = '''        rev_rows = _mq("SELECT net, gross, amount FROM sales_daily WHERE DATE_FORMAT(created_at, '%%Y-%%m') = %s AND gross > 0", (ym,))
        game_rev = 0.0; food_rev = 0.0; discounts = 0.0
        for r in rev_rows:
            g = float(r.get("gross") or 0)
            n = float(r.get("net") or 0)
            a = float(r.get("amount") or 0)
            discounts += (g - n)
            # Food has NO discount: food_rev = min(gross - amount, net)
            food_amt = max(g - a, 0)
            food_rev += min(food_amt, n)
            # Game gets the remaining after food: game_rev = max(net - food_amt, 0)
            game_rev += max(n - food_amt, 0)'''

new_rev = '''        rev_rows = _mq("SELECT net, gross, amount, notes FROM sales_daily WHERE DATE_FORMAT(created_at, '%%Y-%%m') = %s AND gross > 0", (ym,))
        game_rev = 0.0; food_rev = 0.0; discounts = 0.0; topup_sales = 0.0
        for r in rev_rows:
            g = float(r.get("gross") or 0)
            n = float(r.get("net") or 0)
            a = float(r.get("amount") or 0)
            notes = (r.get("notes") or "")
            discounts += (g - n)
            # Food has NO discount: food_rev = min(gross - amount, net)
            food_amt = max(g - a, 0)
            food_rev += min(food_amt, n)
            # Exclude topup entries from game_rev (topups are deferred revenue)
            # Only wallet_consumed (FIFO) counts as topup-derived revenue
            if notes.startswith("Topup") or notes.startswith("New member"):
                topup_sales += max(n - food_amt, 0)
            else:
                # Game gets the remaining after food: game_rev = max(net - food_amt, 0)
                game_rev += max(n - food_amt, 0)'''

t = t.replace(old_rev, new_rev, 1)
print("1. P&L: topup sales_daily excluded from game_rev ✅")

# Remove topup_rev from total_revenue (only wallet_consumed counts)
old_total = '        total_revenue = game_rev + food_rev + topup_rev + wallet_consumed'
new_total = '        total_revenue = game_rev + food_rev + wallet_consumed'

t = t.replace(old_total, new_total, 1)
print("2. P&L: topup_rev removed from total_revenue (was double-counting) ✅")

# Update the revenue dict to show topup_rev as separate info (not included in total)
old_dict = '''            "revenue": {"game_revenue": round(game_rev,0), "food_revenue": round(food_rev,0), "topup_revenue": round(topup_rev,0), "wallet_consumed": round(wallet_consumed,0), "discounts": round(discounts,0), "total_revenue": round(total_revenue,0)},'''

new_dict = '''            "revenue": {"game_revenue": round(game_rev,0), "food_revenue": round(food_rev,0), "topup_revenue": round(topup_rev,0), "wallet_consumed": round(wallet_consumed,0), "topup_deferred": round(topup_sales,0), "discounts": round(discounts,0), "total_revenue": round(total_revenue,0)},'''

t = t.replace(old_dict, new_dict, 1)
print("3. P&L: topup_deferred field added ✅")

# Also fix the Balance Sheet: it currently has topup_revenue which is fine (not used in calc)
# But ensure retained earnings correctly subtracts member_liability

with open(f, 'w') as fh:
    fh.write(t)
compile(t, f, 'exec')
print("✅ OK")
