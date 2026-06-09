import re

with open("/root/Aung Chan Myint/Sales-Tele-Bot/api_server/api_server.js", "r") as f:
    js = f.read()

# 1. Daily summary - add wave, cb, aya
js = js.replace(
    "let todayCount=0,todayNet=0,todayKpay=0,todayCash=0;",
    "let todayCount=0,todayNet=0,todayKpay=0,todayCash=0,todayWave=0,todayCb=0,todayAya=0;"
)
js = js.replace(
    "todayKpay+=parseNum(r[9]);todayCash+=parseNum(r[10]);",
    "todayKpay+=parseNum(r[9]);todayCash+=parseNum(r[10]);todayWave+=parseNum(r[15]||'0');todayCb+=parseNum(r[16]||'0');todayAya+=parseNum(r[17]||'0');"
)
js = js.replace(
    "return{today_count:todayCount,today_net:todayNet,today_kpay:todayKpay,today_cash:todayCash,total_count:rows.length-1};",
    "return{today_count:todayCount,today_net:todayNet,today_kpay:todayKpay,today_cash:todayCash,today_wave:todayWave,today_cb:todayCb,today_aya:todayAya,total_count:rows.length-1};"
)

# 2. Monthly report - add wave, cb, aya for sales
js = js.replace(
    "let guestGameRev=0,foodRev=0,discountTotal=0,salesKpay=0,salesCash=0,walletDeductMins=0;",
    "let guestGameRev=0,foodRev=0,discountTotal=0,salesKpay=0,salesCash=0,salesWave=0,salesCb=0,salesAya=0,walletDeductMins=0;"
)
js = js.replace(
    "foodRev+=parseNum(r[6]??'0');discountTotal+=parseNum(r[7]??'0');salesKpay+=parseNum(r[9]??'0');salesCash+=parseNum(r[10]??'0');",
    "foodRev+=parseNum(r[6]??'0');discountTotal+=parseNum(r[7]??'0');salesKpay+=parseNum(r[9]??'0');salesCash+=parseNum(r[10]??'0');salesWave+=parseNum(r[15]??'0');salesCb+=parseNum(r[16]??'0');salesAya+=parseNum(r[17]??'0');"
)

# 3. Monthly report - add wave, cb, aya for topups
js = js.replace(
    "let topupAmount=0,topupKpay=0,topupCash=0,topupMins=0;",
    "let topupAmount=0,topupKpay=0,topupCash=0,topupWave=0,topupCb=0,topupAya=0,topupMins=0;"
)
js = js.replace(
    "topupKpay+=parseNum(r[5]??'0');topupCash+=parseNum(r[6]??'0');topupMins+=parseNum(r[7]??'0');",
    "topupKpay+=parseNum(r[5]??'0');topupCash+=parseNum(r[6]??'0');topupWave+=parseNum(r[10]??'0');topupCb+=parseNum(r[11]??'0');topupAya+=parseNum(r[12]??'0');topupMins+=parseNum(r[7]??'0');"
)

with open("/root/Aung Chan Myint/Sales-Tele-Bot/api_server/api_server.js", "w") as f:
    f.write(js)
print("API_SERVER_ANALYTICS_DONE")
