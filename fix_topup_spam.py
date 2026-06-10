#!/usr/bin/env python3

import sys
import subprocess
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read the original file
with open('/root/psvibe-sales-bot/bot/handlers/members.py', 'r') as f:
    content = f.read()

# Find the step_tu_kpay function and replace it
old_step_tu_kpay = '''@log_duration("members:step_tu_kpay")
async def step_tu_kpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dynamic payment method + amount for Top Up."""
    text = update.message.text
    d = context.user_data
    amt = d.get("tu_amt", 0)

    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        context.user_data.pop("tu_amt", None)
        return await prompt_tu_amt(update, context)

    # Check if text is a payment method
    methods = fetch_payment_methods()
    if text in methods:
        d["tu_current_pay_method"] = text
        psf = sum(d.get("tu_payments", {}).values())
        rem = amt - psf
        await update.message.reply_text(
            f"\\U0001f4b3 *{text}* \\u1015\\u1019\\u102b\\u100f \\u101b\\u102d\\u102f\\u1000\\u103a\\u1015\\u102b\\n"
            f"\\u2501" * 30 + f"\\n"
            f"\\U0001f4b0 Top Up: *{amt:,} Ks*  |  Remaining: *{rem:,} Ks*\\n"
            f"\\u2501" * 30 + f"\\n"
            f"(0 - {rem:,}) \\u1011\\u100a\\u1039\\u1037\\u1015\\u102b\\u1038 -",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return TU_KPAY

    # Try to parse as amount for current method
    try:
        method_amt = int(text.replace(",", "").strip())
    except ValueError:
        # Not a number - continue to check BTN_PAY_DONE
        pass
    else:
        current_method = d.get("tu_current_pay_method", "")
        if not current_method:
            return await prompt_tu_kpay(update, context)
        psf = sum(d.get("tu_payments", {}).values())
        rem = amt - psf
        if method_amt < 0 or method_amt > rem:
            await update.message.reply_text(
                f"\\u26a0\\ufe0f 0 \\u1014\\u101c\\u1039 {rem:,} \\u1000\\u1032 \\u1014\\u1031\\u1000\\u103a \\u1002\\u1014\\u103a\\u1000\\u103e  \\u101b\\u102d\\u102f\\u1000\\u103a\\u1015\\u102b -",
                parse_mode="Markdown",
            )
            return TU_KPAY
        if "tu_payments" not in d:
            d["tu_payments"] = {}
        d["tu_payments"][current_method] = method_amt
        return await prompt_tu_kpay(update, context)

    # Check if text is BTN_PAY_DONE
    if text == BTN_PAY_DONE:
        payments = d.get("tu_payments", {})
        psf = sum(payments.values())
        if psf <= 0:
            await update.message.reply_text("\\u26a0\\ufe0f \\u1021\\u1014\\u102c\\u100a\\u1036\\u1006\\u1031\\u1038 payment method \\u1010\\u1005\\u1039 \\u1011\\u102d\\u1004\\u1039\\u1015\\u102b\\u1038 -")
            return await prompt_tu_kpay(update, context)
        d["tu_kpay"] = payments.get("KPay", 0)
        d["tu_cash"] = payments.get("Cash", 0)

    # Show review (common for both BTN_PAY_DONE and amount parse)
    r          = display_rank(d.get("tu_rank", "Warrior"))
    r_em       = rank_emoji(r)
    base_mins  = d.get("tu_base_mins", 0)
    bonus_mins = d.get("tu_bonus_mins", 0)
    total_mins = d.get("tu_mins", 0)
    kpay       = d.get("tu_kpay", 0)
    cash       = d.get("tu_cash", 0)
    tu_amt     = d.get("tu_amt", 0)

    # Build dynamic payment display
    payments = d.get("tu_payments", {})
    pay_lines = []
    for method, a in payments.items():
        pay_lines.append(f"  \\u2022 {method}: *{a:,} Ks*")
    pay_display = "\\n".join(pay_lines)

    net_spend       = d.get("tu_total_spend", 0)
    master_thresh   = d.get("tu_master_thresh", 0)
    immortal_thresh = d.get("tu_immortal_thresh", 0)
    if r == "Warrior" and int(master_thresh) > 0:
        remaining = master_thresh - (net_spend + tu_amt)
        next_tier_ln = (
            f"\\n\\U0001f4ca After Top-Up Spend: *{net_spend + tu_amt:,} Ks*\\n"
            f"\\U0001f3c5 Remaining to Master: *{max(remaining,0):,} Ks*"
            + ("\\n🎉 *New Tier Unlocked!* 🏅" if remaining <= 0 else "")
        )
    elif r == "Master" and int(immortal_thresh) > 0:
        remaining = immortal_thresh - (net_spend + tu_amt)
        next_tier_ln = (
            f"\\n\\U0001f4ca After Top-Up Spend: *{net_spend + tu_amt:,} Ks*\\n"
            f"\\U0001f48e Remaining to Immortal: *{max(remaining,0):,} Ks*"
            + ("\\n🎉 *New Tier Unlocked!* 💎" if remaining <= 0 else "")
        )
    else:
        next_tier_ln = "\\n\\U0001f3c6 _Top Rank \\u2014 Immortal!_"

    kb = [[BTN_CONFIRM_SAVE], NAV_ROW]
    await update.message.reply_text(
        f"\\U0001f4cb *Review Your Entry \\u2014 Top Up*\\n"
        f"\\u2501" * 30 + f"\\n"
        f"\\U0001faaa *{d["tu_id"]}* \\u2014 {d.get("tu_name","")}\n"
        f"\\U0001f396 Rank: *{r_em} {r}*\\n"
        f"\\u2501" * 30 + f"\\n"
        f"\\U0001f4b0 Top Up Amount: *{tu_amt:,} Ks*\\n"
        f"\\u23f1 Base Mins: *{base_mins:,} mins*\\n"
        f"\\U0001f389 Rank Bonus: *+{bonus_mins} mins*\\n"
        f"\\U0001f525 Total to be Added: *{total_mins:,} mins*\\n"
        f"\\u2501" * 30 + f"\\n"
        f"{pay_display}"
        f"{next_tier_ln}\\n\\n"
        f"\\u1019\\u1039\\u1000\\u1014\\u1039\\u1000\\u102d\\u102f\\u1015\\u102b\\u101e\\u101c\\u102c\\u1038? \\u2705 Confirm & Save \\u1014\\u103a\\u102d\\u1000\\u1039\\u1015\\u102b\\u1038 -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return TU_CONFIRM'''

