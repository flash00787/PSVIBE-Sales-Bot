#!/usr/bin/env python3
"""Check console status and bookings on VPS. Reads API key from env file."""
import os, sys

# Load env
env_file = '/etc/psvibe/secrets.env'
if os.path.exists(env_file):
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

KEY = os.environ.get('API_KEY', '')

import urllib.request, json, pymysql

# Check console status
req = urllib.request.Request('http://localhost:8000/api/fetch_console_status', headers={'X-API-Key': KEY})
try:
    res = json.load(urllib.request.urlopen(req, timeout=5))
except Exception as e:
    print(f"API error: {e}")
    sys.exit(1)

print("=== Console Status ===")
for c in res.get('data',{}).get('consoles',[]):
    sid = c.get('console_id','?')
    st = c.get('status','?')
    memb = c.get('current_member') or '-'
    ctype = c.get('console_type','?')
    start = c.get('start_time') or '-'
    cgame = c.get('current_game') or '-'
    print(f'{sid} ({ctype}): {st} | member={memb} | game={cgame} | start={str(start)[:19]}')

# Check booking data directly from MySQL
conn = pymysql.connect(host='127.0.0.1', user='psvibe_user', password='PsVibe@2026_Rotated!', database='psvibe_api', cursorclass=pymysql.cursors.DictCursor)
cur = conn.cursor()

# Active sessions
cur.execute("SELECT id, console_id, member_id, status, start_time, end_time FROM console_booking WHERE status='Active' ORDER BY id")
print('\n=== Active Sessions ===')
for r in cur.fetchall():
    print(f"Booking #{r['id']}: C-{r['console_id']} | member={r['member_id']} | start={str(r['start_time'])[:19]} | end={str(r['end_time'])[:19]}")

# Fixed: confirmed bookings not expired
cur.execute("SELECT id, console_id, member_id, status, start_time, end_time, game_name FROM console_booking WHERE status IN ('confirmed','pending') ORDER BY id")
print('\n=== Pending/Confirmed ===')
for r in cur.fetchall():
    print(f"Booking #{r['id']}: C-{r['console_id']} | {r.get('game_name','?')} | {r['status']} | start={str(r['start_time'])[:19]} | end={str(r['end_time'])[:19]}")
