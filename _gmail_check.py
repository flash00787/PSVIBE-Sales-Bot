#!/usr/bin/env python3
"""Gmail Inbox Check — Morning Routine"""
import json, urllib.request, urllib.parse, base64, os, sys
from email.mime.text import MIMEText
from email.parser import BytesParser
from email.policy import default

WS = "/home/node/.openclaw/workspace"
SECRET_FILE = os.path.join(WS, "secret.json")
TOKEN_FILE = os.path.join(WS, "token.json")

def refresh_token():
    with open(SECRET_FILE) as f:
        s = json.load(f)["installed"]
    with open(TOKEN_FILE) as f:
        td = json.load(f)
    d = urllib.parse.urlencode({
        "client_id": s["client_id"],
        "client_secret": s["client_secret"],
        "refresh_token": td["refresh_token"],
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=d)
    with urllib.request.urlopen(req, timeout=10) as r:
        nt = json.loads(r.read())
    td["access_token"] = nt["access_token"]
    with open(TOKEN_FILE, "w") as f:
        json.dump(td, f)
    return td["access_token"]

def gmail_api(path, params=None):
    token = refresh_token()
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def get_message_detail(msg_id):
    """Get full message with headers + body"""
    data = gmail_api(f"messages/{msg_id}", {"format": "full"})
    headers = {}
    for h in data.get("payload", {}).get("headers", []):
        headers[h["name"].lower()] = h["value"]

    # Decode body
    body = ""
    parts = data.get("payload", {}).get("parts", [])
    if not parts:
        # Single part
        bd = data.get("payload", {}).get("body", {}).get("data", "")
        if bd:
            body = base64.urlsafe_b64decode(bd + "===").decode("utf-8", errors="replace")
    else:
        for part in parts:
            if part.get("mimeType") == "text/plain":
                bd = part.get("body", {}).get("data", "")
                if bd:
                    body = base64.urlsafe_b64decode(bd + "===").decode("utf-8", errors="replace")
                break
        if not body:
            for part in parts:
                bd = part.get("body", {}).get("data", "")
                if bd:
                    body = base64.urlsafe_b64decode(bd + "===").decode("utf-8", errors="replace")
                    break

    return {
        "id": msg_id,
        "threadId": data.get("threadId"),
        "from": headers.get("from", "?"),
        "to": headers.get("to", "?"),
        "subject": headers.get("subject", "(no subject)"),
        "date": headers.get("date", "?"),
        "snippet": data.get("snippet", ""),
        "body": body[:3000],
        "labelIds": data.get("labelIds", [])
    }

print("=" * 60)
print("📬 GMAIL INBOX CHECK — Morning Routine")
print("=" * 60)

# === 1. GET UNREAD EMAILS ===
print("\n🔍 1. Checking UNREAD emails...")
unread = gmail_api("messages", {"q": "is:unread", "maxResults": 20})
unread_msgs = unread.get("messages", [])
print(f"   Unread: {len(unread_msgs)} messages")

unread_details = []
for m in unread_msgs[:10]:
    try:
        detail = get_message_detail(m["id"])
        unread_details.append(detail)
    except Exception as e:
        print(f"   ⚠️ Failed to fetch {m['id']}: {e}")

# === 2. CHECK NOVA EMAILS ===
print("\n🔍 2. Checking Nova emails (yeyintoo12345678@gmail.com)...")
nova = gmail_api("messages", {"q": "from:yeyintoo12345678@gmail.com", "maxResults": 10})
nova_msgs = nova.get("messages", [])
print(f"   Nova emails: {len(nova_msgs)} total")

nova_details = []
for m in nova_msgs[:5]:
    try:
        detail = get_message_detail(m["id"])
        nova_details.append(detail)
    except Exception as e:
        print(f"   ⚠️ Failed to fetch {m['id']}: {e}")

# === 3. RECENT EMAILS (last 2 days) ===
print("\n🔍 3. Checking recent emails (last 2 days)...")
recent = gmail_api("messages", {"q": "newer_than:2d", "maxResults": 20})
recent_msgs = recent.get("messages", [])
print(f"   Recent: {len(recent_msgs)} messages")

recent_details = []
for m in recent_msgs[:10]:
    try:
        detail = get_message_detail(m["id"])
        recent_details.append(detail)
    except Exception as e:
        print(f"   ⚠️ Failed to fetch {m['id']}: {e}")

# === SUMMARY ===
print("\n" + "=" * 60)
print("📊 SUMMARY")
print("=" * 60)

# Unread
print("\n--- UNREAD EMAILS ---")
if not unread_details:
    print("✅ No unread emails.")
else:
    for i, e in enumerate(unread_details, 1):
        labels = [l for l in e["labelIds"] if l not in ("UNREAD", "INBOX")]
        promo = "PROMO" if "CATEGORY_PROMOTIONS" in e["labelIds"] else ""
        important = "⭐ IMPORTANT" if "IMPORTANT" in e["labelIds"] else ""
        print(f"\n{i}. From: {e['from']}")
        print(f"   Subject: {e['subject']}")
        print(f"   Date: {e['date']}")
        print(f"   Labels: {promo} {important} {' | '.join(labels)}")
        print(f"   Preview: {e['snippet'][:150]}")

# Nova specifics
print("\n--- NOVA EMAILS (yeyintoo12345678@gmail.com) ---")
if not nova_details:
    print("✅ No Nova emails found.")
else:
    for i, e in enumerate(nova_details, 1):
        print(f"\n{i}. Subject: {e['subject']}")
        print(f"   Date: {e['date']}")
        print(f"   Preview: {e['snippet'][:200]}")
        # Check for wallet handover keywords
        body_lower = (e["body"] + e["subject"] + e["snippet"]).lower()
        keywords = ["wallet", "handover", "personal-wallet", "tele-bot", "hand over", "transfer"]
        matched = [k for k in keywords if k in body_lower]
        if matched:
            print(f"   🔑 KEYWORDS FOUND: {matched}")

# Recent
print("\n--- RECENT EMAILS (last 2 days) ---")
if not recent_details:
    print("✅ No recent emails.")
else:
    for i, e in enumerate(recent_details, 1):
        promo = "🏷️ PROMO" if "CATEGORY_PROMOTIONS" in e["labelIds"] else ""
        print(f"\n{i}. [{promo}] {e['from']} — {e['subject']}")
        print(f"   {e['date']}")

# === FINAL VERDICT ===
print("\n" + "=" * 60)
print("🎯 FINAL VERDICT")
print("=" * 60)

# Important detection
important_emails = []
nova_wallet_reply = None

for e in unread_details:
    is_promo = "CATEGORY_PROMOTIONS" in e["labelIds"]
    is_important = "IMPORTANT" in e["labelIds"]
    if not is_promo and (is_important or "nova" in e.get("from","").lower() or "yeyintoo" in e.get("from","").lower()):
        important_emails.append(e)

for e in nova_details:
    body_lower = (e["body"] + e["subject"] + e["snippet"]).lower()
    if any(k in body_lower for k in ["wallet", "handover", "hand over"]):
        nova_wallet_reply = e
        important_emails.append(e)

print(f"Total unread: {len(unread_details)}")
print(f"Important non-promo: {len(important_emails)}")
print(f"Nova wallet reply: {'YES ✅' if nova_wallet_reply else 'No ❌'}")

# Output JSON for caller
output = {
    "unread_count": len(unread_details),
    "important_count": len(important_emails),
    "nova_wallet_reply": nova_wallet_reply is not None,
    "nova_emails_count": len(nova_details),
    "recent_count": len(recent_details),
    "important_emails": [{"from": e["from"], "subject": e["subject"], "snippet": e["snippet"][:100]} for e in important_emails],
    "nova_details": [{"subject": e["subject"], "date": e["date"], "snippet": e["snippet"][:200]} for e in nova_details]
}

print("\n📤 JSON_OUTPUT:")
print(json.dumps(output, indent=2, ensure_ascii=False))
