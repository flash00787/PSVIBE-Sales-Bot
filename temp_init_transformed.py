# Data Flow: Bot → API Client (api_client.py) → API Server (localhost:8000)
#            Now: API Server → MySQL (primary) → GSheets (fallback)
#            Previously: API Server → GSheets (direct)
import os
import re
import sys
from dataclasses import dataclass, field
import json
import time
import fcntl
import signal
import asyncio
import logging
from pathlib import Path
import functools
import concurrent.futures
# ── API Client for READ operations ──
try:
    from bot.api_client import (
        api_fetch_members, api_fetch_member_data, api_fetch_wallet_mins,
        api_fetch_balance_mins, api_fetch_member_tier, api_fetch_staff,
        api_fetch_staff_names, api_fetch_food_prices, api_fetch_food_costs,
        api_fetch_games, api_fetch_game_library, api_fetch_console_games, api_get_games_on_console,
        api_get_consoles_with_game, api_fetch_base_rate, api_fetch_console_multiplier,
        api_fetch_new_member_defaults, api_fetch_rank_thresholds, api_fetch_bonus_table,
        api_fetch_rank_table_display, api_fetch_alltime_effective_rate,
        api_fetch_member_effective_rate, api_build_member_rate_dict,
        api_fetch_base_salaries, api_fetch_attendance, api_fetch_salary_advances,
        api_fetch_promotions_cached, api_fetch_allowed_staff_ids, api_next_voucher,
        # -- Async READ imports (Phase: async migration) --
        api_fetch_wallet_mins_async, api_fetch_members_async, api_fetch_member_data_async,
        api_fetch_base_rate_async, api_fetch_food_prices_async, api_fetch_food_costs_async,
        api_fetch_console_multiplier_async, api_fetch_allowed_staff_ids_async,
        api_fetch_console_status_async, api_fetch_rank_thresholds_async,
        api_fetch_bonus_table_async, api_fetch_new_member_defaults_async,
        api_next_member_id, api_next_member_row_no, api_fetch_referral_code,
        api_fetch_console_status,
        # ── WRITE operations  ──
        api_create_booking, api_end_booking, api_cancel_booking,
        api_save_attendance, api_add_console_game, api_remove_console_game,
        api_set_game_disc_count, api_update_game_library_install,
        api_add_console_to_setting, api_remove_console_from_setting, api_update_console_multiplier,
        # ── Async core + WRITE async ──
        _api_call_async,
        api_fetch_balance_mins_async, api_fetch_member_tier_async,
        api_get_consoles_with_game_async, api_get_games_on_console_async,
        api_add_console_game_async, api_remove_console_game_async,
        api_end_booking_async, api_cancel_booking_async, api_create_booking_async,
        api_fetch_promotions_cached_async,
        api_fetch_games_async, api_fetch_game_library_async,
        api_fetch_console_games_async, api_set_game_disc_count_async,
        api_update_game_library_install_async, api_fetch_food_menu_async,
    )
    _HAS_API = True
except ImportError:
    _HAS_API = False


from datetime import datetime, timezone, timedelta

# ── Re-export from focused modules (backward compatible) ──
from enum import IntEnum

# Myanmar Time — GMT+6:30
MMT = timezone(timedelta(hours=6, minutes=30))
def now_mmt() -> datetime:
    return datetime.now(MMT)

BOT_VERSION = "2026.05.05-r1"   # Console double-booking conflict check (409 guard)

