"""PS VIBE Bot — Referral Code Assignment handlers.
Auto-refactored from monolithic handlers.py (Phase 6).
"""
# ═══════ Imports from bot package ═══════
import bot as _bot_module  # for globals that need mutation  # noqa: F401
from bot import *  # noqa: F401,F403


async def prompt_referral_code(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    member_id: str,
) -> int:
    """Ask staff to enter a referral code for the member (member card required)."""
    context.user_data["ref_member_id"] = member_id
    existing = fetch_referral_code(member_id)
    existing_ln = f"\n_(လက်ရှိ Code: *{existing}*)_" if existing else ""
    await update.message.reply_text(
        f"🎁 *Referral Code သတ်မှတ်*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🪖 Member: *{member_id}*{existing_ln}\n\n"
        f"Referral Code ရိုက်ပါ -\n"
        f"_(ဥပမာ: REF-001, PSV-TIN-001)_\n\n"
        f"⚠️ Member Card ရှိသော Member များသာ Referral Code ရနိုင်သည်",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [["❌ ဖျက်မည် (Remove Code)"], [BTN_BACK, BTN_CANCEL]],
            resize_keyboard=True,
        ),
    )
    return REFERRAL_CODE

async def step_referral_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle referral code input from staff."""
    import re as _re
    text      = (update.message.text or "").strip()
    member_id = context.user_data.get("ref_member_id", "")

    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_BACK:
        if member_id:
            return await prompt_mm_lookup(update, context)
        return await show_mm_menu(update, context)

    # Validate member still exists
    members = fetch_members()
    if member_id not in members:
        await update.message.reply_text(
            "⚠️ Member မတွေ့ပါ — ထပ်ကြိုးစာပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
        )
        context.user_data.pop("ref_member_id", None)
        return MM_MENU

    # Handle remove code
    if text == "❌ ဖျက်မည် (Remove Code)":
        ok = await asyncio.get_event_loop().run_in_executor(
            None, save_referral_code, member_id, ""
        )
        if ok:
            await update.message.reply_text(
                f"✅ *{member_id}* — Referral Code ဖျက်ပြီး",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
            )
        else:
            await update.message.reply_text(
                "❌ ဖျက်မှ မအောင်မြင်ပါ — ထပ်ကြိုးစာပါ",
                reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
            )
        context.user_data.pop("ref_member_id", None)
        return MM_MENU

    # Validate code format: alphanumeric, hyphens, underscores, 4-20 chars
    if not _re.match(r'^[A-Za-z0-9_\-]{4,20}$', text):
        await update.message.reply_text(
            "⚠️ Code format မမှန်ပါ\n"
            "• 4–20 characters\n"
            "• Letters, numbers, hyphens, underscores သာ ခွင့်ပြု\n"
            "• ဥပမာ: REF-001, PSV-TIN-001\n\n"
            "ထပ်ရိုက်ပါ -",
            reply_markup=ReplyKeyboardMarkup(
                [["❌ ဖျက်မည် (Remove Code)"], [BTN_BACK, BTN_CANCEL]],
                resize_keyboard=True,
            ),
        )
        return REFERRAL_CODE

    # Check uniqueness across all members
    try:
        all_rows = member_sh.get_all_values()
        for row in all_rows[1:]:
            if len(row) > 13 and row[13].strip().upper() == text.upper():
                existing_owner = row[1].strip() if len(row) > 1 else "?"
                if existing_owner != member_id:
                    await update.message.reply_text(
                        f"⚠️ Code *{text}* ကို *{existing_owner}* မှာ သုးနေပြီး\n"
                        f"တခ်ခာ Code ရိုက်ပါ -",
                        parse_mode="Markdown",
                        reply_markup=ReplyKeyboardMarkup(
                            [["❌ ဖျက်မည် (Remove Code)"], [BTN_BACK, BTN_CANCEL]],
                            resize_keyboard=True,
                        ),
                    )
                    return REFERRAL_CODE
    except Exception as e:
        logging.warning("Referral uniqueness check failed: %s", e)

    # Save the code
    ok = await asyncio.get_event_loop().run_in_executor(
        None, save_referral_code, member_id, text
    )
    context.user_data.pop("ref_member_id", None)
    if ok:
        await update.message.reply_text(
            f"✅ *Referral Code သတ်မှတ်ပြီး*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🪖 Member: *{member_id}*\n"
            f"🎁 Code: *{text}*\n\n"
            f"_Customer Bot မှ Member ကို code ပြပေးမည်_",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
        )
    else:
        await update.message.reply_text(
            "❌ Code သိမ်မှ မအောင်မြင်ပါ — ထပ်ကြိုးစာပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
        )
    return MM_MENU
