import os, sys
sys.path.insert(0, '/root/psvibe_api_server')
from mysql_db import execute as _me
from mysql_db import query as _mq

# Check full details for bookings 255 and 256
rows = _mq("SELECT id, console_id, member_id, status, booking_date, start_time, end_time, created_at FROM console_booking WHERE id IN (255,256) ORDER BY id")
for r in rows:
    print(f"#{r['id']}: console={r['console_id']} member={r['member_id']} status={r['status']} date={r['booking_date']} start={r['start_time']} end={r['end_time']} created={r['created_at']}")

# Delete the older duplicate booking 255 (keep 256)
print("\nDeleting booking #255 (duplicate Active for C-03)...")
_me("DELETE FROM console_booking WHERE id=255")
print("Done.")

# Verify
rows = _mq("SELECT id, console_id, member_id, status FROM console_booking WHERE console_id='C-03' AND status IN ('Active','Confirmed') ORDER BY id")
print(f"\nRemaining Active bookings for C-03: {len(rows)}")
for r in rows:
    print(f"  #{r['id']}: {r['console_id']} | {r['member_id']} | {r['status']}")