new_step_tu_kpay = '''@log_duration("members:step_tu_kpay")
async def step_tu_kpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dynamic payment method + amount for Top Up."""
    text = update.message.text
    d = context.user_data
    amt = d.get("tu_amt", 0)

    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        context.user_data.pop("tu_amt", None)
        return await prompt_tu_amt(update, context)

    # Check if text is a payment method
    methods = fetch_payment_methods()
    if text in methods:
        # Store current method but DON'T send separate message
        # Instead, call prompt_tu_kpay with method selection state
        d["tu_current_pay_method"] = text
        d["tu_show_amount_input"] = True
        return await prompt_tu_kpay(update, context)

    # Try to parse as amount for current method
    try:
        method_amt = int(text.replace(",", "").strip())
    except ValueError:
        # Not a number - continue to check BTN_PAY_DONE
        pass
    else:
        current_method = d.get("tu_current_pay_method", "")
        if not current_method:
            return await prompt_tu_kpay(update, context)
        psf = sum(d.get("tu_payments", {}).values())
        rem = amt - psf
        if method_amt < 0 or method_amt > rem:
            await update.message.reply_text(
                f"\\u26a0\\ufe0f 0 \\u1014\\u101c\\u1039 {rem:,} \\u1000\\u1032 \\u1014\\u1031\\u1000\\u103a \\u1002\\u1014\\u103a\\u1000\\u103e  \\u101b\\u102d\\u102f\\u1000\\u103a\\u1015\\u102b -",
                parse_mode="Markdown",
            )
            return TU_KPAY
        if "tu_payments" not in d:
            d["tu_payments"] = {}
        d["tu_payments"][current_method] = method_amt
        # Clear the method selection state
        d.pop("tu_current_pay_method", None)
        d.pop("tu_show_amount_input", None)
        return await prompt_tu_kpay(update, context)

    # Check if text is BTN_PAY_DONE
    if text == BTN_PAY_DONE:
        payments = d.get("tu_payments", {})
        psf = sum(payments.values())
        if psf <= 0:
            await update.message.reply_text("\\u26a0\\ufe0f \\u1021\\u1014\\u102c\\u100a\\u1036\\u1006\\u1031\\u1038 payment method \\u1010\\u1005\\u1039 \\u1011\\u102d\\u1004\\u1039\\u1015\\u102b\\u1038 -")
            return await prompt_tu_kpay(update, context)
        d["tu_kpay"] = payments.get("KPay", 0)
        d["tu_cash"] = payments.get("Cash", 0)
        return await step_tu_confirm(update, context)

    # Invalid input - show current state
    return await prompt_tu_kpay(update, context)'''

