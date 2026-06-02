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
import gspread
from gspread.exceptions import APIError
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
    )
    _HAS_API = True
except ImportError:
    _HAS_API = False


# ─────────────────────────────────────────
#  GOOGLE SHEETS RETRY WRAPPER (Phase 2 - Data Safety)
#  Retries on 429/500/503 with exponential backoff
#  403 = permission denied → critical log, no retry
# ─────────────────────────────────────────
_gsheets_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=8, thread_name_prefix="gsheets"
)

_SHEETS_RETRY_CODES = (429, 500, 503)
_SHEETS_MAX_RETRIES = 3
_SHEETS_BASE_DELAY  = 1  # seconds

# ─────────────────────────────────────────
#  HANDLER DURATION LOGGING
#  Logs execution time of every state handler
# ─────────────────────────────────────────
import time as _time_module

def log_duration(handler_name: str):
    """Decorator that logs handler execution duration in milliseconds."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = _time_module.monotonic()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = (_time_module.monotonic() - start) * 1000
                logging.info(f"duration:{handler_name} took {elapsed:.0f}ms")
        return wrapper
    return decorator



class SheetsPermissionError(Exception):
    """Raised when the service account lacks permission to access a sheet.
    This is NOT transient — check Sharing settings and SA email."""
    pass


def _get_sa_email(sa_file: str = "service_account.json") -> str:
    """Extract the service account client_email from the JSON key file."""
    try:
        with open(sa_file, "r") as f:
            data = json.load(f)
        return data.get("client_email", "unknown")
    except Exception:
        return "unknown"


def _sheets_retry(func):
    """Decorator: retry gspread calls on transient API errors (429/500/503).
    403 = immediate critical log + SheetsPermissionError (no retry)."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        last_exc = None
        for attempt in range(_SHEETS_MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                code = e.response.status_code if hasattr(e, 'response') else 0
                # ── 403: permission denied – log critical, never retry ──
                if code == 403:
                    sa_email = _get_sa_email()
                    sheet_id = os.environ.get("SHEET_ID", "unknown")
                    logging.critical(
                        "🔴 SHEETS 403 FORBIDDEN — Permission denied!\n"
                        "   Service Account: %s\n"
                        "   Sheet ID:        %s\n"
                        "   Action: Share the sheet with the SA email above (Editor access).\n"
                        "   Error details: %s",
                        sa_email, sheet_id, str(e)[:200]
                    )
                    raise SheetsPermissionError(
                        f"403 Forbidden — SA '{sa_email}' cannot access sheet '{sheet_id}'. "
                        f"Share the sheet with Editor access to this email."
                    ) from e
                # ── Transient codes: retry ──
                if code in _SHEETS_RETRY_CODES and attempt < _SHEETS_MAX_RETRIES:
                    delay = _SHEETS_BASE_DELAY * (2 ** attempt)
                    logging.warning(
                        "Sheets API %d error (attempt %d/%d), retrying in %ds: %s",
                        code, attempt + 1, _SHEETS_MAX_RETRIES, delay,
                        str(e)[:100]
                    )
                    time.sleep(delay)
                    last_exc = e
                else:
                    raise
            except (ConnectionError, TimeoutError, OSError) as e:
                if attempt < _SHEETS_MAX_RETRIES:
                    delay = _SHEETS_BASE_DELAY * (2 ** attempt)
                    logging.warning(
                        "Sheets network error (attempt %d/%d), retrying in %ds: %s",
                        attempt + 1, _SHEETS_MAX_RETRIES, delay,
                        str(e)[:100]
                    )
                    time.sleep(delay)
                    last_exc = e
                else:
                    raise
        raise last_exc
    return wrapper
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timezone, timedelta

# ── Re-export from focused modules (backward compatible) ──
from enum import IntEnum

# Myanmar Time — GMT+6:30
MMT = timezone(timedelta(hours=6, minutes=30))
def now_mmt() -> datetime:
    return datetime.now(MMT)

BOT_VERSION = "2026.05.05-r1"   # Console double-booking conflict check (409 guard)

__all__ = ['wb', 'MMT', 'now_mmt', 'BOT_VERSION', 'get_att_sh', 'get_booking_sh', 'fetch_console_status', 'create_booking', 'end_booking', 'get_salary_adv_sh', 'get_game_lib_sh', 'fetch_games', 'set_game_disc_count', 'get_console_games_sh', 'fetch_console_games', 'get_games_on_console', 'get_consoles_with_game', 'check_disc_session_conflict', 'add_console_game', 'remove_console_game', 'update_game_library_install', 'calc_duration', 'cancel_booking', 'add_console_to_setting', 'remove_console_from_setting', 'get_consoles_from_setting', 'MAIN_MENU', 'MEMBER', 'CONSOLE', 'MINS', 'FOOD_MENU', 'FOOD_QTY', 'CONFIRM_SUMMARY', 'DISCOUNT', 'KPAY_AMT', 'SALE_CONFIRM', 'MM_MENU', 'NM_NAME', 'NM_PHONE', 'NM_EMAIL', 'NM_ID', 'NM_AMT', 'NM_KPAY', 'NM_REFERRAL', 'NM_CONFIRM', 'NM_GIFT_PIN', 'TU_MEMBER', 'TU_AMT', 'TU_KPAY', 'TU_CONFIRM', 'MM_LOOKUP', 'STOCK_PIN', 'STOCK_MENU', 'STOCK_ITEM', 'STOCK_QTY', 'SI_ITEM', 'SI_QTY', 'SI_COST', 'SI_CART', 'SI_PAY', 'SI_CONFIRM', 'ATTEND_STAFF', 'ATTEND_LEAVE', 'ATTEND_LATE', 'ATTEND_DEDUCT', 'ADMIN_PIN', 'ADMIN_MENU', 'SI_PAY_SPLIT', 'SAL_ADV_STAFF', 'SAL_ADV_AMT', 'SAL_ADV_PAY', 'SAL_ADV_CONFIRM', 'BOOK_LINK', 'BOOK_CONSOLE', 'BOOK_MEMBER', 'CONSOLE_MENU', 'END_SESSION_SELECT', 'GAME_MENU', 'GAME_ADD_TITLE', 'GAME_ADD_PLATFORM', 'GAME_ADD_GENRE', 'GAME_ADD_STATUS', 'GAME_DEL_SELECT', 'CON_MGMT_MENU', 'CON_ADD_ID', 'CON_ADD_TYPE', 'CON_ADD_MULT', 'CON_DEL_SELECT', 'CON_EDIT_MULT_SELECT', 'CON_EDIT_MULT_VALUE', 'SESSION_SHORTFALL', 'DS_MEMBER_IN_SESSION', 'DS_CONSOLE_IN_SESSION', 'BOOK_DUP_WARN', 'BOOK_GAME', 'BOOK_MINS', 'GAME_CHANGE_CONS', 'GAME_CHANGE_GAME', 'SBK_CONSOLE', 'SBK_CUST_NAME', 'SBK_DATE', 'SBK_TIME', 'SBK_DUR', 'SBK_GAME', 'SBK_CONFIRM', 'GINST_MENU', 'GINST_VIEW_CONS', 'GINST_ADD_CONS', 'GINST_ADD_GAME', 'GINST_ADD_TYPE', 'GINST_DEL_CONS', 'GINST_DEL_GAME', 'SSD_MENU', 'SSD_VIEW_SSD', 'SSD_ADD_SSD', 'SSD_ADD_GAME', 'SSD_ADD_TYPE', 'SSD_DEL_SSD', 'SSD_DEL_GAME', 'SSD_XFER_SSD', 'SSD_XFER_GAME', 'SSD_XFER_CONS', 'SSD_RET_CONS', 'SSD_RET_GAME', 'DISC_SELECT', 'DISC_SET_QTY', 'FINANCE_MENU', 'OPEX_CAT', 'OPEX_DESC', 'OPEX_AMT', 'OPEX_ACCT', 'OPEX_PAY', 'OPEX_CONFIRM', 'ASSET_NAME', 'ASSET_CAT', 'ASSET_DATE', 'ASSET_COST', 'ASSET_QTY', 'ASSET_LIFE', 'ASSET_SALVAGE', 'ASSET_PAY', 'ASSET_CONFIRM', 'ASSET_DISPOSE_SEL', 'ASSET_DISPOSE_DATE', 'ASSET_DISPOSE_QTY', 'ASSET_DISPOSE_PROCEEDS', 'ASSET_DISPOSE_CONFIRM', 'PREPAID_DESC', 'PREPAID_CAT', 'PREPAID_AMT', 'PREPAID_ACCT', 'PREPAID_START', 'PREPAID_END', 'PREPAID_CONFIRM', 'ACCT_TRF_FROM', 'ACCT_TRF_TO', 'ACCT_TRF_AMT', 'ACCT_TRF_NOTE', 'ACCT_TRF_CONFIRM', 'PAY_VENDOR', 'PAY_DESC', 'PAY_AMT', 'PAY_DUE', 'PAY_ACCT', 'PAY_CONFIRM', 'REC_CUST', 'REC_DESC', 'REC_AMT', 'REC_DUE', 'REC_ACCT', 'REC_CONFIRM', 'FIN_REPORT_MENU', 'CAP_ACCT', 'CAP_AMT', 'CAP_CONFIRM', 'SHARE_NAME', 'SHARE_ROLE', 'SHARE_CAP', 'SHARE_OWN', 'SHARE_CONFIRM', 'PAY_SETTLE_LIST', 'PAY_SETTLE_ACCT', 'PAY_SETTLE_CONFIRM', 'REC_SETTLE_LIST', 'REC_SETTLE_ACCT', 'REC_SETTLE_CONFIRM', 'ADVPAY_PARTY', 'ADVPAY_DESC', 'ADVPAY_AMT', 'ADVPAY_ACCT', 'ADVPAY_DUE', 'ADVPAY_NOTE', 'ADVPAY_CONFIRM', 'ADVPAY_LIST', 'ADVPAY_SETTLE_CONFIRM', 'PROMO_SELECT', 'BUNDLE_FOC', 'REFERRAL_CODE', 'GAME_EDIT_SELECT', 'GAME_EDIT_FIELD', 'GAME_EDIT_VALUE', 'ADJUST_TIME', 'WL_MENU', 'BTN_BACK', 'BTN_BACK_MAIN', 'BTN_DONE', 'BTN_YES', 'BTN_SAVE', 'BTN_NEW_SALE', 'BTN_CANCEL', 'BTN_CONFIRM_SAVE', 'NAV_ROW', 'VALID_CONSOLES', 'BTN_DAILY_SALES', 'BTN_MEMBER_MGMT', 'BTN_TODAY_REPORT', 'BTN_STOCK_UPDATE', 'BTN_STAFF_KPI', 'BTN_PAYROLL', 'BTN_FINANCIAL_REPORT', 'BTN_ADMIN', 'BTN_HELP', 'BTN_ADMIN_ATTEND', 'BTN_ADMIN_PNL', 'BTN_ADMIN_CF', 'BTN_ADMIN_LIB', 'BTN_ADMIN_BOOK', 'BTN_ADMIN_SAL_ADV', 'BTN_PROMO_REPORTS', 'BTN_CONSOLE_STATUS', 'BTN_CONSOLE_BOOK', 'BTN_CONSOLES', 'BTN_START_SESSION', 'BTN_END_SESSION', 'BTN_STATUS_BOARD', 'BTN_GAME_LIB_MENU', 'BTN_CON_MANAGE', 'BTN_ADD_GAME', 'BTN_VIEW_GAMES', 'BTN_DEL_GAME', 'BTN_ADD_CONSOLE', 'BTN_LIST_CONSOLE', 'BTN_DEL_CONSOLE', 'BTN_YES_END', 'BTN_NO_BACK', 'BTN_SI_SPLIT', 'BTN_STOCK_OUT', 'BTN_STOCK_IN_M', 'BTN_INVENTORY_VIEW', 'BTN_SKIP_DISC', 'BTN_PROMO_APPLY', 'BTN_MANUAL_DISC, BTN_APPLY_COUPON', 'BTN_CASH_DOWN', 'BTN_TOPUP_SESSION', 'BTN_SKIP_SALES', 'BTN_YES_END_SESSION', 'BTN_NO_RESELECT', 'BTN_BOOK_PROCEED', 'BTN_SKIP_TIMER', 'BTN_STAFF_BOOK', 'BTN_CANCEL_BOOKING', 'BTN_SBK_TODAY', 'BTN_SBK_TOMORROW', 'BTN_SBK_CUSTOM', 'BTN_SBK_SKIP_PHONE', 'BTN_SBK_SKIP_GAME', 'BTN_SBK_CONFIRM_BOOK', 'BTN_SBK_NEW', 'BTN_SBK_CONFIRMED', 'BTN_SBK_WAITLIST', 'BTN_WL_VIEW_WAITING', 'BTN_WL_VIEW_ALL', 'BTN_WL_NOTIFY_NEXT', 'BTN_WL_REFRESH', 'BTN_CONSOLE_INSTALL', 'BTN_GINST_VIEW', 'BTN_GINST_ADD', 'BTN_GINST_REMOVE', 'BTN_GINST_HDD', 'BTN_GINST_DISC', 'BTN_GINST_SSD', 'BTN_SKIP_GAME', 'BTN_CHANGE_GAME', 'BTN_SSD_MANAGE', 'BTN_SSD_VIEW', 'BTN_SSD_ADD', 'BTN_SSD_REMOVE', 'BTN_SSD_TRANSFER', 'BTN_SSD_RETURN', 'BTN_SSD_T1', 'BTN_SSD_BLUE', 'BTN_SSD_GREY', 'BTN_DISC_RECORD', 'BTN_EDIT_GAME', 'BTN_FINANCE', 'BTN_FIN_OPEX', 'BTN_FIN_ASSET', 'BTN_FIN_PREPAID', 'BTN_FIN_TRANSFER', 'BTN_FIN_PAYABLE', 'BTN_FIN_RECEIVABLE', 'BTN_FIN_REPORT', 'BTN_FIN_SETUP', 'BTN_FIN_PNL', 'BTN_FIN_BS', 'BTN_FIN_ACCTS', 'BTN_FIN_DEPR', 'BTN_FIN_ASSET_DISPOSE', 'BTN_FIN_PROFIT_SHARE', 'BTN_FIN_CAPITAL', 'BTN_FIN_SHAREHOLDER', 'BTN_FIN_SETTLE_PAY', 'BTN_FIN_SETTLE_REC', 'BTN_FIN_ADVPAY', 'BTN_FIN_SETTLE_ADVPAY', 'BTN_FIN_BACK', 'STOCK_ACCESS_PIN', 'CUSTOMER_BOT_TOKEN', 'STAFF_NOTIFY_CHAT', 'N8N_SESSION_WEBHOOK', 'N8N_BOOKING_WEBHOOK', 'BTN_FIRST_PURCHASE', 'BTN_TOP_UP', 'BTN_CHECK_MEMBER', 'BTN_VIEW_RANKS', 'BTN_ASSIGN_REFERRAL', 'BTN_CONFIRM_ID', 'BTN_NM_CUSTOM', 'BTN_NM_GIFT', 'BTN_SKIP_PHONE', 'BTN_SKIP_EMAIL', 'BTN_SKIP_REFERRAL', 'BTN_CLEAR_CART', 'BTN_SI_ADD', 'BTN_SI_FINISH', 'next_voucher', 'fetch_members', 'fetch_attendance', 'save_attendance', 'fetch_staff', 'fetch_base_salaries', 'ensure_sheet_headers', 'fetch_promotions_cached', 'fetch_allowed_staff_ids', 'fetch_wallet_mins', 'fetch_base_rate', 'fetch_new_member_defaults', 'fetch_food_prices', 'fetch_food_costs', 'fetch_console_multiplier', 'fetch_rank_thresholds', 'fetch_member_total_spend', 'fetch_member_phone', 'fetch_member_data', 'fetch_referral_code', 'save_referral_code', 'fetch_balance_mins', 'fetch_member_effective_rate', 'update_member_effective_rate', 'build_member_rate_dict', 'fetch_member_rank_from_sheet', 'fetch_member_tier', 'get_member_rank', 'display_rank', 'RANK_EMOJI', 'rank_emoji', 'build_rank_bonus_lines', 'fetch_bonus_table', 'get_bonus_mins', 'next_member_row_no', 'next_write_row', 'next_member_id', 'fetch_rank_table_display', 'get_top_up_suggestion', 'today_str', 'step_hdr', 'RECEIPTS_DIR', 'save_receipt_json', 'get_receipt_url', 'get_receipt_kb', 'PAY_METHOD', 'PAY_AMOUNT', 'BTN_PAY_DONE', 'BTN_ADD_PAY', 'BTN_NO_MORE', 'BotState']
# Inline health-check server (stdlib only — no extra deps)
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
    if _HAS_API:
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
            return mapped
        logging.warning("API api_fetch_console_status() failed, falling back to gspread")
    today = today_str()
    # Use cached console_multipliers if available, fallback to direct Sheets read
    cfg = _get_cfg()
    cached_mults = cfg.get("console_multipliers", {})
    if cached_mults:
        names = list(cached_mults.keys())
        types = [""] * len(names)
        mults = [cached_mults[n] for n in names]
    else:
        names  = setting_sh.col_values(8)[1:]   # H
        types  = setting_sh.col_values(9)[1:]   # I (console type)
        mults  = setting_sh.col_values(10)[1:]  # J (multiplier)
    consoles = []
    for i, name in enumerate(names):
        if not name.strip():
            continue
        try:
            mult = float(str(mults[i] if i < len(mults) else "1").replace(",", "").strip()) or 1.0
        except (ValueError, IndexError):
            mult = 1.0
        ctype = (types[i] if i < len(types) else "").strip()
        consoles.append({"id": name.strip(), "type": ctype, "mult": mult,
                         "status": "Free", "member": None, "start": None, "staff": None, "booking_id": None})

    # Overlay active bookings — cached 30 s
    try:
        global _BK_ROWS, _BK_TS
        if not _BK_ROWS or (time.time() - _BK_TS) > _BK_TTL:
            _BK_ROWS = get_booking_sh().get("A:I")  # OPT: range-restricted read (A=ID through I=notes)
            _BK_TS   = time.time()
        for row in _BK_ROWS[1:]:
            if len(row) < 7:
                continue
            bk_date   = row[1].strip()
            bk_cid    = row[2].strip()
            bk_status = row[6].strip()
            if bk_date == today and bk_status in ("Active", "Scheduled"):
                for c in consoles:
                    if c["id"] == bk_cid:
                        c["status"]     = bk_status
                        c["member"]     = row[3].strip() or "Guest"
                        c["start"]      = row[4].strip()
                        c["staff"]      = row[7].strip() if len(row) > 7 else ""
                        c["booking_id"] = row[0].strip()
                        break
    except Exception as e:
        logging.exception("fetch_console_status: booking_overlay: %s", e)
    return consoles


def create_booking(console_id: str, member_id: str, staff: str, notes: str = "", planned_end: str = "") -> str:
    """Append a row to Console_Booking and return the BookingID.
    planned_end: optional planned end time (HH:MM) stored in col F so the
    customer bot can detect disc-game conflicts accurately. Overwritten with
    actual end time when the session ends.
    """
    if _HAS_API:
        result = api_create_booking(console_id, member_id, staff, notes, planned_end)
        if result is not None:
            bk = result.get("data", {}).get("booking_id") or ""
            if bk:
                return bk
        logging.warning("API api_create_booking() failed, falling back to gspread")
    sh     = get_booking_sh()
    now    = now_mmt()
    date   = now.strftime("%-m/%-d/%Y")
    time_s = now.strftime("%H:%M")
    seq    = now.strftime("%H%M")
    bk_id  = f"BK-{now.strftime('%Y%m%d')}-{console_id.replace(' ','').replace('-','')}-{seq}"
    sh.append_row([bk_id, date, console_id, member_id, time_s, planned_end, "Active", staff, notes],
                  value_input_option="USER_ENTERED")
    return bk_id


def end_booking(booking_id: str) -> bool:
    """Mark a booking as Done and fill EndTime. Returns True if found."""
    if _HAS_API:
        result = api_end_booking(booking_id)
        if result is not None:
            return True
        logging.warning("API api_end_booking() failed, falling back to gspread")
    try:
        sh   = get_booking_sh()
        rows = sh.get("A:G")  # OPT: range-restricted (A=ID through G=status)
        for i, row in enumerate(rows[1:], start=2):
            if row and row[0].strip() == booking_id:
                now = now_mmt()
                sh.update(f"F{i}", [[now.strftime("%H:%M")]])
                sh.update(f"G{i}", [["Done"]])
                return True
    except Exception as e:
        logging.exception("end_booking: %s", e)
    return False


def get_salary_adv_sh():
    """Return (or create) the Salary_Advance worksheet.
    Columns: A=Date, B=Staff, C=Amount, D=Payment (Cash/KPay), E=Note
    """
    try:
        return wb.worksheet("Salary_Advance")
    except Exception:
        sh = wb.add_worksheet("Salary_Advance", rows=500, cols=5)
        sh.update("A1:E1", [["Date", "Staff", "Amount", "Payment", "Note"]])
        return sh


def get_game_lib_sh():
    """Return the Game_Library worksheet (must already exist with correct layout).
    Actual columns: A=No, B=Game Name, C=Final Status, D=Available Discs,
                    E=In Use, F=C-01, G=C-02 ... (console checkboxes),
                    Q=T7, R=SD1, S=SD2, T=Free Consoles, U=Installed_On
    """
    return wb.worksheet("Game_Library")


def fetch_games() -> list[dict]:
    """Return all games from Game_Library sheet (cached 10 min).
    Sheet columns: A=No, B=Game Name, C=Final Status, D=Available Discs,
                   E=In Use, F=C-01 ... (console checkboxes), SSD cols.
    Filters out garbage/metadata rows (empty title or non-game status).
    """
    if _HAS_API:
        result = api_fetch_game_library()   # has final_status + disc_count
        if result is not None:
            # Map MySQL keys → GSheet-era keys for handler compatibility
            mapped = []
            for i, g in enumerate(result.get("games", [])):
                mapped.append({
                    "row":        i + 2,  # 1-indexed + header
                    "title":      g.get("game_title", ""),
                    "status":     g.get("final_status", ""),
                    "discs":      str(g.get("disc_count", "")),
                    "solo_multi": g.get("solo_multi", ""),
                    "genre":      g.get("genre", ""),
                })
            return mapped
        logging.warning("API api_fetch_game_library() failed, falling back to gspread")
    try:
        global _GAME_ROWS, _GAME_TS
        if not _GAME_ROWS or (time.time() - _GAME_TS) > _GAME_TTL:
            _GAME_ROWS = get_game_lib_sh().get("A:U")  # OPT: range-restricted read (A=No through U=metadata)
            _GAME_TS   = time.time()
        rows = _GAME_ROWS
        if len(rows) < 2:
            return []
        games = []
        for i, row in enumerate(rows[1:], start=2):
            if not row:
                continue
            title  = row[1].strip() if len(row) > 1 else ""
            status = row[2].strip() if len(row) > 2 else ""
            if not title:
                continue
            # Skip metadata/section header rows (No must be numeric or empty-but-has-title)
            row_no = row[0].strip() if row else ""
            if row_no and not row_no.isdigit():
                continue  # skip section headers like "Game Data Transfer Record"
            # Skip rows that look like column headers (col B = "From ( SSD )" etc.)
            if title.lower() in ("from ( ssd )", "to ( console )", "game name",
                                 "samsung t - 7", "sandisk - 1", "sandisk - 2",
                                 "game data transfer record"):
                continue
            # col U (index 20) = Installed_On — we repurpose as "solo_multi|genre" metadata
            meta      = row[20].strip() if len(row) > 20 else ""
            solo_multi = ""
            genre      = ""
            if "|" in meta:
                parts = meta.split("|", 1)
                solo_multi = parts[0].strip()
                genre      = parts[1].strip()
            games.append({
                "row":       i,
                "title":     title,
                "status":    status,
                "discs":     row[3].strip() if len(row) > 3 else "",
                "solo_multi": solo_multi,
                "genre":     genre,
            })
        return games
    except Exception:
        return []


def set_game_disc_count(row_num: int, count: int) -> bool:
    """Update column D (Available Discs) for a game row in Game_Library. Returns True on success."""
    global _GAME_ROWS, _GAME_TS
    if _HAS_API:
        result = api_set_game_disc_count(row_num, count)
        if result is not None:
            _GAME_ROWS = None                   # invalidate cache
            _GAME_TS   = 0
            return True
        logging.warning("API api_set_game_disc_count() failed, falling back to gspread")
    try:
        sh = get_game_lib_sh()
        sh.update_cell(row_num, 4, count)   # col D = index 4
        _GAME_ROWS = None                   # invalidate cache
        _GAME_TS   = 0
        return True
    except Exception:
        return False


def get_console_games_sh():
    """Return (or create) the Console_Games worksheet.
    Columns: A=Console_ID, B=Game_Title, C=Install_Type, D=Date, E=Notes
    """
    try:
        return wb.worksheet("Console_Games")
    except Exception:
        sh = wb.add_worksheet("Console_Games", rows=1000, cols=5)
        sh.update("A1:E1", [["Console_ID", "Game_Title", "Install_Type", "Date", "Notes"]])
        return sh


def fetch_console_games() -> list[dict]:
    """Return all console-game installation records (cached 5 min)."""
    if _HAS_API:
        result = api_fetch_console_games()
        if result is not None:
            # API returns {"console_games": [{console_id, console_name, game_id, game_title, genre, status, slot_position}]}
            # Map MySQL keys to GSheet-era keys for handler compatibility
            raw = result.get("console_games", [])
            mapped = []
            for i, g in enumerate(raw):
                mapped.append({
                    "row":          i + 2,
                    "console_id":   g.get("console_id", ""),
                    "game_title":   g.get("game_title", ""),
                    "install_type": g.get("status", ""),
                    "date":         g.get("created_at", "") or "",
                    "notes":        "",
                })
            return mapped
        logging.warning("API api_fetch_console_games() failed, falling back to gspread")
    try:
        global _CGAME_ROWS, _CGAME_TS
        if not _CGAME_ROWS or (time.time() - _CGAME_TS) > _CGAME_TTL:
            _CGAME_ROWS = get_console_games_sh().get("A:E")  # OPT: range-restricted (A=console through E=notes)
            _CGAME_TS   = time.time()
        rows = _CGAME_ROWS
        if len(rows) < 2:
            return []
        return [
            {
                "row":          i,
                "console_id":   row[0].strip() if len(row) > 0 else "",
                "game_title":   row[1].strip() if len(row) > 1 else "",
                "install_type": row[2].strip() if len(row) > 2 else "",
                "date":         row[3].strip() if len(row) > 3 else "",
                "notes":        row[4].strip() if len(row) > 4 else "",
            }
            for i, row in enumerate(rows[1:], start=2)
            if row and row[0].strip()
        ]
    except Exception:
        return []


def get_games_on_console(console_id: str) -> list[str]:
    """Return list of game titles installed on a specific console.
    Excludes 'Session' type records (session tracking) to avoid duplicates.
    """
    if _HAS_API:
        result = api_get_games_on_console(console_id)
        if result is not None:
            # API returns {console_id, games: [{game_title, genre, status, slot_position}]}
            # Extract game titles from games array
            games_raw = result.get("games", []) if isinstance(result, dict) else result
            seen = set()
            titles = []
            for g in (games_raw if isinstance(games_raw, list) else []):
                t = g.get("game_title", "")
                if t and t not in seen:
                    seen.add(t)
                    titles.append(t)
            return titles
        logging.warning("API api_get_games_on_console(console_id) failed, falling back to gspread")
    seen = set()
    result = []
    for r in fetch_console_games():
        if (r["console_id"].upper() == console_id.upper()
                and r["game_title"]
                and r.get("install_type", "") != "Session"):
            t = r["game_title"]
            if t not in seen:
                seen.add(t)
                result.append(t)
    return result


def get_consoles_with_game(game_title: str) -> list[str]:
    """Return list of console IDs that have a specific game installed."""
    if _HAS_API:
        result = api_get_consoles_with_game(game_title)
        if result is not None:
            # API returns {game_title, consoles: [{console_id, console_name}]}
            # Extract console_ids from consoles array
            cons_raw = result.get("consoles", []) if isinstance(result, dict) else result
            if isinstance(cons_raw, list):
                return [r.get("console_id", "") for r in cons_raw if r.get("console_id")]
            return list(cons_raw) if isinstance(cons_raw, (list, set)) else []
        logging.warning("API api_get_consoles_with_game(game_title) failed, falling back to gspread")
    gl = game_title.strip().lower()
    return [
        r["console_id"] for r in fetch_console_games()
        if r["game_title"].strip().lower() == gl
    ]




def check_disc_session_conflict(game_name: str, bk_time: str) -> str:
    """Check if a disc game's copies are all in use at booking time (for staff bot).

    Returns a warning string if all disc copies are busy at bk_time,
    or empty string if no conflict.
    """
    game_lower = game_name.strip().lower()
    games = fetch_games()
    game_obj = next((g for g in games if g["title"].strip().lower() == game_lower), None)
    if not game_obj:
        return ""
    # Use "discs" (col D = Available Discs) — the column staff manages via the bot
    _discs_raw = game_obj.get("discs", "0") or "0"
    try:
        total = int(str(_discs_raw).strip()) if str(_discs_raw).strip().isdigit() else 0
    except Exception:
        total = 0
    if total == 0:
        return ""  # digital/SSD -- no disc limit

    try:
        bh, bm = map(int, bk_time.split(":"))
        bk_mins = bh * 60 + bm
    except Exception:
        return ""

    today = today_str()
    active_sessions = []
    try:
        sh   = get_booking_sh()
        rows = sh.get("A:I")  # OPT: range-restricted read (A=ID through I=notes)
        for row in rows[1:]:
            if len(row) < 7:
                continue
            if row[1].strip() != today:
                continue
            if row[6].strip() != "Active":
                continue
            notes = row[8].strip() if len(row) > 8 else ""
            if notes.lower() != game_lower:
                continue
            active_sessions.append({
                "console": row[2].strip(),
                "start":   row[4].strip() if len(row) > 4 else "",
                "end":     row[5].strip() if len(row) > 5 else "",
            })
    except Exception:
        return ""

    if len(active_sessions) < total:
        return ""  # enough discs available

    # All discs busy -- check if any session overlaps booking time
    overlapping = []
    can_proceed_all = True
    for s in active_sessions:
        end = s.get("end", "")
        if end and len(end) == 5:
            try:
                eh, em = map(int, end.split(":"))
                if eh * 60 + em > bk_mins:
                    overlapping.append(s)
                    can_proceed_all = False
            except Exception:
                overlapping.append(s)
                can_proceed_all = False
        else:
            overlapping.append(s)
            can_proceed_all = False

    if not overlapping:
        return ""  # all sessions end before booking time

    # Build warning message
    lines_str = ""
    for s in active_sessions:
        cid = s["console"]
        st  = s["start"] or "?"
        en  = s["end"]
        if en and len(en) == 5:
            lines_str += f"  🔴 {cid} — {st} ~ *{en}*\n"
        else:
            lines_str += f"  🔴 {cid} — {st} မှ ဆော့နေဆဲ\n"

    if can_proceed_all:
        return (
            f"ℹ️ *Disc Game — အခွေစစ်ဆေးပါ*\n"
            f"💿 *{game_name}* အခွေ {total} ခု ဆော့နေသည်\n"
            f"{lines_str}"
            f"✅ Session များ *{bk_time}* မတိုင်ခင် ပြီးမည် — Booking OK"
        )
    else:
        ends = [s["end"] for s in active_sessions if s.get("end") and len(s["end"]) == 5]
        ends.sort()
        earliest = ends[0] if ends else None
        earliest_line = f"⏰ အစောဆုံး ပြီးမည်် session: *{earliest}*\n" if earliest else ""
        return (
            f"⚠️ *Disc Game — အခွေမလောက်ဘူး!*\n"
            f"💿 *{game_name}* အခွေ {total} ခုပဲ ရှိပြီး ဆော့နေသည်\n"
            f"{lines_str}"
            f"{earliest_line}"
            f"Booking time *{bk_time}* မှာ disc ရနိုင်မည် မဟုတ်"
        )

def add_console_game(console_id: str, game_title: str, install_type: str, notes: str = "") -> bool:
    """Add a game installation record. Returns True on success."""
    global _CGAME_ROWS
    if _HAS_API:
        result = api_add_console_game(console_id, game_title, install_type, notes)
        if result is not None:
            _CGAME_ROWS = None   # invalidate cache
            return True
        logging.warning("API api_add_console_game() failed, falling back to gspread")
    try:
        sh   = get_console_games_sh()
        date = now_mmt().strftime("%-m/%-d/%Y")
        sh.append_row([console_id, game_title, install_type, date, notes],
                      value_input_option="USER_ENTERED")
        _CGAME_ROWS = None   # invalidate cache so next fetch reads fresh data
        return True
    except Exception:
        return False


def remove_console_game(console_id: str, game_title: str) -> bool:
    """Remove a game installation record. Returns True if found and removed."""
    global _CGAME_ROWS
    if _HAS_API:
        result = api_remove_console_game(console_id, game_title)
        if result is not None:
            _CGAME_ROWS = None   # invalidate cache
            return True
        logging.warning("API api_remove_console_game() failed, falling back to gspread")
    try:
        sh   = get_console_games_sh()
        rows = sh.get("A:B")  # OPT: range-restricted (A=console_id, B=game_title)
        for i, row in enumerate(rows[1:], start=2):
            if (len(row) >= 2
                    and row[0].strip().upper() == console_id.upper()
                    and row[1].strip().lower() == game_title.strip().lower()):
                sh.delete_rows(i)
                _CGAME_ROWS = None   # invalidate cache
                return True
    except Exception as e:
        logging.exception("remove_console_game: %s", e)
    return False


def _norm_cid(cid: str) -> str:
    """Normalise console ID for comparison: remove spaces, uppercase. 'C - 01' → 'C-01'."""
    return cid.replace(" ", "").upper()


def update_game_library_install(game_title: str, console_id: str, installed: bool) -> bool:
    """Set TRUE/FALSE in Game_Library for (game_title, console_id) intersection.
    Column B = Game Name; columns G:S = console headers (C-01 … SD2).
    Returns True on success.
    """
    if _HAS_API:
        result = api_update_game_library_install(game_title, console_id, installed)
        if result is not None:
            return True
        logging.warning("API api_update_game_library_install() failed, falling back to gspread")
    try:
        sh   = wb.worksheet("Game_Library")
        rows = sh.get("A:U")  # OPT: range-restricted read (A=No through U=metadata)
        if not rows:
            return False

        header_row = rows[0]  # row 1

        # Find console column index (G onwards = index 6)
        cid_norm = _norm_cid(console_id)
        col_idx  = None
        for i, h in enumerate(header_row):
            if _norm_cid(h) == cid_norm:
                col_idx = i
                break
        if col_idx is None:
            return False  # console column not found in sheet

        # Find game row (col B = index 1 = "Game Name")
        game_lower = game_title.strip().lower()
        row_idx    = None
        for i, row in enumerate(rows[1:], start=2):
            cell_val = row[1].strip().lower() if len(row) > 1 else ""
            if cell_val == game_lower:
                row_idx = i
                break
        if row_idx is None:
            return False  # game not found

        # Convert col_idx to A1 column letter(s)
        col_letter = ""
        n = col_idx + 1  # 1-indexed
        while n > 0:
            n, r = divmod(n - 1, 26)
            col_letter = chr(65 + r) + col_letter
        cell_addr = f"{col_letter}{row_idx}"

        sh.update(cell_addr, [[True if installed else ""]])
        return True
    except Exception:
        return False


def calc_duration(start_time_str: str) -> tuple[int, str]:
    """Calculate elapsed minutes from HH:MM start string. Returns (minutes, 'Xh Ym')."""
    try:
        from datetime import timedelta
        now   = now_mmt()
        h, m  = map(int, start_time_str.strip().split(":"))
        start = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if start > now:
            start -= timedelta(days=1)
        total_mins = int((now - start).total_seconds() // 60)
        hrs  = total_mins // 60
        mins = total_mins % 60
        fmt  = (f"{hrs}h {mins}m" if hrs > 0 else f"{mins}m")
        return total_mins, fmt
    except Exception:
        return 0, "?"


def cancel_booking(booking_id: str) -> bool:
    """Mark a booking as Cancelled. Returns True if found."""
    if _HAS_API:
        result = api_cancel_booking(booking_id)
        if result is not None:
            return True
        logging.warning("API api_cancel_booking() failed, falling back to gspread")
    try:
        sh   = get_booking_sh()
        rows = sh.get("A:G")  # OPT: range-restricted read (A=ID through G=status)
        for i, row in enumerate(rows[1:], start=2):
            if row and row[0].strip() == booking_id:
                sh.update(f"G{i}", [["Cancelled"]])
                return True
    except Exception as e:
        logging.exception("cancel_booking: %s", e)
    return False


def add_console_to_setting(console_id: str, ctype: str, multiplier: float) -> bool:
    """Append a new console to Setting!H:J. Returns True on success."""
    if _HAS_API:
        result = api_add_console_to_setting(console_id, ctype, multiplier)
        if result is not None:
            return True
        logging.warning("API api_add_console_to_setting() failed, falling back to gspread")
    try:
        names    = setting_sh.col_values(8)      # includes header row
        next_row = len(names) + 1
        setting_sh.update(f"H{next_row}:J{next_row}",
                          [[console_id, ctype, str(multiplier)]],
                          value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        logging.error("add_console_to_setting error: %s", e)
        return False


def remove_console_from_setting(console_id: str) -> bool:
    """Clear a console row from Setting!H:J. Returns True if found."""
    if _HAS_API:
        result = api_remove_console_from_setting(console_id)
        if result is not None:
            return True
        logging.warning("API api_remove_console_from_setting() failed, falling back to gspread")
    try:
        names = setting_sh.col_values(8)
        for i, name in enumerate(names):
            if name.strip() == console_id.strip():
                row = i + 1
                setting_sh.update(f"H{row}:J{row}", [["", "", ""]])
                return True
    except Exception as e:
        logging.exception("remove_console_from_setting: %s", e)
    return False



def update_console_multiplier(console_id: str, multiplier: float) -> bool:
    """Update multiplier for an existing console in Setting!J. Returns True on success."""
    if _HAS_API:
        result = api_update_console_multiplier(console_id, multiplier)
        if result is not None:
            return True
        logging.warning("API api_update_console_multiplier() failed, falling back to gspread")
    try:
        names = setting_sh.col_values(8)
        for i, name in enumerate(names):
            if name.strip() == console_id.strip():
                row = i + 1
                setting_sh.update(f"J{row}", [[str(multiplier)]],
                              value_input_option="USER_ENTERED")
                return True
    except Exception as e:
        logging.exception("update_console_multiplier: %s", e)
    return False


def get_consoles_from_setting() -> list[dict]:
    """Return all consoles from Setting!H:J as list of dicts."""
    try:
        names = setting_sh.col_values(8)[1:]
        types = setting_sh.col_values(9)[1:]
        mults = setting_sh.col_values(10)[1:]
        result = []
        for i, name in enumerate(names):
            if not name.strip():
                continue
            result.append({
                "id":   name.strip(),
                "type": types[i].strip() if i < len(types) else "",
                "mult": mults[i].strip() if i < len(mults) else "1",
            })
        return result
    except Exception:
        return []

# ─────────────────────────────────────────

class BotState(IntEnum):
    """Bot conversation states with integer values for ConversationHandler."""
    MAIN_MENU = 0
    MEMBER = 1
    CONSOLE = 2
    MINS = 3
    FOOD_MENU = 4
    FOOD_QTY = 5
    CONFIRM_SUMMARY = 6
    DISCOUNT = 7
    KPAY_AMT = 8
    SALE_CONFIRM = 9
    MM_MENU = 10
    NM_NAME = 11
    NM_PHONE = 12
    NM_EMAIL = 13
    NM_ID = 14
    NM_AMT = 15
    NM_KPAY = 16
    NM_REFERRAL = 17
    NM_CONFIRM = 18
    NM_GIFT_PIN = 19
    TU_MEMBER = 20
    TU_AMT = 21
    TU_KPAY = 22
    TU_CONFIRM = 23
    MM_LOOKUP = 24
    STOCK_PIN = 25
    STOCK_MENU = 26
    STOCK_ITEM = 27
    STOCK_QTY = 28
    SI_ITEM = 29
    SI_QTY = 30
    SI_COST = 31
    SI_CART = 32
    SI_PAY = 33
    SI_CONFIRM = 34
    ATTEND_STAFF = 37
    ATTEND_LEAVE = 38
    ATTEND_LATE = 39
    ATTEND_DEDUCT = 40
    ADMIN_PIN = 41
    ADMIN_MENU = 42
    SI_PAY_SPLIT = 43
    SAL_ADV_STAFF = 44
    SAL_ADV_AMT = 45
    SAL_ADV_PAY = 46
    SAL_ADV_CONFIRM = 47
    BOOK_LINK = 48
    BOOK_CONSOLE = 49
    BOOK_MEMBER = 50
    CONSOLE_MENU = 51
    END_SESSION_SELECT = 52
    GAME_MENU = 53
    GAME_ADD_TITLE = 54
    GAME_ADD_PLATFORM = 55
    GAME_ADD_GENRE = 56
    GAME_ADD_STATUS = 57
    GAME_DEL_SELECT = 58
    CON_MGMT_MENU = 59
    CON_ADD_ID = 60
    CON_ADD_TYPE = 61
    CON_ADD_MULT = 62
    CON_DEL_SELECT = 63
    CON_EDIT_MULT_SELECT = 101
    CON_EDIT_MULT_VALUE = 102
    SESSION_SHORTFALL = 64
    DS_MEMBER_IN_SESSION = 65
    DS_CONSOLE_IN_SESSION = 66
    BOOK_DUP_WARN = 67
    BOOK_GAME = 68
    BOOK_MINS = 69
    GAME_CHANGE_CONS = 70
    GAME_CHANGE_GAME = 71
    SBK_CONSOLE = 72
    SBK_CUST_NAME = 73
    SBK_DATE = 74
    SBK_TIME = 75
    SBK_DUR = 76
    SBK_GAME = 77
    SBK_CONFIRM = 78
    GINST_MENU = 79
    GINST_VIEW_CONS = 80
    GINST_ADD_CONS = 81
    GINST_ADD_GAME = 82
    GINST_ADD_TYPE = 83
    GINST_DEL_CONS = 84
    GINST_DEL_GAME = 85
    SSD_MENU = 86
    SSD_VIEW_SSD = 87
    SSD_ADD_SSD = 88
    SSD_ADD_GAME = 89
    SSD_ADD_TYPE = 90
    SSD_DEL_SSD = 91
    SSD_DEL_GAME = 92
    SSD_XFER_SSD = 93
    SSD_XFER_GAME = 94
    SSD_XFER_CONS = 95
    SSD_RET_CONS = 96
    SSD_RET_GAME = 97
    DISC_SELECT = 98
    DISC_SET_QTY = 99
    FINANCE_MENU = 100
    OPEX_CAT = 101
    OPEX_DESC = 102
    OPEX_AMT = 103
    OPEX_ACCT = 104
    OPEX_PAY = 105
    OPEX_CONFIRM = 106
    ASSET_NAME = 107
    ASSET_CAT = 108
    ASSET_DATE = 109
    ASSET_COST = 110
    ASSET_QTY = 111
    ASSET_LIFE = 112
    ASSET_SALVAGE = 113
    ASSET_PAY = 114
    ASSET_CONFIRM = 115
    ASSET_DISPOSE_SEL = 116
    ASSET_DISPOSE_DATE = 117
    ASSET_DISPOSE_QTY = 118
    ASSET_DISPOSE_PROCEEDS = 119
    ASSET_DISPOSE_CONFIRM = 120
    PREPAID_DESC = 121
    PREPAID_CAT = 122
    PREPAID_AMT = 123
    PREPAID_ACCT = 124
    PREPAID_START = 125
    PREPAID_END = 126
    PREPAID_CONFIRM = 127
    ACCT_TRF_FROM = 128
    ACCT_TRF_TO = 129
    ACCT_TRF_AMT = 130
    ACCT_TRF_NOTE = 131
    ACCT_TRF_CONFIRM = 132
    PAY_VENDOR = 133
    PAY_DESC = 134
    PAY_AMT = 135
    PAY_DUE = 136
    PAY_ACCT = 137
    PAY_CONFIRM = 138
    REC_CUST = 139
    REC_DESC = 140
    REC_AMT = 141
    REC_DUE = 142
    REC_ACCT = 143
    REC_CONFIRM = 144
    FIN_REPORT_MENU = 145
    CAP_ACCT = 146
    CAP_AMT = 147
    CAP_CONFIRM = 148
    SHARE_NAME = 149
    SHARE_ROLE = 150
    SHARE_CAP = 151
    SHARE_OWN = 152
    SHARE_CONFIRM = 153
    PAY_SETTLE_LIST = 154
    PAY_SETTLE_ACCT = 155
    PAY_SETTLE_CONFIRM = 156
    REC_SETTLE_LIST = 157
    REC_SETTLE_ACCT = 158
    REC_SETTLE_CONFIRM = 159
    ADVPAY_PARTY = 160
    ADVPAY_DESC = 161
    ADVPAY_AMT = 162
    ADVPAY_ACCT = 163
    ADVPAY_DUE = 164
    ADVPAY_NOTE = 165
    ADVPAY_CONFIRM = 166
    ADVPAY_LIST = 167
    ADVPAY_SETTLE_CONFIRM = 168
    PROMO_SELECT = 169
    BUNDLE_FOC = 170
    REFERRAL_CODE = 171
    PAY_METHOD = 177
    PAY_AMOUNT = 178
    GAME_EDIT_SELECT = 172
    GAME_EDIT_FIELD = 173
    GAME_EDIT_VALUE = 174
    ADJUST_TIME = 175
    WL_MENU = 176

# ── Module-level aliases for backward compatibility ──
MAIN_MENU = BotState.MAIN_MENU
MEMBER = BotState.MEMBER
CONSOLE = BotState.CONSOLE
MINS = BotState.MINS
FOOD_MENU = BotState.FOOD_MENU
FOOD_QTY = BotState.FOOD_QTY
CONFIRM_SUMMARY = BotState.CONFIRM_SUMMARY
DISCOUNT = BotState.DISCOUNT
KPAY_AMT = BotState.KPAY_AMT
SALE_CONFIRM = BotState.SALE_CONFIRM
MM_MENU = BotState.MM_MENU
NM_NAME = BotState.NM_NAME
NM_PHONE = BotState.NM_PHONE
NM_EMAIL = BotState.NM_EMAIL
NM_ID = BotState.NM_ID
NM_AMT = BotState.NM_AMT
NM_KPAY = BotState.NM_KPAY
NM_REFERRAL = BotState.NM_REFERRAL
NM_CONFIRM = BotState.NM_CONFIRM
NM_GIFT_PIN = BotState.NM_GIFT_PIN
TU_MEMBER = BotState.TU_MEMBER
TU_AMT = BotState.TU_AMT
TU_KPAY = BotState.TU_KPAY
TU_CONFIRM = BotState.TU_CONFIRM
MM_LOOKUP = BotState.MM_LOOKUP
STOCK_PIN = BotState.STOCK_PIN
STOCK_MENU = BotState.STOCK_MENU
STOCK_ITEM = BotState.STOCK_ITEM
STOCK_QTY = BotState.STOCK_QTY
SI_ITEM = BotState.SI_ITEM
SI_QTY = BotState.SI_QTY
SI_COST = BotState.SI_COST
SI_CART = BotState.SI_CART
SI_PAY = BotState.SI_PAY
SI_CONFIRM = BotState.SI_CONFIRM
ATTEND_STAFF = BotState.ATTEND_STAFF
ATTEND_LEAVE = BotState.ATTEND_LEAVE
ATTEND_LATE = BotState.ATTEND_LATE
ATTEND_DEDUCT = BotState.ATTEND_DEDUCT
ADMIN_PIN = BotState.ADMIN_PIN
ADMIN_MENU = BotState.ADMIN_MENU
SI_PAY_SPLIT = BotState.SI_PAY_SPLIT
SAL_ADV_STAFF = BotState.SAL_ADV_STAFF
SAL_ADV_AMT = BotState.SAL_ADV_AMT
SAL_ADV_PAY = BotState.SAL_ADV_PAY
SAL_ADV_CONFIRM = BotState.SAL_ADV_CONFIRM
BOOK_LINK = BotState.BOOK_LINK
BOOK_CONSOLE = BotState.BOOK_CONSOLE
BOOK_MEMBER = BotState.BOOK_MEMBER
CONSOLE_MENU = BotState.CONSOLE_MENU
END_SESSION_SELECT = BotState.END_SESSION_SELECT
GAME_MENU = BotState.GAME_MENU
GAME_ADD_TITLE = BotState.GAME_ADD_TITLE
GAME_ADD_PLATFORM = BotState.GAME_ADD_PLATFORM
GAME_ADD_GENRE = BotState.GAME_ADD_GENRE
GAME_ADD_STATUS = BotState.GAME_ADD_STATUS
GAME_DEL_SELECT = BotState.GAME_DEL_SELECT
CON_MGMT_MENU = BotState.CON_MGMT_MENU
CON_ADD_ID = BotState.CON_ADD_ID
CON_ADD_TYPE = BotState.CON_ADD_TYPE
CON_ADD_MULT = BotState.CON_ADD_MULT
CON_DEL_SELECT = BotState.CON_DEL_SELECT
CON_EDIT_MULT_SELECT = BotState.CON_EDIT_MULT_SELECT
CON_EDIT_MULT_VALUE = BotState.CON_EDIT_MULT_VALUE
SESSION_SHORTFALL = BotState.SESSION_SHORTFALL
DS_MEMBER_IN_SESSION = BotState.DS_MEMBER_IN_SESSION
DS_CONSOLE_IN_SESSION = BotState.DS_CONSOLE_IN_SESSION
BOOK_DUP_WARN = BotState.BOOK_DUP_WARN
BOOK_GAME = BotState.BOOK_GAME
BOOK_MINS = BotState.BOOK_MINS
GAME_CHANGE_CONS = BotState.GAME_CHANGE_CONS
GAME_CHANGE_GAME = BotState.GAME_CHANGE_GAME
SBK_CONSOLE = BotState.SBK_CONSOLE
SBK_CUST_NAME = BotState.SBK_CUST_NAME
SBK_DATE = BotState.SBK_DATE
SBK_TIME = BotState.SBK_TIME
SBK_DUR = BotState.SBK_DUR
SBK_GAME = BotState.SBK_GAME
SBK_CONFIRM = BotState.SBK_CONFIRM
GINST_MENU = BotState.GINST_MENU
GINST_VIEW_CONS = BotState.GINST_VIEW_CONS
GINST_ADD_CONS = BotState.GINST_ADD_CONS
GINST_ADD_GAME = BotState.GINST_ADD_GAME
GINST_ADD_TYPE = BotState.GINST_ADD_TYPE
GINST_DEL_CONS = BotState.GINST_DEL_CONS
GINST_DEL_GAME = BotState.GINST_DEL_GAME
SSD_MENU = BotState.SSD_MENU
SSD_VIEW_SSD = BotState.SSD_VIEW_SSD
SSD_ADD_SSD = BotState.SSD_ADD_SSD
SSD_ADD_GAME = BotState.SSD_ADD_GAME
SSD_ADD_TYPE = BotState.SSD_ADD_TYPE
SSD_DEL_SSD = BotState.SSD_DEL_SSD
SSD_DEL_GAME = BotState.SSD_DEL_GAME
SSD_XFER_SSD = BotState.SSD_XFER_SSD
SSD_XFER_GAME = BotState.SSD_XFER_GAME
SSD_XFER_CONS = BotState.SSD_XFER_CONS
SSD_RET_CONS = BotState.SSD_RET_CONS
SSD_RET_GAME = BotState.SSD_RET_GAME
DISC_SELECT = BotState.DISC_SELECT
DISC_SET_QTY = BotState.DISC_SET_QTY
FINANCE_MENU = BotState.FINANCE_MENU
OPEX_CAT = BotState.OPEX_CAT
OPEX_DESC = BotState.OPEX_DESC
OPEX_AMT = BotState.OPEX_AMT
OPEX_ACCT = BotState.OPEX_ACCT
OPEX_PAY = BotState.OPEX_PAY
OPEX_CONFIRM = BotState.OPEX_CONFIRM
ASSET_NAME = BotState.ASSET_NAME
ASSET_CAT = BotState.ASSET_CAT
ASSET_DATE = BotState.ASSET_DATE
ASSET_COST = BotState.ASSET_COST
ASSET_QTY = BotState.ASSET_QTY
ASSET_LIFE = BotState.ASSET_LIFE
ASSET_SALVAGE = BotState.ASSET_SALVAGE
ASSET_PAY = BotState.ASSET_PAY
ASSET_CONFIRM = BotState.ASSET_CONFIRM
ASSET_DISPOSE_SEL = BotState.ASSET_DISPOSE_SEL
ASSET_DISPOSE_DATE = BotState.ASSET_DISPOSE_DATE
ASSET_DISPOSE_QTY = BotState.ASSET_DISPOSE_QTY
ASSET_DISPOSE_PROCEEDS = BotState.ASSET_DISPOSE_PROCEEDS
ASSET_DISPOSE_CONFIRM = BotState.ASSET_DISPOSE_CONFIRM
PREPAID_DESC = BotState.PREPAID_DESC
PREPAID_CAT = BotState.PREPAID_CAT
PREPAID_AMT = BotState.PREPAID_AMT
PREPAID_ACCT = BotState.PREPAID_ACCT
PREPAID_START = BotState.PREPAID_START
PREPAID_END = BotState.PREPAID_END
PREPAID_CONFIRM = BotState.PREPAID_CONFIRM
ACCT_TRF_FROM = BotState.ACCT_TRF_FROM
ACCT_TRF_TO = BotState.ACCT_TRF_TO
ACCT_TRF_AMT = BotState.ACCT_TRF_AMT
ACCT_TRF_NOTE = BotState.ACCT_TRF_NOTE
ACCT_TRF_CONFIRM = BotState.ACCT_TRF_CONFIRM
PAY_VENDOR = BotState.PAY_VENDOR
PAY_DESC = BotState.PAY_DESC
PAY_AMT = BotState.PAY_AMT
PAY_DUE = BotState.PAY_DUE
PAY_ACCT = BotState.PAY_ACCT
PAY_CONFIRM = BotState.PAY_CONFIRM
REC_CUST = BotState.REC_CUST
REC_DESC = BotState.REC_DESC
REC_AMT = BotState.REC_AMT
REC_DUE = BotState.REC_DUE
REC_ACCT = BotState.REC_ACCT
REC_CONFIRM = BotState.REC_CONFIRM
FIN_REPORT_MENU = BotState.FIN_REPORT_MENU
CAP_ACCT = BotState.CAP_ACCT
CAP_AMT = BotState.CAP_AMT
CAP_CONFIRM = BotState.CAP_CONFIRM
SHARE_NAME = BotState.SHARE_NAME
SHARE_ROLE = BotState.SHARE_ROLE
SHARE_CAP = BotState.SHARE_CAP
SHARE_OWN = BotState.SHARE_OWN
SHARE_CONFIRM = BotState.SHARE_CONFIRM
PAY_SETTLE_LIST = BotState.PAY_SETTLE_LIST
PAY_SETTLE_ACCT = BotState.PAY_SETTLE_ACCT
PAY_SETTLE_CONFIRM = BotState.PAY_SETTLE_CONFIRM
REC_SETTLE_LIST = BotState.REC_SETTLE_LIST
REC_SETTLE_ACCT = BotState.REC_SETTLE_ACCT
REC_SETTLE_CONFIRM = BotState.REC_SETTLE_CONFIRM
ADVPAY_PARTY = BotState.ADVPAY_PARTY
ADVPAY_DESC = BotState.ADVPAY_DESC
ADVPAY_AMT = BotState.ADVPAY_AMT
ADVPAY_ACCT = BotState.ADVPAY_ACCT
ADVPAY_DUE = BotState.ADVPAY_DUE
ADVPAY_NOTE = BotState.ADVPAY_NOTE
ADVPAY_CONFIRM = BotState.ADVPAY_CONFIRM
ADVPAY_LIST = BotState.ADVPAY_LIST
ADVPAY_SETTLE_CONFIRM = BotState.ADVPAY_SETTLE_CONFIRM
PROMO_SELECT = BotState.PROMO_SELECT
BUNDLE_FOC = BotState.BUNDLE_FOC
REFERRAL_CODE = BotState.REFERRAL_CODE
PAY_METHOD = BotState.PAY_METHOD
PAY_AMOUNT = BotState.PAY_AMOUNT
GAME_EDIT_SELECT = BotState.GAME_EDIT_SELECT
GAME_EDIT_FIELD = BotState.GAME_EDIT_FIELD
GAME_EDIT_VALUE = BotState.GAME_EDIT_VALUE
ADJUST_TIME = BotState.ADJUST_TIME
WL_MENU = BotState.WL_MENU


# ─────────────────────────────────────────
#  BUTTON LABELS
# ─────────────────────────────────────────
BTN_BACK         = "⬅️ ပြန်သွား"
BTN_BACK_MAIN    = "⬅️ Main Menu သို့ပြန်"
BTN_DONE         = "Done ✅"
BTN_YES          = "Yes ✅"
BTN_SAVE         = "သိမ်းမည် ✅"
BTN_NEW_SALE     = "📝 New Sale"
BTN_CANCEL       = "❌ Cancel"
BTN_CONFIRM_SAVE = "✅ Confirm & Save"
BTN_PAY_DONE  = "✅ Payment Done"
BTN_ADD_PAY   = "➕ Add Payment"
BTN_NO_MORE   = "❌ No More"

# Attendance flow buttons
BTN_ATTEND_DONE = "✅ ပြီးပါပြီ"
BTN_ATTEND_SKIP = "⏭ Skip"

NAV_ROW = [BTN_BACK, BTN_CANCEL]   # appended to every wizard keyboard

# ── Finance Category Lists ──
OPEX_CATEGORIES = [
    "လစာ", "ငှားရမ်းခ", "မီတာခ", "အင်တာနက်",
    "ပြုပြင်စရိတ်", "ရုံးသုံးစရိတ်", "အခြား",
]
PAY_METHODS = ["Cash", "KPay", "WavePay", "Bank Transfer"]
ASSET_CATEGORIES = ["Furniture", "Equipment", "Electronics", "Vehicle", "Gaming Console", "Other"]
PREPAID_CATEGORIES = ["Rent", "Insurance", "Subscription", "Software License", "Other"]
FINANCE_ACCOUNTS = ["Cash", "KPay", "WavePay", "CB Bank", "AYA Bank", "Other"]
CAPITAL_ACCOUNTS = ["Cash", "KPay", "WavePay", "CB Bank", "AYA Bank", "Other"]
_SHARE_ROLES = ["Owner", "Partner", "Investor", "Staff"]

# Business start date for depreciation calculations
from datetime import datetime as _dt  # noqa: F811
_BIZ_START = _dt(2023, 1, 1)

def get_valid_consoles() -> set:
    """Return the set of active console IDs from the Settings sheet."""
    try:
        consoles = get_consoles_from_setting()
        return {c["id"] for c in consoles if c.get("id")}
    except Exception:
        # Fallback to cached data from fetch_console_status
        try:
            return {c["id"] for c in fetch_console_status() if c.get("id")}
        except Exception:
            # Hard emergency fallback
            return {
                "C - 01", "C - 02", "C - 03", "C - 04", "C - 05",
                "C - 06", "C - 07", "C - 08", "C - 09", "C - 10",
            }

# Dynamic VALID_CONSOLES — call get_valid_consoles() for live data
VALID_CONSOLES = get_valid_consoles()

# Main menu
BTN_DAILY_SALES  = "🛒 Daily Sales"
BTN_MEMBER_MGMT  = "💳 Member Management"
BTN_TODAY_REPORT = "📊 Today's Report"
BTN_STOCK_UPDATE = "📦 Stock Update"
BTN_STAFF_KPI          = "📈 Staff KPI"
BTN_PAYROLL            = "💰 Payroll"
BTN_FINANCIAL_REPORT   = "💹 Financial Report"
BTN_ADMIN              = "🔧 Admin Panel"
BTN_HELP               = "📋 Commands"
BTN_ADMIN_ATTEND  = "📅 Attendance"
BTN_ADMIN_PNL     = "📊 Monthly P&L"
BTN_ADMIN_CF      = "💵 Cash Flow"
BTN_ADMIN_LIB     = "💳 Card Liability"
BTN_ADMIN_BOOK    = "📋 Pending Bookings"
BTN_ADMIN_SAL_ADV = "💸 Salary Advance"
BTN_PROMO_REPORTS = "📊 Promo Reports"
BTN_CONSOLE_STATUS = "🕹️ Console Status"
BTN_CONSOLE_BOOK   = "📋 New Booking"
# Console Management submenu
BTN_CONSOLES        = "🕹️ Consoles"
BTN_START_SESSION   = "▶️ Session စတင်"
BTN_END_SESSION     = "⏹️ Session ဆုံး"
BTN_STATUS_BOARD    = "📊 Status ကြည့်"
BTN_GAME_LIB_MENU   = "🎮 Game Library"
BTN_CON_MANAGE      = "⚙️ Console စီမံ"
# Game Library
BTN_ADD_GAME        = "➕ ဂိမ်းထည့်"
BTN_VIEW_GAMES      = "📋 ဂိမ်းစာရင်း"
BTN_DEL_GAME        = "🗑️ ဂိမ်းဖျက်"
# Console CRUD
BTN_ADD_CONSOLE     = "➕ Console ထည့်"
BTN_LIST_CONSOLE    = "📋 Console စာရင်း"
BTN_DEL_CONSOLE     = "🗑️ Console ဖျက်"
BTN_EDIT_MULT     = "🖋️ Mult ပြင်မည်"
# Confirm/End
BTN_YES_END         = "✅ Yes — ဆုံးမည်"
BTN_NO_BACK         = "❌ No — ပြန်"
BTN_SI_SPLIT     = "💰 ခွဲပေး (Cash + KPay)"
BTN_STOCK_OUT        = "📦 Stock Out (ထုတ်ယူ)"
BTN_STOCK_IN_M       = "📥 Stock In (ဝယ်ယူ)"
BTN_INVENTORY_VIEW   = "📊 Inventory ကြည့်ရှု"
BTN_SKIP_DISC        = "⏩ Skip (Discount မထည့်)"
BTN_PROMO_APPLY      = "🎁 Promotion ထည်သွင်း"
BTN_MANUAL_DISC, BTN_APPLY_COUPON      = "✏️ Manual Discount ရိုက်"
# Session → Daily Sales bridge
BTN_CASH_DOWN        = "💵 Cash Down (ချက်ချင်းပေး)"
BTN_TOPUP_SESSION    = "💳 Top Up ပြီး ဆက်"
BTN_SKIP_SALES       = "⏭ Skip (မမှတ်တမ်းတင်)"
BTN_YES_END_SESSION  = "✅ Session ကို End မည်"
BTN_NO_RESELECT      = "❌ ပြန်ရွေး"
BTN_BOOK_PROCEED     = "⚠️ ဒါပဲ ဆက်ဖွင့်မည်"
BTN_SKIP_TIMER       = "⏭ Skip (Timer မလိုပါ)"
BTN_STAFF_BOOK       = "📅 Customer Booking"
BTN_CANCEL_BOOKING   = "🚫 Cancel Booking"
BTN_SBK_TODAY        = "📅 ယနေ့"
BTN_SBK_TOMORROW     = "📅 မနက်ဖြန်"
BTN_SBK_CUSTOM       = "✏️ ရက်ထည့်"
BTN_SBK_SKIP_PHONE   = "⏭ Phone မထည့်"
BTN_SBK_SKIP_GAME    = "⏭ Game မထည့်"
BTN_SBK_CONFIRM_BOOK = "✅ Booking ဖန်တီးမည်"
BTN_SBK_NEW          = "➕ New Booking"
BTN_SBK_CONFIRMED    = "✅ Confirmed Bookings"
BTN_SBK_WAITLIST     = "⏳ Waitlist"
# Waitlist management buttons
BTN_WL_VIEW_WAITING  = "📋 Waiting List ကြည့်"
BTN_WL_VIEW_ALL      = "📂 All Entries ကြည့်"
BTN_WL_NOTIFY_NEXT   = "🔔 Next ကို Notify"
BTN_WL_REFRESH       = "🔄 Refresh"
BTN_CONSOLE_INSTALL  = "🖥️ Console Install"
BTN_GINST_VIEW       = "📋 ဘယ် Console မှာ ဘာ ရှိသလဲ"
BTN_GINST_ADD        = "➕ Install မှတ်သား"
BTN_GINST_REMOVE     = "❌ Install ဖျက်"
BTN_GINST_HDD        = "💾 HDD (Internal)"
BTN_GINST_DISC       = "💿 Disc"
BTN_GINST_SSD        = "🔌 Portable SSD"
# External SSD Management
BTN_SKIP_GAME    = "⏭ ဂိမ်း မထည့်"
BTN_CHANGE_GAME  = "🔄 Game ပြောင်း"
BTN_SSD_MANAGE   = "📀 External SSD"
BTN_SSD_VIEW     = "📋 SSD ထဲ ဘာ ရှိသလဲ"
BTN_SSD_ADD      = "➕ SSD ထဲ ဂိမ်း ထည့်"
BTN_SSD_REMOVE   = "❌ SSD မှ ဂိမ်း ဖျက်"
BTN_SSD_TRANSFER = "🔄 SSD → Console (Transfer)"
BTN_SSD_RETURN   = "↩️ Console → SSD (Return)"
BTN_SSD_T1       = "Samsung T1 Shield"
BTN_SSD_BLUE     = "Sandisk Extreme (Blue)"
BTN_SSD_GREY     = "Sandisk Extreme (Grey)"
# Game Discs Record
BTN_DISC_RECORD  = "💿 Game Discs"
BTN_EDIT_GAME    = "✏️ Edit Game"

# ── Finance module buttons ──
BTN_FINANCE          = "💼 Finance"
BTN_FIN_OPEX         = "📝 OPEX"
BTN_FIN_ASSET        = "🏢 Asset"
BTN_FIN_PREPAID      = "📅 Prepaid"
BTN_FIN_TRANSFER     = "💸 Transfer"
BTN_FIN_PAYABLE      = "📤 Payable"
BTN_FIN_RECEIVABLE   = "📥 Receivable"
BTN_FIN_REPORT       = "📊 Reports"
BTN_FIN_SETUP        = "⚙️ Sheet Setup"
BTN_FIN_PNL          = "📊 P&L Report"
BTN_FIN_BS           = "🏦 Balance Sheet"
BTN_FIN_ACCTS        = "💰 Accounts"
BTN_FIN_DEPR         = "📉 Depreciation"
BTN_FIN_ASSET_DISPOSE = "🔄 Dispose Asset"
BTN_FIN_PROFIT_SHARE = "💸 Profit Sharing"
BTN_FIN_CAPITAL      = "🏦 Capital"
BTN_FIN_SHAREHOLDER  = "👥 Partners"
BTN_FIN_SETTLE_PAY   = "✅ Settle Pay"
BTN_FIN_SETTLE_REC   = "✅ Settle Rec"
BTN_FIN_ADVPAY       = "💵 Advance"
BTN_FIN_SETTLE_ADVPAY= "✅ Settle Adv"
BTN_FIN_BACK         = "⬅️ Finance Menu"

fetch_game_library  = fetch_games            # alias used in SSD management
write_console_game  = add_console_game       # alias used in SSD management
delete_console_game = remove_console_game    # alias used in SSD management


def _delete_session_game(console_id: str) -> None:
    """Remove any 'Session' type entry for a console from Console_Games."""
    try:
        sh   = get_console_games_sh()
        rows = sh.get("A:C")  # OPT: range-restricted read (A=console_id, C=install_type)
        for i, row in enumerate(rows[1:], start=2):
            if (len(row) >= 3
                    and row[0].strip().upper() == console_id.strip().upper()
                    and row[2].strip() == "Session"):
                sh.delete_rows(i)
                # Invalidate cache
                global _CGAME_ROWS, _CGAME_TS
                _CGAME_TS = 0
                return
    except Exception as e:
        logging.exception("_delete_session_game: %s", e)

SSD_NAMES: dict[str, str] = {
    "SSD-T1":   "Samsung T1 Shield",
    "SSD-Blue": "Sandisk Extreme (Blue)",
    "SSD-Grey": "Sandisk Extreme (Grey)",
}
SSD_BTN_TO_ID: dict[str, str] = {v: k for k, v in SSD_NAMES.items()}

STOCK_ACCESS_PIN    = os.environ["STOCK_PIN"]
CUSTOMER_BOT_TOKEN  = os.environ.get("CUSTOMER_BOT_TOKEN", "")
STAFF_NOTIFY_CHAT   = os.environ.get("STAFF_NOTIFY_CHAT", "")   # group chat ID for booking notifications
# Comma-separated Telegram user IDs allowed to use /broadcast (e.g. "12345678,87654321")
_BROADCAST_ADMIN_IDS: set[str] = {
    s.strip() for s in os.environ.get("ADMIN_USER_IDS", "").split(",") if s.strip()
}

# n8n Phase 2 — Session reminder webhook (restart-proof timer)
# Test URL  : https://psvibe.app.n8n.cloud/webhook-test/session-reminder
# Production : https://psvibe.app.n8n.cloud/webhook/session-reminder
N8N_SESSION_WEBHOOK  = os.environ.get("N8N_SESSION_WEBHOOK", "")
N8N_BOOKING_WEBHOOK  = os.environ.get("N8N_BOOKING_WEBHOOK", "")

# Member Management sub-menu
BTN_FIRST_PURCHASE = "🆕 New Member"
BTN_TOP_UP         = "💰 Top Up"
BTN_CHECK_MEMBER   = "🔍 Check Member"
BTN_VIEW_RANKS     = "📋 Rank Bonuses"
BTN_ASSIGN_REFERRAL = "🎁 Referral Code သတ်မှတ်"
BTN_CONFIRM_ID     = "✅ Confirm ID"
BTN_NM_CUSTOM      = "✏️ Enter Different Amount"
BTN_NM_GIFT        = "🎁 Gift / Free Card"
BTN_SKIP_PHONE     = "⏩ Skip"
BTN_SKIP_EMAIL     = "⏩ Email မထည့်"
BTN_SKIP_REFERRAL  = "⏩ Referral Code မထည့်"
BTN_CLEAR_CART     = "🗑️ Clear Cart"
BTN_SI_ADD         = "➕ Item ထပ်ထည့်"
BTN_SI_FINISH      = "💳 Payment & Save All"


# ═════════════════════════════════════════
#  SHEET HELPERS
# ═════════════════════════════════════════

def _int(val):
    """Safe int from sheet value — strips commas, 'Ks', spaces, handles floats."""
    try:
        cleaned = str(val).replace(",", "").replace("Ks", "").strip()
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0


def next_voucher():
    if _HAS_API:
        result = api_next_voucher()
        if result is not None:
            return result
        logging.warning("API api_next_voucher() failed, falling back to gspread")
    col = sales_sh.col_values(2)
    ids = [v for v in col[1:] if v.upper().startswith("V-")]
    if ids:
        try:
            return f"V-{int(ids[-1].split('-')[1]) + 1:03d}"
        except (IndexError, ValueError):
            pass
    return "V-001"


def fetch_members():
    if _HAS_API:
        result = api_fetch_members()
        if result is not None:
            return result
        logging.warning("API api_fetch_members() failed, falling back to gspread")
    raw = member_sh.col_values(2)[1:]
    return [m.strip() for m in raw if m.strip()]


async def fetch_members_async():
    """Async version - hot-path: called on every sales flow and member management."""
    if _HAS_API:
        result = await api_client.api_fetch_members_async()
        if result is not None:
            return result
        logging.warning("API api_fetch_members_async failed, falling back to gspread")
    return await asyncio.to_thread(fetch_members)


def fetch_attendance(month_str: str) -> dict[str, dict]:
    """Read Attendance_Log for given month. Returns {staff: {leave, late, deduct_per_late}}."""
    if _HAS_API:
        result = api_fetch_attendance(month_str)
        if result is not None:
            # API returns {"attendance": [{staff_name, login_time, logout_time, date, hours_worked, status}]}
            # Convert to bot format: {staff_name: {leave_days, late_count, deduct_per_late}}
            att_list = result.get("attendance", []) if isinstance(result, dict) else []
            converted = {}
            for a in att_list:
                sname = a.get("staff_name", "")
                if sname:
                    status = a.get("status", "")
                    converted[sname] = {
                        "leave_days": 1 if status and status.lower() != "present" else 0,
                        "late_count": 1 if status and "late" in status.lower() else 0,
                        "deduct_per_late": 500,
                    }
            return converted
        logging.warning("API api_fetch_attendance(month_str) failed, falling back to gspread")
    result: dict[str, dict] = {}
    try:
        rows = get_att_sh().get("A:E")  # OPT: range-restricted read (A=month through E=deduct)
        for row in rows[1:]:
            if len(row) < 4:
                continue
            if row[0].strip() != month_str:
                continue
            staff = row[1].strip()
            if not staff:
                continue
            result[staff] = {
                "leave_days":     int(row[2].strip() or 0) if len(row) > 2 else 0,
                "late_count":     int(row[3].strip() or 0) if len(row) > 3 else 0,
                "deduct_per_late": int(row[4].strip() or 500) if len(row) > 4 and row[4].strip() else 500,
            }
    except Exception as e:
        logging.warning("fetch_attendance: %s", e)
    return result


def save_attendance(month_str: str, staff: str, leave_days: int, late_count: int, deduct_per_late: int):
    """Insert or update row in Attendance_Log for given month+staff."""
    if _HAS_API:
        result = api_save_attendance(month_str, staff, leave_days, late_count, deduct_per_late)
        if result is not None:
            return
        logging.warning("API api_save_attendance() failed, falling back to gspread")
    try:
        sh   = get_att_sh()
        rows = sh.get("A:E")  # OPT: range-restricted read (A=month through E=deduct)
        for i, row in enumerate(rows[1:], start=2):
            if row[0].strip() == month_str and row[1].strip() == staff:
                sh.update(f"A{i}:E{i}", [[month_str, staff, leave_days, late_count, deduct_per_late]])
                return
        sh.append_row([month_str, staff, leave_days, late_count, deduct_per_late])
    except Exception as e:
        logging.warning("save_attendance: %s", e)


def fetch_staff() -> list[str]:
    """Read staff names from Setting!S2:S10 (col 19)."""
    if _HAS_API:
        result = api_fetch_staff()
        if result is not None:
            return result
        logging.warning("API api_fetch_staff() failed, falling back to gspread")
    try:
        vals = setting_sh.col_values(19)[1:]  # col S = index 19 (1-based)
        return [v.strip() for v in vals if v.strip()]
    except Exception:
        return ["Staff A", "Staff B"]


def fetch_base_salaries() -> dict[str, int]:
    """Read base salaries from Setting!T2:T10 (col 20). Returns {staff_name: salary}."""
    if _HAS_API:
        result = api_fetch_base_salaries()
        if result is not None:
            # API returns {"salaries": [{staff_name, base_salary, role}]}
            # Convert to {staff_name: base_salary} dict
            sal_list = []
            if isinstance(result, dict):
                sal_list = result.get("salaries", [])
            elif isinstance(result, list):
                sal_list = result
            return {s.get("staff_name", ""): int(float(s.get("base_salary", 0) or 0)) for s in sal_list if s.get("staff_name")}
        logging.warning("API api_fetch_base_salaries() failed, falling back to gspread")
    try:
        staff   = setting_sh.col_values(19)[1:]   # S = staff names
        salaries = setting_sh.col_values(20)[1:]  # T = base salaries
        result: dict[str, int] = {}
        for i, name in enumerate(staff):
            name = name.strip()
            if not name:
                continue
            sal_str = salaries[i].strip() if i < len(salaries) else "0"
            result[name] = int(sal_str.replace(",", "")) if sal_str.replace(",", "").isdigit() else 0
        return result
    except Exception:
        return {}


def ensure_sheet_headers():
    """Write column headers for new staff-tracking columns (idempotent).
    Uses batch write to avoid quota burn from 5 individual update_cell calls."""
    try:
        cells_to_update = []
        if not sales_sh.cell(1, 15).value:
            cells_to_update.append({"range": "Sales_Daily!O1", "value": "Staff"})
        if not member_sh.cell(1, 11).value:
            cells_to_update.append({"range": "Card_Wallet!K1", "value": "Reg_Staff"})
        if not topup_sh.cell(1, 10).value:
            cells_to_update.append({"range": "TopUp_Log!J1", "value": "Staff"})
        if not setting_sh.cell(1, 19).value:
            cells_to_update.append({"range": "Setting!S1", "value": "Staff Names"})
        if not setting_sh.cell(1, 20).value:
            cells_to_update.append({"range": "Setting!T1", "value": "Base Salary"})
        if cells_to_update:
            _batch_update(sales_sh, cells_to_update)
        existing = [v.strip() for v in setting_sh.col_values(19)[1:] if v.strip()]
        if not existing:
            setting_sh.update("S2:T3", [["Staff A", "0"], ["Staff B", "0"]])
    except Exception as e:
        logging.warning("ensure_sheet_headers: %s", e)


# ─────────────────────────────────────────
@dataclass
class BotStateData:
    cfg: dict = field(default_factory=dict)
    cfg_ts: float = 0.0
    member_rows: list = field(default_factory=list)
    member_ts: float = 0.0


#  BOT-LEVEL CONFIG + MEMBER CACHE
#  Eliminates ~8 Sheets API calls per user interaction.
#  Config refreshes every 5 min; member rows every 2 min.
# ─────────────────────────────────────────
_CFG:      dict  = {}
_CFG_TS:   float = 0.0
_CFG_TTL   = 300   # 5 minutes

_MBR_ROWS: list  = []
_MBR_TS:   float = 0.0
_MBR_TTL   = 180   # 3 minutes

# ── Console_Booking rows (live session overlay) ───────────────────────────────
_BK_ROWS:    list  = []
_BK_TS:      float = 0.0
_BK_TTL      = 30          # 30 s  — active sessions change frequently

# ── Game_Library rows ─────────────────────────────────────────────────────────
_GAME_ROWS:  list  = []
_GAME_TS:    float = 0.0
_GAME_TTL    = 600         # 10 min

# ── Console_Games rows ───────────────────────────────────────────────────────
_CGAME_ROWS: list  = []
_CGAME_TS:   float = 0.0
_CGAME_TTL   = 300         # 5 min

# ── Promotions cache (staff bot) ─────────────────────────────────────────────
_PROMO_CACHE: list  = []
_CACHE_LOCK = asyncio.Lock()  # async lock for background tasks
_THREAD_CACHE_LOCK = _threading.Lock()  # thread-safe lock for sync cache fns
_PROMO_TS:    float = 0.0
_PROMO_TTL    = 120          # 2 min — promotions don't change often


def fetch_promotions_cached() -> list:
    """Return active promotions list with 2-min cache to avoid repeated API calls."""
    if _HAS_API:
        result = api_fetch_promotions_cached()
        if result is not None:
            # API returns {"promotions": [{id, promo_name, ...}]} or list
            if isinstance(result, dict):
                return result.get("promotions", [])
            return result if isinstance(result, list) else []
        logging.warning("API api_fetch_promotions_cached() failed, falling back to gspread")
    global _PROMO_CACHE, _PROMO_TS
    with _THREAD_CACHE_LOCK:
        if _PROMO_CACHE and (time.time() - _PROMO_TS) < _PROMO_TTL:
            return _PROMO_CACHE
    data = _replit_get("sheets/promotions")
    promos = (data or {}).get("promotions", [])
    with _THREAD_CACHE_LOCK:
        _PROMO_CACHE = promos
        _PROMO_TS    = time.time()
    return promos


def _cfg_fresh() -> bool:
    with _THREAD_CACHE_LOCK:
        return bool(_CFG) and (time.time() - _CFG_TS) < _CFG_TTL


def _replit_get(path: str, timeout: int = 8):
    """GET JSON from API server. Returns parsed dict/list or safe empty fallback.

    Never returns None — callers can safely iterate/access the result.
    * List-like endpoints (bookings, waitlist, consoles, inventory, etc.) → []
    * Dict-like endpoints (sheets/config, finance, etc.) → {}
    """
    # Heuristic: endpoints whose name suggests a list return type
    _list_keywords = (
        "bookings", "waitlist", "consoles", "inventory",
        "staff", "games", "members", "logs", "attendance",
        "accounts", "payments", "salary", "promotions",
    )
    # sheets/ endpoints always return dicts; only raw resource paths return lists
    is_list_path = (
        not path.startswith("sheets/")
        and not path.startswith("finance/")
        and any(kw in path for kw in _list_keywords)
    )
    fallback = [] if is_list_path else {}

    base = _api_base()
    if not base:
        logging.warning("API base not configured — returning %s", type(fallback).__name__)
        return fallback
    try:
        import urllib.request as _req
        _rg_req = _req.Request(f"{base}/api/{path}", headers={"X-API-Key": _API_KEY})
        with _req.urlopen(_rg_req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            if data is None:
                logging.warning("API GET /%s returned null — returning %s", path, type(fallback).__name__)
                return fallback
            # Auto-unwrap {"data": [...], "success": true} envelope for list paths
            if is_list_path and isinstance(data, dict) and "data" in data:
                inner = data["data"]
                if isinstance(inner, list):
                    return inner
                if isinstance(inner, dict):
                    # Try common list keys inside data
                    for _list_key in ("bookings", "items", "members", "consoles", "games", "waitlist"):
                        if _list_key in inner and isinstance(inner[_list_key], list):
                            return inner[_list_key]
                    # Single-item dict (e.g. {"booking": {...}}) — return inner
                    return inner
            return data
    except Exception as e:
        logging.warning("API GET /%s failed: %s — returning %s", path, e, type(fallback).__name__)
        return fallback

def _replit_post(path: str, payload: dict, timeout: int = 10) -> dict | None:
    """POST JSON to API server. Returns parsed response dict or None on error."""
    base = _api_base()
    if not base:
        return None
    try:
        import urllib.request as _req
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = _req.Request(
            f"{base}/api/{path}",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json", "X-API-Key": _API_KEY},
        )
        with _req.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logging.warning("API POST /%s failed (payload keys: %s): %s", path, list(payload.keys()) if payload else [], e)
        return None


def _replit_delete(path: str, timeout: int = 10) -> dict | None:
    """DELETE request to API server. Returns parsed response dict or None on error."""
    base = _api_base()
    if not base:
        return None
    try:
        import urllib.request as _req
        req = _req.Request(
            f"{base}/api/{path}",
            method="DELETE",
            headers={"X-API-Key": _API_KEY},
        )
        with _req.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logging.warning("API DELETE /%s failed: %s", path, e)
        return None

def _replit_patch(path: str, payload: dict, timeout: int = 10) -> dict | None:
    """PATCH JSON to API server. Returns parsed response dict or None on error."""
    base = _api_base()
    if not base:
        return None
    try:
        import urllib.request as _req
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = _req.Request(
            f"{base}/api/{path}",
            data=data,
            method="PATCH",
            headers={"Content-Type": "application/json", "X-API-Key": _API_KEY},
        )
        with _req.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logging.warning("API PATCH /%s failed: %s", path, e)
        return None


def _replit_put(path: str, payload: dict, timeout: int = 10) -> dict | None:
    """PUT JSON to API server. Returns parsed response dict or None on error."""
    base = _api_base()
    if not base:
        return None
    try:
        import urllib.request as _req
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = _req.Request(
            f"{base}/api/{path}",
            data=data,
            method="PUT",
            headers={"Content-Type": "application/json", "X-API-Key": _API_KEY},
        )
        with _req.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logging.warning("API PUT /%s failed: %s", path, e)
        return None

def _load_cfg() -> None:
    global _CFG, _CFG_TS
    data = _replit_get("sheets/config")
    # API returns {"config": {...}} — unwrap nested config dict
    cfg = data.get("config", data) if isinstance(data, dict) else data
    if cfg and isinstance(cfg, dict) and "base_rate" in cfg:
        with _THREAD_CACHE_LOCK:
            _CFG    = cfg
            _CFG_TS = time.time()
        logging.info("Config cache refreshed (base_rate=%s, keys=%d)", cfg.get("base_rate"), len(cfg))


def _get_cfg() -> dict:
    if not _cfg_fresh():
        _load_cfg()
    return _CFG


def _mbr_fresh() -> bool:
    with _THREAD_CACHE_LOCK:
        return bool(_MBR_ROWS) and (time.time() - _MBR_TS) < _MBR_TTL


def _load_members() -> None:
    global _MBR_ROWS, _MBR_TS
    try:
        _MBR_ROWS = member_sh.get("A:Q")  # OPT: range-restricted read (A=row_no through Q=referral_code)
        with _THREAD_CACHE_LOCK:
            _MBR_TS   = time.time()
    except Exception as e:
        logging.warning("Member cache refresh failed: %s", e)


def _get_member_rows() -> list:
    if not _mbr_fresh():
        _load_members()
    return _MBR_ROWS


async def _bg_cache_refresh() -> None:
    """Background asyncio task — refresh config + member cache every 3 min."""
    while True:
        await asyncio.sleep(180)
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _load_cfg)
            await loop.run_in_executor(None, _load_members)
            logging.info("Background cache refresh done")
        except Exception as e:
            logging.warning("Background cache refresh error: %s", e)


# --- Staff Whitelist: dynamic from Google Sheets Setting!B30 ---
_STAFF_IDS:     set[int] = set()
_STAFF_IDS_TS:  float = 0.0
_STAFF_IDS_TTL  = 300  # 5 minutes

def fetch_allowed_staff_ids() -> set[int]:
    if _HAS_API:
        result = api_fetch_allowed_staff_ids()
        if result is not None:
            if isinstance(result, list):
                return set(result)
            return set(result.get("data", []))
        logging.warning("API api_fetch_allowed_staff_ids() failed, falling back to gspread")
    # Return allowed staff Telegram user IDs from Setting!B30 (comma-separated).
    # Falls back to hardcoded defaults if the cell is empty or unreadable.
    # Cached for 5 minutes.
    global _STAFF_IDS, _STAFF_IDS_TS
    if _STAFF_IDS and (time.time() - _STAFF_IDS_TS) < _STAFF_IDS_TTL:
        return _STAFF_IDS
    try:
        raw = setting_sh.cell(30, 2).value  # B30 = "Allowed Staff IDs"
        if raw and str(raw).strip():
            ids = {int(s.strip()) for s in str(raw).split(",") if s.strip().isdigit()}
            if ids:
                _STAFF_IDS = ids
                _STAFF_IDS_TS = time.time()
                logging.info("Staff whitelist loaded from Sheet: %s", sorted(ids))
                return _STAFF_IDS
    except Exception as e:
        logging.warning("Failed to read allowed staff IDs from Setting!B30: %s - using fallback", e)
    # Fallback to hardcoded defaults
    fallback = {8539344655, 8336350778, 6296803251}
    _STAFF_IDS = fallback
    _STAFF_IDS_TS = time.time()
    return fallback


async def fetch_allowed_staff_ids_async() -> set[int]:
    """Async version - hot-path: called on every main menu access."""
    if _HAS_API:
        result = await api_client.api_fetch_allowed_staff_ids_async()
        if result is not None:
            if isinstance(result, list):
                return set(result)
            return set(result.get("data", []))
        logging.warning("API api_fetch_allowed_staff_ids_async() failed, falling back to gspread")
    # Fallback to sync logic (wrapped in thread to avoid blocking)
    return await asyncio.to_thread(fetch_allowed_staff_ids)


def fetch_wallet_mins(member_id):
    if _HAS_API:
        result = api_fetch_wallet_mins(member_id)
        if result is not None:
            return result
        logging.warning("API api_fetch_wallet_mins(member_id) failed, falling back to gspread")
    for row in _get_member_rows()[1:]:
        if len(row) > 1 and row[1].strip() == member_id.strip():
            return _int(row[7]) if len(row) > 7 and row[7].strip() else None
    return None


async def fetch_wallet_mins_async(member_id):
    """Async version - hot-path: called on every sales flow."""
    if _HAS_API:
        result = await api_client.api_fetch_wallet_mins_async(member_id)
        if result is not None:
            return result
        logging.warning("API api_fetch_wallet_mins_async failed, falling back to gspread")
    return await asyncio.to_thread(fetch_wallet_mins, member_id)


def fetch_base_rate():
    if _HAS_API:
        result = api_fetch_base_rate()
        if result is not None:
            return result
        logging.warning("API api_fetch_base_rate() failed, falling back to gspread")
    cfg = _get_cfg()
    if cfg.get("base_rate"):
        return cfg["base_rate"]
    return _int(setting_sh.cell(2, 2).value)


async def fetch_base_rate_async():
    """Async version - hot-path: called on every sales flow."""
    if _HAS_API:
        result = await api_client.api_fetch_base_rate_async()
        if result is not None:
            return result
        logging.warning("API api_fetch_base_rate_async failed, falling back to gspread")
    return await asyncio.to_thread(fetch_base_rate)


def fetch_new_member_defaults():
    """Return (card_price, base_mins) from Setting!B20 and Setting!B21."""
    if _HAS_API:
        result = api_fetch_new_member_defaults()
        if result is not None:
            # API returns {"card_price": N, "base_mins": N} — unpack keys
            if isinstance(result, dict):
                return result.get("card_price", 0), result.get("base_mins", 0)
            return result
        logging.warning("API api_fetch_new_member_defaults() failed, falling back to gspread")
    cfg = _get_cfg()
    if cfg.get("new_member_card_price") is not None:
        return cfg["new_member_card_price"], cfg.get("new_member_base_mins", 0)
    try:
        price = _int(setting_sh.cell(20, 2).value)
        mins  = _int(setting_sh.cell(21, 2).value)
        return price, mins
    except Exception:
        return 0, 0


def fetch_food_prices():
    if _HAS_API:
        result = api_fetch_food_prices()
        if result is not None:
            return result
        logging.warning("API api_fetch_food_prices() failed, falling back to gspread")
    cfg = _get_cfg()
    if cfg.get("food_prices"):
        return dict(cfg["food_prices"])
    names  = setting_sh.col_values(4)[1:]
    prices = setting_sh.col_values(5)[1:]
    return {n.strip(): _int(p) for n, p in zip(names, prices) if n and p}


async def fetch_food_prices_async():
    """Async version - hot-path: called on every sales flow."""
    if _HAS_API:
        result = await api_client.api_fetch_food_prices_async()
        if result is not None:
            return result
        logging.warning("API api_fetch_food_prices_async failed, falling back to gspread")
    return await asyncio.to_thread(fetch_food_prices)


def fetch_food_costs():
    if _HAS_API:
        result = api_fetch_food_costs()
        if result is not None:
            return result
        logging.warning("API api_fetch_food_costs() failed, falling back to gspread")
    cfg = _get_cfg()
    if cfg.get("food_costs"):
        return dict(cfg["food_costs"])
    names = setting_sh.col_values(4)[1:]
    costs = setting_sh.col_values(6)[1:]
    return {n.strip(): (_int(c) if str(c).strip() else 0) for n, c in zip(names, costs) if n.strip()}


async def fetch_food_costs_async():
    """Async version - hot-path: called on every sales flow."""
    if _HAS_API:
        result = await api_client.api_fetch_food_costs_async()
        if result is not None:
            return result
        logging.warning("API api_fetch_food_costs_async failed, falling back to gspread")
    return await asyncio.to_thread(fetch_food_costs)


def fetch_console_multiplier(console_id):
    if _HAS_API:
        result = api_fetch_console_multiplier(console_id)
        if result is not None:
            return result
        logging.warning("API api_fetch_console_multiplier(console_id) failed, falling back to gspread")
    cfg = _get_cfg()
    mults = cfg.get("console_multipliers", {})
    if mults:
        return float(mults.get(console_id.strip(), 1.0)) or 1.0
    try:
        console_names = setting_sh.col_values(8)[1:]
        multipliers   = setting_sh.col_values(10)[1:]
        for name, mult in zip(console_names, multipliers):
            if name.strip() == console_id.strip():
                val = float(str(mult).replace(",", "").strip())
                return val if val > 0 else 1.0
    except Exception as e:
        logging.exception("fetch_console_multiplier: %s", e)
    return 1.0


async def fetch_console_multiplier_async(console_id):
    """Async version - hot-path: called on every sales flow."""
    if _HAS_API:
        result = await api_client.api_fetch_console_multiplier_async(console_id)
        if result is not None:
            return result
        logging.warning("API api_fetch_console_multiplier_async failed, falling back to gspread")
    return await asyncio.to_thread(fetch_console_multiplier, console_id)


def fetch_rank_thresholds():
    if _HAS_API:
        result = api_fetch_rank_thresholds()
        if result is not None:
            return _int(result.get("master_threshold", 0)), _int(result.get("immortal_threshold", 0))
        logging.warning("API api_fetch_rank_thresholds() failed, falling back to gspread")
    cfg = _get_cfg()
    if cfg.get("master_threshold") is not None:
        return _int(cfg["master_threshold"]), _int(cfg.get("immortal_threshold", 0))
    try:
        master   = _int(setting_sh.cell(3, 13).value)
        immortal = _int(setting_sh.cell(4, 13).value)
        return master, immortal
    except Exception:
        return 0, 0


def fetch_member_total_spend(member_id):
    """Return member's ranking net spend (Col F) — uses cached member rows."""
    if _HAS_API:
        result = api_fetch_member_data(member_id)
        if result is not None:
            return result.get("net_spend", 0)
        logging.warning("API api_fetch_member_data failed, falling back to gspread")
    try:
        for row in _get_member_rows()[1:]:
            if len(row) > 1 and row[1].strip() == member_id.strip():
                return _int(row[5]) if len(row) > 5 and row[5].strip() else 0
    except Exception as e:
        logging.exception("fetch_member_total_spend: %s", e)
    return 0


def fetch_member_phone(member_id):
    """Return phone (Col D) — uses cached member rows."""
    if _HAS_API:
        result = api_fetch_member_data(member_id)
        if result is not None:
            return result.get("phone", "-")
        logging.warning("API api_fetch_member_data failed, falling back to gspread")
    try:
        for row in _get_member_rows()[1:]:
            if len(row) > 1 and row[1].strip() == member_id.strip():
                return row[3].strip() if len(row) > 3 and row[3].strip() else "-"
    except Exception as e:
        logging.exception("fetch_member_phone: %s", e)
    return "-"


def fetch_member_data(member_id):
    """Single Card_Wallet read (cached) returning all commonly-needed member fields.
    Card_Wallet columns: A=row_no, B=member_id, C=name, D=phone,
    E=lifetime_spend, F=ranking_net_spend, G=rank_tier, H=wallet_mins,
    K=reg_staff, L=effective_rate, M=email, N=reserved, O=reserved, P=birthday, Q=referral_code"""
    if _HAS_API:
        result = api_fetch_member_data(member_id)
        if result is not None:
            return result
        logging.warning("API api_fetch_member_data(member_id) failed, falling back to gspread")
    try:
        for row in _get_member_rows()[1:]:
            if len(row) > 1 and row[1].strip() == member_id.strip():
                name          = row[2].strip()  if len(row) > 2  else "-"
                phone         = row[3].strip()  if len(row) > 3  else "-"
                net_spend     = _int(row[5])    if len(row) > 5  and row[5].strip() else 0
                wallet_mins   = _int(row[7])    if len(row) > 7  and row[7].strip() else None
                email         = row[12].strip() if len(row) > 12 else ""
                referral_code = row[16].strip() if len(row) > 16 else ""
                # Always compute rank from spend so sheet stale values don't mislead
                mt, it   = fetch_rank_thresholds()
                rank_raw = get_member_rank(net_spend, mt, it)
                return {
                    "name":          name or "-",
                    "phone":         phone or "-",
                    "email":         email,
                    "net_spend":     net_spend,
                    "rank_raw":      rank_raw,
                    "wallet_mins":   wallet_mins,
                    "referral_code": referral_code,
                }
    except Exception as e:
        logging.exception("fetch_member_data: %s", e)
    return {"name": "-", "phone": "-", "email": "", "net_spend": 0, "rank_raw": "Warrior", "wallet_mins": None, "referral_code": ""}

def fetch_referral_code(member_id: str) -> str:
    """Return the referral code for a member from Card_Wallet col Q (index 16). Live read."""
    if _HAS_API:
        result = api_fetch_referral_code(member_id)
        if result is not None:
            return result
        logging.warning("API api_fetch_referral_code(member_id) failed, falling back to gspread")
    try:
        rows = member_sh.get("A:Q")  # OPT: range-restricted read (A=row_no through Q=referral_code)
        for row in rows[1:]:
            if len(row) > 1 and row[1].strip() == member_id.strip():
                return row[16].strip() if len(row) > 16 else ""
    except Exception as e:
        logging.exception("fetch_referral_code: %s", e)
    return ""

def save_referral_code(member_id: str, code: str) -> bool:
    """Write referral code to Card_Wallet col Q (1-based col 17) for the given member. Returns True on success."""
    try:
        rows = member_sh.get("A:Q")  # OPT: range-restricted read (A=row_no through Q=referral_code)
        for i, row in enumerate(rows[1:], start=2):  # 1-based, skip header
            if len(row) > 1 and row[1].strip() == member_id.strip():
                # Ensure header exists
                if len(rows[0]) < 17 or not rows[0][16].strip():
                    member_sh.update_cell(1, 17, "Referral_Code")
                member_sh.update_cell(i, 17, code.strip())
                global _MBR_TS
                _MBR_TS = 0.0  # invalidate cache
                return True
    except Exception as e:
        import logging
        logging.error("save_referral_code failed for %s: %s", member_id, e)
    return False


def fetch_balance_mins(member_id: str) -> int:
    """Read current wallet balance (minutes) from Card_Wallet column H — bypasses cache (must be live)."""
    if _HAS_API:
        result = api_fetch_balance_mins(member_id)
        if result is not None:
            return result
        logging.warning("API api_fetch_balance_mins(member_id) failed, falling back to gspread")
    try:
        rows = member_sh.get("A:H")  # OPT: range-restricted read (A=row_no through H=wallet_mins)
        for row in rows[1:]:
            if len(row) > 1 and row[1].strip() == member_id.strip():
                return _int(row[7]) if len(row) > 7 and row[7].strip() else 0
    except Exception as e:
        logging.exception("fetch_balance_mins: %s", e)
    return 0


def fetch_member_effective_rate(member_id: str) -> float:
    """Read stored per-member effective rate from Card_Wallet col L."""
    if _HAS_API:
        result = api_fetch_member_effective_rate(member_id)
        if result is not None:
            # API returns {"member_id": ..., "effective_rate": float} - extract float
            if isinstance(result, dict):
                return float(result.get("effective_rate", 0.0) or 0.0)
            return float(result) if result else 0.0
        logging.warning("API api_fetch_member_effective_rate(member_id) failed, falling back to gspread")
    try:
        for row in _get_member_rows()[1:]:
            if len(row) > 1 and row[1].strip() == member_id.strip():
                val = row[11].strip() if len(row) > 11 else ""
                if val:
                    return float(val)
    except Exception as e:
        logging.warning("fetch_member_effective_rate %s: %s", member_id, e)
    return 0.0


def update_member_effective_rate(member_id: str, new_rate: float) -> None:
    """Write per-member effective rate to Card_Wallet col L (1-based col 12)."""
    try:
        rows = member_sh.get("A:L")  # OPT: range-restricted read (A=row_no through L=effective_rate)
        for i, row in enumerate(rows[1:], start=2):
            if len(row) > 1 and row[1].strip() == member_id.strip():
                member_sh.update_cell(i, 12, round(new_rate, 4))
                # Invalidate member cache so next read picks up the change
                global _MBR_TS
                _MBR_TS = 0.0
                return
        logging.warning("update_member_effective_rate: member %s not found", member_id)
    except Exception as e:
        logging.warning("update_member_effective_rate %s: %s", member_id, e)


def build_member_rate_dict() -> dict[str, float]:
    """Return {member_id: effective_rate} for all members with a stored rate in col L."""
    if _HAS_API:
        result = api_build_member_rate_dict()
        if result is not None:
            return result
        logging.warning("API api_build_member_rate_dict() failed, falling back to gspread")
    result: dict[str, float] = {}
    try:
        for row in _get_member_rows()[1:]:
            if len(row) > 1 and row[1].strip():
                m_id = row[1].strip()
                val  = row[11].strip() if len(row) > 11 else ""
                if val:
                    try:
                        result[m_id] = float(val)
                    except ValueError:
                        pass
    except Exception as e:
        logging.warning("build_member_rate_dict: %s", e)
    return result


def fetch_member_rank_from_sheet(member_id):
    """Read the member's rank label directly from Card_Wallet Column G (cached)."""
    if _HAS_API:
        result = api_fetch_member_data(member_id)
        if result is not None:
            return result.get("rank_raw", "Warrior")
        logging.warning("API api_fetch_member_data failed, falling back to gspread")
    try:
        for row in _get_member_rows()[1:]:
            if len(row) > 1 and row[1].strip() == member_id.strip():
                rank_val = row[6].strip() if len(row) > 6 else ""
                if rank_val:
                    return rank_val
                rank_progress = _int(row[5]) if len(row) > 5 else 0
                master, immortal = fetch_rank_thresholds()
                return get_member_rank(rank_progress, master, immortal)
    except Exception as e:
        logging.exception("fetch_member_rank_from_sheet: %s", e)
    return "New Member"


def fetch_member_tier(member_id: str) -> str:
    """Return the member's current tier label from Card_Wallet Column G (cached)."""
    if _HAS_API:
        result = api_fetch_member_tier(member_id)
        if result is not None:
            return result
        logging.warning("API api_fetch_member_tier(member_id) failed, falling back to gspread")
    try:
        for row in _get_member_rows()[1:]:
            if len(row) > 1 and row[1].strip() == member_id.strip():
                tier = row[6].strip() if len(row) > 6 else ""
                return tier if tier else "Warrior"
    except Exception as e:
        logging.exception("fetch_member_tier: %s", e)
    return "New Member"


def get_member_rank(total_spend, master_thresh, immortal_thresh):
    """Return rank label based on net Top-Up spend (Column E).
    0 spend = 'Warrior' (all registered members start as Warrior).
    Otherwise Warrior/Master/Immortal."""
    if immortal_thresh > 0 and total_spend >= immortal_thresh:
        return "Immortal"
    if master_thresh > 0 and total_spend >= master_thresh:
        return "Master"
    return "Warrior"


def display_rank(rank):
    """Normalise rank label for display — 'New Member' maps to 'Warrior'
    since all registered members hold at least Warrior status."""
    return "Warrior" if rank in ("New Member", "", None) else rank


RANK_EMOJI = {"Warrior": "⚔️", "Master": "🏅", "Immortal": "💎"}


def rank_emoji(rank):
    return RANK_EMOJI.get(display_rank(rank), "⚔️")


def build_rank_bonus_lines(rank, bonus_table):
    """Return formatted lines showing each bonus tier for the member's rank."""
    rank_col = {"Warrior": 1, "Master": 2, "Immortal": 3}
    eff_rank = display_rank(rank)
    col      = rank_col.get(eff_rank, 1)
    lines    = []
    for (threshold, w, m, i) in sorted(bonus_table, key=lambda x: x[0]):
        bonus = (w, m, i)[col - 1]
        if threshold > 0:
            lines.append(f"  • {threshold:,} Ks  →  +{bonus} mins")
    return lines


def fetch_bonus_table():
    """Fetch bonus table from cache (or Setting!O2:R5 as fallback).
    Returns list of (threshold, warrior_bonus, master_bonus, immortal_bonus)."""
    if _HAS_API:
        result = api_fetch_bonus_table()
        if result is not None:
            # API returns [{threshold, warrior_bonus, master_bonus, immortal_bonus}, ...]
            # Convert to [(threshold, w_bonus, m_bonus, i_bonus), ...] tuple format
            if result and isinstance(result, list):
                converted = []
                for row in result:
                    t = int(row.get("threshold", 0) or 0)
                    w = int(row.get("warrior_bonus", 0) or 0)
                    m = int(row.get("master_bonus", 0) or 0)
                    i = int(row.get("immortal_bonus", 0) or 0)
                    if t > 0 or w or m or i:
                        converted.append((t, w, m, i))
                return converted
            return result
        logging.warning("API api_fetch_bonus_table() failed, falling back to gspread")
    cfg = _get_cfg()
    if cfg.get("bonus_table"):
        return [tuple(row) for row in cfg["bonus_table"]]
    try:
        rows = setting_sh.get("O2:R5")
        result = []
        for row in rows:
            if len(row) < 4:
                continue
            try:
                threshold = _int(row[0])
                w_bonus   = _int(row[1])
                m_bonus   = _int(row[2])
                i_bonus   = _int(row[3])
                if threshold > 0 or any([w_bonus, m_bonus, i_bonus]):
                    result.append((threshold, w_bonus, m_bonus, i_bonus))
            except (ValueError, TypeError):
                continue
        return result
    except Exception:
        return []


def get_bonus_mins(rank, amount, bonus_table):
    """Return bonus mins for the given rank and top-up amount.
    Finds the row with the highest threshold that is still <= amount."""
    if not bonus_table:
        return 0
    rank_col = {"Warrior": 1, "Master": 2, "Immortal": 3}
    col = rank_col.get(display_rank(rank), 1)
    matched_bonus     = 0
    matched_threshold = -1
    for (threshold, w, m, i) in bonus_table:
        if amount >= threshold and threshold > matched_threshold:
            matched_threshold = threshold
            matched_bonus     = (w, m, i)[col - 1]
    return matched_bonus


def next_member_row_no():
    """Return the next sequential row number for Card_Wallet Column A (No).
    Reads all values in col A, finds the last integer, and returns +1."""
    if _HAS_API:
        result = api_next_member_row_no()
        if result is not None:
            return result
        logging.warning("API api_next_member_row_no() failed, falling back to gspread")
    try:
        col_a = member_sh.col_values(1)[1:]   # skip header
        nums  = []
        for v in col_a:
            try:
                nums.append(int(str(v).strip()))
            except (ValueError, TypeError):
                pass
        return (max(nums) + 1) if nums else 1
    except Exception:
        return 1


def next_write_row(worksheet):
    """Return the next empty row number for a worksheet.
    Uses Column B (always written by the bot, never a formula) as the anchor
    so ARRAYFORMULA-filled columns don't inflate the count."""
    return len(worksheet.col_values(2)) + 1


def next_member_id():
    """Auto-increment the last member ID in Card_Wallet Column B.
    Handles any trailing digits: 'PSV_A_003' → 'PSV_A_004'.
    Returns 'PSV_A_001' when no members exist yet."""
    if _HAS_API:
        result = api_next_member_id()
        if result is not None:
            return result
        logging.warning("API api_next_member_id() failed, falling back to gspread")
    try:
        ids = [v.strip() for v in member_sh.col_values(2)[1:] if v.strip()]
        if not ids:
            return "PSV_A_001"
        last = ids[-1]
        m = re.search(r'(\d+)$', last)
        if m:
            prefix = last[:m.start()]
            num    = int(m.group(1)) + 1
            width  = len(m.group(1))
            return f"{prefix}{num:0{width}d}"
        return last + "_1"
    except Exception:
        return "PSV_A_001"


def fetch_rank_table_display():
    """Fetch Setting!O1:R5 and return a clean English list grouped by rank.
    Row 1 = headers, rows 2-5 = data tiers."""
    if _HAS_API:
        result = api_fetch_rank_table_display()
        if result is not None:
            return result
        logging.warning("API api_fetch_rank_table_display() failed, falling back to gspread")
    try:
        rows = setting_sh.get("O1:R5")
        if not rows or len(rows) < 2:
            return "_(no data)_"
        warrior_lines  = []
        master_lines   = []
        immortal_lines = []
        for row in rows[1:]:
            if len(row) < 4:
                continue
            try:
                amt = _int(row[0])
                if amt == 0:
                    continue
                w = _int(row[1])
                m = _int(row[2])
                i = _int(row[3])
                if w > 0:
                    warrior_lines.append(f"  Top-up {amt:,} Ks \u2192 *+{w} bonus mins*")
                if m > 0:
                    master_lines.append(f"  Top-up {amt:,} Ks \u2192 *+{m} bonus mins*")
                if i > 0:
                    immortal_lines.append(f"  Top-up {amt:,} Ks \u2192 *+{i} bonus mins*")
            except Exception:
                continue
        sections = []
        if warrior_lines:
            sections.append("\u2694\ufe0f *Warrior*\n" + "\n".join(warrior_lines))
        if master_lines:
            sections.append("\U0001f3c5 *Master*\n" + "\n".join(master_lines))
        if immortal_lines:
            sections.append("\U0001f48e *Immortal*\n" + "\n".join(immortal_lines))
        return "\n\n".join(sections) if sections else "_(no data)_"
    except Exception:
        return "_(fetch error)_"


def get_top_up_suggestion(rank, bonus_table):
    """Return (suggested_amount, bonus_mins) for the given rank — highest bonus tier."""
    rank_col = {"Warrior": 1, "Master": 2, "Immortal": 3}
    col      = rank_col.get(display_rank(rank), 1)
    best_amt, best_bonus = 0, 0
    for (threshold, w, m, i) in bonus_table:
        bonus = (w, m, i)[col - 1]
        if bonus > best_bonus:
            best_bonus = bonus
            best_amt   = threshold
    return best_amt, best_bonus


def today_str():
    return now_mmt().strftime("%-m/%-d/%Y")


def step_hdr(step: int, total: int, label: str) -> str:
    """Return a Form Wizard progress header for every prompt message."""
    filled = "▰" * step
    empty  = "▱" * (total - step)
    return f"*{label}*\n`{filled}{empty}` _({step}/{total})_\n━━━━━━━━━━━━━━━━━━\n"


# ─────────────────────────────────────────
#  RECEIPT HELPERS
# ─────────────────────────────────────────
RECEIPTS_DIR = Path(__file__).parent / "receipts"
RECEIPTS_DIR.mkdir(exist_ok=True)


_API_KEY = os.environ.get("API_KEY", "")

def _api_base() -> str:
    """Return the API server base URL (no trailing slash), or empty string if not configured."""
    return os.environ.get("API_BASE_URL", "").rstrip("/")


def save_receipt_json(voucher_id: str, data: dict) -> None:
    """Persist receipt data locally and push to API server."""
    safe_id = voucher_id.replace("/", "-").replace("\\", "-")
    path = RECEIPTS_DIR / f"{safe_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    base = _api_base()
    if not base:
        return
    try:
        import urllib.request
        secret = os.environ.get("RECEIPT_SECRET", "")
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{base}/api/receipt",
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "x-receipt-secret": secret,
                "X-API-Key": _API_KEY,
            },
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        logging.warning("Failed to push receipt to API server: %s", e)


def get_receipt_url(voucher_id: str) -> str:
    """Return the public receipt URL or empty string if API_BASE_URL not set."""
    import os
    base = os.environ.get("RECEIPT_BASE_URL", "").rstrip("/")
    if not base:
        base = _api_base()
    if not base:
        return ""
    safe_id = voucher_id.replace("/", "-").replace("\\", "-")
    return f"{base}/api/receipt/{safe_id}"


def get_receipt_kb(voucher_id: str):
    """Return InlineKeyboardMarkup with a 🧾 Print Receipt button, or None if no domain set."""
    url = get_receipt_url(voucher_id)
    if not url:
        return None
    return InlineKeyboardMarkup([[InlineKeyboardButton("🧾 Print Receipt", url=url)]])



# ── Import all handlers so they're accessible from bot package ──


# ── PIN-then-action wrapper ──
async def _pin_then(after: str, label: str, update, context):
    """Store target action, prompt for PIN, return ADMIN_PIN state."""
    context.user_data["_after_pin"] = after
    await update.message.reply_text(
        f"\U0001f510 *{label}* PIN \u101b\u102d\u102f\u1000\u103a\u1011\u100a\u1037\u103a\u1015\u102b -",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ADMIN_PIN


# ── Payment Methods Fetcher ──
def fetch_payment_methods():
    """Return list of payment method options, with API-backed fallback."""
    try:
        data = _replit_get("sheets/payment-methods")
        if isinstance(data, dict) and "methods" in data:
            return data["methods"]
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return list(PAY_METHODS)


# constants imported by bot package itself
# helpers imported by bot package itself
# Handlers imported lazily to break circular dependency
_HANDLER_MODULES = {}
def _get_handler(hname):
    if hname not in _HANDLER_MODULES:
        import importlib
        _HANDLER_MODULES[hname] = importlib.import_module(f"bot.handlers.{hname}")
    return _HANDLER_MODULES[hname]
# main() is imported from bot.app directly by main.py — avoid circular import


# ── Lazy handler function exports (break circular import) ──
def cmd_cancel(*args, **kwargs):
    return _get_handler("commands").cmd_cancel(*args, **kwargs)

def prompt_discount(*args, **kwargs):
    return _get_handler("discount").prompt_discount(*args, **kwargs)

def show_main_menu(*args, **kwargs):
    return _get_handler("main_menu").show_main_menu(*args, **kwargs)

def show_console_menu(*args, **kwargs):
    return _get_handler("console").show_console_menu(*args, **kwargs)

def show_admin_menu(*args, **kwargs):
    return _get_handler("admin").show_admin_menu(*args, **kwargs)

def cmd_setattend(*args, **kwargs):
    return _get_handler("attendance").cmd_setattend(*args, **kwargs)

def cmd_setattend_cmd(*args, **kwargs):
    return _get_handler("attendance").cmd_setattend_cmd(*args, **kwargs)

def cmd_staff_kpi(*args, **kwargs):
    return _get_handler("broadcast").cmd_staff_kpi(*args, **kwargs)

def show_game_menu(*args, **kwargs):
    return _get_handler("games").show_game_menu(*args, **kwargs)

def cmd_payroll(*args, **kwargs):
    return _get_handler("payroll").cmd_payroll(*args, **kwargs)

def prompt_kpay(*args, **kwargs):
    return _get_handler("sales").prompt_kpay(*args, **kwargs)

def prompt_book_console(*args, **kwargs):
    return _get_handler("booking").prompt_book_console(*args, **kwargs)

def prompt_end_session(*args, **kwargs):
    return _get_handler("booking").prompt_end_session(*args, **kwargs)
def show_stock_menu(*args, **kwargs):
    return _get_handler("stock").show_stock_menu(*args, **kwargs)
