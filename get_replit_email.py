#!/usr/bin/env python3
import base64, json, os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file('/root/.openclaw/workspace/token.json', ['https://www.googleapis.com/auth/gmail.readonly'])
service = build('gmail', 'v1', credentials=creds)

# Find Replit email
result = service.users().messages().list(userId='me', q="from:notifications@replit.com Personal-Wallet-Tele-Bot", maxResults=5).execute()
msgs = result.get('messages', [])
print(f"Found {len(msgs)} messages matching Replit query")

for m in msgs:
    msg = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
    payload = msg.get('payload', {})
    
    headers = {h['name']: h['value'] for h in payload.get('headers', [])}
    print(f"\n{'='*60}")
    print(f"From: {headers.get('From')}")
    print(f"Subject: {headers.get('Subject')}")
    print(f"Date: {headers.get('Date')}")
    print(f"Labels: {msg.get('labelIds')}")
    
    # Get body
    body = ""
    if payload.get('body', {}).get('data'):
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
    else:
        parts = payload.get('parts', [])
        for p in parts:
            if p.get('mimeType') == 'text/plain' and p.get('body', {}).get('data'):
                body = base64.urlsafe_b64decode(p['body']['data']).decode('utf-8', errors='replace')
                break
            if p.get('parts'):
                for sp in p['parts']:
                    if sp.get('mimeType') == 'text/plain' and sp.get('body', {}).get('data'):
                        body = base64.urlsafe_b64decode(sp['body']['data']).decode('utf-8', errors='replace')
                        break
    
    print(f"\nBody:\n{body[:2000]}")
    print("="*60)

# Also check n8n security email
result2 = service.users().messages().list(userId='me', q="from:security@info.n8n.io", maxResults=5).execute()
msgs2 = result2.get('messages', [])
print(f"\n\nFound {len(msgs2)} n8n security emails")

for m in msgs2:
    msg = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
    payload = msg.get('payload', {})
    headers = {h['name']: h['value'] for h in payload.get('headers', [])}
    print(f"Subject: {headers.get('Subject')}")
