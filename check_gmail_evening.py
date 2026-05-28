#!/usr/bin/env python3
"""
Evening Gmail Check - Cron Job
Checks for unread/recent emails, especially from Nova about Personal-Wallet-Tele-Bot-2 handover.
"""
import os
import json
import base64
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = '/home/node/.openclaw/workspace/token.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def refresh_token():
    """Refresh token if expired"""
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    return creds

def decode_msg_part(part):
    """Decode email body from a message part."""
    if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
    return None

def get_email_body(service, msg_id):
    """Get full email body text."""
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    
    payload = msg.get('payload', {})
    
    # Try direct body first
    if payload.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
    
    # Try parts
    parts = payload.get('parts', [])
    for part in parts:
        result = decode_msg_part(part)
        if result:
            return result
        # Check nested parts
        if part.get('parts'):
            for subpart in part['parts']:
                result = decode_msg_part(subpart)
                if result:
                    return result
    
    return "[Body could not be decoded]"

def list_recent_emails(service, max_results=20):
    """List recent unread/important emails."""
    now = datetime.datetime.utcnow()
    
    # Query: recent messages (last 24 hours), prioritize unread
    query = "newer_than:1d"
    
    result = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=max_results
    ).execute()
    
    messages = result.get('messages', [])
    if not messages:
        return []
    
    email_list = []
    for msg in messages:
        meta = service.users().messages().get(
            userId='me', id=msg['id'], format='metadata',
            metadataHeaders=['From', 'To', 'Subject', 'Date']
        ).execute()
        
        headers = {h['name']: h['value'] for h in meta.get('payload', {}).get('headers', [])}
        
        is_unread = 'UNREAD' in meta.get('labelIds', [])
        
        email_list.append({
            'id': msg['id'],
            'from': headers.get('From', 'Unknown'),
            'to': headers.get('To', 'Unknown'),
            'subject': headers.get('Subject', '(No Subject)'),
            'date': headers.get('Date', 'Unknown'),
            'unread': is_unread,
            'labels': meta.get('labelIds', [])
        })
    
    return email_list

def main():
    print("=" * 60)
    print("📧 Evening Gmail Inbox Check")
    print(f"🕐 Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)
    
    # Refresh token
    creds = refresh_token()
    service = build('gmail', 'v1', credentials=creds)
    
    # Get profile info
    profile = service.users().getProfile(userId='me').execute()
    print(f"📫 Account: {profile.get('emailAddress', 'Unknown')}")
    print()
    
    # List recent emails
    emails = list_recent_emails(service, max_results=20)
    
    if not emails:
        print("📭 No emails found in the last 24 hours.")
        print()
        print("=" * 60)
        print("CONCLUSION: NO_REPLY — No recent emails found.")
        return
    
    # Categorize
    important = []
    from_nova = []
    promotional = []
    other = []
    
    for e in emails:
        subject = e['subject'].lower()
        from_addr = e['from'].lower()
        
        # Check if from Nova
        if 'yeyintoo12345678@gmail.com' in from_addr:
            from_nova.append(e)
            important.append(e)
            continue
        
        # Skip promotional/newsletter
        is_promo = False
        promo_keywords = ['unsubscribe', 'marketing', 'promotions', 'newsletter', 'sale', 'discount', 
                         'promo', 'spam', 'advertisement', 'you won', 'lottery', 'prize']
        for kw in promo_keywords:
            if kw in subject or kw in from_addr:
                is_promo = True
                break
        
        # Check for common promo senders
        promo_domains = ['marketing', 'newsletter', 'mailchimp', 'sendgrid', 'hubspot', 
                        'constantcontact', 'campaign', 'bulk', 'info@', 'noreply@', 'no-reply@']
        for d in promo_domains:
            if d in from_addr:
                is_promo = True
                break
        
        if is_promo:
            promotional.append(e)
        else:
            # Check for important keywords
            important_keywords = ['handover', 'wallet', 'personal-wallet-tele-bot', 'nova', 
                                 'reply', 'urgent', 'important', 'payment', 'transfer',
                                 'bot-2', 'bot 2', 'password', 'token', 'security']
            is_important = False
            for kw in important_keywords:
                if kw in subject:
                    is_important = True
                    break
            
            if is_important:
                important.append(e)
            else:
                other.append(e)
    
    # Print Nova emails first
    if from_nova:
        print("📩 ** EMAILS FROM NOVA (yeyintoo12345678@gmail.com) **")
        print("-" * 60)
        for e in from_nova:
            status = "🔴 UNREAD" if e['unread'] else "✅ Read"
            print(f"  From: {e['from']}")
            print(f"  Subject: {e['subject']}")
            print(f"  Date: {e['date']}")
            print(f"  Status: {status}")
            # Get body for Nova's emails
            body = get_email_body(service, e['id'])
            print(f"  Body preview: {body[:300]}")
            print()
    
    # Print other important emails
    non_nova_important = [e for e in important if e not in from_nova]
    if non_nova_important:
        print("📌 ** OTHER IMPORTANT EMAILS **")
        print("-" * 60)
        for e in non_nova_important:
            status = "🔴 UNREAD" if e['unread'] else "✅ Read"
            print(f"  From: {e['from']}")
            print(f"  Subject: {e['subject']}")
            print(f"  Status: {status}")
            print()
    
    # Print regular emails summary
    if other:
        print(f"📋 Regular emails ({len(other)}):")
        for e in other:
            status = "🆕" if e['unread'] else "📖"
            print(f"  {status} {e['from'][:40]} — {e['subject'][:60]}")
        print()
    
    # Print skipped promotional
    if promotional:
        print(f"📪 Skipped promotional/newsletter emails: {len(promotional)}")
        for e in promotional[:3]:
            print(f"   • {e['from'][:40]} — {e['subject'][:50]}")
        if len(promotional) > 3:
            print(f"   ... and {len(promotional)-3} more")
        print()
    
    # Conclusion
    print("=" * 60)
    print("📊 CONCLUSION:")
    print(f"   Total recent emails: {len(emails)}")
    print(f"   From Nova: {len(from_nova)}")
    print(f"   Important (other): {len(non_nova_important)}")
    print(f"   Regular: {len(other)}")
    print(f"   Promotional (skipped): {len(promotional)}")
    
    if from_nova:
        print("\n⚠️  Nova replied! Check details above.")
        for e in from_nova:
            body = get_email_body(service, e['id'])
            print(f"\n📝 Full body from Nova:")
            print(body[:500])
            print("..." if len(body) > 500 else "")
    elif important:
        print("\n📌 Important emails found (non-Nova).")
    else:
        print("\n✅ Nothing significant — no important or Nova emails found.")

if __name__ == '__main__':
    main()
