        else:
            member_id = text  # allow free-text (walk-in not in sheet)

    try:
        staff_list = fetch_staff_names()
        staff = staff_list[0] if len(staff_list) == 1 else context.user_data.get("staff_name", "")
    except Exception:
        staff = context.user_data.get("staff_name", "")

    # ── Duplicate session guard (non-guest only) ─────────────────────────
    if member_id not in ("Guest", "0 (Guest)"):
        try:
            all_consoles = fetch_console_status()
        except Exception:
            all_consoles = []
        existing = [
            c for c in all_consoles
            if c.get("member") == member_id and c.get("status") in ("Active", "Scheduled")
        ]
        if existing:
            # Build list of all active sessions for this member
            session_lines = []
            for ex in existing:
                s = ex.get("start", "?")
                _, dfmt = calc_duration(s) if s and s != "?" else (0, "?")
                session_lines.append(f"🕹️ <b>{ex['id']}</b>  |  🕐 {s} ({dfmt})")
            sessions_text = "\n".join(session_lines)
            # Store pending booking params for the confirm handler
            context.user_data["bk_pending_member"] = member_id
            context.user_data["bk_pending_staff"]  = staff
            await update.message.reply_text(
                f"⚠️ <b>ထပ်နေသော Session {len(existing)} ခုရှိသည်!</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 Member  : <b>{member_id}</b>\n"
                f"{sessions_text}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"ဒီ member ကို <b>{cid}</b> မှာ ထပ် session ဖွင့်မည်လား?",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(
                    [[BTN_BOOK_PROCEED], [BTN_NO_RESELECT]],
                    resize_keyboard=True,
                ),
            )
            return BOOK_DUP_WARN
    # ────────────────────────────────────────────────────────────────────

    # Save resolved member+staff and ask which game first
    context.user_data["bk_member"] = member_id
    context.user_data["bk_staff"]  = staff
    return await prompt_book_game(update, context)


