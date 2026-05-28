import os, json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']
creds = None

if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    else:
        print('NO_VALID_CREDS')
        exit(1)

service = build('gmail', 'v1', credentials=creds)

results = service.users().messages().list(userId='me', maxResults=10, q='in:inbox').execute()
messages = results.get('messages', [])

print(f'Total messages (last 10): {len(messages)}')
print('=' * 70)

for msg in messages:
    msg_data = service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['From','Subject','Date']).execute()
    headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
    label_ids = msg_data.get('labelIds', [])
    is_unread = 'UNREAD' in label_ids
    
    unread_tag = '🟢 UNREAD' if is_unread else '⚪ Read'
    print()
    print(f"ID: {msg['id']}")
    print(f"From: {headers.get('From','N/A')}")
    print(f"Subject: {headers.get('Subject','N/A')}")
    print(f"Date: {headers.get('Date','N/A')}")
    print(f"Status: {unread_tag}")
    print('---')
