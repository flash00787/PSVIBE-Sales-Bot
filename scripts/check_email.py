import os, json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

token_path = '/home/node/.openclaw/workspace/token.json'
secret_path = '/home/node/.openclaw/workspace/secret.json'

creds = None
if os.path.exists(token_path):
    creds = Credentials.from_authorized_user_file(token_path, ['https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/gmail.send'])

if not creds or not creds.valid:
    print('TOKEN_EXPIRED')
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, 'w') as f:
            f.write(creds.to_json())
        print('TOKEN_REFRESHED')
else:
    print('TOKEN_VALID')

if creds and creds.valid:
    service = build('gmail', 'v1', credentials=creds)
    # Search for Nova-related emails
    results = service.users().messages().list(
        userId='me', 
        maxResults=10, 
        q='(from:nova OR from:yeyintoo OR to:nova OR nova agent)'
    ).execute()
    msgs = results.get('messages', [])
    print(f'FOUND {len(msgs)} related emails')
    for m in msgs:  # Just show first 3
        msg = service.users().messages().get(
            userId='me', id=m['id'], format='metadata',
            metadataHeaders=['From','To','Subject','Date']
        ).execute()
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
        print(f"  - {headers.get('Date','?')[:25]} | From: {headers.get('From','?')} | Subject: {headers.get('Subject','?')}")
    
    # Also check recent unread
    results2 = service.users().messages().list(
        userId='me', maxResults=5, q='is:unread'
    ).execute()
    unread = results2.get('messages', [])
    print(f'\nUNREAD: {len(unread)} unread emails')
    for m in unread:
        msg = service.users().messages().get(
            userId='me', id=m['id'], format='metadata',
            metadataHeaders=['From','To','Subject','Date']
        ).execute()
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
        print(f"  - {headers.get('Date','?')[:25]} | From: {headers.get('From','?')} | Subject: {headers.get('Subject','?')}")
else:
    print('NO_CREDENTIALS')
