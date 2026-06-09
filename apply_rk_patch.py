#!/usr/bin/env python3
"""
Apply ReplyKeyboard patch to booking flow.
Changes all InlineKeyboardMarkup selections to ReplyKeyboardMarkup.
"""
import re
import os

# ── Paths ──
BASE = "/root/psvibe-sales-bot/customer_bot"
HANDLERS = f"{BASE}/handlers.py"
BOOKING_HANDLERS = f"{BASE}/booking_handlers.py"
MAIN = f"{BASE}/main.py"

# ── Backup first ──
for f in [HANDLERS, BOOKING_HANDLERS, MAIN]:
    os.system(f"cp {f} {f}.rk_bak")

print("Backups created (.rk_bak)")

# ══════════════════════════════════════════════════════════
# 1. handlers.py — cmd_book() entry point
# ══════════════════════════════════════════════════════════

with open(HANDLERS, "r") as f:
    h = f.read()

# Replace cmd_book() inline keyboard with reply keyboard
old_cmd_book = """async def cmd_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    asyncio.create_task(_api.track_usage(update.effective_user, "book_start"))
    context.user_data["bk_reserved_console"] = None
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("ရှိပါတယ်", callback_data="bk_mem:yes")],
        [InlineKeyboardButton("မရှိဘူး (Guest)", callback_data="bk_mem:no")],
    ])
    await update.message.reply_text(
        "\\U0001f4c5 *Booking Form*\\n\\nMember Card ရှိပါသလား?",
        parse_mode="Markdown",
        reply_markup=kb,
    )
    return BK_MEMBER_CHECK"""

new_cmd_book = """async def cmd_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    asyncio.create_task(_api.track_usage(update.effective_user, "book_start"))
    context.user_data["bk_reserved_console"] = None
    kb = ReplyKeyboardMarkup(
        [["ရှိပါတယ်"], ["မရှိဘူး (Guest)"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        "\\U0001f4c5 *Booking Form*\\n\\nMember Card ရှိပါသလား?",
        parse_mode="Markdown",
        reply_markup=kb,
    )
    return BK_MEMBER_CHECK"""

assert old_cmd_book in h, "cmd_book() not found in handlers.py!"
h = h.replace(old_cmd_book, new_cmd_book)

with open(HANDLERS, "w") as f:
    f.write(h)

print(f"✅ Patched {HANDLERS} — cmd_book() now uses ReplyKeyboard")

# ══════════════════════════════════════════════════════════
# 2. booking_handlers.py — Full rewrite
# ══════════════════════════════════════════════════════════

with open(BOOKING_HANDLERS, "r") as f:
    bh = f.read()

# ═══ 2a. Add ReplyKeyboard import ═══
if "from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update" in bh:
    bh = bh.replace(
        "from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update",
        "from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update",
    )
    print("✅ Added ReplyKeyboardMarkup import")

# ═══ 2b. Replace helper keyboard functions ═══

# _make_date_keyboard
old_date_kb = """def _make_date_keyboard() -> InlineKeyboardMarkup:
    \"\"\"Build date selection keyboard: Today, Tomorrow, Day After.\"\"\"
    today = datetime.strptime(today_mmt(), "%Y-%m-%d")
    dates = [
        (today, "ယနေ့ (Today)"),
        (today + timedelta(days=1), "မနက်ဖြန် (Tomorrow)"),
        (today + timedelta(days=2), "သဘက်ခါ (Day After)"),
    ]
    buttons = []
    for d, label in dates:
        ds = d.strftime("%Y-%m-%d")
        buttons.append([InlineKeyboardButton(label, callback_data=f"bkdate:{ds}")])
    buttons.append([InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="bkdate:cancel")])
    return InlineKeyboardMarkup(buttons)"""

new_date_kb = """def _make_date_keyboard() -> ReplyKeyboardMarkup:
    \"\"\"Build date selection reply keyboard: Today, Tomorrow, Day After.\"\"\"
    return ReplyKeyboardMarkup(
        [["ယနေ့ (Today)"], ["မနက်ဖြန် (Tomorrow)"], ["သဘက်ခါ (Day After)"], ["❌ ပယ်ဖျက်မည်"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )"""

assert old_date_kb in bh, "_make_date_keyboard not found!"
bh = bh.replace(old_date_kb, new_date_kb)
print("✅ _make_date_keyboard → ReplyKeyboard")

# _make_time_keyboard
old_time_kb = """def _make_time_keyboard(free_slots: list[str]) -> InlineKeyboardMarkup:
    \"\"\"Build time slot keyboard for available hours.\"\"\"
    buttons = []
    row = []
    for slot in free_slots[:12]:  # max 12 slots shown
        row.append(InlineKeyboardButton(slot, callback_data=f"bktime:{slot}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("✏️ Custom Time", callback_data="bk_custom:ask")])
    buttons.append([InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="bktime:cancel")])
    return InlineKeyboardMarkup(buttons)"""

new_time_kb = """def _make_time_keyboard(free_slots: list[str]) -> ReplyKeyboardMarkup:
    \"\"\"Build time slot reply keyboard for available hours.\"\"\"
    buttons = []
    row = []
    for slot in free_slots[:12]:
        row.append(slot)
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append(["✏️ Custom Time"])
    buttons.append(["❌ ပယ်ဖျက်မည်"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)"""

assert old_time_kb in bh, "_make_time_keyboard not found!"
bh = bh.replace(old_time_kb, new_time_kb)
print("✅ _make_time_keyboard → ReplyKeyboard")

# _make_console_keyboard
old_con_kb = """def _make_console_keyboard() -> InlineKeyboardMarkup:
    \"\"\"Build console type selection keyboard.\"\"\"
    buttons = [[InlineKeyboardButton(t, callback_data=f"bk_con:{t}")] for t in CONSOLE_TYPES]
    buttons.append([InlineKeyboardButton("🤷 မရွေးတတ်ပါ", callback_data="bk_con:not_sure")])
    buttons.append([InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="bk_con:cancel")])
    return InlineKeyboardMarkup(buttons)"""

new_con_kb = """def _make_console_keyboard() -> ReplyKeyboardMarkup:
    \"\"\"Build console type selection reply keyboard.\"\"\"
    buttons = [[t] for t in CONSOLE_TYPES]
    buttons.append(["🤷 မရွေးတတ်ပါ"])
    buttons.append(["❌ ပယ်ဖျက်မည်"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)"""

assert old_con_kb in bh, "_make_console_keyboard not found!"
bh = bh.replace(old_con_kb, new_con_kb)
print("✅ _make_console_keyboard → ReplyKeyboard")

# _make_duration_keyboard
old_dur_kb = """def _make_duration_keyboard() -> InlineKeyboardMarkup:
    \"\"\"Build duration selection keyboard.\"\"\"
    buttons = []
    row = []
    for i, dur in enumerate(DURATION_OPTS):
        mins = int(dur.split()[0])
        row.append(InlineKeyboardButton(dur, callback_data=f"bk_dur:{mins}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="bk_dur:cancel")])
    return InlineKeyboardMarkup(buttons)"""

new_dur_kb = """def _make_duration_keyboard() -> ReplyKeyboardMarkup:
    \"\"\"Build duration selection reply keyboard.\"\"\"
    buttons = []
    row = []
    for dur in DURATION_OPTS:
        row.append(dur)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append(["❌ ပယ်ဖျက်မည်"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)"""

assert old_dur_kb in bh, "_make_duration_keyboard not found!"
bh = bh.replace(old_dur_kb, new_dur_kb)
print("✅ _make_duration_keyboard → ReplyKeyboard")

# _make_game_keyboard
old_game_kb = """def _make_game_keyboard(games: list[str], page: int = 0, per_page: int = 6) -> InlineKeyboardMarkup:
    \"\"\"Build game selection keyboard with pagination.\"\"\"
    start = page * per_page
    end = start + per_page
    page_games = games[start:end]
    buttons = [[InlineKeyboardButton(g[:50], callback_data=f"bk_game:{g[:50]}")] for g in page_games]

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Previous", callback_data=f"bk_game_page:{page - 1}"))
    if end < len(games):
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"bk_game_page:{page + 1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton("🤷 မရွေးတတ်ပါ", callback_data="bk_game:not_sure")])
    buttons.append([InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="bk_game:cancel")])
    return InlineKeyboardMarkup(buttons)"""

