#!/usr/bin/env python3
"""
PS VIBE — Daily EOD (End of Day) Report Script
==============================================
Runs at 20:00 MMT (13:30 UTC) daily via cron.
Queries MySQL for today's sales, member activity, and top packages.
Formats a Burmese-language summary and sends to Boss Telegram (6296803251).

Requires: requests, pymysql (or uses docker exec for MySQL)
Uses BOT_TOKEN (Sales Bot) for sendMessage.
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta, timezone

# ── Config ────────────────────────────────────────────────────────────────────
BOSS_CHAT_ID = "6296803251"
STAFF_CHAT_ID = "-1003686032747"  # Admin group
MMT = timezone(timedelta(hours=6, minutes=30))

# Load env vars
ENV_FILE = "/root/psvibe-sales-bot/.env"
SECRETS_FILE = "/etc/psvibe/secrets.env"

def _load_env_file(filepath):
    if not os.path.isfile(filepath):
        return
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:]
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val

_load_env_file(ENV_FILE)
_load_env_file(SECRETS_FILE)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ── MySQL Query via Docker ────────────────────────────────────────────────────
def sql(query):
    """Run MySQL query via docker exec on psvibe-mysql container."""
    cmd = [
        "docker", "exec", "psvibe-mysql",
        "mysql", "-upsvibe_user", "-pPsVibe@2026_Rotated!",
        "psvibe_api", "-N", "-B", "-e", query
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception as e:
        print(f"SQL ERROR: {e}", file=sys.stderr)
        return None


def sql_one(query):
    """Run a scalar query, return first value or None."""
    result = sql(query)
    if result:
        lines = result.strip().split("\n")
        return lines[0] if lines else None
    return None


def tg_send(chat_id, text, token=None, parse_mode="HTML"):
    """Send Telegram message via Bot API."""
    import requests
    token = token or BOT_TOKEN
    if not token or not chat_id:
        print("ERROR: Missing token or chat_id", file=sys.stderr)
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
            timeout=15,
        )
        ok = resp.status_code == 200
        if not ok:
            print(f"Telegram API error: {resp.status_code} {resp.text}", file=sys.stderr)
        return ok
    except Exception as e:
        print(f"Telegram send error: {e}", file=sys.stderr)
        return False


# ── Data Collection ───────────────────────────────────────────────────────────
now_mmt = datetime.now(MMT)
today_str = now_mmt.strftime("%Y-%m-%d")
date_display = now_mmt.strftime("%d %B %Y (%A)")

# 1. Total revenue from sales_daily today
total_sales_raw = sql_one(
    f"SELECT COALESCE(SUM(net), 0) FROM sales_daily WHERE sale_date = '{today_str}'"
)
total_sales = float(total_sales_raw) if total_sales_raw else 0

# 2. Gross sales (before discount)
gross_sales_raw = sql_one(
    f"SELECT COALESCE(SUM(gross), 0) FROM sales_daily WHERE sale_date = '{today_str}'"
)
gross_sales = float(gross_sales_raw) if gross_sales_raw else 0

# 3. Total discount given today
discount_raw = sql_one(
    f"SELECT COALESCE(SUM(discount), 0) FROM sales_daily WHERE sale_date = '{today_str}'"
)
discount_total = float(discount_raw) if discount_raw else 0

# 4. Number of sales transactions today
txn_count_raw = sql_one(
    f"SELECT COUNT(*) FROM sales_daily WHERE sale_date = '{today_str}'"
)
txn_count = int(txn_count_raw) if txn_count_raw else 0

# 5. Top-ups today
topup_amount_raw = sql_one(
    f"SELECT COALESCE(SUM(amount), 0) FROM topup_log WHERE DATE(topup_date) = '{today_str}'"
)
topup_amount = float(topup_amount_raw) if topup_amount_raw else 0

topup_count_raw = sql_one(
    f"SELECT COUNT(*) FROM topup_log WHERE DATE(topup_date) = '{today_str}'"
)
topup_count = int(topup_count_raw) if topup_count_raw else 0

# 6. Member check-ins (attendance log today)
checkins_raw = sql_one(
    f"SELECT COUNT(*) FROM attendance_log WHERE date = '{today_str}'"
)
checkins = int(checkins_raw) if checkins_raw else 0

# 7. Unique members served today
unique_members_raw = sql_one(
    f"SELECT COUNT(DISTINCT member_id) FROM sales_daily WHERE sale_date = '{today_str}' AND member_id IS NOT NULL AND member_id != ''"
)
unique_members = int(unique_members_raw) if unique_members_raw else 0

# 8. Active consoles right now
active_consoles_raw = sql_one(
    "SELECT COUNT(*) FROM console_status WHERE status IN ('Active','in_use','In Use')"
)
active_consoles = int(active_consoles_raw) if active_consoles_raw else 0

# 9. Total consoles
total_consoles_raw = sql_one("SELECT COUNT(*) FROM console_status")
total_consoles = int(total_consoles_raw) if total_consoles_raw else 0

# 10. Top 5 sales by console/game today
top_items_raw = sql(
    f"SELECT COALESCE(console_id,'Walk-in'), COALESCE(SUM(net),0) as rev, COUNT(*) as cnt "
    f"FROM sales_daily WHERE sale_date = '{today_str}' "
    f"GROUP BY console_id ORDER BY rev DESC LIMIT 5"
)

# 11. Payment method breakdown
payment_methods_raw = sql(
    f"SELECT payment_method, COALESCE(SUM(net),0), COUNT(*) "
    f"FROM sales_daily WHERE sale_date = '{today_str}' "
    f"GROUP BY payment_method ORDER BY SUM(net) DESC"
)

# 12. Total members
total_members_raw = sql_one("SELECT COUNT(*) FROM members")
total_members = int(total_members_raw) if total_members_raw else 0

# 13. New members today
new_members_raw = sql_one(
    f"SELECT COUNT(*) FROM members WHERE DATE(created_at) = '{today_str}'"
)
new_members = int(new_members_raw) if new_members_raw else 0

# ── Build Burmese Report ──────────────────────────────────────────────────────
# Burmese month names
mm_months = {
    1: "ဇန်နဝါရီ", 2: "ဖေဖော်ဝါရီ", 3: "မတ်", 4: "ဧပြီ",
    5: "မေ", 6: "ဇွန်", 7: "ဇူလိုင်", 8: "ဩဂုတ်",
    9: "စက်တင်ဘာ", 10: "အောက်တိုဘာ", 11: "နိုဝင်ဘာ", 12: "ဒီဇင်ဘာ"
}

mm_days = {
    0: "တနင်္လာ", 1: "အင်္ဂါ", 2: "ဗုဒ္ဓဟူး",
    3: "ကြာသပတေး", 4: "သောကြာ", 5: "စနေ", 6: "တနင်္ဂနွေ"
}

mm_date = f"{now_mmt.day} {mm_months[now_mmt.month]} {now_mmt.year} ({mm_days[now_mmt.weekday()]})"

def fmt_k(v):
    """Format number with commas, Myanmar style."""
    if v >= 100000:
        return f"{v/100000:.1f} သိန်း"
    return f"{v:,.0f}"

lines = []
lines.append("📊 <b>PS VIBE — ယနေ့ အရောင်းအစီရင်ခံစာ</b>")
lines.append(f"📅 {mm_date}")
lines.append("")
lines.append("━" * 22)
lines.append("")

# Revenue section
lines.append("💰 <b>အရောင်း</b>")
lines.append(f"  📝 အရောင်း အကြိမ်ရေ   : <b>{txn_count}</b> ကြိမ်")
lines.append(f"  💵 Gross (မလျှော့ခင်) : <b>{fmt_k(gross_sales)} Ks</b>")
if discount_total > 0:
    lines.append(f"  🎁 Discount          : <b>{fmt_k(discount_total)} Ks</b>")
lines.append(f"  💰 Net (စုစုပေါင်း)    : <b>{fmt_k(total_sales)} Ks</b>")
lines.append("")

# Top-up section
lines.append("💳 <b>Top Up</b>")
lines.append(f"  🔄 Top Up အကြိမ်ရေ  : <b>{topup_count}</b> ကြိမ်")
lines.append(f"  💵 Top Up ပမာဏ      : <b>{fmt_k(topup_amount)} Ks</b>")
lines.append("")

# Total
total_revenue = total_sales + topup_amount
lines.append(f"🏆 <b>စုစုပေါင်း ဝင်ငွေ : {fmt_k(total_revenue)} Ks</b>")
lines.append("")

# Member section
lines.append("👥 <b>Member</b>")
lines.append(f"  🆕 Member အသစ်      : <b>{new_members}</b> ယောက်")
lines.append(f"  🎮 ယနေ့ လာရောက်သူ  : <b>{unique_members}</b> ယောက်")
lines.append(f"  📋 Member စုစုပေါင်း : <b>{total_members:,}</b> ယောက်")
lines.append("")

# Console status
lines.append("🕹️ <b>Console အခြေအနေ</b>")
lines.append(f"  ✅ Active : <b>{active_consoles}</b> / {total_consoles}")
lines.append("")

# Staff attendance
lines.append(f"📅 <b>Staff တက်ရောက်မှု</b>")
lines.append(f"  👤 ယနေ့ တက်ရောက်   : <b>{checkins}</b> ယောက်")
lines.append("")

# Top consoles/games
if top_items_raw:
    lines.append("🏆 <b>Top 5 Consoles / Games</b>")
    for i, line in enumerate(top_items_raw.strip().split("\n")[:5], 1):
        parts = line.split("\t")
        if len(parts) >= 2:
            console = parts[0].strip() or "Walk-in"
            rev = float(parts[1]) if parts[1] else 0
            lines.append(f"  {i}. {console} — <b>{fmt_k(rev)} Ks</b>")
    lines.append("")

# Payment breakdown
if payment_methods_raw:
    lines.append("💳 <b>ငွေပေးချေမှု ပုံစံ</b>")
    for line in payment_methods_raw.strip().split("\n")[:5]:
        parts = line.split("\t")
        if len(parts) >= 2:
            method = parts[0].strip() or "Unknown"
            amt = float(parts[1]) if parts[1] else 0
            lines.append(f"  {method} : <b>{fmt_k(amt)} Ks</b>")
    lines.append("")

lines.append("━" * 22)
lines.append("🤖 <i>Kora — Auto Daily Report</i>")
lines.append(f"🕗 {now_mmt.strftime('%I:%M %p')} MMT")

message = "\n".join(lines)

# ── Send ──────────────────────────────────────────────────────────────────────
print("=" * 50)
print(message)
print("=" * 50)

if BOT_TOKEN:
    # Try staff/admin group first, fallback to Boss
    success = tg_send(STAFF_CHAT_ID, message)
    if success:
        print(f"✅ EOD report sent to Admin Group ({STAFF_CHAT_ID})")
    else:
        print(f"⚠️ Admin group send failed, trying Boss fallback...", file=sys.stderr)
        success = tg_send(BOSS_CHAT_ID, message)
        if success:
            print(f"✅ EOD report sent to Boss ({BOSS_CHAT_ID}) via fallback")
        else:
            print(f"❌ Failed to send EOD report to both targets", file=sys.stderr)
            sys.exit(1)
else:
    print("⚠️ BOT_TOKEN not set — message NOT sent (dry run)", file=sys.stderr)
    sys.exit(1)
