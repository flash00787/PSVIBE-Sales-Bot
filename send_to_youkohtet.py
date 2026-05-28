#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Send coordination email to You Ko Htet"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace')
from send_email_api import send_email

subject = "PS VIBE Bot — Deploy Coordination"

body = """မင်္ဂလာပါ ကိုယူကိုထက်၊

အခုလက်ရှိ PS VIBE Bot အတွက် Fix-26 (Healthcheck Endpoint) နဲ့ Fix-29 (Customer Bot Fetch Optimization) တွေကို Kora က VPS ပေါ်မှာ deploy လုပ်ဖို့ ပြင်ဆင်နေပါတယ်။

ကိုယူကိုထက်က VPS ပေါ်တင်တာနဲ့ ပတ်သက်ပြီး မသိတာရှိရင် CoCo နဲ့ နှစ်ယောက်တိုင်ပင်ပြီး လုပ်ကြဖို့ Boss (ကိုအောင်ချမ်းမြင့်) က မှာထားပါတယ်။ လိုအပ်တာရှိရင်လည်း Kora က ကူညီပေးဖို့ အဆင်သင့်ရှိပါတယ်။

VPS ပေါ်ကနေ pull လုပ်ပေးမှာဖြစ်ကြောင်းကိုလည်း အသိပေးအပ်ပါတယ်။

ကောင်းမွန်စွာ ပူးပေါင်းဆောင်ရွက်နိုင်ပါစေလို့ ဆုတောင်းပါတယ်။

— Kora (Aung Chan Myint's Personal Assistant) 🤖
"""

msg_id = send_email("rein020124@gmail.com", subject, body)
print(f"SUCCESS: {msg_id}")
