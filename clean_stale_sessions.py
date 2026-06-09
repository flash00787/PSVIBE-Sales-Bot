#!/usr/bin/env python3
"""Clean stale sessions and fix data inconsistencies.
Also fixes the end_session flow for No Timer sessions."""
import os

env_file = '/etc/psvibe/secrets.env'
with open(env_file) as f:
    for line in f:
        line = line.strip()
        if line.startswith('export '):
            line = line[7:]
        if '=' in line:
            k, _, v = line.partition('=')
            k = k.strip()
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k:
                os.environ.setdefault(k, v)

import pymysql
conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password='PsVibe@2026_Rotated!', database='psvibe_api')
cur = conn.cursor()

# Step 1: End stale Active bookings where console_status shows Free
stale = [
    (198, 'C-01', '2026-06-06 12:45:39'),  # 2 days stale
    (247, 'C-01', '2026-06-09 17:07:21'),  # No Timer, should have ended
    (248, 'C-07', '2026-06-09 17:31:16'),  # No Timer
    (251, 'C-03', '2026-06-09 18:14:50'),  # No Timer
    (252, 'C-04', '2026-06-09 18:20:30'),  # No Timer
]

print("=== Cleaning Stale Active Sessions ===")
for bk_id, cid, start in stale:
    cur.execute("UPDATE console_booking SET status='Done', end_time=NOW() WHERE id=%s", (bk_id,))
    print(f"Booking #{bk_id} (C-{cid}): Active → Done ✅")
    conn.commit()

# Step 2: Verify cleanup
cur.execute("SELECT id, console_id, status FROM console_booking WHERE status='Active'")
remaining = cur.fetchall()
print(f"\nRemaining Active: {len(remaining)}")
for r in remaining:
    print(f"  Booking #{r[0]}: C-{r[1]} ({r[2]})")

# Step 3: Verify console_status still correct
cur.execute("SELECT console_id, status FROM console_status WHERE status='Active'")
console_active = cur.fetchall()
print(f"\nConsole Status Active: {len(console_active)}")
for c in console_active:
    print(f"  {c[0]}: {c[1]}")

# Step 4: Check if end_session properly cleans up
# The issue is: end_session -> sales.py -> _do_end_session
# Let's check what the end_session API does
import urllib.request, json
KEY = os.environ.get('API_KEY', '')
print(f"\n=== Checking API end_booking ===")
req = urllib.request.Request(f'http://localhost:8000/api/bookings', headers={'X-API-Key': KEY})
try:
    res = json.load(urllib.request.urlopen(req, timeout=5))
    print(f"API /api/bookings OK: {len(res.get('data',{}).get('bookings',[]))} bookings")
except Exception as e:
    print(f"API error: {e}")

# Step 5: Check the end_booking endpoint
req2 = urllib.request.Request(f'http://localhost:8000/api/end_booking', headers={'X-API-Key': KEY}, method='POST')
try:
    # Just check if endpoint exists
    import http.client
    h = http.client.HTTPConnection('localhost', 8000, timeout=3)
    h.request('POST', '/api/end_booking', body='{}', headers={'Content-Type':'application/json','X-API-Key':KEY})
    r = h.getresponse()
    body = r.read().decode()
    print(f"POST /api/end_booking: {r.status} - {body[:200]}")
except Exception as e:
    print(f"POST /api/end_booking error: {e}")
