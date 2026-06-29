#!/usr/bin/env python3
"""Evening Gmail Check — IMAP via app password"""
import imaplib, email, ssl, json, os, sys
from email.header import decode_header
from datetime import datetime, timezone, timedelta

EMAIL = "chanmyint123456789@gmail.com"
APP_PASSWORD = "knpeqhkhwbvhmwey"
WS = "/root/.openclaw/workspace"

def decode_hdr(s):
    if not s: return ""
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
                        p = part.get_payload(decode=True)
                        if p: return p.decode("utf-8", errors="replace")[:800]
                    except: pass
            return "(multipart)"
        else:
            p = msg.get_payload(decode=True)
            if p: return p.decode("utf-8", errors="replace")[:800]
    except: return "(error)"
    return ""

def is_promotional(sender, subject, body):
    s = (sender + " " + subject + " " + body[:200]).lower()
    promo = [
        "newsletter", "n8n.io", "info@n8n", "twitch.tv", "dior", "pexx.com",
        "google play", "thank you for your purchase", "subscription",
        "weekly digest", "unsubscribe", "sale ends", "just uploaded",
        "tweeted:", "don't be selfish", "refer a friend", "offer!",
        "your highlights", "new post", "free download", "youtube.com",
        "shopifyemail.com", "foodpanda", "quora.com", "medium.com",
        "linkedin.com", "facebookmail.com", "instagram.com", "pinterest",
        "reddit.com", "mailersp", "zoom.us", "complete missions",
        "github.com", "notifications@github", "@insideapple",
        "@ses.binance.com", "maiair.aero", "wordpress.com",
        "brand assault", "tres chic", "big discount", "flash sale",
        "clearance", "limited time", "don't miss", "exclusive offer",
        "promo code", "junkjet.pink"
    ]
    return any(k in s for k in promo)

# Connect
ctx = ssl.create_default_context()
conn = imaplib.IMAP4_SSL("imap.gmail.com", 993, ssl_context=ctx, timeout=25)
conn.login(EMAIL, APP_PASSWORD)
conn.select("INBOX")

# Get unread
status, data = conn.search(None, "UNSEEN")
unread_ids = data[0].split() if data[0] else []
print(f"🔵 UNREAD: {len(unread_ids)}")

# Get last 3 days
since_3d = (datetime.now() - timedelta(days=3)).strftime("%d-%b-%Y")
status, data = conn.search(None, f"SINCE {since_3d}")
recent_ids = data[0].split() if data[0] else []
print(f"🕐 RECENT (3d): {len(recent_ids)}")

# Combine + deduplicate
all_ids = list({mid.decode() if isinstance(mid, bytes) else mid for mid in unread_ids + recent_ids})
print(f"📋 Unique to process: {len(all_ids)}")

nova_emails = []
wallet_emails = []
important_emails = []
promo_count = 0
unread_count = 0
total = 0

for mid in all_ids:
    try:
        status, data = conn.fetch(mid.encode() if isinstance(mid, str) else mid, "(FLAGS RFC822)")
        if not data or not data[0]: continue
        
        flags_raw = ""
        msg_bytes = None
        for item in data:
            if isinstance(item, tuple):
                flags_raw = item[0].decode("utf-8", errors="replace") if isinstance(item[0], bytes) else str(item[0])
                msg_bytes = item[1]
                break
        
        if not msg_bytes: continue
        total += 1
        
        is_unread = "\\Seen" not in flags_raw
        if is_unread: unread_count += 1
        
        msg = email.message_from_bytes(msg_bytes)
        subject = decode_hdr(msg.get("Subject", "(no subject)"))
        sender = decode_hdr(msg.get("From", "(unknown)"))
        date_str = msg.get("Date", "")
        body = get_body(msg)
        
        combined = f"{sender.lower()} {subject.lower()} {body[:400].lower()}"
        status_icon = "🔵" if is_unread else "⚪"
        
        # Check promotional
        if is_promotional(sender, subject, body):
            promo_count += 1
            print(f"[{total}] {status_icon} PROMO | {sender[:50]}")
            print(f"    Subject: {subject[:80]}")
            continue
        
        info = {
            "from": sender, "subject": subject, "date": date_str,
            "is_unread": is_unread, "body_preview": body[:400]
        }
        
        # Check Nova
        is_nova = "yeyintoo12345678" in combined or "yeyintoo" in sender.lower()
        
        # Wallet-related
        wallet_kw = ["wallet", "personal-wallet", "handover", "tele-bot"]
        is_wallet = any(kw in combined for kw in wallet_kw)
        
        # Important
        imp_kw = ["urgent", "action required", "invoice", "payment",
                   "security alert", "password reset", "verification",
                   "account suspended", "important notice", "confirmation",
                   "ps vibe", "synergy hub", "booking"]
        is_important = any(kw in combined for kw in imp_kw)
        
        if is_nova:
            nova_emails.append(info)
            label = "🔴 NOVA"
        elif is_wallet:
            wallet_emails.append(info)
            label = "💰 WALLET"
        elif is_important:
            important_emails.append(info)
            label = "📌 IMPORTANT"
        else:
            label = "📩 OTHER"
        
        print(f"[{total}] {status_icon} {label} | {sender[:50]}")
        print(f"    Subject: {subject[:80]}")
        if body.strip() and body.strip() != "(multipart)":
            print(f"    Body: {body[:150]}")
        
    except Exception as e:
        print(f"  ❌ Error {mid}: {e}")

conn.logout()

# Summary
print(f"\n{'='*60}")
print("📊 EVENING CHECK SUMMARY")
print(f"{'='*60}")
print(f"Total processed:    {total}")
print(f"Unread:             {unread_count}")
print(f"Promo (skipped):    {promo_count}")
print(f"Nova emails:        {len(nova_emails)}")
print(f"Wallet-related:     {len(wallet_emails)}")
print(f"Important:          {len(important_emails)}")

for e in nova_emails:
    print(f"\n🔴 NOVA: {e['subject'][:80]}")
    print(f"   From: {e['from']}")
    print(f"   Date: {e['date']}")
    print(f"   Body: {e['body_preview'][:300]}")

for e in wallet_emails:
    print(f"\n💰 WALLET: {e['subject'][:80]}")
    print(f"   From: {e['from']}")
    print(f"   Body: {e['body_preview'][:200]}")

for e in important_emails:
    print(f"\n📌 IMPORTANT: {e['subject'][:80]}")
    print(f"   From: {e['from']}")
    print(f"   Body: {e['body_preview'][:200]}")

# Final result tags
result_tags = []
if nova_emails:
    result_tags.append("NOVA_REPLY_FOUND")
if wallet_emails:
    result_tags.append("WALLET_FOUND")
if important_emails:
    result_tags.append("IMPORTANT_FOUND")

result = ",".join(result_tags) if result_tags else "NO_REPLY"
print(f"\n🎯 RESULT: {result}")

# Save JSON
with open(os.path.join(WS, "gmail_evening_result.json"), "w") as f:
    json.dump({
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "total": total, "unread": unread_count, "promo_skipped": promo_count,
        "nova_count": len(nova_emails), "wallet_count": len(wallet_emails),
        "important_count": len(important_emails),
        "nova_emails": nova_emails, "wallet_emails": wallet_emails,
        "important_emails": important_emails, "result": result
    }, f, indent=2, ensure_ascii=False)

print(f"\n__FINAL__: {result}")
