#!/usr/bin/env python3
"""Send email to You Ko Htet requesting CoCo setup data"""
import sys, os
sys.path.insert(0, "/root/.openclaw/workspace")
from send_email_api import send_email

subject = "CoCo (OpenClaw Agent) — Setup Data Request"

body = """မင်္ဂလာပါ ကိုယူကိုထက်၊

ကျွန်တော် Kora (Aung Chan Myint အစ်ကိုရဲ့ Personal Assistant) ပါ။

OC - CoCo (OpenClaw Agent) ကို သင့် local host ကနေ လှမ်းဆွဲပြီး setup လုပ်ဖို့အတွက် လိုအပ်တဲ့ data တွေကို မေးမြန်းလိုပါတယ်။ အောက်ပါ အချက်အလက်တွေကို ပေးပို့နိုင်ရင် ကောင်းပါတယ် —

၁။ **CoCo အတွက် Telegram Bot Token** (BotFather ကနေ ရယူထားတဲ့ token)
၂။ **CoCo ရဲ့ OpenClaw Config** (သင့် local မှာ လက်ရှိသုံးနေတဲ့ openclaw.json သို့မဟုတ် config file)
၃။ **API Keys / Access Tokens** — အောက်ပါတို့အနက်မှ ရှိရင်:
   - OpenRouter API Key (code review / fixer အတွက် Claude Sonnet)
   - Grok / xAI API Key (research အတွက်)
   - အခြား သုံးနေကျ API keys များ
၄။ **CoCo ရဲ့ Identity Info** — Owner name, Role, Preferred language, Tone of Voice
၅။ **Allowlist Telegram IDs** — CoCo ကို ဘယ်သူတွေ သုံးခွင့်ပြုမလဲ (Telegram User IDs)
၆။ **အခြား လိုအပ်တဲ့ Config Details** — Databases, SSH keys, Services တွေရှိရင်

ဒီ data တွေရရှိပြီးရင် CoCo ကို မြန်ဆန်စွာ setup လုပ်ပြီး စတင်အသုံးပြုလို့ရအောင် လုပ်ပေးပါမယ်။

ကျေးဇူးတင်ပါတယ်။

လေးစားစွာဖြင့်၊
Kora
(Aung Chan Myint ၏ Personal AI Assistant)"""

try:
    msg_id = send_email("rein020124@gmail.com", subject, body)
    print(f"SUCCESS: Email sent! Message ID: {msg_id}")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
