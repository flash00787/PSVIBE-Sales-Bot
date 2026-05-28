#!/usr/bin/env python3
"""Get detailed body of important emails."""
import os
import base64
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = '/home/node/.openclaw/workspace/token.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def refresh_token():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    return creds

def get_email_body(service, msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    payload = msg.get('payload', {})
    
    if payload.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
    
    def decode_parts(parts):
        for part in parts:
            if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
            if part.get('parts'):
                result = decode_parts(part['parts'])
                if result:
                    return result
        return None
    
    result = decode_parts(payload.get('parts', []))
    return result or "[Body could not be decoded]"

# Search for the Replit email about Personal-Wallet-Tele-Bot
def search_emails(service, query):
    result = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
    return result.get('messages', [])

creds = refresh_token()
service = build('gmail', 'v1', credentials=creds)

# Search for Nova emails specifically
print("=" * 60)
print("🔍 Searching for Nova emails...")
nova_msgs = search_emails(service, "from:yeyintoo12345678@gmail.com")
if nova_msgs:
    for m in nova_msgs:
        meta = service.users().messages().get(userId='me', id=m['id'], format='metadata',
            metadataHeaders=['From', 'To', 'Subject', 'Date']).execute()
        headers = {h['name']: h['value'] for h in meta.get('payload', {}).get('headers', [])}
        print(f"\nFrom: {headers.get('From')}")
        print(f"Subject: {headers.get('Subject')}")
        print(f"Date: {headers.get('Date')}")
        body = get_email_body(service, m['id'])
        print(f"Body:\n{body[:500]}")
else:
    print("❌ No emails from Nova (yeyintoo12345678@gmail.com) found.")

# Search for Personal-Wallet-Tele-Bot related
print("\n" + "=" * 60)
print("🔍 Searching for Personal-Wallet-Tele-Bot emails...")
pw_msgs = search_emails(service, "Personal-Wallet-Tele-Bot")
if pw_msgs:
    for m in pw_msgs:
        meta = service.users().messages().get(userId='me', id=m['id'], format='metadata',
            metadataHeaders=['From', 'To', 'Subject', 'Date']).execute()
        headers = {h['name']: h['value'] for h in meta.get('payload', {}).get('headers', [])}
        print(f"\nFrom: {headers.get('From')}")
        print(f"Subject: {headers.get('Subject')}")
        print(f"Date: {headers.get('Date')}")
        body = get_email_body(service, m['id'])
        print(f"Body:\n{body[:800]}")
else:
    print("❌ No emails about Personal-Wallet-Tele-Bot found.")

# Check recent AYA OTP notifications
print("\n" + "=" * 60)
print("🔍 Checking AYA Bank OTP notifications...")
aya_msgs = search_emails(service, "from:noreply.securetransaction@ayabank.com newer_than:1d")
if aya_msgs:
    for m in aya_msgs:
        meta = service.users().messages().get(userId='me', id=m['id'], format='metadata',
            metadataHeaders=['From', 'To', 'Subject', 'Date']).execute()
        headers = {h['name']: h['value'] for h in meta.get('payload', {}).get('headers', [])}
        print(f"From: {headers.get('From')}")
        print(f"Subject: {headers.get('Subject')}")
        print(f"Date: {headers.get('Date')}")

# Check recent Transaction notification
print("\n" + "=" * 60)
print("🔍 Checking AYA Transaction Notification...")
txn_msgs = search_emails(service, "TRANSACTION NOTIFICATION newer_than:1d")
if txn_msgs:
    for m in txn_msgs:
        meta = service.users().messages().get(userId='me', id=m['id'], format='metadata',
            metadataHeaders=['From', 'To', 'Subject', 'Date']).execute()
        headers = {h['name']: h['value'] for h in meta.get('payload', {}).get('headers', [])}
        print(f"From: {headers.get('From')}")
        print(f"Subject: {headers.get('Subject')}")
        print(f"Date: {headers.get('Date')}")
        body = get_email_body(service, m['id'])
        print(f"Body:\n{body[:500]}")

print("\n✅ Detailed check complete.")
