#!/usr/bin/env python3
"""Check active sessions and test end_booking API."""
import os, json, urllib.request

key = os.environ.get("API_KEY", "")
base = os.environ.get("API_BASE", "http://localhost:8000")

if not key:
    key_file = "/etc/psvibe/secrets.env"
    with open(key_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith("API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("API_BASE="):
                base = line.split("=", 1)[1].strip().strip('"')

print(f"API_BASE: {base}")
print(f"API_KEY len: {len(key)} first: {key[:8]}...")

# Test 1: fetch_console_status
req = urllib.request.Request(
    f"{base}/api/fetch_console_status",
    headers={"X-API-Key": key}
)
try:
    resp = urllib.request.urlopen(req, timeout=5)
    data = json.loads(resp.read().decode())
    consoles = data.get("data", {}).get("consoles", [])
    print(f"\n=== Console Status ===")
    print(f"Total: {len(consoles)}")
    
    active = [c for c in consoles if c.get("status") == "Active"]
    print(f"Active: {len(active)}")
    for c in active:
        bid = c.get("booking_id") or ""
        cid = c.get("console_id", "")
        ctype = c.get("console_type", "")
        member = c.get("current_member", "")
        start = c.get("start_time", "")
        print(f"  cid='{cid}' type='{ctype}' bid='{bid}' member='{member}' start='{start}'")
    
    if active:
        c = active[0]
        bid = c.get("booking_id") or ""
        cid = c.get("console_id", "")
        print(f"\n=== Testing end_booking for {cid} (bid={bid}) ===")
        if bid:
            req2 = urllib.request.Request(
                f"{base}/api/end_booking/{bid}",
                method="PUT",
                headers={"X-API-Key": key}
            )
            resp2 = urllib.request.urlopen(req2, timeout=5)
            print(f"Result: {resp2.read().decode()}")
        else:
            print("No booking_id - cannot test automatically")
    else:
        print("No active sessions found")
        for c in consoles[:5]:
            print(f"  cid='{c.get('console_id','')}' status='{c.get('status','')}'")
except Exception as e:
    print(f"Error: {e}")
