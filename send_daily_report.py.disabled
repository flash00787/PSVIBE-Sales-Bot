#!/usr/bin/env python3
"""
PS VIBE — Auto Daily Report Sender
====================================
Runs via cron at 10 PM MMT (3:30 PM UTC).
Generates today's sales report and sends to the staff Telegram chat.

Usage (cron):
    30 15 * * * cd /root/psvibe-sales-bot && python3 send_daily_report.py >> /tmp/daily_report_cron.log 2>&1
"""

import os
import sys
import json
import logging
import urllib.request
from datetime import datetime, timezone, timedelta

# ── Setup logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/root/psvibe-sales-bot/daily_report.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("daily_report")

# ── Add bot to path ──
sys.path.insert(0, "/root/psvibe-sales-bot")

# ── Config ──
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
STAFF_CHAT_ID = os.environ.get("STAFF_CHAT_ID", os.environ.get("STAFF_NOTIFY_CHAT", ""))
MMT = timezone(timedelta(hours=6, minutes=30))

if not BOT_TOKEN:
    logger.error("BOT_TOKEN not set — cannot send daily report")
    sys.exit(1)
if not STAFF_CHAT_ID:
    logger.warning("STAFF_CHAT_ID not set — report will not be sent to any chat")


def escape_md(text: str) -> str:
    """Escape MarkdownV2 special characters."""
    special = r"_*[]()~`>#+-=|{}.!"
    for ch in special:
        text = text.replace(ch, f"\\{ch}")
    return text


def send_telegram_message(chat_id: str, text: str, parse_mode: str = "Markdown") -> dict:
    """Send a message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.error("Telegram send failed: %s", e)
        return {"ok": False, "error": str(e)}


def main():
    today = datetime.now(MMT)
    today_str = f"{today.month}/{today.day}/{today.year}"
    logger.info("=== Generating daily report for %s ===", today_str)

    try:
        from bot.report_generator import get_report_generator
        gen = get_report_generator()
        report = gen.daily_report()
        text = gen.format_daily_report_brief(report)
    except Exception as e:
        logger.exception("Failed to generate report: %s", e)
        text = (
            f"📊 *PS VIBE Daily — {escape_md(today_str)}*\n"
            f"❌ Report generation failed: {escape_md(str(e))}"
        )

    logger.info("Report generated (%d chars), sending to chat: %s", len(text), STAFF_CHAT_ID)

    if STAFF_CHAT_ID:
        result = send_telegram_message(STAFF_CHAT_ID, text)
        if result.get("ok"):
            logger.info("✅ Daily report sent successfully!")
        else:
            logger.error("❌ Failed to send: %s", result.get("error", "unknown"))
    else:
        logger.info("No STAFF_CHAT_ID configured — printing to stdout:")
        print(text)


if __name__ == "__main__":
    main()
