#!/usr/bin/env python3
"""Read last week's emails from Gmail inbox and summarize"""
import json, urllib.request, urllib.parse, base64, os, datetime

WS = "/home/node/.openclaw/workspace"
SECRET_FILE = os.path.join(WS, "secret.json")
TOKEN_FILE = os.path.join(WS, "token.json")

with open(SECRET_FILE) as f:
    s = json.load(f)["installed"]
CID = s["client_id"]
CS = s["client_secret"]

def refresh_token():
    with open(TOKEN_FILE) as f:
        td = json.load(f)
    d = urllib.parse.urlencode({
        "client_id": CID,
        "client_secret": CS,
        "refresh_token": td["refresh_token"],
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=d)
    with urllib.request.urlopen(req, timeout=10) as r:
        nt = json.loads(r.read())
    td["access_token"] = nt["access_token"]
    with open(TOKEN_FILE, "w") as f:
        json.dump(td, f)
    return td["access_token"]

def decode_body(payload):
    """Recursively decode email body from payload"""
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
            elif 'parts' in part:
                return decode_body(part)
    elif 'body' in payload and 'data' in payload['body']:
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
    return '(no text body)'

def get_headers(headers):
    """Extract key headers"""
    result = {}
    for h in headers:
        name = h.get('name', '').lower()
        if name in ('from', 'to', 'subject', 'date'):
            result[name] = h.get('value', '')
    return result

def list_emails():
    token = refresh_token()
    
    # Calculate date 7 days ago in MYT (Asia/Yangon = UTC+6.5)
    now = datetime.datetime.utcnow()
    week_ago = now - datetime.timedelta(days=7)
    after_str = week_ago.strftime('%Y/%m/%d')
    query = urllib.parse.quote(f"after:{after_str} in:inbox")
    
    # List messages matching query
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?q={query}&maxResults=50"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    
    messages = data.get('messages', [])
    print(f"Found {len(messages)} emails in the past week")
    print("=" * 80)
    
    summaries = []
    
    for i, msg in enumerate(messages, 1):
        # Get full message
        url2 = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}?format=full"
        req2 = urllib.request.Request(url2, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req2, timeout=10) as r2:
                full = json.loads(r2.read())
        except Exception as e:
            print(f"[{i}] ERROR fetching: {e}")
            continue
        
        headers = get_headers(full.get('payload', {}).get('headers', []))
        body = decode_body(full.get('payload', {}))
        snippet = full.get('snippet', '')
        
        # Truncate body for summary
        body_short = body[:300].replace('\n', ' | ') if len(body) > 300 else body.replace('\n', ' | ')
        
        summary = {
            'from': headers.get('from', '?'),
            'subject': headers.get('subject', '(no subject)'),
            'date': headers.get('date', '?'),
            'snippet': snippet,
            'body_preview': body_short
        }
        summaries.append(summary)
        
        print(f"[{i}] {summary['date']}")
        print(f"    From: {summary['from']}")
        print(f"    Subj: {summary['subject']}")
        print(f"    Body: {body_short[:200]}")
        print()
    
    # Categorize
    print("=" * 80)
    print("SUMMARY BY CATEGORY:")
    print("=" * 80)
    
    important = []
    newsletters = []
    notifications = []
    others = []
    
    for s in summaries:
        subj_lower = s['subject'].lower()
        from_lower = s['from'].lower()
        
        # Detect important
        if any(kw in subj_lower for kw in ['nov', 'handover', 'wallet', 'password', 'urgent', 'important', 'invoice', 'payment', 'bill', 'receipt', 'contract', 'deadline']):
            important.append(s)
        elif any(site in from_lower for site in ['linkedin', 'facebook', 'twitter', 'github', 'youtube', 'medium', 'notion']):
            notifications.append(s)
        elif any(kw in subj_lower for kw in ['newsletter', 'digest', 'weekly', 'promo', 'sale', 'offer', 'discount', 'update']) or any(d in from_lower for d in ['newsletter', 'marketing', 'promo']):
            newsletters.append(s)
        else:
            others.append(s)
    
    if important:
        print(f"\n🔴 IMPORTANT ({len(important)}):")
        for s in important:
            print(f"  [{s['subject']}] - {s['from']}")
    if notifications:
        print(f"\n🟡 NOTIFICATIONS ({len(notifications)}):")
        for s in notifications:
            print(f"  [{s['subject']}] - {s['from']}")
    if newsletters:
        print(f"\n🟢 NEWSLETTERS ({len(newsletters)}):")
        for s in newsletters:
            print(f"  [{s['subject']}] - {s['from']}")
    if others:
        print(f"\n⚪ OTHERS ({len(others)}):")
        for s in others:
            print(f"  [{s['subject']}] - {s['from']}")
    
    print(f"\nTotal: {len(summaries)} emails in the past week")

if __name__ == "__main__":
    list_emails()
