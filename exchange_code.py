#!/usr/bin/env python3
"""
Exchange OAuth authorization code for Gmail tokens.
Usage: python3 exchange_code.py '<authorization_code_or_redirect_url>'
"""
import sys
import os
import urllib.parse
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 exchange_code.py '<code_or_redirect_url>'")
        sys.exit(1)

    code_or_url = sys.argv[1]
    code = code_or_url
    if "code=" in code_or_url:
        parsed = urllib.parse.urlparse(code_or_url)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            code = params["code"][0]

    print(f"Exchanging code: {code} ...")

    flow = InstalledAppFlow.from_client_secrets_file(
        '/home/node/.openclaw/workspace/credentials.json',
        scopes=SCOPES
    )
    flow.redirect_uri = 'http://localhost'

    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials

        token_path = '/home/node/.openclaw/workspace/token.json'
        with open(token_path, 'w') as f:
            f.write(credentials.to_json())

        print(f"✅ Success! New token saved to {token_path}")
        print(f"   Expiry: {credentials.expiry}")
        print(f"   Scopes: {credentials.scopes}")
    except Exception as e:
        print(f"❌ Error exchanging code: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