new_game_kb = """def _make_game_keyboard(games: list[str], page: int = 0, per_page: int = 4) -> ReplyKeyboardMarkup:
    \"\"\"Build game selection reply keyboard with pagination.\"\"\"
    start = page * per_page
    end = start + per_page
    page_games = games[start:end]
    buttons = []
    for g in page_games:
        # Truncate long game names for keyboard display
        label = g[:25] + "..." if len(g) > 28 else g
        buttons.append([label])

    nav_row = []
    if page > 0:
        nav_row.append("◀️ Previous")
    if end < len(games):
        nav_row.append("Next ▶️")
    if nav_row:
        buttons.append(nav_row)

    buttons.append(["🤷 မရွေးတတ်ပါ"])
    buttons.append(["❌ ပယ်ဖျက်မည်"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)"""

assert old_game_kb in bh, "_make_game_keyboard not found!"
bh = bh.replace(old_game_kb, new_game_kb)
print("✅ _make_game_keyboard → ReplyKeyboard")

# _make_confirm_keyboard
old_confirm_kb = """def _make_confirm_keyboard() -> InlineKeyboardMarkup:
    \"\"\"Build confirmation keyboard.\"\"\"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Booking", callback_data="bk_ok:yes")],
        [InlineKeyboardButton("❌ ပယ်ဖျက်မည်", callback_data="bk_ok:no")],
    ])"""

new_confirm_kb = """def _make_confirm_keyboard() -> ReplyKeyboardMarkup:
    \"\"\"Build confirmation reply keyboard.\"\"\"
    return ReplyKeyboardMarkup(
        [["✅ Confirm Booking"], ["❌ ပယ်ဖျက်မည်"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )"""

assert old_confirm_kb in bh, "_make_confirm_keyboard not found!"
bh = bh.replace(old_confirm_kb, new_confirm_kb)
print("✅ _make_confirm_keyboard → ReplyKeyboard")

# _make_warning_keyboard
old_warn_kb = """def _make_warning_keyboard(continue_cb: str, back_cb: str = "bk_ok:no") -> InlineKeyboardMarkup:
    \"\"\"Build warning keyboard with 'Continue Anyway' and 'Go Back'.\"\"\"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\u26a0\ufe0f \u1012\u102b\u1015\u1031\u1019\u1032 \u101e\u1000\u103a\u1010\u1004\u103a\u1019\u100a\u103a", callback_data=continue_cb)],
        [InlineKeyboardButton("\ud83d\udd19 \u1019\u1010\u1004\u103a\u1010\u1031\u102c\u1037\u1015\u102b", callback_data=back_cb)],
    ])"""

new_warn_kb = """def _make_warning_keyboard(continue_cb: str = "\u26a0\ufe0f \u1012\u102b\u1015\u1031\u1019\u1032 \u1006\u1000\u103a\u1010\u1004\u103a\u1019\u100a\u103a", back_cb: str = "\ud83d\udd19 \u1019\u1010\u1004\u103a\u1010\u1031\u102c\u1037\u1015\u102b") -> ReplyKeyboardMarkup:
    \"\"\"Build warning reply keyboard with 'Continue Anyway' and 'Go Back'.\"\"\"
    return ReplyKeyboardMarkup(
        [[continue_cb], [back_cb]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )"""

assert old_warn_kb in bh, "_make_warning_keyboard not found!"
bh = bh.replace(old_warn_kb, new_warn_kb)
print("✅ _make_warning_keyboard → ReplyKeyboard (text-based now)")

# ═══ 2c. Now rewrite all handler functions ═══
# The main challenge: handlers that read from callback_query need to read from message.text instead

# Since rewriting all handler functions in-place is too complex for simple string replacement,
# let me use targeted function-by-function replacements.

# ── bk_member_check_entry ──
old_mem_check = """async def bk_member_check_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Called after cmd_book — present member card Yes/No.\"\"\"
    if not update.callback_query:
        text = (update.message.text or "").strip()
        menu_result = await _bk_intercept_menu(text, update, context)
        if menu_result:
            return menu_result

    query = update.callback_query
    await query.answer()
    data = query.data or ""
    member_id = context.user_data.get("bk_member_id")

    if data == "bk_mem:yes":
        # User says they have a member card — search by phone
        phone = await _get_user_phone(update, context)
        if phone:
            members = await _api._fetch_members()
            phone_norm = phone.replace(" ", "").replace("-", "")
            matched = [
                (mid, m) for mid, m in members.items()
                if (m.get("phone") or "").replace(" ", "").replace("-", "") == phone_norm
            ]
            if len(matched) == 1:
                mid, m = matched[0]
                context.user_data["bk_member_id"] = mid
                context.user_data["bk_name"] = m.get("name", "")
                context.user_data["bk_phone"] = phone
                context.user_data["bk_member_data"] = m
                await query.edit_message_text(
                    f"👤 Member found: *{m.get('name', '?')}*\\n📞 Phone: *{phone}*\\n\\n✅ မှန်ကန်ပါသလား?",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ မှန်ပါသည်", callback_data="bk_dc:yes")],
                        [InlineKeyboardButton("❌ မဟုတ်ပါ", callback_data="bk_dc:no")],
                    ]),
                )
                return BK_DATA_CONFIRM
            elif len(matched) > 1:
                # Multiple members — show selection
                buttons = []
                for mid, m in matched[:10]:
                    label = f"{m.get('name','?')} ({m.get('phone','?')})"
                    buttons.append([InlineKeyboardButton(label, callback_data=f"bk_sel:{mid}")])
                buttons.append([InlineKeyboardButton("❌ မရှိပါ", callback_data="bk_sel:none")])
                await query.edit_message_text(
                    "👥 သင့် member profile *များစွာ* တွေ့ရှိပါသည် — ရွေးပေးပါ:",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
                return BK_MEMBER_SELECT
        # No phone match — let them pick member by ID
        await query.edit_message_text(
            "📋 Member ID ရိုက်ထည့်ပေးပါ (သို့မဟုတ် member card နံပါတ်):\\n\\n"
            "_Member card မရှိပါက 'no' ဟုရိုက်ပါ_",
            parse_mode="Markdown",
        )
        return BK_MEMBER_SELECT

    elif data == "bk_mem:no":
        # No member card — go to name entry
        await query.edit_message_text(
            "👤 နာမည်ရိုက်ထည့်ပေးပါ:",
        )
        return BK_NAME
    else:
        await query.edit_message_text("❌ Invalid option — please try again.")
        return ConversationHandler.END"""

new_mem_check = """async def bk_member_check_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Called after cmd_book — present member card Yes/No (ReplyKeyboard version).\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == "မရှိဘူး (Guest)":
        # No member card — go to name entry
        await update.message.reply_text(
            "👤 နာမည်ရိုက်ထည့်ပေးပါ:",
        )
        return BK_NAME

    elif text == "ရှိပါတယ်":
        # User says they have a member card — search by phone
        phone = await _get_user_phone(update, context)
        if phone:
            members = await _api._fetch_members()
            phone_norm = phone.replace(" ", "").replace("-", "")
            matched = [
                (mid, m) for mid, m in members.items()
                if (m.get("phone") or "").replace(" ", "").replace("-", "") == phone_norm
            ]
            if len(matched) == 1:
                mid, m = matched[0]
                context.user_data["bk_member_id"] = mid
                context.user_data["bk_name"] = m.get("name", "")
                context.user_data["bk_phone"] = phone
                context.user_data["bk_member_data"] = m
                kb = ReplyKeyboardMarkup(
                    [["✅ မှန်ပါသည်"], ["❌ မဟုတ်ပါ"]],
                    resize_keyboard=True,
                    one_time_keyboard=True,
                )
                await update.message.reply_text(
                    f"👤 Member found: *{m.get('name', '?')}*\\n📞 Phone: *{phone}*\\n\\n✅ မှန်ကန်ပါသလား?",
                    parse_mode="Markdown",
                    reply_markup=kb,
                )
                return BK_DATA_CONFIRM
            elif len(matched) > 1:
                # Multiple members — show selection
                buttons = []
                for mid, m in matched[:10]:
                    buttons.append([f"{m.get('name','?')} ({m.get('phone','?')})"])
                buttons.append(["❌ မရှိပါ"])
                kb = ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
                await update.message.reply_text(
                    "👥 သင့် member profile *များစွာ* တွေ့ရှိပါသည် — ရွေးပေးပါ:",
                    parse_mode="Markdown",
                    reply_markup=kb,
                )
                return BK_MEMBER_SELECT
        # No phone match — let them pick member by ID
        await update.message.reply_text(
            "📋 Member ID ရိုက်ထည့်ပေးပါ (သို့မဟုတ် member card နံပါတ်):\\n\\n"
            "_Member card မရှိပါက 'no' ဟုရိုက်ပါ_",
            parse_mode="Markdown",
        )
        return BK_MEMBER_SELECT

    else:
        await update.message.reply_text("❌ Invalid option — please try again.")
        return ConversationHandler.END"""

