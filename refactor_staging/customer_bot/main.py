"""
PS Vibe Customer Bot — Entry point (refactored v3.0).

Application setup, handler registration, main() and run() with crash recovery.
Replaces the old inline-ifmain block from customer_bot.py.
"""
import asyncio
import logging
import os
import signal
import time

from telegram import BotCommand
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, ConversationHandler,
    MessageHandler, filters, CallbackQueryHandler,
)

from . import api as _api
from . import ai as _ai
from .handlers import (
    BUFFER_GLOBAL_WAIT,
    # Conversation states
    BK_MEMBER_CHECK, BK_MEMBER_SELECT, BK_PHONE_VERIFY, BK_DATA_CONFIRM,
    BK_NAME, BK_PHONE, BK_DATE, BK_TIME, BK_CONSOLE, BK_DURATION,
    BK_GAME, BK_CONSOLE_PREF, BK_CONFIRM, BK_END,
    # Handlers
    start, refresh_cmd, menu_cmd, today_cmd, rate_cmd, myid_cmd,
    contact_cmd, promotions_cmd, feedback_cmd,
    handle_menu_buttons, handle_free_text,
    # Booking conv handlers
    bk_start, bk_member_check, bk_member_select, bk_phone_verify,
    bk_phone_unknown, bk_data_confirm, bk_name, bk_phone, bk_date,
    bk_time, bk_console, bk_duration, bk_game, bk_console_pref,
    bk_confirm, bk_end,
    cb_booking_action, cb_mybookings_history,
    cb_reschedule_booking, cb_reschedule_date, cb_reschedule_time,
    cb_reschedule_custom_time_prompt, cb_reschedule_confirm,
    cb_reschedule_cancel, cb_cancel_booking, cb_cancel_booking_confirm,
    cb_wl_action,
)

_log = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("CUSTOMER_BOT_TOKEN", "")
_GLOBALS_INJECTED = False


def _inject_globals() -> None:
    """Inject runtime globals into api module before first handler fires."""
    global _GLOBALS_INJECTED
    if _GLOBALS_INJECTED:
        return
    _api.BOT_TOKEN = BOT_TOKEN
    _api._CACHE_TTL = {
        "games": int(os.environ.get("CACHE_TTL_GAMES", "300")),
        "members": int(os.environ.get("CACHE_TTL_MEMBERS", "300")),
        "consoles": int(os.environ.get("CACHE_TTL_CONSOLES", "300")),
        "contacts": int(os.environ.get("CACHE_TTL_CONTACTS", "600")),
        "config": int(os.environ.get("CACHE_TTL_CONFIG", "300")),
        "promotions": int(os.environ.get("CACHE_TTL_PROMOTIONS", "1800")),
    }
    _GLOBALS_INJECTED = True


