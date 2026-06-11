#!/usr/bin/env python3
"""
Check shared drives and try uploading with PS VIBE service account.
Also share game folders with PS VIBE account so it can upload.
"""
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

OPENCLAW_SA = "/home/node/.openclaw/workspace/service-account.json"
PSVIBE_SA = "/tmp/service_account.json"

def get_service(key_file, scopes=None):
    if scopes is None:
        scopes = ['https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_file(key_file, scopes=scopes)
    return build('drive', 'v3', credentials=creds)

# Check shared drives with both accounts
for name, key_file in [("openclawagent", OPENCLAW_SA), ("psvibe", PSVIBE_SA)]:
    print(f"\n{'='*60}")
    print(f"Account: {name}")
    
    with open(key_file) as f:
        info = json.load(f)
    print(f"Email: {info['client_email']}")
    
    service = get_service(key_file)
    
    # Check shared drives
    try:
        results = service.drives().list(pageSize=50).execute()
        drives = results.get('drives', [])
        print(f"Shared drives: {len(drives)}")
        for d in drives:
            print(f"  - {d['name']} (id: {d['id']})")
    except Exception as e:
        print(f"  Shared drives error: {e}")
    
    # Check About (storage quota)
    try:
        about = service.about().get(fields="storageQuota,user").execute()
        sq = about.get('storageQuota', {})
        print(f"  Storage quota: limit={sq.get('limit')}, usage={sq.get('usage')}")
        print(f"  User: {about.get('user', {}).get('emailAddress')}")
    except Exception as e:
        print(f"  About error: {e}")
    
    # Try uploading a tiny test file
    try:
        test_path = "/tmp/drive_test.txt"
        with open(test_path, 'w') as f:
            f.write("test")
        media = MediaFileUpload(test_path, mimetype='text/plain', resumable=True)
        file_metadata = {'name': 'test_upload.txt'}
        f = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"  Test upload SUCCESS: {f['id']}")
        # Clean up
        service.files().delete(fileId=f['id']).execute()
    except Exception as e:
        print(f"  Test upload FAILED: {e}")

# Try to share a game folder with psvibe account
print(f"\n{'='*60}")
print("Sharing game folders with psvibe account...")

# Read psvibe email
with open(PSVIBE_SA) as f:
    psvibe_info = json.load(f)
psvibe_email = psvibe_info['client_email']

openclaw_service = get_service(OPENCLAW_SA)

# Share the Naruto folder as a test
test_folder_id = "1LL1eejVvabHlHo8M_M9tbe561ixJTy5r"

permission = {
    'type': 'user',
    'role': 'writer',
    'emailAddress': psvibe_email
}

try:
    result = openclaw_service.permissions().create(
        fileId=test_folder_id,
        body=permission,
        sendNotificationEmail=False,
        fields='id'
    ).execute()
    print(f"  Shared Naruto folder with {psvibe_email}: permission id={result['id']}")
except Exception as e:
    print(f"  Share FAILED: {e}")

# Now try uploading with psvibe account to the shared folder
print(f"\nTesting upload with psvibe account to shared folder...")
psvibe_service = get_service(PSVIBE_SA)

test_path = "/tmp/drive_test2.txt"
with open(test_path, 'w') as f:
    f.write("test2")

media = MediaFileUpload(test_path, mimetype='text/plain', resumable=True)
file_metadata = {
    'name': 'test_from_psvibe.txt',
    'parents': [test_folder_id]
}

try:
    f = psvibe_service.files().create(body=file_metadata, media_body=media, fields='id,name').execute()
    print(f"  Psvibe upload SUCCESS: {f['name']} ({f['id']})")
    # Clean up
    psvibe_service.files().delete(fileId=f['id']).execute()
except Exception as e:
    print(f"  Psvibe upload FAILED: {e}")
