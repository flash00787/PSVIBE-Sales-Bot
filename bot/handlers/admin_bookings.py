"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json

from bot import (
    CUSTOMER_BOT_TOKEN, _replit_get, _replit_patch,
    check_disc_session_conflict, get_booking_sh, get_consoles_with_game,
    now_mmt, show_admin_menu,
)
from bot.handlers.notify import _notify_customer, get_customer_chat_id
from bot.handlers.booking_flow import _post_n8n_booking_reminder


logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta

import asyncio
# show_admin_menu imported lazily in functions below



async def cmd_admin_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from bot.handlers.admin import show_admin_menu
    await update.message.reply_text("⏳ Pending bookings စစ်နေသည်...", reply_markup=ReplyKeyboardRemove())
    bookings = _replit_get("bookings?status=pending")
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

    await _do_booking_action(bk_id, action, staff_name, reply_fn=edit_fn)

async def _do_booking_action(bk_id: int, action: str, staff_name: str, reply_fn):
    """Shared approve/reject logic — updates DB, replies, notifies customer."""
    new_status = "confirmed" if action == "approve" else "rejected"

    patch_body: dict = {
        "status":    new_status,
        "staffNote": f"{'Approved' if action == 'approve' else 'Rejected'} by {staff_name}",
    }

    # Auto-assign a free console of the matching type on approval
    # If booking has a gameName, prefer consoles that have the game installed
    assigned_console = ""
    install_warn     = ""
    if action == "approve":
        bk_data      = await asyncio.to_thread(_replit_get, f"bookings/{bk_id}")
        bk_info      = bk_data or {}
        # Unwrap {"data": {"booking": {...}}} envelope
        if isinstance(bk_info, dict) and bk_info.get("data") and isinstance(bk_info["data"], dict):
            inner = bk_info["data"]
            if "booking" in inner:
                bk_info = inner["booking"]
            else:
                bk_info = inner
        console_type = bk_info.get("consoleType", "")
        game_name    = (bk_info.get("gameName") or "").strip()

        if console_type:
            consoles_data = await asyncio.to_thread(_replit_get, "sheets/consoles")
            consoles      = (consoles_data or {}).get("consoles", []) if consoles_data else []
            free = [c for c in consoles
                    if c.get("type", "").strip() == console_type
                    and c.get("liveStatus", "").lower() == "free"]

            chosen = None
            if free and game_name:
                # Prefer a free console that already has the game installed
                consoles_with_game = await asyncio.to_thread(get_consoles_with_game, game_name)
                cw_upper  = {c.upper() for c in consoles_with_game}
                game_free = [c for c in free if c["id"].upper() in cw_upper]

                if game_free:
                    chosen = game_free[0]
                else:
                    # Fall back to first free console, but warn staff
                    chosen = free[0]
                    if consoles_with_game:
                        install_warn = (
                            f"\n⚠️ <b>「{game_name}」 Install စစ်ဆေးပါ!</b>\n"
                            f"Free console ({chosen['id']}) မှာ install မရှိပါ\n"
                            f"Install ရှိသော console: <b>{', '.join(consoles_with_game)}</b>\n"
                            f"ကြိုတင် Install / SSD transfer ပြင်ဆင်ပါ"
                        )
                    else:
                        install_warn = (
                            f"\n⚠️ <b>「{game_name}」 မည်သည့် Console မှ Install မရှိ!</b>\n"
                            f"Session မတိုင်မီ Install ပြင်ဆင်ပါ"
                        )
            elif free:
                chosen = free[0]

            if chosen:
                patch_body["consoleId"] = chosen["id"]
                assigned_console        = chosen["id"]
                import bot as _b; _b._BK_TS = 0.0  # invalidate booking cache so status reflects new reservation

    result = await asyncio.to_thread(
        _replit_patch,
        f"bookings/{bk_id}/status",
        patch_body,
    )
    if not result:
        await reply_fn(f"❌ Booking #{bk_id} ကို update မရပါ")
        return

    # Unwrap {"data": {"booking": {...}}} envelope
    if isinstance(result, dict):
        data_outer = result.get("data") or {}
        if isinstance(data_outer, dict) and "booking" in data_outer:
            b = data_outer["booking"]
        elif isinstance(data_outer, dict) and "bookings" in data_outer:
            b = data_outer["bookings"][0] if data_outer["bookings"] else result
        else:
            b = result
    else:
        b = result
    if action == "approve":
        console_line = f"\n🖥️ Console: <b>{assigned_console}</b>" if assigned_console else ""
        game_line    = f"\n🕹️ Game: <b>{b.get('gameName') or '—'}</b>" if b.get("gameName") else ""
        msg = (
            f"✅ <b>Booking #{bk_id} Confirmed!</b>\n"
            f"👤 {b.get('customerName', 'Unknown')}  📞 {b.get('phone', '-')}\n"
            f"📅 {b.get('date', '?')}  🕐 {b.get('timeSlot', '?')}\n"
            f"🎮 {b.get('consoleType', '-')}  ⏱️ {b.get('durationMins', '?')} mins"
            f"{game_line}{console_line}\n"
            f"<i>Approved by {staff_name}</i>"
            f"{install_warn}"
        )
    else:
        msg = (
            f"❌ <b>Booking #{bk_id} Rejected</b>\n"
            f"👤 {b.get('customerName', 'Unknown')}  📅 {b.get('date', '?')}  🕐 {b.get('timeSlot', '?')}\n"
            f"<i>Rejected by {staff_name}</i>"
        )
    await reply_fn(msg, parse_mode="HTML")

    # Notify customer via customer bot if we have their chat_id
    tg_chat = b.get("telegramChatId") or ""
    # Fallback: look up chat_id from member data if not in booking data
    if not tg_chat:
        member_id = b.get("memberId") or ""
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
                f"📅 {b.get('date', '?')}  🕐 {b.get('timeSlot', '?')}\n"
                f"🎮 {b.get('consoleType', '')}  ⏱️ {b.get('durationMins', '?')} mins{console_line}\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"PS Vibe မှ ကြိုဆိုပါသည်! ✨\n"
                f"ကျေးဇူးတင်ပါတယ်"
            )
        else:
            cust_msg = (
                f"😔 <b>Booking #{bk_id} Rejected</b>\n\n"
                f"📅 {b.get('date', '?')}  🕐 {b.get('timeSlot', '?')}\n\n"
                f"အဆင်မပြေသဖြင့် တောင်းပန်ပါသည်။ နောက်ထပ် booking ထပ်မံလုပ်နိုင်ပါသည်။\n"
                f"📞 ဆက်သွယ်ရန် @psvibeofficial"
            )
        await asyncio.to_thread(_notify_customer, tg_chat, cust_msg)

    # Write Scheduled row to Console_Booking so console appears busy in status board
    if assigned_console:
        try:
            _sched_sh = get_booking_sh()
            _sched_now = now_mmt()
            _date_str = _sched_now.strftime("%-m/%-d/%Y")
            _sched_id = f"BK-{_sched_now.strftime('%Y%m%d')}-{assigned_console.replace(' ','').replace('-','')}-S{_sched_now.strftime('%H%M')}"
            _sched_sh.append_row([
                _sched_id, _date_str, assigned_console,
                b.get("customerName", "") or b.get("memberId", ""),
                b.get("timeSlot", ""), "", "Scheduled",
                staff_name, f"API_BK#{bk_id}"
            ], value_input_option="USER_ENTERED")
            logger.info("Console %s marked as Scheduled (API BK#%d)", assigned_console, bk_id)
        except Exception as e:
            logger.warning("Console_Booking Scheduled write failed: %s", e, exc_info=True)

    # Fire n8n reminder when customer booking approved
    if action == "approve":
        asyncio.create_task(_post_n8n_booking_reminder(
            bk_id=bk_id,
            customer_name=b.get("customerName", ""),
            phone=b.get("phone", ""),
            console_id=b.get("consoleId") or "",
            console_type=b.get("consoleType", ""),
            date_str=b.get("date", ""),
            time_slot=b.get("timeSlot", ""),
            duration_mins=int(b.get("durationMins") or 60),
            tg_chat=tg_chat,
        ))
