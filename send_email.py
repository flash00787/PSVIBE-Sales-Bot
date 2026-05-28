import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sender = "chanmyint123456789@gmail.com"
receiver = "chansusuhlaing@gmail.com"
app_password = "knpe qhkh wbvh mwey".replace(" ", "")

subject = "Kora - သင်၏ ကိုယ်ပိုင် ဒစ်ဂျစ်တယ် လက်ထောက် အသေးစိတ် မိတ်ဆက်"

body = """မင်္ဂလာပါ ခင်ဗျာ၊

ကျွန်တော် Kora ပါ။ Aung Chan Myint အစ်ကိုရဲ့ ကိုယ်ပိုင် ဒစ်ဂျစ်တယ် လက်ထောက် (Personal Digital Assistant) တစ်ယောက်ဖြစ်ပါတယ်။ OpenClaw နည်းပညာဖြင့် လည်ပတ်နေပြီး အစ်ကိုရဲ့ လုပ်ငန်းဆောင်တာတွေကို ထိရောက်မြန်ဆန်စွာ ကူညီပံ့ပိုးပေးနိုင်ဖို့ ဒီဇိုင်းထုတ်ထားတာပါ။

ကျွန်တော် ဘယ်သူလဲ?
ကျွန်တော်ဟာ OpenClaw ပေါ်မှာ လည်ပတ်နေတဲ့ AI Agent တစ်ဦးဖြစ်ပြီး နည်းပညာပိုင်းဆိုင်ရာ ကျွမ်းကျင်မှု၊ ပရော်ဖက်ရှင်နယ် ဆက်ဆံရေးနဲ့ ထိရောက်တဲ့ လုပ်ဆောင်နိုင်စွမ်းတွေနဲ့ ပြည့်စုံပါတယ်။

ဘာတွေ လုပ်ဆောင်နိုင်သလဲ?
ကျွန်တော့်ရဲ့ အဓိက လုပ်ဆောင်နိုင်စွမ်းတွေကတော့:

• နည်းပညာပိုင်းဆိုင်ရာ ကူညီပံ့ပိုးမှု: Google Sheets Automation (dynamic arrays, complex QUERY), Database Management, Server Infrastructure (VPS, Docker), Telegram Bots တည်ဆောက်ခြင်းနဲ့ စီမံခန့်ခွဲခြင်း

• အလိုအလျောက်စနစ်များ: လုပ်ငန်းဆောင်တာတွေကို အလိုအလျောက်လုပ်ဆောင်နိုင်ဖို့ Script တွေ၊ Bot တွေ ရေးဆွဲရာမှာ ကူညီပေးနိုင်ပါတယ်

• စီမံခန့်ခွဲမှုနှင့် အချက်အလက်ခွဲခြမ်းစိတ်ဖြာခြင်း: အချက်အလက်တွေ စုဆောင်းတာ၊ စီမံခန့်ခွဲတာ၊ ခွဲခြမ်းစိတ်ဖြာတာနဲ့ အစီရင်ခံစာတွေ ပြင်ဆင်တာတွေကို လုပ်ဆောင်နိုင်ပါတယ်

• အထွေထွေ လက်ထောက်လုပ်ငန်းများ: ဖိုင်တွေ စီမံခွဲတာ၊ အချက်အလက်တွေ ရှာဖွေတာ၊ သတိပေးချက်တွေ ပေးပို့တာနဲ့ အခြားသော ရုံးလုပ်ငန်းဆိုင်ရာ ကူညီမှုတွေ

• Coding နှင့် Debugging: Programming မေးခွန်းတွေ၊ Code ရေးသားတာ၊ Error ရှာဖွေတာ စတဲ့ လုပ်ငန်းတွေမှာ အထူးကူညီနိုင်ပါတယ်

ကျွန်တော့်ရဲ့ ထူးခြားချက်များ:
• မြန်မာဘာသာစကားဖြင့် ကျွမ်းကျင်စွာ ဆက်သွယ်နိုင်မှု — လိုအပ်ပါက အင်္ဂလိပ် နည်းပညာဆိုင်ရာ ဝေါဟာရများကိုလည်း ရောနှောအသုံးပြုနိုင်ပါတယ်
• တိကျမှုနှင့် ထိရောက်မှု — အလုပ်တိုင်းကို တိကျသေချာစွာနဲ့ အချိန်ကုန်သက်သာအောင် လုပ်ဆောင်ပေးနိုင်ပါတယ်
• ပရော်ဖက်ရှင်နယ် ပုံစံ — လုပ်ငန်းခွင်အတွက် သင့်လျော်တဲ့ ပရော်ဖက်ရှင်နယ် ဆက်ဆံရေး ပုံစံကို အမြဲထိန်းသိမ်းထားပါတယ်

Aung Chan Myint အစ်ကိုရဲ့ PS VIBE နဲ့ Synergy Hub လုပ်ငန်းတွေမှာ ကူညီပေးနေသလိုပဲ၊ အစ်မ Chan Su Su Hlaing အတွက်လည်း အကျိုးရှိစေမယ့် အကူအညီတွေ ပေးနိုင်လိမ့်မယ်လို့ မျှော်လင့်ပါတယ်။

အကယ်၍ ကျွန်တော်နဲ့ ပတ်သက်ပြီး ထပ်မံသိရှိလိုသည်များရှိပါက မေးမြန်းနိုင်ပါတယ်ခင်ဗျာ။

လေးစားစွာဖြင့်၊

Kora
Aung Chan Myint ၏ ကိုယ်ပိုင် ဒစ်ဂျစ်တယ် လက်ထောက်"""

msg = MIMEMultipart()
msg["From"] = sender
msg["To"] = receiver
msg["Subject"] = subject
msg.attach(MIMEText(body, "plain", "utf-8"))

try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(sender, app_password)
    server.sendmail(sender, receiver, msg.as_string())
    server.quit()
    print("SUCCESS: Email sent to chansusuhlaing@gmail.com")
except Exception as e:
    print(f"FAILED: {e}")
