"""PS VIBE Bot — Console Management & Session Control handlers.
Auto-refactored from monolithic handlers.py (Phase 6).
"""
# ═══════ Imports from bot package ═══════
import bot as _bot_module  # for globals that need mutation  # noqa: F401
from bot import *  # noqa: F401,F403


async def cmd_console_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show live console status — uses API (Sheet + PostgreSQL reservations)."""
    await update.message.reply_text("⏳ Console status ဆွဲနေသည်…", parse_mode="Markdown")

    data = await asyncio.to_thread(_replit_get, "sheets/consoles")
    api_consoles = (data.get("consoles", []) if isinstance(data, dict) else [])

    if not api_consoles:
        # Fallback: Google Sheet only (no reservations)
        try:
            raw = fetch_console_status()
            api_consoles = [{"id": c["id"], "type": c.get("type", ""),
                             "liveStatus": c["status"],
                             "member": c.get("member"), "startTime": c.get("start"),
                             "reservedFor": None, "reservedAt": None, "reservedDuration": None}
                            for c in raw]
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            return

    free_list  = [c for c in api_consoles if c.get("liveStatus", "Free") == "Free"]
    busy_list  = [c for c in api_consoles if c.get("liveStatus", "Free") in ("Active", "Scheduled")]
    rsv_list   = [c for c in api_consoles if c.get("liveStatus", "Free") == "Reserved"]

    now_str = now_mmt().strftime("%H:%M")
    lines = [
        f"🕹️ *Console Status Board*  |  {now_str} MMT",
        "━━━━━━━━━━━━━━━━━━",
        f"✅ Free: {len(free_list)}  |  🔴 Active: {len(busy_list)}  |  🟡 Reserved: {len(rsv_list)}",
        "━━━━━━━━━━━━━━━━━━",
    ]

    for c in sorted(api_consoles, key=lambda x: x.get("id", "")):
        cid    = c.get("id", "?")
        ctype  = c.get("type", "")
        live   = c.get("liveStatus", "Free")
        ctype_str = f" ({ctype})" if ctype else ""

        if live == "Free":
            icon   = "🟢"
            detail = "Free"
        elif live == "Reserved":
            icon      = "🟡"
            rsv_who   = c.get("reservedFor") or c.get("member") or "Guest"
            rsv_at    = c.get("reservedAt") or c.get("startTime") or "—"
            # Calculate end time
            dur = c.get("reservedDuration") or c.get("durationMins") or 60
            try:
                sh, sm = map(int, rsv_at.split(":"))
                total_m = sh * 60 + sm + int(dur)
                end_str = f"{total_m // 60:02d}:{total_m % 60:02d}"
                time_range = f"{rsv_at}–{end_str}"
            except Exception:
                time_range = rsv_at
            detail = f"Reserved {time_range} — {rsv_who}"
        else:
            icon   = "🔴"
            mbr    = c.get("member") or "Guest"
            since  = f" since {c['startTime']}" if c.get("startTime") else ""
            detail = f"Active — {mbr}{since}"

        # Installed games on this console (excluding SSD-transferred ones shown separately)
        installed = [
            r["game_title"] for r in fetch_console_games()
            if r["console_id"].upper() == cid.upper() and r["game_title"]
        ]
        game_str = ""
        if installed:
            game_str = f"\n    🎮 {' · '.join(installed)}"

        lines.append(f"{icon} *{cid}*{ctype_str}: {detail}{game_str}")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
    )

async def show_console_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Console Management submenu — accessible from Main Menu and Admin Panel."""
    kb = [
        [BTN_START_SESSION,  BTN_END_SESSION],
        [BTN_STATUS_BOARD,   BTN_GAME_LIB_MENU],
        [BTN_CHANGE_GAME,    BTN_SSD_MANAGE],
        [BTN_BACK_MAIN],
    ]
    await update.message.reply_text(
        "🕹️ *Console Management*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Action ရွေးပါ ↓",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return CONSOLE_MENU

async def step_console_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    if choice == BTN_BACK_MAIN:
        return await show_main_menu(update, context)
    if choice == BTN_START_SESSION:
        return await prompt_book_console(update, context)
    if choice == BTN_END_SESSION:
        return await prompt_end_session(update, context)
    if choice == BTN_STATUS_BOARD:
        await cmd_console_status(update, context)
        return await show_console_menu(update, context)
    if choice == BTN_GAME_LIB_MENU:
        return await show_game_menu(update, context)
    if choice == BTN_SSD_MANAGE:
        return await show_ssd_menu(update, context)
    if choice == BTN_CHANGE_GAME:
        return await prompt_game_change_cons(update, context)
    return await show_console_menu(update, context)

async def prompt_game_change_cons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show active consoles so staff can pick which one to change game for."""
    try:
        consoles = fetch_console_status()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await show_console_menu(update, context)
    active = [c for c in consoles if c["status"] == "Active"]
    if not active:
        await update.message.reply_text(
            "ℹ️ လက်ရှိ Active session မရှိပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK]], resize_keyboard=True),
        )
        return CONSOLE_MENU
    kb = [[f"{c['id']} ({c.get('member') or 'Guest'})"] for c in active] + [[BTN_BACK]]
    await update.message.reply_text(
        "🔄 <b>Game ပြောင်း</b>\n\nGame ပြောင်းမည့် Active Console ရွေးပါ:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return GAME_CHANGE_CONS

async def step_game_change_cons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_console_menu(update, context)
    cid = text.split("(")[0].strip()
    context.user_data["gc_console"] = cid
    # Show current game
    cur_games = [
        r["game_title"] for r in fetch_console_games()
        if r["console_id"].upper() == cid.upper() and r["install_type"] == "Session"
    ]
    cur_str = f"ဘာသိသလဲ: <b>{cur_games[0]}</b>" if cur_games else "Current Game: —"
    # Only show games installed on this console
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
    else:
        kb_rows.append(["(ဂိမ်း မရှိသေးပါ)"])
    kb_rows.append([BTN_SSD_TRANSFER])
    kb_rows.append([BTN_SKIP_GAME])
    kb_rows.append([BTN_BACK])
    await update.message.reply_text(
        f"🕹️ <b>{cid}</b>\n{cur_str}\n\n"
        f"🎮 အသစ် ကစားမည့် ဂိမ်း ရွေးပါ\n"
        f"မပါသော ဂိမ်းဆို <b>🔄 SSD Transfer</b> နှိပ်ပါ:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb_rows, resize_keyboard=True),
    )
    return GAME_CHANGE_GAME

async def step_game_change_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    cid  = context.user_data.pop("gc_console", "")
    if text == BTN_BACK:
        return await prompt_game_change_cons(update, context)
    if text == BTN_SKIP_GAME:
        await update.message.reply_text("ℹ️ ပြောင်းမပြောင်းဘဲ ထားခဲ့သည်")
        return await show_console_menu(update, context)
    if text == BTN_SSD_TRANSFER:
        # Redirect to SSD transfer; after transfer return to game-change console picker
        context.user_data["gc_console"] = cid  # restore popped cid
        context.user_data["ssd_return_to_session"] = True
        context.user_data["ssd_xfer_target_cons"]  = cid
        await update.message.reply_text(
            f"🔄 <b>SSD → {cid} Transfer</b>\n\nSSD ကို ရွေးပါ:",
            parse_mode="HTML",
            reply_markup=_ssd_kb(),
        )
        return SSD_XFER_SSD
    new_game = text
    # Delete old Session entry, write new one
    _delete_session_game(cid)
    ok = add_console_game(cid, new_game, "Session", "Changed")
    if ok:
        await update.message.reply_text(
            f"✅ <b>{cid}</b> → Game ပြောင်းပြီ\n🎮 <b>{new_game}</b>",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("❌ Game ပြောင်းမရပါ — ထပ်ကြိုးစားပါ")
    return await show_console_menu(update, context)

async def prompt_end_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of active sessions for the user to pick and end."""
    try:
        consoles = fetch_console_status()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await show_console_menu(update, context)

    active = [c for c in consoles if c["status"] == "Active"]
    if not active:
        await update.message.reply_text(
            "ℹ️ လက်ရှိ Active session မရှိပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK]], resize_keyboard=True),
        )
        return CONSOLE_MENU

    lines = ["⏹️ <b>Session ဆုံးမည် — Console ရွေးပါ</b>\n━━━━━━━━━━━━━━━━━━"]
    kb    = []
    for c in active:
        _, dur_fmt = calc_duration(c["start"]) if c.get("start") else (0, "?")
        mbr  = c.get("member") or "Guest"
        ctype = f" ({c['type']})" if c.get("type") else ""
        lines.append(f"🔴 <b>{c['id']}</b>{ctype}  |  👤 {mbr}  |  ⏱ {dur_fmt}")
        kb.append([c["id"] + (f" ({c['type']})" if c.get("type") else "")])
    kb.append([BTN_BACK])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return END_SESSION_SELECT

async def step_end_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User picked a console to end — find its booking and end it."""
    text = update.message.text.strip()
    if text in (BTN_BACK, BTN_BACK_MAIN):
        return await show_console_menu(update, context)
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)

    cid = text.split("(")[0].strip()
    try:
        consoles = fetch_console_status()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await show_console_menu(update, context)

    target = next((c for c in consoles if c["id"] == cid and c["status"] == "Active"), None)
    if not target:
        await update.message.reply_text(
            f"⚠️ <b>{cid}</b> မှာ Active session မတွေ့ပါ\nStatus စစ်ကြည့်ပါ",
            parse_mode="HTML",
        )
        return await prompt_end_session(update, context)

    bk_id   = target.get("booking_id", "")
    start_t = target.get("start", "")
    mbr     = target.get("member") or "Guest"
    session_staff = target.get("staff", "")
    total_mins, dur_fmt = calc_duration(start_t) if start_t else (0, "?")

    ok = end_booking(bk_id) if bk_id else False
    if not ok:
        await update.message.reply_text(f"❌ Booking ID ရှာမတွေ့ပါ ({bk_id})")
        return await show_console_menu(update, context)

    end_t = now_mmt().strftime("%H:%M")

    # ── SSD Transfer Warning ────────────────────────────────────────────────
    ssd_warn = ""
    ssd_transfers = [
        r for r in fetch_console_games()
        if r["console_id"].upper() == cid.upper()
        and "SSD Transfer" in r.get("install_type", "")
    ]
    if ssd_transfers:
        game_names = [r["game_title"] for r in ssd_transfers]
        ssd_warn = (
            f"\n\n⚠️ <b>SSD ပြန်ရွေ့ပါ!</b>\n"
            f"ဤ console မှ SSD ထဲ ပြန်ရွေ့ရမည့် ဂိမ်းများ:\n"
            + "\n".join(f"  📀 {g}" for g in game_names)
        )

    # Show current session game if any
    session_games = [
        r["game_title"] for r in fetch_console_games()
        if r["console_id"].upper() == cid.upper() and r["install_type"] == "Session"
    ]
    game_line = f"\n🎮 Game     : <b>{session_games[0]}</b>" if session_games else ""

    await update.message.reply_text(
        f"✅ <b>Session ဆုံးပြီ!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕹️ Console  : <b>{cid}</b>\n"
        f"👤 Member   : <b>{mbr}</b>"
        f"{game_line}\n"
        f"🕐 Start    : <b>{start_t}</b>\n"
        f"🕑 End      : <b>{end_t}</b>\n"
        f"⏱ Duration : <b>{dur_fmt}</b> ({total_mins} mins)\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 Sales Voucher ဖွင့်နေသည်..."
        f"{ssd_warn}",
        parse_mode="HTML",
    )
    # Clean up Session game entry for this console
    _delete_session_game(cid)
    # Try to find linked booking_id from bookings store
    _linked_bk_id = ""
    try:
        _bks = _replit_get(f"bookings?memberId={mbr}") or []
        for _b in _bks:
            if (_b.get("status") in ("confirmed", "arrived")
                    and (_b.get("consoleId") or "").strip() == cid):
                _linked_bk_id = str(_b.get("id", ""))
                break
    except Exception:
        pass
    return await launch_session_sale(update, context, cid, mbr, total_mins, session_staff,
                                     booking_id=_linked_bk_id)
