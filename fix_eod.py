#!/usr/bin/env python3
"""Quick fix script for eod_report.py"""
f = open('/root/psvibe-sales-bot/scripts/eod_report.py')
c = f.read()
f.close()

# Fix 1: Use member_wallets instead of members for count
c = c.replace('FROM members WHERE', 'FROM member_wallets WHERE')
c = c.replace("SELECT COUNT(*) FROM members\")", 'SELECT COUNT(*) FROM member_wallets\")')

# Fix 2: Payment method — properly handle 3-column output (method, amount, count)
old_payment = '''            lines.append(f"  {method} : <b>{fmt_k(amt)} Ks</b>")'''
new_payment = '''            cnt_part = f" (x{int(float(parts[2]))})" if len(parts) >= 3 and parts[2] and parts[2].isdigit() and int(parts[2]) > 0 else ""
            lines.append(f"  {method}{cnt_part} : <b>{fmt_k(amt)} Ks</b>")'''
c = c.replace(old_payment, new_payment)

f = open('/root/psvibe-sales-bot/scripts/eod_report.py', 'w')
f.write(c)
f.close()
print('Fixed eod_report.py successfully')
