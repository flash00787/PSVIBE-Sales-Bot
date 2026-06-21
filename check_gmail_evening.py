#!/usr/bin/env python3
"""Kora Gmail Inbox Checker — checks unread & recent emails via Gmail API"""
import json, urllib.request, urllib.parse, base64, os, re, sys
from email.parser import BytesParser
from email.policy import default
from datetime import datetime, timezone, timedelta

WS = "/root/.openclaw/workspace"
SECRET_FILE = os.path.join(WS, "secret.json")
TOKEN_FILE = os.path.join(WS, "gmail_token.json")

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
    if "refresh_token" in nt:
        td["refresh_token"] = nt["refresh_token"]
    with open(TOKEN_FILE, "w") as f:
        json.dump(td, f)
    return td["access_token"]

def gmail_api(path, token, params=None):
    """Make a Gmail API GET request"""
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}"
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def decode_email(payload):
    """Decode Gmail API payload to extract headers and body"""
    headers = {}
    for h in payload.get("headers", []):
        headers[h["name"].lower()] = h["value"]
    
    body_text = ""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            body_text = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    elif payload.get("mimeType") == "multipart/alternative":
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body_text = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
                    break
    elif "parts" in payload:
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body_text += base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    
    return headers, body_text

def get_header_value(payload, name):
    for h in payload.get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""