__all__ = ['wb', 'MMT', 'now_mmt', 'BOT_VERSION', 'get_att_sh', 'get_booking_sh', 'fetch_console_status', 'create_booking', 'end_booking', 'get_salary_adv_sh', 'get_game_lib_sh', 'fetch_games', 'set_game_disc_count', 'get_console_games_sh', 'fetch_console_games', 'get_games_on_console', 'get_consoles_with_game', 'check_disc_session_conflict', 'add_console_game', 'remove_console_game', 'update_game_library_install', 'calc_duration', 'cancel_booking', 'add_console_to_setting', 'remove_console_from_setting', 'get_consoles_from_setting', 'MAIN_MENU', 'MEMBER', 'CONSOLE', 'MINS', 'FOOD_MENU', 'FOOD_QTY', 'CONFIRM_SUMMARY', 'DISCOUNT', 'KPAY_AMT', 'SALE_CONFIRM', 'MM_MENU', 'NM_NAME', 'NM_PHONE', 'NM_EMAIL', 'NM_ID', 'NM_AMT', 'NM_KPAY', 'NM_REFERRAL', 'NM_CONFIRM', 'NM_GIFT_PIN', 'TU_MEMBER', 'TU_AMT', 'TU_KPAY', 'TU_CONFIRM', 'MM_LOOKUP', 'STOCK_PIN', 'STOCK_MENU', 'STOCK_ITEM', 'STOCK_QTY', 'SI_ITEM', 'SI_QTY', 'SI_COST', 'SI_CART', 'SI_PAY', 'SI_CONFIRM', 'ATTEND_STAFF', 'ATTEND_LEAVE', 'ATTEND_LATE', 'ATTEND_DEDUCT', 'ADMIN_PIN', 'ADMIN_MENU', 'SI_PAY_SPLIT', 'SAL_ADV_STAFF', 'SAL_ADV_AMT', 'SAL_ADV_PAY', 'SAL_ADV_CONFIRM', 'BOOK_LINK', 'BOOK_CONSOLE', 'BOOK_MEMBER', 'CONSOLE_MENU', 'END_SESSION_SELECT', 'GAME_MENU', 'GAME_ADD_TITLE', 'GAME_ADD_PLATFORM', 'GAME_ADD_GENRE', 'GAME_ADD_STATUS', 'GAME_DEL_SELECT', 'CON_MGMT_MENU', 'CON_ADD_ID', 'CON_ADD_TYPE', 'CON_ADD_MULT', 'CON_DEL_SELECT', 'CON_EDIT_MULT_SELECT', 'CON_EDIT_MULT_VALUE', 'SESSION_SHORTFALL', 'SALE_GAME_SELECT', 'DS_MEMBER_IN_SESSION', 'DS_CONSOLE_IN_SESSION', 'BOOK_DUP_WARN', 'BOOK_GAME', 'BOOK_MINS', 'GAME_CHANGE_CONS', 'GAME_CHANGE_GAME', 'SBK_CONSOLE', 'SBK_CUST_NAME', 'SBK_DATE', 'SBK_TIME', 'SBK_DUR', 'SBK_GAME', 'SBK_CONFIRM', 'GINST_MENU', 'GINST_VIEW_CONS', 'GINST_ADD_CONS', 'GINST_ADD_GAME', 'GINST_ADD_TYPE', 'GINST_DEL_CONS', 'GINST_DEL_GAME', 'SSD_MENU', 'SSD_VIEW_SSD', 'SSD_ADD_SSD', 'SSD_ADD_GAME', 'SSD_ADD_TYPE', 'SSD_DEL_SSD', 'SSD_DEL_GAME', 'SSD_XFER_SSD', 'SSD_XFER_GAME', 'SSD_XFER_CONS', 'SSD_RET_CONS', 'SSD_RET_GAME', 'SSD_MOVE_SSD', 'SSD_MOVE_GAME', 'SSD_MOVE_CONS', 'SSD_MOVE_FROM_CONS', 'SSD_MOVE_FROM_GAME', 'SSD_MOVE_TO_SSD', 'DISC_SELECT', 'DISC_SET_QTY', 'FINANCE_MENU', 'OPEX_CAT', 'OPEX_DESC', 'OPEX_AMT', 'OPEX_ACCT', 'OPEX_PAY', 'OPEX_CONFIRM', 'ASSET_NAME', 'ASSET_CAT', 'ASSET_DATE', 'ASSET_COST', 'ASSET_QTY', 'ASSET_LIFE', 'ASSET_SALVAGE', 'ASSET_PAY', 'ASSET_CONFIRM', 'ASSET_DISPOSE_SEL', 'ASSET_DISPOSE_DATE', 'ASSET_DISPOSE_QTY', 'ASSET_DISPOSE_PROCEEDS', 'ASSET_DISPOSE_CONFIRM', 'PREPAID_DESC', 'PREPAID_CAT', 'PREPAID_AMT', 'PREPAID_ACCT', 'PREPAID_START', 'PREPAID_END', 'PREPAID_CONFIRM', 'ACCT_TRF_FROM', 'ACCT_TRF_TO', 'ACCT_TRF_AMT', 'ACCT_TRF_NOTE', 'ACCT_TRF_CONFIRM', 'PAY_VENDOR', 'PAY_DESC', 'PAY_AMT', 'PAY_DUE', 'PAY_ACCT', 'PAY_CONFIRM', 'REC_CUST', 'REC_DESC', 'REC_AMT', 'REC_DUE', 'REC_ACCT', 'REC_CONFIRM', 'FIN_REPORT_MENU', 'CAP_ACCT', 'CAP_AMT', 'CAP_CONFIRM', 'SHARE_NAME', 'SHARE_ROLE', 'SHARE_CAP', 'SHARE_OWN', 'SHARE_CONFIRM', 'PAY_SETTLE_LIST', 'PAY_SETTLE_ACCT', 'PAY_SETTLE_CONFIRM', 'REC_SETTLE_LIST', 'REC_SETTLE_ACCT', 'REC_SETTLE_CONFIRM', 'ADVPAY_PARTY', 'ADVPAY_DESC', 'ADVPAY_AMT', 'ADVPAY_ACCT', 'ADVPAY_DUE', 'ADVPAY_NOTE', 'ADVPAY_CONFIRM', 'ADVPAY_LIST', 'ADVPAY_SETTLE_CONFIRM', 'PROMO_SELECT', 'BUNDLE_FOC', 'REFERRAL_CODE', 'GAME_EDIT_SELECT', 'GAME_EDIT_FIELD', 'GAME_EDIT_VALUE', 'GAME_DETAIL_PICK', 'ADJUST_TIME', 'WL_MENU', 'BTN_BACK', 'BTN_BACK_MAIN', 'BTN_DONE', 'BTN_YES', 'BTN_SAVE', 'BTN_NEW_SALE', 'BTN_CANCEL', 'BTN_CONFIRM_SAVE', 'NAV_ROW', 'VALID_CONSOLES', 'BTN_DAILY_SALES', 'BTN_MEMBER_MGMT', 'BTN_TODAY_REPORT', 'BTN_STOCK_UPDATE', 'BTN_STAFF_KPI', 'BTN_PAYROLL', 'BTN_FINANCIAL_REPORT', 'BTN_BALANCE', 'BTN_ADMIN', 'BTN_HELP', 'BTN_ADMIN_ATTEND', 'BTN_ADMIN_PNL', 'BTN_ADMIN_CF', 'BTN_ADMIN_LIB', 'BTN_ADMIN_BOOK', 'BTN_ADMIN_SAL_ADV', 'BTN_PROMO_REPORTS', 'BTN_CONSOLE_STATUS', 'BTN_CONSOLE_BOOK', 'BTN_CONSOLES', 'BTN_START_SESSION', 'BTN_END_SESSION', 'BTN_STATUS_BOARD', 'BTN_GAME_LIB_MENU', 'BTN_CON_MANAGE', 'BTN_ADD_GAME', 'BTN_VIEW_GAMES', 'BTN_DEL_GAME', 'BTN_ADD_CONSOLE', 'BTN_LIST_CONSOLE', 'BTN_DEL_CONSOLE', 'BTN_YES_END', 'BTN_NO_BACK', 'BTN_SI_SPLIT', 'BTN_STOCK_OUT', 'BTN_STOCK_IN_M', 'BTN_INVENTORY_VIEW', 'BTN_SKIP_DISC', 'BTN_PROMO_APPLY', 'BTN_MANUAL_DISC', 'BTN_APPLY_COUPON', 'BTN_CASH_DOWN', 'BTN_TOPUP_SESSION', 'BTN_SKIP_SALES', 'BTN_FOOD_SALE', 'BTN_YES_END_SESSION', 'BTN_NO_RESELECT', 'BTN_BOOK_PROCEED', 'BTN_SKIP_TIMER', 'BTN_STAFF_BOOK', 'BTN_CANCEL_BOOKING', 'BTN_SBK_TODAY', 'BTN_SBK_TOMORROW', 'BTN_SBK_CUSTOM', 'BTN_SBK_SKIP_PHONE', 'BTN_SBK_SKIP_GAME', 'BTN_SBK_CONFIRM_BOOK', 'BTN_SBK_NEW', 'BTN_SBK_CONFIRMED', 'BTN_SBK_WAITLIST', 'BTN_WL_VIEW_WAITING', 'BTN_WL_VIEW_ALL', 'BTN_WL_NOTIFY_NEXT', 'BTN_WL_REFRESH', 'BTN_CONSOLE_INSTALL', 'BTN_GINST_VIEW', 'BTN_GINST_ADD', 'BTN_GINST_REMOVE', 'BTN_GINST_HDD', 'BTN_GINST_DISC', 'BTN_GINST_SSD', 'BTN_SKIP_GAME', 'BTN_CHANGE_GAME', 'BTN_SSD_MANAGE', 'BTN_SSD_VIEW', 'BTN_SSD_ADD', 'BTN_SSD_REMOVE', 'BTN_SSD_TRANSFER', 'BTN_SSD_RETURN', 'BTN_SSD_MOVE_TO_CONSOLE', 'BTN_SSD_MOVE_TO_SSD', 'BTN_SSD_T1', 'BTN_SSD_BLUE', 'BTN_SSD_GREY', 'BTN_DISC_RECORD', 'BTN_EDIT_GAME', 'BTN_FINANCE', 'BTN_FIN_OPEX', 'BTN_FIN_ASSET', 'BTN_FIN_PREPAID', 'BTN_FIN_TRANSFER', 'BTN_FIN_PAYABLE', 'BTN_FIN_RECEIVABLE', 'BTN_FIN_REPORT', 'BTN_FIN_SETUP', 'BTN_FIN_PNL', 'BTN_FIN_BS', 'BTN_FIN_ACCTS', 'BTN_FIN_DEPR', 'BTN_FIN_ASSET_DISPOSE', 'BTN_FIN_PROFIT_SHARE', 'BTN_FIN_CAPITAL', 'BTN_FIN_SHAREHOLDER', 'BTN_FIN_SETTLE_PAY', 'BTN_FIN_SETTLE_REC', 'BTN_FIN_ADVPAY', 'BTN_FIN_SETTLE_ADVPAY', 'BTN_FIN_BACK', 'STOCK_ACCESS_PIN', 'CUSTOMER_BOT_TOKEN', 'STAFF_NOTIFY_CHAT', 'N8N_SESSION_WEBHOOK', 'N8N_BOOKING_WEBHOOK', 'BTN_FIRST_PURCHASE', 'BTN_TOP_UP', 'BTN_CHECK_MEMBER', 'BTN_VIEW_RANKS', 'BTN_ASSIGN_REFERRAL', 'BTN_CONFIRM_ID', 'BTN_NM_CUSTOM', 'BTN_NM_GIFT', 'BTN_SKIP_PHONE', 'BTN_SKIP_EMAIL', 'BTN_SKIP_REFERRAL', 'BTN_CLEAR_CART', 'BTN_SI_ADD', 'BTN_SI_FINISH', 'next_voucher', 'fetch_members', 'fetch_attendance', 'save_attendance', 'fetch_staff', 'fetch_base_salaries', 'ensure_sheet_headers', 'fetch_promotions_cached', 'fetch_allowed_staff_ids', 'fetch_wallet_mins', 'fetch_base_rate', 'fetch_new_member_defaults', 'fetch_food_prices', 'fetch_food_costs', 'fetch_console_multiplier', 'fetch_rank_thresholds', 'fetch_member_total_spend', 'fetch_member_phone', 'fetch_member_data', 'fetch_referral_code', 'save_referral_code', 'fetch_balance_mins', 'fetch_member_effective_rate', 'update_member_effective_rate', 'build_member_rate_dict', 'fetch_member_rank_from_sheet', 'fetch_member_tier', 'get_member_rank', 'display_rank', 'RANK_EMOJI', 'rank_emoji', 'build_rank_bonus_lines', 'fetch_bonus_table', 'get_bonus_mins', 'next_member_row_no', 'next_write_row', 'next_member_id', 'fetch_rank_table_display', 'get_top_up_suggestion', 'today_str', 'step_hdr', 'RECEIPTS_DIR', 'save_receipt_json', 'get_receipt_url', 'get_receipt_kb', 'PAY_METHOD', 'PAY_AMOUNT', 'BTN_PAY_DONE', 'BTN_ADD_PAY', 'BTN_NO_MORE', 'BotState']# Inline health-check server (stdlib only — no extra deps)
import os as _os, json as _json, time as _time, threading as _threading, logging as _logging
from http.server import HTTPServer as _HTTPServer, BaseHTTPRequestHandler as _BaseHandler
_HEALTH_LOG = _logging.getLogger("health")
_HEALTH_PORT = int(_os.environ.get("HEALTH_PORT", "8080"))
_START_TS = _time.time()

