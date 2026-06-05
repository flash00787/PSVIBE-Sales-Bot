from bot import (
    ACCT_TRF_AMT, ACCT_TRF_CONFIRM, ACCT_TRF_FROM, ACCT_TRF_NOTE,
    ACCT_TRF_TO, ADJUST_TIME, ADMIN_MENU, ADMIN_PIN, ADVPAY_ACCT,
    ADVPAY_AMT, ADVPAY_CONFIRM, ADVPAY_DESC, ADVPAY_DUE, ADVPAY_LIST,
    ADVPAY_NOTE, ADVPAY_PARTY, ADVPAY_SETTLE_CONFIRM, ASSET_CAT,
    ASSET_CONFIRM, ASSET_COST, ASSET_DATE, ASSET_DISPOSE_CONFIRM,
    ASSET_DISPOSE_DATE, ASSET_DISPOSE_PROCEEDS, ASSET_DISPOSE_QTY,
    ASSET_DISPOSE_SEL, ASSET_LIFE, ASSET_NAME, ASSET_PAY, ASSET_QTY,
    ASSET_SALVAGE, ATTEND_DEDUCT, ATTEND_LATE, ATTEND_LEAVE,
    ATTEND_STAFF, BOOK_CONSOLE, BOOK_DUP_WARN, BOOK_GAME, BOOK_LINK,
    BOOK_MEMBER, BOOK_MINS, BUNDLE_FOC, CAP_ACCT, CAP_AMT, CAP_CONFIRM,
    CONFIRM_SUMMARY, CONSOLE, CONSOLE_MENU, CON_ADD_ID, CON_ADD_MULT,
    CON_ADD_TYPE, CON_DEL_SELECT, CON_EDIT_MULT_SELECT, CON_EDIT_MULT_VALUE, CON_MGMT_MENU, DISCOUNT, DISC_SELECT,
    DISC_SET_QTY, DS_CONSOLE_IN_SESSION, DS_MEMBER_IN_SESSION,
    END_SESSION_SELECT, FINANCE_MENU, FIN_REPORT_MENU, FOOD_MENU,
    FOOD_QTY, GAME_ADD_GENRE, GAME_ADD_PLATFORM, GAME_ADD_STATUS,
    GAME_ADD_TITLE, GAME_DEL_SELECT,
    GAME_EDIT_FIELD, GAME_EDIT_SELECT, GAME_EDIT_VALUE, GAME_DETAIL_PICK, GAME_MENU,
    GINST_ADD_CONS, GINST_ADD_GAME, GINST_ADD_TYPE, GINST_DEL_CONS,
    GINST_DEL_GAME, GINST_MENU, GINST_VIEW_CONS, KPAY_AMT, MAIN_MENU,
    MEMBER, MINS, MM_LOOKUP, MM_MENU, NM_AMT, NM_CONFIRM, NM_EMAIL,
    NM_GIFT_PIN, NM_ID, NM_KPAY, NM_NAME, NM_PHONE, NM_REFERRAL,
    OPEX_ACCT, OPEX_AMT, OPEX_CAT, OPEX_CONFIRM, OPEX_DESC, OPEX_PAY,
    PAY_ACCT, PAY_AMOUNT, PAY_AMT, PAY_CONFIRM, PAY_DESC, PAY_DUE,
    PAY_METHOD, PAY_SETTLE_ACCT, PAY_SETTLE_CONFIRM, PAY_SETTLE_LIST,
    PAY_VENDOR, PREPAID_ACCT, PREPAID_AMT, PREPAID_CAT, PREPAID_CONFIRM,
    PREPAID_DESC, PREPAID_END, PREPAID_START, PROMO_SELECT, REC_ACCT,
    REC_AMT, REC_CONFIRM, REC_CUST, REC_DESC, REC_DUE, REC_SETTLE_ACCT,
    REC_SETTLE_CONFIRM, REC_SETTLE_LIST, REFERRAL_CODE, SALE_CONFIRM,
    SALE_GAME_SELECT,
    SAL_ADV_AMT, SAL_ADV_CONFIRM, SAL_ADV_PAY, SAL_ADV_STAFF,
    SBK_CONFIRM, SBK_CONSOLE, SBK_CUST_NAME, SBK_DATE, SBK_DUR, SBK_GAME,
    SBK_TIME, SESSION_SHORTFALL, SHARE_CAP, SHARE_CONFIRM, SHARE_NAME,
    SHARE_OWN, SHARE_ROLE, SI_CART, SI_CONFIRM, SI_COST, SI_ITEM, SI_PAY,
    SI_PAY_SPLIT, SI_QTY, SSD_ADD_GAME, SSD_ADD_SSD, SSD_ADD_TYPE,
    SSD_DEL_GAME, SSD_DEL_SSD, SSD_MENU, SSD_RET_CONS, SSD_RET_GAME,
    SSD_MOVE_SSD, SSD_MOVE_GAME, SSD_MOVE_CONS, SSD_MOVE_FROM_CONS,
    SSD_MOVE_FROM_GAME, SSD_MOVE_TO_SSD,
    SSD_VIEW_SSD, SSD_XFER_CONS, SSD_XFER_GAME, SSD_XFER_SSD, STOCK_ITEM,
    STOCK_MENU, STOCK_PIN, STOCK_QTY, TU_AMT, TU_CONFIRM, TU_KPAY,
    TU_MEMBER, WL_MENU, _bg_cache_refresh, _get_cfg, _get_member_rows,
    _load_cfg, _load_members, fetch_allowed_staff_ids,
    fetch_allowed_staff_ids_async,
)

