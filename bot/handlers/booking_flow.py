from bot import (
    BTN_BACK_MAIN, CONSOLE_MENU, CUSTOMER_BOT_TOKEN, MAIN_MENU,
    STAFF_NOTIFY_CHAT, STAFF_NOTIFY_THREAD,
    _api_base, _psvibe_get, _psvibe_get_async, _psvibe_patch, _psvibe_patch_async, _psvibe_post_async, get_booking_sh, now_mmt,
    today_str, end_booking_async,
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
from bot.handlers.notify import _notify_customer, get_customer_chat_id
from bot.session_reminder_store import persist_reminder, remove_persisted_reminder

# Re-export for backward compatibility — moved to session_reminder.py
from bot.handlers.session_reminder import (
    _SESSION_END_TIMES, _SESSION_TOTAL_MINS, _REMIND_TASKS, _LAST_REMINDER_SENT,
    _pending_cancel_note, _NO_TIMER_CONSOLES,
    _remind_key, _cancel_remind, _extend_timer_kb, _remind_loop,
    _send_session_reminder, _post_n8n_session_reminder, _post_n8n_booking_reminder,
    add_no_timer_console, remove_no_timer_console, _is_session_active,
)

async def cmd_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of upcoming confirmed bookings — staff can cancel any of them."""
    await update.message.reply_text("⏳ Booking list ရယူနေသည်...")
    data = await _psvibe_get_async("bookings?status=confirmed")
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
            f"🎫 <b>#{b['id']} {b.get('customerName') or '—'}</b>\n"
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
    bk_info = await _psvibe_get_async(f"bookings/{bk_id}")
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
    is_query = hasattr(query_or_msg, "edit_message_text")

    # Fetch full booking data BEFORE cancelling — PATCH response only has {booking_id, status}
    _bk_pre = await _psvibe_get_async(f"bookings/{bk_id}")
    if isinstance(_bk_pre, dict) and "booking" in _bk_pre:
        _bk_pre = _bk_pre["booking"]
    _pre_cust = (_bk_pre.get("customerName") or "") if isinstance(_bk_pre, dict) else ""
    _pre_date = (_bk_pre.get("date") or "") if isinstance(_bk_pre, dict) else ""
    _pre_time = (_bk_pre.get("timeSlot") or "") if isinstance(_bk_pre, dict) else ""
    _pre_console = (_bk_pre.get("consoleType") or _bk_pre.get("console_id") or "") if isinstance(_bk_pre, dict) else ""
    _pre_duration = (_bk_pre.get("durationMins") or 60) if isinstance(_bk_pre, dict) else 60
    _pre_game = (_bk_pre.get("gameName") or "") if isinstance(_bk_pre, dict) else ""
    _pre_phone = (_bk_pre.get("phone") or _bk_pre.get("customerPhone") or "") if isinstance(_bk_pre, dict) else ""
    _pre_tg_chat = (_bk_pre.get("telegramChatId") or "") if isinstance(_bk_pre, dict) else ""

    staff_note = f"Cancelled by {staff_name}: {reason}"
    result = await _psvibe_patch_async(
        f"bookings/{bk_id}/status",
        {"status": "cancelled", "staffNote": staff_note},
    )
    # Cancel any pending 30-min advance reminder
    try:
        _r = await _psvibe_post_async("webhook/booking-reminder/cancel", {"bk_id": bk_id})
        logger.debug("_do_cancel_booking: reminder cancel bk#%d → %s", bk_id, _r)
    except Exception:
        pass
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

    # Cancel any pending advance reminder task (bot-based)
    try:
        from bot.handlers.booking import _cancel_advance_reminder
        if _cancel_advance_reminder(bk_id):
            logger.info("_do_cancel_booking: cancelled advance reminder bk#%d", bk_id)
    except Exception:
        pass
    _cancel_console = (_bk_pre.get("console_id") or "").strip() if isinstance(_bk_pre, dict) else ""
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
        # Clean up No Timer tracking for this console
        if _cancel_console:
            remove_no_timer_console(_cancel_console)

    done_txt = (
        f"🚫 <b>Booking #{bk_id} Cancelled</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 {_pre_cust or '?'}  📅 {_pre_date or '?'}\n"
        f"⏰ {_pre_time or '?'}  🎮 {_pre_console or '?'}\n"
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

    # Notify admin group about cancellation (fix: was only showing in staff's chat)
    if STAFF_NOTIFY_CHAT:
        admin_msg = (
            f"🚫 <b>Booking #{bk_id} Cancelled</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 {_pre_cust or '?'}  📅 {_pre_date or '?'}\n"
            f"⏰ {_pre_time or '?'}  🎮 {_pre_console or '?'}\n"
            f"📝 {reason}\n"
            f"👮 {staff_name}"
        )
        try:
            if hasattr(query_or_msg, 'message'):
                kwargs = {"chat_id": int(STAFF_NOTIFY_CHAT), "text": admin_msg, "parse_mode": "HTML"}
                if STAFF_NOTIFY_THREAD:
                    kwargs["message_thread_id"] = STAFF_NOTIFY_THREAD
                await query_or_msg.message.bot.send_message(**kwargs)
        except Exception as _ane:
            logger.debug("_do_cancel_booking: admin notify failed: %s", _ane)

    # Notify customer if they have Telegram (use pre-fetched data)
    if _pre_tg_chat and CUSTOMER_BOT_TOKEN:
        cust_msg = (
            f"❌ <b>Booking #{bk_id} ကို ပယ်ဖျက်ပြီ</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📅 {_pre_date or '?'}  ⏰ {_pre_time or '?'}\n"
            f"🎮 {_pre_console or '?'}  🕹 {_pre_game or '—'}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📝 အကြောင်းပြချက်: {reason}\n"
            f"ကျေးဇူးပြု၍ ဆက်သွယ်ရန် @psvibeofficial"
        )
        await asyncio.to_thread(_notify_customer, _pre_tg_chat, cust_msg)

    # Notify admin group
    if STAFF_NOTIFY_CHAT:
        admin_notif = (
            f"❌ <b>Booking #{bk_id} Cancelled by Staff</b>\n"
            f"👤 {_pre_cust or '?'}  📞 {_pre_phone or '—'}\n"
            f"📅 {_pre_date or '?'}  ⏰ {_pre_time or '?'}\n"
            f"🎮 {_pre_console or '?'}  🕹 {_pre_game or '—'}\n"
            f"📝 Reason: {reason}\n"
            f"👮 By: {staff_name}"
        )
        try:
            bot = query_or_msg.get_bot()
            kwargs = {"chat_id": int(STAFF_NOTIFY_CHAT), "text": admin_notif, "parse_mode": "HTML"}
            if STAFF_NOTIFY_THREAD:
                kwargs["message_thread_id"] = STAFF_NOTIFY_THREAD
            await bot.send_message(**kwargs)
        except Exception:
            pass

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
                     chat_id: int, extra_mins: int,
                     message_thread_id: int = 0):
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

    # Compute total remaining seconds for timer delay correction
    total_rem_secs = max(0, (new_end_dt - now).total_seconds())
    # Save accumulated total BEFORE _cancel_remind (it now clears the dict)
    _session_key = _remind_key(cid, chat_id)
    _old_total = _SESSION_TOTAL_MINS.get(_session_key, 0)
    _cancel_remind(cid, chat_id)   # stop old loop before starting new one
    # Update stored end time immediately so next extend uses correct base
    _SESSION_END_TIMES[_session_key] = new_end_t
    # Accumulate total plan mins (original + all extends)
    _SESSION_TOTAL_MINS[_session_key] = _old_total + extra_mins
    # Sync extended duration to DB via API (so console status shows correct timer)
    # ⚠️ AWAIT instead of fire-and-forget: ensures DB is updated before returning.
    # Without this, the console status board shows the OLD duration when extend
    # API call silently fails (fire-and-forget catches exceptions but can't retry).
    try:
        _db_result = await _psvibe_post_async(
            "bookings/extend-duration",
            {"console_id": cid, "extra_mins": extra_mins}
        )
        if _db_result is None:
            logger.error("_do_extend: DB sync returned empty for %s", cid)
            # Try to notify staff about the failure
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"⚠️ <b>DB Sync Warning</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"🕹️ Console: <b>{cid}</b>\n"
                        f"➕ Extended: <b>+{extra_mins} mins</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"Database ကို sync မလုပ်နိုင်ပါ — Console Status ပေါ်တွင်\n"
                        f"အချိန်မှန်မပြတတ်ပါ။ ထပ်မံကြိုးစားရန် session ကို ပြန် Extend လုပ်ပေးပါ။"
                    ),
                    parse_mode="HTML",
                )
            except Exception:
                pass
    except Exception as e:
        logger.error("_do_extend: DB sync failed for %s: %s", cid, e)
    # Persist updated end time to disk (rem_mins ≈ remaining minutes)
    _persist_rem_mins = max(1, int(total_rem_secs / 60))
    persist_reminder(cid, chat_id, member_id, _persist_rem_mins, new_end_t,
                      new_end_dt.isoformat(), message_thread_id,
                      total_plan_mins=_SESSION_TOTAL_MINS[_session_key])
    # Skip timer if original session was No Timer
    if cid in _NO_TIMER_CONSOLES:
        has_remind = False
        text += "\n\n⏸️ No Timer session — reminder မပေးပါ"
    if has_remind:
        ext_delay = max(0, total_rem_secs - 5 * 60)  # seconds until 5-min-before-end
        # planned_mins = remaining minutes for display (at least 1)
        rem_mins = max(1, int(total_rem_secs / 60))
        # Bot loop: fire at "5 min before end", then every 5 min
        task = asyncio.create_task(
            _remind_loop(bot, chat_id, cid, member_id,
                         rem_mins, new_end_t, ext_delay, message_thread_id)
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

    # ── ⏹️ Redirect to Sale Bot ───────────────────────────────────────────────
    if extra_str == "redirect":
        still_active_r = await _is_session_active(cid)
        if not still_active_r:
            await query.edit_message_text(
                "⛔ <b>Session ပြီးသွားပြီ!</b>\n"
                f"🕹️ Console : <b>{cid}</b>  👤 <b>{member_id}</b>",
                parse_mode="HTML",
            )
            _cancel_remind(cid, chat_id)
        else:
            await query.edit_message_text(
                f"⏹️ <b>Session End — Sale Bot မှ လုပ်ပါ</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🕹️ Console : <b>{cid}</b>  👤 <b>{member_id}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📋 Sale Bot → Console Management → Session End\n"
                f"ဒီနေရာမှာ End လုပ်လို့ မရပါ — Voucher ထွက်မှာမဟုတ်ပါ",
                parse_mode="HTML",
            )
        return

    # ── ✅ End (legacy — button removed, keep for backwards compat) ────────
    if extra_str == "0":
        # Find active booking for this console and end it
        bk_id = None
        try:
            consoles = await _psvibe_get_async("fetch_console_status")
            for c in (consoles or []):
                if (c.get("console_id") or "").strip().upper() == cid.strip().upper():
                    bk_id = c.get("booking_id")
                    break
        except Exception as e:
            logger.warning("cb_extend_timer: fetch_console_status failed: %s", e)

        if bk_id:
            ok = await end_booking_async(str(bk_id))
            if ok:
                _cancel_remind(cid, chat_id)
                await query.edit_message_text(
                    f"✅ <b>Session ပြီးပြီ!</b>\n"
                    f"🕹️ Console : <b>{cid}</b>  👤 <b>{member_id}</b>\n"
                    f"⏹️ Session ဆုံး နှိပ်ပြီး Voucher ဖန်တီးပါ",
                    parse_mode="HTML",
                )
            else:
                await query.edit_message_text(
                    f"⚠️ Session ဆုံးဖို့ API error တက်ပါသည်။\n"
                    f"Console Management → Session End မှ ပြန်လုပ်ပါ။",
                    parse_mode="HTML",
                )
        else:
            await query.edit_message_text(
                f"⚠️ <b>{cid}</b> တွင် active session မတွေ့ပါ။\n"
                f"Console Management → Session End မှ ပြန်လုပ်ပါ။",
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
            f"━��━━━━━━━━━━━━━━━━\n"
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
    _mtid = getattr(getattr(query, 'message', None), 'message_thread_id', 0)
    await _do_extend(context.bot, query, cid, member_id, chat_id, extra_mins, _mtid)

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
        result = await _psvibe_patch_async(f"bookings/{bk_id}/status", patch_body)
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
        result = await _psvibe_patch_async(f"bookings/{bk_id}/status", patch_body)
        if result:
            # Clean up Scheduled Console_Booking row for no-show
            try:
                _ns_bk_data = await _psvibe_get_async(f"bookings/{bk_id}")
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
            # Clean up No Timer tracking for this console
            if _ns_console:
                remove_no_timer_console(_ns_console)

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

    _mtid = getattr(getattr(update, 'message', None), 'message_thread_id', 0)
    await _do_extend(context.bot, None, cid, member_id, chat_id, extra_mins, _mtid)
    raise ApplicationHandlerStop  # done — don't let conv handler see this message
