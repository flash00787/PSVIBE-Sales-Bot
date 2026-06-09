#!/usr/bin/env python3
"""Kora Email Sender using Gmail API + OAuth 2.0 (HTTPS port 443)"""
import json, urllib.request, urllib.parse, base64, os
from email.mime.text import MIMEText

WS = os.environ.get("KORA_WS", "/home/node/.openclaw/workspace")
SECRET_FILE = os.path.join(WS, "secret.json")
TOKEN_FILE = os.path.join(WS, "token.json")

with open(SECRET_FILE) as f:
    s = json.load(f)["installed"]
CID = s["client_id"]
CS = s["client_secret"]

def refresh_token():
    """Refresh the access token using saved refresh token"""
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

def send_email(to_addr, subject, body):
    """Send email via Gmail API"""
    token = refresh_token()
    msg = MIMEText(body, "plain", "utf-8")
    msg["To"] = to_addr
    msg["From"] = "chanmyint123456789@gmail.com"
    msg["Subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=json.dumps({"raw": raw}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        result = json.loads(r.read())
    return result.get("id")

if __name__ == "__main__":
    print("send_email_api.py — Email sender module")
    print("Usage: from send_email_api import send_email")
    print("       msg_id = send_email('recipient@example.com', 'Subject', 'Body')")
    print()
    print("⚠️  This script is a module — do NOT run directly.")
    print("   No emails will be sent without explicit function call.")
