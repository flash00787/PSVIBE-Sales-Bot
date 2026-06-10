from bot import (
    ADMIN_MENU, BTN_BACK_MAIN, MAIN_MENU, _psvibe_get, _psvibe_get_async, now_mmt,
    today_str,
)
"""PS VIBE Bot — Handler module.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
import asyncio
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta
async def cmd_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current inventory levels from Replit API."""
    await update.message.reply_text("⏳ Inventory စစ်နေသည်...", reply_markup=ReplyKeyboardRemove())
    data = await _psvibe_get_async("sheets/inventory")
    if not data:
        await update.message.reply_text(
            "❌ Inventory data ရယူ၍ မရပါ။",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
        )
        return
    items = data.get("items", [])
    STATUS_EMOJI = {
        "In Stock":     "🟢",
        "Low Stock":    "🟡",
        "Out of Stock": "🔴",
        "No Stock":     "⚫",
    }
    lines = ["📦 *Inventory Status*\n━━━━━━━━━━━━━━━━━━"]
    for item in items:
        qty_val = item.get("qty", 0)
        if qty_val > 5:
            derived_status = "In Stock"
        elif qty_val > 0:
            derived_status = "Low Stock"
        elif qty_val == 0:
            derived_status = "Out of Stock"
        else:
            derived_status = "No Stock"
        em    = STATUS_EMOJI.get(derived_status, "⚫")
        stock = max(0, item.get("qty", 0))
        val   = item.get("total", 0)
        name  = item.get("name", "?")
        lines.append(f"{em} *{name}*: {stock} pcs")
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
    )
async def cmd_stocktoday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show today's items sold from Replit API."""
    await update.message.reply_text("⏳ Today's stock data ရယူနေသည်...", reply_markup=ReplyKeyboardRemove())
    data = await _psvibe_get_async("sheets/stock-today")
    if not data:
        await update.message.reply_text("❌ Stock data ရယူ၍ မရပါ။")
        return
    items = data.get("items", [])
    if not items:
        await update.message.reply_text("ℹ️ ဒီနေ့ ပစ္စည်းများ မရောင်းရသေးပါ။")
        return
    total_val = sum(i.get("value", 0) for i in items)
    total_qty = sum(i.get("qty", 0) for i in items)
    lines = [f"🛒 *Items Sold Today — {data.get('date','')}*\n━━━━━━━━━━━━━━━━━━"]
    for item in items:
        for item in items:
            name = item.get("name", "?")
            qty  = item.get("qty", 0)
            val  = item.get("value", 0)
            lines.append(f"• *{name}*: {qty} pcs — {val:,} Ks")
    lines.append(f"━━━━━━━━━━━━━━━━━━\n📦 Total: *{total_qty} items*  💰 *{total_val:,} Ks*")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
