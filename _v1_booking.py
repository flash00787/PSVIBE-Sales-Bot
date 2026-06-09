def _sbk_console_kb() -> list:
    """Return keyboard of all consoles with live+reserved status via API."""
    try:
        data = _replit_get("sheets/consoles")
        consoles = data.get("consoles", []) if isinstance(data, dict) else []
    except Exception:
        consoles = []
    if not consoles:
        # fallback to local fetch
        try:
            consoles = [{"id": c["id"], "type": c.get("type",""), "liveStatus": c.get("status","Free")}
                        for c in fetch_console_status()]
        except Exception:
            return [[c] for c in sorted(VALID_CONSOLES)] + [[BTN_BACK, BTN_CANCEL]]
    rows = []
    row  = []
    for c in sorted(consoles, key=lambda x: x["id"]):
        live = c.get("liveStatus", "Free")
        if live == "Free":
            icon = "✅"
        elif live == "Reserved":
            icon = "🟡"
        else:
            icon = "🔴"
        label = f"{c['id']} ({c.get('type','?')}) {icon}"
        row.append(label)
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([BTN_BACK, BTN_CANCEL])
    return rows


def _sbk_parse_console_label(text: str) -> tuple[str, str]:
    """Extract (console_id, console_type) from keyboard label like 'C - 01 (PS5 Pro) ✅'."""
    # Format: "C - 01 (PS5 Pro) ✅" or "C - 01 (PS5) 🔴"
    import re
    m = re.match(r"^(C\s*-\s*\d+)\s*\(([^)]+)\)", text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    cid = text.split("(")[0].strip().split("✅")[0].strip().split("🔴")[0].strip().split("🟡")[0].strip()
    return cid, "PS Console"


async def cmd_staff_book_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Booking hub: show pending bookings + navigation to confirmed bookings."""
    context.user_data["sbk_from_hub"] = True

    # Fetch counts for both statuses in parallel (sync thread)
    pending_bks   = _replit_get("bookings?status=pending") or []
    confirmed_bks = _replit_get("bookings?status=confirmed") or []

    n_pending   = len(pending_bks)   if isinstance(pending_bks,   list) else 0
    n_confirmed = len(confirmed_bks) if isinstance(confirmed_bks, list) else 0

    await update.message.reply_text(
        f"📅 *Customer Booking*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 Pending: *{n_pending}* ခု  |  ✅ Confirmed: *{n_confirmed}* ခု",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [[BTN_SBK_NEW], [BTN_SBK_CONFIRMED], [BTN_BACK_MAIN]],
            resize_keyboard=True,
        ),
    )

    if not pending_bks:
        await update.message.reply_text(
            "📋 *Pending Bookings မရှိပါ*",
            parse_mode="Markdown",
        )
        return MAIN_MENU

    await update.message.reply_text(
        f"📋 *Pending Bookings — {n_pending} ခု*\n"
        f"━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown",
    )
    for b in pending_bks:
        card = (
            f"🎫 *Booking #{b['id']}*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 {b['customerName']}  📞 {b.get('phone') or '—'}\n"
            f"📅 {b['date']}  🕐 {b['timeSlot']}\n"
            f"🎮 {b['consoleType']}  ⏱️ {b['durationMins']} mins\n"
            f"🕹️ {b.get('gameName') or '-'}"
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Approve", callback_data=f"bkm:approve:{b['id']}"),
            InlineKeyboardButton("❌ Reject",  callback_data=f"bkm:reject:{b['id']}"),
        ]])
        await update.message.reply_text(card, parse_mode="Markdown", reply_markup=kb)
    return MAIN_MENU


async def cmd_confirmed_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show upcoming confirmed bookings with Cancel button each."""
    await update.message.reply_text("⏳ Confirmed bookings စစ်နေသည်...")
    bookings = _replit_get("bookings?status=confirmed") or []
    if not isinstance(bookings, list):
        bookings = []

    now_str  = now_mmt().strftime("%H:%M")
    today_s  = now_mmt().strftime("%-m/%-d/%Y")

    # Sort: today first (upcoming slots), then future dates
    def sort_key(b):
        return (b.get("date", ""), b.get("timeSlot", ""))
    bookings = sorted(bookings, key=sort_key)

    if not bookings:
        await update.message.reply_text(
            "✅ *Confirmed Bookings မရှိပါ*",
            parse_mode="Markdown",
        )
        return MAIN_MENU

    await update.message.reply_text(
        f"✅ *Confirmed Bookings — {len(bookings)} ခု*\n"
        f"━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown",
    )

    for b in bookings[:15]:
        console_hint = b.get("consoleId") or b.get("consoleType", "?")
        is_today = b.get("date", "") == today_s
        today_tag = "  🔵 Today" if is_today else ""
        card = (
            f"✅ *Booking #{b['id']}*{today_tag}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 {b['customerName']}  📞 {b.get('phone') or '—'}\n"
            f"📅 {b['date']}  🕐 {b['timeSlot']}\n"
            f"🎮 {console_hint}  ⏱️ {b.get('durationMins', '?')} mins\n"
            f"🕹️ {b.get('gameName') or '-'}"
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚫 Cancel", callback_data=f"bkc:{b['id']}"),
        ]])
        await update.message.reply_text(card, parse_mode="Markdown", reply_markup=kb)

    return MAIN_MENU


