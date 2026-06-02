# /root/psvibe-sales-bot/customer_bot/booking.py
# Real implementations for My Bookings, Refer, Waitlist

import logging
import asyncio
from . import api as _api

logger = logging.getLogger(__name__)

async def cmd_mybookings(update, context):
    """Show user's current bookings from API"""
    uid = str(update.effective_user.id)
    try:
        data = await _api._api_get(f"bookings/search?telegram_chat_id={uid}", timeout=10)
        if isinstance(data, dict) and "bookings" in data:
            data = data["bookings"]
        if not isinstance(data, list):
            data = []
    except Exception:
        data = []

    if not data:
        await update.message.reply_text(
            "📋 *မရှိသေးပါ။*\n\n"
            "မှာထားတဲ့ booking မရှိသေးပါ။\n"
            "Booking လုပ်ရန် \"📅 Booking လုပ်မည်\" ကိုနှိပ်ပါ။",
            parse_mode="Markdown",
        )
        return

    lines = ["📋 *မင်္ဂလာပါ ချိန်းဆိုထားသော*"]
    for b in data[:10]:
        status = b.get("status", "unknown")
        emoji = {"confirmed": "✅", "pending": "⏳", "completed": "✔️", "cancelled": "❌"}.get(status, "❓")
        console = b.get("console_id", b.get("console", "?"))
        date = b.get("booking_date", b.get("date", "?"))
        time = b.get("booking_time", b.get("time_slot", "?"))
        lines.append(f"\n{emoji} #{b.get('id','?')} | {console} | {date} {time}")
    lines.append("\n\nAdmin ကို ဆက်သွယ်ရန်: @psvibeofficial")
    await update.message.reply_text("".join(lines), parse_mode="Markdown")


async def cmd_refer(update, context):
    """Generate referral link with user's Telegram info"""
    user = update.effective_user
    uname = f"@{user.username}" if user.username else user.full_name or user.first_name or "Friend"
    ref_link = f"https://t.me/psvibe_customer_bot?start=ref_{user.id}"

    msg = (
        "🎁 *Refer a Friend*\n\n"
        f"မင်္ဂလာပါ {uname}!\n\n"
        "သင်၏ referral link မှာ —\n"
        f"`{ref_link}`\n\n"
        "ဒီ link ကို သူငယ်ချင်းတွေကို Share လုပ်ပါ။\n"
        "*Coming soon:* Referral bonus system ကို မကြာမီ စတင်ပါမည်။"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_waitlist(update, context):
    """Show waitlist info — coming soon"""
    await update.message.reply_text(
        "🎮 *Waitlist*\n\n"
        "Waitlist တွင် ထည့်သွင်းရန် အဆင်သင့်ဖြစ်နေပါပြီ။\n\n"
        "သင်စောင့်ဆိုင်းလိုသော console (PS5, PS4, etc.)\n"
        "နှင့် အချိန်ကို ဖော်ပြပါ။\n\n"
        "*Coming soon:* 'Auto-notify' စနစ် — console ရှင်းသည်နှင့်\n"
        "Telegram မှ အလိုအလျောက် အကြောင်းကြားပါမည်။",
        parse_mode="Markdown",
    )
