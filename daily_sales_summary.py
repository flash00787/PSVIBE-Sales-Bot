#!/usr/bin/env python3
"""Daily Sales Summary — uses docker exec for MySQL queries"""
import subprocess, json

def sql(query):
    """Run MySQL query via docker exec"""
    cmd = [
        "docker", "exec", "psvibe-mysql",
        "mysql", "-upsvibe_user", "-pPsVibe@User2024!", "psvibe_api", "-N", "-B",
        "-e", query
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"

# Get data
total_sales_raw = sql("SELECT COALESCE(SUM(amount),0) FROM sales_daily WHERE DATE(created_at)=CURDATE()-INTERVAL 1 DAY")
total_sales = float(total_sales_raw) if total_sales_raw and total_sales_raw != "ERROR" else 0

total_topups_raw = sql("SELECT COALESCE(SUM(amount),0) FROM topup_log WHERE DATE(created_at)=CURDATE()-INTERVAL 1 DAY AND status='completed'")
total_topups = float(total_topups_raw) if total_topups_raw and "ERROR" not in total_topups_raw else 0

member_raw = sql("SELECT COUNT(*) FROM members WHERE status != 'deleted'")
member_count = int(member_raw) if member_raw and member_raw.isdigit() else 0

active_raw = sql("SELECT COUNT(*) FROM console_status WHERE status='occupied'")
active = int(active_raw) if active_raw and active_raw.isdigit() else 0

# Get yesterday date
from datetime import datetime, timedelta, timezone
MMT = timezone(timedelta(hours=6, minutes=30))
yesterday = (datetime.now(MMT) - timedelta(days=1)).strftime("%Y-%m-%d")

# Format message
msg = f"📊 PS VIBE Daily Summary — {yesterday}\n"
msg += "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
msg += f"💰 Sales: {total_sales:,.0f} Ks\n"
msg += f"💳 Topups: {total_topups:,.0f} Ks\n"
msg += f"👥 Members: {member_count:,}\n"
msg += f"🎮 Active Now: {active}\n"
msg += f"📈 Total Revenue: {total_sales+total_topups:,.0f} Ks\n"

# Top games
top_raw = sql("SELECT COALESCE(g.name,'Direct') as n, COALESCE(SUM(sf.amount),0) as r FROM sales_daily sf LEFT JOIN games g ON sf.game_id=g.id WHERE DATE(sf.created_at)=CURDATE()-INTERVAL 1 DAY GROUP BY g.name ORDER BY r DESC LIMIT 3")
if top_raw:
    lines = top_raw.strip().split("\n")
    if lines and lines[0]:
        msg += "\n🏆 Top Games:\n"
        for i, line in enumerate(lines[:3], 1):
            parts = line.split("\t")
            if len(parts) >= 2:
                msg += f"  {i}. {parts[0]} — {float(parts[1]):,.0f} Ks\n"

msg += "\n🤖 Kora — Daily Auto-Report"

# Save
with open("/tmp/kora_daily_sales.txt", "w") as f:
    f.write(msg)
print(msg)
print("\n✅ Ready for Telegram")
