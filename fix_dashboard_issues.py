#!/usr/bin/env python3
"""Fix: clean stale bookings, update dashboard console query, add BS member breakdown."""
import pymysql, os

# ── Part 1: Clean stale booking #247 (C-01, console_status=Free but booking=Active) ──
conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password='PsVibe@2026_Rotated!', database='psvibe_api')
cur = conn.cursor()

cur.execute("UPDATE console_booking SET status='Done', end_time=NOW() WHERE id=247 AND status='Active'")
print(f"Booking #247: {cur.rowcount} row(s) affected → Done ✅")
conn.commit()

# ── Part 2: Fix dashboard GET /consoles to respect console_status ──
f = '/root/psvibe_api_server/dashboard_routes.py'
with open(f) as fh:
    t = fh.read()

# Fix the LEFT JOIN to only show bookings when console is Active OR when there's a genuine booking
old_q = '''        rows = _mysql_query("""
            SELECT c.console_id as id, c.console_id as name, c.status,
                   cb.id as booking_id, cb.member_id as customer_name,
                   cb.start_time, cb.end_time, cb.status as booking_status
            FROM console_status c
            LEFT JOIN console_booking cb ON c.console_id = cb.console_id
                AND DATE(cb.booking_date) = %s
                AND cb.status IN ('Active', 'Confirmed')
            ORDER BY c.console_id
        """, (today,))'''

new_q = '''        rows = _mysql_query("""
            SELECT c.console_id as id, c.console_id as name, c.status,
                   cb.id as booking_id, cb.member_id as customer_name,
                   cb.start_time, cb.end_time, cb.status as booking_status
            FROM console_status c
            LEFT JOIN console_booking cb ON c.console_id = cb.console_id
                AND DATE(cb.booking_date) = %s
                AND cb.status IN ('Active', 'Confirmed')
                AND c.status = 'Active'
            ORDER BY c.console_id
        """, (today,))'''

t = t.replace(old_q, new_q, 1)
print("Dashboard /consoles: LEFT JOIN respects console_status ✅")

# ── Part 3: Add member liability breakdown to Balance Sheet ──
old_bs_end = '''            "liabilities":{"member_liability":round(member_liab,0),"total":round(member_liab,0)},'''

new_bs_end = '''            "liabilities":{"member_liability":round(member_liab,0),"member_details":_member_details,"total":round(member_liab,0)},'''

t = t.replace(old_bs_end, new_bs_end, 1)
# We need to capture _member_details from the loop above
# Let me check if the member_liab loop already has per-member data
# It does: _r2 contains member_id, paid, mins, balance_mins
# Need to build _member_details in the loop

# Insert member detail collection before the loop
old_loop = '''        _member_liab_val = 0.0
        for _r2 in _ml2:'''

new_loop = '''        _member_liab_val = 0.0
        _member_details = []
        for _r2 in _ml2:'''

t = t.replace(old_loop, new_loop, 1)

# Add detail collection inside the loop
old_detail = '''            if _mins2 > 0 and _paid2 > 0 and _bal2 > 0:
                _member_liab_val += _paid2 / _mins2 * _bal2'''

new_detail = '''            if _mins2 > 0 and _paid2 > 0 and _bal2 > 0:
                _member_liab_val += _paid2 / _mins2 * _bal2
                _member_details.append({
                    "member_id": _r2["member_id"],
                    "balance_mins": _bal2,
                    "paid": _paid2,
                    "mins_bought": _mins2,
                    "rate_per_min": round(_paid2 / _mins2, 0),
                    "liability": round(_paid2 / _mins2 * _bal2, 0)
                })'''

t = t.replace(old_detail, new_detail, 1)
print("BS: member liability details added ✅")

with open(f, 'w') as fh:
    fh.write(t)
compile(t, f, 'exec')
print("All fixes applied ✅")
