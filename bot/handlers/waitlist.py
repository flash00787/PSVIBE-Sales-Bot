"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta
from bot import *




def _wl_console_availability(console_pref: str) -> dict:
    """
    Check live console availability for a given console_pref ("PS5", "PS5 Pro", "Any").
    Returns dict: { free: [cid,...], busy: [cid,...], total: int }
    """
    data = _replit_get("sheets/consoles")
    consoles = data.get("consoles", []) if data else []
    if console_pref == "Any":
        relevant = consoles
    else:
        relevant = [c for c in consoles if c.get("type", "").strip() == console_pref]
    free = [c["id"] for c in relevant if c.get("liveStatus", "").lower() == "free"]
    busy = [c["id"] for c in relevant if c.get("liveStatus", "").lower() != "free"]
    return {"free": free, "busy": busy, "total": len(relevant)}

def _fmt_mmt_dt(iso_str: str) -> str:
    """Convert ISO UTC timestamp string to MMT (UTC+6:30) formatted string."""
    if not iso_str:
        return "—"
    try:
        from datetime import datetime as _dt, timezone as _tz, timedelta as _td
        _MMT = _tz(_td(hours=6, minutes=30))
        dt = _dt.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(_MMT).strftime("%Y-%m-%d %H:%M")
    except Exception as e:
        logger.error("_fmt_mmt_dt: %s", e, exc_info=True)
        return iso_str[:16].replace("T", " ")

def _wl_status_label(status: str) -> str:
    """Human-readable status label with emoji."""
    return {
        "waiting":   "⏳ Waiting",
        "notified":  "🔔 Notified",
        "claimed":   "✅ Claimed",
        "cancelled": "❌ Cancelled",
        "expired":   "⌛ Expired",
    }.get(status, status)

def _wl_pref_label(pref: str) -> str:
    return {"PS5": "🎮 PS5", "PS5 Pro": "🎮 PS5 Pro", "Any": "🎮 Any"}.get(pref, pref)

async def cmd_waitlist_mgmt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: /waitlist command — show waitlist management menu."""
    await _show_wl_menu(update, context)
    return WL_MENU

async def _show_wl_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Render waitlist summary + menu keyboard."""
    import asyncio as _asyncio
    store = await _asyncio.to_thread(_replit_get, "waitlist")
    rows = store.get("rows", []) if store else []
    waiting   = [r for r in rows if r.get("status") == "waiting"]
    notified  = [r for r in rows if r.get("status") == "notified"]
    n_waiting  = len(waiting)
    n_notified = len(notified)
    summary = (
        f"⏳ *Waitlist Management*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 Waiting  : *{n_waiting}* ယောက်\n"
        f"🔔 Notified : *{n_notified}* ယောက် (Soft Reserve active)\n"
    )
    kb = [
        [BTN_WL_VIEW_WAITING, BTN_WL_VIEW_ALL],
        [BTN_WL_NOTIFY_NEXT,  BTN_WL_REFRESH],
        [BTN_BACK_MAIN],
    ]
    await update.message.reply_text(
        summary,
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )

