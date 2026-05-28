import os
import sys
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def main():
    recipient = "yeyintoo12345678@gmail.com"
    subject = "PS Vibe Bots - Comprehensive Security & Architecture Audit Report"
    
    body = """Mingalabar Ye Yint Oo,

Aung Chan Myint requested me to send you the comprehensive security and architectural audit report for the PS Vibe Bots (Staff Bot, Customer Bot, and shared infrastructure).

Please find the attached audit report file (psvibe_bots_audit_report.md) which contains detailed analyses of security risks, concurrency, and data integrity along with recommended fixes.

Best regards,
Kora (Aung Chan Myint's Personal Assistant)"""

    token_path = '/root/token.json'
    if not os.path.exists(token_path):
        print("token.json not found!")
        sys.exit(1)
        
    creds = Credentials.from_authorized_user_file(token_path)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())
            
    service = build('gmail', 'v1', credentials=creds)
    
    sender = "chanmyint123456789@gmail.com"
    
    # Create MIME message
    msg = MIMEMultipart()
    msg['to'] = recipient
    msg['from'] = sender
    msg['subject'] = subject
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    # Attach file
    file_path = '/root/psvibe_bots_audit_report.md'
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{os.path.basename(file_path)}"'
            )
            msg.attach(part)
    else:
        print("Audit report file not found!")
        sys.exit(1)
        
    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
    
    try:
        sent_message = service.users().messages().send(
            userId="me",
            body={'raw': raw_message}
        ).execute()
        print(f"Success! Email sent to {recipient}. Message ID: {sent_message['id']}")
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
