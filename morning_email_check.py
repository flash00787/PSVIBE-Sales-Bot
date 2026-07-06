#!/usr/bin/env python3
"""Morning Email Check — checks Gmail inbox for new/unread/important emails"""
import json, urllib.request, urllib.parse, base64, os, sys
from datetime import datetime, timezone

WS = "/root/.openclaw/workspace"
TOKEN_FILE = os.path.join(WS, "token.json")
SECRET_FILE = os.path.join(WS, "secret.json")

def refresh_token():
    with open(SECRET_FILE) as f:
        s = json.load(f)["installed"]
    with open(TOKEN_FILE) as f:
        td = json.load(f)
    # Only refresh if expired
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
    if "refresh_token" in nt:
        td["refresh_token"] = nt["refresh_token"]
    with open(TOKEN_FILE, "w") as f:
        json.dump(td, f)
    return nt["access_token"]

def gmail_api(path, token, params=None):
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def get_header(payload, name):
    for h in payload.get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""

def decode_body(payload):
    body_text = ""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            body_text = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    elif "parts" in payload:
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body_text += base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
                break
        if not body_text:
            for part in payload.get("parts", []):
                data = part.get("body", {}).get("data", "")
                if data:
                    body_text += base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    return body_text

def main():
    print("=" * 60)
    print("☀️ MORNING EMAIL CHECK")
    print(f"   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    token = refresh_token()

    # Fetch unread messages
    unread = gmail_api("messages", token, {"q": "is:unread", "maxResults": 30})
    unread_msgs = unread.get("messages", [])
    print(f"\n🔵 Unread: {len(unread_msgs)}")

    # Fetch recent (last 3 days)
    recent = gmail_api("messages", token, {"q": "newer_than:3d", "maxResults": 30})
    recent_msgs = recent.get("messages", [])
    print(f"🕐 Recent (3d): {len(recent_msgs)}")

    # Deduplicate
    all_ids = {}
    for m in unread_msgs + recent_msgs:
        all_ids[m["id"]] = m

    if not all_ids:
        print("\n✅ No unread or recent emails found.")
        return "NO_REPLY", {}

    print(f"\n📋 Processing {len(all_ids)} messages...\n")

    # Promo keywords/senders to filter out
    promo_keywords = [
        "newsletter", "n8n", "twitch", "dior", "eSIM", "pexx",
        "google play", "subscription", "weekly digest", "unsubscribe",
        "sale", "discount", "promotion", "community party",
        "thank you for your purchase"
    ]
    promo_senders = [
        "noreply@", "no-reply@", "notifications@github.com",
        "newsletter@", "marketing@", "info@n8n", "twitch.tv",
        "dior", "pexx.com", "noreply"
    ]

    important_emails = []
    nova_emails = []
    promo_emails = []
    normal_emails = []

    for msg_id in all_ids:
        try:
            msg = gmail_api(f"messages/{msg_id}", token, {"format": "full"})
            payload = msg.get("payload", {})
            
            subject = get_header(payload, "subject") or "(no subject)"
            from_addr = get_header(payload, "from") or ""
            date_str = get_header(payload, "date") or ""
            snippet = msg.get("snippet", "")
            body = decode_body(payload)
            is_unread = "UNREAD" in msg.get("labelIds", [])

            combined = f"{subject} {snippet} {body[:300]}".lower()
            
            # Check promo
            is_promo = any(kw in combined for kw in promo_keywords) or \
                       any(ps in from_addr.lower() for ps in promo_senders)

            entry = {
                "id": msg_id,
                "from": from_addr,
                "subject": subject,
                "date": date_str,
                "unread": is_unread,
                "snippet": snippet[:150],
                "body_preview": body[:400]
            }

            if is_promo:
                promo_emails.append(entry)
                print(f"  ⚪ [PROMO] {from_addr[:40]} — {subject[:50]}")
                continue

            status = "🔵" if is_unread else "⚪"
            print(f"  {status} {from_addr[:40]} | {subject[:60]}")

            # Check for Nova
            if "yeyintoo12345678" in from_addr.lower() or "yeyintoo12345678" in body.lower():
                nova_emails.append(entry)
                print(f"         ⚠️  NOVA EMAIL!")
                continue

            # Check important keywords
            important_keywords = [
                "handover", "urgent", "payment", "invoice", "wallet",
                "important", "action required", "confirm", "verification",
                "security alert", "password reset", "account",
                "ps vibe", "synergy", "business", "client",
                "telegram bot", "booking", "contract", "agreement",
                "meeting", "deadline", "overdue"
            ]
            matched = [kw for kw in important_keywords if kw in combined]
            if matched:
                entry["keywords"] = matched
                important_emails.append(entry)
                print(f"         📌 Keywords: {', '.join(matched)}")

            normal_emails.append(entry)

        except Exception as e:
            print(f"  ❌ Error: {e}")

    # === SUMMARY ===
    print(f"\n{'=' * 60}")
    print("📊 SUMMARY")
    print(f"{'=' * 60}")
    print(f"   Total: {len(all_ids)} unique messages")
    print(f"   Unread: {len(unread_msgs)}")
    print(f"   Promo/skip: {len(promo_emails)}")
    print(f"   Nova: {len(nova_emails)}")
    print(f"   Important: {len(important_emails)}")
    print(f"   Normal: {len(normal_emails)}")

    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "total": len(all_ids),
        "unread": len(unread_msgs),
        "promo": len(promo_emails),
        "nova": len(nova_emails),
        "important": len(important_emails),
        "normal": len(normal_emails),
        "nova_emails": nova_emails,
        "important_emails": important_emails,
        "promo_emails": promo_emails[:5],
        "normal_emails": normal_emails[:5]
    }

    # Save results
    with open(os.path.join(WS, "morning_email_check_result.json"), "w") as f:
        json.dump(result, f, indent=2)

    if nova_emails:
        print(f"\n🔴 NOVA REPLIES FOUND!")
        return "NOVA_REPLY", result
    elif important_emails:
        print(f"\n📌 IMPORTANT EMAILS FOUND!")
        return "IMPORTANT", result
    else:
        print(f"\n✅ Nothing important.")
        return "NO_REPLY", result

if __name__ == "__main__":
    result_type, data = main()
    sys.exit(0)