async def cmd_staff_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point: show all consoles (free ✅ / busy 🔴) for staff advance booking."""
    from_hub = context.user_data.get("sbk_from_hub", False)
    context.user_data.clear()
    if from_hub:
        context.user_data["sbk_from_hub"] = True
    rows = _sbk_console_kb()
    await update.message.reply_text(
        "📅 *Customer Advance Booking*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "✅ = Free   🔴 = Busy\n\n"
        "🕹️ Console ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(rows, resize_keyboard=True),
    )
    return SBK_CONSOLE


async def step_sbk_console(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle console selection."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text in (BTN_BACK, BTN_BACK_MAIN):
        if context.user_data.get("sbk_from_hub"):
            return await cmd_staff_book_hub(update, context)
        return await show_admin_menu(update, context)

    cid, ctype = _sbk_parse_console_label(text)
    # validate against known consoles
    try:
        all_c = fetch_console_status()
        valid = {c["id"] for c in all_c}
    except Exception:
        valid = VALID_CONSOLES
    if cid not in valid:
        await update.message.reply_text("⚠️ Keyboard မှ Console ရွေးပေးပါ")
        return await cmd_staff_booking(update, context)

    context.user_data["sbk_console_id"]   = cid
    context.user_data["sbk_console_type"] = ctype

    # Offer member list for quick selection
    try:
        members = fetch_members()
    except Exception:
        members = []
    kb = [["👤 Guest (Walk-in)"]] + [[m] for m in members[:20]] + [[BTN_BACK, BTN_CANCEL]]
    await update.message.reply_text(
        f"🕹️ Console: <b>{cid}</b>  ({ctype})\n\n"
        "👤 Customer name ထည့်ပါ\n"
        "( Member list မှ ရွေး သို့ Manual ရိုက် )",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SBK_CUST_NAME


async def step_sbk_cust_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle customer name / member selection."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await cmd_staff_booking(update, context)

    name = "Guest" if text == "👤 Guest (Walk-in)" else text
    context.user_data["sbk_cust_name"] = name

    # Ask phone
    kb = [[BTN_SBK_SKIP_PHONE], [BTN_BACK, BTN_CANCEL]]
    await update.message.reply_text(
        f"👤 Customer: <b>{name}</b>\n\n"
        "📞 Phone number ထည့်ပါ (optional — Skip နှိပ်နိုင်)",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SBK_DATE


async def step_sbk_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone → then ask booking date."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await cmd_staff_booking(update, context)

    phone = "—" if text == BTN_SBK_SKIP_PHONE else text
    context.user_data["sbk_phone"] = phone

    # Ask date
    today    = now_mmt().date()
    tomorrow = today + timedelta(days=1)
    d2       = today + timedelta(days=2)
    def dfmt(d): return d.strftime("%-m/%-d/%Y")
    kb = [
        [dfmt(today) + " (ယနေ့)", dfmt(tomorrow) + " (မနက်ဖြန်)"],
        [dfmt(d2)],
        [BTN_SBK_CUSTOM],
        [BTN_BACK, BTN_CANCEL],
    ]
    await update.message.reply_text(
        "📅 Booking Date ရွေးပါ:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SBK_TIME


async def step_sbk_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date → then ask time slot."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        # re-ask phone
        name = context.user_data.get("sbk_cust_name", "")
        kb = [[BTN_SBK_SKIP_PHONE], [BTN_BACK, BTN_CANCEL]]
        await update.message.reply_text(
            f"👤 Customer: <b>{name}</b>\n\n📞 Phone number ထည့်ပါ:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return SBK_DATE

    if text == BTN_SBK_CUSTOM:
        await update.message.reply_text(
            "📅 ရက် ရိုက်ထည့်ပါ (format: M/D/YYYY)\nဥပမာ: 5/10/2026",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK, BTN_CANCEL]], resize_keyboard=True),
        )
        return SBK_TIME

    # Parse date from label like "5/4/2026 (ယနေ့)"
    import re as _re
    m = _re.match(r"(\d{1,2}/\d{1,2}/\d{4})", text)
    if m:
        date_str = m.group(1)
    else:
        # try direct parse e.g. "5/4/2026"
        parts = text.split("/")
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            date_str = text
        else:
            await update.message.reply_text("⚠️ ရက် format မမှန်ပါ (M/D/YYYY)")
            return SBK_TIME

    context.user_data["sbk_date"] = date_str

    # Build time slot keyboard
    slots = [
        ["10:00", "11:00", "12:00"],
        ["13:00", "14:00", "15:00"],
        ["16:00", "17:00", "18:00"],
        ["19:00", "20:00", "21:00"],
        ["22:00"],
    ]
    kb = slots + [[BTN_BACK, BTN_CANCEL]]
    await update.message.reply_text(
        f"📅 {date_str}\n\n⏰ Time Slot ရွေးပါ (HH:MM):",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SBK_DUR


async def step_sbk_dur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time slot → ask duration."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        # re-ask date
        today    = now_mmt().date()
        tomorrow = today + timedelta(days=1)
        d2       = today + timedelta(days=2)
        def dfmt(d): return d.strftime("%-m/%-d/%Y")
        kb = [
            [dfmt(today) + " (ယနေ့)", dfmt(tomorrow) + " (မနက်ဖြန်)"],
            [dfmt(d2)],
            [BTN_SBK_CUSTOM],
            [BTN_BACK, BTN_CANCEL],
        ]
        await update.message.reply_text(
            "📅 Booking Date ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return SBK_TIME

    # Validate HH:MM
    import re as _re2
    if not _re2.match(r"^\d{1,2}:\d{2}$", text):
        await update.message.reply_text("⚠️ Time format: HH:MM  (ဥပမာ: 14:30)")
        return SBK_DUR

    context.user_data["sbk_time"] = text

    kb = [
        ["30", "60", "90"],
        ["120", "150", "180"],
        ["240", "300", "360"],
        [BTN_BACK, BTN_CANCEL],
    ]
    await update.message.reply_text(
        f"⏰ {text}\n\n⏱️ Duration (မိနစ်) ရွေးပါ:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SBK_GAME


async def step_sbk_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle duration → ask game."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        # re-ask time
        slots = [
            ["10:00", "11:00", "12:00"],
            ["13:00", "14:00", "15:00"],
            ["16:00", "17:00", "18:00"],
            ["19:00", "20:00", "21:00"],
            ["22:00"],
        ]
        await update.message.reply_text(
            "⏰ Time Slot ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(slots + [[BTN_BACK, BTN_CANCEL]], resize_keyboard=True),
        )
        return SBK_DUR

    try:
        dur = int(text)
    except ValueError:
        await update.message.reply_text("⚠️ ဂဏန်းသာ ထည့်ပါ သို့ keyboard မှ ရွေးပါ")
        return SBK_GAME
    context.user_data["sbk_dur"] = dur

    # Build game keyboard
    try:
        games = fetch_games()
        game_names = [g["title"] for g in games if g.get("title")][:30]
    except Exception:
        game_names = []

    kb = [[BTN_SBK_SKIP_GAME]]
    row = []
    for g in game_names:
        row.append(g)
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([BTN_BACK, BTN_CANCEL])

    await update.message.reply_text(
        f"⏱️ Duration: <b>{dur} mins</b>\n\n"
        "🎮 Game ရွေးပါ (optional):",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SBK_CONFIRM


async def step_sbk_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """SBK_CONFIRM state — phase 1: receive game name and show summary.
       Phase 2: receive BTN_SBK_CONFIRM_BOOK and create the booking.
    """
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)

    # ── Phase 2: create booking (user pressed confirm) ─────────────────────
    if text == BTN_SBK_CONFIRM_BOOK:
        cid      = context.user_data.get("sbk_console_id", "")
        ctype    = context.user_data.get("sbk_console_type", "")
        name     = context.user_data.get("sbk_cust_name", "Guest")
        phone    = context.user_data.get("sbk_phone", "—")
        date     = context.user_data.get("sbk_date", "")
        slot     = context.user_data.get("sbk_time", "")
        dur      = context.user_data.get("sbk_dur", 60)
        game     = context.user_data.get("sbk_game", "")
        staff    = update.effective_user.full_name or "Staff"

        await update.message.reply_text("⏳ Booking ဖန်တီးနေသည်...", reply_markup=ReplyKeyboardRemove())

        payload = {
            "customerName": name,
            "phone":        phone,
            "date":         date,
            "timeSlot":     slot,
            "consoleType":  ctype,
            "consoleId":    cid,
            "durationMins": int(dur),
            "gameName":     game or None,
            "status":       "confirmed",
            "source":       "staff",
            "staffNote":    f"Console: {cid} | Booked by {staff}",
        }

        result = await asyncio.to_thread(_replit_post, "bookings", payload)
        if not result or "id" not in result:
            await update.message.reply_text(
                "❌ Booking create မအောင်မြင်ပါ\nAPI စစ်ပြီး ထပ်ကြိုးစားပါ",
            )
            return await show_main_menu(update, context)

        bk_id = result["id"]

        # Notify staff group
        if STAFF_NOTIFY_CHAT:
            notif = (
                f"📅 <b>New Staff Booking #{bk_id}</b>\n"
                f"🕹️ {cid} ({ctype})\n"
                f"👤 {name}  📞 {phone}\n"
                f"📅 {date}  ⏰ {slot}\n"
                f"⏱️ {dur} mins  🎮 {game or '—'}\n"
                f"Created by {staff}"
            )
            _notify_customer(STAFF_NOTIFY_CHAT, notif)

        # Fire n8n reminder webhook (non-blocking)
        asyncio.create_task(_post_n8n_booking_reminder(
            bk_id=bk_id, customer_name=name, phone=phone,
            console_id=cid, console_type=ctype,
            date_str=date, time_slot=slot, duration_mins=int(dur),
            tg_chat="",
        ))

        await update.message.reply_text(
            f"✅ <b>Booking #{bk_id} Created!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🕹️ Console  : <b>{cid}</b>  ({ctype})\n"
            f"👤 Customer : <b>{name}</b>  📞 {phone}\n"
            f"📅 {date}  ⏰ {slot}\n"
            f"⏱️ {dur} mins  🎮 {game or '—'}\n"
            f"Status: <b>Confirmed ✅</b>\n"
            f"{'📲 Reminder scheduled via n8n' if N8N_BOOKING_WEBHOOK else ''}",
            parse_mode="HTML",
        )
        context.user_data.clear()
        return await show_main_menu(update, context)

    # ── BTN_BACK: re-show game selection ──────────────────────────────────
    if text == BTN_BACK:
        dur = context.user_data.get("sbk_dur", 60)
        context.user_data.pop("sbk_game", None)
        try:
            games = fetch_games()
            game_names = [g["title"] for g in games if g.get("title")][:30]
        except Exception:
            game_names = []
        kb = [[BTN_SBK_SKIP_GAME]]
        row = []
        for g in game_names:
            row.append(g)
            if len(row) == 2:
                kb.append(row)
                row = []
        if row:
            kb.append(row)
        kb.append([BTN_BACK, BTN_CANCEL])
        await update.message.reply_text(
            f"⏱️ Duration: <b>{dur} mins</b>\n\n🎮 Game ရွေးပါ:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return SBK_CONFIRM

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