class _HealthHandler(_BaseHandler):
    def log_message(self, *a): pass
    def _send(self, code, payload):
        b = _json.dumps(payload, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def do_GET(self):
        if self.path in ("/health", "/healthz", "/"):
            s = int(_time.time() - _START_TS)
            m, s = divmod(s, 60); h, m = divmod(m, 60); d, h = divmod(h, 24)
            parts = []
            if d: parts.append(f"{d}d")
            if h: parts.append(f"{h}h")
            if m: parts.append(f"{m}m")
            parts.append(f"{s}s")
            self._send(200, {"status":"ok","service":"psvibe-sales-bot","version":"2026.05.05-r1","uptime_seconds":round(_time.time()-_START_TS,1),"uptime_human":" ".join(parts)})
        else:
            self._send(404, {"error":"not found"})
    def do_HEAD(self):
        code = 200 if self.path in ("/health","/healthz","/") else 404
        self.send_response(code); self.send_header("Content-Type","application/json"); self.end_headers()

def keep_alive():
    try:
        srv = _HTTPServer(("0.0.0.0", _HEALTH_PORT), _HealthHandler)
        srv.allow_reuse_address = True
        _threading.Thread(target=srv.serve_forever, daemon=True, name="health").start()
        _HEALTH_LOG.info("Health server started on port %d", _HEALTH_PORT)
    except Exception as e:
        _HEALTH_LOG.exception("Health server failed: %s", e)

from telegram import BotCommand, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.error import NetworkError, TimedOut
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    TypeHandler,
    filters,
)

