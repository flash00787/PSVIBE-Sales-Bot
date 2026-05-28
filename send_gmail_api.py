import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def main():
    token_path = '/home/node/.openclaw/workspace/token.json'
    if not os.path.exists(token_path):
        print("token.json not found!")
        return
        
    creds = Credentials.from_authorized_user_file(token_path)
    
    # If credentials expired, refresh them
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())
            
    # Build the service
    service = build('gmail', 'v1', credentials=creds)
    
    # Create the email
    sender = "chanmyint123456789@gmail.com"
    recipient = "chanmyint123456789@gmail.com"
    subject = "Kora Gmail API Connection Test"
    
    body = """Mingalabar Aung Chan Myint,

This is a test email sent from your personal assistant Kora (OpenClaw) using the official Google Gmail API (OAuth 2.0 over HTTPS)!

If you received this, it means our Gmail API integration is working 100% perfectly. It runs safely over HTTPS Port 443, making it completely immune to VPS port blocks.

We can now use this integration to send rich emails and notifications automatically as needed!

Best regards,
Kora"""
    
    message = MIMEText(body, 'plain', 'utf-8')
    message['to'] = recipient
    message['from'] = sender
    message['subject'] = subject
    
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    try:
        sent_message = service.users().messages().send(
            userId="me",
            body={'raw': raw_message}
        ).execute()
        print(f"Success! Email sent. Message ID: {sent_message['id']}")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == '__main__':
    main()
