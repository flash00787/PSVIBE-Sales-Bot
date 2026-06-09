#!/usr/bin/env python3
"""Fix the sales_daily query to exclude topup notes, without using LIKE with % in SQL."""
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    src = f.read()

# Fix FB: line 1802 - incomplete SQL, add back proper filter
q1 = "rows = _mq(\"SELECT payment_method, net, notes FROM sales_daily WHERE payment_method IS NOT NULL AND payment_method != ''\")"
q1_old = src.find("rows = _mq(\"SELECT payment_method, net FROM sales_daily WHERE payment_method IS NOT NULL AND payment_method != ''")
if q1_old > 0:
    end = src.find('\n', q1_old)
    src = src[:q1_old] + "        " + q1 + src[end:]

# Fix BS: line 2144 - add notes to SELECT and use WHERE IN filter
q2 = src.find("SELECT payment_method, net FROM sales_daily WHERE payment_method IS NOT NULL AND payment_method != '' AND (notes IS NULL OR (notes NOT LIKE 'Topup%' AND notes NOT LIKE 'New member%'))")
if q2 > 0:
    old = "SELECT payment_method, net FROM sales_daily WHERE payment_method IS NOT NULL AND payment_method != '' AND (notes IS NULL OR (notes NOT LIKE 'Topup%' AND notes NOT LIKE 'New member%'))"
    new = "SELECT payment_method, net, notes FROM sales_daily WHERE payment_method IS NOT NULL AND payment_method != '' AND COALESCE(notes,'') NOT LIKE CONCAT(CHAR(84),CHAR(111),CHAR(112),CHAR(117),CHAR(112),CHAR(37)) AND COALESCE(notes,'') NOT LIKE CONCAT(CHAR(78),CHAR(101),CHAR(119),CHAR(32),CHAR(109),CHAR(101),CHAR(109),CHAR(98),CHAR(101),CHAR(114),CHAR(37))"
    src = src.replace(old, new, 1)

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(src)
try:
    compile(src, '/root/psvibe_api_server/dashboard_routes.py', 'exec')
    print("Syntax OK")
except SyntaxError as e:
    print(f"Error: {e}")