def main():
    token = refresh_token()
    
    print("=" * 70)
    print("📬 GMAIL INBOX CHECK — EVENING")
    print(f"   Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)
    
    # Fetch unread messages
    unread_list = gmail_api("messages", token, {
        "q": "is:unread",
        "maxResults": "30"
    })
    
    unread_msgs = unread_list.get("messages", [])
    print(f"\n🔵 UNREAD MESSAGES: {len(unread_msgs)}")
    
    important_emails = []
    nova_emails = []
    promotional_emails = []
    all_emails = []
    
    # Also fetch recent messages (last 3 days)
    recent_list = gmail_api("messages", token, {
        "q": "newer_than:3d",
        "maxResults": "30"
    })
    recent_msgs = recent_list.get("messages", [])
    print(f"🕐 RECENT (3d): {len(recent_msgs)}")
    
    # Combine and deduplicate
    all_msg_ids = {}
    for m in unread_msgs + recent_msgs:
        all_msg_ids[m["id"]] = m
    
    if not all_msg_ids:
        print("\n✅ No unread or recent emails found.")
        print("\nRESULT: NO_REPLY")
        return
    
    print(f"\n📋 Processing {len(all_msg_ids)} unique messages...\n")
    
    # Promotional keywords to skip
    promo_keywords = ["newsletter", "n8n", "twitch", "dior", "diễn", "eSIM", "pexx", 
                      "google play", "thank you for your purchase", "community party",
                      "subscription", "weekly digest", "unsubscribe", "sale ends"]
    
    for i, (msg_id, _) in enumerate(all_msg_ids.items()):
        try:
            full_msg = gmail_api(f"messages/{msg_id}", token, {"format": "full"})
            payload = full_msg.get("payload", {})
            headers, body = decode_email(payload)
            
            # Internal date
            internal_date = full_msg.get("internalDate", "0")
            ts = int(internal_date) / 1000
            date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            
            subject = get_header_value(payload, "subject") or "(no subject)"
            from_addr = get_header_value(payload, "from") or ""
            to_addr = get_header_value(payload, "to") or ""
            snippet = full_msg.get("snippet", "")
            is_unread = "UNREAD" in full_msg.get("labelIds", [])
            
            email_info = {
                "id": msg_id,
                "threadId": full_msg.get("threadId", ""),
                "from": from_addr,
                "to": to_addr,
                "subject": subject,
                "date": date_str,
                "is_unread": is_unread,
                "snippet": snippet,
                "body_preview": body[:500] if body else ""
            }
            all_emails.append(email_info)
            
            # Check for promotional
            combined_text = f"{subject} {snippet} {body[:300]}".lower()
            is_promo = any(kw in combined_text for kw in promo_keywords)
            
            # Also check sender patterns for promos
            promo_senders = ["noreply@", "no-reply@", "notifications@github.com",
                           "newsletter@", "marketing@", "info@n8n", "twitch.tv",
                           "dior", "pexx.com"]
            is_promo_sender = any(ps in from_addr.lower() for ps in promo_senders)
            
            if is_promo or is_promo_sender:
                promotional_emails.append(email_info)
                if is_unread:
                    status = "🔵 UNREAD [PROMO]"
                else:
                    status = "⚪ READ [PROMO]"
            else:
                status = "🔵 UNREAD" if is_unread else "⚪ READ"
            
            print(f"{'─' * 60}")
            print(f"[{i+1}] {status} | {date_str}")
            print(f"    From: {from_addr}")
            print(f"    Subject: {subject}")
            print(f"    Snippet: {snippet[:120]}")
            
            # Skip promotional from further checks
            if is_promo or is_promo_sender:
                continue
            
            # Check for Nova's email (yeyintoo12345678@gmail.com)
            if "yeyintoo12345678" in from_addr.lower() or "yeyintoo12345678" in str(body).lower():
                nova_emails.append(email_info)
                print(f"    ⚠️  NOVA EMAIL DETECTED!")
            
            # Check for important/keyword-based emails
            important_keywords = [
                "handover", "urgent", "payment", "invoice", "wallet",
                "important", "action required", "confirm", "verification",
                "security", "password", "reset", "account",
                "ps vibe", "synergy", "business", "client",
                "tele", "bot", "telegram", "booking"
            ]
            matched_kw = [kw for kw in important_keywords if kw in combined_text]
            if matched_kw:
                important_emails.append({**email_info, "keywords": matched_kw})
                print(f"    📌 Important keywords: {', '.join(matched_kw)}")
            
        except Exception as e:
            print(f"   ❌ Error processing message {msg_id}: {e}")
    
    # ============ SUMMARY ============
    print(f"\n{'=' * 70}")
    print("📊 EVENING CHECK SUMMARY")
    print(f"{'=' * 70}")
    print(f"   Total messages processed: {len(all_emails)}")
    print(f"   Total unread: {len(unread_msgs)}")
    print(f"   Promotional (skipped): {len(promotional_emails)}")
    print(f"   Nova emails: {len(nova_emails)}")
    print(f"   Important emails: {len(important_emails)}")
    
    if nova_emails:
        print(f"\n🔴 NOVA EMAILS FOUND:")
        for ne in nova_emails:
            print(f"   - [{ne['date']}] {ne['subject']}")
            print(f"     From: {ne['from']}")
            print(f"     Preview: {ne['body_preview'][:200]}")
    
    if important_emails:
        print(f"\n📌 IMPORTANT EMAILS (non-promo):")
        for ie in important_emails:
            print(f"   - [{ie['date']}] {ie['subject']}")
            print(f"     From: {ie['from']}")
            print(f"     Keywords: {', '.join(ie.get('keywords', []))}")
    
    if not nova_emails and not important_emails:
        print(f"\n✅ No Nova or important non-promotional emails found.")
        print(f"RESULT: NO_REPLY")
        return "NO_REPLY"
    
    # Output results for automation
    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "total_unread": len(unread_msgs),
        "total_processed": len(all_emails),
        "nova_found": len(nova_emails),
        "important_found": len(important_emails),
        "promotional_skipped": len(promotional_emails),
        "nova_emails": nova_emails,
        "important_emails": important_emails
    }
    
    # Save results
    with open(os.path.join(WS, "gmail_check_results.json"), "w") as f:
        json.dump(result, f, indent=2)
    
    if nova_emails:
        print(f"\n⚠️ RESULT: NOVA_REPLY_FOUND — Boss should be notified!")
        print(f"\n__NOVA_JSON__")
        print(json.dumps(nova_emails, indent=2))
        return "NOVA_REPLY_FOUND"
    elif important_emails:
        print(f"\n⚠️ RESULT: IMPORTANT_FOUND — Boss should be notified!")
        print(f"\n__IMPORTANT_JSON__")
        print(json.dumps(important_emails, indent=2))
        return "IMPORTANT_FOUND"
    
    return "NO_REPLY"

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result == "NO_REPLY" else 1)
