"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, ApplicationHandlerStop
from telegram.constants import ParseMode
import logging, re, json, html, random

from bot import (
    CUSTOMER_BOT_TOKEN,
    _psvibe_get_async, _psvibe_patch_async, _psvibe_post_async,
    check_disc_session_conflict,  get_consoles_with_game, get_consoles_with_game_async,
    now_mmt, show_admin_menu,
)
from bot.handlers.notify import _notify_customer, get_customer_chat_id
from bot.handlers.booking_flow import _post_n8n_booking_reminder, _remind_loop, _remind_key, _REMIND_TASKS, _cancel_remind
from bot.handlers.booking import _sbk_advance_reminder


logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta

import asyncio
# show_admin_menu imported lazily in functions below



async def cmd_admin_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.handlers.admin import show_admin_menu
    await update.message.reply_text("⏳ Pending bookings စစ်နေသည်...", reply_markup=ReplyKeyboardRemove())
    bookings = await _psvibe_get_async("bookings?status=pending")
    if not bookings:
        await update.message.reply_text(
            "✅ *Pending bookings မရှိပါ*",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return await show_admin_menu(update, context)

    # Show only the 20 most recent pending bookings
    recent = bookings[:20] if len(bookings) > 20 else bookings
    total = len(bookings)

    await update.message.reply_text(
        f"📋 *Pending Bookings — {total} ခု (Showing {len(recent)} latest)*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )

    for b in recent:
        game_name_bk = (b.get('gameName') or '').strip()
        disc_warn_bk = ""
        if game_name_bk and b.get('timeSlot'):
            import asyncio as _asyncio
            disc_warn_bk = await _asyncio.to_thread(
                check_disc_session_conflict, game_name_bk, b.get('timeSlot', '?')
            )
        card = (
            f"🎫 *Booking #{b['id']}*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 {b.get('customerName', 'Unknown')}  📞 {b.get('phone', '-')}\n"
            f"📅 {b.get('date', '?')}  🕐 {b.get('timeSlot', '?')}\n"
            f"🎮 {b.get('consoleType', '-')}  ⏱️ {b.get('durationMins', '?')} mins\n"
            f"🕹️ {game_name_bk or '-'}"
            + (f"\n\n{disc_warn_bk}" if disc_warn_bk else "")
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data=f"bkm:approve:{b['id']}"),
            InlineKeyboardButton("❌ Reject",  callback_data=f"bkm:reject:{b['id']}"),
        ]])
        await update.message.reply_text(card, parse_mode="Markdown", reply_markup=kb)

    return await show_admin_menu(update, context)
async def cmd_approve_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /approve_<id> text command (fallback)."""
    cmd = update.message.text.strip()
    try:
        bk_id = int(cmd.split("_", 1)[1])
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Invalid command. Use /approve_<id>")
        return
    await _do_booking_action(bk_id, "approve", update.effective_user.full_name or "Staff",
                             reply_fn=update.message.reply_text)

async def cmd_reject_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reject_<id> text command (fallback)."""
    cmd = update.message.text.strip()
    try:
        bk_id = int(cmd.split("_", 1)[1])
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Invalid command. Use /reject_<id>")
        return
    await _do_booking_action(bk_id, "reject", update.effective_user.full_name or "Staff",
                             reply_fn=update.message.reply_text)

