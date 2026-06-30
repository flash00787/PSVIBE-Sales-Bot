#!/usr/bin/env python3
"""Gmail OAuth re-auth — generates URL for Boss to click, then exchanges code for token."""
import json, urllib.request, urllib.parse, os

WS = os.environ.get("KORA_WS", "/home/node/.openclaw/workspace")
SECRET_FILE = os.path.join(WS, "secret.json")
TOKEN_FILE = os.path.join(WS, "token.json")

with open(SECRET_FILE) as f:
    s = json.load(f)["installed"]

CID = s["client_id"]
CS = s["client_secret"]

# Step 1: Generate auth URL
params = urllib.parse.urlencode({
    "client_id": CID,
    "redirect_uri": "http://localhost",
    "response_type": "code",
    "scope": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly",
    "access_type": "offline",
    "prompt": "consent",
})
auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"

print("=" * 70)
print("🔑 Gmail OAuth Re-Auth Required")
print("=" * 70)
print()
print("Boss — အောက်က link ကို browser မှာဖွင့်ပြီး Google account နဲ့ login လုပ်ပါ။")
print("Login ပြီးရင် redirect လုပ်တဲ့ URL ထဲက 'code=...' parameter ကို copy လုပ်ပြီး ပို့ပေးပါ။")
print()
print(f"AUTH URL:\n{auth_url}")
print()
print("=" * 70)
