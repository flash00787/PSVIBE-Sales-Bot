#!/usr/bin/env python3
"""PS VIBE Customer Bot — Clean V2 Entry Point.
Refactored from _v1_compat.py (removed 2026-05-28).
Booking conversation handlers need to be migrated from _v1_compat.py backup.
"""
import asyncio
import logging
import os
import signal
import sys
import time

# Ensure parent dir + customer_bot dir are on path for imports
_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_pkg_dir)
for _d in (_pkg_dir, _parent_dir):
    if _d not in sys.path:
        sys.path.insert(0, _d)

from telegram import BotCommand
from telegram.error import Conflict
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, ConversationHandler,
    MessageHandler, filters, CallbackQueryHandler,
)

from customer_bot.handlers import (
    BK_MEMBER_CHECK, BK_MEMBER_SELECT, BK_PHONE_VERIFY, BK_DATA_CONFIRM,
    BK_NAME, BK_PHONE, BK_DATE, BK_TIME,
    BK_CONSOLE, BK_DURATION, BK_GAME, BK_CONSOLE_PREF, BK_CONFIRM,
    BK_DUP_WARN, BK_DISC_WARN, BK_CON_CONFLICT, BK_END,
    cmd_start, cmd_menu, cmd_today, cmd_rate, cmd_myid,
    cmd_contact, cmd_promotions, cmd_help, cmd_refresh,
    cmd_balance, cmd_game_library, cmd_console_status, cmd_location,
    cmd_book, cmd_cancel, cmd_feedback, cmd_mybookings, cmd_refer, cmd_waitlist,
    cb_feedback_rating, cb_feedback_comment_prompt, cb_feedback_skip,
    handle_menu_buttons, show_main_menu,
)
from customer_bot.booking_handlers import (
    bk_member_check_entry, bk_member_select, bk_phone_verify, bk_data_confirm,
    bk_name_entry, bk_phone_entry, bk_date_select, bk_time_select,
    bk_console_select, bk_duration_select, bk_game_select, bk_console_pref,
    bk_confirm, bk_dup_warn, bk_disc_warn, bk_con_conflict, bk_end_handler,
    bk_time_text_input,
)

_log = logging.getLogger(__name__)
BOT_TOKEN = os.environ.get("CUSTOMER_BOT_TOKEN", "")


def _register_handlers(app: Application) -> None:
    """Register all command and callback handlers."""

    # Simple commands
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("menu",   cmd_menu))
    app.add_handler(CommandHandler("today",  cmd_today))
    app.add_handler(CommandHandler("rate",   cmd_rate))
    app.add_handler(CommandHandler("myid",   cmd_myid))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("contact",cmd_contact))
    app.add_handler(CommandHandler("location",cmd_location))
    app.add_handler(CommandHandler("promotions",cmd_promotions))
    app.add_handler(CommandHandler("refresh",cmd_refresh))
    app.add_handler(CommandHandler("balance",cmd_balance))
    app.add_handler(CommandHandler("games",  cmd_game_library))
    app.add_handler(CommandHandler("status", cmd_console_status))
        # /book and /booking handled by ConversationHandler below
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("feedback",cmd_feedback))
    app.add_handler(CommandHandler("mybookings",cmd_mybookings))
    app.add_handler(CommandHandler("refer",  cmd_refer))
    app.add_handler(CommandHandler("waitlist",cmd_waitlist))

    # Booking conversation — V2 handler stubs (TODO: migrate from _v1_compat backup)
    bk_conv = ConversationHandler(
        entry_points=[
            CommandHandler("book", cmd_book),
            CommandHandler("booking", cmd_book),
        ],
        states={
            BK_MEMBER_CHECK:  [CallbackQueryHandler(bk_member_check_entry, pattern=r"^bk_mem:")],
            BK_MEMBER_SELECT: [CallbackQueryHandler(bk_member_select, pattern=r"^bk_sel:")],
            BK_PHONE_VERIFY:  [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_phone_verify)],
            BK_DATA_CONFIRM:  [CallbackQueryHandler(bk_data_confirm, pattern=r"^bk_dc:")],
            BK_NAME:          [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_name_entry)],
            BK_PHONE:         [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_phone_entry)],
            BK_DATE:          [CallbackQueryHandler(bk_date_select, pattern=r"^bkdate:")],
            BK_TIME:          [
                CallbackQueryHandler(bk_time_select, pattern=r"^(bktime:|bk_custom:)"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bk_time_text_input),
            ],
            BK_CONSOLE:       [CallbackQueryHandler(bk_console_select, pattern=r"^bk_con:")],
            BK_DURATION:      [CallbackQueryHandler(bk_duration_select, pattern=r"^bk_dur:")],
            BK_GAME:          [CallbackQueryHandler(bk_game_select, pattern=r"^bk_game:")],
            BK_CONSOLE_PREF:  [CallbackQueryHandler(bk_console_pref, pattern=r"^bk_con:")],
            BK_CONFIRM:       [CallbackQueryHandler(bk_confirm, pattern=r"^bk_ok:")],
            BK_DUP_WARN:      [CallbackQueryHandler(bk_dup_warn, pattern=r"^(bk_warn:|bk_ok:)")],
            BK_DISC_WARN:     [CallbackQueryHandler(bk_disc_warn, pattern=r"^(bk_warn:|bk_ok:)")],
            BK_CON_CONFLICT:  [CallbackQueryHandler(bk_con_conflict, pattern=r"^(bk_warn:|bk_ok:)")],
            BK_END:           [MessageHandler(filters.TEXT & ~filters.COMMAND, bk_end_handler)],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        per_message=True,
    )
    app.add_handler(bk_conv)

    # Feedback callbacks
    app.add_handler(CallbackQueryHandler(cb_feedback_rating,         pattern=r"^fb:\d+:"))
    app.add_handler(CallbackQueryHandler(cb_feedback_comment_prompt, pattern=r"^fbc:"))
    app.add_handler(CallbackQueryHandler(cb_feedback_skip,           pattern=r"^fbskip$"))

    # Menu buttons catch-all
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_buttons))


async def _post_init(app: Application) -> None:
    """Set bot commands."""
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
    """Global error handler - 409 Conflict handled gracefully."""
    err = context.error
    if isinstance(err, Conflict):
        _log.warning("409 Conflict: another instance polling - will resolve automatically")
        return
    _log.error("Unhandled error: %s", err, exc_info=err)
    try:
        if update and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Technical error. Please try again later. ",
            )
    except Exception:
        pass


def main() -> None:
    """Build app, register handlers, start polling."""
    if not BOT_TOKEN:
        _log.critical("CUSTOMER_BOT_TOKEN not set!")
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    app.add_error_handler(_error_handler)
    _register_handlers(app)

    _log.info("Customer bot (clean V2) starting polling...")
    app.run_polling(drop_pending_updates=True)


def run() -> None:
    """Run with crash recovery."""
    while True:
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            main()
        except KeyboardInterrupt:
            _log.info("Shutdown by KeyboardInterrupt")
            break
        except Conflict as exc:
            _log.warning("409 Conflict in polling: %s - will retry in 3s", exc)
            time.sleep(3)
        except Exception as exc:
            _log.error("Customer bot crashed: %s — restart in 5s", exc, exc_info=True)
            time.sleep(5)


if __name__ == "__main__":
    run()