async def cb_booking_mgmt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline button handler for ✅/❌ on pending booking cards."""
    query = update.callback_query
    await query.answer()
    try:
        _, action, bk_id_str = query.data.split(":")
        bk_id = int(bk_id_str)
    except Exception as e:
        logger.error("cb_booking_mgmt: %s", e, exc_info=True)
        return
    staff_name = query.from_user.full_name or "Staff"

    async def edit_fn(text: str, **kw):
        # Replace the card text to show result inline
        try:
            await query.edit_message_text(text, **kw)
        except Exception as e:
            logger.error("edit_fn: %s", e, exc_info=True)
            pass

    if action == "reject":
        # Prompt for rejection reason
        await query.answer("📝 Reason ရိုက်ထည့်ပါ (သို့မဟုတ် Skip နှိပ်ပါ)", show_alert=False)

        user_id = query.from_user.id
        # Store pending reject state in bot_data (keyed by user_id) to avoid ConversationHandler conflicts
        context.bot_data[f'_reject_{user_id}'] = {
            'bk_id': bk_id,
            'staff_name': staff_name,
            'card_chat_id': query.message.chat_id,
            'card_message_id': query.message.message_id,
        }
        logger.debug("REJECT DEBUG: Set pending_reject for BK#%d (user=%d)", bk_id, user_id)

        # Send reason prompt
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭️ Skip (No Reason)", callback_data=f"bkr:skip:{bk_id}")],
        ])
        prompt = await query.message.reply_text(
            f"📋 <b>Booking #{bk_id} — Reject</b>\n\n"
            f"ဘာကြောင့် <b>Reject</b> လုပ်တာလဲ?\n"
            f"Reason ရိုက်ထည့်ပါ (သို့မဟုတ် Skip နှိပ်ပါ):",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        context.bot_data[f'_reject_{user_id}']['prompt_message_id'] = prompt.message_id
        return

    # Approve — proceed directly
    await _do_booking_action(bk_id, action, staff_name, reply_fn=edit_fn)


async def cb_reject_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Skip button when rejecting — proceed without reason."""
    query = update.callback_query
    await query.answer()
    try:
        _, _, bk_id_str = query.data.split(":")
        bk_id = int(bk_id_str)
    except Exception:
        return

    user_id = query.from_user.id
    logger.debug("REJECT DEBUG: cb_reject_skip for BK#%d (user=%d)", bk_id, user_id)
    pending = context.bot_data.pop(f'_reject_{user_id}', None)
    if not pending or pending['bk_id'] != bk_id:
        await query.edit_message_text("⚠️ Reject expired or already processed", parse_mode="HTML")
        logger.debug("REJECT DEBUG: Skip — pending_reject missing or mismatched (got bk_id=%d, expected=%s, bot_data_keys=%s)",
                       bk_id, pending.get('bk_id') if pending else 'None', list(context.bot_data.keys()))
        return

    staff_name = pending['staff_name']
    card_chat_id = pending['card_chat_id']
    card_message_id = pending['card_message_id']

    # Clean up the prompt message
    try:
        await query.message.delete()
    except Exception:
        pass

    # Edit the original booking card with reject result
    async def edit_card(text: str, **kw):
        try:
            await context.bot.edit_message_text(
                chat_id=card_chat_id,
                message_id=card_message_id,
                text=text,
                **kw
            )
        except Exception as e:
            logger.error("edit_card: %s", e, exc_info=True)

    await _do_booking_action(bk_id, "reject", staff_name, reply_fn=edit_card)


async def handle_reject_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for rejection reason."""
    user_id = update.effective_user.id if update.effective_user else 0
    pending = context.bot_data.get(f'_reject_{user_id}')
    logger.debug("REJECT DEBUG: handle_reject_reason called, user=%d, pending=%s, text=%s",
                user_id, pending is not None,
                (update.message.text or '')[:50] if update.message else 'None')
    if not pending:
        return  # Not in reject-reason mode — let other handlers process

    bk_id = pending['bk_id']
    staff_name = pending['staff_name']
    card_chat_id = pending['card_chat_id']
    card_message_id = pending['card_message_id']
    prompt_message_id = pending.get('prompt_message_id')
    reason = update.message.text.strip() if update.message and update.message.text else ""

    # Clear pending state immediately
    context.bot_data.pop(f'_reject_{user_id}', None)
    logger.debug("REJECT DEBUG: Processing reject BK#%d, reason=%s", bk_id, reason[:50])

    # Clean up the prompt message
    if prompt_message_id:
        try:
            await context.bot.delete_message(chat_id=update.message.chat_id, message_id=prompt_message_id)
        except Exception:
            pass

    # Edit the original booking card with reject result
    async def edit_card(text: str, **kw):
        try:
            await context.bot.edit_message_text(
                chat_id=card_chat_id,
                message_id=card_message_id,
                text=text,
                **kw
            )
        except Exception as e:
            logger.error("edit_card: %s", e, exc_info=True)

    await _do_booking_action(bk_id, "reject", staff_name, reply_fn=edit_card, reject_reason=reason)
    raise ApplicationHandlerStop()  # Prevent ConversationHandler from processing

async def _send_checkin_notification(tg_chat: str, booking_id: int):
    """Notify customer that they've checked in."""
    msg = (
        f"\U0001f389 *Welcome to PS VIBE!* \ud83c\udfae\n\n"
        f"\u2705 Booking #{booking_id} \u2014 Checked In!\n"
        f"Staff will start your session shortly. Enjoy! \ud83c\udf89"
    )
    try:
        from bot import CUSTOMER_BOT_TOKEN
        if tg_chat and CUSTOMER_BOT_TOKEN:
            import json
            import urllib.request
            data = json.dumps({"chat_id": tg_chat, "text": msg, "parse_mode": "Markdown"}).encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{CUSTOMER_BOT_TOKEN}/sendMessage",
                data=data, headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass

