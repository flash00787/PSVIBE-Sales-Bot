from bot import (
    BTN_BACK_MAIN, CONSOLE_MENU, CUSTOMER_BOT_TOKEN, MAIN_MENU, MMT,
    N8N_BOOKING_WEBHOOK, N8N_SESSION_WEBHOOK, STAFF_NOTIFY_CHAT,
    _api_base, _replit_get, _replit_get_async, _replit_patch, _replit_patch_async, get_booking_sh, now_mmt,
    today_str,
)

"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
from telegram.ext import ContextTypes, ConversationHandler, ApplicationHandlerStop
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
import asyncio
import time
from bot.handlers.notify import _notify_customer

# Module-level state
_pending_cancel_note: Dict[int, dict] = {}
_REMIND_TASKS: dict[str, "asyncio.Task[None]"] = {}
_SESSION_END_TIMES: dict[str, str] = {}





def _extend_timer_kb(cid: str, member_id: str, chat_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard attached to reminder messages for extending the session."""
    tag = f"{cid}|{member_id}|{chat_id}"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ +30 min", callback_data=f"ext:30:{tag}"),
            InlineKeyboardButton("➕ +60 min", callback_data=f"ext:60:{tag}"),
            InlineKeyboardButton("➕ +90 min", callback_data=f"ext:90:{tag}"),
        ],
        [InlineKeyboardButton("✏️ Custom (မိနစ် ကိုယ်တိုင်ထည့်)", callback_data=f"ext:custom:{tag}")],
        [InlineKeyboardButton("✅ ပြီးပြီ (End မည်)", callback_data=f"ext:0:{tag}")],
    ])

def _remind_key(cid: str, chat_id: int) -> str:
    return f"{cid}|{chat_id}"

def _cancel_remind(cid: str, chat_id: int) -> None:
    key  = _remind_key(cid, chat_id)
    task = _REMIND_TASKS.pop(key, None)
    if task and not task.done():
        task.cancel()

async def _is_session_active(cid: str) -> bool:
    """Quick sync check: is this console Active today? (via MySQL API)."""
    try:
        # Use fetch_console_status endpoint - _replit_get_async returns list of dicts
        bk_data = await _replit_get_async("fetch_console_status")
        if isinstance(bk_data, list):
            for row in bk_data:
                if isinstance(row, dict) and row.get("console_id", "").strip() == cid and row.get("status", "").strip() == "Active":
                    return True
        elif isinstance(bk_data, dict):
            consoles = bk_data.get("consoles", bk_data.get("data", []))
            if isinstance(consoles, list):
                for row in consoles:
                    if isinstance(row, dict) and row.get("console_id", "").strip() == cid and row.get("status", "").strip() == "Active":
                        return True
            elif isinstance(consoles, dict):
                for row in consoles.get("consoles", []):
                    if isinstance(row, dict) and row.get("console_id", "").strip() == cid and row.get("status", "").strip() == "Active":
                        return True
    except Exception as e:
        logger.error("_is_session_active: %s", e, exc_info=True)
        return True
    return False

async def _remind_loop(
    bot, chat_id: int, cid: str, member_id: str,
    planned_mins: int, end_t: str, initial_delay: int,
):
    """Fires reminder at initial_delay, then every 5 mins while session is still Active.

    IMPORTANT: The FIRST fire always sends (no active-check) so that edge cases
    like an interrupted session-end flow (status briefly "Ended") still deliver
    the inline-keyboard Extend/Done prompt.  Subsequent fires check the sheet.
    """
    key = _remind_key(cid, chat_id)
    _REMIND_TASKS[key] = asyncio.current_task()   # type: ignore[assignment]
    _SESSION_END_TIMES[key] = end_t               # track current planned end time
    try:
        await asyncio.sleep(initial_delay)
        fire_count = 0
        while True:
            # Always check if session is still active before firing any reminder
            still_active = await _is_session_active(cid)
            if not still_active:
                break
            fire_count += 1
            try:
                # fire_count == 1 → "5 min ကျန်တော့သည်" (initial_delay fires 5 min before end)
                # fire_count == 2 → session end time reached (0 min overdue)
                # fire_count >= 3 → overdue by (fire_count - 2) * 5 mins
                if fire_count == 1:
                    _warn_line = "⚠️ <b>Session ဆုံးချိန် 5 မိနစ် ကျန်တော့သည်!</b>"
                elif fire_count == 2:
                    _warn_line = "🔔 <b>Session ဆုံးချိန်ရောက်ပြီ!</b>"
                else:
                    _overdue_mins = (fire_count - 2) * 5
                    _warn_line = f"🚨 <b>Session ကျော်လွန်နေပြီ! ({_overdue_mins} မိနစ် ကျော်ပြီ)</b>"
                # Always read current end time from _SESSION_END_TIMES (updated on extend)
                _current_end_t = _SESSION_END_TIMES.get(key, end_t)
                _remind_text = (
                    f"⏰ <b>Session Reminder!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🕹️ Console : <b>{cid}</b>\n"
                    f"👤 Member  : <b>{member_id}</b>\n"
                    f"⏱️ Planned : <b>{planned_mins} mins</b>\n"
                    f"🕑 End ~   : <b>{_current_end_t}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"{_warn_line}\n"
                    f"ဆက်ကစားမည်ဆိုက ➕ Extend ကိုနှိပ်ပါ\n"
                    f"ပြီးပြီဆိုက ✅ ပြီးပြီ ကိုနှိပ်ပြီး ⏹️ Session ဆုံး နှိပ်ပါ"
                )
                # Send ONLY to group chat with inline buttons
                # (single destination prevents dual-chat end/extend conflict)
                _target_chat = int(STAFF_NOTIFY_CHAT) if STAFF_NOTIFY_CHAT else chat_id
                _remind_kb = _extend_timer_kb(cid, member_id, _target_chat)
                await bot.send_message(
                    chat_id=_target_chat,
                    text=_remind_text,
                    parse_mode="HTML",
                    reply_markup=_remind_kb,
                )
            except Exception as e:
                logger.error("_remind_loop: %s", e, exc_info=True)
                pass
            # ── customer session warning (if member has a known chat_id) ───
            if member_id not in ("Guest", "0 (Guest)", ""):
                try:
                    cust_chat = await asyncio.to_thread(get_customer_chat_id, member_id)
                    if cust_chat:
                        if fire_count == 1:
                            _cust_warn = "⏱️ <b>5 မိနစ် ကျန်တော့သည်</b>"
                        elif fire_count == 2:
                            _cust_warn = "🔔 <b>Session ဆုံးချိန်ရောက်ပြီ!</b>"
                        else:
                            _cust_warn = f"🚨 <b>Session {(fire_count - 2) * 5} မိနစ် ကျော်ပြီ!</b>"
                        cust_msg = (
                            f"⏰ <b>PS VIBE — Session သတိပေးချက်!</b>\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"🕹️ Console: <b>{cid}</b>\n"
                            f"{_cust_warn}\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"ဆက်ကစားလိုပါက Staff ကို ပြောပြပါ"
                        )
                        await asyncio.to_thread(_notify_customer, cust_chat, cust_msg)
                except Exception as e:
                    logger.error("_remind_loop: %s", e, exc_info=True)
                    pass
            # ── next reminder in 5 mins ────────────────────────────────────
            await asyncio.sleep(5 * 60)
    except asyncio.CancelledError:
        pass
    finally:
        # Only remove from dict if this task is still the registered one
        # (prevents race condition where a newer task was already registered)
        if _REMIND_TASKS.get(key) is asyncio.current_task():
            _REMIND_TASKS.pop(key, None)
            _SESSION_END_TIMES.pop(key, None)

async def _send_session_reminder(
    bot, chat_id: int, cid: str, member_id: str,
    planned_mins: int, end_t: str, delay_secs: int,
):
    """Legacy single-fire wrapper — kept for n8n fallback path.
    Real repeat logic lives in _remind_loop."""
    await asyncio.sleep(delay_secs)
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"⏰ <b>Session Reminder!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🕹️ Console : <b>{cid}</b>\n"
                f"👤 Member  : <b>{member_id}</b>\n"
                f"⏱️ Planned : <b>{planned_mins} mins</b>\n"
                f"🕑 End ~   : <b>{end_t}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ <b>Session ဆုံးချိန်ရောက်ပြီ!</b>\n"
                f"ဆက်ကစားမည်ဆိုက ➕ Extend ကိုနှိပ်ပါ\n"
                f"ပြီးပြီဆိုက ✅ ပြီးပြီ ကိုနှိပ်ပြီး ⏹️ Session ဆုံး နှိပ်ပါ"
            ),
            parse_mode="HTML",
            reply_markup=_extend_timer_kb(cid, member_id, chat_id),
        )
    except Exception as e:
        logger.error("_send_session_reminder: %s", e, exc_info=True)
        pass

async def _post_n8n_session_reminder(
    chat_id: int, cid: str, member_id: str,
    planned_mins: int, end_t: str, delay_secs: int,
) -> bool:
    """POST session reminder payload to n8n webhook (restart-proof timer).
    Uses stdlib urllib so no extra package needed on VPS."""
    if not N8N_SESSION_WEBHOOK:
        return False
    import json as _json
    import urllib.request as _req
    remind_at_dt  = now_mmt() + timedelta(seconds=delay_secs)
    remind_at_iso = remind_at_dt.isoformat()
    message = (
        f"⏰ <b>Session Reminder!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕹️ Console : <b>{cid}</b>\n"
        f"👤 Member  : <b>{member_id}</b>\n"
        f"⏱️ Planned : <b>{planned_mins} mins</b>\n"
        f"🕑 End ~   : <b>{end_t}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ <b>5 မိနစ်အတွင်း Session ဆုံးမည်!</b>\n"
        f"ဆက်ကစားမည်ဆိုက ➕ Extend ကိုနှိပ်ပါ\n"
        f"ပြီးပြီဆိုက ✅ ပြီးပြီ ကိုနှိပ်ပြီး ⏹️ Session ဆုံး နှိပ်ပါ"
    )
    payload = _json.dumps({
        "chat_id":     chat_id,
        "cid":         cid,
        "member_id":   member_id,
        "planned_mins": planned_mins,
        "end_t":       end_t,
        "remind_at":   remind_at_iso,
        "message":     message,
    }).encode()
    try:
        request = _req.Request(
            N8N_SESSION_WEBHOOK,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        await asyncio.to_thread(lambda: _req.urlopen(request, timeout=10))
        return True
    except Exception as e:
        logging.warning(f"n8n session reminder POST failed: {e}")
        return False

async def _post_n8n_booking_reminder(
    bk_id: int, customer_name: str, phone: str,
    console_id: str, console_type: str,
    date_str: str, time_slot: str, duration_mins: int,
    tg_chat: str = "",
) -> bool:
    """POST booking confirmation to n8n for restart-proof follow-up reminders.
    n8n workflow schedules:
      • 10-min-before  → customer + staff reminder
      • At booking time → staff check-in prompt (Arrived / No-Show buttons)
      • +15 min         → auto-cancel if still confirmed
    """
    if not N8N_BOOKING_WEBHOOK:
        return False
    import json as _json, urllib.request as _req2, re as _re
    m = _re.match(r"(\d+)/(\d+)/(\d+)", date_str or "")
    if not m:
        logging.warning("_post_n8n_booking_reminder: bad date_str=%s", date_str)
        return False
    try:
        mon, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        h, mi = map(int, time_slot.split(":"))
        booking_dt  = datetime(year, mon, day, h, mi, tzinfo=MMT)
        booking_iso = booking_dt.isoformat()
    except Exception as e:
        logging.warning("_post_n8n_booking_reminder: parse error %s", e)
        return False
    api_url  = (_api_base() + "/api") if _api_base() else ""
    payload  = _json.dumps({
        "bk_id":            bk_id,
        "customer_name":    customer_name,
        "phone":            phone,
        "console_id":       console_id,
        "console_type":     console_type,
        "date":             date_str,
        "time_slot":        time_slot,
        "booking_iso":      booking_iso,
        "duration_mins":    duration_mins,
        "staff_notify_chat": STAFF_NOTIFY_CHAT,
        "telegram_chat_id": tg_chat,
        "replit_api_url":   api_url,
    }).encode()
    try:
        req = _req2.Request(
            N8N_BOOKING_WEBHOOK, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        await asyncio.to_thread(lambda: _req2.urlopen(req, timeout=10))
        logging.info("n8n booking reminder queued — bk#%s at %s", bk_id, booking_iso)
        return True
    except Exception as e:
        logging.warning("n8n booking webhook POST failed: %s", e)
        return False

async def cmd_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of upcoming confirmed bookings — staff can cancel any of them."""
    await update.message.reply_text("⏳ Booking list ရယူနေသည်...")
    data = await _replit_get_async("bookings?status=confirmed")
    bks  = data if isinstance(data, list) else []
    if not bks:
        await update.message.reply_text(
            "📅 ဖျက်ရန် Confirmed Booking မရှိပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
        )
        return MAIN_MENU
    now_str = now_mmt().strftime("%H:%M")
    upcoming = [b for b in bks if (b.get("date","") > now_mmt().strftime("%-m/%-d/%Y")
                                   or (b.get("date","") == now_mmt().strftime("%-m/%-d/%Y")
                                       and (b.get("timeSlot","") or "99:99") >= now_str))]
    if not upcoming:
        upcoming = bks  # show all if none are upcoming
    for b in upcoming[:10]:
        console_hint = b.get("consoleId") or b.get("consoleType","?")
        card = (
            f"🎫 <b>#{b['id']} {b['customerName']}</b>\n"
            f"📅 {b['date']}  ⏰ {b['timeSlot']}\n"
            f"🕹️ {console_hint}  ⏱️ {b.get('durationMins','?')} min\n"
            f"📞 {b.get('phone','-')}  "
            f"{'🔵 Today' if b.get('date') == now_mmt().strftime('%-m/%-d/%Y') else ''}"
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚫 Cancel Booking", callback_data=f"bkc:{b['id']}"),
        ]])
        await update.message.reply_text(card, parse_mode="HTML", reply_markup=kb)
    await update.message.reply_text(
        f"↑ Cancel လုပ်ချင်သည့် Booking ကိုရွေးပါ ({len(upcoming)} bookings).",
        reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
    )
    return MAIN_MENU

