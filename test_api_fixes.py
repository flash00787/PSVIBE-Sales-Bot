import json, urllib.request

url_base = 'http://localhost:8000'
ak = 'api_key=JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ'

# Test 1: Start session
print("=== Test 1: Start session on C-02 ===")
payload = json.dumps({'console_id':'C-02','member_id':'Staff'}).encode()
req = urllib.request.Request(f'{url_base}/api/consoles/start-session?{ak}', data=payload, headers={'Content-Type':'application/json'})
res = json.load(urllib.request.urlopen(req, timeout=5))
print(json.dumps(res, indent=2, ensure_ascii=False))

# Test 2: Guard
print("\n=== Test 2: Guard - duplicate start ===")
req = urllib.request.Request(f'{url_base}/api/consoles/start-session?{ak}', data=payload, headers={'Content-Type':'application/json'})
try:
    res = json.load(urllib.request.urlopen(req, timeout=5))
    print(json.dumps(res, indent=2, ensure_ascii=False))
except urllib.error.HTTPError as e:
    print(f'Error {e.code}: {e.read().decode()[:300]}')

# Test 3: Confirmed booking
print("\n=== Test 3: Confirmed booking for C-03 ===")
req = urllib.request.Request(f'{url_base}/api/get-confirmed-booking?console_id=C-03&{ak}')
res = json.load(urllib.request.urlopen(req, timeout=5))
print(json.dumps(res, indent=2, ensure_ascii=False))

# Cleanup
print("\n=== Cleanup ===")
import os, sys
sys.path.insert(0, '/root/psvibe_api_server')
from mysql_db import execute as _me, query as _mq
_me("UPDATE console_status SET status='Free', current_member=NULL, current_game=NULL, start_time=NULL WHERE console_id='C-02'")
bk = _mq("SELECT id FROM console_booking WHERE console_id='C-02' AND status='Active'")
if bk:
    _me("UPDATE console_booking SET status='Done', end_time=NOW() WHERE id=%s", (bk[0]['id'],))
    print(f"Cleaned booking #{bk[0]['id']}")
else:
    print("Nothing to clean")
