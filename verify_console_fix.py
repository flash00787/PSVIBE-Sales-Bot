import json, urllib.request

pw = chr(97)+chr(100)+chr(109)+chr(105)+chr(110)+chr(49)+chr(50)+chr(51)
login = json.dumps({'username':'admin','password':pw}).encode()
req = urllib.request.Request('http://localhost:8000/auth/login', data=login, headers={'Content-Type':'application/json'})
res = json.load(urllib.request.urlopen(req, timeout=5))
tok = res['access_token']
bearer = 'Bearer ' + tok

req = urllib.request.Request('http://localhost:8000/api/dashboard/consoles', headers={'Authorization': bearer})
res = json.load(urllib.request.urlopen(req, timeout=5))
data = res.get('data', [])
print(f'Dashboard consoles: {len(data)} rows')
seen = set()
for c in data:
    cid = c['id']
    flag = ' DUPLICATE!' if cid in seen else ''
    seen.add(cid)
    booking = c.get('current_booking')
    bk_info = f' | bk_id={booking["id"]}' if booking else ''
    print(f'  {cid}: {c["status"]}{bk_info}{flag}')
