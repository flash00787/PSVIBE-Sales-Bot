#!/usr/bin/env python3
"""Gmail Inbox Checker — lists unread + recent emails, checks for Nova's reply"""
import json, urllib.request, urllib.parse, os, sys
from datetime import datetime, timezone, timedelta
from email.header import decode_header
from email.utils import parsedate_to_datetime
import base64

WS = os.environ.get("KORA_WS", "/root/.openclaw/workspace")
SECRET_FILE = os.path.join(WS, "secret.json")
TOKEN_FILE = os.path.join(WS, "token.json")

with open(SECRET_FILE) as f:
    s = json.load(f)["installed"]
CID = s["client_id"]
CS = s["client_secret"]

def refresh_token():
    with open(TOKEN_FILE) as f:
        td = json.load(f)
    d = urllib.parse.urlencode({
        "client_id": CID,
        "client_secret": CS,
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

def api_call(url, timeout=15):
    token = refresh_token()
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def decode_header_text(hdr):
    """Decode RFC 2047 encoded headers"""
    if not hdr:
        return "(no subject)"
    parts = decode_header(hdr)
    result = []
    for text, charset in parts:
        if isinstance(text, bytes):
            try:
                result.append(text.decode(charset or "utf-8", errors="replace"))
            except:
                result.append(text.decode("utf-8", errors="replace"))
        else:
            result.append(text)
    return "".join(result)

def get_header(headers_list, name):
    """Get header value from headers list"""
    for h in headers_list:
        if h["name"].lower() == name.lower():
            return h["value"]
    return None

def extract_body(payload):
    """Extract plain text body from message payload (handles multipart)"""
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part["body"].get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data + "===").decode("utf-8", errors="replace")[:500]
        # Try nested multipart
        for part in payload["parts"]:
            if "parts" in part:
                for subpart in part["parts"]:
                    if subpart.get("mimeType") == "text/plain":
                        data = subpart["body"].get("data", "")
                        if data:
                            return base64.urlsafe_b64decode(data + "===").decode("utf-8", errors="replace")[:500]
    elif payload.get("mimeType") == "text/plain":
        data = payload["body"].get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "===").decode("utf-8", errors="replace")[:500]
    return "(no text body)"

def list_unread():
    """List unread emails from inbox"""
    print("=" * 70)
    print("📬 UNREAD EMAILS")
    print("=" * 70)
    result = api_call(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages"
        "?q=is:unread+in:inbox&maxResults=20"
    )
    messages = result.get("messages", [])
    if not messages:
        print("✅ No unread emails.\n")
        return []
    print(f"Found {len(messages)} unread email(s).\n")
    emails = []
    for i, msg in enumerate(messages):
        full = api_call(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}"
            "?format=full"
        )
        headers = full["payload"]["headers"]
        subject = decode_header_text(get_header(headers, "Subject"))
        sender = get_header(headers, "From") or "(unknown)"
        date_str = get_header(headers, "Date") or ""
        snippet = full.get("snippet", "")[:200]
        body = extract_body(full["payload"])
        
        print(f"--- Email #{i+1} ---")
        print(f"From:    {sender}")
        print(f"Subject: {subject}")
        print(f"Date:    {date_str}")
        print(f"Snippet: {snippet}")
        print(f"Preview: {body[:300]}")
        print()
        
        emails.append({
            "id": msg["id"],
            "from": sender,
            "subject": subject,
            "date": date_str,
            "snippet": snippet,
            "body_preview": body[:300]
        })
    return emails

def check_nova_reply():
    """Check for emails from Nova (yeyintoo12345678@gmail.com) about wallet handover"""
    print("=" * 70)
    print("🔍 CHECKING FOR NOVA REPLY (yeyintoo12345678@gmail.com)")
    print("=" * 70)
    # Search for emails from Nova, sorted by newest
    result = api_call(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages"
        "?q=from:yeyintoo12345678@gmail.com&maxResults=5"
    )
    messages = result.get("messages", [])
    if not messages:
        print("❌ No emails from Nova found at all.\n")
        return []
    
    print(f"Found {len(messages)} email(s) from Nova.\n")
    nova_emails = []
    for i, msg in enumerate(messages):
        full = api_call(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}"
            "?format=full"
        )
        headers = full["payload"]["headers"]
        subject = decode_header_text(get_header(headers, "Subject"))
        date_str = get_header(headers, "Date") or ""
        snippet = full.get("snippet", "")[:200]
        body = extract_body(full["payload"])
        label_ids = full.get("labelIds", [])
        is_unread = "UNREAD" in label_ids
        
        unread_mark = "🔴 UNREAD" if is_unread else "✅ Read"
        print(f"--- Nova Email #{i+1} [{unread_mark}] ---")
        print(f"Subject: {subject}")
        print(f"Date:    {date_str}")
        print(f"Snippet: {snippet}")
        print(f"Preview: {body[:300]}")
        print()
        
        nova_emails.append({
            "id": msg["id"],
            "subject": subject,
            "date": date_str,
            "snippet": snippet,
            "body_preview": body[:300],
            "is_unread": is_unread
        })
    return nova_emails

