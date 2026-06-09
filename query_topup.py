#!/usr/bin/env python3
"""Query MySQL for topup_log payment methods."""
import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='PsVibe@MySQL2024!', database='psvibe_api')
cursor = conn.cursor()
cursor.execute("SELECT payment_method, COUNT(*), COALESCE(SUM(amount),0) FROM topup_log WHERE amount > 0 GROUP BY payment_method ORDER BY COUNT(*) DESC LIMIT 20")
for row in cursor.fetchall():
    print(f"  PM: '{row[0]}' | count={row[1]} | total={row[2]:,.0f} Ks")
conn.close()
