#!/usr/bin/env python3
"""Verify booking_id fix - check active sessions show booking_id now."""
import os, json, urllib.request

key = ""
base = "http://localhost:8000"
key_file = "/etc/psvibe/secrets.env"
with open(key_file) as f:
    for line in f:
        line = line.strip()
        if line.startswith("API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("API_BASE="):
            base = line.split("=", 1)[1].strip().strip('"')

req = urllib.request.Request(
    f"{base}/api/fetch_console_status",
    headers={"X-API-Key": key}
)
resp = urllib.request.urlopen(req, timeout=5)
data = json.loads(resp.read().decode())
consoles = data.get("data", {}).get("consoles", [])
active = [c for c in consoles if c.get("status") == "Active"]
print(f"Total consoles: {len(consoles)}")
print(f"Active: {len(active)}")
for c in active:
    cid = c.get("console_id", "")
    bid = c.get("booking_id") or ""
    ctype = c.get("console_type", "")
    member = c.get("current_member", "")
    start = c.get("start_time", "")
    print(f"  cid='{cid}' bid='{bid}' type='{ctype}' member='{member}' start='{start}'")

if active:
    c = active[0]
    bid = c.get("booking_id") or ""
    print(f"\nTesting end_booking for {c['console_id']} bid={bid}...")
    if bid:
        req2 = urllib.request.Request(
            f"{base}/api/end_booking/{bid}",
            method="PUT",
            headers={"X-API-Key": key}
        )
        resp2 = urllib.request.urlopen(req2, timeout=5)
        result = json.loads(resp2.read().decode())
        print(f"Result: success={result.get('success')}")
        
        # Verify console freed
        resp3 = urllib.request.urlopen(req, timeout=5)
        data3 = json.loads(resp3.read().decode())
        consoles3 = data3.get("data", {}).get("consoles", [])
        for c3 in consoles3:
            if c3.get("console_id") == c.get("console_id"):
                print(f"  Console {c3['console_id']} status now: {c3['status']}")
    else:
        print("No booking_id present - fix NOT WORKING!")
else:
    print("No active sessions to test")
