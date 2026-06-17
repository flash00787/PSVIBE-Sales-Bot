#!/usr/bin/env python3
"""Check Gmail inbox for unread + recent emails, with Nova-specific search."""
import json, urllib.request, urllib.parse, os, sys

WS = "/root/.openclaw/workspace"
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

def gmail_api(path, params=None):
    """Make GET request to Gmail API."""
    token = refresh_token()
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def get_message_detail(msg_id):
    """Get full message detail."""
    return gmail_api(f"messages/{msg_id}", {"format": "full"})

def extract_email_body(msg):
    """Extract text body from message payload."""
    payload = msg.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    
    # Try to get text/plain or text/html body
    body_data = None
    parts = payload.get("parts", [])
    
    if not parts and "body" in payload and payload["body"].get("data"):
        body_data = payload["body"]["data"]
    else:
        for part in parts:
            if part.get("mimeType") == "text/plain":
                body_data = part["body"].get("data", "")
                break
        if not body_data:
            for part in parts:
                if part.get("mimeType") == "text/html":
                    body_data = part["body"].get("data", "")
                    break
    
    if body_data:
        import base64
        return base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")
    return "(no text body)"

def get_date(headers):
    """Extract date from headers."""
    return headers.get("date", "unknown")

def main():
    print("=" * 70)
    print("📧 GMAIL INBOX CHECK — Evening")
    print("=" * 70)
    
    # 1. Get UNREAD emails
    print("\n🔴 UNREAD EMAILS:")
    print("-" * 50)
    try:
        unread = gmail_api("messages", {"q": "is:unread", "maxResults": 15})
        unread_msgs = unread.get("messages", [])
    except Exception as e:
        print(f"Error fetching unread: {e}")
        unread_msgs = []
    
    if not unread_msgs:
        print("  ✅ No unread emails.")
    else:
        for i, m in enumerate(unread_msgs):
            detail = get_message_detail(m["id"])
            headers = {h["name"].lower(): h["value"] for h in detail.get("payload", {}).get("headers", [])}
            frm = headers.get("from", "unknown")
            subj = headers.get("subject", "(no subject)")
            date = headers.get("date", "unknown")
            snippet = detail.get("snippet", "")
            
            print(f"\n  [{i+1}] From: {frm}")
            print(f"      Subject: {subj}")
            print(f"      Date: {date}")
            print(f"      Snippet: {snippet[:200]}")
            
            # Check if from Nova
            if "yeyintoo12345678" in frm.lower() or "nova" in frm.lower() or "ye yint" in frm.lower():
                print(f"      ⚠️  NOVA EMAIL DETECTED!")
                body = extract_email_body(detail)
                print(f"      Body (first 500 chars): {body[:500]}")
    
    # 2. Specifically search for Nova emails
    print("\n" + "=" * 50)
    print("🔍 SEARCHING FOR NOVA/YE YINT EMAILS (yeyintoo12345678@gmail.com):")
    print("-" * 50)
    try:
        nova_msgs = gmail_api("messages", {"q": "from:yeyintoo12345678@gmail.com OR yeyintoo", "maxResults": 10})
        nova_list = nova_msgs.get("messages", [])
    except Exception as e:
        print(f"Error: {e}")
        nova_list = []
    
    if not nova_list:
        print("  No emails from Nova found.")
    else:
        for i, m in enumerate(nova_list):
            detail = get_message_detail(m["id"])
            headers = {h["name"].lower(): h["value"] for h in detail.get("payload", {}).get("headers", [])}
            frm = headers.get("from", "N/A")
            subj = headers.get("subject", "(no subject)")
            date = headers.get("date", "N/A")
            snippet = detail.get("snippet", "")
            label_ids = detail.get("labelIds", [])
            is_unread = "UNREAD" in label_ids
            
            print(f"\n  [{i+1}] {'🔴 UNREAD' if is_unread else '✅ READ'} — {subj}")
            print(f"      From: {frm}")
            print(f"      Date: {date}")
            print(f"      Snippet: {snippet[:250]}")
            
            # Check for handover/wallet related keywords
            body = extract_email_body(detail)
            body_lower = body.lower()
            keywords = ["wallet", "handover", "tele-bot", "personal", "transfer", "repo", "code"]
            matched = [k for k in keywords if k in body_lower or k in subj.lower()]
            if matched:
                print(f"      🎯 KEYWORDS MATCHED: {matched}")
                print(f"      Body preview: {body[:800]}")
    
    # 3. Recent emails (last 24h)
    print("\n" + "=" * 50)
    print("📬 RECENT EMAILS (last 20, any sender):")
    print("-" * 50)
    try:
        recent = gmail_api("messages", {"q": "newer_than:2d", "maxResults": 20})
        recent_list = recent.get("messages", [])
    except Exception as e:
        print(f"Error: {e}")
        recent_list = []
    
    # Remove duplicates with unread
    unread_ids = {m["id"] for m in unread_msgs}
    nova_from_ids = {m["id"] for m in nova_list}
    seen_ids = set()
    
    important_found = []
    count = 0
    for m in recent_list:
        if m["id"] in seen_ids:
            continue
        seen_ids.add(m["id"])
        count += 1
        if count > 20:
            break
            
        detail = get_message_detail(m["id"])
        headers = {h["name"].lower(): h["value"] for h in detail.get("payload", {}).get("headers", [])}
        frm = headers.get("from", "unknown")
        subj = headers.get("subject", "(no subject)")
        date = headers.get("date", "unknown")
        snippet = detail.get("snippet", "")
        label_ids = detail.get("labelIds", [])
        is_unread = "UNREAD" in label_ids
        
        # Skip promotional
        is_promo = "CATEGORY_PROMOTIONS" in label_ids or "CATEGORY_SOCIAL" in label_ids
        unread_mark = "🔴" if is_unread else "  "
        promo_mark = "📢 PROMO" if is_promo else ""
        
        if is_promo:
            continue  # Skip promotional entirely
            
        print(f"\n  [{count}] {unread_mark} {promo_mark} {frm[:60]}")
        print(f"       Subject: {subj[:80]}")
        print(f"       Date: {date}")
        
        # Track important emails
        body = extract_email_body(detail)
        body_lower = body.lower()
        important_kw = ["wallet", "handover", "bot", "urgent", "payment", "invoice", 
                       "nova", "personal-wallet", "tele-bot", "ps vibe", "psvibe"]
        matched_kw = [k for k in important_kw if k in body_lower or k in subj.lower() or k in frm.lower()]
        if matched_kw:
            important_found.append({
                "from": frm,
                "subject": subj,
                "date": date,
                "snippet": snippet[:200],
                "keywords": matched_kw,
                "is_unread": is_unread,
                "is_promo": is_promo
            })
            print(f"       🎯 Matched: {matched_kw}")
    
    # 4. Summary
    print("\n" + "=" * 70)
    print("📊 CONCLUSION:")
    print("=" * 70)
    print(f"  Unread emails: {len(unread_msgs)}")
    print(f"  Nova emails found: {len(nova_list)}")
    print(f"  Important/relevant emails: {len(important_found)}")
    
    if important_found:
        print("\n  ⚠️  IMPORTANT EMAILS DETECTED:")
        for e in important_found:
            print(f"    • From: {e['from']}")
            print(f"      Subject: {e['subject']}")
            print(f"      Date: {e['date']}")
            print(f"      Keywords: {e['keywords']}")
            print()
    else:
        print("\n  ✅ No important/relevant emails found.")
        print("  NO_REPLY")

if __name__ == "__main__":
    main()