def _register_handlers(app: Application) -> None:
    """Register all command and conversation handlers."""

    # ── Simple commands ─────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("refresh", refresh_cmd))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("today", today_cmd))
    app.add_handler(CommandHandler("rate", rate_cmd))
    app.add_handler(CommandHandler("myid", myid_cmd))
    app.add_handler(CommandHandler("contact", contact_cmd))
    app.add_handler(CommandHandler("promotions", promotions_cmd))
    app.add_handler(CommandHandler("feedback", feedback_cmd))

    # ── Booking conversation ────────────────────────────────────────────
    bk_conv = ConversationHandler(
        entry_points=[
            CommandHandler("book", bk_start),
            CommandHandler("booking", bk_start),
            MessageHandler(filters.Regex(r"^🎮\s*ဝင်မယ်လေ|🎮\s*Book"), bk_start),
        ],
        states={
            BK_MEMBER_CHECK:  [CallbackQueryHandler(bk_member_check,  pattern=r"^bk_mem:(yes|no|existing)$")],
            BK_MEMBER_SELECT: [CallbackQueryHandler(bk_member_select, pattern=r"^bk_sel:\d+$")],
            BK_PHONE_VERIFY:  [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_phone_verify)],
            BK_DATA_CONFIRM:  [CallbackQueryHandler(bk_data_confirm,  pattern=r"^bk_dc:(yes|no|edit)$")],
            BK_NAME:          [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_name)],
            BK_PHONE:         [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_phone)],
            BK_DATE:          [CallbackQueryHandler(bk_date,           pattern=r"^bkdate:")],
            BK_TIME:          [CallbackQueryHandler(bk_time,           pattern=r"^(bktime:|bk_custom:)")],
            BK_CONSOLE:       [CallbackQueryHandler(bk_console,        pattern=r"^bk_con:")],
            BK_DURATION:      [CallbackQueryHandler(bk_duration,       pattern=r"^bk_dur:")],
            BK_GAME:          [CallbackQueryHandler(bk_game,           pattern=r"^bk_game:")],
            BK_CONSOLE_PREF:  [CallbackQueryHandler(bk_console_pref,   pattern=r"^bk_cp:")],
            BK_CONFIRM:       [CallbackQueryHandler(bk_confirm,        pattern=r"^bk_ok:")],
            BK_END:           [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_end)],
        },
        fallbacks=[
            CommandHandler("cancel", bk_end),
            MessageHandler(filters.Regex(r"^(cancel|cancel|cancel_book)$"), bk_end),
        ],
    )
    app.add_handler(bk_conv)

    # ── Callback handlers (no state) ────────────────────────────────────
    app.add_handler(CallbackQueryHandler(cb_booking_action,     pattern=r"^bk:(approve|reject|arrived|noshow):\d+$"))
    app.add_handler(CallbackQueryHandler(cb_mybookings_history, pattern=r"^mybk:history$"))
    app.add_handler(CallbackQueryHandler(cb_reschedule_booking, pattern=r"^bkr:\d+$"))
    app.add_handler(CallbackQueryHandler(cb_reschedule_date,    pattern=r"^rsd:\d+:[\d-]+$"))
    app.add_handler(CallbackQueryHandler(cb_reschedule_time,    pattern=r"^rst:\d+:[\d-]+:\d{2}:\d{2}$"))
    app.add_handler(CallbackQueryHandler(cb_reschedule_custom_time_prompt, pattern=r"^rscustom:\d+:[\d-]+$"))
    app.add_handler(CallbackQueryHandler(cb_reschedule_confirm, pattern=r"^rsok:\d+:[\d-]+:\d{2}:\d{2}$"))
    app.add_handler(CallbackQueryHandler(cb_reschedule_cancel,  pattern=r"^rscancel:\d+$"))
    app.add_handler(CallbackQueryHandler(cb_cancel_booking,     pattern=r"^bkc:\d+$"))
    app.add_handler(CallbackQueryHandler(cb_cancel_booking_confirm, pattern=r"^cx(ok|no):\d+$"))
    app.add_handler(CallbackQueryHandler(cb_wl_action,          pattern=r"^wl:(check|cancel:\d+)$"))

    # ── Catch-all: menu buttons + free-text ──────────────────────────────
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_buttons))

    # ── Free-text handler (Gemini AI) ───────────────────────────────────
    # Registered as a low-priority fallback
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_free_text), group=1)


async def _post_init(app: Application) -> None:
    """Post-init hook: set bot commands."""
    _inject_globals()
    await app.bot.set_my_commands([
        BotCommand("start",    "Restart the bot"),
        BotCommand("menu",     "View PS VIBE menu"),
        BotCommand("book",     "Book a console"),
        BotCommand("today",    "Today's bookings"),
        BotCommand("rate",     "Rate & pricing"),
        BotCommand("myid",     "Your member info"),
        BotCommand("contact",  "Contact PS VIBE"),
        BotCommand("promotions", "Current promotions"),
        BotCommand("feedback", "Send feedback"),
        BotCommand("refresh",  "Refresh data"),
    ])


async def _error_handler(update, context) -> None:
    """Global error handler — logs and recovers gracefully."""
    _log.error("Unhandled error: %s", context.error, exc_info=context.error)
    try:
        if update and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ နည်းပညာချို့ယွင်းချက်တစ်ခုရှိသွားပါတယ်။ ခဏလေးစောင့်ပြီးမှ ပြန်ကြိုးစားကြည့်ပါ။ 🙏",
            )
    except Exception:
        pass


def main() -> None:
    """Main entry point — build app, register handlers, start polling."""
    if not BOT_TOKEN:
        _log.critical("CUSTOMER_BOT_TOKEN not set!")
        return

    _inject_globals()

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    app.add_error_handler(_error_handler)
    _register_handlers(app)

    _log.info("Customer bot (refactored v3.0) starting polling...")
    app.run_polling(drop_pending_updates=True)


def run() -> None:
    """Run main() with infinite crash recovery loop."""
    while True:
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            main()
        except KeyboardInterrupt:
            _log.info("Shutdown by KeyboardInterrupt")
            break
        except Exception as exc:
            _log.error("Customer bot crashed: %s — restart in 5s", exc, exc_info=True)
            time.sleep(5)


if __name__ == "__main__":
    run()
