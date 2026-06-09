
from bot import *
"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta




async def cmd_setattend_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /setattend — PIN then attendance."""
    return await _pin_then("setattend", "Attendance", update, context)

async def cmd_setattend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start attendance wizard — pick staff to record leave/late for."""
    context.user_data.clear()
    staff_list = fetch_staff()
    context.user_data["attend_staff_list"] = staff_list
    context.user_data["attend_idx"]        = 0
    context.user_data["attend_records"]    = {}
    month_str   = now_mmt().strftime("%Y-%m")
    month_label = now_mmt().strftime("%B %Y")
    context.user_data["attend_month"] = month_str
    kb = [[s] for s in staff_list] + [[BTN_CANCEL]]
    await update.message.reply_text(
        f"📅 *Attendance — {month_label}*\n\n"
        f"ခွင့်ယူ / နောက်ကျ မှတ်တမ်းကို Staff တစ်ယောက်ချင်း ထည့်ပေးပါ\n\n"
        f"မှတ်မည့် Staff ကို ရွေးပါ -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ATTEND_STAFF

async def step_attend_staff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_ATTEND_DONE:
        return await _attend_finish(update, context)
    staff_list = context.user_data.get("attend_staff_list", [])
    if text not in staff_list:
        await update.message.reply_text("⚠️ Keyboard မှ Staff ရွေးပေးပါ -")
        return ATTEND_STAFF
    context.user_data["attend_current"] = text
    kb = [[BTN_ATTEND_SKIP], [BTN_CANCEL]]
    await update.message.reply_text(
        f"👤 *{text}*\n\n"
        f"📅 *ခွင့်ယူ ရက်* ဘယ်နှစ်ရက် ထည့်မည်နည်း?\n"
        f"_(0 ဆိုရင် Skip နှိပ်ပါ)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ATTEND_LEAVE

async def step_attend_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_ATTEND_SKIP:
        context.user_data["_att_leave"] = 0
    else:
        try:
            days = int(text)
            if days < 0:
                raise ValueError
            context.user_data["_att_leave"] = days
        except ValueError:
            await update.message.reply_text("⚠️ ဂဏန်းသက်သက် ရိုက်ပေးပါ (0 ↑) -")
            return ATTEND_LEAVE
    kb = [[BTN_ATTEND_SKIP], [BTN_CANCEL]]
    await update.message.reply_text(
        f"⏰ *နောက်ကျ ကြိမ်* ဘယ်နှစ်ကြိမ်?\n"
        f"_(0 ဆိုရင် Skip နှိပ်ပါ)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ATTEND_LATE

async def step_attend_late(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_ATTEND_SKIP:
        context.user_data["_att_late"] = 0
        context.user_data["_att_deduct"] = 500
        return await _attend_save_and_next(update, context)
    try:
        late = int(text)
        if late < 0:
            raise ValueError
        context.user_data["_att_late"] = late
    except ValueError:
        await update.message.reply_text("⚠️ ဂဏန်းသက်သက် ရိုက်ပေးပါ (0 ↑) -")
        return ATTEND_LATE
    if context.user_data["_att_late"] == 0:
        context.user_data["_att_deduct"] = 500
        return await _attend_save_and_next(update, context)
    kb = [[BTN_ATTEND_SKIP], [BTN_CANCEL]]
    await update.message.reply_text(
        f"💸 *တစ်ကြိမ် နောက်ကျ ဖြတ်တောက်ကြေး*\n"
        f"_(default 500 Ks — Skip နှိပ်ရင် 500 Ks သုံးမည်)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ATTEND_DEDUCT

async def step_attend_deduct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await cmd_cancel(update, context)
    if text == BTN_ATTEND_SKIP:
        context.user_data["_att_deduct"] = 500
    else:
        try:
            amt = int(text.replace(",", ""))
            if amt < 0:
                raise ValueError
            context.user_data["_att_deduct"] = amt
        except ValueError:
            await update.message.reply_text("⚠️ ဂဏန်းသက်သက် ရိုက်ပေးပါ -")
            return ATTEND_DEDUCT
    return await _attend_save_and_next(update, context)

async def _attend_save_and_next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save current staff attendance then ask for next staff or finish."""
    d              = context.user_data
    staff          = d.get("attend_current", "")
    leave_days     = d.pop("_att_leave", 0)
    late_count     = d.pop("_att_late", 0)
    deduct_per_late= d.pop("_att_deduct", 500)
    month_str      = d.get("attend_month", now_mmt().strftime("%Y-%m"))

    save_attendance(month_str, staff, leave_days, late_count, deduct_per_late)
    d.setdefault("attend_records", {})[staff] = {
        "leave": leave_days, "late": late_count, "deduct": deduct_per_late,
    }

    remaining = [s for s in d.get("attend_staff_list", []) if s not in d["attend_records"]]
    if remaining:
        kb = [[s] for s in remaining] + [[BTN_ATTEND_DONE], [BTN_CANCEL]]
        await update.message.reply_text(
            f"✅ *{staff}* — မှတ်တမ်းသိမ်းပြီး\n\n"
            f"📅 ခွင့်: *{leave_days} ရက်*  ⏰ နောက်ကျ: *{late_count} ကြိမ်*\n\n"
            f"နောက် Staff ရွေးပါ (သို့မဟုတ် ✅ ပြီးပါပြီ) -",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return ATTEND_STAFF
    return await _attend_finish(update, context)

async def _attend_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show summary and exit."""
    records    = context.user_data.get("attend_records", {})
    month_str  = context.user_data.get("attend_month", "")
    month_label= now_mmt().strftime("%B %Y")
    if not records:
        await update.message.reply_text("ℹ️ မှတ်တမ်း မထည့်ရသေး — OK ပါ။")
        return await show_main_menu(update, context)
    lines = [f"✅ *Attendance Saved — {month_label}*\n━━━━━━━━━━━━━━━━━━"]
    for s, rec in records.items():
        lines.append(
            f"👤 *{s}*\n"
            f"   📅 ခွင့်: {rec['leave']} ရက်  ⏰ နောက်ကျ: {rec['late']} ကြိမ် ({rec['deduct']:,}/ကြိမ်)"
        )
    lines.append("\n_/payroll နဲ့ စစ်ကြည့်နိုင်ပါပြီ_")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    return await show_main_menu(update, context)

