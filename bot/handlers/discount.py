"""PS VIBE Bot — Handler module.
"""
from bot import (
    prompt_kpay,
    BTN_BACK, BTN_CANCEL, BTN_MANUAL_DISC, BTN_PROMO_APPLY,
    BTN_SKIP_DISC, BUNDLE_FOC, DISCOUNT, NAV_ROW, PROMO_SELECT,
    cmd_cancel, fetch_base_rate, fetch_promotions_cached,
)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import asyncio, logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta




async def prompt_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show discount options: apply a promotion or manual discount."""
    d     = context.user_data
    # Compute gross for display purposes:
    # For member wallet sessions: game_amt=0 (wallet deducted), so use
    # effective_cost_mins * base_rate / 60 as the game value equivalent.
    game_amt   = d.get("game_amt", 0)
    food_total = d.get("food_total", 0)
    net_total  = d.get("net_total", 0)

    # For member wallet sessions: game_amt=0, compute wallet game equivalent value
    # base_rate is always set at step_mins (line 1726), so d.get is safe
    base_rate = d.get("base_rate") or fetch_base_rate()
    mult      = d.get("multiplier", 1.0)
    eff_mins  = d.get("effective_cost_mins") or d.get("mins", 0)

    if game_amt == 0:
        # Wallet session (with or without food) — compute wallet game value
        wallet_val = round(eff_mins * base_rate * mult / 60)
        gross = wallet_val + food_total
        d["wallet_game_value"] = wallet_val
    else:
        gross = net_total if net_total > 0 else (game_amt + food_total)
        d["wallet_game_value"] = 0

    d["gross_total"] = gross
    # For wallet sessions net_total stays as food_total (what customer actually pays cash)
    if "net_total" not in d or d["net_total"] == 0:
        d["net_total"] = food_total
    d.setdefault("discount", 0)

    # Fetch active promotions from API (cached — 2 min TTL for fast response)
    # Run in thread to avoid blocking the async event loop
    promos = await asyncio.to_thread(fetch_promotions_cached)

    # For display: wallet sessions show wallet value as reference, not payable amount
    is_wallet_session = d.get("wallet_game_value", 0) > 0
    wallet_val = d.get("wallet_game_value", 0)
    food_total_disp = d.get("food_total", 0)

    if is_wallet_session:
        gross_label = (
            f"🎮 Wallet Game Value: *{wallet_val:,} Ks* (mins deduct)\n"
            f"🍔 Food Total: *{food_total_disp:,} Ks*\n"
            f"💰 Cash Payable: *{food_total_disp:,} Ks*"
        )
    else:
        gross_label = f"💰 Gross Total: *{gross:,} Ks*"

    if promos:
        # Build keyboard with promotion buttons + manual + skip
        kb = [[BTN_PROMO_APPLY], [BTN_MANUAL_DISC], [BTN_SKIP_DISC], NAV_ROW]
        promo_lines = []
        for i, p in enumerate(promos, 1):
            emoji = p.get("emoji", "🎁")
            # Escape Markdown special chars in title to prevent parse errors
            title = p.get("title", "").replace("_", " ").replace("*", "").replace("`", "").replace("[", "").replace("]", "")
            ptype = p.get("type", "general")
            disc_pct = p.get("discount_percent", "")
            tag = f" ({disc_pct}% OFF)" if disc_pct and ptype == "discount" else ""
            promo_lines.append(f"  {emoji} {title}{tag}")
        promo_list = "\n".join(promo_lines)
        await update.message.reply_text(
            f"💸 *Discount / Promotion*\n\n"
            f"{gross_label}\n\n"
            f"🎁 *Active Promotions:*\n{promo_list}\n\n"
            f"📋 Promotion ရွေးချင်ရင် *Promotion ရွေးပါ* နှိပ်ပါ\n"
            f"Manual ရိုက်ချင်ရင် *Manual Discount* နှိပ်ပါ -",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
    else:
        # No active promotions — show manual discount only
        kb = [[BTN_SKIP_DISC], NAV_ROW]
        await update.message.reply_text(
            f"💸 *Discount ထည်မလား?*\n\n"
            f"{gross_label}\n\n"
            f"Discount ပမာဏ ရိုက်ပါ (ဥပမာ 500)\n"
            f"သို့မဟုတ် *Skip* နှိပ်ပါ -",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
    return DISCOUNT

async def prompt_promo_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show promotion selection list for staff to pick one."""
    d = context.user_data
    gross = d.get("gross_total", d.get("net_total", 0))

    promos = await asyncio.to_thread(fetch_promotions_cached)

    if not promos:
        await update.message.reply_text("❌ Active promotions မရှိပါ")
        return await prompt_discount(update, context)

    # Store promos list for selection
    d["_promos_list"] = promos

    # Build keyboard: one button per promotion
    kb = []
    for i, p in enumerate(promos, 1):
        emoji = p.get("emoji", "🎁")
        title = p.get("title", "")
        disc_pct = p.get("discount_percent", "")
        ptype = p.get("type", "general")
        tag = f" ({disc_pct}% OFF)" if disc_pct and ptype == "discount" else ""
        kb.append([f"{emoji} {i}. {title}{tag}"])
    kb.append([BTN_BACK, BTN_CANCEL])

    await update.message.reply_text(
        f"🎁 *Promotion ရွေးပါ*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Gross: *{gross:,} Ks*\n\n"
        f"Promotion ရွေးပါ ↓",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return PROMO_SELECT

async def step_promo_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle promotion selection — calculate discount and record promo_id."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_discount(update, context)

    d = context.user_data
    promos = d.get("_promos_list", [])
    gross = d.get("gross_total", d.get("net_total", 0))

    # Match selected promotion by button text
    selected = None
    for i, p in enumerate(promos, 1):
        emoji = p.get("emoji", "🎁")
        title = p.get("title", "")
        disc_pct = p.get("discount_percent", "")
        ptype = p.get("type", "general")
        tag = f" ({disc_pct}% OFF)" if disc_pct and ptype == "discount" else ""
        btn_text = f"{emoji} {i}. {title}{tag}"
        if text == btn_text:
            selected = p
            break

    if not selected:
        await update.message.reply_text("⚠️ Promotion မရှိပါ — ပြန်သော ရွေးပါ -")
        return PROMO_SELECT

    # Calculate discount based on type
    ptype = selected.get("type", "general")
    disc_pct = selected.get("discount_percent", 0)
    promo_id = selected.get("id", "")
    promo_title = selected.get("title", "")

    if ptype == "bonus_mins":
        # Bonus minutes promotion — ask how many bonus mins to add
        d["_selected_promo"]   = selected
        d["_bonus_mins_entry"] = True
        bonus_val = selected.get("discount_percent", "")
        hint = f" (ဥပမာ {bonus_val} mins)" if bonus_val else ""
        bundle_items = selected.get("bundle_items", "") or selected.get("description", "")
        desc_line = f"\n📝 {bundle_items}" if bundle_items else ""
        await update.message.reply_text(
            f"⏱️ *{promo_title}*{desc_line}\n"
            f"Bonus Minutes ထည့်ပါ{hint} -",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([[BTN_SKIP_DISC], [BTN_CANCEL]], resize_keyboard=True),
        )
        return DISCOUNT

    elif ptype in ("discount", "cashback") and disc_pct:
        disc_target = selected.get("discount_target", "overall")
        game_amt_val  = d.get("game_amt", 0)
        food_total_val = d.get("food_total", 0)
        is_member = d.get("m_id", "-").strip() not in ("-", "0 (Guest)")

        # Wallet session = member card holder; game cost deducted from wallet mins (no cash)
        is_wallet_session = is_member and game_amt_val == 0
        eff_mins = d.get("effective_cost_mins") or d.get("mins", 0)

        # Member wallet session: game/overall discount -> bonus mins
        # Member card holders don't pay cash for game time.
        # Any game-related discount must be returned as bonus minutes, not cash.
        if is_wallet_session and disc_target in ("game_only", "overall"):
            bonus_mins_calc = round(eff_mins * float(disc_pct) / 100)
            if bonus_mins_calc <= 0:
                bonus_mins_calc = round(60 * float(disc_pct) / 100)  # fallback: 1hr
            d["promo_id"]    = promo_id
            d["promo_title"] = promo_title
            d["discount"]    = 0
            d["bonus_mins"]  = bonus_mins_calc
            net_pay = d.get("net_total", food_total_val)
            await update.message.reply_text(
                f"✅ *{promo_title}* ထည့်သွင်းပြီးပါပြီ\n"
                f"⏱️ Member session — Game discount ကို Bonus Mins ပြောင်းပါပြီ\n"
                f"🎁 Bonus: *+{bonus_mins_calc} mins* ({disc_pct}% of {eff_mins} mins)\n"
                f"💰 Net Payable: *{net_pay:,} Ks* (ဆော့ဖိုး မပါပြီ)",
                parse_mode="Markdown",
            )
            return await prompt_kpay(update, context)

        # Normal cash discount (guest session, or food_only for member)
        if disc_target == "game_only":
            disc = round(game_amt_val * float(disc_pct) / 100)
        elif disc_target == "food_only":
            disc = round(food_total_val * float(disc_pct) / 100)
        else:  # overall - cash session only reaches here
            disc = round(gross * float(disc_pct) / 100)

        if disc <= 0 or disc >= gross:
            await update.message.reply_text(
                f"⚠️ Discount (*{disc:,} Ks*) မမှန်ကန်ပါ — Manual ရိုက်ပါ -",
                parse_mode="Markdown",
            )
            return DISCOUNT

        d["discount"]    = disc
        d["promo_id"]    = promo_id
        d["promo_title"] = promo_title
        d["disc_target"] = disc_target
        # For wallet sessions: net_total = food_total - disc (cash only)
        # For cash/guest: net_total = gross - disc
        _food_tv = d.get("food_total", 0)
        _is_wv = d.get("game_amt", 0) == 0 and d.get("m_id", "0 (Guest)").strip() not in ("0 (Guest)", "-", "")
        if _is_wv:
            d["net_total"] = max(0, _food_tv - disc)
        else:
            d["net_total"] = gross - disc

        await update.message.reply_text(
            f"✅ *{promo_title}* ထည့်သွင်းပြီးပါပြီ\n"
            f"💸 Discount: *{disc:,} Ks* ({disc_pct}% OFF)\n"
            f"💰 Net Payable: *{d['net_total']:,} Ks*",
            parse_mode="Markdown",
        )
        return await prompt_kpay(update, context)
    else:
        # bundle / free_item / general — ask which item is FOC (if food items exist)
        bundle_items = selected.get("bundle_items", "") or selected.get("description", "")
        d["promo_id"]        = promo_id
        d["promo_title"]     = promo_title
        d["discount"]        = 0
        d["promo_disc_note"] = bundle_items
        d["_selected_promo"] = selected

        food_items = d.get("food_items", [])
        if food_items:
            # Build keyboard from food items in cart
            kb = []
            for fi in food_items:
                kb.append([f"🍺 {fi['name']} x{fi['qty']} ({fi['subtotal']:,} Ks)"])
            kb.append(["❌ FOC မသတ်ပါ (Skip)"])
            kb.append([BTN_CANCEL])
            desc_line = f"\n📝 {bundle_items}" if bundle_items else ""
            await update.message.reply_text(
                f"🎁 *{promo_title}*{desc_line}\n\n"
                f"❓ ဘယ် drink/item က FOC ပေးပါလဲ? \n"
                f"(Cart ထဲး item ရွေးပါပြီ ရွေးပါ) ↓",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            )
            return BUNDLE_FOC
        else:
            # No food items — just note the promotion, no discount
            desc_line = f"\n📝 {bundle_items}" if bundle_items else ""
            await update.message.reply_text(
                f"✅ *{promo_title}* မှတ်တမ်းတင်ပြီးပါပြီ{desc_line}\n"
                f"💰 Net Payable: *{gross:,} Ks*\n\n"
                f"ဆက်သွားမလား?",
                parse_mode="Markdown",
            )
            return await prompt_kpay(update, context)

async def step_bundle_foc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle FOC item selection for bundle/free_item promotions."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)

    d = context.user_data
    gross = d.get("gross_total", d.get("net_total", 0))
    food_items = d.get("food_items", [])
    promo_title = d.get("promo_title", "")

    # Skip FOC
    if text == "❌ FOC မသတ်ပါ (Skip)":
        d["discount"] = 0
        await update.message.reply_text(
            f"✅ *{promo_title}* မှတ်တမ်းတင်ပြီးပါပြီ (FOC မသတ်ပါ)\n"
            f"💰 Net Payable: *{gross:,} Ks*",
            parse_mode="Markdown",
        )
        return await prompt_kpay(update, context)

    # Match selected FOC item from button text: "🍺 {name} x{qty} ({subtotal:,} Ks)"
    foc_item = None
    for fi in food_items:
        btn = f"🍺 {fi['name']} x{fi['qty']} ({fi['subtotal']:,} Ks)"
        if text == btn:
            foc_item = fi
            break

    if not foc_item:
        await update.message.reply_text("⚠️ Item မရှိပါ — ပြန်ရွေးရွေး ရွေးပါ -")
        return BUNDLE_FOC

    # Set FOC discount = subtotal of the selected item
    foc_price = foc_item["subtotal"]
    foc_name  = foc_item["name"]
    foc_qty   = foc_item["qty"]

    # Safety: don't let discount exceed gross
    disc = min(foc_price, gross)

    d["discount"]        = disc
    d["net_total"]       = gross - disc
    d["foc_item_name"]   = foc_name
    d["foc_item_qty"]    = foc_qty
    d["foc_item_price"]  = foc_price
    d["promo_disc_note"] = f"FOC: {foc_name} x{foc_qty}"

    await update.message.reply_text(
        f"✅ *{promo_title}*\n"
        f"🎁 FOC Item: *{foc_name} x{foc_qty}* (-{foc_price:,} Ks)\n"
        f"💰 Net Payable: *{d['net_total']:,} Ks*",
        parse_mode="Markdown",
    )
    return await prompt_kpay(update, context)

async def step_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        return await prompt_confirm(update, context)
    if text == BTN_SKIP_DISC:
        context.user_data["discount"] = 0
        context.user_data.pop("promo_id", None)
        context.user_data.pop("promo_title", None)
        return await prompt_kpay(update, context)
    if text == BTN_PROMO_APPLY:
        return await prompt_promo_select(update, context)
    if text == BTN_MANUAL_DISC:
        # Show manual entry prompt
        d = context.user_data
        gross = d.get("gross_total", d.get("net_total", 0))
        _food_disp = d.get("food_total", 0)
        _is_w = d.get("game_amt", 0) == 0 and d.get("m_id", "0 (Guest)").strip() not in ("0 (Guest)", "-", "")
        if _is_w:
            gross_line = (
                f"🎮 Wallet Game Value: *{d.get('wallet_game_value', 0):,} Ks* (mins)\n"
                f"🍔 Food: *{_food_disp:,} Ks*\n"
                f"💰 Cash Payable: *{_food_disp:,} Ks* (ဆော့ဖိုး မပါ)"
            )
        else:
            gross_line = f"💰 Gross: *{gross:,} Ks*"
        await update.message.reply_text(
            f"✏️ *Manual Discount*\n"
            f"{gross_line}\n\n"
            f"Discount ပမာဏ ရိုက်ပါ (Ks) -",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([[BTN_SKIP_DISC], NAV_ROW], resize_keyboard=True),
        )
        return DISCOUNT

    try:
        val = int(text.replace(",", "").strip())
    except ValueError:
        await update.message.reply_text("⚠️ ဂဏန်သက်သက် ရိုက်ပေးပါ -")
        return DISCOUNT

    d     = context.user_data
    gross = d.get("gross_total", d.get("net_total", 0))

    # ── Bonus minutes entry path ──────────────────────────────────────────────
    if d.pop("_bonus_mins_entry", False):
        bonus_mins     = val
        selected_promo = d.pop("_selected_promo", None)
        if selected_promo:
            d["promo_id"]    = selected_promo.get("id", "")
            d["promo_title"] = selected_promo.get("title", "")
        d["bonus_mins"] = bonus_mins
        d["discount"]   = 0
        await update.message.reply_text(
            f"✅ Bonus *+{bonus_mins} mins* ထည့်သွင်းပြီးပါပြီ\n"
            f"💰 Net Payable: *{gross:,} Ks* (Discount မရှိပါ)",
            parse_mode="Markdown",
        )
        return await prompt_kpay(update, context)

    # ── Normal discount entry ─────────────────────────────────────────────────
    disc = val
    # For wallet sessions, cash payable = food_total only (game is wallet-deducted)
    _food_total_v = d.get("food_total", 0)
    _is_wallet_s  = d.get("game_amt", 0) == 0 and d.get("m_id", "0 (Guest)").strip() not in ("0 (Guest)", "-", "")
    _cash_payable = _food_total_v if _is_wallet_s else gross
    _limit_check  = _cash_payable if _cash_payable > 0 else gross
    if disc < 0 or disc >= _limit_check:
        await update.message.reply_text(
            f"⚠️ Discount (*{disc:,} Ks*) သည် Cash Payable (*{_limit_check:,} Ks*) ထက် မကျော်ရပါ -",
            parse_mode="Markdown",
        )
        return DISCOUNT

    # If a promo was selected earlier (free_item/bundle), keep promo_id
    selected_promo = d.pop("_selected_promo", None)
    if selected_promo and not d.get("promo_id"):
        d["promo_id"]    = selected_promo.get("id", "")
        d["promo_title"] = selected_promo.get("title", "")
    d["discount"]  = disc
    # Wallet session: net_total = food_total - disc (cash only, game is wallet)
    # Cash/guest session: net_total = gross - disc
    if _is_wallet_s:
        d["net_total"] = max(0, _food_total_v - disc)
    else:
        d["net_total"] = gross - disc
    await update.message.reply_text(
        f"✅ Discount *{disc:,} Ks* ထည့်ပြီး\n"
        f"💰 Net Payable: *{d['net_total']:,} Ks*",
        parse_mode="Markdown",
    )
    return await prompt_kpay(update, context)

