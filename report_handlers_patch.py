
# ═══════════════════════════════════════════════════════════════════
#  Phase 3 — Advanced Report Commands
# ═══════════════════════════════════════════════════════════════════

async def cmd_daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send today's sales report (Phase 3 enhanced)."""
    await update.message.reply_text("⏳ Daily report generating...", reply_markup=ReplyKeyboardRemove())
    kb = ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True)

    try:
        from bot.report_generator import get_report_generator
        gen = get_report_generator()
        report = gen.daily_report()
        text = gen.format_daily_report(report)
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=kb,
        )
    except Exception as e:
        logging.exception("cmd_daily_report failed: %s", e)
        await update.message.reply_text(
            f"❌ Report generation failed: {e}",
            reply_markup=kb,
        )
    return MAIN_MENU


async def cmd_weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send this week's trend report."""
    await update.message.reply_text("⏳ Weekly report generating...", reply_markup=ReplyKeyboardRemove())
    kb = ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True)

    try:
        from bot.report_generator import get_report_generator
        gen = get_report_generator()
        report = gen.weekly_report()
        text = gen.format_weekly_report(report)
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=kb,
        )
    except Exception as e:
        logging.exception("cmd_weekly_report failed: %s", e)
        await update.message.reply_text(
            f"❌ Weekly report generation failed: {e}",
            reply_markup=kb,
        )
    return MAIN_MENU


async def cmd_member_insights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send member insights report."""
    await update.message.reply_text("⏳ Member insights loading...", reply_markup=ReplyKeyboardRemove())
    kb = ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True)

    try:
        from bot.report_generator import get_report_generator
        gen = get_report_generator()
        insights = gen.member_insights()
        text = gen.format_member_insights(insights)
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=kb,
        )
    except Exception as e:
        logging.exception("cmd_member_insights failed: %s", e)
        await update.message.reply_text(
            f"❌ Member insights generation failed: {e}",
            reply_markup=kb,
        )
    return MAIN_MENU