assert old_mem_check in bh, "bk_member_check_entry not found!"
bh = bh.replace(old_mem_check, new_mem_check)
print("✅ bk_member_check_entry → text-based (ReplyKeyboard)")

# ── bk_member_select ──
old_mem_sel = """async def bk_member_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle member selection callback or manual ID input.\"\"\"
    # Check if it's a callback query
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data.startswith("bk_sel:"):
            mid = data.split(":", 1)[1]
            if mid == "none":
                await query.edit_message_text("👤 နာမည်ရိုက်ထည့်ပေးပါ:")
                return BK_NAME

            # Look up member
            members = await _api._fetch_members()
            m = members.get(mid)
            if m:
                context.user_data["bk_member_id"] = mid
                context.user_data["bk_name"] = m.get("name", "")
                context.user_data["bk_phone"] = m.get("phone", "")
                context.user_data["bk_member_data"] = m
                # Ask for phone verification
                phone = m.get("phone", "")
                masked = phone[-4:] if len(phone) >= 4 else phone
                await query.edit_message_text(
                    f"👤 *{m.get('name','?')}*\\n"
                    f"📞 ဖုန်းနံပါတ် နောက်ဆုံး ၄ လုံး: *...{masked}*\\n\\n"
                    f"မှန်ကန်ပါက ✅ နှိပ်ပါ — သို့မဟုတ် ဖုန်းနံပါတ် အပြည့် ရိုက်ထည့်ပါ",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ မှန်ပါသည်", callback_data="bk_dc:yes")],
                        [InlineKeyboardButton("❌ မဟုတ်ပါ", callback_data="bk_dc:no")],
                    ]),
                )
                return BK_DATA_CONFIRM
            else:
                await query.edit_message_text("❌ Member မတွေ့ပါ — နာမည်ရိုက်ထည့်ပါ:")
                return BK_NAME
        else:
            await query.edit_message_text("❌ Invalid selection.")
            return ConversationHandler.END

    # MessageHandler: manual member ID input
    text = (update.message.text or "").strip()
    # Check for menu buttons
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    text_lower = text.lower()
    if text_lower == "no" or text == "မရှိပါ":
        await update.message.reply_text("👤 နာမည်ရိုက်ထည့်ပေးပါ:")
        return BK_NAME

    # Try to look up by member ID
    members = await _api._fetch_members()
    m = members.get(text_lower)
    if m:
        context.user_data["bk_member_id"] = text
        context.user_data["bk_name"] = m.get("name", "")
        context.user_data["bk_phone"] = m.get("phone", "")
        context.user_data["bk_member_data"] = m
        phone = m.get("phone", "")
        masked = phone[-4:] if len(phone) >= 4 else phone
        await update.message.reply_text(
            f"👤 *{m.get('name','?')}*\\n"
            f"📞 ဖုန်းနံပါတ် နောက်ဆုံး ၄ လုံး: *...{masked}*\\n\\n"
            f"မှန်ကန်ပါက ✅ နှိပ်ပါ — သို့မဟုတ် ဖုန်းနံပါတ် အပြည့် ရိုက်ထည့်ပါ",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ မှန်ပါသည်", callback_data="bk_dc:yes")],
                [InlineKeyboardButton("❌ မဟုတ်ပါ", callback_data="bk_dc:no")],
            ]),
        )
        return BK_DATA_CONFIRM
    else:
        await update.message.reply_text(
            f"❌ Member ID `{text}` မတွေ့ပါ\\n"
            "ထပ်ကြိုးစားပါ — သို့မဟုတ် 'no' ဟုရိုက်ပြီး member မရှိဘဲ ဆက်လုပ်ပါ",
            parse_mode="Markdown",
        )
        return BK_MEMBER_SELECT"""

new_mem_sel = """async def bk_member_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle member selection — text or member ID input (ReplyKeyboard version).\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    # Check if text matches a member name from the keyboard (prefix matching)
    members = await _api._fetch_members()
    # Try to match text to a member name from the shown list
    matched_by_name = None
    for mid, m in members.items():
        label = f"{m.get('name','?')} ({m.get('phone','?')})"
        if text == label or text == m.get("name", ""):
            matched_by_name = (mid, m)
            break

    if text == "❌ မရှိပါ":
        await update.message.reply_text("👤 နာမည်ရိုက်ထည့်ပေးပါ:")
        return BK_NAME

    if matched_by_name:
        mid, m = matched_by_name
        context.user_data["bk_member_id"] = mid
        context.user_data["bk_name"] = m.get("name", "")
        context.user_data["bk_phone"] = m.get("phone", "")
        context.user_data["bk_member_data"] = m
        phone = m.get("phone", "")
        masked = phone[-4:] if len(phone) >= 4 else phone
        kb = ReplyKeyboardMarkup(
            [["✅ မှန်ပါသည်"], ["❌ မဟုတ်ပါ"]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(
            f"👤 *{m.get('name','?')}*\\n"
            f"📞 ဖုန်းနံပါတ် နောက်ဆုံး ၄ လုံး: *...{masked}*\\n\\n"
            f"မှန်ကန်ပါက \"✅ မှန်ပါသည်\" နှိပ်ပါ — သို့မဟုတ် ဖုန်းနံပါတ် အပြည့် ရိုက်ထည့်ပါ",
            parse_mode="Markdown",
            reply_markup=kb,
        )
        return BK_DATA_CONFIRM

    # Manual input handling (no callback query anymore)
    text_lower = text.lower()
    if text_lower == "no" or text == "မရှိပါ":
        await update.message.reply_text("👤 နာမည်ရိုက်ထည့်ပေးပါ:")
        return BK_NAME

    # Try to look up by member ID
    m = members.get(text_lower)
    if m:
        context.user_data["bk_member_id"] = text
        context.user_data["bk_name"] = m.get("name", "")
        context.user_data["bk_phone"] = m.get("phone", "")
        context.user_data["bk_member_data"] = m
        phone = m.get("phone", "")
        masked = phone[-4:] if len(phone) >= 4 else phone
        kb = ReplyKeyboardMarkup(
            [["✅ မှန်ပါသည်"], ["❌ မဟုတ်ပါ"]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(
            f"👤 *{m.get('name','?')}*\\n"
            f"📞 ဖုန်းနံပါတ် နောက်ဆုံး ၄ လုံး: *...{masked}*\\n\\n"
            f"မှန်ကန်ပါက \"✅ မှန်ပါသည်\" နှိပ်ပါ — သို့မဟုတ် ဖုန်းနံပါတ် အပြည့် ရိုက်ထည့်ပါ",
            parse_mode="Markdown",
            reply_markup=kb,
        )
        return BK_DATA_CONFIRM
    else:
        await update.message.reply_text(
            f"❌ Member ID `{text}` မတွေ့ပါ\\n"
            "ထပ်ကြိုးစားပါ — သို့မဟုတ် 'no' ဟုရိုက်ပြီး member မရှိဘဲ ဆက်လုပ်ပါ",
            parse_mode="Markdown",
        )
        return BK_MEMBER_SELECT"""

assert old_mem_sel in bh, "bk_member_select not found!"
bh = bh.replace(old_mem_sel, new_mem_sel)
print("✅ bk_member_select → text-based (ReplyKeyboard)")

# ── bk_phone_verify ──
old_phone_verify = """async def bk_phone_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Verify phone number entered by user.\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result
    member = context.user_data.get("bk_member_data", {})
    expected_phone = member.get("phone", "")


    if text == expected_phone or (len(text) >= 4 and expected_phone.endswith(text)):
        # Phone verified
        await update.message.reply_text(
            "✅ ဖုန်းနံပါတ် မှန်ကန်ပါသည်!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Confirm & Continue", callback_data="bk_dc:yes")],
                [InlineKeyboardButton("❌ မဟုတ်ပါ", callback_data="bk_dc:no")],
            ]),
        )
        return BK_DATA_CONFIRM
    else:
        await update.message.reply_text(
            "❌ ဖုန်းနံပါတ် မကိုက်ညီပါ — ထပ်ကြိုးစားပါ (သို့မဟုတ် 'no' ရိုက်ပြီး skip လုပ်ပါ):",
        )
        return BK_PHONE_VERIFY"""

