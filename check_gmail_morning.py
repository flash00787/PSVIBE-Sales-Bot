#!/usr/bin/env python3
"""
Morning Gmail Check - Cron Job
Checks for unread/recent emails, especially from Nova about Personal-Wallet-Tele-Bot-2 handover.
"""
import os
import sys
import json
import base64
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Try multiple token paths
TOKEN_CANDIDATES = [
    '/root/.openclaw/workspace/token.json',
    '/home/node/.openclaw/workspace/token.json',
    os.path.expanduser('~/.openclaw/workspace/token.json'),
]
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_creds():
    """Load credentials from token."""
    for path in TOKEN_CANDIDATES:
        if os.path.exists(path):
            creds = Credentials.from_authorized_user_file(path, SCOPES)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(path, 'w') as f:
                    f.write(creds.to_json())
            return creds
    
    raise FileNotFoundError("No Gmail token found!")

def decode_msg_part(part):
    """Decode email body from a message part."""
    if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
    return None

def get_email_body(service, msg_id):
    """Get full email body text."""
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    
    payload = msg.get('payload', {})
    
    if payload.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
    
    parts = payload.get('parts', [])
    for part in parts:
        result = decode_msg_part(part)
        if result:
            return result
        if part.get('parts'):
            for subpart in part['parts']:
                result = decode_msg_part(subpart)
                if result:
                    return result
    
    return "[Body could not be decoded]"

def list_recent_emails(service, max_results=20):
    """List recent unread/important emails."""
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
    output = []
    output.append("=" * 60)
    output.append("📧 Morning Gmail Inbox Check")
    output.append(f"🕐 Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    output.append("=" * 60)
    
    try:
        creds = get_creds()
        service = build('gmail', 'v1', credentials=creds)
        
        profile = service.users().getProfile(userId='me').execute()
        output.append(f"📫 Account: {profile.get('emailAddress', 'Unknown')}")
        output.append("")
        
        emails = list_recent_emails(service, max_results=20)
        
        if not emails:
            output.append("📭 No emails found in the last 24 hours.")
            output.append("")
            output.append("=" * 60)
            output.append("CONCLUSION: NO_REPLY — No recent emails found.")
            print("\n".join(output))
            return "NO_REPLY"
        
        important = []
        from_nova = []
        promotional = []
        other = []
        
        for e in emails:
            subject = e['subject'].lower()
            from_addr = e['from'].lower()
            
            if 'yeyintoo12345678@gmail.com' in from_addr:
                from_nova.append(e)
                important.append(e)
                continue
            
            is_promo = False
            promo_keywords = ['unsubscribe', 'marketing', 'promotions', 'newsletter', 'sale', 'discount',
                             'promo', 'spam', 'advertisement', 'you won', 'lottery', 'prize']
            for kw in promo_keywords:
                if kw in subject or kw in from_addr:
                    is_promo = True
                    break
            
            promo_domains = ['marketing', 'newsletter', 'mailchimp', 'sendgrid', 'hubspot',
                            'constantcontact', 'campaign', 'bulk', 'info@', 'noreply@', 'no-reply@']
            for d in promo_domains:
                if d in from_addr:
                    is_promo = True
                    break
            
            if is_promo:
                promotional.append(e)
            else:
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
        
        nova_bodies = {}
        if from_nova:
            output.append("📩 ** EMAILS FROM NOVA (yeyintoo12345678@gmail.com) **")
            output.append("-" * 60)
            for e in from_nova:
                status = "🔴 UNREAD" if e['unread'] else "✅ Read"
                output.append(f"  From: {e['from']}")
                output.append(f"  Subject: {e['subject']}")
                output.append(f"  Date: {e['date']}")
                output.append(f"  Status: {status}")
                body = get_email_body(service, e['id'])
                nova_bodies[e['id']] = body
                output.append(f"  Body preview: {body[:400]}")
                output.append("")
        
        non_nova_important = [e for e in important if e not in from_nova]
        if non_nova_important:
            output.append("📌 ** OTHER IMPORTANT EMAILS **")
            output.append("-" * 60)
            for e in non_nova_important:
                status = "🔴 UNREAD" if e['unread'] else "✅ Read"
                output.append(f"  From: {e['from']}")
                output.append(f"  Subject: {e['subject']}")
                output.append(f"  Status: {status}")
                output.append("")
        
        if other:
            output.append(f"📋 Regular emails ({len(other)}):")
            for e in other:
                status = "🆕" if e['unread'] else "📖"
                output.append(f"  {status} {e['from'][:40]} — {e['subject'][:60]}")
            output.append("")
        
        if promotional:
            output.append(f"📪 Skipped promotional/newsletter emails: {len(promotional)}")
            for e in promotional[:3]:
                output.append(f"   • {e['from'][:40]} — {e['subject'][:50]}")
            if len(promotional) > 3:
                output.append(f"   ... and {len(promotional)-3} more")
            output.append("")
        
        output.append("=" * 60)
        output.append("📊 CONCLUSION:")
        output.append(f"   Total recent emails: {len(emails)}")
        output.append(f"   From Nova: {len(from_nova)}")
        output.append(f"   Important (other): {len(non_nova_important)}")
        output.append(f"   Regular: {len(other)}")
        output.append(f"   Promotional (skipped): {len(promotional)}")
        
        if from_nova:
            output.append("\n⚠️  NOVA REPLIED! ⚠️")
            for e in from_nova:
                body = nova_bodies.get(e['id'], get_email_body(service, e['id']))
                output.append(f"\n📝 Full body from Nova ({e['subject']}):")
                output.append(body[:800])
                if len(body) > 800:
                    output.append("...")
        elif non_nova_important:
            output.append("\n📌 Important emails found (non-Nova).")
        else:
            output.append("\n✅ Nothing significant.")
        
        print("\n".join(output))
        
        if from_nova:
            # Nova replied - construct notification
            nova_summary = []
            for e in from_nova:
                body = nova_bodies.get(e['id'], '')
                nova_summary.append(f"  📩 From: {e['from']}\n  📋 {e['subject']}\n  📝 {body[:500]}")
            return ("NOVA_REPLY", "\n\n".join(nova_summary))
        elif non_nova_important:
            return ("IMPORTANT", f"{len(non_nova_important)} other important email(s)")
        else:
            return ("NOTHING", None)
            
    except Exception as e:
        output.append(f"\n❌ ERROR: {e}")
        print("\n".join(output))
        return ("ERROR", str(e))

if __name__ == '__main__':
    result = main()
    # Output structured result for the shell to parse
    print(f"\n---RESULT:{json.dumps(result)}---")
