
    # ── Phase 1: receive game name, show summary ───────────────────────────
    game = "" if text == BTN_SBK_SKIP_GAME else text
    context.user_data["sbk_game"] = game

    cid   = context.user_data.get("sbk_console_id", "")
    ctype = context.user_data.get("sbk_console_type", "")
    name  = context.user_data.get("sbk_cust_name", "")
    phone = context.user_data.get("sbk_phone", "—")
    date  = context.user_data.get("sbk_date", "")
    slot  = context.user_data.get("sbk_time", "")
    dur   = context.user_data.get("sbk_dur", 0)

    # ── SSD transfer check ─────────────────────────────────────────────────
    ssd_warning = ""
    context.user_data["sbk_needs_ssd"] = False
    if game:
        installed = await asyncio.to_thread(get_games_on_console, cid)
        installed_lower = [g.lower() for g in installed]
        if game.lower() not in installed_lower:
            # check if game exists on any console (installed anywhere)
            consoles_with_game = await asyncio.to_thread(get_consoles_with_game, game)
            ssd_consoles = [
                r["console_id"] for r in fetch_console_games()
                if r["game_title"].lower() == game.lower()
                and r["install_type"] == "Portable SSD"
            ]
            if consoles_with_game:
                context.user_data["sbk_needs_ssd"] = True
                ssd_warning = (
                    f"\n⚠️ <b>SSD Transfer လိုသည်!</b>\n"
                    f"「{game}」 ကို {cid} မှာ Install မရှိပါ\n"
                    f"{'🔌 SSD (' + ', '.join(ssd_consoles) + ') မှ transfer လိုမည်' if ssd_consoles else '📋 Install မှတ်တမ်း စစ်ဆေးပါ'}\n"
                )
            else:
                ssd_warning = f"\n📝 <i>「{game}」 Install မှတ်တမ်း မရှိသေးပါ</i>\n"

    summary = (
        f"📋 <b>Booking Summary — စစ်ဆေးပါ</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕹️ Console  : <b>{cid}</b>  ({ctype})\n"
        f"👤 Customer : <b>{name}</b>\n"
        f"📞 Phone    : {phone}\n"
        f"📅 Date     : <b>{date}</b>\n"
        f"⏰ Time     : <b>{slot}</b>\n"
        f"⏱️ Duration : <b>{dur} mins</b>\n"
        f"🎮 Game     : {game or '—'}"
        f"{ssd_warning}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"ဤ booking ကို create မည်လား?"
    )
    kb = [[BTN_SBK_CONFIRM_BOOK], [BTN_BACK, BTN_CANCEL]]
    await update.message.reply_text(
        summary, parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SBK_CONFIRM


# ═════════════════════════════════════════
#  BOOKING MANAGEMENT (staff side)
# ═════════════════════════════════════════

def _notify_customer(chat_id_or_phone: str, text: str):
    """Send Telegram message via customer bot token to notify customer."""
    if not CUSTOMER_BOT_TOKEN or not chat_id_or_phone:
        return
    try:
        import urllib.request as _req
        payload = json.dumps({
            "chat_id": chat_id_or_phone,
            "text": text,
            "parse_mode": "HTML",
        }).encode()
        r = _req.Request(
            f"https://api.telegram.org/bot{CUSTOMER_BOT_TOKEN}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        _req.urlopen(r, timeout=10)
    except Exception as e:
        logging.warning("customer notify failed: %s", e)


def get_customer_chat_id(member_id: str) -> str | None:
    """Look up most-recent Telegram chat_id for a member from bookings store."""
    try:
        bks = _replit_get(f"bookings?memberId={member_id}")
        if bks:
            for b in bks:
                cid = (b.get("telegramChatId") or b.get("telegram_chat_id") or "").strip()
                if cid:
                    return cid
    except Exception as e:
        logging.warning("get_customer_chat_id %s: %s", member_id, e)
    return None


async def _check_low_balance_alert(member_id: str, console_id: str) -> None:
    """Wait for Sheet formula to settle, then send low-balance alert to customer."""
    try:
        await asyncio.sleep(7)
        balance = await asyncio.to_thread(fetch_balance_mins, member_id)
        threshold = int(os.environ.get("LOW_BALANCE_THRESHOLD", "120"))
        if balance >= threshold:
            return
        chat_id = await asyncio.to_thread(get_customer_chat_id, member_id)
        if not chat_id:
            return
        msg = (
            f"⚠️ <b>PS VIBE — Balance နည်းလာပြီ!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💳 Member: <code>{member_id}</code>\n"
            f"🎮 လက်ကျန် Balance: <b>{balance} မိနစ်</b>\n"
            f"⏱️ PS5 ဆိုပါက {balance} မိနစ် ကစားနိုင်သေးသည်\n"
            f"\n"
            f"💰 ဆက်ကစားနိုင်ရန် Top-up လုပ်ပါ 👇\n"
            f"/topup"
        )
        await asyncio.to_thread(_notify_customer, chat_id, msg)
        logging.info("low_balance_alert sent: member=%s balance=%d", member_id, balance)
    except Exception as e:
        logging.warning("_check_low_balance_alert %s: %s", member_id, e)


async def cmd_admin_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pending bookings — each as a separate card with ✅/❌ inline buttons."""
    await update.message.reply_text("⏳ Pending bookings စစ်နေသည်...", reply_markup=ReplyKeyboardRemove())
    bookings = _replit_get("bookings?status=pending")
    if not bookings:
        await update.message.reply_text(
            "✅ *Pending bookings မရှိပါ*",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return await show_admin_menu(update, context)

    await update.message.reply_text(
        f"📋 *Pending Bookings — {len(bookings)} ခု*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )

    for b in bookings:
        card = (
            f"🎫 *Booking #{b['id']}*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 {b['customerName']}  📞 {b['phone']}\n"
            f"📅 {b['date']}  🕐 {b['timeSlot']}\n"
            f"🎮 {b['consoleType']}  ⏱️ {b['durationMins']} mins\n"
            f"🕹️ {b.get('gameName') or '-'}"
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
    except Exception:
        return
    staff_name = query.from_user.full_name or "Staff"

    async def edit_fn(text: str, **kw):
        # Replace the card text to show result inline
        try:
            await query.edit_message_text(text, **kw)
        except Exception:
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
