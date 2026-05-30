"""PS VIBE Bot - Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
import asyncio
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta
from bot import (
    CUSTOMER_BOT_TOKEN, _replit_get, fetch_balance_mins,
)





def _notify_customer(chat_id_or_phone: str, text: str):
    """Send Telegram message via customer bot token to notify customer."""
    if not CUSTOMER_BOT_TOKEN or not chat_id_or_phone:
        return
    try:
        import urllib.request as _req
        payload = json.dumps({
            "chat_id": chat_id_or_phone,
            "text": text,
            "parse_mode": "HTML",
        }).encode()
        r = _req.Request(
            f"https://api.telegram.org/bot{CUSTOMER_BOT_TOKEN}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        _req.urlopen(r, timeout=10)
    except Exception as e:
        logging.warning("customer notify failed: %s", e)

def get_customer_chat_id(member_id: str) -> str | None:
    """Look up most-recent Telegram chat_id for a member from bookings store."""
    try:
        bks = _replit_get(f"bookings?memberId={member_id}")
        if bks:
            for b in bks:
                cid = (b.get("telegramChatId") or b.get("telegram_chat_id") or "").strip()
                if cid:
                    return cid
    except Exception as e:
        logging.warning("get_customer_chat_id %s: %s", member_id, e)
    return None

async def _check_low_balance_alert(member_id: str, console_id: str) -> None:
    """Wait for Sheet formula to settle, then send low-balance alert to customer."""
    try:
        await asyncio.sleep(7)
        balance = await asyncio.to_thread(fetch_balance_mins, member_id)
        threshold = int(os.environ.get("LOW_BALANCE_THRESHOLD", "120"))
        if balance >= threshold:
            return
        chat_id = await asyncio.to_thread(get_customer_chat_id, member_id)
        if not chat_id:
            return
        msg = (
            f"⚠️ <b>PS VIBE — Balance နည်းလာပြီ!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💳 Member: <code>{member_id}</code>\n"
            f"🎮 လက်ကျန် Balance: <b>{balance} မိနစ်</b>\n"
            f"⏱️ PS5 ဆိုပါက {balance} မိနစ် ကစားနိုင်သေးသည်\n"
            f"\n"
            f"💰 ဆက်ကစားနိုင်ရန် Top-up လုပ်ပါ 👇\n"
            f"/topup"
        )
        await asyncio.to_thread(_notify_customer, chat_id, msg)
        logging.info("low_balance_alert sent: member=%s balance=%d", member_id, balance)
    except Exception as e:
        logging.warning("_check_low_balance_alert %s: %s", member_id, e)
