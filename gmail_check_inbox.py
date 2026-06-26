#!/usr/bin/env python3
"""Gmail Inbox Checker — fetches unread emails with full metadata."""

import json
import urllib.request
import urllib.parse
import os
import sys
from datetime import datetime, timezone, timedelta

SCRIPT_DIR = "/root/.openclaw/workspace"
TOKEN_FILE = os.path.join(SCRIPT_DIR, "gmail_token.json")
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "credentials.json")

# Load credentials
with open(CREDENTIALS_FILE) as f:
    creds = json.load(f)["installed"]
CLIENT_ID = creds["client_id"]
CLIENT_SECRET = creds["client_secret"]

# Load token
with open(TOKEN_FILE) as f:
    token_data = json.load(f)

REFRESH_TOKEN = token_data.get("refresh_token", "")


def refresh_access_token():
    """Refresh the access token using refresh_token."""
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            new_tokens = json.loads(resp.read())
            token_data["access_token"] = new_tokens["access_token"]
            if "refresh_token" in new_tokens:
                token_data["refresh_token"] = new_tokens["refresh_token"]
            token_data["expires_in"] = 3599
            with open(TOKEN_FILE, "w") as f:
                json.dump(token_data, f, indent=2)
            return new_tokens["access_token"]
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"Token refresh failed (HTTP {e.code}): {err[:300]}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Token refresh failed: {e}", file=sys.stderr)
        sys.exit(1)


def gmail_api(path, access_token, method="GET", data=None, timeout=20):
    """Call Gmail API."""
    url = f"https://gmail.googleapis.com/gmail/v1/{path}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    if data:
        req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method=method)
    else:
        req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"API error {e.code} on {path}: {err_body[:300]}", file=sys.stderr)
        return None


def get_header(headers, name):
    """Extract header value from Gmail header list."""
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def main():
    access_token = refresh_access_token()
    print("Token refreshed OK", file=sys.stderr)

    # Step 1: List unread messages (max 30)
    result = gmail_api(
        "users/me/messages?q=is:unread&maxResults=30",
        access_token
    )
    if not result:
        print("Failed to fetch messages", file=sys.stderr)
        sys.exit(1)

    messages = result.get("messages", [])
    result_size = result.get("resultSizeEstimate", 0)
    print(f"Unread messages: {len(messages)} (estimated: {result_size})", file=sys.stderr)

    if not messages:
        output = {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "total_unread": 0,
            "nova_found": False,
            "nova_emails": [],
            "important_emails": [],
            "all_emails": [],
        }
        out_path = os.path.join(SCRIPT_DIR, "gmail_check_results.json")
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # Step 2: Fetch full details for each message
    all_emails = []
    nova_emails = []
    important_emails = []

    NOVA_EMAIL = "yeyintoo12345678@gmail.com"

    # Important sender patterns
    IMPORTANT_PATTERNS = [
        "github.com", "gitlab.com",
        "digitalocean.com",
        "strategyfirst",
        "psvibe", "ps vibe",
        "synergy",
        "invoice", "payment", "subscription", "billing",
        "security", "login", "password", "hack",
        "handover", "wallet", "tele-bot", "telebot",
        "urgent", "important",
        "noreply@",
        "bank", "transfer",
        "receipt",
        "server", "vps", "hosting",
    ]

    for i, msg in enumerate(messages):
        msg_id = msg["id"]
        thread_id = msg.get("threadId", "")

        full = gmail_api(
            f"users/me/messages/{msg_id}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date&metadataHeaders=To&metadataHeaders=Cc",
            access_token
        )
        if not full:
            continue

        headers = full.get("payload", {}).get("headers", [])
        from_addr = get_header(headers, "From")
        subject = get_header(headers, "Subject")
        date_str = get_header(headers, "Date")
        snippet = full.get("snippet", "")

        email_info = {
            "id": msg_id,
            "threadId": thread_id,
            "from": from_addr,
            "subject": subject,
            "date": date_str,
            "snippet": snippet,
            "unread": True,
        }

        all_emails.append(email_info)

        # Check for Nova
        if NOVA_EMAIL.lower() in from_addr.lower():
            email_info["nova"] = True
            nova_emails.append(email_info)

        # Check for important
        combined = (from_addr + " " + subject + " " + (snippet or "")).lower()
        is_important = any(p.lower() in combined for p in IMPORTANT_PATTERNS)
        if is_important and NOVA_EMAIL.lower() not in from_addr.lower():
            email_info["important"] = True
            important_emails.append(email_info)

        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(messages)}...", file=sys.stderr)

    output = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "total_unread": len(messages),
        "nova_found": len(nova_emails) > 0,
        "nova_emails": nova_emails,
        "important_emails": important_emails,
        "all_emails": all_emails,
    }

    out_path = os.path.join(SCRIPT_DIR, "gmail_check_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {out_path}", file=sys.stderr)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
