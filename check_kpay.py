#!/usr/bin/env python3
"""Check KPay balance calculation in detail."""
import os, sys, json, pymysql

with open('/etc/psvibe/secrets.env') as f:
    for line in f:
        line = line.strip()
        if line.startswith('export '):
            line = line[7:]
        if '=' in line:
            k, v = line.split('=', 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k == 'MYSQL_PASSWORD':
                os.environ['MPW'] = v

PW = ***'MPW', '')
conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password=*** database='psvibe_api', charset='utf8mb4')
cur = conn.cursor()

print("=== SALES DAILY with KPay ===")
cur.execute("SELECT id, payment_method, net, gross, created_at, notes FROM sales_daily WHERE payment_method LIKE '%KPay%' OR payment_method LIKE '%kpay%' ORDER BY id")
kpay_income = 0
for r in cur.fetchall():
    pm = r[1] or ''
    for part in pm.replace('|','/').split('/'):
        part = part.strip()
        if ':' in part:
            m, _, v = part.partition(':')
            m = m.strip().lower()
            if m in ('kpay', 'k-pay'):
                amt = float(v or 0)
                kpay_income += amt
                print(f"  #{r[0]}: KPay={amt} | net={r[2]} | {str(r[4])[:10]}")
print(f"Total KPay from sales_daily: {kpay_income}")

print("\n=== TOPUP LOG (all) ===")
cur.execute("SELECT id, payment_method, amount, member_id FROM topup_log WHERE amount > 0")
kpay_topup = 0
for r in cur.fetchall():
    pm = r[1] or ''
    for part in pm.replace('|','/').split('/'):
        part = part.strip()
        if ':' in part:
            m, _, v = part.partition(':')
            m = m.strip().lower()
            if m == 'kpay':
                amt = float(v or 0)
                kpay_topup += amt
                print(f"  #{r[0]}: KPay={amt} | {r[3]}")
print(f"Total KPay from topup: {kpay_topup}")

print("\n=== CASH MOVEMENTS (KPay) ===")
cur.execute("SELECT movement_type, amount, note, created_at FROM cash_movements WHERE account='KPay' ORDER BY created_at")
k_inj = k_ej = k_ti = k_to = 0
for r in cur.fetchall():
    mt, amt, note, dt = r[0], float(r[1] or 0), (r[2] or '')[:40], str(r[3])[:16]
    if mt == 'inject': k_inj += amt; print(f"  INJECT +{amt} | {note}")
    elif mt == 'eject': k_ej += amt; print(f"  EJECT -{amt} | {note}")
    elif mt == 'transfer_in': k_ti += amt; print(f"  T_IN +{amt}")
    elif mt == 'transfer_out': k_to += amt; print(f"  T_OUT -{amt}")

print("\n=== OPEX (KPay) ===")
cur.execute("SELECT COALESCE(SUM(amount),0) FROM opex WHERE LOWER(payment_method) LIKE '%kpay%'")
kpay_opex = float(cur.fetchone()[0] or 0)
print(f"OPEX: {kpay_opex}")

print("\n=== STOCK IN (KPay) ===")
cur.execute("SELECT COALESCE(SUM(quantity*unit_cost),0) FROM stock_in WHERE LOWER(payment_method) LIKE '%kpay%'")
kpay_stock = float(cur.fetchone()[0] or 0)
print(f"Stock In: {kpay_stock}")

print("\n=== EXPECTED BALANCE ===")
print(f"  Sales income:     +{kpay_income}")
print(f"  Topup income:     +{kpay_topup}")
print(f"  Inject:           +{k_inj}")
print(f"  Eject:            -{k_ej}")
print(f"  Transfer In:      +{k_ti}")
print(f"  Transfer Out:     -{k_to}")
expected = kpay_income + kpay_topup + k_inj - k_ej + k_ti - k_to
print(f"  =======================")
print(f"  Expected balance:  {expected}")
print(f"  Dashboard shows:   212333")

conn.close()
