from bot import *
"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta




async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shortcut: /admin — Admin Panel PIN prompt."""
    return await _pin_then("admin", "Admin Panel", update, context)

async def step_admin_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify Admin PIN — delete message then route."""
    entered = update.message.text.strip()
    try:
        await update.message.delete()
    except Exception as e:
        logger.error("step_admin_pin: %s", e, exc_info=True)
        pass
    if entered != STOCK_ACCESS_PIN:
        await update.message.reply_text(
            "❌ PIN မမှန်ကန်ပါ။\n\nMain Menu သို့ ပြန်သွားမည်။",
            reply_markup=ReplyKeyboardRemove(),
        )
        return await show_main_menu(update, context)

    # Route to specific command if called via direct /cmd shortcut
    after = context.user_data.pop("_after_pin", None)
    if after == "payroll":
        return await cmd_payroll(update, context)
    if after == "kpi":
        return await cmd_staff_kpi(update, context)
    if after == "setattend":
        return await cmd_setattend(update, context)
    if after == "finance":
        return await show_finance_menu(update, context)
    return await show_admin_menu(update, context)

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Admin sub-menu."""
    kb = [
        [BTN_STOCK_UPDATE,   BTN_ADMIN_ATTEND],
        [BTN_ADMIN_SAL_ADV,  BTN_PAYROLL],
        [BTN_STAFF_KPI,      BTN_ADMIN_LIB],
        [BTN_ADMIN_PNL,      BTN_ADMIN_CF],
        [BTN_PROMO_REPORTS,  BTN_FINANCE],
        [BTN_CON_MANAGE,     BTN_BACK_MAIN],
    ]
    await update.message.reply_text(
        "🔧 *Admin Panel*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Action ရွေးပါ ↓",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return ADMIN_MENU

async def step_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route Admin menu choices."""
    choice = update.message.text.strip()

    if choice == BTN_BACK_MAIN:
        return await show_main_menu(update, context)
    if choice == BTN_STOCK_UPDATE:
        return await show_stock_menu(update, context)
    if choice == BTN_ADMIN_ATTEND:
        return await cmd_setattend(update, context)
    if choice == BTN_ADMIN_SAL_ADV:
        return await cmd_admin_sal_adv(update, context)
    if choice == BTN_PAYROLL:
        return await cmd_payroll(update, context)
    if choice == BTN_STAFF_KPI:
        return await cmd_staff_kpi(update, context)
    if choice == BTN_ADMIN_PNL:
        return await cmd_admin_pnl(update, context)
    if choice == BTN_ADMIN_CF:
        return await cmd_admin_cashflow(update, context)
    if choice == BTN_ADMIN_LIB:
        return await cmd_admin_liability(update, context)
    if choice == BTN_ADMIN_BOOK:
        return await cmd_admin_bookings(update, context)
    if choice == BTN_STAFF_BOOK:
        return await cmd_staff_booking(update, context)
    if choice == BTN_SBK_CONFIRMED:
        return await cmd_confirmed_bookings(update, context)
    if choice == BTN_CONSOLES:
        return await show_console_menu(update, context)
    if choice == BTN_CON_MANAGE:
        return await show_con_mgmt_menu(update, context)
    if choice == BTN_PROMO_REPORTS:
        return await cmd_promo_reports(update, context)
    if choice == BTN_FINANCE:
        return await show_finance_menu(update, context)

    return await show_admin_menu(update, context)

def fetch_salary_advances(month_str: str) -> dict[str, dict]:
    """Return {staff: {total, cash, kpay}} for the given month (YYYY-MM).
    Sheet cols: A=Date, B=Staff, C=Amount, D=Payment(Cash/KPay), E=Note
    """
    year_i, mon_i = int(month_str[:4]), int(month_str[5:7])
    result: dict[str, dict] = {}
    try:
        sh = get_salary_adv_sh()
        for row in sh.get_all_values()[1:]:
            if len(row) < 3 or not row[0].strip():
                continue
            d = _parse_date_mmt(row[0].strip())
            if not d or d.year != year_i or d.month != mon_i:
                continue
            staff   = row[1].strip()
            amount  = _int(row[2])
            payment = row[3].strip().lower() if len(row) > 3 else "cash"
            if staff and amount > 0:
                if staff not in result:
                    result[staff] = {"total": 0, "cash": 0, "kpay": 0}
                result[staff]["total"] += amount
                if "kpay" in payment:
                    result[staff]["kpay"] += amount
                else:
                    result[staff]["cash"] += amount
    except Exception as e:
        logging.warning("fetch_salary_advances: %s", e)
    return result