logger.info("Replacing step_tu_kpay function...")

if old_step_tu_kpay not in content:
    logger.info("ERROR: Could not find exact step_tu_kpay function to replace")
    sys.exit(1)

content = content.replace(old_step_tu_kpay, new_step_tu_kpay)

# Now also update prompt_tu_kpay to handle amount input state
old_prompt_start = 'async def prompt_tu_kpay(update: Update, context: ContextTypes.DEFAULT_TYPE):'
new_prompt_start = 'async def prompt_tu_kpay(update: Update, context: ContextTypes.DEFAULT_TYPE):'

# Find and update the prompt function to handle the amount input state
old_prompt_tu_kpay = '''async def prompt_tu_kpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show dynamic payment method buttons for Top Up."""
    d   = context.user_data
    amt = d.get("tu_amt", 0)

    if "tu_payments" not in d:
        d["tu_payments"] = {}

    if amt <= 0:
        d["tu_kpay"] = 0
        d["tu_cash"] = 0
        return await step_tu_confirm(update, context)

    methods = fetch_payment_methods()
    paid_so_far = sum(d["tu_payments"].values())
    remaining = amt - paid_so_far

    # Auto-confirm when full payment complete
    if remaining <= 0:
        d["tu_kpay"] = d["tu_payments"].get("KPay", 0)
        d["tu_cash"] = d["tu_payments"].get("Cash", 0)
        return await step_tu_confirm(update, context)

    kb = [[m] for m in methods]
    kb.append([BTN_PAY_DONE])
    kb.append(NAV_ROW)

    payment_status = ""
    if d["tu_payments"]:
        ll = []
        for method, ap in d["tu_payments"].items():
            ll.append(f"  \\u2022 {method}: *{ap:,} Ks*")
        payment_status = "\\n".join(ll)
        payment_status += f"\\n  \\u2500 Paid: *{paid_so_far:,} Ks*  |  Remaining: *{remaining:,} Ks*\\n\\n"

    r   = display_rank(d.get("tu_rank", "Warrior"))
    r_em = rank_emoji(r)
    await update.message.reply_text(
        step_hdr(3, 3, "Payment \\u2014 Method") +
        f"\\U0001faaa *{d.get('tu_id','')}* \\u2014 {d.get('tu_name','')}\n"
        f"\\U0001f396 Rank: *{r_em} {r}*  |  \\U0001f4b0 Top Up: *{amt:,} Ks*\\n"
        f"\\u23f1 {d.get('tu_base_mins',0):,} base + {d.get('tu_bonus_mins',0)} bonus mins\\n\\n"
        f"{payment_status}"
        "\\U0001f4b3 Payment Method \\u1012\\u1039\\u101b\\u1032\\u1015\\u102b\\u1038 -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return TU_KPAY'''