async def step_wl_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.handlers.main_menu import show_main_menu
    """Handle waitlist menu button presses."""
    import asyncio as _asyncio
    choice = update.message.text.strip()

    if choice == BTN_BACK_MAIN:
        return await show_main_menu(update, context)

    if choice in (BTN_WL_REFRESH, BTN_WL_VIEW_WAITING):
        store = await _asyncio.to_thread(_replit_get, "waitlist?status=waiting")
        rows = store.get("rows", []) if store else []
        if not rows:
            await update.message.reply_text("✅ Waitlist ဗလာပါ — ဘယ်သူမှ မစောင့်ဆိုင်းပါ")
            return await _show_wl_menu(update, context)
        await update.message.reply_text(
            f"⏳ *Waiting List — {len(rows)} ယောက်*",
            parse_mode="Markdown",
        )
        for i, r in enumerate(rows, 1):
            joined = _fmt_mmt_dt(r.get("joined_at", ""))
            name = r.get("customer_name", "?")
            phone = r.get("phone") or "—"
            pref = _wl_pref_label(r.get("console_pref", "Any"))
            entry_id = r.get("id")
            card = (
                f"*#{i} — {name}*\n"
                f"📞 {phone}  |  {pref}\n"
                f"🕐 Joined: {joined} MMT\n"
                f"🆔 Entry ID: `{entry_id}`"
            )
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔔 Notify", callback_data=f"wl:notify:{entry_id}"),
                InlineKeyboardButton("🗑️ Remove", callback_data=f"wl:remove:{entry_id}"),
            ]])
            await update.message.reply_text(card, parse_mode="Markdown", reply_markup=kb)
        return WL_MENU

    if choice == BTN_WL_VIEW_ALL:
        store = await _asyncio.to_thread(_replit_get, "waitlist")
        rows = store.get("rows", []) if store else []
        if not rows:
            await update.message.reply_text("📂 Waitlist ဗလာပါ")
            return await _show_wl_menu(update, context)
        await update.message.reply_text(
            f"📂 *All Waitlist Entries — {len(rows)} ခု*",
            parse_mode="Markdown",
        )
        for i, r in enumerate(rows, 1):
            joined = _fmt_mmt_dt(r.get("joined_at", ""))
            status_label = _wl_status_label(r.get("status", ""))
            name = r.get("customer_name", "?")
            phone = r.get("phone") or "—"
            pref = _wl_pref_label(r.get("console_pref", "Any"))
            entry_id = r.get("id")
            card = (
                f"*#{i}* — {name}  |  {status_label}\n"
                f"📞 {phone}  |  {pref}\n"
                f"🕐 {joined} MMT  |  🆔 `{entry_id}`"
            )
            if r.get("status") == "waiting":
                kb = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔔 Notify", callback_data=f"wl:notify:{entry_id}"),
                    InlineKeyboardButton("🗑️ Remove", callback_data=f"wl:remove:{entry_id}"),
                ]])
                await update.message.reply_text(card, parse_mode="Markdown", reply_markup=kb)
            else:
                await update.message.reply_text(card, parse_mode="Markdown")
        return WL_MENU

    if choice == BTN_WL_NOTIFY_NEXT:
        # ── Pre-check: get next waiting entry's console_pref, then verify availability ──
        wl_store = await _asyncio.to_thread(_replit_get, "waitlist?status=waiting")
        waiting_rows = (wl_store.get("rows", []) if wl_store else [])
        if not waiting_rows:
            await update.message.reply_text("✅ Waitlist ဗလာပါ — Notify မလုပ်ရ")
            return await _show_wl_menu(update, context)
        next_entry = waiting_rows[0]
        next_pref = next_entry.get("console_pref", "Any")
        avail = await _asyncio.to_thread(_wl_console_availability, next_pref)
        if not avail["free"]:
            pref_label = next_pref if next_pref != "Any" else "Console"
            busy_list = ", ".join(avail["busy"][:4]) if avail["busy"] else "—"
            await update.message.reply_text(
                f"⛔ *Notify မလုပ်နိုင်ပါ*\n\n"
                f"🎮 {next_entry.get('customer_name','?')} ({next_pref}) အတွက်\n"
                f"🔒 {pref_label} console အားလုံး Busy ဖြစ်နေသည် ({busy_list})\n\n"
                f"Console တစ်ခု Free ဖြစ်မှသာ Notify လုပ်ပါ",
                parse_mode="Markdown",
            )
            return await _show_wl_menu(update, context)
        # Console free — proceed with notify
        resp = await _asyncio.to_thread(_replit_post, "waitlist/notify", {})
        if not resp:
            await update.message.reply_text("❌ Notify မအောင်မြင်ပါ — API error")
        elif not resp.get("notified"):
            await update.message.reply_text("✅ Waitlist ဗလာပါ — Notify မလုပ်ရ")
        else:
            entry = resp.get("entry", {})
            name = entry.get("customer_name", "?")
            phone = entry.get("phone") or "—"
            pref = entry.get("console_pref", "Any")
            free_list = ", ".join(avail["free"][:3])
            await update.message.reply_text(
                f"🔔 *Notified!*\n"
                f"👤 {name}\n"
                f"📞 {phone}\n"
                f"🎮 {pref}\n"
                f"✅ Free consoles: {free_list}\n"
                f"⏳ 15 min Soft Reserve window စတင်ပြီ",
                parse_mode="Markdown",
            )
        return await _show_wl_menu(update, context)

    return await _show_wl_menu(update, context)

