from google_auth_oauthlib.flow import InstalledAppFlow
import sys
import urllib.parse

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        '/home/node/.openclaw/workspace/credentials.json',
        scopes=SCOPES
    )
    flow.redirect_uri = 'http://localhost'
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    print("--- AUTHORIZATION URL ---")
    print(authorization_url)
    print("-------------------------")
    print("Please input the code or redirect URL:")
    sys.stdout.flush()
    
    # Read input
    code_or_url = sys.stdin.readline().strip()
    
    code = code_or_url
    if "code=" in code_or_url:
        parsed = urllib.parse.urlparse(code_or_url)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            code = params["code"][0]
            
    print(f"Exchanging code: {code} ...")
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        token_path = '/home/node/.openclaw/workspace/token.json'
        with open(token_path, 'w') as token_file:
            token_file.write(credentials.to_json())
            
        print(f"Success! Credentials saved to {token_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
