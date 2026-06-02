#!/usr/bin/env python3
"""Auto-cancel bookings where customer hasn't checked in within 15 mins of start time.
Calls API endpoints only - bot notification is handled by Sale Bot."""
import requests
import json
from datetime import datetime, timedelta
import os
import sys

API_URL = os.environ.get("PSVIBE_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("PSVIBE_API_KEY", "")

def auto_cancel():
    """Check confirmed bookings past their start time + 15 min and auto-cancel."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    headers = {"X-API-Key": API_KEY}
    
    try:
        resp = requests.get(
            f"{API_URL}/api/bookings/search",
            params={"date": today, "status": "confirmed"},
            headers=headers,
            timeout=10,
        )
        data = resp.json()
    except Exception as e:
        print(f"Error fetching bookings: {e}")
        return
    
    bookings = []
    if isinstance(data, dict):
        data_inner = data.get("data", data)
        if isinstance(data_inner, dict):
            bookings = data_inner.get("bookings", [])
        elif isinstance(data_inner, list):
            bookings = data_inner
    elif isinstance(data, list):
        bookings = data
    
    if not bookings:
        print(f"No confirmed bookings found for {today}")
        return
    
    # Current Myanmar Time (UTC+6:30)
    now_mmt = datetime.utcnow() + timedelta(hours=6, minutes=30)
    cancelled = 0
    
    for b in bookings:
        status = (b.get("status") or "").lower()
        if status not in ("confirmed", "pending", "scheduled"):
            continue
        
        time_slot = b.get("timeSlot") or ""
        bk_date = b.get("date") or today
        
        if not time_slot:
            continue
        
        try:
            h, m = map(int, time_slot.split(":"))
            # Build booking datetime in MMT
            booking_dt = datetime.strptime(bk_date, "%Y-%m-%d").replace(hour=h, minute=m)
            
            # If 15 mins past booking time and no check-in
            if now_mmt > booking_dt + timedelta(minutes=15):
                bk_id = b.get("id")
                if not bk_id:
                    continue
                
                # Cancel via API
                cancel_resp = requests.post(
                    f"{API_URL}/api/bookings/cancel",
                    json={"id": bk_id},
                    headers=headers,
                    timeout=10,
                )
                cancel_data = cancel_resp.json()
                
                if cancel_data.get("success") or cancel_data.get("data", {}).get("message"):
                    cancelled += 1
                    customer = b.get("customerName") or b.get("memberId") or "?"
                    print(f"Cancelled booking {bk_id} for {customer} at {time_slot}")
                else:
                    print(f"Failed to cancel booking {bk_id}: {cancel_data}")
        except Exception as e:
            print(f"Error processing booking {b.get('id', '?')}: {e}")
    
    print(f"Auto-cancel complete. Cancelled: {cancelled}")

if __name__ == "__main__":
    auto_cancel()

