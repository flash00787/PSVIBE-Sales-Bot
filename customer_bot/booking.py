# /root/psvibe-sales-bot/customer_bot/booking.py
# Real implementations for My Bookings, Refer, Waitlist
#
# FIXED (2026-06-03):
#   - Time-based filtering: past bookings are excluded from active list
#   - Expired bookings shown with ❌ icon instead of ✅/⏳

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from . import api as _api

logger = logging.getLogger(__name__)

# MMT timezone (UTC+6:30)
MMT = timezone(timedelta(hours=6, minutes=30))

# 15-min grace period before a booking is considered expired
NO_SHOW_GRACE_MINUTES = 15


def _parse_booking_datetime_mmt(booking: dict):
    """Parse booking date + time into an MMT-aware datetime.
    Returns None if parsing fails."""
    bk_date = booking.get("date") or booking.get("booking_date") or ""
    time_slot = booking.get("timeSlot") or booking.get("startTime") or ""

    if not bk_date or not time_slot:
        return None

    # Clean date: handle datetime/date objects as well as strings
    if hasattr(bk_date, "strftime"):
        bk_date_clean = bk_date.strftime("%Y-%m-%d")
    else:
        bk_date_str = str(bk_date)
        bk_date_clean = bk_date_str.split(" ")[0]

    # Clean time (extract HH:MM)
    time_str = str(time_slot)
    if "T" in time_str:
        time_str = time_str.split("T")[1][:5]
    if " " in time_str:
        parts = time_str.split(" ")
        time_str = parts[1][:5] if len(parts) > 1 and ":" in parts[1] else parts[0][:5]

    try:
        h, m = map(int, time_str.split(":"))
        naive = datetime.strptime(bk_date_clean, "%Y-%m-%d").replace(hour=h, minute=m)
        return naive.replace(tzinfo=MMT)
    except (ValueError, AttributeError):
        return None


def _is_booking_expired(booking: dict) -> bool:
    """Check if a booking's time has passed (with grace period)."""
    bk_dt = _parse_booking_datetime_mmt(booking)
    if bk_dt is None:
        return False  # Can't determine — assume not expired

    now_mmt = datetime.now(MMT)
    grace_cutoff = bk_dt + timedelta(minutes=NO_SHOW_GRACE_MINUTES)
    return now_mmt > grace_cutoff


async def cmd_mybookings(update, context):
    """Show user's active/upcoming bookings with details.
    Past bookings (expired) are shown separately with ❌ icon."""
    if update is None or update.effective_user is None:
        logger.warning("cmd_mybookings: update or effective_user is None")
        if update and update.message:
            await update.message.reply_text(
                "မင်္ဂလာပါ... သင့်အနေဖြင့် Booking တင်ထားခြင်း မရှိသေးပါ။"
            )
        return

    uid = str(update.effective_user.id)

    NO_BOOKINGS_MSG = (
        "မင်္ဂလာပါ... သင့်အနေဖြင့် Booking တင်ထားခြင်း မရှိသေးပါ။"
    )

    try:
        raw_data = await _api._api_get(f"search-bookings?telegram_chat_id={uid}", timeout=10)
        if isinstance(raw_data, dict) and "bookings" in raw_data:
            data = raw_data["bookings"]
        elif isinstance(raw_data, list):
            data = raw_data
        else:
            logger.warning("cmd_mybookings: unexpected response format: %s", type(raw_data))
            data = []
        if not isinstance(data, list):
            data = []
    except Exception as e:
        logger.warning("cmd_mybookings: API call failed: %s", e)
        await update.message.reply_text(NO_BOOKINGS_MSG)
        return

    # Filter by status first — include 'active' status as well (staff-scheduled sessions show as Active)
    valid_statuses = ("pending", "confirmed", "scheduled", "active")
    all_active = [b for b in data if str(b.get("status", "")).lower() in valid_statuses]

    if not all_active:
        await update.message.reply_text(NO_BOOKINGS_MSG)
        return

    # Split into upcoming and expired
    upcoming = []
    expired = []
    for b in all_active:
        if _is_booking_expired(b):
            expired.append(b)
        else:
            upcoming.append(b)

    # If nothing at all
    if not upcoming and not expired:
        await update.message.reply_text(NO_BOOKINGS_MSG)
        return

    lines = []

    # ── Upcoming bookings ──
    if upcoming:
        lines.append("📋 My Bookings (Upcoming)")
        for b in upcoming[:10]:
            lines.append(_format_booking_line(b))
    else:
        lines.append("📋 My Bookings")
        lines.append("\n- No upcoming bookings.")

    # ── Expired bookings ──
    if expired:
        lines.append("\n\n⚠️ Expired Bookings")
        lines.append("(အချိန်ကျော်သွားပါပြီ — auto-cancel ခံရနိုင်ပါသည်)")
        for b in expired[:5]:
            lines.append(_format_booking_line(b, is_expired=True))

    lines.append("\n\nAdmin ကို ဆက်သွယ်ရန်: https://t.me/psvibeofficial")
    await update.message.reply_text("".join(lines), )


