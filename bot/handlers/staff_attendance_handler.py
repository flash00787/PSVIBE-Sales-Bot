"""
PS VIBE — Staff Attendance Handler (Check-in/Check-out)
========================================================
Drop-in handler for the PS VIBE Sale Bot.
Add to bot/handlers/ and register in app.py for Telegram command support.

Commands:
  /checkin [staff_id]  — Record check-in
  /checkout [staff_id] — Record check-out
  /attendance [date]   — Show daily attendance
  /salary [staff_id] [start] [end] — Calculate salary
  /staff_status        — Show all staff status
  /staff_list          — List all staff
"""
import requests
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

ATTENDANCE_API = "http://127.0.0.1:3099"

def _api_call(action, params=None):
    """Call the attendance HTTP server."""
    try:
        r = requests.post(f"{ATTENDANCE_API}/{action}", params=params, timeout=5)
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        logger.warning(f"Attendance API call failed ({action}): {e}")
        return None


async def cmd_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /checkin <staff_id>"""
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /checkin <staff_id>\nExample: /checkin 1")
        return
    try:
        staff_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid staff ID. Use numbers only.")
        return
    result = _api_call("checkin", {"staff_id": staff_id})
    if result:
        await update.message.reply_text(result.get("message", "Unknown response"), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ Attendance service unavailable.")


async def cmd_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /checkout <staff_id>"""
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /checkout <staff_id>\nExample: /checkout 1")
        return
    try:
        staff_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid staff ID. Use numbers only.")
        return
    result = _api_call("checkout", {"staff_id": staff_id})
    if result:
        await update.message.reply_text(result.get("message", "Unknown response"), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ Attendance service unavailable.")


async def cmd_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /attendance [date|YYYY-MM-DD]"""
    date_str = context.args[0] if context.args else "today"
    result = _api_call("attendance", {"date": date_str})
    if result:
        await update.message.reply_text(result.get("message", "Unknown response"), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ Attendance service unavailable.")


async def cmd_salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /salary <staff_id> [start_date] [end_date]"""
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /salary <staff_id> [start_date] [end_date]\nExample: /salary 1 2026-06-01 2026-06-30")
        return
    try:
        staff_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid staff ID.")
        return
    params = {"staff_id": staff_id}
    if len(context.args) >= 2:
        params["start_date"] = context.args[1]
    if len(context.args) >= 3:
        params["end_date"] = context.args[2]
    result = _api_call("salary", params)
    if result:
        await update.message.reply_text(result.get("message", "Unknown response"), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ Attendance service unavailable.")


async def cmd_staff_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /staff_status — show all staff current check-in status"""
    result = _api_call("status")  # no staff_id = all
    if not result:
        await update.message.reply_text("❌ Attendance service unavailable.")
        return
    if isinstance(result, dict):
        await update.message.reply_text(result.get("message", "No data"), parse_mode=ParseMode.MARKDOWN)


async def cmd_staff_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /staff_list — list all staff with rates"""
    result = _api_call("staff-list")
    if not result:
        await update.message.reply_text("❌ Attendance service unavailable.")
        return
    staff = result.get("staff", [])
    if not staff:
        await update.message.reply_text("No staff found.")
        return
    lines = ["👥 *Staff List*", "━━━━━━━━━━━━━━━━━━"]
    for s in staff:
        icon = "✅" if s.get("is_active") else "❌"
        lines.append(f"{icon} ID:{s['staff_id']} *{s['staff_name']}* — {int(float(s.get('base_salary', 0))):,} Ks ({float(s.get('hourly_rate', 0)):,.2f}/hr)")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def staff_attendance_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help for staff attendance commands."""
    await update.message.reply_text(
        "📋 *Staff Attendance Commands*\n\n"
        "/checkin `<staff_id>` — Check in\n"
        "/checkout `<staff_id>` — Check out\n"
        "/attendance `[date]` — Daily report\n"
        "/salary `<staff_id>` `[start]` `[end]` — Salary report\n"
        "/staff_status — Current status\n"
        "/staff_list — Staff list",
        parse_mode=ParseMode.MARKDOWN
    )
