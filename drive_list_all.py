#!/usr/bin/env python3
"""List all Google Drive files/folders accessible to the service account."""
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILES = [
    "/tmp/service_account.json",
    "/home/node/.openclaw/workspace/service-account.json"
]

def get_service(key_file):
    creds = service_account.Credentials.from_service_account_file(
        key_file,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)

for key_file in SERVICE_ACCOUNT_FILES:
    print(f"\n{'='*80}")
    print(f"Using service account: {key_file}")
    with open(key_file) as f:
        sa_info = json.load(f)
    print(f"  Email: {sa_info.get('client_email')}")
    
    try:
        service = get_service(key_file)
        
        # List all folders
        print("\n  Folders:")
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name, createdTime)",
            pageSize=100
        ).execute()
        folders = results.get('files', [])
        if not folders:
            print("    (none)")
        for f in folders:
            print(f"    - {f['name']} (id: {f['id']})")
        
        # List all files (non-folders)
        print("\n  All files (first 200):")
        results = service.files().list(
            q="mimeType!='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name, mimeType, size, createdTime, parents)",
            pageSize=200,
            orderBy="name"
        ).execute()
        files = results.get('files', [])
        if not files:
            print("    (none)")
        for f in files[:200]:
            parents = f.get('parents', [])
            print(f"    - {f['name']} ({f['mimeType']}, {f.get('size','?')} bytes, parents: {parents})")
        
        if len(files) >= 200:
            print(f"    ... and more ({len(files)} shown)")
            
    except Exception as e:
        print(f"  ERROR: {e}")