def _format_booking_line(b: dict, is_expired: bool = False) -> str:
    """Format a single booking into a display line."""
    bk_id = b.get("id", "?")
    status = str(b.get("status", "")).lower()
    date = b.get("booking_date") or b.get("date") or "?"
    time_str = b.get("booking_time") or b.get("timeSlot") or b.get("startTime") or "?"
    if "T" in str(time_str):
        time_str = str(time_str).split("T")[1][:5]
    # For pending bookings, console_id stores the type (e.g. "PS5", "PS5 Pro")
    # For confirmed bookings, console_id is the specific console (e.g. "C - 01")
    # Use console_id first; if empty, fall back to "PS5"
    raw_console = b.get("console_id") or b.get("consoleType") or ""
    if not str(raw_console).strip():
        raw_console = "PS5"
    console_type = str(raw_console)
    duration = b.get("duration_mins") or b.get("durationMins") or ""
    game = b.get("game_name") or b.get("gameName") or ""
    phone = b.get("phone") or ""

    if is_expired:
        emoji = "❌"
        status_text = "Expired"
    else:
        emoji = {"confirmed": "✅", "pending": "⏳", "scheduled": "📌"}.get(status, "❓")
        status_text = "Pending" if status == "pending" else ("Scheduled" if status == "scheduled" else "Confirmed")

    parts = [
        f"\n{emoji} Booking #{bk_id} \u2014 {status_text}",
        f"\n📅 {date}  🕐 {time_str}",
        f"\n🎮 {console_type}  ⏱️ {duration} mins",
    ]
    if game:
        parts.append(f"\n🕹️ {game}")
    if phone:
        parts.append(f"\n📞 {phone}")
    if status == "pending" and not is_expired:
        parts.append(f"\n❌ Cancel: /cancelbooking {bk_id}")
    parts.append("\n" + "\u2500" * 20)
    return "".join(parts)


async def cmd_cancel_booking(update, context):
    """Cancel a booking by ID."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Cancel လုပ်ရန် Booking ID ထည့်ပါ။\n"
            "ဥပမာ: `/cancelbooking 131`\n\n"
            "pending booking များကိုသာ cancel လုပ်နိုင်ပါသည်။"
        )
        return

    try:
        bk_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Booking ID မှားယွင်းနေပါသည်။")
        return

    try:
        # Fetch booking data first for admin notification
        try:
            booking = await _api._api_get(f"bookings/{bk_id}")
            if isinstance(booking, dict) and "booking" in booking:
                booking = booking["booking"]
        except Exception:
            booking = {}
        _bk_date = (booking.get("date") or booking.get("booking_date") or "?") if isinstance(booking, dict) else "?"
        _bk_time = (booking.get("timeSlot") or booking.get("startTime") or "?") if isinstance(booking, dict) else "?"
        _bk_console = (booking.get("consoleType") or booking.get("console_id") or "?") if isinstance(booking, dict) else "?"
        _bk_game = (booking.get("gameName") or booking.get("game_name") or "") if isinstance(booking, dict) else ""
        _bk_phone = (booking.get("phone") or booking.get("customerPhone") or "") if isinstance(booking, dict) else ""
        _bk_cust = (booking.get("customerName") or "") if isinstance(booking, dict) else ""

        result = await _api._api_patch(f"bookings/{bk_id}/status", {
            "status": "cancelled",
            "staff_note": "Cancelled by customer",
        })
        if result and isinstance(result, dict) and (result.get("success") or result.get("status") == "cancelled"):
            await update.message.reply_text(
                f"✅ *Booking #{bk_id} ကို ပယ်ဖျက်လိုက်ပါပြီ။*",
                parse_mode="Markdown",
            )
            # Notify admin group (deduped: skip if same booking notified <30s ago)
            staff_chat = _api.STAFF_NOTIFY_CHAT
            if staff_chat:
                import time as _time
                if not hasattr(_api, '_cancel_notify_sent'):
                    _api._cancel_notify_sent = {}
                _sent_key = f"cancel_{bk_id}"
                _now = _time.time()
                if _now - _api._cancel_notify_sent.get(_sent_key, 0) > 30:
                    _api._cancel_notify_sent[_sent_key] = _now
                    cust_name = _bk_cust or update.effective_user.full_name or "Customer"
                    username = f" @{update.effective_user.username}" if update.effective_user.username else ""
                    try:
                        await _api._tg_send({
                            "chat_id": staff_chat,
                            "text": (
                                f"🚫 <b>Booking #{bk_id} — Customer Cancelled</b>\n"
                                f"👤 {cust_name}{username}  📞 {_bk_phone or '—'}\n"
                                f"📅 {_bk_date}  ⏰ {_bk_time}\n"
                                f"🎮 {_bk_console}" +
                                (f"  🕹 {_bk_game}" if _bk_game else "") +
                                f"\n📝 Customer မှ /cancelbooking ဖြင့် ပယ်ဖျက်သည်"
                            ),
                            "parse_mode": "HTML",
                        })
                    except Exception:
                        pass
        else:
            err = (result or {}).get("error", "") if isinstance(result, dict) else ""
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
    ref_link = f"https://t.me/psvibe_customer_service_bot?start=ref_{user.id}"

    msg = (
        "🎁 *Refer a Friend*\n\n"
        f"မင်္ဂလာပါ {uname}!\n\n"
        "သင်၏ referral link မှာ —\n"
        f"`{ref_link}`\n\n"
        "ဒီ link ကို သူငယ်ချင်းတွေကို Share လုပ်ပါ။\n"
        "*Coming soon:* Referral bonus system ကို မကြာမီ စတင်ပါမည်။"
    )
    await update.message.reply_text(msg, )


async def cmd_waitlist(update, context):
    """Show waitlist info — coming soon"""
    await update.message.reply_text(
        "🎮 *Waitlist*\n\n"
        "Waitlist တွင် ထည့်သွင်းရန် အဆင်သင့်ဖြစ်နေပါပြီ။\n\n"
        "သင်စောင့်ဆိုင်းလိုသော console (PS5, PS4, etc.)\n"
        "နှင့် အချိန်ကို ဖော်ပြပါ။\n\n"
        "*Coming soon:* 'Auto-notify' စနစ် — console ရှင်းသည်နှင့်\n"
        "Telegram မှ အလိုအလျောက် အကြောင်းကြားပါမည်။"
    )