new_phone_verify = """async def bk_phone_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Verify phone number entered by user (ReplyKeyboard version).\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result
    member = context.user_data.get("bk_member_data", {})
    expected_phone = member.get("phone", "")


    if text == expected_phone or (len(text) >= 4 and expected_phone.endswith(text)):
        # Phone verified
        kb = ReplyKeyboardMarkup(
            [["✅ မှန်ပါသည်"], ["❌ မဟုတ်ပါ"]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await update.message.reply_text(
            "✅ ဖုန်းနံပါတ် မှန်ကန်ပါသည်!",
            reply_markup=kb,
        )
        return BK_DATA_CONFIRM
    else:
        await update.message.reply_text(
            "❌ ဖုန်းနံပါတ် မကိုက်ညီပါ — ထပ်ကြိုးစားပါ (သို့မဟုတ် 'no' ရိုက်ပြီး skip လုပ်ပါ):",
        )
        return BK_PHONE_VERIFY"""

assert old_phone_verify in bh, "bk_phone_verify not found!"
bh = bh.replace(old_phone_verify, new_phone_verify)
print("✅ bk_phone_verify → ReplyKeyboard confirm")

# ── bk_data_confirm ──
old_data_confirm = """async def bk_data_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Confirm member data or go to manual name entry.\"\"\"
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_dc:yes":
        # Confirmed — skip to date selection
        await query.edit_message_text("📅 ဘိုကင်လုပ်မည့် ရက်ရွေးပါ:")
        await query.message.reply_text(
            "📅 ဘယ်ရက်မှာ လာဆော့မလဲ?",
            reply_markup=_make_date_keyboard(),
        )
        return BK_DATE
    elif data == "bk_dc:no":
        # Not correct — go to manual name entry
        context.user_data.pop("bk_member_id", None)
        context.user_data.pop("bk_member_data", None)
        await query.edit_message_text("👤 နာမည်အမှန် ရိုက်ထည့်ပေးပါ:")
        return BK_NAME
    else:
        await query.edit_message_text("❌ Invalid option.")
        return ConversationHandler.END"""

new_data_confirm = """async def bk_data_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Confirm member data or go to manual name entry (ReplyKeyboard version).\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == "✅ မှန်ပါသည်":
        # Confirmed — skip to date selection
        await update.message.reply_text("📅 ဘိုကင်လုပ်မည့် ရက်ရွေးပါ:")
        await update.message.reply_text(
            "📅 ဘယ်ရက်မှာ လာဆော့မလဲ?",
            reply_markup=_make_date_keyboard(),
        )
        return BK_DATE
    elif text == "❌ မဟုတ်ပါ":
        # Not correct — go to manual name entry
        context.user_data.pop("bk_member_id", None)
        context.user_data.pop("bk_member_data", None)
        await update.message.reply_text("👤 နာမည်အမှန် ရိုက်ထည့်ပေးပါ:")
        return BK_NAME
    else:
        await update.message.reply_text("❌ Invalid option.")
        return ConversationHandler.END"""

assert old_data_confirm in bh, "bk_data_confirm not found!"
bh = bh.replace(old_data_confirm, new_data_confirm)
print("✅ bk_data_confirm → text-based (ReplyKeyboard)")

# ── bk_date_select ──
old_date_sel = """async def bk_date_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle date selection callback.\"\"\"
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bkdate:cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    if data.startswith("bkdate:"):
        date_str = data.split(":", 1)[1]
        context.user_data["bk_date"] = date_str

        # Get available slots
        await query.edit_message_text("⏳ Available slots စစ်ဆေးနေသည်...")
        free_slots = await _get_available_slots(date_str)

        if not free_slots:
            await query.edit_message_text(
                f"😔 *{date_str}* တွင် slot အားလုံး ပြည့်နေပါပြီ\\n\\n"
                "အခြားရက်ကို ရွေးပေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_date_keyboard(),
            )
            return BK_DATE

        await query.edit_message_text(
            f"📅 *{date_str}* တွင် ရနိုင်သော အချိန်များ:\\n"
            f"ရနိုင်သော slot — *{len(free_slots)} ခု*",
            parse_mode="Markdown",
            reply_markup=_make_time_keyboard(free_slots),
        )
        return BK_TIME

    await query.edit_message_text("❌ Invalid date selection.")
    return BK_DATE"""

new_date_sel = """async def bk_date_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle date selection — text-based (ReplyKeyboard version).\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == "❌ ပယ်ဖျက်မည်":
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Booking ဖျက်လိုက်ပါပြီ",
            reply_markup=MAIN_MENU_KB,
        )
        return ConversationHandler.END

    # Map date text to date string
    today = today_mmt()
    date_map = {
        "ယနေ့ (Today)": today,
        "မနက်ဖြန် (Tomorrow)": (datetime.strptime(today, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
        "သဘက်ခါ (Day After)": (datetime.strptime(today, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d"),
    }

    if text in date_map:
        date_str = date_map[text]
        context.user_data["bk_date"] = date_str

        # Get available slots
        await update.message.reply_text("⏳ Available slots စစ်ဆေးနေသည်...")
        free_slots = await _get_available_slots(date_str)

        if not free_slots:
            await update.message.reply_text(
                f"😔 *{date_str}* တွင် slot အားလုံး ပြည့်နေပါပြီ\\n\\n"
                "အခြားရက်ကို ရွေးပေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_date_keyboard(),
            )
            return BK_DATE

        await update.message.reply_text(
            f"📅 *{date_str}* တွင် ရနိုင်သော အချိန်များ:\\n"
            f"ရနိုင်သော slot — *{len(free_slots)} ခု*",
            parse_mode="Markdown",
            reply_markup=_make_time_keyboard(free_slots),
        )
        return BK_TIME

    await update.message.reply_text("❌ Invalid date selection.")
    return BK_DATE"""

assert old_date_sel in bh, "bk_date_select not found!"
bh = bh.replace(old_date_sel, new_date_sel)
print("✅ bk_date_select → text-based (ReplyKeyboard)")

# ── bk_time_select ──
old_time_sel = """async def bk_time_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle time slot selection callback.\"\"\"
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bktime:cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    if data.startswith("bktime:"):
        time_str = data.split(":", 1)[1]
        context.user_data["bk_time"] = time_str
        await query.edit_message_text(
            f"⏰ အချိန်: *{time_str}*\\n\\n🎮 Console အမျိုးအစား ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=_make_console_keyboard(),
        )
        return BK_CONSOLE

    if data == "bk_custom:ask":
        await query.edit_message_text(
            "✏️ လိုချင်သော အချိန်ကို HH:MM format ဖြင့် ရိုက်ထည့်ပါ\\n"
            "(ဥပမာ: 14:30, 10:00)\\n\\n"
            f"⏰ Operating hours: {OPEN_HOUR}:00 - {CLOSE_HOUR}:00",
        )
        return BK_TIME

    if data.startswith("bk_custom:"):
        # This would handle the custom time message input
        # But the main.py routes bk_custom: to CallbackQueryHandler, so this catches
        # the actual text input would come through BK_END or a separate handler
        pass

    # Check if it's a text message with custom time
    if update.message:
        text = (update.message.text or "").strip()
        m = re.match(r'^(\\d{1,2}):(\\d{2})$', text)
        if m:
            hour, minute = int(m.group(1)), int(m.group(2))
            if OPEN_HOUR <= hour <= CLOSE_HOUR and minute in (0, 30) and hour != CLOSE_HOUR:
                time_str = f"{hour:02d}:{minute:02d}"
                context.user_data["bk_time"] = time_str
                await update.message.reply_text(
                    f"⏰ Custom Time: *{time_str}*\\n\\n🎮 Console အမျိုးအစား ရွေးပါ:",
                    parse_mode="Markdown",
                    reply_markup=_make_console_keyboard(),
                )
                return BK_CONSOLE
            else:
                await update.message.reply_text(
                    f"⚠️ မမှန်ကန်သော အချိန် — {OPEN_HOUR}:00 မှ {CLOSE_HOUR}:00 အတွင်း "
                    "နာရီဝက် သို့မဟုတ် နာရီပြည့်ဖြင့် ထည့်ပေးပါ",
                )
                return BK_TIME
        else:
            await update.message.reply_text("⚠️ HH:MM format ဖြင့် ရိုက်ထည့်ပါ (ဥပမာ: 14:00)")
            return BK_TIME

    await query.edit_message_text("❌ Invalid time selection.")
    return BK_TIME"""

