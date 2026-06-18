"""PS VIBE Customer Bot — Broadcast handler.
/admin_broadcast <message> — sends a message to all known customer Telegram IDs.
"""
import asyncio
import logging
import os

from telegram import Update
from telegram.ext import ContextTypes

from . import api as _api

logger = logging.getLogger(__name__)

# Admin IDs from env (comma-separated Telegram user IDs)
_ADMIN_IDS: set[str] = {
    s.strip() for s in os.environ.get("ADMIN_USER_IDS", "").split(",") if s.strip()
}


async def cmd_admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only broadcast to all customer bot users."""
    uid = str(update.effective_user.id)

    # Access control
    if _ADMIN_IDS and uid not in _ADMIN_IDS:
        await update.message.reply_text("❌ Admin access only.")
        return

    parts = (update.message.text or "").split(None, 1)
    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text(
            "📢 <b>Broadcast</b>\n\n"
            "/admin_broadcast &lt;message&gt;\n\n"
            "<i>Example:</i>\n"
            "/admin_broadcast PS VIBE မှ မင်္ဂလာပါ! 🎮",
            parse_mode="HTML",
        )
        return

    msg_text = parts[1].strip()

    # Fetch targets from API
    data = await _api._api_get("bookings/broadcast-targets") or {}
    if not data:
        await update.message.reply_text("❌ Broadcast target list မရပါ။")
        return

    telegram_ids = data.get("telegram_ids", [])
    if not telegram_ids:
        await update.message.reply_text("⚠️ Customer bot user မရှိသေးပါ။")
        return

    status_msg = await update.message.reply_text(
        f"📡 {len(telegram_ids)} ဦးထံ sending..."
    )

    sent = 0
    failed = 0
    for tg_id in telegram_ids:
        try:
            await context.bot.send_message(
                chat_id=int(tg_id),
                text=f"📢 <b>PS VIBE</b>\n\n{msg_text}",
                parse_mode="HTML",
            )
            sent += 1
            await asyncio.sleep(0.05)  # ~20 msg/sec — within rate limits
        except Exception as e:
            logger.warning("Broadcast failed for %s: %s", tg_id, e)
            failed += 1

    await status_msg.edit_text(
        f"✅ <b>Broadcast complete</b>\n\n"
        f"📤 Sent: <b>{sent}</b>\n"
        f"❌ Failed: <b>{failed}</b>",
        parse_mode="HTML",
    )
