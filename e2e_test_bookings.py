#!/usr/bin/env python3
"""Full end-to-end test of booking approve flow."""
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

headers = {"X-API-Key": key, "Content-Type": "application/json"}

# 1. Create a new booking
print("=== 1. CREATE a pending booking ===")
create_body = {
    "customerName": "Kora Test",
    "phone": "09123456789",
    "date": "2026-06-09",
    "timeSlot": "15:00",
    "consoleType": "PS5",
    "durationMins": 60,
    "gameName": "Spider Man 2",
    "status": "pending",
    "source": "staff",
    "staffName": "Kora"
}
req = urllib.request.Request(f"{base}/api/bookings", 
    data=json.dumps(create_body).encode(), headers=headers, method="POST")
resp = urllib.request.urlopen(req, timeout=5)
d = json.loads(resp.read().decode())
bk_id = d.get("data", {}).get("id")
print(f"  Created booking #{bk_id} ✅" if bk_id else f"  Failed: {d}")

if not bk_id:
    print("  Trying GET pending...")
    # Get any pending from confirmed (we might have only confirmed)
    req = urllib.request.Request(f"{base}/api/bookings?status=confirmed", headers=headers)
    resp = urllib.request.urlopen(req, timeout=5)
    d = json.loads(resp.read().decode())
    bks = d.get("data", {}).get("bookings", [])
    if bks:
        bk_id = bks[0]["id"]
        print(f"  Using existing confirmed booking #{bk_id}")
    else:
        print("  No bookings found at all")
        # Try pending
        req = urllib.request.Request(f"{base}/api/bookings?status=pending", headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        d = json.loads(resp.read().decode())
        bks = d.get("data", {}).get("bookings", [])
        if bks:
            bk_id = bks[0]["id"]
            print(f"  Using pending booking #{bk_id}")

# 2. GET single booking (what bot does)
if bk_id:
    print(f"\n=== 2. GET /api/bookings/{bk_id} (bot's _replit_get_async) ===")
    req = urllib.request.Request(f"{base}/api/bookings/{bk_id}", headers=headers)
    resp = urllib.request.urlopen(req, timeout=5)
    d = json.loads(resp.read().decode())
    bk = d.get("data", {}).get("booking", {})
    print(f"  Response: {json.dumps(d, indent=2)[:400]}")
    print(f"\n  ⚠️ Bot extracts: bk_info.get('consoleType') = {bk.get('consoleType', '❌ EMPTY')}")
    print(f"  ⚠️ Bot extracts: bk_info.get('gameName') = {bk.get('gameName', '❌ EMPTY')}")

    # 3. PATCH booking status
    print(f"\n=== 3. PATCH /api/bookings/{bk_id}/status (approve) ===")
    patch_body = {"status": "confirmed", "staffNote": "Approved by Test Staff"}
    req = urllib.request.Request(f"{base}/api/bookings/{bk_id}/status",
        data=json.dumps(patch_body).encode(), headers=headers, method="PATCH")
    resp = urllib.request.urlopen(req, timeout=5)
    d = json.loads(resp.read().decode())
    print(f"  success={d.get('success')} data={d.get('data')}")

    # 4. Verify it changed
    print(f"\n=== 4. Verify booking #{bk_id} status ===")
    req = urllib.request.Request(f"{base}/api/bookings?status=confirmed", headers=headers)
    resp = urllib.request.urlopen(req, timeout=5)
    d = json.loads(resp.read().decode())
    bks = d.get("data", {}).get("bookings", [])
    for b in bks:
        if b["id"] == bk_id:
            print(f"  Status: {b['status']} ✅")
            break
    else:
        print(f"  Booking #{bk_id} not found in confirmed list ❌")