new_time_sel = """async def bk_time_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle time slot selection — text-based (ReplyKeyboard version).\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == "❌ ပယ်ဖျက်မည်":
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Booking ဖျက်လိုက်ပါပြီ",
            reply_markup=MAIN_MENU_KB,
        )
        return ConversationHandler.END

    if text == "✏️ Custom Time":
        await update.message.reply_text(
            "✏️ လိုချင်သော အချိန်ကို HH:MM format ဖြင့် ရိုက်ထည့်ပါ\\n"
            "(ဥပမာ: 14:30, 10:00)\\n\\n"
            f"⏰ Operating hours: {OPEN_HOUR}:00 - {CLOSE_HOUR}:00",
        )
        return BK_TIME

    # Check if text matches a time slot from the keyboard
    m = re.match(r'^(\\d{2}):(\\d{2})$', text)
    if m:
        hour, minute = int(m.group(1)), int(m.group(2))
        if OPEN_HOUR <= hour <= CLOSE_HOUR and minute == 0:
            time_str = text
            context.user_data["bk_time"] = time_str
            await update.message.reply_text(
                f"⏰ အချိန်: *{time_str}*\\n\\n🎮 Console အမျိုးအစား ရွေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_console_keyboard(),
            )
            return BK_CONSOLE

    # Try custom HH:MM format too (for custom typed input)
    m = re.match(r'^(\\d{1,2}):(\\d{2})$', text)
    if m:
        hour, minute = int(m.group(1)), int(m.group(2))
        if OPEN_HOUR <= hour <= CLOSE_HOUR and minute in (0, 30) and hour != CLOSE_HOUR:
            time_str = f"{hour:02d}:{minute:02d}"
            context.user_data["bk_time"] = time_str
            await update.message.reply_text(
                f"⏰ Custom Time: *{time_str}*\\n\\n🎮 Console အမျိုးအစား ရွေးပါ:",
                parse_mode="Markdown",
                reply_markup=_make_console_keyboard(),
            )
            return BK_CONSOLE
        else:
            await update.message.reply_text(
                f"⚠️ မမှန်ကန်သော အချိန် — {OPEN_HOUR}:00 မှ {CLOSE_HOUR}:00 အတွင်း "
                "နာရီဝက် သို့မဟုတ် နာရီပြည့်ဖြင့် ထည့်ပေးပါ",
            )
            return BK_TIME
    else:
        await update.message.reply_text("⚠️ HH:MM format ဖြင့် ရိုက်ထည့်ပါ (ဥပမာ: 14:00)")
        return BK_TIME"""

assert old_time_sel in bh, "bk_time_select not found!"
bh = bh.replace(old_time_sel, new_time_sel)
print("✅ bk_time_select → text-based (ReplyKeyboard)")

# ── bk_console_select (also used for BK_CONSOLE) ──
old_con_sel = """async def bk_console_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle console type selection.\"\"\"
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_con:cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    if data.startswith("bk_con:"):
        con = data.split(":", 1)[1]
        if con == "not_sure":
            context.user_data["bk_console"] = "Any"
        else:
            context.user_data["bk_console"] = con
        await query.edit_message_text(
            f"🎮 Console: *{context.user_data['bk_console']}*\\n\\n"
            "⏱️ ကြာချိန် ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=_make_duration_keyboard(),
        )
        return BK_DURATION

    await query.edit_message_text("❌ Invalid console selection.")
    return BK_CONSOLE"""

new_con_sel = """async def bk_console_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle console type selection — text-based (ReplyKeyboard version).\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == "❌ ပယ်ဖျက်မည်":
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Booking ဖျက်လိုက်ပါပြီ",
            reply_markup=MAIN_MENU_KB,
        )
        return ConversationHandler.END

    if text in CONSOLE_TYPES:
        context.user_data["bk_console"] = text
        await update.message.reply_text(
            f"🎮 Console: *{text}*\\n\\n"
            "⏱️ ကြာချိန် ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=_make_duration_keyboard(),
        )
        return BK_DURATION
    elif text == "🤷 မရွေးတတ်ပါ":
        context.user_data["bk_console"] = "Any"
        await update.message.reply_text(
            "🎮 Console: *Any*\\n\\n"
            "⏱️ ကြာချိန် ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=_make_duration_keyboard(),
        )
        return BK_DURATION

    await update.message.reply_text("❌ Invalid console selection.")
    return BK_CONSOLE"""

assert old_con_sel in bh, "bk_console_select not found!"
bh = bh.replace(old_con_sel, new_con_sel)
print("✅ bk_console_select → text-based (ReplyKeyboard)")

# ── bk_duration_select ──
old_dur_sel = """async def bk_duration_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle duration selection.\"\"\"
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_dur:cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    if data.startswith("bk_dur:"):
        try:
            mins = int(data.split(":", 1)[1])
        except ValueError:
            await query.edit_message_text("❌ Invalid duration.")
            return BK_DURATION

        context.user_data["bk_duration_mins"] = mins
        await query.edit_message_text("🕹️ Game list ဆွဲနေသည်...")

        # Fetch games
        games = await _api._fetch_games(context.user_data.get("bk_console", ""))
        context.user_data["_bk_game_list"] = games
        context.user_data["_bk_game_page"] = 0

        if not games:
            await query.edit_message_text(
                "⚠️ Game list မရဘူး — skip လုပ်မလား?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⏭️ Skip", callback_data="bk_game:not_sure")],
                ]),
            )
            return BK_GAME

        await query.edit_message_text(
            f"⏱️ Duration: *{mins} mins*\\n\\n"
            f"🕹️ ဆော့မည့်ဂိမ်းရွေးပါ (Total: {len(games)} games):",
            parse_mode="Markdown",
            reply_markup=_make_game_keyboard(games),
        )
        return BK_GAME

    await query.edit_message_text("❌ Invalid duration selection.")
    return BK_DURATION"""

new_dur_sel = """async def bk_duration_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle duration selection — text-based (ReplyKeyboard version).\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == "❌ ပယ်ဖျက်မည်":
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Booking ဖျက်လိုက်ပါပြီ",
            reply_markup=MAIN_MENU_KB,
        )
        return ConversationHandler.END

    # Match duration options from DURATION_OPTS
    if text in DURATION_OPTS:
        try:
            mins = int(text.split()[0])
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Invalid duration.")
            return BK_DURATION

        context.user_data["bk_duration_mins"] = mins
        await update.message.reply_text("🕹️ Game list ဆွဲနေသည်...")

        # Fetch games
        games = await _api._fetch_games(context.user_data.get("bk_console", ""))
        context.user_data["_bk_game_list"] = games
        context.user_data["_bk_game_page"] = 0

        if not games:
            kb = ReplyKeyboardMarkup(
                [["⏭️ Skip"]],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            await update.message.reply_text(
                "⚠️ Game list မရဘူး — skip လုပ်မလား?",
                reply_markup=kb,
            )
            return BK_GAME

        await update.message.reply_text(
            f"⏱️ Duration: *{mins} mins*\\n\\n"
            f"🕹️ ဆော့မည့်ဂိမ်းရွေးပါ (Total: {len(games)} games):",
            parse_mode="Markdown",
            reply_markup=_make_game_keyboard(games),
        )
        return BK_GAME

    await update.message.reply_text("❌ Invalid duration selection.")
    return BK_DURATION"""

assert old_dur_sel in bh, "bk_duration_select not found!"
bh = bh.replace(old_dur_sel, new_dur_sel)
print("✅ bk_duration_select → text-based (ReplyKeyboard)")

# ── bk_game_select ──
old_game_sel = """async def bk_game_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle game selection callback.\"\"\"
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_game:cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    if data.startswith("bk_game_page:"):
        page = int(data.split(":", 1)[1])
        context.user_data["_bk_game_page"] = page
        games = context.user_data.get("_bk_game_list", [])
        await query.edit_message_text(
            f"🕹️ ဆော့မည့်ဂိမ်းရွေးပါ (Total: {len(games)} games, Page {page + 1}):",
            reply_markup=_make_game_keyboard(games, page),
        )
        return BK_GAME

    if data.startswith("bk_game:"):
        game = data.split(":", 1)[1]
        if game == "not_sure":
            context.user_data["bk_game"] = "Any"
        else:
            context.user_data["bk_game"] = game

        await query.edit_message_text(
            f"🕹️ Game: *{context.user_data['bk_game']}*\\n\\n"
            "💻 Console preference ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=_make_console_keyboard(),
        )
        return BK_CONSOLE_PREF

    await query.edit_message_text("❌ Invalid game selection.")
    return BK_GAME"""