async def cb_wl_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline button handler for 🔔 Notify / 🗑️ Remove on waitlist cards."""
    import asyncio as _asyncio
    query = update.callback_query
    await query.answer()
    try:
        _, action, entry_id_str = query.data.split(":", 2)
        entry_id = int(entry_id_str)
    except Exception as e:
        logger.error("cb_wl_action: %s", e, exc_info=True)
        return

    if action == "notify":
        entry_data = await _asyncio.to_thread(_replit_get, f"waitlist/{entry_id}")
        if not entry_data or entry_data.get("status") != "waiting":
            try:
                await query.edit_message_text("⚠️ Entry မတွေ့ပါ သို့မဟုတ် status ပြောင်းသွားပြီ")
            except Exception as e:
                logger.error("cb_wl_action: %s", e, exc_info=True)
                pass
            return
        # ── Pre-check: verify console availability for this entry's pref ──
        entry_pref = entry_data.get("console_pref", "Any")
        avail = await _asyncio.to_thread(_wl_console_availability, entry_pref)
        if not avail["free"]:
            busy_list = ", ".join(avail["busy"][:4]) if avail["busy"] else "—"
            try:
                await query.edit_message_text(
                    f"⛔ *Notify မလုပ်နိုင်ပါ*\n\n"
                    f"🎮 {entry_data.get('customer_name','?')} ({entry_pref}) အတွက်\n"
                    f"🔒 {entry_pref} console အားလုံး Busy ဖြစ်နေသည် ({busy_list})\n\n"
                    f"Console တစ်ခု Free ဖြစ်မှသာ Notify လုပ်ပါ",
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.error("cb_wl_action: %s", e, exc_info=True)
                pass
            return
        # Console free — proceed with notify
        resp = await _asyncio.to_thread(
            _replit_post, "waitlist/notify",
            {"console_id": entry_data.get("console_pref", "")}
        )
        if resp and resp.get("notified"):
            notified_entry = resp.get("entry", {})
            name = notified_entry.get("customer_name", "?")
            phone = notified_entry.get("phone") or "—"
            pref = notified_entry.get("console_pref", "Any")
            free_list = ", ".join(avail["free"][:3])
            try:
                await query.edit_message_text(
                    f"🔔 *Notified!*\n"
                    f"👤 {name}\n"
                    f"📞 {phone}\n"
                    f"🎮 {pref}\n"
                    f"✅ Free consoles: {free_list}\n"
                    f"⏳ 15 min Soft Reserve window စတင်ပြီ",
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.error("cb_wl_action: %s", e, exc_info=True)
                pass
        else:
            try:
                await query.edit_message_text("❌ Notify မအောင်မြင်ပါ")
            except Exception as e:
                logger.error("cb_wl_action: %s", e, exc_info=True)
                pass

    elif action == "remove":
        resp = await _asyncio.to_thread(_replit_delete, f"waitlist/{entry_id}")
        if resp and resp.get("ok"):
            try:
                await query.edit_message_text(f"🗑️ Entry #{entry_id} ကို Waitlist မှ ဖယ်ရှားပြီ")
            except Exception as e:
                logger.error("cb_wl_action: %s", e, exc_info=True)
                pass
        else:
            try:
                await query.edit_message_text("❌ Remove မအောင်မြင်ပါ")
            except Exception as e:
                logger.error("cb_wl_action: %s", e, exc_info=True)
                pass
