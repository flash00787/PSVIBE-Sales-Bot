"""PS VIBE Bot — Session reminder / timer module.
Extracted from booking_flow.py for maintainability.

Manages: session end-time tracking, reminder-asyncio-task scheduling,
n8n webhook timers, extend/repeat logic, and session-active checks.
"""
from bot import (
    MMT, N8N_BOOKING_WEBHOOK, N8N_SESSION_WEBHOOK, STAFF_NOTIFY_CHAT, STAFF_NOTIFY_THREAD,
    _api_base, _psvibe_get_async, _psvibe_post_async, now_mmt,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging, json, re
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta
from typing import Dict
import asyncio
import time
from bot.handlers.notify import _notify_customer, get_customer_chat_id
from bot.session_reminder_store import persist_reminder, remove_persisted_reminder

# Module-level state
_pending_cancel_note: Dict[int, dict] = {}
_REMIND_TASKS: dict[str, "asyncio.Task[None]"] = {}
_SESSION_END_TIMES: dict[str, str] = {}
# ⚠️ Dedup: prevent duplicate reminder messages within 60s per console
_LAST_REMINDER_SENT: Dict[str, float] = {}
_SESSION_TOTAL_MINS: dict[str, int] = {}  # accumulated total plan (original + all extends)
_NO_TIMER_CONSOLES: set[str] = set()  # consoles that should never fire reminders


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
        [InlineKeyboardButton("⏹️ Sale Bot → Session End", callback_data=f"ext:redirect:{tag}")],
    ])

def _remind_key(cid: str, chat_id: int) -> str:
    return f"{cid}|{chat_id}"

def add_no_timer_console(cid: str) -> None:
    """Mark a console as No Timer - reminders will never be scheduled for it."""
    _NO_TIMER_CONSOLES.add(cid)
    logger.info("No Timer: %s added", cid)

def remove_no_timer_console(cid: str) -> None:
    """Remove No Timer tracking (e.g., session ended)."""
    _NO_TIMER_CONSOLES.discard(cid)
    logger.info("No Timer: %s removed", cid)


def _cancel_remind(cid: str, chat_id: int) -> None:
    key  = _remind_key(cid, chat_id)
    task = _REMIND_TASKS.pop(key, None)
    if task and not task.done():
        task.cancel()
    # Clean up in-memory state so old sessions don't leak into new ones
    _SESSION_END_TIMES.pop(key, None)
    _SESSION_TOTAL_MINS.pop(key, None)
    # Also purge from persistent store so restarts don't revive it
    remove_persisted_reminder(cid, chat_id)

async def _is_session_active(cid: str) -> bool:
    """Quick sync check: is this console Active today? (via console_status + cross-check booking)."""
    try:
        # Check console_status via API
        bk_data = await _psvibe_get_async("fetch_console_status")
        console_status_active = False
        if isinstance(bk_data, list):
            for row in bk_data:
                if isinstance(row, dict) and row.get("console_id", "").strip() == cid and row.get("status", "").strip() == "Active":
                    console_status_active = True
                    break
        elif isinstance(bk_data, dict):
            consoles = bk_data.get("consoles", bk_data.get("data", []))
            if isinstance(consoles, list):
                for row in consoles:
                    if isinstance(row, dict) and row.get("console_id", "").strip() == cid and row.get("status", "").strip() == "Active":
                        console_status_active = True
                        break
            elif isinstance(consoles, dict):
                for row in consoles.get("consoles", []):
                    if isinstance(row, dict) and row.get("console_id", "").strip() == cid and row.get("status", "").strip() == "Active":
                        console_status_active = True
                        break

        # Cross-check: if console_status says NOT Active, verify against booking table
        if not console_status_active:
            bookings = await _psvibe_get_async("bookings")
            booking_active = False
            booking_list = []
            if isinstance(bookings, list):
                booking_list = bookings
            elif isinstance(bookings, dict):
                booking_list = bookings.get("bookings", bookings.get("data", []))
            if isinstance(booking_list, list):
                for b in booking_list:
                    if isinstance(b, dict) and (b.get("console_id", "") or "").strip() == cid and str(b.get("status", "")).strip() == "Active":
                        booking_active = True
                        logger.warning(
                            "console_status/booking MISMATCH for %s (BK#%s) — trusting booking table",
                            cid, b.get("id", "?"))
                        break
            if booking_active:
                return True  # Booking says Active → console_status is wrong

        return console_status_active
    except Exception as e:
        logger.error("_is_session_active: %s", e, exc_info=True)
        return True
    return False

