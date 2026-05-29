from bot import *
try:
    from bot.api_client import api_add_sales_record, api_add_stock_out
except ImportError:
    def api_add_sales_record(data): return None
    def api_add_stock_out(data): return None
"""PS VIBE Bot — Handler module.

"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta

# Explicit import for helper from stock module
# update_inv_total_k1 imported lazily inside functions to avoid circular deps

def next_voucher() -> str:
    """Generate next sequential voucher number (YYYYMMDD-NNN)."""
    from datetime import datetime
    import random
    now = datetime.now()
    return f"{now.strftime('%Y%m%d')}-{random.randint(100, 999)}"





async def prompt_member(update: Update, context: ContextTypes.DEFAULT_TYPE,
                        search_results: list | None = None, query: str = ""):
    v_no    = context.user_data["v_no"]
    members = fetch_members()

    if search_results is not None:
        # Filtered view after a search query
        display  = search_results
        hint     = f"🔍 *\"{query}\"* — {len(display)} ရလဒ် တွေ့သည်\n"
    else:
        display  = members
        hint     = "🔍 _ID ရိုက်ပြီး ရှာနိုင်သည်_ (e.g. `PSV_A`)\n" if len(members) > 5 else ""

    # Guest always pinned at top; members below
    kb = [["0 (Guest)"]] + [[m] for m in display] + [[BTN_BACK_MAIN, BTN_CANCEL]]
    await update.message.reply_text(
        step_hdr(1, 6, "Select Member") +
        f"📋 Voucher: *{v_no}*\n\n"
        f"{hint}"
        f"👤 Member ID ရွေးပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return MEMBER

async def prompt_console(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m_id        = context.user_data.get("m_id", "")
    is_guest    = m_id.strip() == "0 (Guest)"
    label       = "Guest" if is_guest else m_id
    wallet_mins = context.user_data.get("wallet_mins")

    if not is_guest and wallet_mins is not None:
        balance_line = f"\n💰 *Wallet Balance: {wallet_mins:,} mins*"
        if wallet_mins <= 0:
            balance_line += "  ⚠️ _Wallet ကုန်ဆုံးနေပြီ!_"
    else:
        balance_line = ""

    try:
        _cons = [c["id"] for c in fetch_console_status()]
    except Exception as e:
        logging.warning("Failed to fetch console status for booking keyboard: %s", e)
        _cons = sorted(VALID_CONSOLES)
    kb  = [_cons[i:i+3] for i in range(0, len(_cons), 3)]
    kb += [NAV_ROW]
    await update.message.reply_text(
        step_hdr(2, 6, "Select Console") +
        f"👤 *{label}*{balance_line}\n\n"
        "🕹️ Console ID ရွေးပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return CONSOLE

async def prompt_mins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet_mins = context.user_data.get("wallet_mins")
    m_id        = context.user_data.get("m_id", "")
    c_id        = context.user_data.get("c_id", "")
    is_guest    = m_id.strip() == "0 (Guest)"
    label       = "Guest" if is_guest else m_id

    if not is_guest and wallet_mins is not None:
        wallet_line = f"\n💰 *Wallet Balance: {wallet_mins:,} mins*"
        if wallet_mins <= 0:
            wallet_line += "  ⚠️ _Wallet ပိုင်ဆိုင်မှုကုန်ဆုံးနေပြီ!_"
    else:
        wallet_line = ""

    kb_mins = [
        ["30", "60", "90"],
        ["120", "150", "180"],
        ["240", "300", "360"],
        NAV_ROW,
    ]
    await update.message.reply_text(
        step_hdr(3, 6, "Play Time (Mins)") +
        f"👤 *{label}*  |  🕹️ *{c_id}*{wallet_line}\n\n"
        f"🕒 Play Mins ကို ရွေးပါ — သို့မဟုတ် ရိုက်ထည့်ပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb_mins, one_time_keyboard=True, resize_keyboard=True),
    )
    return MINS

async def prompt_adjust_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show ±10 min time adjustment step (only for from_session=True flows)."""
    mins = context.user_data.get("mins", 0)
    kb = ReplyKeyboardMarkup([
        ["-10 min", "-5 min", "-3 min"],
        ["-2 min", "-1 min", "+1 min"],
        ["+2 min", "+3 min", "+5 min"],
        ["+10 min"],
        ["⏩ ပြောင်းမည်မဟုတ်"],
    ], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "⏱️ <b>Game Play Time Adjust</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📌 Recorded Time: <b>{mins} mins</b>\n\n"
        "±10 မိနစ်အတွင်း adjust လုပ်နိုင်သည်\n"
        "ပြောင်းလဲမှု မရှိလျှင် ⏩ ကိုနှိပ်ပါ",
        parse_mode="HTML",
        reply_markup=kb,
    )
    return ADJUST_TIME

