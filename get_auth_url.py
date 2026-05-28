from google_auth_oauthlib.flow import InstalledAppFlow
import json

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
    print(f"STATE: {state}")

if __name__ == '__main__':
    main()
