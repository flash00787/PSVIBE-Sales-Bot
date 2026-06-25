#!/usr/bin/env python3
"""Gmail Inbox Checker via IMAP — focused on recent & important emails"""
import imaplib
import email
import ssl
import re
from email.header import decode_header
from datetime import datetime, timezone, timedelta

EMAIL = "chanmyint123456789@gmail.com"
APP_PASSWORD = "knpeqhkhwbvhmwey"

def decode_hdr(s):
    if not s:
        return ""
    parts = decode_header(s)
    result = []
    for text, charset in parts:
        if isinstance(text, bytes):
            result.append(text.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(str(text))
    return "".join(result)

def get_body(msg):
    try:
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                cd = part.get("Content-Disposition", "")
                if ct == "text/plain" and "attachment" not in cd:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            return payload.decode("utf-8", errors="replace")[:500]
                    except:
                        pass
            return "(multipart — no text)"
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode("utf-8", errors="replace")[:500]
    except:
        return "(decode error)"
    return ""

def is_promotional(sender, subject, body):
    """Filter out promotional/newsletter/social media emails"""
    promo_domains = [
        "twitter.com", "info@twitter", "@insideapple", "@email.apple.com",
        "shopifyemail.com", "wordpress.com", "foodpanda", "youtube.com",
        "@ses.binance.com", "mailersp", "@maiair.aero", "zoom.us",
        "quora.com", "medium.com", "linkedin.com", "facebookmail.com",
        "instagram.com", "pinterest.com", "reddit.com"
    ]
    combined = f"{sender} {subject}".lower()
    for d in promo_domains:
        if d in combined:
            return True
    
    promo_keywords = [
        "just uploaded a video", "tweeted:", "don't be selfish",
        "refer a friend", "offer!", "sale!", "discount", "deal",
        "newsletter", "weekly digest", "your highlights",
        "apps you'll feel", "new post", "free download",
        "schedule a zoom meeting", "shared \"", "last call:",
        "be fast, iphone", "complete missions"
    ]
    combined2 = combined + " " + body[:200]
    for kw in promo_keywords:
        if kw in combined2.lower():
            return True
    return False

print("=" * 70)
print("📬 GMAIL INBOX CHECK — Morning Routine")
print(f"   Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
print("=" * 70)

ctx = ssl.create_default_context()
conn = imaplib.IMAP4_SSL("imap.gmail.com", 993, ssl_context=ctx, timeout=20)
conn.login(EMAIL, APP_PASSWORD)
conn.select("INBOX")

# Get recent emails (last 7 days to be safe, but focus on last 2)
since_7d = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
since_2d = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")

# Search for emails in last 2 days first (most relevant)
status, data = conn.search(None, f"SINCE {since_2d}")
recent_ids_2d = data[0].split() if data[0] else []

# Also check last 7 days for Nova specifically
status, data = conn.search(None, f"SINCE {since_7d}")
recent_ids_7d = data[0].split() if data[0] else []

print(f"Recent (2 days): {len(recent_ids_2d)}")
print(f"Recent (7 days): {len(recent_ids_7d)}")

# Process 2-day emails first (most relevant)
nova_emails = []
important_emails = []
wallet_emails = []
other_emails = []
unread_count = 0

# Process 2-day emails
for mid in recent_ids_2d:
    try:
        status, data = conn.fetch(mid, "(FLAGS RFC822)")
        if not data or not data[0]:
            continue
        
        # Parse flags
        flags_raw = ""
        msg_bytes = None
        for item in data:
            if isinstance(item, tuple):
                # item[0] is flags like b'123 (FLAGS (\\Seen))'
                flags_raw = item[0].decode("utf-8", errors="replace") if isinstance(item[0], bytes) else str(item[0])
                msg_bytes = item[1]
                break
        
        if not msg_bytes:
            continue
        
        is_unread = "\\Seen" not in flags_raw
        if is_unread:
            unread_count += 1
        
        msg = email.message_from_bytes(msg_bytes)
        subject = decode_hdr(msg.get("Subject", "(no subject)"))
        sender = decode_hdr(msg.get("From", "(unknown)"))
        date_str = msg.get("Date", "")
        body = get_body(msg)
        
        combined = f"{sender.lower()} {subject.lower()} {body[:300].lower()}"
        
        info = {
            "from": sender,
            "subject": subject,
            "date": date_str,
            "is_unread": is_unread,
            "body": body[:300]
        }
        
        # Check Nova
        is_nova = "yeyintoo12345678" in combined or "yeyintoo" in sender.lower()
        
        # Check wallet related
        wallet_kw = ["wallet", "personal-wallet", "handover", "tele-bot", "telegram bot"]
        is_wallet = any(kw in combined for kw in wallet_kw)
        
        # Check important
        imp_kw = ["urgent", "action required", "invoice", "payment successful",
                   "security alert", "password reset", "verification required",
                   "account suspended", "important notice", "confirmation"]
        is_important = any(kw in combined for kw in imp_kw)
        
        # Check promotional
        is_promo = is_promotional(sender, subject, body)
        
        if is_nova:
            nova_emails.append(info)
        elif is_wallet:
            wallet_emails.append(info)
        elif is_important and not is_promo:
            important_emails.append(info)
        elif not is_promo:
            other_emails.append(info)
            
    except Exception as e:
        print(f"Error processing msg: {e}")

conn.logout()

# ── PRINT ALL RESULTS ──
print(f"\nUnread (in recent 2d): {unread_count}")
print(f"Filtered (non-promo):  {len(nova_emails) + len(wallet_emails) + len(important_emails) + len(other_emails)}")

def print_emails(label, emails):
    if not emails:
        return
    print(f"\n{'─' * 60}")
    print(f"  {label} ({len(emails)})")
    print(f"{'─' * 60}")
    for e in emails:
        status = "🔴" if e["is_unread"] else "📖"
        print(f"  {status} [{e['date'][:40]}]")
        print(f"     From: {e['from']}")
        print(f"     Subj: {e['subject']}")
        if e.get("body"):
            print(f"     Body: {e['body'][:200]}")
        print()

print_emails("🔴 NOVA EMAILS", nova_emails)
print_emails("💰 WALLET-RELATED", wallet_emails)
print_emails("📌 IMPORTANT", important_emails)
print_emails("📩 OTHER (non-promo)", other_emails)

# ── SUMMARY ──
print(f"\n{'=' * 60}")
print(f"📊 SUMMARY")
print(f"{'=' * 60}")
print(f"Recent 2d total:  {len(recent_ids_2d)}")
print(f"Recent 7d total:  {len(recent_ids_7d)}")
print(f"Nova emails:      {len(nova_emails)}")
print(f"Wallet-related:   {len(wallet_emails)}")
print(f"Important:        {len(important_emails)}")
print(f"Other (non-promo):{len(other_emails)}")

if nova_emails:
    print(f"\n⚠️  NOVA HAS REPLIED!")
    for e in nova_emails:
        print(f"   {e['subject']}")
elif wallet_emails:
    print(f"\n💰 Wallet-related emails found")
elif important_emails:
    print(f"\n📌 Important emails need attention")
else:
    print(f"\n✅ Nothing notable in recent emails.")
    print(f"   (Promotional/social emails filtered out)")

# Output JSON-like summary for automation
print(f"\n__CHECK_RESULT__")
print(f"NOVA_REPLY={'yes' if nova_emails else 'no'}")
print(f"UNREAD_RECENT={unread_count}")
print(f"IMPORTANT_COUNT={len(important_emails)}")
print(f"WALLET_COUNT={len(wallet_emails)}")
print(f"OTHER_COUNT={len(other_emails)}")
