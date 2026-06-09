#!/usr/bin/env python3
"""Verify new booking API endpoints."""
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

# Test GET /api/bookings?status=pending
req1 = urllib.request.Request(f"{base}/api/bookings?status=pending", headers={"X-API-Key": key})
resp1 = urllib.request.urlopen(req1, timeout=5)
d1 = json.loads(resp1.read().decode())
bks = d1.get("data", {}).get("bookings", [])
print(f"GET /api/bookings?status=pending: {len(bks)} bookings")

if bks:
    b = bks[0]
    bk_id = b["id"]
    print(f"  #{bk_id} {b.get('customerName')} - {b.get('status')}")

    # Test GET /api/bookings/{id}
    req2 = urllib.request.Request(f"{base}/api/bookings/{bk_id}", headers={"X-API-Key": key})
    resp2 = urllib.request.urlopen(req2, timeout=5)
    d2 = json.loads(resp2.read().decode())
    bk = d2.get("data", {}).get("booking", {})
    print(f"  GET /api/bookings/{bk_id}: {bk.get('customerName')} - Console: {bk.get('consoleType')} ✅")

    # Test PATCH /api/bookings/{id}/status
    data3 = json.dumps({"status": b["status"], "staffNote": "Verified by Kora test"}).encode()
    req3 = urllib.request.Request(f"{base}/api/bookings/{bk_id}/status", data=data3,
        headers={"X-API-Key": key, "Content-Type": "application/json"}, method="PATCH")
    resp3 = urllib.request.urlopen(req3, timeout=5)
    d3 = json.loads(resp3.read().decode())
    print(f"  PATCH /api/bookings/{bk_id}/status: success={d3.get('success')} ✅")
else:
    print("  No pending bookings found")
# Also test confirmed
req4 = urllib.request.Request(f"{base}/api/bookings?status=confirmed", headers={"X-API-Key": key})
resp4 = urllib.request.urlopen(req4, timeout=5)
d4 = json.loads(resp4.read().decode())
bks4 = d4.get("data", {}).get("bookings", [])
print(f"GET /api/bookings?status=confirmed: {len(bks4)} bookings")
for b in bks4:
    print(f"  #{b['id']} {b.get('customerName')} - {b.get('timeSlot')}")