new_prompt_tu_kpay = '''async def prompt_tu_kpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show dynamic payment method buttons for Top Up."""
    d   = context.user_data
    amt = d.get("tu_amt", 0)

    if "tu_payments" not in d:
        d["tu_payments"] = {}

    if amt <= 0:
        d["tu_kpay"] = 0
        d["tu_cash"] = 0
        return await step_tu_confirm(update, context)

    methods = fetch_payment_methods()
    paid_so_far = sum(d["tu_payments"].values())
    remaining = amt - paid_so_far

    # Auto-confirm when full payment complete
    if remaining <= 0:
        d["tu_kpay"] = d["tu_payments"].get("KPay", 0)
        d["tu_cash"] = d["tu_payments"].get("Cash", 0)
        return await step_tu_confirm(update, context)

    # Check if we need to show amount input for selected method
    if d.get("tu_show_amount_input") and d.get("tu_current_pay_method"):
        method = d["tu_current_pay_method"]
        await update.message.reply_text(
            f"\\U0001f4b3 *{method}* \\u1015\\u1019\\u102b\\u100f \\u101b\\u102d\\u102f\\u1000\\u103a\\u1015\\u102b\\n"
            f"\\u2501" * 30 + f"\\n"
            f"\\U0001f4b0 Top Up: *{amt:,} Ks*  |  Remaining: *{remaining:,} Ks*\\n"
            f"\\u2501" * 30 + f"\\n"
            f"(0 - {remaining:,}) \\u1011\\u100a\\u1039\\u1037\\u1015\\u102b\\u1038 -",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([NAV_ROW], resize_keyboard=True),
        )
        return TU_KPAY

    kb = [[m] for m in methods]
    kb.append([BTN_PAY_DONE])
    kb.append(NAV_ROW)

    payment_status = ""
    if d["tu_payments"]:
        ll = []
        for method, ap in d["tu_payments"].items():
            ll.append(f"  \\u2022 {method}: *{ap:,} Ks*")
        payment_status = "\\n".join(ll)
        payment_status += f"\\n  \\u2500 Paid: *{paid_so_far:,} Ks*  |  Remaining: *{remaining:,} Ks*\\n\\n"

    r   = display_rank(d.get("tu_rank", "Warrior"))
    r_em = rank_emoji(r)
    await update.message.reply_text(
        step_hdr(3, 3, "Payment \\u2014 Method") +
        f"\\U0001faaa *{d.get('tu_id','')}* \\u2014 {d.get('tu_name','')}\n"
        f"\\U0001f396 Rank: *{r_em} {r}*  |  \\U0001f4b0 Top Up: *{amt:,} Ks*\\n"
        f"\\u23f1 {d.get('tu_base_mins',0):,} base + {d.get('tu_bonus_mins',0)} bonus mins\\n\\n"
        f"{payment_status}"
        "\\U0001f4b3 Payment Method \\u1012\\u1039\\u101b\\u1032\\u1015\\u102b\\u1038 -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return TU_KPAY'''

logger.info("Replacing prompt_tu_kpay function...")

if old_prompt_tu_kpay not in content:
    logger.info("ERROR: Could not find exact prompt_tu_kpay function to replace")
    sys.exit(1)

content = content.replace(old_prompt_tu_kpay, new_prompt_tu_kpay)

# Write the updated content
with open('/root/psvibe-sales-bot/bot/handlers/members.py', 'w') as f:
    f.write(content)

logger.info("✅ Successfully updated Top Up payment flow")
logger.info("📋 Changes made:")
logger.info("   1. Removed duplicate message sending in step_tu_kpay")
logger.info("   2. Added amount input state handling to prevent spam")
logger.info("   3. Consolidated all message display through prompt_tu_kpay")

# Test compilation
try:
    result = subprocess.run(['python3', '-m', 'py_compile', '/root/psvibe-sales-bot/bot/handlers/members.py'],
                          capture_output=True, text=True, cwd='/root/psvibe-sales-bot')
    if result.returncode == 0:
        logger.info("✅ Python compilation successful")
    else:
        logger.info(f"❌ Compilation error: {result.stderr}")
        sys.exit(1)
except Exception as e:
    logger.info(f"❌ Compilation test failed: {e}")
    sys.exit(1)