_log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
_file_handler  = logging.FileHandler("bot_status.log", encoding="utf-8")
_file_handler.setFormatter(_log_formatter)
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_log_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[_file_handler, _console_handler],
)

# ── In-memory Cache System ──
import threading
_GLOBAL_CACHE = {}
_CACHE_LOCK = threading.Lock()
_CACHE_TTL = 300  # 5 seconds default TTL

def _cached(ttl=_CACHE_TTL):
    """Decorator: cache function results with TTL in seconds."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = (func.__name__, args, tuple(sorted(kwargs.items())))
            now = time.time()
            with _CACHE_LOCK:
                if key in _GLOBAL_CACHE:
                    val, ts = _GLOBAL_CACHE[key]
                    if now - ts < ttl:
                        return val
            result = func(*args, **kwargs)
            with _CACHE_LOCK:
                _GLOBAL_CACHE[key] = (result, now)
            return result
        return wrapper
    return decorator

def _clear_cache():
    """Clear all cached data."""
    with _CACHE_LOCK:
        _GLOBAL_CACHE.clear()

def _clear_cache_prefix(prefix: str):
    """Clear cache entries matching a prefix."""
    with _CACHE_LOCK:
        keys_to_remove = [k for k in _GLOBAL_CACHE if k[0].startswith(prefix)]
        for k in keys_to_remove:
            del _GLOBAL_CACHE[k]


# ── Lazy Worksheet Proxy ──
class _LazyWorksheet:
    """Worksheet that connects lazily — only on first actual use."""
    def __init__(self, name: str):
        self._name = name
        self._ws = None
        self._lock = threading.Lock()
    def _get(self):
        if self._ws is None:
            with self._lock:
                if self._ws is None:  # double-check
                    self._ws = wb.worksheet(self._name)
        return self._ws
    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return getattr(self._get(), name)
    def __iter__(self):
        return iter(self._get())
    def __len__(self):
        return len(self._get())
    def __getitem__(self, key):
        return self._get()[key]
    # gspread common methods
    def get_all_values(self, *a, **kw):
        return self._get().get_all_values(*a, **kw)
    def get_all_records(self, *a, **kw):
        return self._get().get_all_records(*a, **kw)
    def col_values(self, *a, **kw):
        return self._get().col_values(*a, **kw)
    def row_values(self, *a, **kw):
        return self._get().row_values(*a, **kw)
    def acell(self, *a, **kw):
        return self._get().acell(*a, **kw)
    def cell(self, *a, **kw):
        return self._get().cell(*a, **kw)
    def range(self, *a, **kw):
        return self._get().range(*a, **kw)
    def update(self, *a, **kw):
        return self._get().update(*a, **kw)
    def update_cell(self, *a, **kw):
        return self._get().update_cell(*a, **kw)
    def append_row(self, *a, **kw):
        return self._get().append_row(*a, **kw)
    def batch_update(self, *a, **kw):
        return self._get().batch_update(*a, **kw)
    def format(self, *a, **kw):
        return self._get().format(*a, **kw)
    def find(self, *a, **kw):
        return self._get().find(*a, **kw)
    def findall(self, *a, **kw):
        return self._get().findall(*a, **kw)
    def title(self):
        return self._name


# ─────────────────────────────────────────
#  SHEET AUTH
# ─────────────────────────────────────────
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds       = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
gc          = gspread.authorize(creds)
wb          = gc.open_by_key(os.environ["SHEET_ID"])
sales_sh    = _LazyWorksheet("Sales_Daily")
setting_sh  = _LazyWorksheet("Setting")
member_sh   = _LazyWorksheet("Card_Wallet")
stock_sh    = _LazyWorksheet("Stock_Out")
stock_in_sh = _LazyWorksheet("Stock_In")
topup_sh    = _LazyWorksheet("TopUp_Log")
inv_sh      = _LazyWorksheet("Inventory")
input_log_sh = _LazyWorksheet("Input_Log")

# ─────────────────────────────────────────

class RetryingWorksheet:
    """Transparent wrapper around a gspread.Worksheet that applies automatic
    retry-on-error for every gspread method call.

    This is an alternative to monkey-patching gspread.Worksheet methods.
    Instead of replacing class-level methods, you wrap individual Worksheet
    instances.  Every attribute access that resolves to a gspread Worksheet
    callable is automatically decorated with :func:`_sheets_retry`, giving you
    the same exponential-backoff behaviour (429 / 500 / 503) without mutating
    the upstream gspread class.

    Usage::

        ws = RetryingWorksheet(wb.worksheet("Sales_Daily"))
        rows = ws.get_all_values()        # automatically retried on API errors
        ws.update("A1", "hello")          # automatically retried on API errors

    Cached wrapped methods ensure that repeated calls to the same method do
    not create a new wrapper each time.

    Attributes:
        _wrapped (gspread.Worksheet): The real underlying Worksheet instance.
        _cache (dict): Cache of already-wrapped method callables.
    """

    __slots__ = ("_wrapped", "_cache")

    def __init__(self, worksheet):
        self._wrapped = worksheet
        self._cache: dict = {}

    def __getattr__(self, name):
        # Delegate to the underlying worksheet for everything not on the wrapper.
        attr = getattr(self._wrapped, name)
        if callable(attr):
            # Only wrap gspread methods, not dunder or private helpers.
            if name in self._cache:
                return self._cache[name]
            wrapped = _sheets_retry(attr)
            self._cache[name] = wrapped
            return wrapped
        return attr

    def __repr__(self):
        return f"<RetryingWorksheet({self._wrapped!r})>"

#  Apply retry wrapper to gspread Worksheet methods
# ─────────────────────────────────────────
_GSPREAD_METHODS_TO_WRAP = [
    'get_all_values', 'get_all_records', 'col_values', 'row_values',
    'append_row', 'append_rows', 'update', 'update_cell', 'update_cells',
    'delete_rows', 'delete_columns', 'get', 'batch_get', 'batch_update',
    'acell', 'cell', 'find', 'findall',
]

for _method_name in _GSPREAD_METHODS_TO_WRAP:
    _orig = getattr(gspread.Worksheet, _method_name, None)
    if _orig and not getattr(_orig, '_sheets_retry_wrapped', False):
        _wrapped = _sheets_retry(_orig)
        _wrapped._sheets_retry_wrapped = True
        setattr(gspread.Worksheet, _method_name, _wrapped)

# Also wrap Spreadsheet.add_worksheet
if hasattr(gspread.Spreadsheet, 'add_worksheet'):
    _orig_add = gspread.Spreadsheet.add_worksheet
    if not getattr(_orig_add, '_sheets_retry_wrapped', False):
        _wrapped_add = _sheets_retry(_orig_add)
        _wrapped_add._sheets_retry_wrapped = True
        gspread.Spreadsheet.add_worksheet = _wrapped_add

logging.info("Google Sheets retry wrapper applied (max %d retries, backoff 1s/2s/4s)", _SHEETS_MAX_RETRIES)


def _batch_update(ws, cells):
    """Batch update multiple cells across worksheets in 1 API call.

    cells: list of {"range": "SheetName!A1", "value": val}
    Uses the spreadsheet from the given worksheet reference.
    """
    data = [{"range": r["range"], "values": [[r["value"]]]} for r in cells]
    body = {"valueInputOption": "USER_ENTERED", "data": data}
    try:
        ws.spreadsheet.values_batch_update(body)
    except Exception as e:
        logging.error("Batch update failed: %s", e)


def get_att_sh():
    """Return (or create) the Attendance_Log worksheet."""
    try:
        return wb.worksheet("Attendance_Log")
    except Exception:
        sh = wb.add_worksheet("Attendance_Log", rows=200, cols=6)
        sh.update("A1:E1", [["Month", "Staff", "Leave_Days", "Late_Count", "Late_Deduct_Ks"]])
        return sh


def get_input_log_sh():
    """Return (or create) the Input_Log worksheet.
    Columns: A=Timestamp, B=Staff_ID, C=Staff_Name, D=Msg_Type,
             E=Input_Text, F=State, G=Voucher, H=Proc_ms, I=Flags
    """
    try:
        return wb.worksheet("Input_Log")
    except Exception:
        sh = wb.add_worksheet("Input_Log", rows=1000, cols=9)
        sh.update('A1:I1', [[
            'Timestamp', 'Staff_ID', 'Staff_Name', 'Msg_Type',
            'Input_Text', 'State', 'Voucher', 'Proc_ms', 'Flags'
        ]])
        return sh


def get_booking_sh():
    """Return (or create) the Console_Booking worksheet.
    Columns: A=BookingID, B=Date, C=ConsoleID, D=MemberID,
             E=StartTime, F=EndTime, G=Status, H=Staff, I=Notes
    """
    try:
        return wb.worksheet("Console_Booking")
    except Exception:
        sh = wb.add_worksheet("Console_Booking", rows=1000, cols=9)
        sh.update("A1:I1", [["BookingID", "Date", "ConsoleID", "MemberID",
                              "StartTime", "EndTime", "Status", "Staff", "Notes"]])
        return sh


def fetch_console_status() -> list[dict]:
    """Return list of console dicts with live status.
    Reads cached console_multipliers for H/I/J info; Console_Booking for live sessions.
    """
        result = api_fetch_console_status()
    if result is not None:
        # API returns {"consoles": [...]} with MySQL keys; map to GSheet-era format
        api_consoles = result.get("consoles", [])
        mapped = []
        # Pull multipliers from settings_config
        mults = _get_cfg().get("console_multipliers", {})
        for c in api_consoles:
            cid = c.get("console_id", "")
            mapped.append({
                "id": cid,
                "type": c.get("console_type", ""),
                "mult": float(mults.get(cid, 1.0)),
                "status": c.get("status", "Free"),
                "member": c.get("current_member"),
                "start": c.get("start_time"),
                "staff": c.get("staff_name"),
                "booking_id": c.get("booking_id"),
            })
        # Dedup by normalized console_id (safety)
        seen = {}
        deduped = []
        for item in mapped:
            norm = item["id"].replace(" ", "").upper()
            if norm not in seen:
                seen[norm] = True
                deduped.append(item)
        return deduped
    logging.error("API api_fetch_console_status() failed")

    # GSheet fallback removed — MySQL API is the single source of truth
    return []