async def cmd_promo_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show promotion analytics report for staff.
    Fetches all promotions from Promotions sheet + sales data.
    """
    await update.message.reply_text("⏳ Promo Reports ယူနေတယ်...", reply_markup=ReplyKeyboardRemove())
    kb = ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True)
    try:
        # Fetch all promotions (including inactive) via API
        promo_data = await _psvibe_get_async("sheets/promotions/all")
        promos = promo_data.get("promotions", []) if promo_data else []
        # Fetch Promotions_Log analytics
        log_data   = await _psvibe_get_async("sheets/promotions-log")
        promo_logs = (log_data or {}).get("logs", [])
        promo_summ = (log_data or {}).get("summary", [])  # list of {promo_id, promo_title, usage_count, total_discount, total_net}
        # Fetch today's sales summary
        rd = await _psvibe_get_async("finance/account-balances")
        sales = rd.get("summary") if rd else None
        lines = [
            "📊 *Promotion Reports*",
            "━━━━━━━━━━━━━━━━━━",
        ]
        # Promotion summary
        total = len(promos)
        active_promos   = [p for p in promos if p.get("active")]
        inactive_promos = [p for p in promos if not p.get("active")]
        lines.append(f"🎁 *Promotions Overview*")
        lines.append(f"   Total: {total}  |  Active: {len(active_promos)}  |  Inactive: {len(inactive_promos)}")
        # Breakdown by type
        if promos:
            types_count = {}
            for p in promos:
                ptype = p.get("type", "general")
                if ptype not in types_count:
                    types_count[ptype] = {"total": 0, "active": 0}
                types_count[ptype]["total"] += 1
                if p.get("active"):
                    types_count[ptype]["active"] += 1
            lines.append("")
            lines.append("📋 *By Type:*")
            emoji_map = {
                "discount": "💰",
                "free_item": "🎁",
                "bundle": "📦",
                "cashback": "💳",
                "general": "🎯"
            }
            for ptype, counts in sorted(types_count.items()):
                emoji = emoji_map.get(ptype, "🎁")
                lines.append(f"   {emoji} {ptype.title()}: {counts['total']} (✅ {counts['active']} active)")
        # Active promotions detail
        if active_promos:
            lines.append("")
            lines.append("✅ *Active Promotions:*")
            for p in active_promos:
                emoji = p.get("emoji", "🎁")
                title = p.get("title", "")
                ptype = p.get("type", "general")
                disc  = p.get("discount_percent", "")
                valid = p.get("valid_until", "")
                bundle = p.get("bundle_items", "")
                cond  = p.get("conditions", "")
                pid   = p.get("id", "")
                detail = f"   {emoji} *{title}*"
                if disc:
                    detail += f" — {disc}% OFF"
                if bundle:
                    detail += f" — {bundle}"
                lines.append(detail)
                if valid:
                    lines.append(f"      📅 Valid until: {valid}")
                if cond:
                    lines.append(f"      ℹ️ {cond}")
                # Show usage stats from Promotions_Log
                usage = next((s for s in promo_summ if s.get("promo_id") == pid), None)
                if usage:
                    lines.append(f"      📈 Used: {usage['usage_count']}x  |  Total Discount: {int(usage['total_discount']):,} Ks")
        # Inactive promotions
        if inactive_promos:
            lines.append("")
            lines.append("⏸️ *Inactive Promotions:*")
            for p in inactive_promos:
                lines.append(f"   • {p.get('title', '')} ({p.get('id', '')})")
        # ── Promotions_Log Analytics ─────────────────────────────────────────────
        if promo_summ:
            total_usage    = sum(s.get("usage_count", 0) for s in promo_summ)
            total_discount = sum(s.get("total_discount", 0) for s in promo_summ)
            total_net_rev  = sum(s.get("total_net", 0) for s in promo_summ)
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━")
            lines.append("📈 *Promotion Usage Analytics (All Time):*")
            lines.append(f"   🔢 Total Uses: {total_usage}")
            lines.append(f"   💸 Total Discount Given: {int(total_discount):,} Ks")
            lines.append(f"   💰 Net Revenue (promo sales): {int(total_net_rev):,} Ks")
            # Top promotion by usage
            if promo_summ:
                top = max(promo_summ, key=lambda s: s.get("usage_count", 0))
                lines.append(f"   🏆 Top Promo: *{top['promo_title']}* ({top['usage_count']}x used)")
        # Today's sales context
        if sales:
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━")
            lines.append("💹 *Today's Sales Context:*")
            net = sales.get("today_net", 0)
            cnt = sales.get("today_count", 0)
            lines.append(f"   🎮 Sessions: {cnt}")
            lines.append(f"   💰 Revenue: {net:,} Ks")
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append("💡 Google Sheets \"Promotions\" tab ကို ပြင်ဆင်နိုင်ပါ")
        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=kb,
        )
    except Exception as e:
        logging.error("cmd_promo_reports failed: %s", e)
        await update.message.reply_text(
            f"❌ Promo Reports ယူမရပါ — {str(e)[:60]}",
            reply_markup=kb,
        )
    return ADMIN_MENU
async def cmd_today_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Today's combined sales + stock report with per-staff breakdown."""
    await update.message.reply_text("⏳ Today's report ရယူနေသည်...", reply_markup=ReplyKeyboardRemove())
    rd    = await _psvibe_get_async("finance/account-balances")   # single batch call (was 3 calls)
    sales = rd.get("summary")   if rd else None
    stock = None
    inv = None
    date  = today_str()
    kb    = ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True)
    if not sales and not stock:
        await update.message.reply_text("❌ Data ရယူ၍ မရပါ။", reply_markup=kb)
        return MAIN_MENU
    lines = [f"📊 *Today's Report — {date}*\n━━━━━━━━━━━━━━━━━━"]
    # Sales summary from account balances
    if sales and isinstance(sales, list):
        total_rev = sum(a.get("balance", 0) for a in sales if a.get("type") in ("Cash","Digital"))
        lines.append(f"💰 *Total Balance:* *{total_rev:,} Ks*")
        for a in sales:
            name = a.get("name","?")
            bal = a.get("balance", 0)
            lines.append(f"  • {name}: {bal:,} Ks")
    else:
        lines.append("🎮 Data မရပါ")
    # Per-staff breakdown from Sales_Daily
    sb = None   # API cache (was direct gspread call) -- TODO: Migrate to MySQL via API, direct gspread is fallback only
    staff_stats = sb.get("staff", {}) if sb else {}
    if staff_stats:
        lines.append(f"━━━━━━━━━━━━━━━━━━")
        lines.append(f"👥 *Per-Staff:*")
        for s, sd in staff_stats.items():
            lines.append(f"  👤 *{s}* — {sd['sessions']} sessions | *{sd['revenue']:,} Ks*")
    # Food/Drinks sold today
    if stock and stock.get("items"):
        items        = stock["items"]
        total_qty    = sum(i.get("qty", 0) for i in items)
        total_rev    = sum(i.get("value", 0) for i in items)
        total_cog    = sum(i.get("cogs", 0) for i in items)
        gross_margin = round((total_rev - total_cog) / total_rev * 100) if total_rev > 0 else 0
        lines.append(f"━━━━━━━━━━━━━━━━━━")
        lines.append(f"🍔 *Food & Drinks:* {total_qty} pcs  |  *{total_rev:,} Ks*")
        for item in items:
            name = item.get("name", "?")
            qty  = item.get("qty", 0)
            val  = item.get("value", 0)
            lines.append(f"  • {name}: {qty} pcs — {val:,} Ks")
        if total_cog > 0:
            lines.append(f"  _{total_cog:,} Ks COGS_  |  GP: *{gross_margin}%*")
    # Low stock alert
    if inv:
        low = [i for i in inv.get("items", []) if 0 < i.get("qty", 0) <= 5]
        out_of_stock = [i for i in inv.get("items", []) if i.get("qty", 0) == 0]
        if low or out_of_stock:
            lines.append(f"━━━━━━━━━━━━━━━━━━")
            lines.append("⚠️ *Low/Out Stock Alert:*")
            for i in out_of_stock:
                name = i.get("name", "?")
                stock_qty = i.get("qty", 0)
                lines.append(f"  🔴 *{name}* — {stock_qty} pcs (Out of Stock)")
            for i in low:
                name = i.get("name", "?")
                stock_qty = i.get("qty", 0)
                lines.append(f"  🟡 *{name}* — {stock_qty} pcs (Low Stock)")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=kb)
    return MAIN_MENU
