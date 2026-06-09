#!/usr/bin/env python3
"""Fix customer bot API auth: change X-API-Key header -> api_key query parameter"""
import sys

with open('/root/psvibe-sales-bot/customer_bot/api.py', 'r') as f:
    content = f.read()

old = '''    headers = {
        "Content-Type": "application/json",
        **({"X-API-Key": _API_KEY} if (api_key and _API_KEY) else {}),
        **(headers_extra or {}),
    }'''

new = '''    headers = {
        "Content-Type": "application/json",
        **(headers_extra or {}),
    }
    # Add api_key as query parameter (API server uses Depends(verify_api_key) which reads ?api_key=)
    if api_key and _API_KEY:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}api_key={_API_KEY}"'''

if old in content:
    content = content.replace(old, new)
    with open('/root/psvibe-sales-bot/customer_bot/api.py', 'w') as f:
        f.write(content)
    print("FIX1_OK: _http_request now uses api_key query parameter")
    sys.exit(0)
else:
    print("FIX1_FAIL: block not found")
    idx = content.find('headers = {')
    if idx > 0:
        print("CURRENT:", repr(content[idx:idx+250]))
    sys.exit(1)
