"""PS VIBE Customer Bot (Refactored v3) — Entry Point"""
import sys, os, asyncio, logging, time
from telegram import BotCommand
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, ConversationHandler,
    MessageHandler, filters, CallbackQueryHandler,
)
import sys; sys.path.insert(0, "".join(__file__.split("/")[:-2])); import customer_bot_original as orig

_log = logging.getLogger(__name__)
BOT_TOKEN = os.environ.get('CUSTOMER_BOT_TOKEN', '')
CACHE_TTL_GAMES = int(os.environ.get('CACHE_TTL_GAMES', '300'))
CACHE_TTL_MEMBERS = int(os.environ.get('CACHE_TTL_MEMBERS', '300'))
CACHE_TTL_CONSOLES = int(os.environ.get('CACHE_TTL_CONSOLES', '300'))
CACHE_TTL_CONTACTS = int(os.environ.get('CACHE_TTL_CONTACTS', '600'))
CACHE_TTL_CONFIG = int(os.environ.get('CACHE_TTL_CONFIG', '300'))
CACHE_TTL_PROMOTIONS = int(os.environ.get('CACHE_TTL_PROMOTIONS', '1800'))

def _register_handlers(app):
    app.add_handler(CommandHandler('start', orig.start))
    app.add_handler(CommandHandler('refresh', orig.refresh_cmd))
    app.add_handler(CommandHandler('menu', orig.menu_cmd))
    app.add_handler(CommandHandler('today', orig.today_cmd))
    app.add_handler(CommandHandler('rate', orig.rate_cmd))
    app.add_handler(CommandHandler('myid', orig.myid_cmd))
    app.add_handler(CommandHandler('contact', orig.contact_cmd))
    app.add_handler(CommandHandler('promotions', orig.promotions_cmd))
    app.add_handler(CommandHandler('feedback', orig.feedback_cmd))
    
    bk_conv = ConversationHandler(
        entry_points=[
            CommandHandler('book', orig.bk_start),
            CommandHandler('booking', orig.bk_start),
            MessageHandler(filters.Regex(r'^\U0001f3ae\s*\u101d\u1004\u1039\u1019\u103a\u101c\u1031|\U0001f3ae\s*Book'), orig.bk_start),
        ],
        states={
            orig.BK_MEMBER_CHECK: [CallbackQueryHandler(orig.bk_member_check, pattern=r'^bk_mem:(yes|no|existing)$')],
            orig.BK_MEMBER_SELECT: [CallbackQueryHandler(orig.bk_member_select, pattern=r'^bk_sel:\d+$')],
            orig.BK_PHONE_VERIFY: [MessageHandler(filters.TEXT & ~filters.COMMAND, orig.bk_phone_verify)],
            orig.BK_DATA_CONFIRM: [CallbackQueryHandler(orig.bk_data_confirm, pattern=r'^bk_dc:(yes|no|edit)$')],
            orig.BK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, orig.bk_name)],
            orig.BK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, orig.bk_phone)],
            orig.BK_DATE: [CallbackQueryHandler(orig.bk_date, pattern=r'^bkdate:')],
            orig.BK_TIME: [CallbackQueryHandler(orig.bk_time, pattern=r'^(bktime:|bk_custom:)')],
            orig.BK_CONSOLE: [CallbackQueryHandler(orig.bk_console, pattern=r'^bk_con:')],
            orig.BK_DURATION: [CallbackQueryHandler(orig.bk_duration, pattern=r'^bk_dur:')],
            orig.BK_GAME: [CallbackQueryHandler(orig.bk_game, pattern=r'^bk_game:')],
            orig.BK_CONSOLE_PREF: [CallbackQueryHandler(orig.bk_console_pref, pattern=r'^bk_cp:')],
            orig.BK_CONFIRM: [CallbackQueryHandler(orig.bk_confirm, pattern=r'^bk_ok:')],
            orig.BK_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, orig.bk_end)],
        },
        fallbacks=[CommandHandler('cancel', orig.bk_end)],
    )
    app.add_handler(bk_conv)
    
    app.add_handler(CallbackQueryHandler(orig.cb_booking_action, pattern=r'^bk:(approve|reject|arrived|noshow):\d+$'))
    app.add_handler(CallbackQueryHandler(orig.cb_mybookings_history, pattern=r'^mybk:history$'))
    app.add_handler(CallbackQueryHandler(orig.cb_reschedule_booking, pattern=r'^bkr:\d+$'))
    app.add_handler(CallbackQueryHandler(orig.cb_reschedule_date, pattern=r'^rsd:\d+:[\d-]+$'))
    app.add_handler(CallbackQueryHandler(orig.cb_reschedule_time, pattern=r'^rst:\d+:[\d-]+:\d{2}:\d{2}$'))
    app.add_handler(CallbackQueryHandler(orig.cb_reschedule_custom_time_prompt, pattern=r'^rscustom:\d+:[\d-]+$'))
    app.add_handler(CallbackQueryHandler(orig.cb_reschedule_confirm, pattern=r'^rsok:\d+:[\d-]+:\d{2}:\d{2}$'))
    app.add_handler(CallbackQueryHandler(orig.cb_reschedule_cancel, pattern=r'^rscancel:\d+$'))
    app.add_handler(CallbackQueryHandler(orig.cb_cancel_booking, pattern=r'^bkc:\d+$'))
    app.add_handler(CallbackQueryHandler(orig.cb_cancel_booking_confirm, pattern=r'^cx(ok|no):\d+$'))
    app.add_handler(CallbackQueryHandler(orig.cb_wl_action, pattern=r'^wl:(check|cancel:\d+)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, orig.handle_menu_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, orig.handle_free_text), group=1)

async def error_handler(update, context):
    _log.error('Unhandled error: %s', context.error, exc_info=context.error)
    try:
        if update and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='\u26a0\ufe0f \u1004\u1014\u1039\u1000\u1039\u1018\u102c\u1001\u103b\u102d\u102f\u1004\u1039\u1001\u103b\u102d\u1031\u102c\u1004\u103a\u1000\u1039\u101b\u103e\u1004\u1039\u101e\u1031\u101c\u102c\u1012\u1039 \u1018\u1031\u102c\u1004\u103a \u101e\u1001\u1039\u1001\u103e\u102c\u1014\u1039 \u1005\u102c\u1019\u1031\u102c\u1000\u1039 \u1019\u103b\u102c\u1014\u1039\u1001\u103d\u102c\u101c\u1039 \u1018\u103c\u1014\u1039\u1000\u1039 \u1000\u103c\u102d\u1033\u1018\u1039 \u1000\u103c\u102d\u1033\u101b\u103d\u1000\u1039\u1000\u102d\u102f\u101b\u1039\u1019\u102d\u1000\u1039\u1019\u103b\u102c\u1015\u1031\u101b\u103e\u1000\u1039 \u101e\u100a\u1039 \u1000\u103c\u102d\u1033\u101b\u1039\u1019\u103e\u100a\u1039 \u1019\u103b\u102c\u1014\u1039\u1001\u103d\u102c\u101c\u1039\u1019\u103b\u102c \u1005\u1031\u102c\u1004\u1039\u1000\u103c\u1032\u1000\u103d\u1031\u101b\u1039\u1000\u103c\u1032\u1000\u103d\u1031\u101b\u1039\u1014\u103d\u1031 \u101e\u101c\u102c\u1004\u1039 \u101e\u102d\u102f\u1021\u1031\u102c\u1000\u1039 \u1006\u102f\u1015\u1039\u1000\u103b\u102c\u101c\u1039 \u1000\u103c\u102d\u1033\u101b\u1039\u1014\u103d\u1031\u1015\u1032 \u1018\u1031\u101c \u101e\u1031\u102c\u1004\u1039\u1000\u103c\u1032\u1000\u103d\u1031\u101b\u1039\u1000\u103c\u1032\u1000\u103d\u1031\u101b\u1039\u1014\u103d\u1031\u1014\u103d\u1031\u1014\u103d\u1031',
            )
    except Exception:
        pass

def main():
    if not BOT_TOKEN:
        _log.error('CUSTOMER_BOT_TOKEN not set')
        return
    
    orig._CACHE_TTL = {
        'games': CACHE_TTL_GAMES, 'members': CACHE_TTL_MEMBERS,
        'consoles': CACHE_TTL_CONSOLES, 'contacts': CACHE_TTL_CONTACTS,
        'config': CACHE_TTL_CONFIG, 'promotions': CACHE_TTL_PROMOTIONS,
    }
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_error_handler(error_handler)
    _register_handlers(app)
    
    _log.info('Customer bot (refactored v3) starting polling...')
    app.run_polling(drop_pending_updates=True)

def run():
    while True:
        try:
            asyncio.set_event_loop(asyncio.new_event_loop())
            main()
        except KeyboardInterrupt:
            break
        except Exception as exc:
            _log.error('Crash: %s — restart 5s', exc, exc_info=True)
            time.sleep(5)

if __name__ == '__main__':
    run()
