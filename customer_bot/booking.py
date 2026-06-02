# /root/psvibe-sales-bot/customer_bot/booking.py
# Real implementations for My Bookings, Refer, Waitlist

import logging
import asyncio
from . import api as _api

logger = logging.getLogger(__name__)

async def cmd_mybookings(update, context):
    """Show user's active/upcoming bookings with details"""
    # Guard against None user (shouldn't happen but defensive)
    if update is None or update.effective_user is None:
        logger.warning("cmd_mybookings: update or effective_user is None")
        if update and update.message:
            await update.message.reply_text(
                "မင်္ဂလာပါ... သင့်အနေဖြင့် Booking တင်ထားခြင်း မရှိသေးပါ။"
            )
        return

    uid = str(update.effective_user.id)

    # Friendly no-bookings message (in Burmese)
    NO_BOOKINGS_MSG = (
        "မင်္ဂလာပါ... သင့်အနေဖြင့် Booking တင်ထားခြင်း မရှိသေးပါ။"
    )

    try:
        data = await _api._api_get(f"bookings/search?telegram_chat_id={uid}", timeout=10)
        if isinstance(data, dict) and "bookings" in data:
            data = data["bookings"]
        if not isinstance(data, list):
            data = []
    except Exception as e:
        logger.warning("cmd_mybookings: API call failed: %s", e)
        # API failed — show friendly message instead of error
        await update.message.reply_text(NO_BOOKINGS_MSG)
        return

    # Filter: only show pending & confirmed (active/upcoming)
    active = [b for b in data if b.get("status") in ("pending", "confirmed")]

    if not active:
        await update.message.reply_text(NO_BOOKINGS_MSG)
        return

    lines = ["📋 *My Bookings (Active / Upcoming)*"]
    for b in active[:10]:
        bk_id = b.get("id", "?")
        status = b.get("status", "unknown")
        date = b.get("booking_date", b.get("date", "?"))
        time_str = b.get("booking_time", b.get("timeSlot", b.get("startTime", "?")))
        if "T" in str(time_str):
            time_str = str(time_str).split("T")[1][:5]
        console_type = b.get("console_id", b.get("consoleType", "?"))
        duration = b.get("duration_mins", b.get("durationMins", ""))
        game = b.get("game_name", b.get("gameName", ""))
        phone = b.get("phone", "")

        emoji = {"confirmed": "✅", "pending": "⏳"}.get(status, "❓")
        status_text = "Pending" if status == "pending" else "Confirmed"

        lines.append(
            f"\n{emoji} *Booking #{bk_id}* \u2014 {status_text}"
            f"\n📅 {date}  🕐 {time_str}"
            f"\n🎮 {console_type}  ⏱️ {duration} mins"
        )
        if game:
            lines.append(f"\n🕹️ {game}")
        if phone:
            lines.append(f"\n📞 {phone}")
        if status == "pending":
            lines.append(f"\n❌ Cancel: /cancelbooking_{bk_id}")
        lines.append("\n" + "\u2500" * 20)

    lines.append("\n\nAdmin ကို ဆက်သွယ်ရန်: @psvibeofficial")
    await update.message.reply_text("".join(lines), parse_mode="Markdown")

async def cmd_cancel_booking(update, context):
    """Cancel a booking by ID."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Cancel လုပ်ရန် Booking ID ထည့်ပါ။\n"
            "ဥပမာ: `/cancelbooking 131`\n\n"
            "pending booking များကိုသာ cancel လုပ်နိုင်ပါသည်။",
            parse_mode="Markdown",
        )
        return

    try:
        bk_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Booking ID မှားယွင်းနေပါသည်။")
        return

    try:
        result = await _api._api_patch(f"bookings/{bk_id}/status", {
            "status": "cancelled",
            "staff_note": "Cancelled by customer",
        })
        if result and isinstance(result, dict) and result.get("success"):
            await update.message.reply_text(
                f"✅ *Booking #{bk_id} ကို ပယ်ဖျက်လိုက်ပါပြီ။*",
                parse_mode="Markdown",
            )
        else:
            err = result.get("error", "") if isinstance(result, dict) else ""
            await update.message.reply_text(
                f"❌ Booking #{bk_id} ကို ပယ်ဖျက်မရပါ။ {err}",
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Cancel booking failed: %s", e)
        await update.message.reply_text("❌ Cancel မရပါ — ခဏနေ ပြန်ကြိုးစားပါ။")




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
