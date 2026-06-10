"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta

from bot import (
    BTN_BACK_MAIN, MAIN_MENU,   cmd_staff_kpi, today_str,
)

import asyncio




async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only: /broadcast <message> — sends a message to all known customer Telegram IDs.

    Access control: set ADMIN_USER_IDS env var to a comma-separated list of
    allowed Telegram user IDs.  If unset, any staff-bot user may broadcast.
    """
    uid = str(update.effective_user.id)
    if _BROADCAST_ADMIN_IDS and uid not in _BROADCAST_ADMIN_IDS:
        await update.message.reply_text("❌ Permission denied. Admin access only.")
        return

    parts = (update.message.text or "").split(None, 1)
    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text(
            "📢 <b>Broadcast Usage</b>\n\n"
            "/broadcast &lt;message text&gt;\n\n"
            "<i>Example:</i>\n"
            "/broadcast PS Vibe မှ မင်္ဂလာပါ! 🎮 Weekend special offer ရှိသည်!",
            parse_mode="HTML",
        )
        return

    msg_text = parts[1].strip()

    # Fetch target IDs from API (bookings.json source)
    data = await _psvibe_get_async("bookings/broadcast-targets") or {}
    if not data:
        await update.message.reply_text("❌ Broadcast target list ကို server မှ ရယူ၍ မရပါ။")
        return

    telegram_ids: list[str] = data.get("telegram_ids", [])
    if not telegram_ids:
        await update.message.reply_text(
            "⚠️ Registered customer Telegram ID များ မတွေ့ပါ။\n"
            "Customer bot မှတဆင့် booking ပြုလုပ်သော customers များ ရှိမှသာ broadcast ပြုလုပ်နိုင်သည်။"
        )
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
                text=f"📢 <b>PS Vibe</b>\n\n{msg_text}",
                parse_mode="HTML",
            )
            sent += 1
            await asyncio.sleep(0.05)   # ~20 msg/sec — within Telegram rate limits
        except Exception as e:
            logging.warning("Broadcast failed for %s: %s", tg_id, e)
            failed += 1

    await status_msg.edit_text(
        f"✅ <b>Broadcast complete</b>\n\n"
        f"📤 Sent    : <b>{sent}</b>\n"
        f"❌ Failed  : <b>{failed}</b>",
        parse_mode="HTML",
    )

async def cmd_staff_kpi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Staff KPI — today's per-staff breakdown from Sales_Daily + overall summary."""
    await update.message.reply_text("⏳ KPI data ရယူနေသည်...", reply_markup=ReplyKeyboardRemove())
    rd    = await _psvibe_get_async("sheets/report-data") or {}  # single batch call (was 2 calls)
    sales = rd.get("summary")     if rd else None
    stock = rd.get("stock_today") if rd else None
    date  = today_str()
    kb    = ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True)

    if not sales:
        await update.message.reply_text("❌ Sales data ရယူ၍ မရပါ။", reply_markup=kb)
        return MAIN_MENU

    cnt      = sales.get("today_count", 0)
    net      = sales.get("today_net", 0)
    kpay     = sales.get("today_kpay", 0)
    cash_    = sales.get("today_cash", 0)
    total_tx = sales.get("total_count", 0)
    avg_rev  = round(net / cnt) if cnt > 0 else 0

    food_qty        = sum(i["qty"] for i in stock.get("items", [])) if stock else 0
    food_item_count = len(stock.get("items", [])) if stock else 0

    # Per-staff breakdown — read Sales_Daily directly
    sb = await _psvibe_get_async("sheets/staff-breakdown") or {}  # API cache (was direct gspread call) -- TODO: Migrate to MySQL via API, direct gspread is fallback only
    staff_stats = sb.get("staff", {}) if sb else {}

    # Performance rating
    if cnt >= 10:
        perf, star = "Excellent", "⭐⭐⭐"
    elif cnt >= 5:
        perf, star = "Good", "⭐⭐"
    elif cnt >= 1:
        perf, star = "Fair", "⭐"
    else:
        perf, star = "No Sessions Yet", "—"

    lines = [
        f"📈 *Staff KPI — {date}*\n━━━━━━━━━━━━━━━━━━",
        f"🎮 Sessions : *{cnt}*    💰 Revenue : *{net:,} Ks*",
        f"📊 Avg/Session : *{avg_rev:,} Ks*",
        f"━━━━━━━━━━━━━━━━━━",
        f"💳 KPay : *{kpay:,} Ks*   |   💵 Cash : *{cash_:,} Ks*",
    ]

    if staff_stats:
        lines.append(f"━━━━━━━━━━━━━━━━━━")
        lines.append(f"👥 *Per-Staff Breakdown:*")
        for s, sd in staff_stats.items():
            s_avg  = round(sd["revenue"] / sd["sessions"]) if sd["sessions"] > 0 else 0
            s_hrs  = round(sd["mins"] / 60, 1)
            lines.append(
                f"\n  👤 *{s}*\n"
                f"     Sessions : *{sd['sessions']}*  |  Play : *{s_hrs} hrs*\n"
                f"     Revenue  : *{sd['revenue']:,} Ks*  (avg {s_avg:,} Ks)"
            )

    lines.extend([
        f"\n━━━━━━━━━━━━━━━━━━",
        f"🛒 Food Sold : *{food_qty} pcs* ({food_item_count} types)",
        f"━━━━━━━━━━━━━━━━━━",
        f"🏆 Performance : *{star} {perf}*",
        f"📋 All-Time Records : *{total_tx}*",
    ])
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=kb)
    return MAIN_MENU