async def step_adjust_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time adjustment input."""
    text = update.message.text.strip()
    mins = context.user_data.get("mins", 0)

    if text == "⏩ ပြောင်းမည်မဟုတ်":
        # No change — proceed to food menu
        return await prompt_food_menu(update, context)

    # Parse delta — accept button labels like "-5 min" or raw numbers like "-3"
    import re as _re
    m = _re.search(r'([+-]?\d+)', text.replace(" min", ""))
    if not m:
        await update.message.reply_text(
            "❌ မမှန်ကန်သော input — ဂဏန်းသာ ထည့်ပါ (ဥပမာ: -5 သို့မဟုတ် +3)",
            reply_markup=ReplyKeyboardRemove(),
        )
        return await prompt_adjust_time(update, context)

    delta = int(m.group(1))
    if abs(delta) > 10:
        await update.message.reply_text(
            f"❌ ±10 မိနစ်သာ adjust လုပ်ခွင့်ရှိသည် (သင်ထည့်သည်: {delta:+d} min)",
            reply_markup=ReplyKeyboardRemove(),
        )
        return await prompt_adjust_time(update, context)

    new_mins = max(1, mins + delta)
    context.user_data["mins"] = new_mins
    context.user_data["actual_play_mins"] = new_mins

    sign = "+" if delta > 0 else ""
    await update.message.reply_text(
        "✅ <b>Time Adjusted!</b>\n"
        f"  {mins} mins → <b>{new_mins} mins</b>  ({sign}{delta} min)",
        parse_mode="HTML",
    )
    return await prompt_food_menu(update, context)

async def prompt_food_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prices     = context.user_data.get("food_prices", {})
    cart_items = context.user_data.get("food_items", [])

    # ── Safety: rebuild stock_map if missing/empty ──
    stock_map = context.user_data.get("food_stock_map")
    if not stock_map:
        try:
            inv_data = _replit_get("sheets/inventory")
            if inv_data and isinstance(inv_data, dict):
                stock_map = {i["name"]: max(0, i.get("current_stock", 0))
                             for i in inv_data.get("items", [])}
                if stock_map:
                    prices = {k: v for k, v in prices.items()
                              if stock_map.get(k, 1) > 0}
                    context.user_data["food_prices"] = prices
            stock_map = stock_map or {}
        except Exception as e:
            logger.warning("prompt_food_menu: stock_map rebuild failed: %s", e)
            stock_map = {}
        context.user_data["food_stock_map"] = stock_map

    # If prices empty after stock filter, return gracefully to main menu
    if not prices:
        await update.message.reply_text(
            "\u26a0\ufe0f Food Menu \u1019\u101b\u1014\u102d\u102f\u1004\u103a\u1015\u102b (stock data \u1019\u1006\u103d\u1032\u1014\u102d\u102f\u1004\u103a)\u104a Main Menu \u101e\u102d\u102f\u1037\u1015\u103c\u1014\u103a\u101e\u103d\u102c\u1038\u1015\u102b\u1019\u100a\u1037\u103a\u104b",
            reply_markup=ReplyKeyboardRemove(),
        )
        return await cmd_cancel(update, context)

    names      = list(prices.keys())
    rows       = [names[i: i + 2] for i in range(0, len(names), 2)]
    clear_row  = [[BTN_CLEAR_CART]] if cart_items else []
    kb         = rows + [[BTN_DONE]] + clear_row + [NAV_ROW]

    # Price list
    price_lines = [f"  • {n}  —  {p:,} Ks" for n, p in prices.items()]
    price_block = "\n".join(price_lines) if price_lines else "  (menu မရှိပါ)"

    # Running cart (already fetched above)
    if cart_items:
        cart_lines    = [f"  ✓ {i['name']} x{i['qty']} = {i['subtotal']:,} Ks" for i in cart_items]
        cart_subtotal = sum(i["subtotal"] for i in cart_items)
        cart_block = (
            f"\n🛒 *ရွေးပြီးသားပစ္စည်း:*\n"
            + "\n".join(cart_lines)
            + f"\n  ─ Subtotal: *{cart_subtotal:,} Ks*\n"
        )
    else:
        cart_block = ""

    await update.message.reply_text(
        step_hdr(4, 6, "Food & Drinks") +
        f"📋 *Menu & Prices:*\n{price_block}\n"
        f"{cart_block}\n"
        f"🍔 Food & Drink ရွေးပါ (မရှိလျှင် Done ✅) -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return FOOD_MENU

async def prompt_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d         = context.user_data
    mins      = d["mins"]
    base_rate = fetch_base_rate()
    d["base_rate"] = base_rate
    is_guest  = d["m_id"].strip() == "0 (Guest)"

    food_lines, food_total = [], 0
    for item in d["food_items"]:
        food_lines.append(f"  • {item['name']} x{item['qty']} = {item['subtotal']:,} Ks")
        food_total += item["subtotal"]
    food_sec = "\n".join(food_lines) if food_lines else "  • မရှိပါ"

    if is_guest:
        multiplier   = fetch_console_multiplier(d.get("c_id", ""))
        game_amt     = round((mins * base_rate * multiplier) / 60)
        net_total    = game_amt + food_total
        mult_display = f"{multiplier:g}"
        d.update(game_amt=game_amt, food_total=food_total,
                 net_total=net_total, remaining_mins=None, multiplier=multiplier)

        body = (
            f"🕹️ Console: *{d.get('c_id', '-')}*\n"
            f"📊 Rate Multiplier: *{mult_display}x*\n"
            f"🎮 Game: {mins} min ({base_rate:,} Ks/hr × {mult_display}) = *{game_amt:,} Ks*\n"
            f"🍔 Food & Drink:\n{food_sec}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 Food Total: *{food_total:,} Ks*\n"
            f"✅ *Net Payable: {net_total:,} Ks*"
        )
        title = "📋 *စာရင်းအချုပ် — Guest*"

    else:
        cash_down_ks = d.get("cash_down_ks", 0)
        actual_mins  = d.get("actual_play_mins", mins)

        if cash_down_ks > 0:
            # Member + Cash Down: shortfall paid as cash
            game_amt  = cash_down_ks
            net_total = game_amt + food_total
            wallet_bal = d.get("wallet_mins", 0)
            d["remaining_mins"] = 0
            d.update(game_amt=game_amt, food_total=food_total, net_total=net_total)
            wallet_block = (
                f"⏳ Wallet: {wallet_bal} mins → 0 (fully used)\n"
                f"🎮 Actual Play: {actual_mins} mins\n"
                f"💵 Cash Down: *{cash_down_ks:,} Ks* (shortfall)\n"
            )
            title = "📋 *စာရင်းအချုပ် — Member + Cash Down*"
        else:
            game_amt  = 0
            net_total = food_total
            wallet_mins       = d.get("wallet_mins")
            effective_cost    = d.get("effective_cost_mins", mins)
            multiplier_val    = d.get("multiplier", 1.0)
            if wallet_mins is not None:
                remaining = wallet_mins - effective_cost
                d["remaining_mins"] = remaining

                # Safety guard — if wallet still insufficient (e.g. stale balance from
                # previous cash-down session), redirect to shortfall screen instead of
                # allowing a negative-balance save.
                if remaining < 0:
                    base_rate_val = d.get("base_rate", fetch_base_rate())
                    shortfall_mins = -remaining
                    shortfall_ks   = round(shortfall_mins * base_rate_val / 60)
                    d["shortfall_mins"] = shortfall_mins
                    d["shortfall_ks"]   = shortfall_ks
                    await update.message.reply_text(
                        f"⚠️ <b>Wallet မလောက်ပါ!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"💳 Balance  : <b>{wallet_mins} mins</b>\n"
                        f"🎮 Cost     : <b>{effective_cost} mins</b>\n"
                        f"❗ Shortfall: <b>{shortfall_mins} mins ≈ {shortfall_ks:,} Ks</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"Top Up (သို့) Cash Down ရွေးပါ",
                        parse_mode="HTML",
                    )
                    return await prompt_session_shortfall(update, context)

                mult_tag = f" ×{multiplier_val:g}" if multiplier_val != 1.0 else ""
                wallet_block = (
                    f"⏳ Wallet Balance: {wallet_mins} mins\n"
                    f"🎮 Play: {mins} mins{mult_tag} → Cost: {effective_cost} wallet mins\n"
                    f"📉 Remaining: {remaining} mins\n"
                )
            else:
                d["remaining_mins"] = None
                wallet_block = f"🎮 Playing: {mins} mins\n"
            d.update(game_amt=game_amt, food_total=food_total, net_total=net_total)
            title = "📋 *စာရင်းအချုပ် — Member*"

        body = (
            f"💳 Member: *{d['m_id']}*\n"
            f"{wallet_block}"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🍔 Food & Drink:\n{food_sec}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Net Payable: {net_total:,} Ks*"
        )

    text = (
        step_hdr(5, 6, "Review Summary") +
        f"{title}\n━━━━━━━━━━━━━━━━━━\n{body}\n\n"
        f"မှန်ကန်ပါသလား? Yes နှိပ်ပြီး Payment ဆက်သွားပါ -"
    )
    kb   = [[BTN_YES], NAV_ROW]
    await update.message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True),
    )
    return CONFIRM_SUMMARY

async def prompt_kpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show dynamic payment method buttons from Setting!Y + Done button."""
    d = context.user_data
    net = d.get("net_total", 0)
    m_id = d.get("m_id", "-")
    c_id = d.get("c_id", "-")
    label = "Guest" if m_id.strip() == "0 (Guest)" else m_id

    if "payments" not in d:
        d["payments"] = {}

    methods = fetch_payment_methods()
    paid_so_far = sum(d["payments"].values())
    remaining = net - paid_so_far

    kb = [[m] for m in methods]
    kb.append([BTN_PAY_DONE])
    kb.append(NAV_ROW)

    payment_status = ""
    if d["payments"]:
        lines = []
        for method, amt in d["payments"].items():
            lines.append(f"  • {method}: *{amt:,} Ks*")
        payment_status = "\n".join(lines) + f"\n  ─ Paid: *{paid_so_far:,} Ks*  |  Remaining: *{remaining:,} Ks*\n\n"

    await update.message.reply_text(
        step_hdr(6, 6, "Payment — Method") +
        f"👤 *{label}*  |  🕹️ *{c_id}*\n"
        f"💰 Total: *{net:,} Ks*\n\n"
        f"{payment_status}"
        f"💳 Payment Method ရွေးပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return PAY_METHOD

async def step_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK_MAIN:
        return await show_main_menu(update, context)
    if text == BTN_BACK:
        return await prompt_member(update, context)

    members = fetch_members()

    # ── Exact match (keyboard tap or exact type) ──────────────────────────
    if text == "0 (Guest)" or text in members:
        context.user_data["m_id"] = text
        if text != "0 (Guest)":
            context.user_data["wallet_mins"] = fetch_wallet_mins(text)
        else:
            context.user_data["wallet_mins"] = None
        if text != "0 (Guest)":
            return await _check_member_in_session(update, context, text)
        return await prompt_console(update, context)

    # ── Search mode: partial match on ID (case-insensitive) ──────────────
    query   = text
    matches = [m for m in members if query.upper() in m.upper()]

    if len(matches) == 1:
        # Auto-select the single result
        context.user_data["m_id"] = matches[0]
        context.user_data["wallet_mins"] = fetch_wallet_mins(matches[0])
        await update.message.reply_text(
            f"✅ *{matches[0]}* ကို ရွေးချယ်လိုက်သည်",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return await _check_member_in_session(update, context, matches[0])

    if matches:
        # Show filtered keyboard
        return await prompt_member(update, context, search_results=matches, query=query)

    # No match at all
    await update.message.reply_text(
        f"⚠️ *\"{query}\"* နှင့် ကိုက်ညီသော Member မတွေ့ပါ\n"
        f"_ID တစ်စိတ်တစ်ဒေသ ရိုက်ထည့်ပြီး ထပ်ကြိုးစားပါ -_",
        parse_mode="Markdown",
    )
    return await prompt_member(update, context)

async def step_console(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        context.user_data.pop("c_id", None)
        return await prompt_member(update, context)

    if text not in VALID_CONSOLES:
        await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ keyboard မှ Console ID ရွေးပါ -")
        return await prompt_console(update, context)

    context.user_data["c_id"] = text
    return await _check_console_in_session(update, context, text)

async def _check_member_in_session(update, context, member_id: str):
    """Check if member has active session(s). Shows all with per-console + combined options."""
    try:
        consoles = fetch_console_status()
    except Exception as e:
        logging.warning("Failed to fetch console status for member session check: %s", e)
        return await prompt_console(update, context)

    actives = [
        c for c in consoles
        if c.get("member") == member_id and c.get("status") in ("Active", "Scheduled")
    ]
    if not actives:
        return await prompt_console(update, context)

    # Store all active sessions
    context.user_data["_in_session_consoles"] = actives

    if len(actives) == 1:
        active  = actives[0]
        start_t = active.get("start", "?")
        _, dfmt = calc_duration(start_t) if start_t and start_t != "?" else (0, "?")
        await update.message.reply_text(
            f"⚠️ <b>{member_id}</b> သည် ဆက်ရှိနေဆဲ Session ရှိသည်!\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🕹️ Console : <b>{active['id']}</b>\n"
            f"🕐 Start   : <b>{start_t}</b>  ({dfmt})\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Session ကို End ပြီးမှ Sales Voucher ဆက်မလား?",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(
                [[BTN_YES_END_SESSION], [BTN_NO_RESELECT]], resize_keyboard=True),
        )
    else:
        lines = []
        kb    = []
        for c in actives:
            s = c.get("start", "?")
            _, dfmt = calc_duration(s) if s and s != "?" else (0, "?")
            lines.append(f"🕹️ <b>{c['id']}</b>  |  🕐 {s} ({dfmt})")
            kb.append([f"⏹ {c['id']} ကိုပဲ End"])
        kb.append(["⏹ ပေါင်းပြီး End (Combined Bill)"])
        kb.append([BTN_NO_RESELECT])
        await update.message.reply_text(
            f"⚠️ <b>{member_id}</b> — Active Session <b>{len(actives)} ခု</b> ရှိသည်!\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            + "\n".join(lines) +
            f"\n━━━━━━━━━━━━━━━━━━\n"
            f"ဘယ် Session ကို End မည်နည်း?",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
    return DS_MEMBER_IN_SESSION

async def _end_single_session_and_launch(update, context, active: dict, m_id: str):
    """End one session and launch the sales voucher for it."""
    bk_id         = active.get("booking_id", "")
    session_cid   = active.get("id", "")
    session_staff = active.get("staff", "")
    start_t       = active.get("start", "")
    total_mins, dur_fmt = calc_duration(start_t) if start_t else (0, "?")
    end_t = now_mmt().strftime("%H:%M")

    # Cancel any pending reminder loop for this console
    _cancel_remind(session_cid, update.effective_chat.id)
    # Also cancel using STAFF_NOTIFY_CHAT key (canonical key used since session start fix)
    if STAFF_NOTIFY_CHAT:
        _cancel_remind(session_cid, int(STAFF_NOTIFY_CHAT))

    ok = end_booking(bk_id) if bk_id else False
    if ok:
        await update.message.reply_text(
            f"✅ <b>Session ဆုံးပြီ!</b>\n"
            f"🕹️ {session_cid}  👤 {m_id}  ⏱ {dur_fmt} ({total_mins} mins)\n"
            f"🕐 {start_t} → {end_t}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📝 Sales Voucher ဖွင့်နေသည်...",
            parse_mode="HTML", reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await update.message.reply_text(
            "⚠️ Session end မရပါ — data ယူပြီး ဆက်သွားပါမည်", parse_mode="HTML")
    context.user_data.clear()
    return await launch_session_sale(update, context,
                                     session_cid, m_id, total_mins, session_staff)

async def step_ds_member_in_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle session-end choice after member-in-session warning in Daily Sales."""
    text    = update.message.text.strip()
    actives = context.user_data.get("_in_session_consoles", [])
    m_id    = context.user_data.get("m_id", "Guest")

    if text in (BTN_NO_RESELECT, BTN_CANCEL):
        context.user_data.pop("_in_session_consoles", None)
        context.user_data.pop("m_id", None)
        context.user_data.pop("wallet_mins", None)
        return await prompt_member(update, context)

    # Single-session shorthand button
    if text == BTN_YES_END_SESSION and actives:
        context.user_data.pop("_in_session_consoles", None)
        return await _end_single_session_and_launch(update, context, actives[0], m_id)

    # Per-console end: "⏹ C-09 ကိုပဲ End"
    for ac in actives:
        if text == f"⏹ {ac['id']} ကိုပဲ End":
            context.user_data.pop("_in_session_consoles", None)
            return await _end_single_session_and_launch(update, context, ac, m_id)

    # Combined bill: end ALL sessions, sum durations + pre-compute effective cost
    if text == "⏹ ပေါင်းပြီး End (Combined Bill)":
        context.user_data.pop("_in_session_consoles", None)
        total_mins          = 0
        total_effective_mins = 0
        session_staff       = ""
        cid_list            = []
        end_t               = now_mmt().strftime("%H:%M")
        summary_lines       = []
        for ac in actives:
            bk_id   = ac.get("booking_id", "")
            start_t = ac.get("start", "")
            mins, dfmt = calc_duration(start_t) if start_t else (0, "?")
            mult_i  = fetch_console_multiplier(ac["id"])
            eff_i   = round(mins * mult_i)
            total_mins           += mins
            total_effective_mins += eff_i
            end_booking(bk_id)
            cid_list.append(ac["id"])
            if not session_staff:
                session_staff = ac.get("staff", "")
            mult_tag = f" ×{mult_i:g}" if mult_i != 1.0 else ""
            summary_lines.append(
                f"🕹️ {ac['id']}{mult_tag}  ⏱ {dfmt} ({mins} mins → {eff_i} wallet mins)  🕐 {start_t}→{end_t}"
            )
        combined_cid = "+".join(cid_list)
        await update.message.reply_text(
            f"✅ <b>Sessions ဆုံးပြီ! (Combined)</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            + "\n".join(summary_lines) +
            f"\n━━━━━━━━━━━━━━━━━━\n"
            f"👤 {m_id}  |  ⏱ Play: <b>{total_mins} mins</b>  |  💳 Cost: <b>{total_effective_mins} wallet mins</b>\n"
            f"📝 Combined Sales Voucher ဖွင့်နေသည်...",
            parse_mode="HTML", reply_markup=ReplyKeyboardRemove(),
        )
        context.user_data.clear()
        return await launch_session_sale(update, context,
                                         combined_cid, m_id, total_mins, session_staff,
                                         pre_effective_mins=total_effective_mins)

    # Unrecognised — re-show (restore actives first)
    context.user_data["_in_session_consoles"] = actives
    return await _check_member_in_session(update, context, m_id)

async def _check_console_in_session(update, context, console_id: str):
    """Check if the chosen console has an active session. If yes → prompt."""
    try:
        consoles = fetch_console_status()
    except Exception as e:
        logging.warning("Failed to fetch console status for console session check: %s", e)
        return await prompt_mins(update, context)

    active = next(
        (c for c in consoles if c.get("id") == console_id
         and c.get("status") in ("Active", "Scheduled")),
        None,
    )
    if not active:
        return await prompt_mins(update, context)

    context.user_data["_in_session_console"] = active
    start_t  = active.get("start", "?")
    mbr      = active.get("member", "Guest")
    _, dur_fmt = calc_duration(start_t) if start_t and start_t != "?" else (0, "?")
    await update.message.reply_text(
        f"⚠️ <b>{console_id}</b> သည် Active Session ရှိနေသည်!\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 Member : <b>{mbr}</b>\n"
        f"🕐 Start  : <b>{start_t}</b>  ({dur_fmt})\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"ဒီ Session ကို End ပြီးမှ ဆက်မလား?",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([[BTN_YES_END_SESSION], [BTN_NO_RESELECT]],
                                         resize_keyboard=True),
    )
    return DS_CONSOLE_IN_SESSION

async def step_ds_console_in_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Yes/No after console-in-session warning in Daily Sales."""
    text = update.message.text.strip()

    if text == BTN_NO_RESELECT or text == BTN_CANCEL:
        context.user_data.pop("_in_session_console", None)
        context.user_data.pop("c_id", None)
        return await prompt_console(update, context)

    if text == BTN_YES_END_SESSION:
        active        = context.user_data.pop("_in_session_console", {})
        bk_id         = active.get("booking_id", "")
        session_cid   = context.user_data.get("c_id") or active.get("id", "")
        session_mbr   = active.get("member", "Guest")
        session_staff = active.get("staff", "")
        start_t       = active.get("start", "")
        total_mins, dur_fmt = calc_duration(start_t) if start_t else (0, "?")

        ok = end_booking(bk_id) if bk_id else False
        end_t = now_mmt().strftime("%H:%M")
        status_msg = (
            f"✅ <b>Session ဆုံးပြီ!</b>\n"
            f"🕹️ {session_cid}  👤 {session_mbr}  ⏱ {dur_fmt} ({total_mins} mins)\n"
            f"🕐 {start_t} → {end_t}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📝 Sales Voucher ဖွင့်နေသည်..."
        ) if ok else (
            f"⚠️ Session end မရပါ — data ယူပြီး ဆက်သွားပါမည်"
        )
        await update.message.reply_text(status_msg, parse_mode="HTML",
                                        reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return await launch_session_sale(update, context,
                                         session_cid, session_mbr, total_mins, session_staff)

    # Unrecognised — re-show prompt
    return await _check_console_in_session(update, context,
                                            context.user_data.get("c_id", ""))

async def step_mins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        context.user_data.pop("mins", None)
        return await prompt_console(update, context)

    try:
        mins = int(text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ ဂဏန်းသက်သက် ရိုက်ပေးပါ -")
        return MINS

    if mins <= 0:
        await update.message.reply_text("⚠️ မိနစ် 1 နှင့်အထက် ထည့်ပေးပါ -")
        return MINS

    context.user_data["mins"]       = mins
    context.user_data["food_items"] = []
    context.user_data["base_rate"]  = fetch_base_rate()

    # Fetch food prices and filter out 0-stock items
    food_prices = fetch_food_prices()
    stock_map: dict = {}
    try:
        inv_data = _replit_get("sheets/inventory")
        if inv_data and isinstance(inv_data, dict):
            stock_map = {i["name"]: max(0, i.get("current_stock", 0))
                         for i in inv_data.get("items", [])}
            food_prices = {k: v for k, v in food_prices.items()
                           if stock_map.get(k, 1) > 0}
    except Exception as e:
        logger.warning("step_mins: stock fetch failed, showing all items: %s", e)
        stock_map = {}
    context.user_data["food_prices"]    = food_prices
    context.user_data["food_stock_map"] = stock_map
    return await prompt_food_menu(update, context)

async def step_food_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text

    if choice == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if choice == BTN_BACK:
        context.user_data.pop("mins", None)
        context.user_data.pop("food_items", None)
        return await prompt_mins(update, context)

    if choice == BTN_DONE:
        return await prompt_confirm(update, context)

    if choice == BTN_CLEAR_CART:
        context.user_data["food_items"] = []
        return await prompt_food_menu(update, context)

    prices = context.user_data.get("food_prices", {})
    if choice not in prices:
        await update.message.reply_text("⚠️ Menu မှ ရွေးချယ်ပါ သို့မဟုတ် Done ✅ နှိပ်ပါ -")
        return await prompt_food_menu(update, context)

    unit_price = prices.get(choice, 0)
    context.user_data["last_food"] = choice

    # Calculate remaining available stock (minus already in cart)
    stock_map   = context.user_data.get("food_stock_map", {}) or {}
    total_stock = stock_map.get(choice, 999)
    carted_qty  = sum(i["qty"] for i in context.user_data.get("food_items", []) if i["name"] == choice)
    max_qty     = max(0, total_stock - carted_qty)
    context.user_data["last_food_max"] = max_qty

    qty_btns = [str(q) for q in range(1, min(max_qty + 1, 6))]
    qty_row  = [qty_btns] if qty_btns else []
    stock_note = f"\n📦 Stock ကျန်: *{max_qty} pcs*" if total_stock < 999 else ""
    await update.message.reply_text(
        step_hdr(4, 6, "Food Qty") +
        f"🔢 *{choice}* ({unit_price:,} Ks/ခု){stock_note}\n\nအရေအတွက် ရွေးပါ သို့မဟုတ် ရိုက်ပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            qty_row + [NAV_ROW],
            one_time_keyboard=True, resize_keyboard=True,
        ),
    )
    return FOOD_QTY

async def step_food_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        context.user_data.pop("last_food", None)
        return await prompt_food_menu(update, context)

    try:
        qty = int(text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ ဂဏန်းသက်သက် ရိုက်ပေးပါ -")
        return FOOD_QTY

    if qty <= 0:
        await update.message.reply_text("⚠️ အရေအတွက် 1 နှင့်အထက် ဖြစ်ရမည် -")
        return FOOD_QTY

    name    = context.user_data["last_food"]
    max_qty = context.user_data.get("last_food_max", 999)
    if qty > max_qty:
        await update.message.reply_text(
            f"❌ *{name}* — stock *{max_qty} pcs* သာ ကျန်တော့သည်!\n\n"
            f"{max_qty} နှင့်အောက် ထည့်ပေးပါ -",
            parse_mode="Markdown",
        )
        return FOOD_QTY

    unit_price = context.user_data["food_prices"].get(name, 0)
    context.user_data["food_items"].append({
        "name":       name,
        "qty":        qty,
        "unit_price": unit_price,
        "subtotal":   qty * unit_price,
    })
    return await prompt_food_menu(update, context)

async def step_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text

    if choice == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if choice == BTN_BACK:
        return await prompt_food_menu(update, context)
    if choice == BTN_YES:
        return await prompt_discount(update, context)

    return await prompt_confirm(update, context)

async def step_pay_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment method selection from dynamic buttons."""
    text = update.message.text.strip()
    d = context.user_data
    net = d.get("net_total", 0)

    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_discount(update, context)

    if text == BTN_NO_MORE or text == BTN_PAY_DONE:
        payments = d.get("payments", {})
        d["kpay"] = payments.get("KPay", 0)
        total_paid = sum(payments.values())
        d["cash"] = net - total_paid
        return await _show_payment_review(update, context)

    if text == BTN_ADD_PAY:
        return await prompt_kpay(update, context)

    methods = fetch_payment_methods()
    if text not in methods:
        await update.message.reply_text(
            f'⚠️ "{text}" သည် payment method list ထဲ မရှိပါ — ပြန်ရွေးပါ -',
            reply_markup=ReplyKeyboardMarkup(
                [[m] for m in methods] + [[BTN_PAY_DONE]] + [NAV_ROW],
                resize_keyboard=True,
            ),
        )
        return PAY_METHOD

    d["current_pay_method"] = text
    paid_so_far = sum(d.get("payments", {}).values())
    remaining = net - paid_so_far

    await update.message.reply_text(
        f"💳 *{text}* ပမာဏ ရိုက်ပါ\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Total: *{net:,} Ks*  |  Remaining: *{remaining:,} Ks*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"(0 - {remaining:,}) အကြား ရိုက်ပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
    )
    return PAY_AMOUNT

async def step_pay_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validate and store payment amount for the selected method."""
    text = update.message.text
    d = context.user_data
    net = d.get("net_total", 0)
    method = d.get("current_pay_method", "")

    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_kpay(update, context)

    try:
        amt = int(text.replace(",", "").strip())
    except ValueError:
        await update.message.reply_text(
            "⚠️ ဂဏန်းသက်သက် ရိုက်ပေးပါ -",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return PAY_AMOUNT

    if amt < 0 or amt > net:
        await update.message.reply_text(
            f"⚠️ 0 နှင့် {net:,} ကြား ဂဏန်း ရိုက်ပေးပါ -",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return PAY_AMOUNT

    paid_so_far = sum(d.get("payments", {}).values())
    remaining = net - paid_so_far

    if amt > remaining:
        await update.message.reply_text(
            f"⚠️ ကျသင့်ငွေ ကျန် ({remaining:,} Ks) ထက် မကျော်ရပါ -\n"
            f"0 နှင့် {remaining:,} ကြား ရိုက်ပါ -",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return PAY_AMOUNT

    payments = d.get("payments", {})
    payments[method] = amt
    d["payments"] = payments
    paid_so_far = sum(payments.values())
    remaining = net - paid_so_far

    if remaining <= 0:
        await update.message.reply_text(
            f"✅ *{method}* {amt:,} Ks ထည့်ပြီးပါပြီ\n"
            f"💰 အားလုံးပေးချေပြီးပါပြီ!",
            parse_mode="Markdown",
        )
        d["kpay"] = payments.get("KPay", 0)
        d["cash"] = net - sum(payments.values())
        return await _show_payment_review(update, context)

    await update.message.reply_text(
        f"✅ *{method}* {amt:,} Ks ထည့်ပြီးပါပြီ\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Paid: *{paid_so_far:,} Ks*  |  Remaining: *{remaining:,} Ks*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"နောက်ထပ် payment method ထည့်မလား?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [[BTN_ADD_PAY], [BTN_NO_MORE]],
            resize_keyboard=True,
        ),
    )
    return PAY_METHOD

async def step_kpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Legacy handler — delegates to PAY_METHOD/PAY_AMOUNT flow."""
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_kpay(update, context)

    # Any text input at PAY_METHOD state → step_pay_method handles it
    return await step_pay_method(update, context)

async def _show_payment_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Build and show the final payment review before saving."""
    d = context.user_data
    payments = d.get("payments", {})
    net = d.get("net_total", 0)
    m_id = d.get("m_id", "-")
    c_id = d.get("c_id", "-")
    play_mins = d.get("mins", 0)
    game_amt = d.get("game_amt", 0)
    food_total = d.get("food_total", 0)
    discount = d.get("discount", 0)
    gross = d.get("gross_total", net)
    mult = d.get("multiplier", 1.0)
    is_guest = m_id.strip() == "0 (Guest)"

    food_lines_review = [
        f"  • {i['name']} x{i['qty']} = {i['subtotal']:,} Ks"
        for i in d.get("food_items", [])
    ]
    food_sec_review = "\n".join(food_lines_review) if food_lines_review else "  • မရှိ"

    member_ln = "👤 Guest" if is_guest else f"💳 Member: *{m_id}*"
    game_ln = (
        f"🎮 {play_mins} mins × {mult:g}x = *{game_amt:,} Ks*"
        if is_guest else f"🎮 Play: *{play_mins} mins* (Wallet deducted)"
    )
    disc_ln = f"💸 Discount: *-{discount:,} Ks*\n" if discount > 0 else ""

    pay_lines = []
    for method, amt in payments.items():
        pay_lines.append(f"  • {method}: *{amt:,} Ks*")
    pay_section = "\n".join(pay_lines) if pay_lines else f"  • Cash: *{net:,} Ks*"

    kb = [[BTN_CONFIRM_SAVE], NAV_ROW]
    await update.message.reply_text(
        f"📋 *Review Your Entry — Daily Sales*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{member_ln}\n"
        f"🕹️ Console: *{c_id}*  |  {game_ln}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🍔 Food & Drink:\n{food_sec_review}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🧾 Game: *{game_amt:,} Ks*  |  Food: *{food_total:,} Ks*\n"
        f"{'💰 Gross: *' + f'{gross:,}' + ' Ks*  →  ' if discount > 0 else ''}"
        f"{disc_ln}"
        f"💰 Net Payable: *{net:,} Ks*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💳 Payments:\n{pay_section}\n\n"
        f"မှန်ကန်ပါသလား? ✅ Confirm & Save နှိပ်ပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SALE_CONFIRM


def _build_payment_receipt_lines(kpay: int, cash: int, payments: dict) -> str:
    """Build dynamic payment display lines for receipt."""
    if not payments or len(payments) <= 1:
        return f"💳 Kpay: *{kpay:,} Ks*  |  💵 Cash: *{cash:,} Ks*"

    lines = []
    for method, amt in payments.items():
        lines.append(f"  • {method}: *{amt:,} Ks*")
    return "💳 Payments:\n" + "\n".join(lines)

async def step_sale_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_kpay(update, context)

    if text != BTN_CONFIRM_SAVE:
        return SALE_CONFIRM

    d     = context.user_data

    # ── Double-confirm guard: prevent duplicate save if user taps twice ──────────────────────────────────────────────────
    if d.get("_sale_saved"):
        await update.message.reply_text("⚠️ အခုန်အပြီးပါပြီ သိမ်းဆည်းပါပြီ — မနေးသိမ်းပါ")
        return await show_main_menu(update, context)

    kpay  = d.get("kpay", 0)
    cash  = d.get("cash", 0)
    today = today_str()

    v_no       = d.get("v_no") or next_voucher()
    d["v_no"]   = v_no  # ensure stored back
    d["_sale_saved"] = True  # mark as saved to prevent double-confirm
    m_id       = d.get("m_id", "-")
    c_id       = d.get("c_id", "-")
    play_mins  = d.get("mins", 0)
    game_amt   = d.get("game_amt", 0)
    food_total = d.get("food_total", 0)
    net_total  = d.get("net_total", 0)
    mult       = d.get("multiplier", 1.0)
    is_guest   = m_id.strip() == "0 (Guest)"
    wallet_before = d.get("wallet_mins")   # balance before this session (None for guests)

    discount = d.get("discount", 0)

    # ── Pre-compute (lightweight sync) ────────────────────────────
    s_row      = next_write_row(sales_sh)   # reserve row before background write
    staff_name = d.get("staff", "")
    food_costs = fetch_food_costs()
    food_sold  = list(d.get("food_items", []))

    # Wallet deduct: play_mins × multiplier (Phase B — no sheet read needed)
    wallet_deduct  = round(play_mins * mult)
    # Extract bonus_mins early so balance_after can include it
    _early_bonus_mins = d.get("bonus_mins", 0)
    remaining_mins = (wallet_before - wallet_deduct + _early_bonus_mins) if not is_guest and wallet_before is not None else None

    # Build receipt strings before clearing user_data
    food_lines_receipt = [
        f"  • {i['name']} x{i['qty']} = {i['subtotal']:,} Ks" for i in food_sold
    ]
    food_sec_receipt = "\n".join(food_lines_receipt) if food_lines_receipt else "  • မရှိ"
    member_ln = "👤 Guest" if is_guest else f"💳 Member: *{m_id}*"
    game_ln   = (f"🎮 Game: {play_mins} mins × {mult:g}x = *{game_amt:,} Ks*" if is_guest
                 else f"🎮 Play: *{play_mins} mins*  |  Wallet: *-{wallet_deduct} mins*")
    wallet_bal_line = (f"\n💰 *Remaining Balance: {remaining_mins:,} mins*"
                       if not is_guest and remaining_mins is not None else "")
    receipt_kb  = get_receipt_kb(v_no)
    staff_line  = f"\n👤 Staff: *{staff_name}*" if staff_name else ""

    d_gross     = d.get("gross_total", net_total + discount)  # gross before discount
    promo_id    = d.get("promo_id", "")
    promo_title = d.get("promo_title", "")
    promo_note  = d.get("promo_disc_note", "")
    bonus_mins  = d.get("bonus_mins", 0)
    disc_target = d.get("disc_target", "overall")
    foc_item_name  = d.get("foc_item_name", "")
    foc_item_qty   = d.get("foc_item_qty", 1)
    foc_item_price = d.get("foc_item_price", 0)

    # Save receipt JSON (local disk — instant)
    save_receipt_json(v_no, {
        "type":           "sale",
        "voucher_id":     v_no,
        "date":           today,
        "member_id":      m_id,
        "console_id":     c_id,
        "play_mins":      play_mins,
        "game_amt":       game_amt,
        "food_items":     food_sold,
        "food_total":     food_total,
        "gross_total":    d_gross,
        "discount":       discount,
        "promo_id":       promo_id,
        "promo_title":    promo_title,
        "promo_note":     promo_note,
        "foc_item_name":  foc_item_name,
        "foc_item_qty":   foc_item_qty,
        "bonus_mins":     bonus_mins,
        "bonus_mins_promo": bonus_mins,  # always save; receipt shows if promo-related
        "net_total":      net_total,
        "kpay":           kpay,
        "cash":           cash,
        "multiplier":     mult,
        "is_guest":       is_guest,
        "prev_balance":   wallet_before,
        "balance_change": -wallet_deduct if not is_guest else None,
        "balance_after":  remaining_mins,  # includes bonus_mins if any
        "wallet_game_value": d.get("wallet_game_value", 0),
        "disc_target":     disc_target,
        "foc_item_price":  foc_item_price,
    })
    booking_id = d.get("booking_id", "")
    payments_data = d.get("payments", {})
    context.user_data.clear()

    # ── Build discount/bonus lines for receipt ───────────────────────────────
    # Sanitize strings for Markdown (prevent parse errors from _ * ` chars)
    def _mds(s: str) -> str:
        return str(s).replace("_", " ").replace("*", "").replace("`", "").replace("[", "").replace("]", "")

    if discount > 0:
        disc_label = f" ({_mds(promo_title)})" if promo_title else ""
        if foc_item_name:
            disc_detail = f" — 🎁 FOC: {_mds(foc_item_name)} x{foc_item_qty}"
        elif promo_note:
            disc_detail = f" — {_mds(promo_note)}"
        else:
            disc_detail = ""
        receipt_disc_line = (
            f"🧾 Game: *{game_amt:,} Ks*  |  Food: *{food_total:,} Ks*\n"
            f"💰 Gross Total: *{d_gross:,} Ks*\n"
            f"🎁 Discount{disc_label}: *-{discount:,} Ks*{disc_detail}\n"
            f"✅ *Net Payable: {net_total:,} Ks*\n"
        )
    elif bonus_mins > 0:
        bonus_label = f" ({_mds(promo_title)})" if promo_title else ""
        receipt_disc_line = (
            f"🧾 Game: *{game_amt:,} Ks*  |  Food: *{food_total:,} Ks*\n"
            f"⏱️ Bonus Mins{bonus_label}: *+{bonus_mins} mins*\n"
            f"✅ *Net Payable: {net_total:,} Ks*\n"
        )
    else:
        receipt_disc_line = (
            f"🧾 Game: *{game_amt:,} Ks*  |  Food: *{food_total:,} Ks*\n"
            f"✅ *Net Payable: {net_total:,} Ks*\n"
        )

    # ── RECEIPT — sent BEFORE sheet writes ────────────────────────
    await update.message.reply_text(
        f"✅ *{v_no} သိမ်းဆည်းပြီးပါပြီ!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{member_ln}{staff_line}\n"
        f"🕹️ Console: *{c_id}*  |  {game_ln}\n"
        f"🍔 Food & Drink:\n{food_sec_receipt}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{receipt_disc_line}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{_build_payment_receipt_lines(kpay, cash, payments_data)}"
        f"{wallet_bal_line}",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    if receipt_kb:
        await update.message.reply_text("🖨️ Receipt ပုံနှိပ်ရန် -", reply_markup=receipt_kb)

    # ── SHEET WRITES — background (user already has receipt) ──────
    _disc = discount if discount else ""
    # Capture promo/bonus vars for closure (d already cleared)
    _promo_id    = promo_id
    _promo_title = promo_title
    _bonus_mins  = bonus_mins
    _d_gross     = d_gross
    _m_id        = m_id

    async def _sale_bg():
        def _do():
            # Col N = wallet_deduct_mins (effective_cost_mins for members, blank for guests)
            _w_deduct = 0 if (not _m_id or _m_id.strip() in ("", "0 (Guest)")) else wallet_deduct
            # ── API write (best-effort, non-blocking) ──
            try:
                api_add_sales_record({
                    "date": today,
                    "voucher_no": v_no,
                    "member_id": _m_id,
                    "console_id": c_id,
                    "play_mins": play_mins,
                    "game_amount": game_amt,
                    "food_total": food_total,
                    "discount": _disc,
                    "net_total": net_total,
                    "kpay": kpay,
                    "cash": cash,
                    "wallet_deduct": _w_deduct,
                    "staff": staff_name,
                })
            except Exception as e:
                logging.warning("Sales API write failed (GSheet fallback OK): %s", e)

            sales_sh.batch_update(
                [{"range": f"A{s_row}:K{s_row}",
                  "values": [[today, v_no, _m_id, c_id, play_mins,
                              game_amt, food_total, _disc, net_total, kpay, cash]]},
                 {"range": f"N{s_row}", "values": [[_w_deduct if _w_deduct else ""]]},
                 {"range": f"O{s_row}", "values": [[staff_name]]}],
                value_input_option="USER_ENTERED",
            )
            for item in food_sold:
                cp = food_costs.get(item["name"], 0)
                # ── API write for stock-out (best-effort) ──
                try:
                    api_add_stock_out({
                        "date": today,
                        "voucher_no": v_no,
                        "item_name": item["name"],
                        "qty": item["qty"],
                        "unit_price": item.get("unit_price", 0),
                        "subtotal": item.get("subtotal", 0),
                        "cost_price": cp,
                        "cost_total": cp * item["qty"],
                    })
                except Exception as e:
                    logging.warning("Stock-out API write failed (GSheet fallback OK): %s", e)
                stock_sh.append_row(
                    [today, v_no, item["name"], item["qty"],
                     item.get("unit_price", 0), item.get("subtotal", 0), cp, cp * item["qty"]],
                    value_input_option="USER_ENTERED",
                )
            if food_sold:
                update_inv_total_k1()
                try: _replit_get("sheets/inventory?nocache=1")
                except Exception: pass
            # ── Promotions_Log: record if a promotion was applied ────────────────────────
            if _promo_id and (_disc or _bonus_mins):
                _replit_post("sheets/promotions-log", {
                    "date":         today,
                    "voucher_no":   v_no,
                    "promo_id":     _promo_id,
                    "promo_title":  _promo_title,
                    "member_id":    _m_id,
                    "console_id":   c_id,
                    "gross_total":  _d_gross,
                    "discount_amt": _disc,
                    "bonus_mins":   _bonus_mins,
                    "net_total":    net_total,
                    "staff":        staff_name,
                })
            # ── Bonus minutes: add to member wallet ──────────────────────────────────────
            if _bonus_mins and not is_guest and _m_id not in ("-", "0 (Guest)"):
                try:
                    _wallet_rows = member_sh.get_all_values()
                    for _wi, _wr in enumerate(_wallet_rows):
                        if _wr and len(_wr) > 1 and _wr[1].strip() == _m_id.strip():
                            _cur_bal = int(str(_wr[7]).replace(",", "").strip() or 0)
                            _new_bal = _cur_bal + _bonus_mins
                            member_sh.update_cell(_wi + 1, 8, _new_bal)
                            logging.info("bonus_mins: %s +%d mins → %d", _m_id, _bonus_mins, _new_bal)
                            break
                except Exception as _be:
                    logging.error("bonus_mins_wallet_update: %s", _be)
        try:
            await asyncio.to_thread(_do)
        except Exception as _e:
            logging.error("sale_bg_write: %s", _e)
    asyncio.create_task(_sale_bg())
    # ── Mark linked booking as completed ─────────────────────────────────────
    _linked_bk_id = booking_id
    if _linked_bk_id and not is_guest:
        async def _mark_bk_completed():
            try:
                await asyncio.to_thread(
                    _replit_patch,
                    f"bookings/{_linked_bk_id}/status",
                    {"status": "completed", "staffNote": f"Session completed — {v_no}"},
                )
                logging.info("Booking #%s marked completed via sale %s", _linked_bk_id, v_no)
            except Exception as _e:
                logging.warning("mark_bk_completed error: %s", _e)
        asyncio.create_task(_mark_bk_completed())

    # ── Waitlist notify (non-blocking) ───────────────────────────────────────
    _wl_cid = c_id
    if _wl_cid and _wl_cid not in ("-", ""):
        async def _wl_notify():
            try:
                resp = await asyncio.to_thread(
                    _replit_post, "waitlist/notify", {"console_id": _wl_cid}
                )
                if resp and resp.get("notified"):
                    logging.info("Waitlist notified: %s for console %s",
                                 resp.get("entry", {}).get("customer_name", "?"), _wl_cid)
            except Exception as _e:
                logging.warning("waitlist notify error: %s", _e)
        asyncio.create_task(_wl_notify())

    # ── Session-end customer notification (non-blocking) ─────────────────────
    if not is_guest:
        async def _session_end_notify():
            try:
                chat_id = await asyncio.to_thread(get_customer_chat_id, m_id)
                if chat_id:
                    await asyncio.to_thread(
                        _replit_post,
                        "session-end-notify",
                        {
                            "telegram_chat_id": chat_id,
                            "member_id":        m_id,
                            "console_id":       c_id,
                            "duration_mins":    play_mins,
                            "booking_id":       booking_id,
                        },
                    )
                    logging.info("session_end_notify sent: member=%s", m_id)
            except Exception as _e:
                logging.warning("session_end_notify error: %s", _e)
        asyncio.create_task(_session_end_notify())
    # ── Low balance alert (non-blocking, member only) ────────────────────────
    if not is_guest:
        asyncio.create_task(_check_low_balance_alert(m_id, c_id))

    return await show_main_menu(update, context)

async def cmd_sales_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /sales — new sale entry."""
    context.user_data.clear()
    context.user_data["v_no"] = next_voucher()
    context.user_data["staff"] = ""
    return await prompt_member(update, context)

async def launch_session_sale(
    update, context,
    cid: str, member_id: str, total_mins: int, session_staff: str,
    pre_effective_mins: int = 0,
    booking_id: str = "",
):
    """Pre-fill user_data from session data and route to the Daily Sales food-menu.
    pre_effective_mins: if > 0, use as effective wallet cost directly (for combined
    sessions where each console may have a different multiplier).
    booking_id: if set, link this sale to the customer booking for tracking.
    """
    is_guest = member_id in ("Guest", "0 (Guest)", "")

    base_rate  = fetch_base_rate()
    # For combined cids (e.g. "C-09+C-10") multiplier lookup returns 1.0 — that's fine
    # because pre_effective_mins already encodes the per-console multipliers.
    multiplier = fetch_console_multiplier(cid) if "+" not in cid else 1.0

    # Fetch food prices filtered by stock
    food_prices = fetch_food_prices()
    stock_map: dict = {}
    try:
        inv_data = _replit_get("sheets/inventory")
        if inv_data and isinstance(inv_data, dict):
            stock_map = {i["name"]: max(0, i.get("current_stock", 0))
                         for i in inv_data.get("items", [])}
            food_prices = {k: v for k, v in food_prices.items()
                           if stock_map.get(k, 1) > 0}
    except Exception as e:
        logger.warning("launch_session_sale: stock fetch failed, showing all items: %s", e)
        stock_map = {}

    m_id = "0 (Guest)" if is_guest else member_id

    context.user_data.update({
        "m_id":             m_id,
        "c_id":             cid,
        "mins":             total_mins,
        "actual_play_mins": total_mins,
        "base_rate":        base_rate,
        "multiplier":       multiplier,
        "v_no":             next_voucher(),
        "food_items":       [],
        "food_prices":      food_prices,
        "food_stock_map":   stock_map,
        "staff":            session_staff,
        # from_session flag: True when this sale originated from an active session
        # end/launch flow. Enables the +/-10 min time-adjust step so staff can
        # fine-tune recorded play time before proceeding to the food menu.
        # Safety: only True when valid session context data (cid + play mins) exists.
        "from_session":     bool(total_mins > 0 and cid),
        "booking_id":       booking_id,
    })

    if is_guest:
        game_amt = round((total_mins * base_rate * multiplier) / 60)
        context.user_data["wallet_mins"] = None
        context.user_data["game_amt"]    = game_amt
        # Show time-adjust step when from_session flag is True AND session data
        # (c_id, mins) is present. Guards against stale flags from prior flows.
        if (context.user_data.get("from_session")
                and context.user_data.get("c_id")
                and context.user_data.get("mins", 0) > 0):
            return await prompt_adjust_time(update, context)
        return await prompt_food_menu(update, context)

    # Member — check wallet balance
    try:
        wallet_balance = fetch_wallet_mins(member_id) or 0
    except Exception as e:
        logger.error("launch_session_sale: %s", e, exc_info=True)
        wallet_balance = 0

    context.user_data["wallet_mins"] = wallet_balance

    # Effective cost in wallet-mins:
    #   single console → play_mins × multiplier
    #   combined       → pre-computed sum of (mins_i × mult_i) per session
    effective_cost_mins = pre_effective_mins if pre_effective_mins > 0 \
                          else round(total_mins * multiplier)
    context.user_data["effective_cost_mins"] = effective_cost_mins

    if wallet_balance >= effective_cost_mins:
        # Sufficient — wallet covers it fully
        context.user_data["game_amt"] = 0
        # Show time-adjust step when from_session flag is True AND session data
        # (c_id, mins) is present. Guards against stale flags from prior flows.
        if (context.user_data.get("from_session")
                and context.user_data.get("c_id")
                and context.user_data.get("mins", 0) > 0):
            return await prompt_adjust_time(update, context)
        return await prompt_food_menu(update, context)

    # Insufficient — compute shortfall and show choice screen
    shortfall_wallet_mins = effective_cost_mins - wallet_balance
    shortfall_ks          = round(shortfall_wallet_mins * base_rate / 60)
    context.user_data["shortfall_mins"] = shortfall_wallet_mins
    context.user_data["shortfall_ks"]   = shortfall_ks
    return await prompt_session_shortfall(update, context)

async def prompt_session_shortfall(update, context):
    """Show the insufficient-balance screen with Top Up / Cash Down / Skip options."""
    d              = context.user_data
    m_id           = d.get("m_id", "-")
    wallet_balance = d.get("wallet_mins", 0)
    eff_cost       = d.get("effective_cost_mins", 0)
    shortfall_mins = d.get("shortfall_mins", 0)
    shortfall_ks   = d.get("shortfall_ks", 0)
    actual_mins    = d.get("actual_play_mins", d.get("mins", 0))
    base_rate      = d.get("base_rate", 0)
    multiplier     = d.get("multiplier", 1.0)

    kb = [
        [BTN_TOPUP_SESSION],
        [BTN_CASH_DOWN],
        [BTN_SKIP_SALES],
    ]
    await update.message.reply_text(
        f"⚠️ <b>Wallet မလောက်ပါ!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💳 Member      : <b>{m_id}</b>\n"
        f"🎮 Play Time   : <b>{actual_mins} mins</b>\n"
        f"⚙️ Multiplier  : <b>×{multiplier:g}</b>\n"
        f"🔢 Cost (wallet): <b>{eff_cost} mins</b>\n"
        f"⏳ Balance     : <b>{wallet_balance} mins</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"❗ Shortfall   : <b>{shortfall_mins} mins ≈ {shortfall_ks:,} Ks</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💳 Top Up — mins ဖြည့်ပြီး ဆက်\n"
        f"💵 Cash Down — shortfall ကို cash ပေး\n"
        f"⏭ Skip — Sales မမှတ်တမ်း",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SESSION_SHORTFALL

async def step_session_shortfall(update, context):
    """Handle the Top Up / Cash Down / Skip choice after insufficient balance."""
    from bot.handlers.console import show_console_menu
    text = update.message.text.strip()

    if text == BTN_SKIP_SALES or text == BTN_CANCEL:
        context.user_data.clear()
        return await show_console_menu(update, context)

    if text == BTN_CASH_DOWN:
        d          = context.user_data
        wallet_bal = d.get("wallet_mins", 0)
        multiplier = d.get("multiplier", 1.0)
        base_rate  = d.get("base_rate", fetch_base_rate())
        shortfall_ks = d.get("shortfall_ks", 0)

        # Record only the wallet-covered portion in Sales_Daily col E
        wallet_play_mins = int(wallet_bal / multiplier) if multiplier > 0 else wallet_bal
        d["mins"]          = wallet_play_mins   # col E — wallet fully depleted
        d["game_amt"]      = shortfall_ks       # cash for extra time
        d["cash_down_ks"]  = shortfall_ks
        d["remaining_mins"] = 0
        return await prompt_food_menu(update, context)

    if text == BTN_TOPUP_SESSION:
        d = context.user_data
        # Snapshot session data so it survives user_data operations during TU flow
        snap_keys = [
            "m_id", "c_id", "mins", "actual_play_mins", "base_rate", "multiplier",
            "v_no", "food_items", "food_prices", "food_stock_map", "staff",
            "from_session", "wallet_mins", "effective_cost_mins",
            "shortfall_mins", "shortfall_ks",
        ]
        d["_session_snap"] = {k: d[k] for k in snap_keys if k in d}
        d["after_topup"]   = "console_sale"
        # Pre-fill tu_id so Top Up member step is skipped
        tu_id = d["m_id"]
        d["tu_id"] = tu_id
        # Load member data for Top Up flow
        try:
            tu_data = fetch_member_data(tu_id)
            master_thresh, immortal_thresh = fetch_rank_thresholds()
            bonus_table = fetch_bonus_table()
            d["tu_rank"]            = tu_data["rank_raw"]
            d["tu_total_spend"]     = tu_data["net_spend"]
            d["tu_phone"]           = tu_data["phone"]
            d["tu_name"]            = tu_data["name"]
            d["tu_wallet_mins"]     = tu_data["wallet_mins"]
            d["tu_master_thresh"]   = master_thresh
            d["tu_immortal_thresh"] = immortal_thresh
            d["tu_bonus_table"]     = bonus_table
        except Exception as e:
            await update.message.reply_text(f"❌ Member data ဖတ်မရပါ: {e}")
            return await prompt_session_shortfall(update, context)
        return await prompt_tu_amt(update, context)

    # Unrecognised input — re-show screen
    return await prompt_session_shortfall(update, context)