new_game_sel = """async def bk_game_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle game selection — text-based (ReplyKeyboard version).\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == "❌ ပယ်ဖျက်မည်":
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Booking ဖျက်လိုက်ပါပြီ",
            reply_markup=MAIN_MENU_KB,
        )
        return ConversationHandler.END

    games = context.user_data.get("_bk_game_list", [])
    page = context.user_data.get("_bk_game_page", 0)
    per_page = 4

    if text == "Next ▶️":
        page += 1
        context.user_data["_bk_game_page"] = page
        await update.message.reply_text(
            f"🕹️ ဆော့မည့်ဂိမ်းရွေးပါ (Total: {len(games)} games, Page {page + 1}):",
            reply_markup=_make_game_keyboard(games, page),
        )
        return BK_GAME

    if text == "◀️ Previous":
        page = max(0, page - 1)
        context.user_data["_bk_game_page"] = page
        await update.message.reply_text(
            f"🕹️ ဆော့မည့်ဂိမ်းရွေးပါ (Total: {len(games)} games, Page {page + 1}):",
            reply_markup=_make_game_keyboard(games, page),
        )
        return BK_GAME

    if text == "🤷 မရွေးတတ်ပါ":
        context.user_data["bk_game"] = "Any"
        await update.message.reply_text(
            "🕹️ Game: *Any*\\n\\n"
            "💻 Console preference ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=_make_console_keyboard(),
        )
        return BK_CONSOLE_PREF

    if text == "⏭️ Skip":
        context.user_data["bk_game"] = "Any"
        await update.message.reply_text(
            "🕹️ Game: *Any* (skipped)\\n\\n"
            "💻 Console preference ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=_make_console_keyboard(),
        )
        return BK_CONSOLE_PREF

    # Check if text matches any game in the list
    # Try exact match first, then prefix match
    game = None
    for g in games:
        label = g[:25] + "..." if len(g) > 28 else g
        if text == g or text == label:
            game = g
            break
    # Fall back to substring match for truncated names
    if not game:
        for g in games:
            if text in g:
                game = g
                break

    if game:
        context.user_data["bk_game"] = game
        await update.message.reply_text(
            f"🕹️ Game: *{game}*\\n\\n"
            "💻 Console preference ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=_make_console_keyboard(),
        )
        return BK_CONSOLE_PREF

    await update.message.reply_text("❌ Invalid game selection — ဂိမ်းနာမည်အတိုင်း ပြန်နှိပ်ပါ သို့မဟုတ် \"🤷 မရွေးတတ်ပါ\" ကိုရွေးပါ")
    return BK_GAME"""

assert old_game_sel in bh, "bk_game_select not found!"
bh = bh.replace(old_game_sel, new_game_sel)
print("✅ bk_game_select → text-based (ReplyKeyboard)")

# ── bk_console_pref ──
old_con_pref = """async def bk_console_pref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle console preference selection.\"\"\"
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_con:cancel":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    if data.startswith("bk_con:"):
        pref = data.split(":", 1)[1]
        if pref == "not_sure":
            context.user_data["bk_console_pref"] = "Any"
        else:
            context.user_data["bk_console_pref"] = pref

        # Show booking summary
        summary = _format_booking_summary(context)
        await query.edit_message_text(
            summary + "\\n\\n✅ Confirm လုပ်မလား?",
            parse_mode="Markdown",
            reply_markup=_make_confirm_keyboard(),
        )
        return BK_CONFIRM

    await query.edit_message_text("❌ Invalid preference selection.")
    return BK_CONSOLE_PREF"""

new_con_pref = """async def bk_console_pref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle console preference selection — text-based (ReplyKeyboard version).\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == "❌ ပယ်ဖျက်မည်":
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Booking ဖျက်လိုက်ပါပြီ",
            reply_markup=MAIN_MENU_KB,
        )
        return ConversationHandler.END

    if text in CONSOLE_TYPES:
        context.user_data["bk_console_pref"] = text
        # Show booking summary
        summary = _format_booking_summary(context)
        await update.message.reply_text(
            summary + "\\n\\n✅ Confirm လုပ်မလား?",
            parse_mode="Markdown",
            reply_markup=_make_confirm_keyboard(),
        )
        return BK_CONFIRM
    elif text == "🤷 မရွေးတတ်ပါ":
        context.user_data["bk_console_pref"] = "Any"
        summary = _format_booking_summary(context)
        await update.message.reply_text(
            summary + "\\n\\n✅ Confirm လုပ်မလား?",
            parse_mode="Markdown",
            reply_markup=_make_confirm_keyboard(),
        )
        return BK_CONFIRM

    await update.message.reply_text("❌ Invalid preference selection.")
    return BK_CONSOLE_PREF"""

assert old_con_pref in bh, "bk_console_pref not found!"
bh = bh.replace(old_con_pref, new_con_pref)
print("✅ bk_console_pref → text-based (ReplyKeyboard)")

# ── bk_confirm ──
old_confirm = """async def bk_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle booking confirmation and submission to API.\"\"\"
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_ok:no":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    if data == "bk_ok:yes":
        await query.edit_message_text("⏳ Booking တင်နေသည်...")

        user = update.effective_user
        uid = str(user.id) if user else ""

        # Check for duplicate booking
        date_str = context.user_data.get("bk_date", "")
        time_str = context.user_data.get("bk_time", "")
        try:
            existing = await _api._api_get(
                f"search-bookings?telegram_chat_id={uid}&date={date_str}&status=confirmed"
            )
            existing = existing if isinstance(existing, list) else []
            dupes = [b for b in existing if b.get("timeSlot") == time_str]
            if dupes:
                await query.edit_message_text(
                    "⚠️ *Duplicate Booking Detected!*\\n\\n"
                    f"📅 {date_str} ⏰ {time_str} တွင် booking ရှိပြီးသားပါ\\n\\n"
                    "ဒါပေမဲ့ ဆက်တင်မလား?",
                    parse_mode="Markdown",
                    reply_markup=_make_warning_keyboard("bk_warn:dup_ok"),
                )
                return BK_DUP_WARN
        except Exception:
            pass

        # Submit booking
        payload = {
            "customerName": context.user_data.get("bk_name", ""),
            "phone": context.user_data.get("bk_phone", ""),
            "date": date_str,
            "timeSlot": time_str,
            "consoleType": context.user_data.get("bk_console", "PS5"),
            "durationMins": context.user_data.get("bk_duration_mins", 60),
            "gameName": context.user_data.get("bk_game", ""),
            "telegramChatId": uid,
            "username": user.username or "",
            "status": "pending",
        }

        try:
            result = await _api._api_post("bookings", payload)
            if result and isinstance(result, dict) and result.get("id"):
                bk_id = result["id"]
                context.user_data["_bk_last_id"] = bk_id
                await query.edit_message_text(
                    f"✅ *Booking Confirmed!*\\n\\n"
                    f"🎫 Booking #{bk_id}\\n"
                    f"📅 {date_str}  ⏰ {time_str}\\n"
                    f"🎮 {payload['consoleType']}  ⏱️ {payload['durationMins']} mins\\n"
                    f"🕹️ {payload['gameName']}\\n\\n"
                    f"_Staff မှ confirm လုပ်ပြီးပါက အကြောင်းကြားပါမည်_ 🎮",
                    parse_mode="Markdown",
                )
                # Notify staff
                asyncio.create_task(_api.track_usage(user, "booking_created"))
                return ConversationHandler.END
            else:
                await query.edit_message_text(
                    "❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ သို့မဟုတ် Admin ကို ဆက်သွယ်ပါ",
                )
                return ConversationHandler.END
        except Exception as e:
            logger.error("Booking submission failed: %s", e)
            await query.edit_message_text(
                "❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ သို့မဟုတ် Admin ကို ဆက်သွယ်ပါ",
            )
            return ConversationHandler.END

    await query.edit_message_text("❌ Invalid confirmation.")
    return BK_CONFIRM"""

