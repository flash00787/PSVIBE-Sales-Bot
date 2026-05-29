from bot import bonus, col, empty, fallback, fetch_attendance, fetch_base_salaries, fetch_staff, filled, fmt, hrs, lines, m, mins, n, now_mmt, parts, row, s, sales_sh, staff, topup_sh, total, val
"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta




def calc_monthly_payroll(month_str: str | None = None) -> list[dict]:
    """
    Calculate monthly payroll for all staff.
    month_str format: 'YYYY-MM' (default = current month).
    Rules:
      - New Member card: 1,500 Ks per card registered
      - Game play bonus (BUSINESS-WIDE total mins):
          ≥ 90,000 mins (1,500 hrs) → 50,000 Ks each
          ≥ 120,000 mins (2,000 hrs) → 100,000 Ks each
      - Food & Drink: daily TOTAL ≥ 50,000 Ks
          → 5% of amount EXCEEDING 50,000 each day
    """
    if month_str is None:
        month_str = now_mmt().strftime("%Y-%m")
    year_i, mon_i = int(month_str[:4]), int(month_str[5:7])

    staff_list = fetch_staff()
    if not staff_list:
        return []

    # daily_food_total: date_key → total F&D sales for that day (ALL staff combined)
    daily_food_total: dict[str, int] = {}
    total_play_mins = 0   # BUSINESS-WIDE sum — col O may be empty for older sessions

    def _parse_date(val: str):
        for fmt in ("%m/%d/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(val.strip(), fmt)
            except ValueError:
                pass
        # fallback: try splitting manually for M/D/YYYY
        try:
            parts = val.strip().split("/")
            if len(parts) == 3:
                return datetime(int(parts[2]), int(parts[0]), int(parts[1]))
        except Exception as e:
            logger.error("_parse_date: %s", e, exc_info=True)
            pass
        return None

    # ── Sales_Daily: col E=PlayMins (idx4), G=FoodTotal (idx6) ──
    try:
        sales_rows = sales_sh.get_all_values()
        for row in sales_rows[1:]:
            if len(row) < 7:
                continue
            d = _parse_date(row[0])
            if not d or d.year != year_i or d.month != mon_i:
                continue
            day_key = d.strftime("%Y-%m-%d")

            # Sum ALL play_mins for the month (regardless of staff field)
            total_play_mins += _int(row[4])

            # Food — accumulate daily TOTAL regardless of staff
            daily_food_total[day_key] = daily_food_total.get(day_key, 0) + _int(row[6])
    except Exception as e:
        logging.warning("calc_monthly_payroll sales read: %s", e)

    # ── TopUp_Log: count total new member registrations for the month ──
    total_nm_count = 0
    try:
        topup_rows = topup_sh.get_all_values()
        for row in topup_rows[1:]:
            if len(row) < 9:
                continue
            if row[8].strip() != "First Purchase":
                continue
            d = _parse_date(row[0].strip())
            if not d or d.year != year_i or d.month != mon_i:
                continue
            total_nm_count += 1
    except Exception as e:
        logging.warning("calc_monthly_payroll topup read: %s", e)

    # ── Shared commissions (same for ALL staff) ──
    # New Member: total cards × 1,500 each
    shared_nm_comm = total_nm_count * 1500

    # Food & Drink: days where cafe total ≥ 50,000 → 5% on amount ABOVE 50,000
    # e.g. 60,000 → (60,000-50,000)*5% = 500; 120,000 → 70,000*5% = 3,500
    food_days_qualified = 0
    shared_food_comm    = 0
    for daily_total in daily_food_total.values():
        if daily_total >= 50000:
            shared_food_comm += int((daily_total - 50000) * 0.05)
            food_days_qualified += 1

    base_salaries = fetch_base_salaries()
    attendance    = fetch_attendance(month_str)

    # Business-wide play bonus (same for all staff — total mins not per-staff)
    play_hrs_total = round(total_play_mins / 60, 1)
    game_bonus_shared = (
        100000 if total_play_mins >= 120000 else
        (50000 if total_play_mins >= 90000 else 0)
    )

    payroll = []
    for s in staff_list:
        commission = game_bonus_shared + shared_nm_comm + shared_food_comm
        base_sal   = base_salaries.get(s, 0)

        att = attendance.get(s, {})
        leave_days      = att.get("leave_days", 0)
        late_count      = att.get("late_count", 0)
        deduct_per_late = att.get("deduct_per_late", 500)
        leave_deduct    = int((base_sal / 26) * leave_days) if base_sal > 0 and leave_days > 0 else 0
        late_deduct     = late_count * deduct_per_late
        total_deduct    = leave_deduct + late_deduct
        net_total       = base_sal + commission - total_deduct

        payroll.append({
            "staff":               s,
            "base_salary":         base_sal,
            "play_hrs":            play_hrs_total,
            "play_mins":           total_play_mins,
            "game_bonus":          game_bonus_shared,
            "nm_count":            total_nm_count,
            "nm_commission":       shared_nm_comm,
            "food_commission":     shared_food_comm,
            "food_days_qualified": food_days_qualified,
            "total_commission":    commission,
            "leave_days":          leave_days,
            "late_count":          late_count,
            "deduct_per_late":     deduct_per_late,
            "leave_deduct":        leave_deduct,
            "late_deduct":         late_deduct,
            "total_deduct":        total_deduct,
            "grand_total":         net_total,
            "advance":             0,          # filled below
            "net_total":           net_total,  # remaining = grand_total - advance
        })

    # Attach salary advances for this month
    try:
        advances = fetch_salary_advances(month_str)
        for p in payroll:
            adv_data       = advances.get(p["staff"], {"total": 0, "cash": 0, "kpay": 0})
            p["advance"]      = adv_data["total"]
            p["advance_cash"] = adv_data["cash"]
            p["advance_kpay"] = adv_data["kpay"]
            p["net_total"]    = max(0, p["grand_total"] - adv_data["total"])
    except Exception as e:
        logging.warning("calc_monthly_payroll advances: %s", e)

    return payroll

async def cmd_payroll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show monthly payroll breakdown for all staff."""
    month_str   = now_mmt().strftime("%Y-%m")
    month_label = now_mmt().strftime("%B %Y")
    await update.message.reply_text("⏳ Payroll တွက်နေသည်...", reply_markup=ReplyKeyboardRemove())
    try:
        payroll = calc_monthly_payroll(month_str)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await show_main_menu(update, context)

    if not payroll:
        await update.message.reply_text(
            "⚠️ Staff ဒေတာ မရှိပါ\n\n"
            "Google Sheet → *Setting* tab:\n"
            "• S2:S3 — Staff Name ထည့်ပါ\n"
            "• T2:T3 — Base Salary ထည့်ပါ",
            parse_mode="Markdown",
        )
        return await show_main_menu(update, context)

    lines = [f"💼 *Salary & Payroll — {month_label}*\n━━━━━━━━━━━━━━━━━━"]
    for p in payroll:
        if p["play_mins"] >= 120000:
            bonus_note = "🏆 ≥2,000 hrs"
        elif p["play_mins"] >= 90000:
            bonus_note = "🎯 ≥1,500 hrs"
        else:
            hrs_left = round((90000 - p["play_mins"]) / 60, 1)
            bonus_note = f"_{hrs_left:,} hrs လိုသေး_"
        base_line = f"💵 Base Salary    : *{p['base_salary']:,} Ks*\n" if p["base_salary"] > 0 else ""

        # Deduction lines
        deduct_lines = ""
        if p["leave_days"] > 0 or p["late_count"] > 0:
            deduct_lines += f"─────────────────\n"
        if p["leave_days"] > 0:
            deduct_lines += f"📅 ခွင့်ယူ        : *{p['leave_days']} ရက်* → *-{p['leave_deduct']:,} Ks*\n"
        if p["late_count"] > 0:
            deduct_lines += f"⏰ နောက်ကျ       : *{p['late_count']} ကြိမ်* × {p['deduct_per_late']:,} → *-{p['late_deduct']:,} Ks*\n"
        if p["total_deduct"] > 0:
            deduct_lines += f"📉 ဖြတ်တောက်     : *-{p['total_deduct']:,} Ks*\n"

        lines.append(
            f"\n👤 *{p['staff']}*\n"
            f"─────────────────\n"
            f"{base_line}"
            f"🎮 Game Play     : *{p['play_hrs']:,.1f} hrs*  {bonus_note}\n"
            f"   Play Bonus   : *{p['game_bonus']:,} Ks*\n"
            f"🆕 New Members   : *{p['nm_count']} cards* → *{p['nm_commission']:,} Ks*\n"
            f"🍔 Food Comm     : *{p['food_days_qualified']} day(s)* → *{p['food_commission']:,} Ks*\n"
            f"📊 Commission    : *{p['total_commission']:,} Ks*\n"
            f"{deduct_lines}"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Gross Payable  : {p['grand_total']:,} Ks*"
            + (
                f"\n💸 Advance Paid    : *-{p['advance']:,} Ks*\n"
                f"💵 *Remaining Pay  : {p['net_total']:,} Ks*"
                if p.get("advance", 0) > 0 else ""
            )
        )
    lines.append("\n\n_/setattend နဲ့ ခွင့်/နောက်ကျ ထည့်နိုင်သည်_")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    return await show_main_menu(update, context)

async def cmd_payroll_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /payroll — PIN then payroll."""
    return await _pin_then("payroll", "Payroll", update, context)

async def cmd_kpi_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /kpi — PIN then staff KPI."""
    return await _pin_then("kpi", "Staff KPI", update, context)

