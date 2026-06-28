#!/usr/bin/env python3
"""
PS VIBE — Daily EOD (End of Day) Report Script
==============================================
Runs at 22:00 MMT (15:30 UTC) daily via cron.
Queries MySQL for today's sales, member activity, and top consoles.
Formats a Burmese-language summary and sends to Admin Group + Boss fallback.

Uses pymysql (direct) — NOT docker exec (auth issues).
Uses BOT_TOKEN (Sales Bot) for sendMessage.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# ── Setup logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] eod_report: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("eod_report")

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

# ── MySQL via pymysql ─────────────────────────────────────────────────────────
import pymysql
from pymysql.cursors import DictCursor

MYSQL_CFG = {
    "host": "127.0.0.1",
    "user": "psvibe_user",
    "password": "PsVibe@2026_Rotated!",
    "database": "psvibe_api",
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
}

def _get_conn():
    return pymysql.connect(**MYSQL_CFG)

def sql_one(query):
    """Run a scalar query, return first value or None."""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
            if row:
                return list(row.values())[0]
            return None
    except Exception as e:
        logger.error("SQL error: %s", e)
        return None
    finally:
        try:
            conn.close()
        except:
            pass

def sql(query):
    """Run a multi-row query, return list of dicts."""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()
    except Exception as e:
        logger.error("SQL error: %s", e)
        return []
    finally:
        try:
            conn.close()
        except:
            pass

def sql_table(query):
    """Run a query returning tab-separated lines (simulating mysql -N -B output)."""
    rows = sql(query)
    if not rows:
        return None
    lines = []
    for row in rows:
        lines.append("\t".join(str(v) if v is not None else "" for v in row.values()))
    return "\n".join(lines)


# ── Telegram Send ─────────────────────────────────────────────────────────────
def tg_send(chat_id, text, token=None, parse_mode="HTML"):
    """Send Telegram message via Bot API."""
    import urllib.request
    token = token or BOT_TOKEN
    if not token or not chat_id:
        logger.error("Missing token or chat_id")
        return False
    try:
        data = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": parse_mode}).encode()
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            ok = resp.status == 200
            if not ok:
                logger.error("Telegram API error: %s", resp.read().decode())
            return ok
    except Exception as e:
        logger.error("Telegram send error: %s", e)
        return False


# ── Data Collection ───────────────────────────────────────────────────────────
now_mmt = datetime.now(MMT)
today_str = now_mmt.strftime("%Y-%m-%d")

logger.info("=== Generating EOD report for %s (MMT) ===", today_str)

# 1. Sales today
total_sales_raw = sql_one(
    f"SELECT COALESCE(SUM(net), 0) FROM sales_daily WHERE sale_date = '{today_str}'"
)
total_sales = float(total_sales_raw or 0)

gross_sales_raw = sql_one(
    f"SELECT COALESCE(SUM(gross), 0) FROM sales_daily WHERE sale_date = '{today_str}'"
)
gross_sales = float(gross_sales_raw or 0)

discount_raw = sql_one(
    f"SELECT COALESCE(SUM(discount), 0) FROM sales_daily WHERE sale_date = '{today_str}'"
)
discount_total = float(discount_raw or 0)

txn_count_raw = sql_one(
    f"SELECT COUNT(*) FROM sales_daily WHERE sale_date = '{today_str}'"
)
txn_count = int(txn_count_raw or 0)

# 2. Top-ups today
topup_amount_raw = sql_one(
    f"SELECT COALESCE(SUM(amount), 0) FROM topup_log WHERE DATE(topup_date) = '{today_str}'"
)
topup_amount = float(topup_amount_raw or 0)

topup_count_raw = sql_one(
    f"SELECT COUNT(*) FROM topup_log WHERE DATE(topup_date) = '{today_str}'"
)
topup_count = int(topup_count_raw or 0)

# 3. Attendance today
checkins_raw = sql_one(
    f"SELECT COUNT(*) FROM attendance_log WHERE date = '{today_str}'"
)
checkins = int(checkins_raw or 0)

# 4. Unique members today
unique_members_raw = sql_one(
    f"SELECT COUNT(DISTINCT member_id) FROM sales_daily WHERE sale_date = '{today_str}' AND member_id IS NOT NULL AND member_id != ''"
)
unique_members = int(unique_members_raw or 0)

# 5. Console status
active_consoles_raw = sql_one(
    "SELECT COUNT(*) FROM console_status WHERE status IN ('Active','in_use','In Use')"
)
active_consoles = int(active_consoles_raw or 0)

total_consoles_raw = sql_one("SELECT COUNT(*) FROM console_status")
total_consoles = int(total_consoles_raw or 0)

# 6. Top 5 by console
top_items_raw = sql_table(
    f"SELECT COALESCE(console_id,'Walk-in'), COALESCE(SUM(net),0) as rev, COUNT(*) as cnt "
    f"FROM sales_daily WHERE sale_date = '{today_str}' "
    f"GROUP BY console_id ORDER BY rev DESC LIMIT 5"
)

# 7. Payment breakdown
payment_methods_raw = sql_table(
    f"SELECT SUBSTRING_INDEX(payment_method, ':', 1) as method, COALESCE(SUM(net),0), COUNT(*) "
    f"FROM sales_daily WHERE sale_date = '{today_str}' "
    f"GROUP BY SUBSTRING_INDEX(payment_method, ':', 1) ORDER BY SUM(net) DESC"
)

# 8. Total members (active)
total_members_raw = sql_one("SELECT COUNT(*) FROM member_wallets")
total_members = int(total_members_raw or 0)

# 9. New members today
new_members_raw = sql_one(
    f"SELECT COUNT(*) FROM member_wallets WHERE DATE(created_at) = '{today_str}'"
)
new_members = int(new_members_raw or 0)


# ── Build English Report ──────────────────────────────────────────────────────
eng_date = now_mmt.strftime("%d %B %Y (%A)")

def fmt_num(v):
    """Format number with commas."""
    if v >= 100000:
        return f"{v/100000:.1f}L"
    return f"{v:,.0f}"

def _f(v):
    """Parse value to float safely."""
    try:
        return float(v) if v else 0
    except:
        return 0

lines = []
lines.append("📊 <b>PS VIBE — Daily Sales Report</b>")
lines.append(f"📅 {eng_date}")
lines.append("")
lines.append("━" * 25)
lines.append("")

# Revenue
lines.append("💰 <b>Sales</b>")
lines.append(f"  📝 Transactions        : <b>{txn_count}</b>")
lines.append(f"  💵 Gross (before disc) : <b>{fmt_num(gross_sales)} Ks</b>")
if discount_total > 0:
    lines.append(f"  🎁 Discount             : <b>{fmt_num(discount_total)} Ks</b>")
lines.append(f"  💰 Net (Total)          : <b>{fmt_num(total_sales)} Ks</b>")
lines.append("")

# Top-up
lines.append("💳 <b>Top Up</b>")
lines.append(f"  🔄 Top Up Count         : <b>{topup_count}</b>")
lines.append(f"  💵 Top Up Amount        : <b>{fmt_num(topup_amount)} Ks</b>")
lines.append("")

# Total revenue
total_revenue = total_sales + topup_amount
lines.append(f"🏆 <b>Total Revenue : {fmt_num(total_revenue)} Ks</b>")
lines.append("")

# Members
lines.append("👥 <b>Members</b>")
lines.append(f"  🆕 New Members          : <b>{new_members}</b>")
lines.append(f"  🎮 Served Today         : <b>{unique_members}</b>")
lines.append(f"  📋 Total Members        : <b>{total_members:,}</b>")
lines.append("")

# Console status
lines.append("🕹️ <b>Console Status</b>")
lines.append(f"  ✅ Active : <b>{active_consoles}</b> / {total_consoles}")
lines.append("")

# Staff attendance
lines.append(f"📅 <b>Staff Attendance</b>")
lines.append(f"  👤 Present Today        : <b>{checkins}</b>")
lines.append("")

# Top Consoles/Games
if top_items_raw:
    lines.append("🏆 <b>Top 5 Consoles / Games</b>")
    for i, line in enumerate(top_items_raw.strip().split("\n")[:5], 1):
        parts = line.split("\t")
        if len(parts) >= 2:
            console = parts[0].strip() or "Walk-in"
            rev = _f(parts[1])
            lines.append(f"  {i}. {console} — <b>{fmt_num(rev)} Ks</b>")
    lines.append("")

# Payment breakdown
if payment_methods_raw:
    lines.append("💳 <b>Payment Methods</b>")
    for line in payment_methods_raw.strip().split("\n")[:5]:
        parts = line.split("\t")
        if len(parts) >= 2:
            method = parts[0].strip() or "Unknown"
            amt = _f(parts[1])
            lines.append(f"  {method} : <b>{fmt_num(amt)} Ks</b>")
    lines.append("")

lines.append("━" * 25)
lines.append("🤖 <i>Kora — Auto Daily Report</i>")
lines.append(f"🕙 {now_mmt.strftime('%I:%M %p')} MMT")

message = "\n".join(lines)

# ── Send ──────────────────────────────────────────────────────────────────────
print("=" * 50)
print(message)
print("=" * 50)

if BOT_TOKEN:
    success = tg_send(STAFF_CHAT_ID, message)
    if success:
        logger.info("✅ EOD report sent to Admin Group (%s)", STAFF_CHAT_ID)
    else:
        logger.warning("Admin group send failed, trying Boss fallback...")
        success = tg_send(BOSS_CHAT_ID, message)
        if success:
            logger.info("✅ EOD report sent to Boss (%s) via fallback", BOSS_CHAT_ID)
        else:
            logger.error("❌ Failed to send EOD report to both targets")
            sys.exit(1)
else:
    logger.error("BOT_TOKEN not set — message NOT sent")
    sys.exit(1)