async def cb_checkin_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Staff checks in a customer — marks booking as checked_in directly.
    Console assignment happens later during Session Start if needed."""
    query = update.callback_query
    await query.answer()
    try:
        _, _, bk_id_str = query.data.split(":")
        bk_id = int(bk_id_str)
    except Exception as e:
        logger.error("cb_checkin_booking: %s", e, exc_info=True)
        return

    # Fetch booking to show customer name
    bk_data = await _psvibe_get_async(f"bookings/{bk_id}") or {}
    if isinstance(bk_data, dict):
        if "booking" in bk_data:
            bk_data = bk_data["booking"]
        elif bk_data.get("data") and isinstance(bk_data["data"], dict):
            inner = bk_data["data"]
            if "booking" in inner:
                bk_data = inner["booking"]
            else:
                bk_data = inner

    name = bk_data.get("customerName", "") or bk_data.get("phone", "?")

    await query.edit_message_text(
        f"⏳ Checking in Booking #{bk_id} — {name}...",
        parse_mode="Markdown",
    )

    # Direct check-in — no console selection
    payload = {"id": bk_id}
    try:
        result = await _psvibe_post_async("bookings/checkin", payload)
    except Exception as e:
        await query.edit_message_text(f"❌ *Check-in failed:* {e}", parse_mode="Markdown")
        return

    if result and isinstance(result, dict):
        tg_chat = result.get("telegram_chat_id", "")
        await query.edit_message_text(
            f"✅ *Checked In — Booking #{bk_id}*\n"
            f"👤 {name}\n"
            f"\n_Session Start တွင် Console နှင့် ချိတ်ဆက်နိုင်ပါသည်_",
            parse_mode="Markdown",
        )
        # Send notification
        if tg_chat:
            asyncio.create_task(_send_checkin_notification(tg_chat, bk_id))
    else:
        await query.edit_message_text(
            f"❌ *Check-in failed* for Booking #{bk_id}",
            parse_mode="Markdown",
        )


async def cb_checkin_select_console(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle console selection during checkin. Proceed to API call."""
    query = update.callback_query
    await query.answer()
    try:
        _, _, bk_id_str, console_id = query.data.split(":", 3)
        bk_id = int(bk_id_str)
    except Exception as e:
        logger.error("cb_checkin_select_console: %s", e, exc_info=True)
        return

    if console_id == "cancel":
        await query.edit_message_text("↩️ Check-in cancelled.", parse_mode="Markdown")
        return

    staff_name = query.from_user.full_name or "Staff"

    # Build payload — include consoleId if not skipped
    payload = {"id": bk_id}
    if console_id != "skip":
        payload["consoleId"] = console_id

    await query.edit_message_text(
        f"⏳ Checking in Booking #{bk_id}...{"  🖥️ " + console_id if console_id != "skip" else ""}",
        parse_mode="Markdown",
    )

    try:
        result = await _psvibe_post_async("bookings/checkin", payload)
    except Exception as e:
        await query.edit_message_text(f"\u274c *Check-in failed:* {e}", parse_mode="Markdown")
        return

    if result and isinstance(result, dict):
        tg_chat = result.get("telegram_chat_id", "")
        cid_line = f"\n🖥️ Console: {console_id}" if console_id != "skip" else ""

        await query.edit_message_text(
            f"\u2705 *Customer Checked In!*\n"
            f"Booking #{bk_id}{cid_line}\n"
            f"Done by: {staff_name}\n\n"
            f"\U0001f4cb Session \u1019\u1005\u101e\u1031\u1038\u1015\u102b\u104b *Start Session* \u1014\u103e\u102d\u1015\u103a\u1015\u102b",
            parse_mode="Markdown",
        )

        # NO timer scheduling here — timer starts only when session starts (separate action)

        if tg_chat:
            asyncio.create_task(_send_checkin_notification(tg_chat, bk_id))
    else:
        err_msg = (result or {}).get("error") or "Unknown error"
        await query.edit_message_text(
            f"\u274c *Check-in failed:* {err_msg}",
            parse_mode="Markdown",
        )


