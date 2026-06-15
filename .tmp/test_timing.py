import requests, time, json

base = "http://localhost:16990"
headers = {"X-API-Key": "psvibe-secret-key-2025", "Content-Type": "application/json"}

calls = [
    ("base_rate", f"{base}/api/base-rate"),
    ("food_prices", f"{base}/api/food-prices"),
]

for name, url in calls:
    t0 = time.time()
    try:
        r = requests.get(url, headers=headers, timeout=5)
        t = time.time() - t0
        print(f"{name}: {t*1000:.0f}ms status={r.status_code}")
    except Exception as e:
        t = time.time() - t0
        print(f"{name}: {t*1000:.0f}ms FAILED: {e}")

# Test coupon gen
t0 = time.time()
try:
    r = requests.post(f"{base}/api/coupons/generate", json={"member_id":"M001","session_minutes":60}, headers=headers, timeout=10)
    t = time.time() - t0
    print(f"coupon_generate: {t*1000:.0f}ms status={r.status_code} body={r.text[:200]}")
except Exception as e:
    t = time.time() - t0
    print(f"coupon_generate: {t*1000:.0f}ms FAILED: {e}")

# Test multiplier
t0 = time.time()
try:
    r = requests.get(f"{base}/api/consoles/C-01/multiplier", headers=headers, timeout=5)
    t = time.time() - t0
    print(f"multiplier: {t*1000:.0f}ms status={r.status_code}")
except Exception as e:
    t = time.time() - t0
    print(f"multiplier: {t*1000:.0f}ms FAILED: {e}")

# Test end_booking timing
t0 = time.time()
try:
    r = requests.post(f"{base}/api/bookings/end", json={"console_id":"C-01","booking_id":"B001"}, headers=headers, timeout=10)
    t = time.time() - t0
    print(f"end_booking: {t*1000:.0f}ms status={r.status_code}")
except Exception as e:
    t = time.time() - t0
    print(f"end_booking: {t*1000:.0f}ms FAILED: {e}")
