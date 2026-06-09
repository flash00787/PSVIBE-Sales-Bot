#!/usr/bin/env python3
"""Query payment methods from sales_daily and topup_log."""
import pymysql
conn = pymysql.connect(host='127.0.0.1', user='root', password='PsVibe@MySQL2024!', database='psvibe_api')
c = conn.cursor()
print("=== Sales Daily PM (first 10) ===")
c.execute("SELECT DISTINCT payment_method FROM sales_daily WHERE payment_method IS NOT NULL AND payment_method != '' LIMIT 10")
for r in c.fetchall():
    print(f"  '{r[0]}'")
print("\n=== Topup Log PM (all) ===")
c.execute("SELECT DISTINCT payment_method, COUNT(*), SUM(amount) FROM topup_log WHERE amount > 0 GROUP BY payment_method")
for r in c.fetchall():
    print(f"  '{r[0]}' | count={r[1]} | total={r[2]:,.0f} Ks")
print("\n=== Sales Daily total amount ===")
c.execute("SELECT COALESCE(SUM(net),0) FROM sales_daily")
print(f"  Total Sales: {c.fetchone()[0]:,.0f} Ks")
print("\n=== Topup Log total amount ===")
c.execute("SELECT COALESCE(SUM(amount),0) FROM topup_log WHERE amount > 0")
print(f"  Total Topup: {c.fetchone()[0]:,.0f} Ks")
conn.close()
