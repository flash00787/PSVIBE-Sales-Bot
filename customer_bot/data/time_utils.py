from datetime import datetime, timezone, timedelta

# Myanmar Time (UTC+6:30)
MMT = timezone(timedelta(hours=6, minutes=30))

def now_mmt():
    return datetime.now(MMT)

def today_str():
    return now_mmt().strftime('%Y-%m-%d')
