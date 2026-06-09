import os, sys
sys.path.insert(0, '/root/psvibe_api_server')
from mysql_db import query as _mq

# First check what columns exist
cols = _mq("DESCRIBE console_booking")
print("console_booking columns:")
for c in cols:
    print(f"  {c['Field']} ({c['Type']})")

print()

# Get ALL Active bookings with full details
rows = _mq("""
    SELECT b.id, b.console_id, b.member_id, b.status, 
           b.booking_date, b.start_time, b.end_time,
           b.created_at,
           m.name as member_name
    FROM console_booking b
    LEFT JOIN members m ON b.member_id = m.member_id
    WHERE b.status IN ('Active', 'Confirmed')
    ORDER BY b.console_id, b.id
""")

print(f"Total Active/Confirmed bookings: {len(rows)}")
print()

for r in rows:
    print(f"#{r['id']}: {r['console_id']} | member={r['member_id']} ({r['member_name']}) | status={r['status']}")
    print(f"  booking_date={r['booking_date']} | start={r['start_time']} | end={r['end_time']}")
    print(f"  created={r['created_at']}")
    print()

# console_status active sessions
rows2 = _mq("SELECT console_id, status, current_member, start_time FROM console_status WHERE status = 'Active'")
print(f"Console Status - Active sessions: {len(rows2)}")
for r in rows2:
    print(f"  {r['console_id']}: {r['status']} | member={r['current_member']} | start={r['start_time']}")

# Check booking status vs console status mismatch
print()
rows3 = _mq("""
    SELECT b.id, b.console_id, b.status, c.status as console_status
    FROM console_booking b
    JOIN console_status c ON b.console_id = c.console_id
    WHERE b.status IN ('Active', 'Confirmed')
    AND c.status != 'Active'
""")
print(f"Bookings Active/Confirmed but console NOT Active: {len(rows3)}")
for r in rows3:
    print(f"  #{r['id']}: {r['console_id']} (bk_status={r['status']}, console_status={r['console_status']})")
