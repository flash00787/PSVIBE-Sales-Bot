from google_auth_oauthlib.flow import InstalledAppFlow
import sys
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def main():
    if len(sys.argv) < 2:
        print("Usage: python exchange_code.py <authorization_code>")
        sys.exit(1)
        
    code = sys.argv[1]
    
    flow = InstalledAppFlow.from_client_secrets_file(
        '/home/node/.openclaw/workspace/credentials.json',
        scopes=SCOPES
    )
    flow.redirect_uri = 'http://localhost'
    
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        token_path = '/home/node/.openclaw/workspace/token.json'
        with open(token_path, 'w') as token_file:
            token_file.write(credentials.to_json())
            
        print(f"Success! Credentials saved to {token_path}")
    except Exception as e:
        print(f"Error exchanging code: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