# app.py imports
import os
import sys
import asyncio
import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    TypeHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ApplicationHandlerStop,
    ContextTypes,
)
import bot
from bot.handlers import *  # noqa: F401,F403
from bot.handlers import error_handler
from bot.handlers.input_logger import input_logger, input_logger_batcher
import bot as _bot_module

async def _auth_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Block all updates from users not in the staff whitelist (loaded from Google Sheets)."""
    user = update.effective_user
    allowed = await fetch_allowed_staff_ids_async()
    if user and user.id in allowed:
        return  # authorized — let the update pass through
    # Unauthorized — send a single rejection message and swallow the update
    if update.message:
        await update.message.reply_text(
            "\U0001f6ab *Access Denied*\n"
            "ဒီ bot ကို authorized staff တွေသာ သုံးနိုင်ပါတယ်။",
            parse_mode="Markdown",
        )
    elif update.callback_query:
        await update.callback_query.answer(
            "\u26d4 Access Denied — authorized staff only.", show_alert=True
        )
    # Raise ApplicationHandlerStop to prevent any further handlers from running
    raise ApplicationHandlerStop

def main():
    app = (
        Application.builder()
        .token(os.environ["BOT_TOKEN"])
        .get_updates_read_timeout(30)
        .get_updates_write_timeout(30)
        .get_updates_connect_timeout(30)
        .get_updates_pool_timeout(30)
        .build()
    )
    app.add_error_handler(error_handler)

    # Register global auth middleware — group=-999 runs before all other handlers
    app.add_handler(TypeHandler(Update, _auth_middleware), group=-999)

    # Register input logger — group=-998 logs all inputs after auth
    app.add_handler(TypeHandler(Update, input_logger), group=-998)

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start",      show_main_menu),
            CommandHandler("menu",       show_main_menu),
            CommandHandler("cancel",     cmd_cancel),
            CommandHandler("help",       cmd_help),
            CommandHandler("version",    cmd_version),
            # Sales
            CommandHandler("sales",      cmd_sales_direct),
            # Members
            CommandHandler("member",     cmd_member_mgmt),
            CommandHandler("newmember",  cmd_newmember),
            CommandHandler("topup",      cmd_topup),
            CommandHandler("check",      cmd_check_member),
            CommandHandler("ranks",      cmd_ranks),
            # Reports
            CommandHandler("report",     cmd_today_report),
            CommandHandler("freport",    cmd_financial_report),
            CommandHandler("broadcast",  cmd_broadcast),
            CommandHandler("kpi",        cmd_kpi_cmd),
            CommandHandler("payroll",    cmd_payroll_cmd),
            CommandHandler("setattend",  cmd_setattend_cmd),
            CommandHandler("admin",      cmd_admin),
            # Booking management
            CommandHandler("bookings",   cmd_admin_bookings),
            CommandHandler("waitlist",   cmd_waitlist_mgmt),
            CommandHandler("newbooking", cmd_staff_booking),
            MessageHandler(filters.Regex(r"^/approve_\d+$"), cmd_approve_booking),
            CommandHandler("approve", cmd_approve_booking),
            MessageHandler(filters.Regex(r"^/reject_\d+$"),  cmd_reject_booking),
            CommandHandler("reject", cmd_reject_booking),
            # Stock
            CommandHandler("stock",      cmd_stock_menu),
            CommandHandler("stockin",    cmd_stockin_direct),
            CommandHandler("stockout",   cmd_stockout_direct),
            CommandHandler("inventory",  cmd_inventory),
            CommandHandler("stocktoday", cmd_stocktoday),
            # Console
            CommandHandler("console",    cmd_console_status),
        ],
        states={
            # ── Main Menu ──
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_main_menu)],

            # ── Member Management sub-menu ──
            MM_MENU:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_mm_menu)],
            MM_LOOKUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_mm_lookup)],

            # ── First Purchase flow ──
            NM_NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_nm_name)],
            NM_PHONE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_nm_phone)],
            NM_EMAIL:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_nm_email)],
            NM_ID:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_nm_id)],
            NM_AMT:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_nm_amt)],
            NM_GIFT_PIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_nm_gift_pin)],
            NM_KPAY:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_nm_kpay)],
            NM_REFERRAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_nm_referral)],
            NM_CONFIRM:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_nm_confirm)],

            # ── Top Up flow ──
            TU_MEMBER:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_tu_member)],
            TU_AMT:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_tu_amt)],
            TU_KPAY:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_tu_kpay)],
            TU_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_tu_confirm)],

            # ── Daily Sales flow ──
            MEMBER:          [MessageHandler(filters.TEXT & ~filters.COMMAND, step_member)],
            CONSOLE:         [MessageHandler(filters.TEXT & ~filters.COMMAND, step_console)],
            MINS:            [MessageHandler(filters.TEXT & ~filters.COMMAND, step_mins)],
            SALE_GAME_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_game_select)],

            ADJUST_TIME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_adjust_time)],
            FOOD_MENU:       [MessageHandler(filters.TEXT & ~filters.COMMAND, step_food_menu)],
            FOOD_QTY:        [MessageHandler(filters.TEXT & ~filters.COMMAND, step_food_qty)],
            CONFIRM_SUMMARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_confirm)],
            KPAY_AMT:        [MessageHandler(filters.TEXT & ~filters.COMMAND, step_kpay)],
            # ── Multi-Payment (NEW) ──
            PAY_METHOD:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_pay_method)],
            PAY_AMOUNT:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_pay_amount)],
            SALE_CONFIRM:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_sale_confirm)],

            # ── Stock PIN entry ──
            STOCK_PIN:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_stock_pin)],
            # ── Stock sub-menu ──
            STOCK_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_stock_menu)],

            # ── Stock Out flow ──
            STOCK_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_stock_item)],
            STOCK_QTY:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_stock_qty)],

            # ── Stock In (Restock) flow ──
            SI_ITEM:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_si_item)],
            SI_QTY:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_si_qty)],
            SI_COST:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_si_cost)],
            SI_CART:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_si_cart)],
            SI_PAY:       [MessageHandler(filters.TEXT & ~filters.COMMAND, step_si_pay)],
            SI_PAY_SPLIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_si_pay_split)],
            SI_CONFIRM:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_si_confirm)],

            # ── Discount step ──
            DISCOUNT:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_discount)],
            COUPON_APPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_coupon_validate)],
            COUPON_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_coupon_confirm)],
            PROMO_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_promo_select)],
            BUNDLE_FOC:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_bundle_foc)],

            # ── Attendance wizard ──
            ATTEND_STAFF:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_attend_staff)],
            ATTEND_LEAVE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_attend_leave)],
            ATTEND_LATE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_attend_late)],
            ATTEND_DEDUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_attend_deduct)],

            # ── Admin Panel ──
            ADMIN_PIN:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_admin_pin)],
            ADMIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_admin_menu)],

            # ── Waitlist Management ──
            WL_MENU:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_wl_menu)],
            # ── Salary Advance flow ──
            SAL_ADV_STAFF:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_sal_adv_staff)],
            SAL_ADV_AMT:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_sal_adv_amt)],
            SAL_ADV_PAY:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_sal_adv_pay)],
            SAL_ADV_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_sal_adv_confirm)],

            # ── Console Booking flow ──
            BOOK_LINK:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_book_link)],
            BOOK_CONSOLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_book_console)],
            BOOK_MEMBER:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_book_member)],

            # ── Console Management submenu ──
            CONSOLE_MENU:       [MessageHandler(filters.TEXT & ~filters.COMMAND, step_console_menu)],

            # ── End Session flow ──
            END_SESSION_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_end_session)],

            # ── Game Library flows ──
            GAME_MENU:          [MessageHandler(filters.TEXT & ~filters.COMMAND, step_game_menu)],
            GAME_ADD_TITLE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_game_add_title)],
            GAME_ADD_PLATFORM:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_game_add_platform)],
            GAME_ADD_GENRE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_game_add_genre)],
            GAME_ADD_STATUS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_game_add_status)],
            GAME_DEL_SELECT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_game_del_select)],
            GAME_DETAIL_PICK:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_game_detail_pick)],
            # ── Game Edit flow ──
            GAME_EDIT_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_game_edit_select)],
            GAME_EDIT_FIELD:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_game_edit_field)],
            GAME_EDIT_VALUE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_game_edit_value)],
            # ── Game Discs Record ──
            DISC_SELECT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_disc_select)],
            DISC_SET_QTY:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_disc_set_qty)],
            # ── Console-Game Install flows ──
            GINST_MENU:         [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ginst_menu)],
            GINST_VIEW_CONS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ginst_view_cons)],
            GINST_ADD_CONS:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ginst_add_cons)],
            GINST_ADD_GAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ginst_add_game)],
            GINST_ADD_TYPE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ginst_add_type)],
            GINST_DEL_CONS:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ginst_del_cons)],
            GINST_DEL_GAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ginst_del_game)],
            # ── External SSD Management flows ──
            SSD_MENU:       [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_menu)],
            SSD_VIEW_SSD:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_view)],
            SSD_ADD_SSD:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_add_ssd)],
            SSD_ADD_GAME:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_add_game)],
            SSD_ADD_TYPE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_add_type)],
            SSD_DEL_SSD:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_del_ssd)],
            SSD_DEL_GAME:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_del_game)],
            SSD_XFER_SSD:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_xfer_ssd)],
            SSD_XFER_GAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_xfer_game)],
            SSD_XFER_CONS:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_xfer_cons)],
            SSD_RET_CONS:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_ret_cons)],
            SSD_RET_GAME:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_ret_game)],
            # ── SSD Move flows ──
            SSD_MOVE_SSD:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_move_ssd)],
            SSD_MOVE_GAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_move_game)],
            SSD_MOVE_CONS:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_move_cons)],
            SSD_MOVE_FROM_CONS:[MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_move_from_cons)],
            SSD_MOVE_FROM_GAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_move_from_game)],
            SSD_MOVE_TO_SSD:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ssd_move_to_ssd)],

            # ── Console CRUD flows ──
            CON_MGMT_MENU:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_con_mgmt_menu)],
            CON_ADD_ID:         [MessageHandler(filters.TEXT & ~filters.COMMAND, step_con_add_id)],
            CON_ADD_TYPE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, step_con_add_type)],
            CON_ADD_MULT:       [MessageHandler(filters.TEXT & ~filters.COMMAND, step_con_add_mult)],
            CON_DEL_SELECT:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_con_del_select)],
            CON_EDIT_MULT_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_con_edit_mult_select)],
            CON_EDIT_MULT_VALUE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_con_edit_mult_value)],

            # ── Session → Daily Sales bridge ──
            SESSION_SHORTFALL:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_session_shortfall)],
            # ── Daily Sales in-session conflict checks ──
            DS_MEMBER_IN_SESSION:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ds_member_in_session)],
            DS_CONSOLE_IN_SESSION:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_ds_console_in_session)],
            # ── Booking duplicate-session warning ──
            BOOK_DUP_WARN:          [MessageHandler(filters.TEXT & ~filters.COMMAND, step_book_dup_warn)],
            # ── Booking game selection ──
            BOOK_GAME:              [MessageHandler(filters.TEXT & ~filters.COMMAND, step_book_game)],
            # ── Booking planned duration / timer ──
            BOOK_MINS:              [MessageHandler(filters.TEXT & ~filters.COMMAND, step_book_mins)],
            # ── Game change for active session ──

            # ── Staff Advance Booking flow ──
            SBK_CONSOLE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_sbk_console)],
            SBK_CUST_NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, step_sbk_cust_name)],
            SBK_DATE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_sbk_date)],
            SBK_TIME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_sbk_time)],
            SBK_DUR:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_sbk_dur)],
            SBK_GAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_sbk_game)],
            SBK_CONFIRM:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_sbk_confirm)],

            # ── Finance module ──
            FINANCE_MENU:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_finance_menu)],
            OPEX_CAT:          [MessageHandler(filters.TEXT & ~filters.COMMAND, step_opex_cat)],
            OPEX_DESC:         [MessageHandler(filters.TEXT & ~filters.COMMAND, step_opex_desc)],
            OPEX_AMT:          [MessageHandler(filters.TEXT & ~filters.COMMAND, step_opex_amt)],
            OPEX_ACCT:         [MessageHandler(filters.TEXT & ~filters.COMMAND, step_opex_acct)],
            OPEX_PAY:          [MessageHandler(filters.TEXT & ~filters.COMMAND, step_opex_pay)],
            OPEX_CONFIRM:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_opex_confirm)],
            ASSET_NAME:            [MessageHandler(filters.TEXT & ~filters.COMMAND, step_asset_name)],
            ASSET_CAT:             [MessageHandler(filters.TEXT & ~filters.COMMAND, step_asset_cat)],
            ASSET_DATE:            [MessageHandler(filters.TEXT & ~filters.COMMAND, step_asset_date)],
            ASSET_COST:            [MessageHandler(filters.TEXT & ~filters.COMMAND, step_asset_cost)],
            ASSET_QTY:             [MessageHandler(filters.TEXT & ~filters.COMMAND, step_asset_qty)],
            ASSET_LIFE:            [MessageHandler(filters.TEXT & ~filters.COMMAND, step_asset_life)],
            ASSET_SALVAGE:         [MessageHandler(filters.TEXT & ~filters.COMMAND, step_asset_salvage)],
            ASSET_PAY:             [MessageHandler(filters.TEXT & ~filters.COMMAND, step_asset_pay)],
            ASSET_CONFIRM:         [MessageHandler(filters.TEXT & ~filters.COMMAND, step_asset_confirm)],
            ASSET_DISPOSE_SEL:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_asset_dispose_sel)],
            ASSET_DISPOSE_DATE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, step_asset_dispose_date)],
            ASSET_DISPOSE_QTY:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_asset_dispose_qty)],
            ASSET_DISPOSE_PROCEEDS:[MessageHandler(filters.TEXT & ~filters.COMMAND, step_asset_dispose_proceeds)],
            ASSET_DISPOSE_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_asset_dispose_confirm)],
            PREPAID_DESC:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_prepaid_desc)],
            PREPAID_CAT:       [MessageHandler(filters.TEXT & ~filters.COMMAND, step_prepaid_cat)],
            PREPAID_AMT:       [MessageHandler(filters.TEXT & ~filters.COMMAND, step_prepaid_amt)],
            PREPAID_ACCT:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_prepaid_acct)],
            PREPAID_START:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_prepaid_start)],
            PREPAID_END:       [MessageHandler(filters.TEXT & ~filters.COMMAND, step_prepaid_end)],
            PREPAID_CONFIRM:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_prepaid_confirm)],
            ACCT_TRF_FROM:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_acct_trf_from)],
            ACCT_TRF_TO:       [MessageHandler(filters.TEXT & ~filters.COMMAND, step_acct_trf_to)],
            ACCT_TRF_AMT:      [MessageHandler(filters.TEXT & ~filters.COMMAND, step_acct_trf_amt)],
            ACCT_TRF_NOTE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_acct_trf_note)],
            ACCT_TRF_CONFIRM:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_acct_trf_confirm)],
            PAY_VENDOR:        [MessageHandler(filters.TEXT & ~filters.COMMAND, step_pay_vendor)],
            PAY_DESC:          [MessageHandler(filters.TEXT & ~filters.COMMAND, step_pay_desc)],
            PAY_AMT:           [MessageHandler(filters.TEXT & ~filters.COMMAND, step_pay_amt)],
            PAY_DUE:           [MessageHandler(filters.TEXT & ~filters.COMMAND, step_pay_due)],
            PAY_ACCT:          [MessageHandler(filters.TEXT & ~filters.COMMAND, step_pay_acct)],
            PAY_CONFIRM:       [MessageHandler(filters.TEXT & ~filters.COMMAND, step_pay_confirm)],
            REC_CUST:          [MessageHandler(filters.TEXT & ~filters.COMMAND, step_rec_cust)],
            REC_DESC:          [MessageHandler(filters.TEXT & ~filters.COMMAND, step_rec_desc)],
            REC_AMT:           [MessageHandler(filters.TEXT & ~filters.COMMAND, step_rec_amt)],
            REC_DUE:           [MessageHandler(filters.TEXT & ~filters.COMMAND, step_rec_due)],
            REC_ACCT:          [MessageHandler(filters.TEXT & ~filters.COMMAND, step_rec_acct)],
            REC_CONFIRM:       [MessageHandler(filters.TEXT & ~filters.COMMAND, step_rec_confirm)],
            FIN_REPORT_MENU:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_fin_report_menu)],
            CAP_ACCT:          [MessageHandler(filters.TEXT & ~filters.COMMAND, step_cap_acct)],
            CAP_AMT:           [MessageHandler(filters.TEXT & ~filters.COMMAND, step_cap_amt)],
            CAP_CONFIRM:       [MessageHandler(filters.TEXT & ~filters.COMMAND, step_cap_confirm)],
            SHARE_NAME:        [MessageHandler(filters.TEXT & ~filters.COMMAND, step_share_name)],
            SHARE_ROLE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, step_share_role)],
            SHARE_CAP:         [MessageHandler(filters.TEXT & ~filters.COMMAND, step_share_cap)],
            SHARE_OWN:         [MessageHandler(filters.TEXT & ~filters.COMMAND, step_share_own)],
            SHARE_CONFIRM:     [MessageHandler(filters.TEXT & ~filters.COMMAND, step_share_confirm)],
            PAY_SETTLE_LIST:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_pay_settle_list)],
            PAY_SETTLE_ACCT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_pay_settle_acct)],
            PAY_SETTLE_CONFIRM:[MessageHandler(filters.TEXT & ~filters.COMMAND, step_pay_settle_confirm)],
            REC_SETTLE_LIST:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_rec_settle_list)],
            REC_SETTLE_ACCT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, step_rec_settle_acct)],
            REC_SETTLE_CONFIRM:[MessageHandler(filters.TEXT & ~filters.COMMAND, step_rec_settle_confirm)],
            # ── Advance Payment ──
            ADVPAY_PARTY:          [MessageHandler(filters.TEXT & ~filters.COMMAND, step_advpay_party)],
            ADVPAY_DESC:           [MessageHandler(filters.TEXT & ~filters.COMMAND, step_advpay_desc)],
            ADVPAY_AMT:            [MessageHandler(filters.TEXT & ~filters.COMMAND, step_advpay_amt)],
            ADVPAY_ACCT:           [MessageHandler(filters.TEXT & ~filters.COMMAND, step_advpay_acct)],
            ADVPAY_DUE:            [MessageHandler(filters.TEXT & ~filters.COMMAND, step_advpay_due)],
            ADVPAY_NOTE:           [MessageHandler(filters.TEXT & ~filters.COMMAND, step_advpay_note)],
            ADVPAY_CONFIRM:        [MessageHandler(filters.TEXT & ~filters.COMMAND, step_advpay_confirm)],
            ADVPAY_LIST:           [MessageHandler(filters.TEXT & ~filters.COMMAND, step_advpay_list)],
                        ADVPAY_SETTLE_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_advpay_settle_confirm)],
            # ── Referral Code assignment ──
            REFERRAL_CODE:         [MessageHandler(filters.TEXT & ~filters.COMMAND, step_referral_code)],
        },
        fallbacks=[
            CommandHandler("cancel",     cmd_cancel),
            CommandHandler("start",      show_main_menu),
            CommandHandler("menu",       show_main_menu),
            CommandHandler("help",       cmd_help),
            CommandHandler("version",    cmd_version),
            # Sales
            CommandHandler("sales",      cmd_sales_direct),
            # Members
            CommandHandler("member",     cmd_member_mgmt),
            CommandHandler("newmember",  cmd_newmember),
            CommandHandler("topup",      cmd_topup),
            CommandHandler("check",      cmd_check_member),
            CommandHandler("ranks",      cmd_ranks),
            # Reports
            CommandHandler("report",     cmd_today_report),
            CommandHandler("freport",    cmd_financial_report),
            CommandHandler("kpi",        cmd_kpi_cmd),
            CommandHandler("payroll",    cmd_payroll_cmd),
            CommandHandler("setattend",  cmd_setattend_cmd),
            CommandHandler("admin",      cmd_admin),
            CommandHandler("broadcast",  cmd_broadcast),
            CommandHandler("finance",    cmd_finance),
            # Booking management
            CommandHandler("bookings",   cmd_admin_bookings),
            CommandHandler("newbooking", cmd_staff_booking),
            MessageHandler(filters.Regex(r"^/approve_\d+$"), cmd_approve_booking),
            CommandHandler("approve", cmd_approve_booking),
            MessageHandler(filters.Regex(r"^/reject_\d+$"),  cmd_reject_booking),
            CommandHandler("reject", cmd_reject_booking),
            # Stock
            CommandHandler("stock",      cmd_stock_menu),
            CommandHandler("stockin",    cmd_stockin_direct),
            CommandHandler("stockout",   cmd_stockout_direct),
            CommandHandler("inventory",  cmd_inventory),
            CommandHandler("stocktoday", cmd_stocktoday),
            # Console
            CommandHandler("console",    cmd_console_status),
        ],
    )

    # Group -1: custom extend reply — fires BEFORE ConversationHandler (group 0)
    # raises ApplicationHandlerStop so conv never sees the message when pending
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_extend_reply),
        group=-1,
    )

    app.add_handler(conv)

    # Global inline-button handler — works regardless of conversation state
    app.add_handler(CallbackQueryHandler(cb_extend_timer,  pattern=r"^ext:"))
    app.add_handler(CallbackQueryHandler(cb_booking_mgmt,   pattern=r"^bkm:(approve|reject):\d+$"))
    app.add_handler(CallbackQueryHandler(cb_checkin_booking,  pattern=r"^bkm:checkin:\d+$"))
    app.add_handler(CallbackQueryHandler(cb_wl_action,       pattern=r"^wl:(notify|remove):\d+$"))
    app.add_handler(CallbackQueryHandler(cb_cancel_booking,     pattern=r"^bkc:\d+$"))
    app.add_handler(CallbackQueryHandler(cb_cancel_with_reason, pattern=r"^bkcr:\d+:\w+$"))
    app.add_handler(CallbackQueryHandler(cb_booking_arrive,      pattern=r"^bkarr:\d+$"))
    app.add_handler(CallbackQueryHandler(cb_booking_arrive,      pattern=r"^bkns:\d+$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cancel_note_input), group=10)

    # Standalone fallback handlers (outside ConversationHandler — for cold starts)
    for cmd, fn in [
        ("start",      show_main_menu),
        ("menu",       show_main_menu),
        ("cancel",     cmd_cancel),
        ("help",       cmd_help),
        ("version",    cmd_version),
        ("sales",      cmd_sales_direct),
        ("member",     cmd_member_mgmt),
        ("newmember",  cmd_newmember),
        ("topup",      cmd_topup),
        ("check",      cmd_check_member),
        ("ranks",      cmd_ranks),
        ("report",     cmd_today_report),
        ("freport",    cmd_financial_report),
        ("broadcast",  cmd_broadcast),
        ("kpi",        cmd_staff_kpi),
        ("payroll",    cmd_payroll),
        ("setattend",  cmd_setattend),
        ("admin",      cmd_admin),
        ("finance",    cmd_finance),
        ("stock",      cmd_stock_menu),
        ("stockin",    cmd_stockin_direct),
        ("stockout",   cmd_stockout_direct),
        ("inventory",  cmd_inventory),
        ("stocktoday",  cmd_stocktoday),
        ("console",     cmd_console_status),
        ("newbooking",     cmd_staff_booking),
        ("cancelbooking",  cmd_cancel_booking),
    ]:
        app.add_handler(CommandHandler(cmd, fn))

    # Register "/" dropdown list with Telegram
    async def _set_commands(application):
        await application.bot.set_my_commands([
            BotCommand("start",      "🏠 Main Menu"),
            BotCommand("menu",       "🏠 Main Menu"),
            BotCommand("sales",      "📝 New Sale (shortcut)"),
            BotCommand("member",     "💳 Member Management"),
            BotCommand("newmember",  "🆕 New Member Register"),
            BotCommand("topup",      "💰 Top Up Member"),
            BotCommand("check",      "🔍 Check Member Info"),
            BotCommand("ranks",      "📋 View Rank Tiers"),
            BotCommand("report",     "📊 Today's Report"),
            BotCommand("freport",    "💹 Financial Report (week + month)"),
            BotCommand("kpi",        "📈 Staff KPI"),
            BotCommand("payroll",    "💰 Monthly Payroll"),
            BotCommand("setattend",  "📅 Record Leave / Late"),
            BotCommand("admin",      "🔧 Admin Panel"),
            BotCommand("broadcast",  "📢 Broadcast message to customers"),
            BotCommand("stock",      "📦 Stock Update menu"),
            BotCommand("stockin",    "📥 Stock In (Restock)"),
            BotCommand("stockout",   "📦 Stock Out"),
            BotCommand("inventory",  "🗂 Inventory Status"),
            BotCommand("stocktoday", "🛒 Items sold today"),
            BotCommand("cancel",     "❌ Cancel & return"),
            BotCommand("help",       "📖 Command list"),
            BotCommand("version",    "📦 Bot version info"),
            BotCommand("console",    "🕹️ Console live status"),
            BotCommand("finance",    "💼 Finance Management"),
        ])

    app.post_init = _set_commands

    # Pre-warm config + member cache so first user interaction is instant
    logging.info("Pre-warming config and member cache...")
    _load_cfg()
    _load_members()

    # Start background cache refresh task (every 5 min)
    def _handle_task_exception(loop, context):
        """Log and suppress unhandled task exceptions to prevent bot crash."""
        msg = context.get("exception", context.get("message", "Unknown task error"))
        logging.error("Unhandled task exception: %s", msg, exc_info=context.get("exception"))
    
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(_handle_task_exception)
    loop.create_task(_bg_cache_refresh())
    loop.create_task(input_logger_batcher())

    logging.info("PS Vibe Bot is running...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        timeout=30,
        drop_pending_updates=True,
    )


