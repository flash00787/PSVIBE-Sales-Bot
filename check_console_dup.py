import os, sys
sys.path.insert(0, '/root/psvibe_api_server')
from mysql_db import query as _mq

rows = _mq("SELECT id, console_id, member_id, status, booking_date FROM console_booking WHERE console_id='C-03' AND status IN ('Active','Confirmed') ORDER BY id")
print(f'Bookings for C-03: {len(rows)} rows')
for r in rows:
    print(f"  #{r['id']}: {r['member_id']} | {r['status']} | {r['booking_date']}")
