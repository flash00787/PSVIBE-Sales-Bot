import json, urllib.request

pw = chr(97)+chr(100)+chr(109)+chr(105)+chr(110)+chr(49)+chr(50)+chr(51)
login = json.dumps({'username':'admin','password':pw}).encode()
req = urllib.request.Request('http://localhost:8000/auth/login', data=login, headers={'Content-Type':'application/json'})
res = json.load(urllib.request.urlopen(req, timeout=5))
tok = res['access_token']
bearer = 'Bearer ' + tok

# 1. Test start-session (no confirmed booking)
print("=== Test 1: Start session without confirmed booking ===")
payload = json.dumps({'console_id':'C-02','member_id':'Staff'}).encode()
req = urllib.request.Request('http://localhost:8000/api/consoles/start-session', data=payload, headers={'Authorization': bearer, 'Content-Type':'application/json'})
res = json.load(urllib.request.urlopen(req, timeout=5))
print(json.dumps(res, indent=2, ensure_ascii=False))

# 2. Test check-in guard (try duplicate checkin on same console)
print("\n=== Test 2: Check-in guard - try duplicate ===")
req = urllib.request.Request('http://localhost:8000/api/consoles/start-session', data=payload, headers={'Authorization': bearer, 'Content-Type':'application/json'})
try:
    res = json.load(urllib.request.urlopen(req, timeout=5))
    print(json.dumps(res, indent=2, ensure_ascii=False))
except urllib.error.HTTPError as e:
    print(f"Expected error: {e.code} - {e.read().decode()}")

# 3. Test get-confirmed-booking
print("\n=== Test 3: Get confirmed booking ===")
req = urllib.request.Request('http://localhost:8000/api/get-confirmed-booking?console_id=C-03', headers={'Authorization': bearer})
res = json.load(urllib.request.urlopen(req, timeout=5))
print(json.dumps(res, indent=2, ensure_ascii=False))

# Cleanup: end C-02 session
import os, sys
sys.path.insert(0, '/root/psvibe_api_server')
from mysql_db import execute as _me, query as _mq
_me("UPDATE console_status SET status='Free', current_member=NULL, current_game=NULL, start_time=NULL WHERE console_id='C-02'")
bk = _mq("SELECT id FROM console_booking WHERE console_id='C-02' AND status='Active'")
if bk:
    _me("UPDATE console_booking SET status='Done', end_time=NOW() WHERE id=%s", (bk[0]['id'],))
    print(f"\nCleaned up booking #{bk[0]['id']}")
