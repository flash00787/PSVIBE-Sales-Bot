#!/usr/bin/env python3
"""Check console status and bookings on VPS."""
import urllib.request, json, sys

KEY = open('/etc/psvibe/secrets.env').read().split('export API_KEY="')[1].split('"')[0]

# Check console status
req = urllib.request.Request('http://localhost:8000/api/fetch_console_status', headers={'X-API-Key': KEY})
res = json.load(urllib.request.urlopen(req))
for c in res.get('data',{}).get('consoles',[]):
    sid = c.get('console_id','?')
    st = c.get('status','?')
    memb = c.get('current_member') or '-'
    ctype = c.get('console_type','?')
    start = c.get('start_time') or '-'
    cgame = c.get('current_game') or '-'
    print(f'{sid} ({ctype}): {st} | member={memb} | game={cgame} | start={str(start)[:19]}')

# Check C-01 booking
req2 = urllib.request.Request('http://localhost:8000/api/bookings?status=confirmed', headers={'X-API-Key': KEY})
res2 = json.load(urllib.request.urlopen(req2))
print('\n=== Confirmed Bookings ===')
for b in res2.get('data',{}).get('bookings',[]):
    print(f"#{b['id']}: {b.get('customerName','?')} | {b.get('date','?')} {b.get('timeSlot','?')} | {b.get('console_id','?')} | {b.get('status','?')}")

# Check active bookings
req3 = urllib.request.Request('http://localhost:8000/api/bookings?status=Active', headers={'X-API-Key': KEY})
res3 = json.load(urllib.request.urlopen(req3))
print('\n=== Active Bookings ===')
for b in res3.get('data',{}).get('bookings',[]):
    print(f"#{b['id']}: {b.get('customerName','?')} | {b.get('date','?')} {b.get('timeSlot','?')} | {b.get('console_id','?')} | {b.get('status','?')}")

# Check active sessions
print('\n=== Active Sessions (console_booking) ===')
import pymysql
conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password='PsVibe@2026_Rotated!', database='psvibe_api', cursorclass=pymysql.cursors.DictCursor)
cur = conn.cursor()
cur.execute("SELECT id, console_id, member_id, status, start_time, end_time FROM console_booking WHERE status='Active'")
for r in cur.fetchall():
    print(f"#{r['id']}: C={r['console_id']} | member={r['member_id']} | start={str(r['start_time'])[:19]} | end={str(r['end_time'])[:19]}")

cur.execute("SELECT id, console_id, member_id, status, start_time FROM console_booking WHERE status IN ('confirmed','pending')")
print('\n=== Pending/Confirmed Bookings ===')
for r in cur.fetchall():
    print(f"#{r['id']}: C={r['console_id']} | member={r['member_id']} | status={r['status']} | start={str(r['start_time'])[:19]}")