async def cmd_financial_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick Financial Report: this week's summary + current month P&L."""
    await update.message.reply_text("⏳ Financial report ရယူနေသည်...", reply_markup=ReplyKeyboardRemove())
    kb = ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True)
    # Fetch weekly report and monthly P&L in parallel
    now   = now_mmt()
    m_str = now.strftime("%Y-%m")
    weekly, pnl = await asyncio.gather(
        _psvibe_get_async("sheets/weekly-report"),
        _psvibe_get_async(f"sheets/pnl?m={m_str}"),
    )
    lines: list[str] = [f"💹 <b>Financial Report</b>"]
    # ── Weekly summary ──
    if weekly:
        wm = weekly.get("telegram_message", "")
        if wm:
            lines.append(wm)
        else:
            def _fmt(n): return f"{round(n or 0):,}"
            ws  = weekly.get("week_start", "?")
            we  = weekly.get("week_end",   "?")
            net = weekly.get("net_total",  0)
            lines.append(
                f"📅 <b>This Week</b>  {ws} – {we}\n"
                f"🎮 Sessions : <b>{weekly.get('sessions', 0)}</b>\n"
                f"💰 Net      : <b>{_fmt(net)} Ks</b>\n"
                f"📲 KPay: {_fmt(weekly.get('kpay',0))} Ks  |  💵 Cash: {_fmt(weekly.get('cash',0))} Ks\n"
                f"🏦 Top-Ups  : <b>{_fmt(weekly.get('topup_amt',0))} Ks</b>  ({weekly.get('topup_count',0)} txns)\n"
                f"🆕 New Members: <b>{weekly.get('new_members',0)}</b>"
            )
    else:
        lines.append("📊 Weekly data မရပါ")
    # ── Monthly P&L ──
    if pnl:
        def _f(n): return f"{round(n or 0):,}"
        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append(f"📆 <b>{m_str} — Monthly P&amp;L</b>")
        game_rev   = pnl.get("game_rev",      pnl.get("salesNet",      0))
        food_rev   = pnl.get("food_rev",      pnl.get("foodRev",       0))
        topup_amt  = pnl.get("topup_amount",  pnl.get("topupAmount",   0))
        net_total  = pnl.get("net_total",     pnl.get("salesNet",      0))
        kpay       = pnl.get("kpay",          pnl.get("salesKpay",     0))
        cash       = pnl.get("cash",          pnl.get("salesCash",     0))
        lines.append(
            f"🎮 Game Rev  : <b>{_f(game_rev)} Ks</b>\n"
            f"🍔 Food Rev  : <b>{_f(food_rev)} Ks</b>\n"
            f"🏦 Top-Up    : <b>{_f(topup_amt)} Ks</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💵 Net Total : <b>{_f(net_total)} Ks</b>\n"
            f"📲 KPay: {_f(kpay)} Ks  |  💵 Cash: {_f(cash)} Ks"
        )
    else:
        lines.append("━━━━━━━━━━━━━━━━━━")
        lines.append(f"📆 {m_str} monthly data မရပါ")
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=kb,
    )
    return MAIN_MENU
