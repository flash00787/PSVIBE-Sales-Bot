#!/usr/bin/env python3
"""
Complete Google Drive OAuth re-auth after user visits auth URL.
Usage: python3 reauth_drive.py <auth_code_or_redirect_url>
The code_verifier is loaded from /tmp/drive_auth_state.json
"""
import json, sys, urllib.parse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CLIENT_SECRET = '/root/.openclaw/workspace/client_secret.json'
TOKEN_PATH = '/root/.openclaw/workspace/token.json'
STATE_PATH = '/tmp/drive_auth_state.json'

code = sys.argv[1] if len(sys.argv) > 1 else input("Paste auth code or redirect URL: ").strip()

# Extract code from redirect URL if full URL is pasted
if code.startswith('http'):
    parsed = urllib.parse.urlparse(code)
    params = urllib.parse.parse_qs(parsed.query)
    if 'code' in params:
        code = params['code'][0]
    elif 'error' in params:
        print(f"❌ Auth error: {params.get('error', ['unknown'])[0]}")
        sys.exit(1)

# Load saved code_verifier
try:
    with open(STATE_PATH) as f:
        auth_state = json.load(f)
except FileNotFoundError:
    print(f"❌ Auth state not found at {STATE_PATH}. Run generate step first.")
    sys.exit(1)

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, scopes=SCOPES)
flow.redirect_uri = auth_state['redirect_uri']

# Manually set code_verifier on the flow's OAuth session
flow.code_verifier = auth_state['code_verifier']
flow.oauth2session._client.code_verifier = auth_state['code_verifier']

flow.fetch_token(code=code)

with open(TOKEN_PATH, 'w') as f:
    f.write(flow.credentials.to_json())

# Cleanup state
import os; os.remove(STATE_PATH)

print(f"✅ Token saved to {TOKEN_PATH}")
print(f"   Expires: {flow.credentials.expiry}")
print(f"   Has refresh_token: {bool(flow.credentials.refresh_token)}")
