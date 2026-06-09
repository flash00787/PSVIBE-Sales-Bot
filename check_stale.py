#!/usr/bin/env python3
"""Investigate stale sessions, dashboard issues, and BS member liability."""
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
            v = v.strip().strip('"').strip("'")
            if k:
                os.environ.setdefault(k, v)

import json, pymysql
conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password='PsVibe@2026_Rotated!', database='psvibe_api', cursorclass=pymysql.cursors.DictCursor)
cur = conn.cursor()

# Check console_status for C-01
cur.execute("SELECT * FROM console_status WHERE console_id='C-01' OR console_id=' -C-01' OR console_id=' - C-01'")
print("=== Console Status C-01 ===")
for r in cur.fetchall():
    print(r)

# Check all console_status records
cur.execute("SELECT console_id, status, current_member, start_time FROM console_status ORDER BY console_id")
print("\n=== All Console Status ===")
for r in cur.fetchall():
    print(f"{r['console_id']}: {r['status']} | member={r.get('current_member','-')} | start={str(r.get('start_time') or '')[:19]}")

# Find stale bookings (Active with no end_time or past 24h)
cur.execute("SELECT id, console_id, status, start_time, end_time, member_id FROM console_booking WHERE status='Active'")
print("\n=== Stale Active Bookings ===")
for r in cur.fetchall():
    sid = r['console_id']
    print(f"Booking #{r['id']}: C='{sid}' | member={r['member_id']} | start={str(r['start_time'])[:19]} | end={r.get('end_time')}")

# Check what the dashboard shows (what the frontend sees is the API)
import urllib.request
KEY = os.environ.get('API_KEY', '')
req = urllib.request.Request('http://localhost:8000/dashboard/api/dashboard-summary', headers={'X-API-Key': KEY})
try:
    res = json.load(urllib.request.urlopen(req, timeout=5))
    print(f"\n=== Dashboard Summary ===\n{json.dumps(res, indent=2)[:500]}")
except Exception as e:
    print(f"\nDashboard API error: {e}")
    req2 = urllib.request.Request('http://localhost:8000/dashboard/api/health', headers={'X-API-Key': KEY})
    try:
        res2 = json.load(urllib.request.urlopen(req2, timeout=5))
        print(f"Health: {res2}")
    except:
        print("Dashboard health API also failed")