def check_wallet_related():
    """Search for any wallet/personal-wallet related recent emails"""
    print("=" * 70)
    print("💰 WALLET-RELATED EMAILS (last 7 days)")
    print("=" * 70)
    result = api_call(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages"
        "?q=wallet+OR+%22Personal-Wallet%22+newer_than:7d+in:inbox&maxResults=10"
    )
    messages = result.get("messages", [])
    if not messages:
        print("❌ No wallet-related emails in last 7 days.\n")
        return []
    
    print(f"Found {len(messages)} wallet-related email(s).\n")
    wallet_emails = []
    for i, msg in enumerate(messages):
        full = api_call(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}"
            "?format=full"
        )
        headers = full["payload"]["headers"]
        subject = decode_header_text(get_header(headers, "Subject"))
        sender = get_header(headers, "From") or "(unknown)"
        date_str = get_header(headers, "Date") or ""
        snippet = full.get("snippet", "")[:200]
        body = extract_body(full["payload"])
        label_ids = full.get("labelIds", [])
        is_unread = "UNREAD" in label_ids
        
        unread_mark = "🔴 UNREAD" if is_unread else "✅ Read"
        print(f"--- Wallet Email #{i+1} [{unread_mark}] ---")
        print(f"From:    {sender}")
        print(f"Subject: {subject}")
        print(f"Date:    {date_str}")
        print(f"Snippet: {snippet}")
        print(f"Preview: {body[:300]}")
        print()
        
        wallet_emails.append({
            "id": msg["id"],
            "from": sender,
            "subject": subject,
            "date": date_str,
            "snippet": snippet,
            "body_preview": body[:300],
            "is_unread": is_unread
        })
    return wallet_emails

def check_recent():
    """Check recent emails in inbox (last 2 days) regardless of read status"""
    print("=" * 70)
    print("🕐 RECENT INBOX EMAILS (last 2 days)")
    print("=" * 70)
    result = api_call(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages"
        "?q=newer_than:2d+in:inbox&maxResults=10"
    )
    messages = result.get("messages", [])
    if not messages:
        print("❌ No emails in last 2 days.\n")
        return []
    
    print(f"Found {len(messages)} email(s) in last 2 days.\n")
    recent = []
    for i, msg in enumerate(messages):
        full = api_call(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}"
            "?format=full"
        )
        headers = full["payload"]["headers"]
        subject = decode_header_text(get_header(headers, "Subject"))
        sender = get_header(headers, "From") or "(unknown)"
        date_str = get_header(headers, "Date") or ""
        snippet = full.get("snippet", "")[:150]
        label_ids = full.get("labelIds", [])
        is_unread = "UNREAD" in label_ids
        
        unread_mark = "🔴" if is_unread else "📖"
        
        # Skip if already shown as unread
        print(f"{unread_mark} [{date_str[:25]}] {sender}")
        print(f"   {subject}")
        print(f"   {snippet}")
        print()
        
        recent.append({
            "id": msg["id"],
            "from": sender,
            "subject": subject,
            "date": date_str,
            "snippet": snippet,
            "is_unread": is_unread
        })
    return recent

# ── MAIN ──
print("\n╔══════════════════════════════════════════════════════════════════╗")
print("║           📧 GMAIL INBOX CHECK — Morning Routine               ║")
print("╠══════════════════════════════════════════════════════════════════╣")
print(f"║  Time (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC                          ║")
print("║  Account:    chanmyint123456789@gmail.com                       ║")
print("╚══════════════════════════════════════════════════════════════════╝")
print()

try:
    unread = list_unread()
except Exception as e:
    unread = []
    print(f"⚠️  Error fetching unread: {e}\n")

try:
    nova = check_nova_reply()
except Exception as e:
    nova = []
    print(f"⚠️  Error checking Nova: {e}\n")

try:
    wallet = check_wallet_related()
except Exception as e:
    wallet = []
    print(f"⚠️  Error checking wallet emails: {e}\n")

try:
    recent = check_recent()
except Exception as e:
    recent = []
    print(f"⚠️  Error checking recent: {e}\n")

# ── SUMMARY ──
print("=" * 70)
print("📊 SUMMARY")
print("=" * 70)
print(f"Unread emails:    {len(unread)}")
print(f"Nova emails:      {len(nova)} ({sum(1 for e in nova if e.get('is_unread'))} unread)")
print(f"Wallet-related:   {len(wallet)} ({sum(1 for e in wallet if e.get('is_unread'))} unread)")
print(f"Recent (2d):      {len(recent)} ({sum(1 for e in recent if e.get('is_unread'))} unread)")

# Check specifically for Nova reply about wallet/bot handover
nova_has_reply = any(
    "wallet" in e.get("subject","").lower() or 
    "wallet" in e.get("snippet","").lower() or
    "bot" in e.get("subject","").lower() or
    "handover" in e.get("subject","").lower() or
    "handover" in e.get("snippet","").lower() or
    "personal" in e.get("subject","").lower()
    for e in nova
)
print(f"Nova Wallet Reply: {'✅ YES — Found!' if nova_has_reply else '❌ No reply yet'}")

# Priority flag
important_unread = any(
    "urgent" in e.get("subject","").lower() or
    "important" in e.get("subject","").lower() or
    "၁" in e.get("subject","") or
    "invoice" in e.get("subject","").lower() or
    "payment" in e.get("subject","").lower()
    for e in unread + wallet
)
print(f"Priority emails:   {'⚠️ YES' if important_unread else '✅ None'}")

print()
print("Done.")
