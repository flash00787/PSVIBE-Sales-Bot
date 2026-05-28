#!/usr/bin/env python3
"""Kora Email Sender using Gmail API + OAuth 2.0 (HTTPS port 443)"""
import json, urllib.request, urllib.parse, base64, os
from email.mime.text import MIMEText

WS = "/root/.openclaw/workspace"
SECRET_FILE = os.path.join(WS, "secret.json")
TOKEN_FILE = os.path.join(WS, "token.json")

with open(SECRET_FILE) as f:
    s = json.load(f)["installed"]
CID = s["client_id"]
CS = s["client_secret"]

def refresh_token():
    """Refresh the access token using saved refresh token"""
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

def send_email(to_addr, subject, body):
    """Send email via Gmail API"""
    token = refresh_token()
    msg = MIMEText(body, "plain", "utf-8")
    msg["To"] = to_addr
    msg["From"] = "chanmyint123456789@gmail.com"
    msg["Subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=json.dumps({"raw": raw}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        result = json.loads(r.read())
    return result.get("id")

if __name__ == "__main__":
    # Test: send Kora introduction
    subject = "Kora - Personal Digital Assistant Introduction"
    body = """မင်္ဂလာပါ ခင်ဗျာ၊

ကျွန်တော် Kora ပါ။ Aung Chan Myint အစ်ကိုရဲ့ ကိုယ်ပိုင် ဒစ်ဂျစ်တယ် လက်ထောက် (Personal Digital Assistant) ဖြစ်ပါတယ်။ OpenClaw နည်းပညာဖြင့် လည်ပတ်နေပြီး အစ်ကိုရဲ့ လုပ်ငန်းဆောင်တာများကို ထိရောက်မြန်ဆန်စွာ ကူညီပံ့ပိုးပေးနိုင်ရန် ဒီဇိုင်းထုတ်ထားပါသည်။

ကျွန်တော်ဟာ AI Agent တစ်ဦးဖြစ်ပြီး အောက်ပါတို့ကို လုပ်ဆောင်နိုင်ပါသည်:
• Google Sheets Automation, Database Management, Server Infrastructure (VPS/Docker)
• Telegram Bots, Script & Bot Development
• အချက်အလက်ခွဲခြမ်းစိတ်ဖြာခြင်းနှင့် အစီရင်ခံစာများ
• ဖိုင်စီမံခန့်ခွဲမှု၊ သတင်းအချက်အလက်ရှာဖွေခြင်း
• Coding & Debugging
• Linux Server & Cloud Infrastructure စီမံခန့်ခွဲခြင်း

ထူးခြားချက်များ: မြန်မာဘာသာစကားဖြင့် ကျွမ်းကျင်စွာ ဆက်သွယ်နိုင်ခြင်း၊ တိကျမှု၊ ပရော်ဖက်ရှင်နယ်ဆန်မှု။

Aung Chan Myint အစ်ကိုရဲ့ PS VIBE နှင့် Synergy Hub လုပ်ငန်းများတွင် ကူညီပေးသကဲ့သို့ အစ်မ Chan Su Su Hlaing အတွက်လည်း အကျိုးရှိစေမည့် အကူအညီများ ပေးနိုင်လိမ့်မည်ဟု မျှော်လင့်ပါသည်။

လေးစားစွာဖြင့်၊
Kora"""

    msg_id = send_email("chansusuhlaing@gmail.com", subject, body)
    print(f"SUCCESS: Email sent! Message ID: {msg_id}")