async def _do_booking_action(bk_id: int, action: str, staff_name: str, reply_fn, reject_reason: str = ""):
    """Shared approve/reject logic — updates DB, replies, notifies customer."""
    new_status = "confirmed" if action == "approve" else "rejected"

    # Fetch booking info early — needed for both approve and reject paths
    bk_data = await _psvibe_get_async(f"bookings/{bk_id}")
    bk_info = bk_data or {}
    # Unwrap {"booking": {...}} or {"data": {"booking": {...}}} envelope
    if isinstance(bk_info, dict):
        if "booking" in bk_info:
            bk_info = bk_info["booking"]
        elif bk_info.get("data") and isinstance(bk_info["data"], dict):
            inner = bk_info["data"]
            if "booking" in inner:
                bk_info = inner["booking"]
            else:
                bk_info = inner

    # Build staffNote with optional reject reason
    if action == "reject" and reject_reason.strip():
        staff_note = f"Rejected by {staff_name}: {reject_reason.strip()}"
    else:
        staff_note = f"{'Approved' if action == 'approve' else 'Rejected'} by {staff_name}"

    patch_body: dict = {
        "status":    new_status,
        "staffNote": staff_note,
    }

    # Auto-assign a free console of the matching type on approval
    # If booking has a gameName, prefer consoles that have the game installed
    assigned_console = ""
    install_warn     = ""
    if action == "approve":
        console_type = bk_info.get("consoleType", "")
        game_name    = (bk_info.get("gameName") or "").strip()
        # ✅ Respect customer's chosen console (if any)
        customer_console = (bk_info.get("consoleId") or bk_info.get("console_id") or "").strip()

        if console_type:
            from bot import fetch_console_status
            consoles_tmp = fetch_console_status()
            consoles = [{"id":c["id"],"type":c.get("type",""),"liveStatus":c.get("status","Free")} for c in consoles_tmp]
            free = [c for c in consoles
                    if c.get("type", "").strip() == console_type
                    and c.get("liveStatus", "").lower() == "free"]

            chosen = None
            bk_date = bk_info.get("date", "")
            bk_time = bk_info.get("timeSlot", "")
            bk_dur = int(bk_info.get("durationMins", 60))

            # Fetch game-installed consoles early (needed for both paths)
            consoles_with_game = []
            if game_name:
                consoles_with_game = await get_consoles_with_game_async(game_name)

            # 🔑 Priority 1: Customer-chosen console — verify & use if free + no conflict
            if customer_console:
                cust_upper = customer_console.upper()
                matched = [c for c in free if c["id"].upper() == cust_upper]
                if matched:
                    cf = await _psvibe_post_async("booking-conflicts", {
                        "date": bk_date,
                        "time_slot": bk_time,
                        "duration_mins": bk_dur,
                        "console_id": customer_console,
                        "exclude_booking_id": bk_id,
                    })
                    if cf and not cf.get("has_conflict"):
                        chosen = matched[0]
                        logger.info("Approve BK#%d: using customer-chosen console %s", bk_id, customer_console)
                    else:
                        logger.warning("Approve BK#%d: customer-chosen %s has conflict or not free — falling back to auto-assign", bk_id, customer_console)
                else:
                    logger.warning("Approve BK#%d: customer-chosen %s not free (type=%s) — falling back to auto-assign", bk_id, customer_console, console_type)

            # Priority 2: Auto-assign (only if customer console unavailable)
            if not chosen:
                # Build candidate list: game-installed consoles first, then rest
                candidates = []
                if game_name:
                    cw_upper = {c.get("console_id","").upper() for c in consoles_with_game if isinstance(c, dict)}
                    game_free = [c for c in free if c["id"].upper() in cw_upper]
                    other_free = [c for c in free if c["id"].upper() not in cw_upper]
                    random.shuffle(game_free)
                    random.shuffle(other_free)
                    candidates = game_free + other_free
                else:
                    candidates = list(free)
                    random.shuffle(candidates)

                # ✅ Conflict-aware auto-assign: check each candidate against existing bookings
                for candidate in candidates:
                    cid = candidate["id"]
                    cf = await _psvibe_post_async("booking-conflicts", {
                        "date": bk_date,
                        "time_slot": bk_time,
                        "duration_mins": bk_dur,
                        "console_id": cid,
                        "exclude_booking_id": bk_id,
                    })
                    if cf and not cf.get("has_conflict"):
                        chosen = candidate
                        break
                    elif cf and cf.get("has_conflict"):
                        logger.info("Auto-assign: %s has conflict for BK#%d — skipping", cid, bk_id)
                if not chosen and candidates:
                    logger.warning("Auto-assign: ALL %d free consoles have conflicts for BK#%d", len(candidates), bk_id)

            if chosen:
                # Game-install warnings (if not in game-installed list)
                if game_name:
                    cw_upper = {c.get("console_id","").upper() for c in consoles_with_game if isinstance(c, dict)}
                    if chosen["id"].upper() not in cw_upper:
                        if consoles_with_game:
                            install_warn = (
                                f"\n⚠️ <b>「{game_name}」 Install စစ်ဆေးပါ!</b>\n"
                                f"Free console ({chosen['id']}) မှာ install မရှိပါ\n"
                                f"Install ရှိသော console: <b>{', '.join(c.get('console_id','') for c in consoles_with_game)}</b>\n"
                                f"ကြိုတင် Install / SSD transfer ပြင်ဆင်ပါ"
                            )
                        else:
                            install_warn = (
                                f"\n⚠️ <b>「{game_name}」 မည်သည့် Console မှ Install မရှိ!</b>\n"
                                f"Session မတိုင်မီ Install ပြင်ဆင်ပါ"
                            )
                patch_body["consoleId"] = chosen["id"]
                assigned_console = chosen["id"]
                import bot as _b; _b._BK_TS = 0.0  # invalidate booking cache

    result = await _psvibe_patch_async(
        f"bookings/{bk_id}/status",
        patch_body,
    )
    if not result:
        await reply_fn(f"❌ Booking #{bk_id} ကို update မရပါ")
        return

    # Cancel any pending 30-min advance reminder
    try:
        _r = await _psvibe_post_async("webhook/booking-reminder/cancel", {"bk_id": bk_id})
        logger.debug("_do_booking_action: reminder cancel bk#%d → %s", bk_id, _r)
    except Exception:
        pass

    # Check for conflict (another staff already approved/rejected)
    if isinstance(result, dict) and result.get("conflict"):
        conflict_status = result.get("current_status", "processed")
        await reply_fn(
            f"⚠️ Booking #{bk_id} ကို အခြား staff မှ {conflict_status} လုပ်ပြီးပါပြီ။",
            parse_mode="HTML",
        )
        return
    if isinstance(result, dict) and result.get("status_code") == 409:
        # Booking already processed — fetch current status and update the card
        try:
            current = await _psvibe_get_async(f"bookings/{bk_id}")
            if current:
                cur_status = current.get("status", "processed").replace("rejected", "Rejected").replace("confirmed", "Confirmed")
                cur_staff = current.get("notes", "").replace("Rejected by ", "").replace("Approved by ", "") or "Staff"
                customer_name = html.escape(current.get('customerName', 'Unknown'))
                msg = (
                    f"⚠️ <b>Booking #{bk_id}</b> — လက်ရှိ <b>{cur_status}</b> ဖြစ်ပြီးပါပြီ\n"
                    f"👤 {customer_name}  📅 {current.get('date', '?')}  🕐 {current.get('timeSlot', '?')}\n"
                    f"<i>By {cur_staff}</i>"
                )
                await reply_fn(msg, parse_mode="HTML")
                return
        except Exception:
            pass
        await reply_fn(
            f"⚠️ Booking #{bk_id} ကို အခြား staff မှ ပြောင်းလဲပြီးပါပြီ။ ထပ်စစ်ဆေးပါ။",
            parse_mode="HTML",
        )
        return

    # Use bk_info (from GET /api/bookings/{id}) for all customer fields.
    # PATCH result only returns {booking_id, status} — no customer data.
    if action == "approve":
        customer_name = html.escape(bk_info.get('customerName', 'Unknown'))
        customer_phone = html.escape(bk_info.get('phone', '-'))
        console_line = f"\n🖥️ Console: <b>{assigned_console}</b>" if assigned_console else ""
        game_line    = f"\n🕹️ Game: <b>{bk_info.get('gameName') or '—'}</b>" if bk_info.get("gameName") else ""
        msg = (
            f"✅ <b>Booking #{bk_id} Confirmed!</b>\n"
            f"👤 {customer_name}  📞 {customer_phone}\n"
            f"📅 {bk_info.get('date', '?')}  🕐 {bk_info.get('timeSlot', '?')}\n"
            f"🎮 {bk_info.get('consoleType', '-')}  ⏱️ {bk_info.get('durationMins', '?')} mins"
            f"{game_line}{console_line}\n"
            f"<i>Approved by {staff_name}</i>"
            f"{install_warn}"
        )
    else:
        customer_name = html.escape(bk_info.get('customerName', 'Unknown'))
        reason_line = f"\n📝 Reason: <i>{html.escape(reject_reason.strip())}</i>" if reject_reason.strip() else ""
        msg = (
            f"❌ <b>Booking #{bk_id} Rejected</b>\n"
            f"👤 {customer_name}  📅 {bk_info.get('date', '?')}  🕐 {bk_info.get('timeSlot', '?')}"
            f"{reason_line}\n"
            f"<i>Rejected by {staff_name}</i>"
        )
    await reply_fn(msg, parse_mode="HTML")

    # Notify customer via customer bot if we have their chat_id
    # IMPORTANT: Use bk_info (from the GET /api/bookings/{id} call earlier), NOT the
    # PATCH result (which only returns {booking_id, status})
    tg_chat = bk_info.get("telegramChatId") or ""
    # Fallback: look up chat_id from member data if not in booking data
    if not tg_chat:
        member_id = bk_info.get("memberId") or ""
        if member_id:
            try:
                tg_chat = get_customer_chat_id(member_id) or ""
            except Exception:
                pass  # graceful fail
    if tg_chat and CUSTOMER_BOT_TOKEN:
        if action == "approve":
            console_line = f"\n🖥️ Console: <b>{assigned_console}</b>" if assigned_console else ""
            cust_msg = (
                "မင်္ဂလာပါ 🙏\n\n"
                f"သင်၏ Booking (#{bk_id}) ကို အတည်ပြုပြီးပါပြီ။\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📅 {bk_info.get('date', '?')}  🕐 {bk_info.get('timeSlot', '?')}\n"
                f"🎮 {bk_info.get('consoleType', '')}  ⏱️ {bk_info.get('durationMins', '?')} mins{console_line}\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"PS Vibe မှ ကြိုဆိုပါသည်! ✨\n"
                f"ကျေးဇူးတင်ပါတယ်"
            )
        else:
            reason_line = f"\n📝 Reason: {html.escape(reject_reason.strip())}" if reject_reason.strip() else ""
            cust_msg = (
                f"😔 <b>Booking #{bk_id} Rejected</b>\n\n"
                f"📅 {bk_info.get('date', '?')}  🕐 {bk_info.get('timeSlot', '?')}"
                f"{reason_line}\n\n"
                f"အဆင်မပြေသဖြင့် တောင်းပန်ပါသည်။ နောက်ထပ် booking ထပ်မံလုပ်နိုင်ပါသည်။\n"
                f"📞 ဆက်သွယ်ရန် @psvibeofficial"
            )
        await asyncio.to_thread(_notify_customer, tg_chat, cust_msg)

    # Mark console as Scheduled via API so status board reflects it
    if assigned_console:
        try:
            # The approve PATCH already updated the booking status.
            # The console status board shows Active/Free based on console_status table.
            # No need for a separate gspread append — the booking data is in MySQL.
            logger.info("Booking #%d approved, console=%s", bk_id, assigned_console)
        except Exception as e:
            logger.warning("Console_Booking post-approval update: %s", e)

    # Fire n8n reminder + bot-based fallback when customer booking approved
    if action == "approve":
        asyncio.create_task(_post_n8n_booking_reminder(
            bk_id=bk_id,
            customer_name=bk_info.get("customerName", ""),
            phone=bk_info.get("phone", ""),
            console_id=bk_info.get("consoleId") or bk_info.get("console_id", ""),
            console_type=bk_info.get("consoleType", ""),
            date_str=bk_info.get("date", ""),
            time_slot=bk_info.get("timeSlot", ""),
            duration_mins=int(bk_info.get("durationMins") or 60),
            tg_chat=tg_chat,
        ))
        # Bot-based 30-min advance reminder fallback (works even if n8n is down)
        from bot import app as _app
        asyncio.create_task(_sbk_advance_reminder(
            _app.bot, booking_id=bk_id, cid=bk_info.get("consoleId") or bk_info.get("console_id", ""),
            ctype=bk_info.get("consoleType", ""),
            name=bk_info.get("customerName", ""), phone=bk_info.get("phone", ""),
            date_str=bk_info.get("date", ""), time_str=bk_info.get("timeSlot", ""),
            dur=int(bk_info.get("durationMins") or 60),
            game=bk_info.get("gameName", ""), staff=staff_name,
            tg_chat=tg_chat,
        ))
