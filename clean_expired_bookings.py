#!/usr/bin/env python3
"""List confirmed bookings and delete expired ones."""
import os, json, urllib.request

key = ""
base = "http://localhost:8000"
with open("/etc/psvibe/secrets.env") as f:
    for line in f:
        line = line.strip()
        if line.startswith("API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("API_BASE="):
            base = line.split("=", 1)[1].strip().strip('"')

from datetime import datetime, timezone, timedelta

# Use Myanmar time (+6:30)
def now_mmt():
    return datetime.now(timezone.utc) + timedelta(hours=6, minutes=30)

now = now_mmt()
today_str = now.strftime("%Y-%m-%d")
now_time = now.strftime("%H:%M")

print(f"Now: {today_str} {now_time} (MMT)")
print()

# Get confirmed bookings
req = urllib.request.Request(f"{base}/api/bookings?status=confirmed", headers={"X-API-Key": key})
resp = urllib.request.urlopen(req, timeout=5)
d = json.loads(resp.read().decode())
bks = d.get("data", {}).get("bookings", [])
print(f"Confirmed bookings: {len(bks)}")
print()

expired = []
for b in bks:
    bk_date = b.get("date", "")
    bk_time = b.get("timeSlot", "")
    bk_id = b["id"]
    print(f"  #{bk_id} {b.get('customerName','?')} | Date: {bk_date} | Time: {bk_time} | C:{b.get('console_id','-')}")

    # Check if expired (past date or same date but past time)
    is_expired = False
    if bk_date < today_str:
        is_expired = True
    elif bk_date == today_str and bk_time and bk_time < now_time:
        is_expired = True

    if is_expired:
        expired.append(b)
        print(f"    ⏰ EXPIRED — will delete")
    else:
        print(f"    ✅ Still upcoming")

print()
print(f"Expired to delete: {len(expired)}")
for b in expired:
    bk_id = b["id"]
    print(f"  Deleting #{bk_id} {b.get('customerName','?')} {b.get('date','?')} {b.get('timeSlot','?')}")
    try:
        data = json.dumps({"id": bk_id}).encode()
        req = urllib.request.Request(f"{base}/api/bookings/cancel",
            data=data, headers={"X-API-Key": key, "Content-Type": "application/json"}, method="POST")
        resp = urllib.request.urlopen(req, timeout=5)
        d2 = json.loads(resp.read().decode())
        print(f"    Result: success={d2.get('success')} {d2.get('data','')}")
    except urllib.error.HTTPError as e:
        print(f"    HTTP {e.code}: {e.read().decode()[:100]}")