async def cb_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline 🚫 Cancel Booking — show reason selection first."""
    query = update.callback_query
    await query.answer()
    try:
        bk_id = int(query.data.split(":")[1])
    except Exception as e:
        logger.error("cb_cancel_booking: %s", e, exc_info=True)
        return

    # Fetch current booking info for confirmation display
    bk_info = await _replit_get_async(f"bookings/{bk_id}")
    if not bk_info or not isinstance(bk_info, dict):
        await query.message.reply_text("❌ Booking ဒ\ါ\တ\ာ \မ\ရ\ိ\ပ\ါ\း (Server \န\ှ\င\့\် \ဆ\က\်\သ\ွ\ယ\်\မ\ှ\ု \မ\ရ\ှ\ိ)")
        return CONSOLE_MENU
    if not bk_info or isinstance(bk_info, list):
        bk_info = {}

    cur_status = bk_info.get("status", "")
    if cur_status in ("cancelled", "rejected", "completed"):
        try:
            await query.edit_message_text(
                f"⚠️ Booking #{bk_id} မှာ ဆောင်ရွက်မရနိုင်ပါ (status: {cur_status})",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error("cb_cancel_booking: %s", e, exc_info=True)
            pass
        return

    cust_name = bk_info.get("customerName", "?")
    date_str  = bk_info.get("date", "?")
    slot_str  = bk_info.get("timeSlot", "?")
    cons_str  = bk_info.get("consoleId") or bk_info.get("consoleType", "?")

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Customer ရပ်တောင်းသောကြောင့်", callback_data=f"bkcr:{bk_id}:cust")],
        [InlineKeyboardButton("🖥️ Console / Technical ပြဿနာ",  callback_data=f"bkcr:{bk_id}:cons")],
        [InlineKeyboardButton("📅 Schedule ပြောင်းလဲသောကြောင့်", callback_data=f"bkcr:{bk_id}:sche")],
        [InlineKeyboardButton("✏️ Note ကိုယ်တိုင်ရိုက်မည်",       callback_data=f"bkcr:{bk_id}:custom")],
        [InlineKeyboardButton("↩️ မပယ်ဖျက်တော့ပါ",              callback_data=f"bkcr:{bk_id}:abort")],
    ])
    try:
        await query.edit_message_text(
            f"🚫 <b>Cancel Booking #{bk_id}?</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 {cust_name}  📅 {date_str}\n"
            f"⏰ {slot_str}  🎮 {cons_str}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"ပယ်ဖျက်ရသည့် အကြောင်းပြချက်ရွေးပါ ↓",
            parse_mode="HTML",
            reply_markup=kb,
        )
    except Exception as e:
        logger.error("cb_cancel_booking: %s", e, exc_info=True)
        pass

async def cb_cancel_with_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reason selection for cancel booking flow."""
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":", 2)
    if len(parts) < 3:
        return
    try:
        bk_id = int(parts[1])
    except Exception as e:
        logger.error("cb_cancel_with_reason: %s", e, exc_info=True)
        return
    reason_key = parts[2]
    staff_name = query.from_user.full_name or "Staff"

    if reason_key == "abort":
        try:
            await query.edit_message_text("↩️ Cancel ပယ်ဖျက်မည့် လုပ်ငန်းကို ရပ်လိုက်သည်။")
        except Exception as e:
            logger.error("cb_cancel_with_reason: %s", e, exc_info=True)
            pass
        return

    if reason_key == "custom":
        # Store pending and ask for typed note
        _pending_cancel_note[query.from_user.id] = {
            "bk_id":   bk_id,
            "staff":   staff_name,
            "chat_id": query.message.chat_id,
        }
        try:
            await query.edit_message_text(
                f"✏️ <b>Booking #{bk_id} — Custom Note</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"ပယ်ဖျက်ရသည့် အကြောင်းပြချက် ရိုက်ပို့ပါ:\n"
                f"<i>(e.g. Double booking, မလာနိုင်ဘူး...)</i>",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error("cb_cancel_with_reason: %s", e, exc_info=True)
            pass
        return

    reason_labels = {
        "cust": "Customer ရပ်တောင်းသောကြောင့်",
        "cons": "Console / Technical ပြဿနာကြောင့်",
        "sche": "Schedule ပြောင်းလဲသောကြောင့်",
    }
    reason = reason_labels.get(reason_key, "Staff Cancelled")
    await _do_cancel_booking(query, bk_id, staff_name, reason)

async def _do_cancel_booking(query_or_msg, bk_id: int, staff_name: str, reason: str):
    """Execute the cancel PATCH and notify customer. Works for both callback query and message."""
    staff_note = f"Cancelled by {staff_name}: {reason}"
    result = await _replit_patch_async(
        f"bookings/{bk_id}/status",
        {"status": "cancelled", "staffNote": staff_note},
    )
    is_query = hasattr(query_or_msg, "edit_message_text")
    if not result:
        txt = f"❌ Booking #{bk_id} cancel မရပါ — API စစ်ပါ"
        try:
            if is_query:
                await query_or_msg.edit_message_text(txt)
            else:
                await query_or_msg.reply_text(txt)
        except Exception as e:
            logger.error("_do_cancel_booking: %s", e, exc_info=True)
            pass
        return


    # Clean up any Scheduled Console_Booking row for this booking's console
    _cancel_console = (result.get("consoleId") or "").strip() if isinstance(result, dict) else ""
    if _cancel_console:
        try:
            _bk_sh = get_booking_sh()
            _today = today_str()
            _rows_data = _bk_sh.get("A:I")
            for _i, _row in enumerate(_rows_data[1:], start=2):
                if (len(_row) >= 7
                        and (_row[1] or "").strip() == _today
                        and (_row[2] or "").strip() == _cancel_console
                        and (_row[6] or "").strip() == "Scheduled"):
                    _bk_sh.update(f"G{_i}", [["Done"]])
                    _bk_sh.update(f"I{_i}", [[f"Cancelled (BK#{bk_id})"]])
                    logger.info("Console_Booking row %d marked Done (booking #%d cancelled)", _i, bk_id)
                    break
        except Exception as _e:
            logger.warning("Console_Booking cleanup on cancel failed: %s", _e, exc_info=True)

    done_txt = (
        f"🚫 <b>Booking #{bk_id} Cancelled</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 {result.get('customerName','?')}  📅 {result.get('date','?')}\n"
        f"⏰ {result.get('timeSlot','?')}  🎮 {result.get('consoleType','?')}\n"
        f"📝 {reason}\n"
        f"👮 {staff_name}"
    )
    try:
        if is_query:
            await query_or_msg.edit_message_text(done_txt, parse_mode="HTML")
        else:
            await query_or_msg.reply_text(done_txt, parse_mode="HTML")
    except Exception as e:
        logger.error("_do_cancel_booking: %s", e, exc_info=True)
        pass

    # Notify customer if they have Telegram
    tg_chat = result.get("telegramChatId") or ""
    if tg_chat and CUSTOMER_BOT_TOKEN:
        cust_msg = (
            f"❌ <b>Booking #{bk_id} ကို ပယ်ဖျက်ပြီ</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📅 {result.get('date','?')}  ⏰ {result.get('timeSlot','?')}\n"
            f"🎮 {result.get('consoleType','?')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📝 အကြောင်းပြချက်: {reason}\n"
            f"ကျေးဇူးပြု၍ ဆက်သွယ်ရန် @psvibeofficial"
        )
        await asyncio.to_thread(_notify_customer, tg_chat, cust_msg)

async def handle_cancel_note_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle typed cancel reason from staff (pending custom note)."""
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id or user_id not in _pending_cancel_note:
        return
    pending   = _pending_cancel_note.pop(user_id)
    bk_id     = pending["bk_id"]
    staff     = pending["staff"]
    reason    = (update.message.text or "").strip() or "Note မပေး"
    await _do_cancel_booking(update.message, bk_id, staff, reason)

async def _do_extend(bot, query, cid: str, member_id: str,
                     chat_id: int, extra_mins: int):
    """Shared logic: acknowledge extension and schedule next reminder."""
    now = now_mmt()
    # Use actual session end time as base (not current time / remind time)
    _key = _remind_key(cid, chat_id)
    _stored_end = _SESSION_END_TIMES.get(_key, "")
    if _stored_end:
        try:
            _eh, _em = map(int, _stored_end.split(":"))
            _base_dt  = now.replace(hour=_eh, minute=_em, second=0, microsecond=0)
            # If stored end is in the past (session overdue), use now as base
            if _base_dt < now:
                _base_dt = now
        except Exception as e:
            logger.error("_do_extend: %s", e, exc_info=True)
            _base_dt = now
    else:
        _base_dt = now
    new_end_dt = _base_dt + timedelta(minutes=extra_mins)
    new_end_t  = new_end_dt.strftime("%H:%M")
    has_remind = extra_mins > 5

    text = (
        f"⏰ <b>Session Extended!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕹️ Console : <b>{cid}</b>\n"
        f"👤 Member  : <b>{member_id}</b>\n"
        f"➕ Extended: <b>+{extra_mins} mins</b>\n"
        f"🕑 New End : <b>{new_end_t}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{'⏰ Next reminder ပေးမည်' if has_remind else '⚠️ 5min မတိုင်တော့ Reminder မပေးနိုင်'}"
    )
    if query is not None:
        await query.edit_message_text(text, parse_mode="HTML")
        # Also notify group chat about the extension
        if STAFF_NOTIFY_CHAT and str(STAFF_NOTIFY_CHAT) != str(chat_id):
            try:
                await bot.send_message(
                    chat_id=int(STAFF_NOTIFY_CHAT),
                    text=text,
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.error("_do_extend: %s", e, exc_info=True)
                pass
    else:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        if STAFF_NOTIFY_CHAT and str(STAFF_NOTIFY_CHAT) != str(chat_id):
            try:
                await bot.send_message(
                    chat_id=int(STAFF_NOTIFY_CHAT),
                    text=text,
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.error("_do_extend: %s", e, exc_info=True)
                pass

    _cancel_remind(cid, chat_id)   # stop old loop before starting new one
    # Update stored end time immediately so next extend uses correct base
    _SESSION_END_TIMES[_remind_key(cid, chat_id)] = new_end_t
    if has_remind:
        ext_delay = (extra_mins - 5) * 60   # seconds until 5-min-before-end
        # Bot loop: fire at "5 min before end", then every 5 min
        task = asyncio.create_task(
            _remind_loop(bot, chat_id, cid, member_id,
                         extra_mins, new_end_t, ext_delay)
        )
        _REMIND_TASKS[_remind_key(cid, chat_id)] = task

async def cb_extend_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """CallbackQuery handler for ➕ Extend / ✏️ Custom / ✅ Done buttons."""
    query = update.callback_query
    await query.answer()

    data = query.data  # "ext:{extra_str}:{cid}|{member_id}|{chat_id}"
    try:
        _, extra_str, tag = data.split(":", 2)
        cid, member_id, chat_id_str = tag.split("|", 2)
        chat_id = int(chat_id_str)
    except Exception as e:
        logger.error("cb_extend_timer: %s", e, exc_info=True)
        await query.edit_message_text("⚠️ Data error — ထပ်မံကြိုးစားပါ")
        return

    # ── ✅ End ───────────────────────────────────────────────────────────────
    if extra_str == "0":
        await query.edit_message_text(
            f"✅ <b>Session ပြီးပြီ!</b>\n"
            f"🕹️ Console : <b>{cid}</b>  👤 <b>{member_id}</b>\n"
            f"⏹️ Session ဆုံး နှိပ်ပြီး Voucher ဖန်တီးပါ",
            parse_mode="HTML",
        )
        return

    # ── ✏️ Custom ────────────────────────────────────────────────────────────
    if extra_str == "custom":
        # Guard: check session is still active before allowing custom extend
        _still_active_c = await _is_session_active(cid)
        if not _still_active_c:
            await query.edit_message_text(
                "⛔ <b>Session ပြီးသွားပြီ!</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                f"🕹️ Console : <b>{cid}</b>  👤 <b>{member_id}</b>\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "ဒီ Session ကို Extend မလုပ်နိုင်တော့ပါ\n"
                "Session ဆုံး နှိပ်ပြီး Voucher ဖန်တီးပါ",
                parse_mode="HTML",
            )
            _cancel_remind(cid, chat_id)
            return
        # Button presser's personal chat ID (works even if button is in group chat)
        presser_id = query.from_user.id
        # Store pending extend context in bot_data keyed by presser_id
        # handle_custom_extend_reply will match by presser_id from personal chat
        context.bot_data[f"_extend_pending_{presser_id}"] = {
            "cid": cid, "member_id": member_id, "chat_id": chat_id,
            "expect_chat_id": presser_id,
            "created_at": time.time(),
        }
        # Edit group chat message to show we're waiting
        await query.edit_message_text(
            f"✏️ <b>Custom Extend</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🕹️ Console : <b>{cid}</b>  👤 <b>{member_id}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"ဆက်ကစားမည့် မိနစ် ရိုက်ထည့်ပြီး Send လုပ်ပါ\n"
            f"(ဥပမာ: <code>45</code>)",
            parse_mode="HTML",
        )
        # Send ForceReply to the button presser's PERSONAL chat (not group chat)
        # This bypasses the _ALLOWED_STAFF_IDS group-message restriction
        await context.bot.send_message(
            chat_id=presser_id,
            text=(
                f"✏️ <b>Custom Extend</b>\n"
                f"🕹️ Console: <b>{cid}</b>  👤 <b>{member_id}</b>\n"
                f"ဆက်ကစားမည့် မိနစ် ထည့်ပါ:"
            ),
            parse_mode="HTML",
            reply_markup=ForceReply(selective=True, input_field_placeholder="မိနစ် (ဥပမာ 45)"),
        )
        return

    # ── Preset +N ────────────────────────────────────────────────────────────
    try:
        extra_mins = int(extra_str)
    except ValueError:
        await query.edit_message_text("⚠️ Data error")
        return

    # Guard: check session is still active before extending
    still_active = await _is_session_active(cid)
    if not still_active:
        await query.edit_message_text(
            "⛔ <b>Session ပြီးသွားပြီ!</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"🕹️ Console : <b>{cid}</b>  👤 <b>{member_id}</b>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "ဒီ Session ကို Extend မလုပ်နိုင်တော့ပါ\n"
            "Session ဆုံး နှိပ်ပြီး Voucher ဖန်တီးပါ",
            parse_mode="HTML",
        )
        _cancel_remind(cid, chat_id)
        return
    await _do_extend(context.bot, query, cid, member_id, chat_id, extra_mins)

async def cb_booking_arrive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline button handler for ✅ ရောက်ပြီ / ❌ မရောက်ဘူး on arrive-check messages."""
    query = update.callback_query
    await query.answer()
    data = query.data  # "bkarr:{bk_id}" or "bkns:{bk_id}"
    try:
        action, bk_id_str = data.split(":", 1)
        bk_id = int(bk_id_str)
    except Exception as e:
        logger.error("cb_booking_arrive: %s", e, exc_info=True)
        await query.edit_message_text("⚠️ Data error")
        return
    staff_name = query.from_user.full_name or "Staff"
    if action == "bkarr":
        # Mark as arrived
        patch_body = {"status": "arrived", "staffNote": f"Arrived — confirmed by {staff_name}"}
        result = await _replit_patch_async(f"bookings/{bk_id}/status", patch_body)
        if result:
            await query.edit_message_text(
                f"✅ <b>Customer ရောက်ပြီ!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📋 Booking: <b>#{bk_id}</b>\n"
                f"👤 Confirmed by: <b>{staff_name}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Console ပြင်ဆင်ပြီး Session စတင်ပါ",
                parse_mode="HTML",
            )
        else:
            await query.edit_message_text(f"⚠️ Update မအောင်မြင်ပါ — Booking #{bk_id}")
    elif action == "bkns":
        # Mark as no-show
        patch_body = {"status": "no_show", "staffNote": f"No-Show — marked by {staff_name}"}
        result = await _replit_patch_async(f"bookings/{bk_id}/status", patch_body)
        if result:
            # Clean up Scheduled Console_Booking row for no-show
            try:
                _ns_bk_data = await _replit_get_async(f"bookings/{bk_id}")
                _ns_console = ""
                if isinstance(_ns_bk_data, dict):
                    _ns_console = (_ns_bk_data.get("consoleId") or "").strip()
                if _ns_console:
                    _bk_sh = get_booking_sh()
                    _today = today_str()
                    _rows_data = _bk_sh.get("A:I")
                    for _i, _row in enumerate(_rows_data[1:], start=2):
                        if (len(_row) >= 7
                                and (_row[1] or "").strip() == _today
                                and (_row[2] or "").strip() == _ns_console
                                and (_row[6] or "").strip() == "Scheduled"):
                            _bk_sh.update(f"G{_i}", [["Done"]])
                            _bk_sh.update(f"I{_i}", [[f"No-show (BK#{bk_id})"]])
                            break
            except Exception as _e:
                logger.warning("Console_Booking cleanup on no-show failed: %s", _e, exc_info=True)

            await query.edit_message_text(
                f"❌ <b>No-Show မှတ်တမ်းတင်ပြီ</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📋 Booking: <b>#{bk_id}</b>\n"
                f"👤 Marked by: <b>{staff_name}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Console ကို Free ဖြင့် ပြန်ထားနိုင်သည်",
                parse_mode="HTML",
            )
        else:
            await query.edit_message_text(f"⚠️ Update မအောင်မြင်ပါ — Booking #{bk_id}")

async def handle_custom_extend_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Group -1 handler: captures the free-text reply for custom extend minutes.
    Uses bot_data keyed by presser_id so it works from personal chat after
    Custom button is pressed in group chat.
    Raises ApplicationHandlerStop to prevent ConversationHandler from also firing."""
    user = update.effective_user
    if not user:
        return
    presser_id = user.id
    # Look up pending extend by the message sender's user ID
    pending = context.bot_data.get(f"_extend_pending_{presser_id}")
    # Also check legacy user_data for backwards compat
    if pending is None:
        pending = context.user_data.get("_extend_pending")
    if pending is None:
        return  # not our message — let ConversationHandler handle it normally

    # Stale pending guard: if created > 300s ago, clear and pass through
    if pending.get("created_at") and time.time() - pending["created_at"] > 300:
        context.bot_data.pop(f"_extend_pending_{presser_id}", None)
        context.user_data.pop("_extend_pending", None)
        return  # stale pending — let ConversationHandler handle it


    text = update.message.text.strip()
    try:
        extra_mins = int(text)
        if extra_mins <= 0:
            raise ValueError
    except ValueError:
        # Silently ignore non-number messages (other staff chatting in group)
        # Only reply with error if it looks like an intentional number attempt
        if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
            await update.message.reply_text(
                "⚠️ မှန်ကန်သော ဂဏနး ရိုက်ထည့်ပါ (ဥပမာ: 45)",
                reply_markup=ForceReply(selective=True, input_field_placeholder="မိနစ် (ဥပမာ 45)"),
            )
            raise ApplicationHandlerStop
        # Non-numeric text — not our message, pass through
        return

    cid       = pending["cid"]
    member_id = pending["member_id"]
    chat_id   = pending["chat_id"]
    # Guard: verify this message is from the expected chat
    expect_chat = pending.get("expect_chat_id")
    if expect_chat is not None and update.effective_chat.id != expect_chat:
        # Stale pending from a different chat — clear and pass through
        context.bot_data.pop(f"_extend_pending_{presser_id}", None)
        context.user_data.pop("_extend_pending", None)
        return  # let ConversationHandler handle it

    # Clear from bot_data (keyed by presser_id)
    context.bot_data.pop(f"_extend_pending_{presser_id}", None)
    context.user_data.pop("_extend_pending", None)

    await _do_extend(context.bot, None, cid, member_id, chat_id, extra_mins)
    raise ApplicationHandlerStop  # done — don't let conv handler see this message
