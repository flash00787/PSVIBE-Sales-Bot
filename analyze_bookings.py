import os, sys
sys.path.insert(0, '/root/psvibe_api_server')
from mysql_db import execute as _me, query as _mq

# 1. Fix stale booking #198 - C-01 ended on June 6 but never marked Done
print("Stale booking #198 (C-01, Jun 6):")
raw = _mq("SELECT id, console_id, status, start_time, end_time, created_at FROM console_booking WHERE id=198")
for r in raw:
    print(f"  Before: id={r['id']} status={r['status']} start={r['start_time']} end={r['end_time']} created={r['created_at']}")

_me("UPDATE console_booking SET status='Done', end_time=NOW() WHERE id=198 AND status='Active'")
print("  → Set to Done ✅")

# 2. Check all stale Active bookings that should be Done
print("\nChecking all Active bookings vs console_status:")
rows = _mq("""
    SELECT b.id, b.console_id, b.status, c.status as cs_status
    FROM console_booking b
    JOIN console_status c ON b.console_id = c.console_id
    WHERE b.status = 'Active'
    AND c.status != 'Active'
""")
for r in rows:
    print(f"  #{r['id']}: {r['console_id']} (bk={r['status']}, console={r['cs_status']})")
    
if not rows:
    print("  ✅ No stale Active bookings remaining")

# 3. Fix: Check session_end logic 
# Let's look at how the end_session API works
import re
with open('/root/psvibe_api_server/app.py', 'r') as f:
    content = f.read()

# Find end_session function
idx = content.find("def end_session")
if idx >= 0:
    print("\nend_session function found at byte", idx)
    # Show first 100 chars
    print(content[idx:idx+200])
    
# Also find where booking status is set to Done
idx2 = content.find("status.*Done")
if idx2 >= 0:
    print(f"\nBooking Done logic at byte {idx2}:")
    print(content[max(0,idx2-100):idx2+100])

# Find session_end route
idx3 = content.find("def api_end_session")
if idx3 >= 0:
    print(f"\napi_end_session route found at byte {idx3}")
    print(content[idx3:idx3+500])
else:
    print("\napi_end_session NOT found in app.py")
    # Check dashboard_routes
    with open('/root/psvibe_api_server/dashboard_routes.py', 'r') as f:
        dr = f.read()
    idx4 = dr.find("end.session")
    if idx4 >= 0:
        print(f"  But found in dashboard_routes.py at byte {idx4}")
        print(dr[max(0,idx4-50):idx4+200])