async def _remind_loop(
    bot, chat_id: int, cid: str, member_id: str,
    planned_mins: int, end_t: str, initial_delay: int, message_thread_id: int = 0,):
    """Fires reminder at initial_delay, then every 5 mins while session is still Active.

    IMPORTANT: The FIRST fire always sends (no active-check) so that edge cases
    like an interrupted session-end flow (status briefly "Ended") still deliver
    the inline-keyboard Extend/Done prompt.  Subsequent fires check the sheet.
    """
    key = _remind_key(cid, chat_id)
    _REMIND_TASKS[key] = asyncio.current_task()   # type: ignore[assignment]
    _SESSION_END_TIMES[key] = end_t               # track current planned end time
    # 🐛 Fix: Initialize _SESSION_TOTAL_MINS so first extend doesn't lose original plan minutes.
    # Without this, _do_extend's  .get(_session_key, 0)  returns 0 and overwrites the total.
    if key not in _SESSION_TOTAL_MINS:
        _SESSION_TOTAL_MINS[key] = planned_mins
    # Persist to disk so it survives bot restart
    # 🐛 Fix: Compute end datetime from end_t (HH:MM), NOT from now+planned_mins.
    # now+planned_mins drifts forward on every restart because 'now' becomes the
    # restart time instead of the original session start time.
    _now = now_mmt()
    try:
        _eh, _em = map(int, end_t.split(":"))
        _end_dt = _now.replace(hour=_eh, minute=_em, second=0, microsecond=0)
    except (ValueError, AttributeError):
        _end_dt = _now + timedelta(minutes=planned_mins)
    _end_dt_iso = _end_dt.isoformat()
    persist_reminder(cid, chat_id, member_id, planned_mins, end_t, _end_dt_iso, message_thread_id,
                      total_plan_mins=_SESSION_TOTAL_MINS.get(key, planned_mins))
    # Mark DB that bot is handling reminders for this session (prevents API timer duplication)
    try:
        from bot import _psvibe_post_async
        # Set telegram_chat_id on the active booking so API timer skips
        _result = await _psvibe_post_async("bookings/mark-bot-reminder", {
            "console_id": cid, "telegram_chat_id": str(chat_id)
        })
        if _result is None:
            logger.debug("_remind_loop: mark-bot-reminder returned None for %s", cid)
    except Exception as _mark_err:
        logger.debug("_remind_loop: mark-bot-reminder failed for %s: %s", cid, _mark_err)
    # Guard: if this console is No Timer, don't run reminders
    if cid in _NO_TIMER_CONSOLES:
        logger.info("_remind_loop: %s is No Timer — exiting immediately", cid)
        return
    try:
        max_fires = 10  # ⚠️ Auto-stop after 10 fires (50 min overdue) to prevent infinite spam
        await asyncio.sleep(initial_delay)
        fire_count = 0
        while True:
            # Always check if session is still active before firing any reminder
            if cid in _NO_TIMER_CONSOLES:
                logger.info("_remind_loop: %s is No Timer — breaking", cid)
                break
            still_active = await _is_session_active(cid)
            if not still_active:
                break
            fire_count += 1
            
            # ⚠️ Max-fire guard: auto-stop after max_fires (50+ min overdue)
            if fire_count > max_fires:
                overdue_mins = (fire_count - 1) * 5
                logger.warning(
                    f"⚠️ Auto-stopping _remind_loop for {cid} after {max_fires} fires "
                    f"(~{overdue_mins} min overdue)"
                )
                # Send one final overdue warning then stop
                try:
                    _target_chat = int(STAFF_NOTIFY_CHAT) if STAFF_NOTIFY_CHAT else chat_id
                    await bot.send_message(
                        chat_id=_target_chat,
                        message_thread_id=message_thread_id or STAFF_NOTIFY_THREAD,
                        text=(
                            f"⚠️ <b>Session Overdue Alert — Auto-Stopped!</b>\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"🕹️ Console: <b>{cid}</b>\n"
                            f"👤 Member: <b>{member_id}</b>\n"
                            f"🚨 <b>{overdue_mins}+ min overdue!</b>\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"⏹️ Reminder loop auto-stopped — လက်ရှိ end လုပ်ပါ"
                        ),
                        parse_mode="HTML",
                    )
                except Exception as _final_err:
                    logger.error("_remind_loop final-warning send failed: %s", _final_err)
                break
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
                # Always read current end time + total plan from shared state (updated on extend)
                _current_end_t = _SESSION_END_TIMES.get(key, end_t)
                _current_plan = _SESSION_TOTAL_MINS.get(key, planned_mins)
                _remind_text = (
                    f"⏰ <b>Session Reminder!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🕹️ Console : <b>{cid}</b>\n"
                    f"👤 Member  : <b>{member_id}</b>\n"
                    f"⏱️ Plan    : <b>{_current_plan} mins</b>\n"
                    f"🕑 End ~   : <b>{_current_end_t}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"{_warn_line}\n"
                    f"ဆက်ကစားမည်ဆိုက ➕ Extend ကိုနှိပ်ပါ\n"
                    f"ပြီးပြီဆိုက ⏹️ <b>Sale Bot → Session End</b> မှ အဆုံးသတ်ပါ"
                )
                # Send ONLY to group chat with inline buttons
                # (single destination prevents dual-chat end/extend conflict)
                _target_chat = int(STAFF_NOTIFY_CHAT) if STAFF_NOTIFY_CHAT else chat_id
                _remind_kb = _extend_timer_kb(cid, member_id, _target_chat)
                # ⚠️ Dedup: skip if same console was reminded within the last 60s

                _now_ts = time.time()

                _last_ts = _LAST_REMINDER_SENT.get(cid, 0)

                if _now_ts - _last_ts < 60 and fire_count == 1:

                    logger.info("_remind_loop: skipping duplicate for %s (last sent %.0fs ago)", cid, _now_ts - _last_ts)

                else:

                    await bot.send_message(

                        chat_id=_target_chat,

                        message_thread_id=message_thread_id or STAFF_NOTIFY_THREAD,

                        text=_remind_text,

                        parse_mode="HTML",

                        reply_markup=_remind_kb,

                    )

                    _LAST_REMINDER_SENT[cid] = _now_ts

                    logger.info("reminder_sent: %s | fire=%d | to=%d", cid, fire_count, _target_chat)
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
            _SESSION_TOTAL_MINS.pop(key, None)
            remove_persisted_reminder(cid, chat_id)
        # Clean up No Timer tracking so next timer session works
        remove_no_timer_console(cid)

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
            message_thread_id=STAFF_NOTIFY_THREAD,
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
                f"ပြီးပြီဆိုက ⏹️ <b>Sale Bot → Session End</b> မှ အဆုံးသတ်ပါ"
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
        f"ပြီးပြီဆိုက ⏹️ <b>Sale Bot → Session End</b> မှ အဆုံးသတ်ပါ"
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