async def cmd_admin_sal_adv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: start Salary Advance recording."""
    staff_list = fetch_staff()
    if not staff_list:
        await update.message.reply_text("❌ Staff list ရှာမတွေ့ပါ။")
        return await show_admin_menu(update, context)

    kb = [[s] for s in staff_list] + [[BTN_BACK_MAIN]]
    await update.message.reply_text(
        "💸 *Salary Advance မှတ်တမ်း*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Advance ပေးမည့် Staff ကို ရွေးပါ:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return SAL_ADV_STAFF

def _parse_date_mmt(val: str):
    for fmt in ("%m/%d/%Y", "%-m/%-d/%Y"):
        try:
            return datetime.strptime(val.strip(), fmt)
        except ValueError:
            continue
    return None

def fetch_alltime_effective_rate() -> float:
    """All-time average Ks/min across every TopUp_Log row (incl. bonus mins).

    This is the only correct rate to use for both:
      - Member earned revenue  (mins used × this rate)
      - Card Liability         (wallet balance mins × this rate)

    Example: member paid 90,000 for 600 base + 100 bonus = 700 total mins
             → rate = 90,000 / 700 = 128.57 Ks/min  (NOT 166.67 Ks/min)
    """
    total_paid = 0
    total_mins = 0
    try:
        for row in topup_sh.get_all_values()[1:]:
            if len(row) < 8:
                continue
            amt  = _int(row[4])
            mins = _int(row[7])   # col H = AddedMins (including bonus)
            if amt > 0 and mins > 0:
                total_paid += amt
                total_mins += mins
    except Exception as e:
        logging.warning("fetch_alltime_effective_rate: %s", e)
    if total_mins > 0:
        return round(total_paid / total_mins, 2)
    # Hard fallback — avoids using naive base_rate
    return fetch_base_rate() or 150.0

def calc_monthly_pnl(month_str: str) -> dict:
    """Aggregate monthly P&L, cash-flow and liability data from all sheets."""
    year_i, mon_i = int(month_str[:4]), int(month_str[5:7])

    # Per-member rates (col L) — fall back to all-time avg if not yet stored
    alltime_rate = fetch_alltime_effective_rate()
    rate_dict    = build_member_rate_dict()   # {member_id: stored_rate}

    res = dict(
        guest_game_rev=0,
        food_rev=0,
        discount_total=0,
        wallet_deduct_mins=0,
        topup_amount=0, topup_kpay=0, topup_cash=0, topup_mins=0,
        sales_kpay=0,           # KPay received from all sales rows (ops cash in)
        sales_cash=0,           # Cash received from all sales rows (ops cash in)
        stock_in_total=0,
        stock_in_cash=0,
        stock_in_kpay=0,
        stock_out_cogs=0,
        payroll_total=0,        # gross salary expense (P&L)
        payroll_advance=0,      # advances already paid mid-month (total)
        payroll_advance_cash=0, # advance portion paid by Cash
        payroll_advance_kpay=0, # advance portion paid by KPay
        payroll_net_pay=0,      # remaining payout at month end
        effective_rate=alltime_rate,
        alltime_rate=alltime_rate,
        member_game_rev=0,
    )

    # 1. Sales_Daily ─ col layout: A=date B=v_no C=member D=console E=play_mins
    #                               F=game_amt G=food_total H=discount I=net_total
    #                               J=kpay K=cash ... N=wallet_deduct(idx13)
    member_deduct: dict[str, int] = {}
    try:
        for row in sales_sh.get_all_values()[1:]:
            if len(row) < 7:
                continue
            d = _parse_date_mmt(row[0])
            if not d or d.year != year_i or d.month != mon_i:
                continue
            member_id  = row[2].strip() if len(row) > 2 else ""
            food_total = _int(row[6]) if len(row) > 6 else 0
            discount   = _int(row[7]) if len(row) > 7 else 0
            kpay       = _int(row[9]) if len(row) > 9 else 0
            cash       = _int(row[10]) if len(row) > 10 else 0
            res["food_rev"]       += food_total
            res["discount_total"] += discount
            # ALL kpay/cash from sales = operating cash received (guest game + food)
            res["sales_kpay"] += kpay
            res["sales_cash"] += cash
            is_guest = member_id in ("", "0 (Guest)")
            if is_guest:
                game_amt = _int(row[5]) if len(row) > 5 else 0
                res["guest_game_rev"] += game_amt
            else:
                w_deduct = _int(row[13]) if len(row) > 13 else 0
                res["wallet_deduct_mins"] += w_deduct
                member_deduct[member_id] = member_deduct.get(member_id, 0) + w_deduct
    except Exception as e:
        logging.warning("calc_pnl sales: %s", e)

    # 2. TopUp_Log
    try:
        for row in topup_sh.get_all_values()[1:]:
            if len(row) < 8:
                continue
            d = _parse_date_mmt(row[0])
            if not d or d.year != year_i or d.month != mon_i:
                continue
            res["topup_amount"] += _int(row[4])
            res["topup_kpay"]   += _int(row[5]) if len(row) > 5 else 0
            res["topup_cash"]   += _int(row[6]) if len(row) > 6 else 0
            res["topup_mins"]   += _int(row[7]) if len(row) > 7 else 0
    except Exception as e:
        logging.warning("calc_pnl topup: %s", e)

    # Per-member revenue: deducted_mins × each member's own stored rate
    # Falls back to alltime_rate for members without a stored rate (legacy / missing)
    member_game_rev = 0
    for m_id, mins in member_deduct.items():
        rate = rate_dict.get(m_id, alltime_rate)
        member_game_rev += int(mins * rate)
    res["member_game_rev"] = member_game_rev

    # 3. Stock_In (purchases)
    try:
        for row in stock_in_sh.get_all_values()[1:]:
            if len(row) < 5:
                continue
            d = _parse_date_mmt(row[0])
            if not d or d.year != year_i or d.month != mon_i:
                continue
            total   = _int(row[4])
            payment = row[5].strip() if len(row) > 5 else ""
            res["stock_in_total"] += total
            # Parse "Cash X / KPay Y" or plain "Cash" / "KPay"
            if "/" in payment:
                parts = payment.split("/")
                for p in parts:
                    p = p.strip()
                    if p.lower().startswith("cash"):
                        res["stock_in_cash"] += _int("".join(filter(lambda c: c.isdigit(), p)))
                    elif p.lower().startswith("kpay"):
                        res["stock_in_kpay"] += _int("".join(filter(lambda c: c.isdigit(), p)))
            elif payment.lower() == "cash":
                res["stock_in_cash"] += total
            elif payment.lower() == "kpay":
                res["stock_in_kpay"] += total
    except Exception as e:
        logging.warning("calc_pnl stock_in: %s", e)

    # 4. Stock_Out COGS (col H = idx 7)
    try:
        for row in stock_sh.get_all_values()[1:]:
            if len(row) < 8:
                continue
            d = _parse_date_mmt(row[0])
            if not d or d.year != year_i or d.month != mon_i:
                continue
            res["stock_out_cogs"] += _int(row[7])
    except Exception as e:
        logging.warning("calc_pnl stock_out: %s", e)

    # 5. Payroll — gross salary expense + advance breakdown
    try:
        payroll = calc_monthly_payroll(month_str)
        res["payroll_total"]         = sum(p["grand_total"]    for p in payroll)
        res["payroll_advance"]       = sum(p.get("advance",      0) for p in payroll)
        res["payroll_advance_cash"]  = sum(p.get("advance_cash", 0) for p in payroll)
        res["payroll_advance_kpay"]  = sum(p.get("advance_kpay", 0) for p in payroll)
        res["payroll_net_pay"]       = sum(p.get("net_total",    0) for p in payroll)
    except Exception as e:
        logging.warning("calc_pnl payroll: %s", e)

    return res

async def cmd_admin_pnl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Monthly P&L — revenue recognition basis (via API cache)."""
    month_label = now_mmt().strftime("%B %Y")
    await update.message.reply_text(
        f"⏳ *{month_label}* P&L တွက်နေသည်...",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    try:
        r = _replit_get("sheets/pnl")
        if "error" in r:
            raise RuntimeError(r["error"])
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await show_admin_menu(update, context)

    game_rev    = r["guest_game_rev"] + r["member_game_rev"]
    total_rev   = game_rev + r["food_rev"]
    net_rev     = total_rev - r["discount_total"]
    total_cost  = r["stock_out_cogs"] + r["payroll_total"]
    net_profit  = net_rev - total_cost

    adv_received = r["topup_amount"]
    adv_earned   = r["member_game_rev"]
    adv_delta    = adv_received - adv_earned   # +ve = liability grew, -ve = liability shrank

    def _ks(v):  return f"{v:,} Ks"
    def _neg(v): return f"({abs(v):,} Ks)"
    profit_icon = "🟢" if net_profit >= 0 else "🔴"

    rate_line = (
        f"   ↳ {r['wallet_deduct_mins']:,} mins × {r['effective_rate']:,.1f} Ks/min\n"
        if r["wallet_deduct_mins"] > 0 else ""
    )
    adv_line = (
        f"   ↳ Advance: {r['payroll_advance']:,}  |  Remaining: {r['payroll_net_pay']:,}\n"
        if r.get("payroll_advance", 0) > 0 else ""
    )
    adv_delta_tag = f"+{adv_delta:,}" if adv_delta >= 0 else f"({abs(adv_delta):,})"
    adv_dir  = "⬆️ Liability ↑" if adv_delta >= 0 else "⬇️ Liability ↓"

    msg = (
        f"📊 *P&L — {month_label}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💹 *REVENUE (Earned)*\n"
        f"  🎮 Guest Game   : *{_ks(r['guest_game_rev'])}*\n"
        f"  💳 Member Game  : *{_ks(r['member_game_rev'])}*\n"
        f"{rate_line}"
        f"  🍔 Food & Drink : *{_ks(r['food_rev'])}*\n"
        f"  🏷️ Discount     : *{_neg(r['discount_total'])}*\n"
        f"  ─────────────────\n"
        f"  💰 Net Revenue  : *{_ks(net_rev)}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💸 *COSTS*\n"
        f"  📦 Food COGS    : *{_neg(r['stock_out_cogs'])}*\n"
        f"  👔 Payroll      : *{_neg(r['payroll_total'])}*\n"
        f"{adv_line}"
        f"  ─────────────────\n"
        f"  📤 Total Costs  : *{_neg(total_cost)}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{profit_icon} *Net Profit : "
        f"{'(' + str(abs(net_profit)) + ')' if net_profit < 0 else str(net_profit)} Ks*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💳 *Member Card Advance*\n"
        f"  📨 Topup ဝင်    : *+{_ks(adv_received)}*\n"
        f"  ✅ Earned (used) : *{_neg(adv_earned)}*\n"
        f"  ─────────────────\n"
        f"  {adv_dir} : *{adv_delta_tag} Ks*\n"
        f"  _({r['topup_mins']:,} mins ထည့်  |  {r['wallet_deduct_mins']:,} mins သုံး)_\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"_Rate: {r['effective_rate']:,.1f} Ks/min_"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    return await show_admin_menu(update, context)

async def cmd_admin_cashflow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Monthly Cash Flow — all actual money movements (via API cache)."""
    month_label = now_mmt().strftime("%B %Y")
    await update.message.reply_text(
        f"⏳ *{month_label}* Cash Flow တွက်နေသည်...",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    try:
        r = _replit_get("sheets/pnl")
        if "error" in r:
            raise RuntimeError(r["error"])
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return await show_admin_menu(update, context)

    sal_advance     = r.get("payroll_advance", 0)
    sal_net_pay     = r.get("payroll_net_pay", 0)
    sal_gross       = r["payroll_total"]
    sal_adv_cash    = r.get("payroll_advance_cash", 0)
    sal_adv_kpay    = r.get("payroll_advance_kpay", 0)

    # Cash IN
    sales_cash  = r["sales_cash"]
    sales_kpay  = r["sales_kpay"]
    topup_cash  = r["topup_cash"]
    topup_kpay  = r["topup_kpay"]
    total_in    = sales_cash + sales_kpay + topup_cash + topup_kpay

    # Cash OUT
    stock_out   = r["stock_in_total"]
    total_out   = stock_out + sal_gross
    net_cash    = total_in - total_out

    def _ks(v):   return f"{v:,} Ks"
    def _neg(v):  return f"({abs(v):,} Ks)"
    def _icon(v): return "🟢" if v >= 0 else "🔴"

    # Payroll breakdown
    if sal_advance > 0:
        pay_line = (
            f"  👔 Payroll       : *{_neg(sal_gross)}*\n"
            f"     Advance ထုတ်   : ({sal_advance:,})  Cash {sal_adv_cash:,} / KPay {sal_adv_kpay:,}\n"
            f"     Month-end ကျန် : ({sal_net_pay:,})\n"
        )
    else:
        pay_line = f"  👔 Payroll       : *{_neg(sal_gross)}*\n"

    msg = (
        f"💵 *Cash Flow — {month_label}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🟢 *CASH ဝင် (IN)*\n"
        f"  Sales Cash        : *{_ks(sales_cash)}*\n"
        f"  Sales KPay        : *{_ks(sales_kpay)}*\n"
        f"  Member Topup Cash : *{_ks(topup_cash)}*\n"
        f"  Member Topup KPay : *{_ks(topup_kpay)}*\n"
        f"  ─────────────────\n"
        f"  💰 Total IN       : *{_ks(total_in)}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔴 *CASH ထွက် (OUT)*\n"
        f"  📦 Stock ဝယ်       : *{_neg(stock_out)}*\n"
        f"     Cash {r['stock_in_cash']:,} / KPay {r['stock_in_kpay']:,}\n"
        f"{pay_line}"
        f"  ─────────────────\n"
        f"  📤 Total OUT      : *{_neg(total_out)}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{_icon(net_cash)} *Net Cash : "
        f"{'(' + str(abs(net_cash)) + ')' if net_cash < 0 else str(net_cash)} Ks*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 *မှတ်ချက်*\n"
        f"  Member Topup ➜ Wallet liability (မိနစ်ကြွေးကျန်)\n"
        f"  {r['topup_mins']:,} mins ထည့်  |  {r['wallet_deduct_mins']:,} mins သုံး"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    return await show_admin_menu(update, context)

async def cmd_admin_liability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Advance Payment Liability — via API cache (no direct sheet reads)."""
    await update.message.reply_text(
        "⏳ Advance Payment Liability တွက်နေသည်...",
        reply_markup=ReplyKeyboardRemove(),
    )
    try:
        liab = _replit_get("sheets/liability")
        pnl  = _replit_get("sheets/pnl")
        if "error" in liab:
            raise RuntimeError(liab["error"])

        active_count    = liab["active_count"]
        total_mins      = liab["total_mins"]
        total_liability = liab["total_liability"]
        alltime_rate    = liab["alltime_rate"]
        stored_count    = liab["stored_rate_count"]
        top_members     = liab["top_members"]   # [{id,name,mins,liability,rate}]

        # This month movement from pnl cache
        month_label = now_mmt().strftime("%B %Y")
        if "error" not in pnl:
            adv_received = pnl["topup_amount"]
            adv_earned   = pnl["member_game_rev"]
            adv_net      = adv_received - adv_earned
            move_sec = (
                f"📅 *This Month ({month_label})*\n"
                f"  📨 Topups     : +{adv_received:,} Ks\n"
                f"  ✅ Earned     : ({adv_earned:,} Ks)\n"
                f"  {'⬆️' if adv_net>=0 else '⬇️'} Net Change : "
                f"{'+'if adv_net>=0 else ''}{adv_net:,} Ks\n"
                f"━━━━━━━━━━━━━━━━━━\n"
            )
        else:
            move_sec = ""

        top_lines = "\n".join(
            f"  {i+1}. *{m['id']}* {m['name'][:9]} — {m['mins']:,} min × {m['rate']:.1f} = *{m['liability']:,} Ks*"
            for i, m in enumerate(top_members)
        )
        top_sec = f"🔝 *Top 5 (Highest Liability)*\n{top_lines}\n━━━━━━━━━━━━━━━━━━\n" if top_lines else ""

        rate_note = (
            f"   _(Per-member rate — {stored_count} stored, "
            f"{max(0, active_count - stored_count)} using avg fallback)_\n"
        )

        msg = (
            f"💳 *Advance Payment Liability*\n"
            f"_(Member Card Unearned Balances)_\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👥 Active Members   : *{active_count}*\n"
            f"⏱️ Total Balance    : *{total_mins:,} mins*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Total Liability : {total_liability:,} Ks*\n"
            f"{rate_note}"
            f"   _(ကျွန်တော်တို့ Member များသို့ ရှင်ပေးရဦးမည့် ငွေ)_\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{move_sec}"
            f"{top_sec}"
        )
    except Exception as e:
        logging.error("cmd_admin_liability: %s", e)
        msg = f"❌ Error: {e}"

    await update.message.reply_text(msg, parse_mode="Markdown")
    return await show_admin_menu(update, context)

