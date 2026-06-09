import os, json, base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
creds = None

if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

service = build('gmail', 'v1', credentials=creds)

# Important message IDs
msg_ids = [
    '19e6b855bda6eac4',  # You Ko Htet - CoCo Agent Setup
    '19e6a29e9d8a6737',  # AYA Bank Transaction
]

for msg_id in msg_ids:
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    print(f"\n{'='*70}")
    print(f"From: {headers.get('From','N/A')}")
    print(f"Subject: {headers.get('Subject','N/A')}")
    print(f"Date: {headers.get('Date','N/A')}")
    print(f"{'='*70}")
    
    # Get body
    parts = [msg['payload']]
    body_text = ""
    
    while parts:
        part = parts.pop(0)
        if 'parts' in part:
            parts.extend(part['parts'])
        if part.get('mimeType', '').startswith('text/plain') and 'data' in part.get('body', {}):
            data = part['body']['data']
            body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            break
        elif part.get('mimeType', '').startswith('text/html') and 'data' in part.get('body', {}):
            # Keep as fallback
            if not body_text:
                data = part['body']['data']
                body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
    
    print(body_text[:3000] if body_text else "(No text body)")
    
    # Check attachment info
    if 'parts' in msg['payload']:
        for part in msg['payload']['parts']:
            if part.get('filename'):
                print(f"  [Attachment: {part['filename']} ({part['mimeType']})]")
