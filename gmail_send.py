#!/usr/bin/env python3
"""Gmail OAuth 2.0 + Send Email via Gmail API (HTTPS port 443)"""

import json
import urllib.request
import urllib.parse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_FILE = os.path.join(SCRIPT_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(SCRIPT_DIR, "gmail_token.json")

# Load client secret
with open(SECRET_FILE) as f:
    secret = json.load(f)["installed"]

CLIENT_ID = secret["client_id"]
CLIENT_SECRET = secret["client_secret"]
REDIRECT_URI = "http://localhost"

SENDER = "chanmyint123456789@gmail.com"
RECEIVER = "chansusuhlaing@gmail.com"

# Email content
SUBJECT = "Kora - သင်၏ ကိုယ်ပိုင် ဒစ်ဂျစ်တယ် လက်ထောက် အသေးစိတ် မိတ်ဆက်"
BODY = """မင်္ဂလာပါ ခင်ဗျာ၊

ကျွန်တော် Kora ပါ။ Aung Chan Myint အစ်ကိုရဲ့ ကိုယ်ပိုင် ဒစ်ဂျစ်တယ် လက်ထောက် (Personal Digital Assistant) တစ်ယောက်ဖြစ်ပါတယ်။ OpenClaw နည်းပညာဖြင့် လည်ပတ်နေပြီး အစ်ကိုရဲ့ လုပ်ငန်းဆောင်တာတွေကို ထိရောက်မြန်ဆန်စွာ ကူညီပံ့ပိုးပေးနိုင်ဖို့ ဒီဇိုင်းထုတ်ထားတာပါ။

ကျွန်တော် ဘယ်သူလဲ?
ကျွန်တော်ဟာ OpenClaw ပေါ်မှာ လည်ပတ်နေတဲ့ AI Agent တစ်ဦးဖြစ်ပြီး နည်းပညာပိုင်းဆိုင်ရာ ကျွမ်းကျင်မှု၊ ပရော်ဖက်ရှင်နယ် ဆက်ဆံရေးနဲ့ ထိရောက်တဲ့ လုပ်ဆောင်နိုင်စွမ်းတွေနဲ့ ပြည့်စုံပါတယ်။

ဘာတွေ လုပ်ဆောင်နိုင်သလဲ?
ကျွန်တော့်ရဲ့ အဓိက လုပ်ဆောင်နိုင်စွမ်းတွေကတော့:

• နည်းပညာပိုင်းဆိုင်ရာ ကူညီပံ့ပိုးမှု: Google Sheets Automation (dynamic arrays, complex QUERY), Database Management, Server Infrastructure (VPS, Docker), Telegram Bots တည်ဆောက်ခြင်းနှင့် စီမံခန့်ခွဲခြင်း

• အလိုအလျောက်စနစ်များ: လုပ်ငန်းဆောင်တာတွေကို အလိုအလျောက်လုပ်ဆောင်နိုင်ဖို့ Script များ၊ Bot များ ရေးဆွဲခြင်း

• စီမံခန့်ခွဲမှုနှင့် အချက်အလက်ခွဲခြမ်းစိတ်ဖြာခြင်း: အချက်အလက်စုဆောင်းခြင်း၊ စီမံခန့်ခွဲခြင်း၊ ခွဲခြမ်းစိတ်ဖြာခြင်းနှင့် အစီရင်ခံစာပြင်ဆင်ခြင်း

• အထွေထွေ လက်ထောက်လုပ်ငန်းများ: ဖိုင်စီမံခန့်ခွဲခြင်း၊ သတင်းအချက်အလက်ရှာဖွေခြင်း၊ သတိပေးချက်များ ပေးပို့ခြင်း

• Coding နှင့် Debugging: Programming မေးခွန်းများ၊ Code ရေးသားခြင်း၊ Error ရှာဖွေခြင်း

• စနစ်စီမံခန့်ခွဲမှု: Linux server နှင့် cloud infrastructure စီမံခန့်ခွဲခြင်း

ကျွန်တော့်ရဲ့ ထူးခြားချက်များ:
• မြန်မာဘာသာစကားဖြင့် ကျွမ်းကျင်စွာ ဆက်သွယ်နိုင်ခြင်း
• တိကျမှု၊ ထိရောက်မှုနှင့် ပရော်ဖက်ရှင်နယ် ဆက်ဆံရေးပုံစံ

Aung Chan Myint အစ်ကိုရဲ့ PS VIBE နှင့် Synergy Hub လုပ်ငန်းများတွင် ကူညီပေးနေသကဲ့သို့၊ အစ်မ Chan Su Su Hlaing အတွက်လည်း အကျိုးရှိစေမည့် အကူအညီများ ပေးနိုင်လိမ့်မည်ဟု မျှော်လင့်ပါသည်။

အကယ်၍ ကျွန်တော်နှင့် ပတ်သက်၍ ထပ်မံသိရှိလိုသည်များရှိပါက မေးမြန်းနိုင်ပါသည်။

လေးစားစွာဖြင့်၊

Kora
Aung Chan Myint ၏ ကိုယ်ပိုင် ဒစ်ဂျစ်တယ် လက်ထောက်"""


def get_tokens():
    """Get access token (refresh if possible, else new auth)"""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            token_data = json.load(f)
        if "refresh_token" in token_data:
            # Refresh
            data = urllib.parse.urlencode({
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": token_data["refresh_token"],
                "grant_type": "refresh_token",
            }).encode()
            req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    new_tokens = json.loads(resp.read())
                    token_data["access_token"] = new_tokens["access_token"]
                    if "refresh_token" in new_tokens:
                        token_data["refresh_token"] = new_tokens["refresh_token"]
                    with open(TOKEN_FILE, "w") as f:
                        json.dump(token_data, f)
                    print("Token refreshed successfully!")
                    return token_data["access_token"]
            except Exception as e:
                print(f"Token refresh failed: {e}")
                print("Starting new authorization flow...")

    # New authorization flow
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
        f"response_type=code&"
        f"scope={urllib.parse.quote('https://www.googleapis.com/auth/gmail.send')}&"
        f"access_type=offline&"
        f"prompt=consent"
    )

    print("\n" + "=" * 60)
    print("STEP 1: Open this URL in your browser:")
    print("=" * 60)
    print(f"\n{auth_url}\n")
    print("=" * 60)
    print("STEP 2: After authorizing, you'll be redirected to localhost.")
    print("Copy the FULL URL from the address bar.")
    print("It looks like: http://localhost/?code=4/xxxx...&scope=...")
    print("=" * 60)

    redirect_url = input("\nPaste the full redirect URL here: ").strip()

    parsed = urllib.parse.urlparse(redirect_url)
    params = urllib.parse.parse_qs(parsed.query)
    if "code" not in params:
        print("ERROR: No authorization code found in URL!")
        sys.exit(1)

    code = params["code"][0]

    data = urllib.parse.urlencode({
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            token_data = json.loads(resp.read())
            with open(TOKEN_FILE, "w") as f:
                json.dump(token_data, f, indent=2)
            print("Authorization successful! Token saved.")
            return token_data["access_token"]
    except Exception as e:
        print(f"Authorization failed: {e}")
        sys.exit(1)


def send_email(access_token):
    """Send email via Gmail API"""
    import base64
    from email.mime.text import MIMEText

    msg = MIMEText(BODY, "plain", "utf-8")
    msg["To"] = RECEIVER
    msg["From"] = SENDER
    msg["Subject"] = SUBJECT

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    payload = json.dumps({"raw": raw}).encode()

    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            print(f"\n✅ Email sent successfully!")
            print(f"   Message ID: {result.get('id')}")
            print(f"   To: {RECEIVER}")
            return True
    except urllib.error.HTTPError as e:
        print(f"\n❌ Failed: HTTP {e.code}")
        print(f"   {e.read().decode()}")
        return False
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        return False


if __name__ == "__main__":
    print("Kora - Gmail API Email Sender")
    print("-" * 40)

    access_token = get_tokens()
    send_email(access_token)