new_confirm = """async def bk_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle booking confirmation and submission to API — ReplyKeyboard version.\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == "❌ ပယ်ဖျက်မည်":
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Booking ဖျက်လိုက်ပါပြီ",
            reply_markup=MAIN_MENU_KB,
        )
        return ConversationHandler.END

    if text in ("✅ Confirm Booking", "⚠️ ဒါပေမဲ့ ဆက်တင်မည်", "✅ ရပါတယ်"):
        await update.message.reply_text("⏳ Booking တင်နေသည်...")

        user = update.effective_user
        uid = str(user.id) if user else ""

        # Check for duplicate booking
        date_str = context.user_data.get("bk_date", "")
        time_str = context.user_data.get("bk_time", "")
        try:
            existing = await _api._api_get(
                f"search-bookings?telegram_chat_id={uid}&date={date_str}&status=confirmed"
            )
            existing = existing if isinstance(existing, list) else []
            dupes = [b for b in existing if b.get("timeSlot") == time_str]
            if dupes:
                await update.message.reply_text(
                    "⚠️ *Duplicate Booking Detected!*\\n\\n"
                    f"📅 {date_str} ⏰ {time_str} တွင် booking ရှိပြီးသားပါ\\n\\n"
                    "ဒါပေမဲ့ ဆက်တင်မလား?",
                    parse_mode="Markdown",
                    reply_markup=_make_warning_keyboard(
                        "⚠️ ဒါပေမဲ့ ဆက်တင်မည်",
                        "🔙 မတင်တော့ပါ",
                    ),
                )
                return BK_DUP_WARN
        except Exception:
            pass

        # Submit booking
        payload = {
            "customerName": context.user_data.get("bk_name", ""),
            "phone": context.user_data.get("bk_phone", ""),
            "date": date_str,
            "timeSlot": time_str,
            "consoleType": context.user_data.get("bk_console", "PS5"),
            "durationMins": context.user_data.get("bk_duration_mins", 60),
            "gameName": context.user_data.get("bk_game", ""),
            "telegramChatId": uid,
            "username": user.username or "",
            "status": "pending",
        }

        try:
            result = await _api._api_post("bookings", payload)
            if result and isinstance(result, dict) and result.get("id"):
                bk_id = result["id"]
                context.user_data["_bk_last_id"] = bk_id
                await update.message.reply_text(
                    f"✅ *Booking Confirmed!*\\n\\n"
                    f"🎫 Booking #{bk_id}\\n"
                    f"📅 {date_str}  ⏰ {time_str}\\n"
                    f"🎮 {payload['consoleType']}  ⏱️ {payload['durationMins']} mins\\n"
                    f"🕹️ {payload['gameName']}\\n\\n"
                    f"_Staff မှ confirm လုပ်ပြီးပါက အကြောင်းကြားပါမည်_ 🎮",
                    parse_mode="Markdown",
                    reply_markup=MAIN_MENU_KB,
                )
                # Notify staff
                asyncio.create_task(_api.track_usage(user, "booking_created"))
                return ConversationHandler.END
            else:
                await update.message.reply_text(
                    "❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ သို့မဟုတ် Admin ကို ဆက်သွယ်ပါ",
                    reply_markup=MAIN_MENU_KB,
                )
                return ConversationHandler.END
        except Exception as e:
            logger.error("Booking submission failed: %s", e)
            await update.message.reply_text(
                "❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ သို့မဟုတ် Admin ကို ဆက်သွယ်ပါ",
                reply_markup=MAIN_MENU_KB,
            )
            return ConversationHandler.END

    await update.message.reply_text("❌ Invalid confirmation.")
    return BK_CONFIRM"""

assert old_confirm in bh, "bk_confirm not found!"
bh = bh.replace(old_confirm, new_confirm)
print("✅ bk_confirm → text-based (ReplyKeyboard)")

# ── bk_dup_warn ──
old_dup_warn_func = """async def bk_dup_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle duplicate booking warning.\"\"\"
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_warn:dup_ok":
        # Continue with booking despite duplicate
        await query.edit_message_text("⏳ Booking တင်နေသည် (duplicate warning overridden)...")

        user = update.effective_user
        uid = str(user.id) if user else ""

        payload = {
            "customerName": context.user_data.get("bk_name", ""),
            "phone": context.user_data.get("bk_phone", ""),
            "date": context.user_data.get("bk_date", ""),
            "timeSlot": context.user_data.get("bk_time", ""),
            "consoleType": context.user_data.get("bk_console", "PS5"),
            "durationMins": context.user_data.get("bk_duration_mins", 60),
            "gameName": context.user_data.get("bk_game", ""),
            "telegramChatId": uid,
            "username": user.username or "",
            "status": "pending",
        }

        try:
            result = await _api._api_post("bookings", payload)
            if result and isinstance(result, dict) and result.get("id"):
                bk_id = result["id"]
                await query.edit_message_text(
                    f"✅ *Booking Confirmed!*\\n\\n"
                    f"🎫 Booking #{bk_id}\\n"
                    f"📅 {payload['date']}  ⏰ {payload['timeSlot']}\\n"
                    f"🎮 {payload['consoleType']}  ⏱️ {payload['durationMins']} mins\\n\\n"
                    f"_Staff မှ confirm လုပ်ပြီးပါက အကြောင်းကြားပါမည်_ 🎮",
                    parse_mode="Markdown",
                )
            else:
                await query.edit_message_text("❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ")
        except Exception as e:
            logger.error("Booking submission (dup override) failed: %s", e)
            await query.edit_message_text("❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ")

        return ConversationHandler.END

    elif data == "bk_ok:no":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    await query.edit_message_text("❌ Invalid option.")
    return BK_DUP_WARN"""

new_dup_warn_func = """async def bk_dup_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle duplicate booking warning — ReplyKeyboard version.\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == "⚠️ ဒါပေမဲ့ ဆက်တင်မည်":
        # Continue with booking despite duplicate
        await update.message.reply_text("⏳ Booking တင်နေသည် (duplicate warning overridden)...")

        user = update.effective_user
        uid = str(user.id) if user else ""

        payload = {
            "customerName": context.user_data.get("bk_name", ""),
            "phone": context.user_data.get("bk_phone", ""),
            "date": context.user_data.get("bk_date", ""),
            "timeSlot": context.user_data.get("bk_time", ""),
            "consoleType": context.user_data.get("bk_console", "PS5"),
            "durationMins": context.user_data.get("bk_duration_mins", 60),
            "gameName": context.user_data.get("bk_game", ""),
            "telegramChatId": uid,
            "username": user.username or "",
            "status": "pending",
        }

        try:
            result = await _api._api_post("bookings", payload)
            if result and isinstance(result, dict) and result.get("id"):
                bk_id = result["id"]
                await update.message.reply_text(
                    f"✅ *Booking Confirmed!*\\n\\n"
                    f"🎫 Booking #{bk_id}\\n"
                    f"📅 {payload['date']}  ⏰ {payload['timeSlot']}\\n"
                    f"🎮 {payload['consoleType']}  ⏱️ {payload['durationMins']} mins\\n\\n"
                    f"_Staff မှ confirm လုပ်ပြီးပါက အကြောင်းကြားပါမည်_ 🎮",
                    parse_mode="Markdown",
                    reply_markup=MAIN_MENU_KB,
                )
            else:
                await update.message.reply_text(
                    "❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ",
                    reply_markup=MAIN_MENU_KB,
                )
        except Exception as e:
            logger.error("Booking submission (dup override) failed: %s", e)
            await update.message.reply_text(
                "❌ Booking တင်မရပါ — ခဏနေ ပြန်ကြိုးစားပါ",
                reply_markup=MAIN_MENU_KB,
            )

        return ConversationHandler.END

    elif text == "🔙 မတင်တော့ပါ":
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Booking ဖျက်လိုက်ပါပြီ",
            reply_markup=MAIN_MENU_KB,
        )
        return ConversationHandler.END

    await update.message.reply_text("❌ Invalid option.")
    return BK_DUP_WARN"""

assert old_dup_warn_func in bh, "bk_dup_warn function not found!"
bh = bh.replace(old_dup_warn_func, new_dup_warn_func)
print("✅ bk_dup_warn → text-based (ReplyKeyboard)")

# ── bk_disc_warn ──
old_disc_warn = """async def bk_disc_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle discount/conflict warning for booking.\"\"\"
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_warn:disc_ok":
        # Proceed to confirmation
        summary = _format_booking_summary(context)
        await query.edit_message_text(
            summary + "\\n\\n⚠️ Discount conflicted but continuing...\\n✅ Confirm လုပ်မလား?",
            parse_mode="Markdown",
            reply_markup=_make_confirm_keyboard(),
        )
        return BK_CONFIRM

    elif data == "bk_ok:no":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    await query.edit_message_text("❌ Invalid option.")
    return BK_DISC_WARN"""

new_disc_warn = """async def bk_disc_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle discount/conflict warning for booking — ReplyKeyboard version.\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == "⚠️ ဒါပေမဲ့ ဆက်တင်မည်":
        # Proceed to confirmation
        summary = _format_booking_summary(context)
        await update.message.reply_text(
            summary + "\\n\\n⚠️ Discount conflicted but continuing...\\n✅ Confirm လုပ်မလား?",
            parse_mode="Markdown",
            reply_markup=_make_confirm_keyboard(),
        )
        return BK_CONFIRM

    elif text == "🔙 မတင်တော့ပါ":
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Booking ဖျက်လိုက်ပါပြီ",
            reply_markup=MAIN_MENU_KB,
        )
        return ConversationHandler.END

    await update.message.reply_text("❌ Invalid option.")
    return BK_DISC_WARN"""