async def prompt_book_game(update, context):
    """Ask which game the customer will play this session.
    Only shows games installed on the selected console.
    Offers SSD Transfer button if game is not yet installed.
    """
    cid       = context.user_data.get("bk_console", "")
    member_id = context.user_data.get("bk_member", "Guest")
    installed = await asyncio.to_thread(get_games_on_console, cid)
    kb_rows: list = []
    if installed:
        row: list = []
        for t in installed:
            row.append(t)
            if len(row) == 2:
                kb_rows.append(row)
                row = []
        if row:
            kb_rows.append(row)
        note = f"📋 <b>{cid}</b> တွင် ထည့်ထားသော ဂိမ်း {len(installed)} ခု"
    else:
        note = f"⚠️ <b>{cid}</b> တွင် ဂိမ်း မထည့်ရသေးပါ — SSD မှ Transfer ဦးလုပ်ပါ"
    kb_rows.append([BTN_SSD_TRANSFER])
    kb_rows.append([BTN_SKIP_GAME])
    kb_rows.append([BTN_BACK, BTN_CANCEL])
    await update.message.reply_text(
        f"🎮 <b>ဘယ် Game ကစားမည်?</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕹️ Console : <b>{cid}</b>  👤 <b>{member_id}</b>\n"
        f"{note}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"မပါသော ဂိမ်း ဆော့မည်ဆို <b>🔄 SSD Transfer</b> နှိပ်ပါ",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return BOOK_GAME


async def step_book_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game selection for the session."""
    text = update.message.text.strip()
    cid       = context.user_data.get("bk_console", "")
    member_id = context.user_data.get("bk_member", "Guest")
    staff     = context.user_data.get("bk_staff", "")
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        context.user_data["bk_member"] = member_id
        context.user_data["bk_staff"]  = staff
        return BOOK_MEMBER
    if text == BTN_SSD_TRANSFER:
        # Redirect to SSD transfer, auto-fill target console = bk_console
        context.user_data["ssd_return_to_session"] = True
        context.user_data["ssd_xfer_target_cons"]  = cid
        await update.message.reply_text(
            f"🔄 <b>SSD → {cid} Transfer</b>\n\nSSD ကို ရွေးပါ:",
            parse_mode="HTML",
            reply_markup=_ssd_kb(),
        )
        return SSD_XFER_SSD
    game = "" if text == BTN_SKIP_GAME else text
    context.user_data["bk_game"] = game
    return await prompt_book_mins(update, context)


async def prompt_book_mins(update, context):
    """Ask for planned play duration so a 5-min reminder can be scheduled."""
    cid       = context.user_data.get("bk_console", "")
    member_id = context.user_data.get("bk_member", "Guest")
    kb = [
        ["30", "60", "90"],
        ["120", "150", "180"],
        ["240", "300", "360"],
        [BTN_SKIP_TIMER],
        [BTN_BACK, BTN_CANCEL],
    ]
    await update.message.reply_text(
        f"⏱️ <b>Play Duration (Timer)</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕹️ Console : <b>{cid}</b>  👤 <b>{member_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"ကစားမည့် မိနစ် ရွေးပါ (5min မတိုင်ခင် auto-remind ပေးမည်)\n"
        f"မလိုပါက Skip နှိပ်ပါ",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return BOOK_MINS


async def step_book_mins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle planned-mins input and finalize the booking."""
    text      = update.message.text.strip()
    cid       = context.user_data.get("bk_console", "")
    member_id = context.user_data.pop("bk_member", "Guest")
    staff     = context.user_data.pop("bk_staff", "")

    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        # Go back to game selection
        context.user_data["bk_member"] = member_id
        context.user_data["bk_staff"]  = staff
        return await prompt_book_game(update, context)

    planned_mins = 0
    if text != BTN_SKIP_TIMER:
        try:
            planned_mins = int(text)
        except ValueError:
            await update.message.reply_text("⚠️ ဂဏန်းသာ ထည့်ပါ သို့ keyboard မှ ရွေးပါ")
            context.user_data["bk_member"] = member_id
            context.user_data["bk_staff"]  = staff
            return await prompt_book_mins(update, context)

    game = context.user_data.pop("bk_game", "")
    return await _do_create_booking(update, context, cid, member_id, staff, planned_mins, game)


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


# ── Reminder task tracker (keyed by "cid|chat_id") ──────────────────────────
_REMIND_TASKS: dict[str, "asyncio.Task[None]"] = {}

def _remind_key(cid: str, chat_id: int) -> str:
    return f"{cid}|{chat_id}"

def _cancel_remind(cid: str, chat_id: int) -> None:
    key  = _remind_key(cid, chat_id)
    task = _REMIND_TASKS.pop(key, None)
    if task and not task.done():
        task.cancel()

def _is_session_active(cid: str) -> bool:
    """Quick sync check: is this console still Active in Console_Booking today?"""
    try:
        sh   = get_booking_sh()
        rows = sh.get_all_values()
        td   = today_str()
        for row in rows[1:]:
            if len(row) < 7:
                continue
            if row[1].strip() == td and row[2].strip() == cid and row[6].strip() == "Active":
                return True
    except Exception:
        return True   # assume active if can't read sheet
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
    try:
        await asyncio.sleep(initial_delay)
        fire_count = 0
        while True:
            # Skip active-check on first fire — always deliver the first reminder
            if fire_count > 0:
                still_active = await asyncio.to_thread(_is_session_active, cid)
                if not still_active:
                    break
            fire_count += 1
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
            except Exception:
                pass
            # ── customer session warning (if member has a known chat_id) ───
            if member_id not in ("Guest", "0 (Guest)", ""):
                try:
                    cust_chat = await asyncio.to_thread(get_customer_chat_id, member_id)
                    if cust_chat:
                        cust_msg = (
                            f"⏰ <b>PS VIBE — Session သတိပေးချက်!</b>\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"🕹️ Console: <b>{cid}</b>\n"
                            f"⏱️ <b>5 မိနစ် ကျန်တော့သည်</b>\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"ဆက်ကစားလိုပါက Staff ကို ပြောပြပါ"
                        )
                        await asyncio.to_thread(_notify_customer, cust_chat, cust_msg)
                except Exception:
                    pass
            # ── next reminder in 5 mins ────────────────────────────────────
            await asyncio.sleep(5 * 60)
    except asyncio.CancelledError:
        pass
    finally:
        _REMIND_TASKS.pop(key, None)

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
    except Exception:
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
    data = await asyncio.to_thread(_replit_get, "bookings?status=confirmed")
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


# Module-level store for pending cancel-with-custom-note requests
# Key: user_id (int) → {"bk_id": int, "staff": str, "chat_id": int}
_pending_cancel_note: dict[int, dict] = {}


async def cb_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline 🚫 Cancel Booking — show reason selection first."""
    query = update.callback_query
    await query.answer()
    try:
        bk_id = int(query.data.split(":")[1])
    except Exception:
        return

    # Fetch current booking info for confirmation display
    bk_info = await asyncio.to_thread(_replit_get, f"bookings/{bk_id}")
    if not bk_info or isinstance(bk_info, list):
        bk_info = {}

    cur_status = bk_info.get("status", "")
    if cur_status in ("cancelled", "rejected", "completed"):
        try:
            await query.edit_message_text(
                f"⚠️ Booking #{bk_id} မှာ ဆောင်ရွက်မရနိုင်ပါ (status: {cur_status})",
                parse_mode="HTML",
            )
        except Exception:
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
    except Exception:
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
    except Exception:
        return
    reason_key = parts[2]
    staff_name = query.from_user.full_name or "Staff"

    if reason_key == "abort":
        try:
            await query.edit_message_text("↩️ Cancel ပယ်ဖျက်မည့် လုပ်ငန်းကို ရပ်လိုက်သည်။")
        except Exception:
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
        except Exception:
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
    result = await asyncio.to_thread(
        _replit_patch,
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
        except Exception:
            pass
        return

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
    except Exception:
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
        _notify_customer(tg_chat, cust_msg)


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
    now        = now_mmt()
    new_end_dt = now + timedelta(minutes=extra_mins)
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
    else:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")

    _cancel_remind(cid, chat_id)   # stop old loop before starting new one
    if has_remind:
        ext_delay = (extra_mins - 5) * 60   # seconds until 5-min-before-end
        if N8N_SESSION_WEBHOOK:
            # n8n fires restart-proof text reminder at ext_delay;
            # bot loop fires at the SAME time so inline-keyboard buttons are always shown.
            asyncio.create_task(
                _post_n8n_session_reminder(
                    chat_id, cid, member_id, extra_mins, new_end_t, ext_delay,
                )
            )
        # Bot loop: fire at "5 min before end", then every 5 min (same timing with or without n8n)
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
    except Exception:
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
        # Store pending extend context so the next text reply is captured
        context.user_data["_extend_pending"] = {
            "cid": cid, "member_id": member_id, "chat_id": chat_id,
        }
        # Edit reminder to signal we're waiting
        await query.edit_message_text(
            f"✏️ <b>Custom Extend</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🕹️ Console : <b>{cid}</b>  👤 <b>{member_id}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"ဆက်ကစားမည့် မိနစ် ရိုက်ထည့်ပြီး Send လုပ်ပါ\n"
            f"(ဥပမာ: <code>45</code>)",
            parse_mode="HTML",
        )
        # ForceReply so the keyboard pops up on mobile automatically
        await context.bot.send_message(
            chat_id=chat_id,
            text="⏱️ ဆက်ကစားမည့် မိနစ် ထည့်ပါ:",
            reply_markup=ForceReply(selective=True, input_field_placeholder="မိနစ် (ဥပမာ 45)"),
        )
        return

    # ── Preset +N ────────────────────────────────────────────────────────────
    try:
        extra_mins = int(extra_str)
    except ValueError:
        await query.edit_message_text("⚠️ Data error")
        return

    await _do_extend(context.bot, query, cid, member_id, chat_id, extra_mins)


async def handle_custom_extend_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Group -1 handler: captures the free-text reply for custom extend minutes.
    Raises ApplicationHandlerStop to prevent ConversationHandler from also firing."""
    pending = context.user_data.get("_extend_pending")
    if pending is None:
        return  # not our message — let ConversationHandler handle it normally

    text = update.message.text.strip()
    try:
        extra_mins = int(text)
        if extra_mins <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "⚠️ မှန်ကန်သော ဂဏန်း ရိုက်ထည့်ပါ (ဥပမာ: 45)",
            reply_markup=ForceReply(selective=True, input_field_placeholder="မိနစ် (ဥပမာ 45)"),
        )
        raise ApplicationHandlerStop  # keep _extend_pending; wait for correct input

    cid       = pending["cid"]
    member_id = pending["member_id"]
    chat_id   = pending["chat_id"]
    context.user_data.pop("_extend_pending", None)

    await _do_extend(context.bot, None, cid, member_id, chat_id, extra_mins)
    raise ApplicationHandlerStop  # done — don't let conv handler see this message


async def _do_create_booking(update, context, cid: str, member_id: str,
                              staff: str, planned_mins: int = 0, game: str = ""):
    """Actually create the booking, show confirmation, and schedule timer if set."""
    try:
        bk_id = create_booking(cid, member_id, staff, notes=game)
    except Exception as e:
        await update.message.reply_text(f"❌ Session save မအောင်မြင်ပါ: {e}")
        return await show_console_menu(update, context)

    # Track current session game in Console_Games (type = "Session")