assert old_disc_warn in bh, "bk_disc_warn not found!"
bh = bh.replace(old_disc_warn, new_disc_warn)
print("✅ bk_disc_warn → text-based (ReplyKeyboard)")

# ── bk_con_conflict ──
old_conflict = """async def bk_con_conflict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle console conflict warning.\"\"\"
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "bk_warn:conf_ok":
        # Proceed despite conflict
        summary = _format_booking_summary(context)
        await query.edit_message_text(
            summary + "\\n\\n⚠️ Console conflict detected but continuing...\\n✅ Confirm လုပ်မလား?",
            parse_mode="Markdown",
            reply_markup=_make_confirm_keyboard(),
        )
        return BK_CONFIRM

    elif data == "bk_warn:change_time":
        # Go back to time selection
        date_str = context.user_data.get("bk_date", "")
        free_slots = await _get_available_slots(date_str)
        await query.edit_message_text(
            f"📅 *{date_str}* — အခြားအချိန် ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=_make_time_keyboard(free_slots),
        )
        return BK_TIME

    elif data == "bk_warn:change_console":
        await query.edit_message_text(
            "🎮 အခြား console ရွေးပါ:",
            reply_markup=_make_console_keyboard(),
        )
        return BK_CONSOLE

    elif data == "bk_ok:no":
        context.user_data.clear()
        await query.edit_message_text("❌ Booking ဖျက်လိုက်ပါပြီ")
        return ConversationHandler.END

    await query.edit_message_text("❌ Invalid option.")
    return BK_CON_CONFLICT"""

new_conflict = """async def bk_con_conflict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handle console conflict warning — ReplyKeyboard version.\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result

    if text == "⚠️ ဒါပေမဲ့ ဆက်တင်မည်" or text == "✅ ရပါတယ်":
        # Proceed despite conflict
        summary = _format_booking_summary(context)
        await update.message.reply_text(
            summary + "\\n\\n⚠️ Console conflict detected but continuing...\\n✅ Confirm လုပ်မလား?",
            parse_mode="Markdown",
            reply_markup=_make_confirm_keyboard(),
        )
        return BK_CONFIRM

    elif text == "⏰ အချိန် ပြောင်းမည်":
        # Go back to time selection
        date_str = context.user_data.get("bk_date", "")
        free_slots = await _get_available_slots(date_str)
        await update.message.reply_text(
            f"📅 *{date_str}* — အခြားအချိန် ရွေးပါ:",
            parse_mode="Markdown",
            reply_markup=_make_time_keyboard(free_slots),
        )
        return BK_TIME

    elif text == "🎮 ဂိမ်း ပြောင်းရွေးမည်":
        await update.message.reply_text(
            "🎮 အခြား console ရွေးပါ:",
            reply_markup=_make_console_keyboard(),
        )
        return BK_CONSOLE

    elif text == "🔙 မတင်တော့ပါ":
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Booking ဖျက်လိုက်ပါပြီ",
            reply_markup=MAIN_MENU_KB,
        )
        return ConversationHandler.END

    await update.message.reply_text("❌ Invalid option.")
    return BK_CON_CONFLICT"""

assert old_conflict in bh, "bk_con_conflict not found!"
bh = bh.replace(old_conflict, new_conflict)
print("✅ bk_con_conflict → text-based (ReplyKeyboard)")

# ═══ 2d. bk_end_handler ── ensure it restores main menu ──
old_end_h = """async def bk_end_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Fallback handler for BK_END state (sentinel -1).\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result
    await update.message.reply_text(
        "Booking session ended. Use 📅 Booking to start a new booking.",
        reply_markup=MAIN_MENU_KB,
    )
    return ConversationHandler.END"""

new_end_h = """async def bk_end_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Fallback handler for BK_END state (sentinel -1). Restores main menu keyboard.\"\"\"
    text = (update.message.text or "").strip()
    menu_result = await _bk_intercept_menu(text, update, context)
    if menu_result:
        return menu_result
    await update.message.reply_text(
        "Booking session ended. Use 📅 Booking to start a new booking.",
        reply_markup=MAIN_MENU_KB,
    )
    return ConversationHandler.END"""

assert old_end_h in bh, "bk_end_handler not found!"
bh = bh.replace(old_end_h, new_end_h)
print("✅ bk_end_handler → ensures MAIN_MENU_KB restored")

with open(BOOKING_HANDLERS, "w") as f:
    f.write(bh)

print(f"✅ Patched {BOOKING_HANDLERS} — all handlers converted to ReplyKeyboard")

# ══════════════════════════════════════════════════════════
# 3. main.py — ConversationHandler registrations
# ══════════════════════════════════════════════════════════

with open(MAIN, "r") as f:
    m = f.read()

old_conv = """    bk_conv = ConversationHandler(
        entry_points=[
            CommandHandler("book", cmd_book),
            CommandHandler("booking", cmd_book),
            MessageHandler(filters.Regex("^" + re.escape(BTN_BOOK) + "$"), cmd_book),
        ],
        states={
            BK_MEMBER_CHECK:  [CallbackQueryHandler(bk_member_check_entry, pattern=r"^bk_mem:")],
            BK_MEMBER_SELECT: [CallbackQueryHandler(bk_member_select, pattern=r"^bk_sel:"), MessageHandler(filters.TEXT & ~filters.COMMAND, bk_member_select)],
            BK_PHONE_VERIFY:  [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_phone_verify)],
            BK_DATA_CONFIRM:  [CallbackQueryHandler(bk_data_confirm, pattern=r"^bk_dc:")],
            BK_NAME:          [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_name_entry)],
            BK_PHONE:         [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_phone_entry)],
            BK_DATE:          [CallbackQueryHandler(bk_date_select, pattern=r"^bkdate:")],
            BK_TIME:          [
                CallbackQueryHandler(bk_time_select, pattern=r"^(bktime:|bk_custom:)"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bk_time_text_input),
            ],
            BK_CONSOLE:       [CallbackQueryHandler(bk_console_select, pattern=r"^bk_con:")],
            BK_DURATION:      [CallbackQueryHandler(bk_duration_select, pattern=r"^bk_dur:")],
            BK_GAME:          [CallbackQueryHandler(bk_game_select, pattern=r"^(bk_game:|bk_game_page:)")],
            BK_CONSOLE_PREF:  [CallbackQueryHandler(bk_console_pref, pattern=r"^bk_con:")],
            BK_CONFIRM:       [CallbackQueryHandler(bk_confirm, pattern=r"^bk_ok:")],
            BK_DUP_WARN:      [CallbackQueryHandler(bk_dup_warn, pattern=r"^(bk_warn:|bk_ok:)")],
            BK_DISC_WARN:     [CallbackQueryHandler(bk_disc_warn, pattern=r"^(bk_warn:|bk_ok:)")],
            BK_CON_CONFLICT:  [CallbackQueryHandler(bk_con_conflict, pattern=r"^(bk_warn:|bk_ok:)")],
            BK_END:           [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_end_handler)],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )"""

new_conv = """    bk_conv = ConversationHandler(
        entry_points=[
            CommandHandler("book", cmd_book),
            CommandHandler("booking", cmd_book),
            MessageHandler(filters.Regex("^" + re.escape(BTN_BOOK) + "$"), cmd_book),
        ],
        states={
            BK_MEMBER_CHECK:  [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_member_check_entry)],
            BK_MEMBER_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_member_select)],
            BK_PHONE_VERIFY:  [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_phone_verify)],
            BK_DATA_CONFIRM:  [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_data_confirm)],
            BK_NAME:          [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_name_entry)],
            BK_PHONE:         [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_phone_entry)],
            BK_DATE:          [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_date_select)],
            BK_TIME:          [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_time_select)],
            BK_CONSOLE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_console_select)],
            BK_DURATION:      [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_duration_select)],
            BK_GAME:          [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_game_select)],
            BK_CONSOLE_PREF:  [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_console_pref)],
            BK_CONFIRM:       [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_confirm)],
            BK_DUP_WARN:      [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_dup_warn)],
            BK_DISC_WARN:     [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_disc_warn)],
            BK_CON_CONFLICT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_con_conflict)],
            BK_END:           [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_end_handler)],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )"""

assert old_conv in m, "ConversationHandler not found in main.py!"
m = m.replace(old_conv, new_conv)

with open(MAIN, "w") as f:
    f.write(m)

print(f"✅ Patched {MAIN} — all handlers converted to MessageHandler")
print("\n=== ALL PATCHES APPLIED SUCCESSFULLY ===")
