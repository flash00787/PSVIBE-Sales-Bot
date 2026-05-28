"""
Telegram Finance Bot — Full Implementation
Logs personal/business transactions into Google Sheets and provides rich analytics.
"""
from __future__ import annotations

import asyncio
import calendar
import csv
import fcntl
import functools
import io
import logging
import os
import re
import socket
import time
import threading
from datetime import datetime, timedelta, date
from logging.handlers import RotatingFileHandler
from zoneinfo import ZoneInfo

import gspread
from gspread import Cell
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, BotCommand
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters,
    PicklePersistence, ContextTypes, JobQueue
)
from telegram.constants import ParseMode

load_dotenv()

# ─── Socket timeout ────────────────────────────────────────────────────────────
socket.setdefaulttimeout(15)

# ─── Logging ───────────────────────────────────────────────────────────────────
os.makedirs("bot", exist_ok=True)
logging.basicConfig(level=logging.INFO)
_log_handler = RotatingFileHandler(
    "bot/bot_status.log", maxBytes=5 * 1024 * 1024, backupCount=3
)
_log_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logging.getLogger().addHandler(_log_handler)
logger = logging.getLogger(__name__)

# ─── Constants ─────────────────────────────────────────────────────────────────
SHEET_ID        = os.environ.get("SHEET_ID", "")
SETTINGS_SHEET  = "Settings"
LOG_SHEET       = "Transaction_Log"
OB_SHEET        = "Opening_Balances"
SAAS_SHEET      = "Saas_Tracker"
TZ              = ZoneInfo(os.environ.get("BOT_TIMEZONE", "Asia/Yangon"))
GOOGLE_SCOPES   = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SEP  = "━━━━━━━━━━━━━━━━━━━━"
BACK = "__back__"
SCOPE_MAP = {
    "Business Expense": ("🏢", "Business"),
    "Personal Expense": ("👤", "Personal"),
    "Income":           ("💵", "Income"),
}
OB_TYPE_EMOJI = {
    "Account":    "💳",
    "Business":   "🏢",
    "Receivable": "📥",
    "Payable":    "📤",
}
HISTORY_PAGE_SIZE   = 5
SETTINGS_CACHE_TTL  = 60
ACCT_CACHE_TTL      = 60
TX_ROWS_CACHE_TTL   = 60
SUMMARY_CACHE_TTL   = 60
OPENING_CACHE_TTL   = 120
FX_CACHE_TTL        = 60
_GSPREAD_CLIENT_TTL = 1800
_SHEETS_TIMEOUT     = 25.0

ALLOWED_USER_IDS: set[int] = {
    int(x) for x in os.environ.get("ALLOWED_USER_IDS", "").split(",")
    if x.strip().isdigit()
}

EXCLUDED_OB_TYPES = frozenset({"payable", "receivable", "asset", "real estate", "business"})
SPENDABLE_OB_TYPES = frozenset({
    "account", "card", "credit", "debit", "visa",
    "mastercard", "wallet", "cash", "bank", "pay", "mobile"
})

# ─── Conversation States ───────────────────────────────────────────────────────
SCOPE_STEP, PROJECT_STEP, CATEGORY_STEP, ACCOUNT_STEP = range(4)
OB_SELECT_TYPE, OB_ENTER_AMOUNT, OB_ENTER_NAME       = range(4, 7)
XFER_AMOUNT, XFER_FROM, XFER_TO                       = range(7, 10)
BUDGET_AMOUNT, BUDGET_CONFIRM                         = range(10, 12)
REMIND_TIME                                           = 12
PHOTO_SCOPE, PHOTO_PROJECT, PHOTO_CATEGORY, PHOTO_ACC = range(13, 17)
SETTLE_TYPE, SETTLE_PERSON, SETTLE_AMT, SETTLE_ACC    = range(17, 21)
EXPENSE_AMT                                           = 21
BORROW_PERSON, BORROW_NAME, BORROW_AMT, BORROW_ACC   = range(22, 26)
LEND_PERSON, LEND_NAME, LEND_AMT, LEND_ACC           = range(26, 30)

# ─── gspread Client Singleton ──────────────────────────────────────────────────
_gspread_client     = None
_gspread_client_ts  = 0.0
# Resolved at startup in __main__; default works when run directly from bot/
_SA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "service_account.json")


def _sheet_client() -> gspread.Client:
    global _gspread_client, _gspread_client_ts
    now = time.time()
    with _cache_lock:
        if _gspread_client and (now - _gspread_client_ts) < _GSPREAD_CLIENT_TTL:
            return _gspread_client
    creds = Credentials.from_service_account_file(_SA_PATH, scopes=GOOGLE_SCOPES)
    client = gspread.authorize(creds)
    with _cache_lock:
        _gspread_client    = client
        _gspread_client_ts = time.time()
    return client


def _get_sheet(tab: str):
    return _sheet_client().open_by_key(SHEET_ID).worksheet(tab)


# ─── Retry Decorator ──────────────────────────────────────────────────────────
def _gsheet_retry(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        exc = None
        for attempt in range(3):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                exc = e
                msg = str(e)
                if any(t in msg for t in ("429", "quota", "timeout", "deadline", "502", "503")):
                    time.sleep(2 ** attempt)
                else:
                    raise
        raise exc
    return wrapper


# ─── Async Sheets Wrapper ─────────────────────────────────────────────────────
async def _sh(fn, *args, timeout: float = _SHEETS_TIMEOUT):
    try:
        return await asyncio.wait_for(asyncio.to_thread(fn, *args), timeout=timeout)
    except asyncio.TimeoutError:
        raise RuntimeError("Google Sheets API timed out — try again.")


# ─── Caches ───────────────────────────────────────────────────────────────────
_cache_lock = threading.Lock()

_settings_cache: dict | None = None
_settings_cache_ts            = 0.0
_acct_cache: dict | None      = None
_acct_cache_ts                = 0.0
_tx_rows_cache: list | None   = None
_tx_rows_cache_ts             = 0.0
_monthly_cache: dict          = {}
_monthly_cache_ts: dict       = {}
_opening_cache: dict | None   = None
_opening_cache_ts             = 0.0
_fx_cache: dict | None        = None
_fx_cache_ts                  = 0.0


def invalidate_all_caches():
    global _settings_cache, _settings_cache_ts
    global _acct_cache, _acct_cache_ts
    global _tx_rows_cache, _tx_rows_cache_ts
    global _monthly_cache, _monthly_cache_ts
    global _opening_cache, _opening_cache_ts
    global _fx_cache, _fx_cache_ts
    with _cache_lock:
        _settings_cache    = None;  _settings_cache_ts  = 0.0
        _acct_cache        = None;  _acct_cache_ts      = 0.0
        _tx_rows_cache     = None;  _tx_rows_cache_ts   = 0.0
        _monthly_cache     = {};    _monthly_cache_ts   = {}
        _opening_cache     = None;  _opening_cache_ts   = 0.0
        _fx_cache          = None;  _fx_cache_ts        = 0.0


# ─── Date Parser ──────────────────────────────────────────────────────────────
_GSHEET_EPOCH = datetime(1899, 12, 30).date()

_DATE_FMTS = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]


def _parse_date_str(s: str) -> date | None:
    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            pass
    return None


def _parse_row_date(row) -> date | None:
    for raw in (row[3] if len(row) > 3 else None, row[1] if len(row) > 1 else None):
        if raw is None or raw == "":
            continue
        if isinstance(raw, (int, float)):
            return _GSHEET_EPOCH + timedelta(days=int(raw))
        d = _parse_date_str(str(raw))
        if d:
            return d
    return None


# ─── Amount Parser ────────────────────────────────────────────────────────────
_MULT = {
    "k": 1_000, "rb": 1_000,
    "jt": 1_000_000, "m": 1_000_000,
    "b": 1_000_000_000, "bn": 1_000_000_000,
}


def parse_amount(text: str) -> float | None:
    text = re.sub(r'^(?:mmk|usd|thb|idr|sgd|[฿$])\s*', '', text.strip(), flags=re.I)
    text = text.replace(",", "").replace("_", "")
    m = re.match(r'^([0-9][0-9.]*)\s*(b|bn|k|rb|jt|m)?$', text, re.I)
    if not m:
        return None
    suffix = (m.group(2) or "").lower()
    return float(m.group(1)) * _MULT.get(suffix, 1)


# ─── Authorization Decorator ──────────────────────────────────────────────────
def authorized(fn):
    @functools.wraps(fn)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if ALLOWED_USER_IDS:
            uid = update.effective_user.id if update.effective_user else None
            if uid not in ALLOWED_USER_IDS:
                await update.effective_message.reply_text("⛔ Not authorized.")
                return ConversationHandler.END
        return await fn(update, context)
    return wrapper


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _month_progress(now: datetime) -> str:
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    pct   = now.day / days_in_month
    bar   = "█" * round(10 * pct) + "░" * (10 - round(10 * pct))
    return f"📆 Day {now.day}/{days_in_month}  {bar}  {pct*100:.0f}%"


def _bar(value: float, max_val: float, width: int = 12) -> str:
    if max_val <= 0:
        return "░" * width
    filled = round(width * value / max_val)
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def _fmt(n: float) -> str:
    return f"{n:,.0f}"


def _sign_emoji(n: float) -> str:
    if n > 0:
        return "🟢"
    if n < 0:
        return "🔴"
    return "⚫"


def _kb(rows: list[list[str | InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(t, callback_data=t) if isinstance(t, str) else t for t in row]
         for row in rows]
    )


def _btn(label: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(label, callback_data=data)


# ─── Google Sheets Data Functions ─────────────────────────────────────────────

@_gsheet_retry
def _fetch_settings() -> dict:
    ws   = _get_sheet(SETTINGS_SHEET)
    rows = ws.get_all_values()
    if not rows:
        return {}
    data_rows = rows[1:]
    accounts   = [r[0].strip() for r in data_rows if len(r) > 0 and r[0].strip()]
    biz_cats   = [r[2].strip() for r in data_rows if len(r) > 2 and r[2].strip()]
    per_cats   = [r[3].strip() for r in data_rows if len(r) > 3 and r[3].strip()]
    projects   = [r[4].strip() for r in data_rows if len(r) > 4 and r[4].strip()]
    inc_cats   = [r[5].strip() for r in data_rows if len(r) > 5 and r[5].strip()]
    fx_rates: dict[str, float] = {}
    for r in data_rows:
        if len(r) > 11 and r[10].strip() and r[11].strip():
            try:
                fx_rates[r[10].strip().upper()] = float(r[11].strip())
            except ValueError:
                pass
    return {
        "accounts":  accounts,
        "biz_cats":  biz_cats,
        "per_cats":  per_cats,
        "projects":  projects,
        "inc_cats":  inc_cats,
        "fx_rates":  fx_rates,
    }


def get_settings() -> dict:
    global _settings_cache, _settings_cache_ts
    now = time.time()
    with _cache_lock:
        if _settings_cache is not None and (now - _settings_cache_ts) < SETTINGS_CACHE_TTL:
            return _settings_cache
    result = _fetch_settings()
    with _cache_lock:
        _settings_cache    = result
        _settings_cache_ts = time.time()
    return result


def get_fx_rates() -> dict[str, float]:
    global _fx_cache, _fx_cache_ts
    now = time.time()
    with _cache_lock:
        if _fx_cache is not None and (now - _fx_cache_ts) < FX_CACHE_TTL:
            return _fx_cache
    result = get_settings().get("fx_rates", {})
    with _cache_lock:
        _fx_cache    = result
        _fx_cache_ts = time.time()
    return result


@_gsheet_retry
def _fetch_tx_rows() -> list:
    ws   = _get_sheet(LOG_SHEET)
    rows = ws.get_all_values(value_render_option="UNFORMATTED_VALUE")
    return rows[1:] if rows else []


def get_tx_rows() -> list:
    global _tx_rows_cache, _tx_rows_cache_ts
    now = time.time()
    with _cache_lock:
        if _tx_rows_cache is not None and (now - _tx_rows_cache_ts) < TX_ROWS_CACHE_TTL:
            return _tx_rows_cache
    result = _fetch_tx_rows()
    with _cache_lock:
        _tx_rows_cache    = result
        _tx_rows_cache_ts = time.time()
    return result


@_gsheet_retry
def _fetch_opening_balances() -> dict:
    ws   = _get_sheet(OB_SHEET)
    rows = ws.get_all_values()
    if not rows:
        return {}
    result: dict[str, float]   = {}
    currencies: dict[str, str] = {}
    for row in rows[1:]:
        if len(row) < 4:
            continue
        ob_type = str(row[1]).strip().lower()
        if not ob_type:
            continue
        if ob_type in EXCLUDED_OB_TYPES:
            continue
        if not any(t in ob_type for t in SPENDABLE_OB_TYPES):
            continue
        name = str(row[2]).strip()
        if not name:
            continue
        try:
            amt = float(row[3])
        except (ValueError, TypeError):
            continue
        result[name] = result.get(name, 0.0) + amt
        if len(row) > 5 and row[5].strip():
            currencies[name] = row[5].strip().upper()
    return {"balances": result, "currencies": currencies}


def get_opening_balances() -> dict:
    global _opening_cache, _opening_cache_ts
    now = time.time()
    with _cache_lock:
        if _opening_cache is not None and (now - _opening_cache_ts) < OPENING_CACHE_TTL:
            return _opening_cache
    result = _fetch_opening_balances()
    with _cache_lock:
        _opening_cache    = result
        _opening_cache_ts = time.time()
    return result


@_gsheet_retry
def _fetch_all_ob_rows() -> list:
    ws   = _get_sheet(OB_SHEET)
    rows = ws.get_all_values()
    return rows[1:] if rows else []


def get_account_balances() -> dict[str, dict]:
    ob_data    = get_opening_balances()
    opening    = ob_data.get("balances", {})
    currencies = ob_data.get("currencies", {})
    tx_rows    = get_tx_rows()
    tx_in: dict[str, float]  = {}
    tx_out: dict[str, float] = {}
    for row in tx_rows:
        if len(row) < 9:
            continue
        tx_type = str(row[4]).strip() if len(row) > 4 else ""
        acc_from = str(row[6]).strip() if len(row) > 6 else ""
        acc_to   = str(row[7]).strip() if len(row) > 7 else ""
        try:
            amt = float(row[8]) if len(row) > 8 and row[8] != "" else 0.0
        except (ValueError, TypeError):
            amt = 0.0
        if acc_from:
            tx_out[acc_from] = tx_out.get(acc_from, 0.0) + amt
        if acc_to:
            tx_in[acc_to] = tx_in.get(acc_to, 0.0) + amt
    all_accts = set(opening.keys()) | set(tx_in.keys()) | set(tx_out.keys())
    result: dict[str, dict] = {}
    for acc in all_accts:
        ob      = opening.get(acc, 0.0)
        balance = ob + tx_in.get(acc, 0.0) - tx_out.get(acc, 0.0)
        cur = currencies.get(acc, "MMK")
        if cur == "MMK":
            name_upper = acc.upper()
            for code in ["USD", "THB", "SGD", "IDR"]:
                if code in name_upper:
                    cur = code
                    break
            for sym, code in [("$", "USD"), ("฿", "THB")]:
                if sym in acc:
                    cur = code
                    break
        result[acc] = {"balance": balance, "currency": cur}
    return result


def get_monthly_summary(year: int, month: int) -> dict:
    global _monthly_cache, _monthly_cache_ts
    key = f"{year}-{month:02d}"
    now = time.time()
    with _cache_lock:
        if key in _monthly_cache and (now - _monthly_cache_ts.get(key, 0)) < SUMMARY_CACHE_TTL:
            return _monthly_cache[key]
    # Compute summary outside lock — get_tx_rows() acquires its own lock
    target_prefix = f"{year}-{month:02d}"
    tx_rows = get_tx_rows()
    total_income   = 0.0
    total_expense  = 0.0
    biz_expense    = 0.0
    per_expense    = 0.0
    cat_totals: dict[str, float]  = {}
    proj_totals: dict[str, float] = {}
    tx_count = 0
    for row in tx_rows:
        if len(row) < 9:
            continue
        month_col = str(row[3]).strip() if len(row) > 3 else ""
        if month_col:
            if month_col != target_prefix:
                continue
        else:
            d = _parse_row_date(row)
            if d is None or d.year != year or d.month != month:
                continue
        tx_type = str(row[4]).strip()
        if tx_type == "Transfer":
            continue
        try:
            amt = float(row[8]) if row[8] != "" else 0.0
        except (ValueError, TypeError):
            amt = 0.0
        scope    = str(row[13]).strip() if len(row) > 13 else ""
        category = str(row[5]).strip()  if len(row) > 5  else ""
        project  = str(row[9]).strip()  if len(row) > 9  else ""
        if tx_type == "Income" or scope == "Income":
            total_income += amt
        else:
            total_expense += amt
            if scope == "Business":
                biz_expense += amt
            else:
                per_expense += amt
        if category:
            cat_totals[category] = cat_totals.get(category, 0.0) + amt
        if project:
            proj_totals[project] = proj_totals.get(project, 0.0) + amt
        tx_count += 1
    summary = {
        "income":      total_income,
        "expense":     total_expense,
        "net":         total_income - total_expense,
        "biz_expense": biz_expense,
        "per_expense": per_expense,
        "categories":  cat_totals,
        "projects":    proj_totals,
        "tx_count":    tx_count,
    }
    with _cache_lock:
        _monthly_cache[key]    = summary
        _monthly_cache_ts[key] = time.time()
    return summary


@_gsheet_retry
def _do_save_transaction(data: dict, row_number: int | None = None):
    ws       = _get_sheet(LOG_SHEET)
    date_str = data.get("date", datetime.now(tz=TZ).strftime("%Y-%m-%d"))
    if row_number is None:
        # Use col B (date) to find last real data row — avoids being fooled
        # by ARRAYFORMULA rows in cols A, C, D, K, L, M which extend far down
        col_b = ws.col_values(2)  # 1-indexed, col B
        # Find last non-empty cell in col B (skip header row 1)
        last_data_row = 1
        for i, val in enumerate(col_b):
            if val.strip():
                last_data_row = i + 1  # convert to 1-indexed
        row_number = last_data_row + 1
    cells = [
        Cell(row_number, 2,  date_str),
        Cell(row_number, 5,  data.get("type", "Expense")),
        Cell(row_number, 6,  data.get("category", "")),
        Cell(row_number, 7,  data.get("acc_from", "")),
        Cell(row_number, 8,  data.get("acc_to", "")),
        Cell(row_number, 9,  data.get("amount", 0)),
        Cell(row_number, 10, data.get("project", "")),
        Cell(row_number, 14, data.get("scope", "")),
    ]
    ws.update_cells(cells, value_input_option="USER_ENTERED")
    return row_number


def save_transaction(data: dict, row_number: int | None = None) -> int:
    rn = _do_save_transaction(data, row_number)
    invalidate_all_caches()
    return rn


@_gsheet_retry
def _do_save_opening_balance(entry: dict):
    ws   = _get_sheet(OB_SHEET)
    date_str = entry.get("date", datetime.now(tz=TZ).strftime("%Y-%m-%d"))
    ws.append_row(
        [date_str, entry["ob_type"], entry["name"],
         entry["amount"], entry.get("notes", ""), entry.get("currency", "")],
        value_input_option="USER_ENTERED"
    )


def save_opening_balance(entry: dict):
    _do_save_opening_balance(entry)
    global _opening_cache, _opening_cache_ts
    with _cache_lock:
        _opening_cache    = None
        _opening_cache_ts = 0.0


@_gsheet_retry
def _do_delete_last_tx(row_number: int):
    ws = _get_sheet(LOG_SHEET)
    cells = [Cell(row_number, c, "") for c in [2, 5, 6, 7, 8, 9, 10, 14]]
    ws.update_cells(cells)


def delete_tx_row(row_number: int):
    _do_delete_last_tx(row_number)
    invalidate_all_caches()


@_gsheet_retry
def _do_update_fx_rate(currency: str, rate: float):
    ws   = _get_sheet(SETTINGS_SHEET)
    rows = ws.get_all_values()
    for i, row in enumerate(rows[1:], start=2):
        if len(row) > 10 and row[10].strip().upper() == currency.upper():
            ws.update_cell(i, 12, rate)
            return
    ws.append_row(["", "", "", "", "", "", "", "", "", "", currency.upper(), rate],
                  value_input_option="USER_ENTERED")


def update_fx_rate(currency: str, rate: float):
    _do_update_fx_rate(currency, rate)
    global _fx_cache, _fx_cache_ts, _settings_cache, _settings_cache_ts
    with _cache_lock:
        _fx_cache          = None;  _fx_cache_ts          = 0.0
        _settings_cache    = None;  _settings_cache_ts    = 0.0


@_gsheet_retry
def _fetch_saas_rows() -> list:
    ws   = _get_sheet(SAAS_SHEET)
    rows = ws.get_all_values()
    return rows[1:] if rows else []


def get_saas_rows() -> list:
    return _fetch_saas_rows()


# ─── Cache Warmer (Async) ─────────────────────────────────────────────────────
async def _async_cache_warmer_loop():
    """Async background warmer — runs inside the main event loop.

    Periodically expires caches and re-fetches them via _sh(), which safely
    dispatches sync gspread calls into the default thread-pool executor.
    """
    while True:
        try:
            invalidate_all_caches()
            await _sh(get_settings)
            await _sh(get_tx_rows)
            await _sh(get_opening_balances)
            now_dt = datetime.now(tz=TZ)
            await _sh(get_monthly_summary, now_dt.year, now_dt.month)
        except Exception as e:
            logger.warning(f"Cache warmer error: {e}")
            global _gspread_client, _gspread_client_ts
            with _cache_lock:
                _gspread_client    = None
                _gspread_client_ts = 0.0
        await asyncio.sleep(90)


# ─── UI Keyboard Builders ─────────────────────────────────────────────────────
def _accounts_kb(prefix: str = "") -> InlineKeyboardMarkup:
    settings = get_settings()
    accts    = settings.get("accounts", [])
    rows_kb  = []
    for i in range(0, len(accts), 2):
        row = [_btn(accts[i], f"{prefix}{accts[i]}")]
        if i + 1 < len(accts):
            row.append(_btn(accts[i + 1], f"{prefix}{accts[i + 1]}"))
        rows_kb.append(row)
    rows_kb.append([_btn("🔙 Cancel", "/cancel")])
    return InlineKeyboardMarkup(rows_kb)


def _categories_kb(cats: list[str], prefix: str = "") -> InlineKeyboardMarkup:
    rows_kb = []
    for i in range(0, len(cats), 2):
        row = [_btn(cats[i], f"{prefix}{cats[i]}")]
        if i + 1 < len(cats):
            row.append(_btn(cats[i + 1], f"{prefix}{cats[i + 1]}"))
        rows_kb.append(row)
    rows_kb.append([_btn("🔙 Back", BACK)])
    return InlineKeyboardMarkup(rows_kb)


def _projects_kb(projects: list[str]) -> InlineKeyboardMarkup:
    rows_kb = []
    for i in range(0, len(projects), 2):
        row = [_btn(projects[i], f"proj_{projects[i]}")]
        if i + 1 < len(projects):
            row.append(_btn(projects[i + 1], f"proj_{projects[i + 1]}"))
        rows_kb.append(row)
    rows_kb.append([_btn("➖ No Project", "proj_none"), _btn("🔙 Back", BACK)])
    return InlineKeyboardMarkup(rows_kb)


# ─── Transaction Card ─────────────────────────────────────────────────────────
def _tx_card(row_num: int, row: list) -> str:
    try:
        amt      = float(row[8]) if len(row) > 8 and row[8] != "" else 0.0
    except Exception:
        amt      = 0.0
    category = str(row[5]).strip()  if len(row) > 5  else "?"
    scope    = str(row[13]).strip() if len(row) > 13 else ""
    tx_type  = str(row[4]).strip()  if len(row) > 4  else ""
    acc_from = str(row[6]).strip()  if len(row) > 6  else ""
    acc_to   = str(row[7]).strip()  if len(row) > 7  else ""
    project  = str(row[9]).strip()  if len(row) > 9  else ""
    d = _parse_row_date(row)
    date_str = d.strftime("%d %b %Y") if d else "?"
    color    = "🔴" if tx_type not in ("Income",) else "🟢"
    lines = [
        f"{color} <b>#{row_num}</b>  {category}  ·  <b>{_fmt(amt)}</b>",
        f"   {scope}  ·  {tx_type}  ·  {date_str}",
    ]
    if tx_type == "Transfer" and acc_from and acc_to:
        lines.append(f"   💳 {acc_from}  →  {acc_to}")
    elif acc_from or acc_to:
        lines.append(f"   💳 {acc_from or acc_to}")
    if project:
        lines.append(f"   📁 {project}")
    return "\n".join(lines)


# ─── Wizard Step Indicator ────────────────────────────────────────────────────
def _step_dots(step: int, total: int) -> str:
    """●●○○  2/4  — compact wizard progress line."""
    return "●" * step + "○" * (total - step) + f"  {step}/{total}"


# ─── Transaction Breadcrumb ───────────────────────────────────────────────────
def _tx_crumb(tx: dict) -> str:
    """Show user their choices so far at each step of the transaction flow."""
    scope_map = {
        "Business Expense": "🏢 Business",
        "Personal Expense": "👤 Personal",
        "Income":           "💵 Income",
    }
    parts = [f"<b>{_fmt(tx.get('amount', 0))}</b>"]
    sk = tx.get("scope_key", "")
    if sk:
        parts.append(scope_map.get(sk, sk))
    proj = tx.get("project", "")
    if proj:
        parts.append(f"📁 {proj}")
    cat = tx.get("category", "")
    if cat:
        parts.append(f"🏷 {cat}")
    return "  ›  ".join(parts)


# ─── Main Transaction Flow ────────────────────────────────────────────────────
@authorized
async def tx_amount_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.strip()
    parts = text.split(None, 1)
    raw_amt = parts[0]
    amt = parse_amount(raw_amt)
    if amt is None or amt <= 0:
        await update.effective_message.reply_text("❌ Invalid amount. Try: 50000, 50k, 1.5m")
        return ConversationHandler.END
    context.user_data["tx"] = {"amount": amt, "raw": text}
    settings = await _sh(get_settings)
    has_projects = bool(settings.get("projects", []))
    total = 4 if has_projects else 3
    context.user_data["tx"]["_steps"] = total
    hint_cat = ""
    if len(parts) > 1:
        hint = parts[1].strip().lower()
        all_cats = (settings.get("biz_cats", []) + settings.get("per_cats", []) +
                    settings.get("inc_cats", []))
        matches = [c for c in all_cats if hint in c.lower()]
        if len(matches) == 1:
            hint_cat = matches[0]
    if hint_cat:
        context.user_data["tx"]["hint_cat"] = hint_cat
    kb = InlineKeyboardMarkup([[
        _btn("🏢 Business", "scope_Business Expense"),
        _btn("👤 Personal", "scope_Personal Expense"),
        _btn("💵 Income",   "scope_Income"),
    ]])
    await update.effective_message.reply_text(
        f"💰 <b>{_fmt(amt)} MMK</b>\n{SEP}\n{_step_dots(1, total)}  ·  Type?",
        reply_markup=kb, parse_mode=ParseMode.HTML
    )
    return SCOPE_STEP


@authorized
async def expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    text = " ".join(args)
    parts = text.split(None, 1)
    if not parts:
        await update.effective_message.reply_text("Usage: /expense 50k food")
        return ConversationHandler.END
    amt = parse_amount(parts[0])
    if amt is None:
        await update.effective_message.reply_text("❌ Invalid amount.")
        return ConversationHandler.END
    context.user_data["tx"] = {"amount": amt, "raw": text}
    settings = await _sh(get_settings)
    has_projects = bool(settings.get("projects", []))
    total = 4 if has_projects else 3
    context.user_data["tx"]["_steps"] = total
    if len(parts) > 1:
        hint = parts[1].strip().lower()
        all_cats = settings.get("biz_cats", []) + settings.get("per_cats", [])
        matches = [c for c in all_cats if hint in c.lower()]
        if len(matches) == 1:
            context.user_data["tx"]["hint_cat"] = matches[0]
    kb = InlineKeyboardMarkup([[
        _btn("🏢 Business", "scope_Business Expense"),
        _btn("👤 Personal", "scope_Personal Expense"),
    ]])
    await update.effective_message.reply_text(
        f"💰 <b>{_fmt(amt)} MMK</b>\n{SEP}\n{_step_dots(1, total)}  ·  Type?",
        reply_markup=kb, parse_mode=ParseMode.HTML
    )
    return SCOPE_STEP


async def tx_scope_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    await q.answer()
    scope_key = q.data.replace("scope_", "")
    context.user_data["tx"]["scope_key"] = scope_key
    settings = await _sh(get_settings)
    projects = settings.get("projects", [])
    if not projects:
        context.user_data["tx"]["project"] = ""
        return await _ask_category(update, context)
    tx    = context.user_data["tx"]
    total = tx.get("_steps", 4)
    crumb = _tx_crumb(tx)
    await q.edit_message_text(
        f"{crumb}\n{SEP}\n{_step_dots(2, total)}  ·  Project?",
        reply_markup=_projects_kb(projects), parse_mode=ParseMode.HTML
    )
    return PROJECT_STEP


async def tx_project_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == BACK:
        tx    = context.user_data.get("tx", {})
        amt   = tx.get("amount", 0.0)
        total = tx.get("_steps", 3)
        kb = InlineKeyboardMarkup([[
            _btn("🏢 Business", "scope_Business Expense"),
            _btn("👤 Personal", "scope_Personal Expense"),
            _btn("💵 Income",   "scope_Income"),
        ]])
        await q.edit_message_text(
            f"💰 <b>{_fmt(amt)} MMK</b>\n{SEP}\n{_step_dots(1, total)}  ·  Type?",
            reply_markup=kb, parse_mode=ParseMode.HTML
        )
        return SCOPE_STEP
    proj = "" if q.data == "proj_none" else q.data.replace("proj_", "")
    context.user_data["tx"]["project"] = proj
    return await _ask_category(update, context)


async def _ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q        = update.callback_query
    tx       = context.user_data["tx"]
    scope_key = tx.get("scope_key", "Personal Expense")
    settings = await _sh(get_settings)
    hint_cat = tx.get("hint_cat", "")
    if hint_cat:
        tx["category"] = hint_cat
        del tx["hint_cat"]
        return await _ask_account(update, context)
    if "Income" in scope_key:
        cats = settings.get("inc_cats", [])
    elif "Business" in scope_key:
        cats = settings.get("biz_cats", [])
    else:
        cats = settings.get("per_cats", [])
    if not cats:
        cats = ["Other"]
    total    = tx.get("_steps", 3)
    cat_step = total - 1
    crumb    = _tx_crumb(tx)
    await q.edit_message_text(
        f"{crumb}\n{SEP}\n{_step_dots(cat_step, total)}  ·  Category?",
        reply_markup=_categories_kb(cats, "cat_"), parse_mode=ParseMode.HTML
    )
    return CATEGORY_STEP


async def tx_category_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == BACK:
        settings = await _sh(get_settings)
        projects = settings.get("projects", [])
        if projects:
            tx    = context.user_data["tx"]
            total = tx.get("_steps", 4)
            crumb = _tx_crumb(tx)
            await q.edit_message_text(
                f"{crumb}\n{SEP}\n{_step_dots(2, total)}  ·  Project?",
                reply_markup=_projects_kb(projects), parse_mode=ParseMode.HTML
            )
            return PROJECT_STEP
        else:
            tx    = context.user_data.get("tx", {})
            amt   = tx.get("amount", 0.0)
            total = tx.get("_steps", 3)
            kb = InlineKeyboardMarkup([[
                _btn("🏢 Business", "scope_Business Expense"),
                _btn("👤 Personal", "scope_Personal Expense"),
                _btn("💵 Income",   "scope_Income"),
            ]])
            await q.edit_message_text(
                f"💰 <b>{_fmt(amt)} MMK</b>\n{SEP}\n{_step_dots(1, total)}  ·  Type?",
                reply_markup=kb, parse_mode=ParseMode.HTML
            )
            return SCOPE_STEP
    context.user_data["tx"]["category"] = q.data.replace("cat_", "")
    return await _ask_account(update, context)


async def _ask_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q        = update.callback_query
    tx       = context.user_data["tx"]
    scope_key = tx.get("scope_key", "Personal Expense")
    is_income = "Income" in scope_key
    settings = await _sh(get_settings)
    accts    = settings.get("accounts", [])
    if not accts:
        await q.edit_message_text(
            f"⚠️ <b>No accounts found</b>\n{SEP}\n"
            "Add accounts to <b>Settings</b> tab Column A and send /reload.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    total   = tx.get("_steps", 3)
    crumb   = _tx_crumb(tx)
    label   = "Receiving account?" if is_income else "Paying account?"
    rows_kb = []
    for i in range(0, len(accts), 2):
        row = [_btn(accts[i], f"acc_{accts[i]}")]
        if i + 1 < len(accts):
            row.append(_btn(accts[i + 1], f"acc_{accts[i + 1]}"))
        rows_kb.append(row)
    rows_kb.append([_btn("🔙 Back", BACK)])
    await q.edit_message_text(
        f"{crumb}\n{SEP}\n{_step_dots(total, total)}  ·  {label}",
        reply_markup=InlineKeyboardMarkup(rows_kb),
        parse_mode=ParseMode.HTML
    )
    return ACCOUNT_STEP


async def tx_account_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == BACK:
        return await _ask_category(update, context)
    account   = q.data.replace("acc_", "")
    tx        = context.user_data.get("tx", {})
    scope_key = tx.get("scope_key", "Personal Expense")
    amt       = tx.get("amount", 0.0)
    category  = tx.get("category", "")
    project   = tx.get("project", "")
    now       = datetime.now(tz=TZ)
    is_income = "Income" in scope_key
    is_biz    = "Business" in scope_key
    if is_income:
        scope    = "Income"
        tx_type  = "Income"
        acc_from = ""
        acc_to   = account
    else:
        scope    = "Business" if is_biz else "Personal"
        tx_type  = "Expense"
        acc_from = account
        acc_to   = ""
    data = {
        "date":     now.strftime("%Y-%m-%d"),
        "type":     tx_type,
        "category": category,
        "acc_from": acc_from,
        "acc_to":   acc_to,
        "amount":   amt,
        "project":  project,
        "scope":    scope,
    }
    try:
        row_num = await _sh(save_transaction, data)
        context.user_data["last_tx_row"] = row_num
        scope_emoji = "🏢" if is_biz else ("💵" if is_income else "👤")
        dot = "🟢" if is_income else "🔴"
        meta = f"{scope_emoji} {scope}  ·  {now.strftime('%d %b %Y')}"
        details = f"💳 {account}" + (f"  ·  📁 {project}" if project else "")
        msg = (
            f"✅ <b>Saved!</b>  <b>#{row_num}</b>\n{SEP}\n"
            f"{dot} <b>{category}</b>  —  <b>{_fmt(amt)} MMK</b>\n"
            f"   {meta}\n"
            f"   {details}"
        )
        kb = InlineKeyboardMarkup([[_btn("✏️ Edit", "edit_last"), _btn("🗑 Delete", "del_last")]])
        await q.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception as e:
        await q.edit_message_text(f"❌ Failed to save.\n{SEP}\n{str(e)[:200]}")
    context.user_data.pop("tx", None)
    return ConversationHandler.END


# ─── Opening Balance Flow ──────────────────────────────────────────────────────
@authorized
async def ob_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[
        _btn("💳 Account",    "ob_Account"),
        _btn("🏢 Business",   "ob_Business"),
    ], [
        _btn("📥 Receivable", "ob_Receivable"),
        _btn("📤 Payable",    "ob_Payable"),
    ]])
    await update.effective_message.reply_text(
        f"📊 <b>Opening Balance</b>\n{SEP}\nSelect type:",
        reply_markup=kb, parse_mode=ParseMode.HTML
    )
    return OB_SELECT_TYPE


async def ob_type_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ob_type = q.data.replace("ob_", "")
    context.user_data["ob"] = {"ob_type": ob_type}
    await q.edit_message_text(
        f"{OB_TYPE_EMOJI.get(ob_type, '📊')} <b>{ob_type}</b>\n{SEP}\nEnter amount:",
        parse_mode=ParseMode.HTML
    )
    return OB_ENTER_AMOUNT


async def ob_amount_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amt = parse_amount(update.effective_message.text.strip())
    if amt is None:
        await update.effective_message.reply_text("❌ Invalid amount. Try again:")
        return OB_ENTER_AMOUNT
    context.user_data["ob"]["amount"] = amt
    ob_type = context.user_data["ob"]["ob_type"]
    prompt = {
        "Account":    "Account name (e.g. KPay, AYA Visa):",
        "Business":   "Business name:",
        "Receivable": "Person or entity name:",
        "Payable":    "Person or entity name:",
    }.get(ob_type, "Name:")
    await update.effective_message.reply_text(f"✏️ {prompt}")
    return OB_ENTER_NAME


async def ob_name_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_message.text.strip()
    if not name:
        await update.effective_message.reply_text("❌ Name is required. Try again:")
        return OB_ENTER_NAME
    ob     = context.user_data.get("ob", {})
    ob_type = ob.get("ob_type", "Account")
    amt    = ob.get("amount", 0.0)
    entry  = {
        "date":    datetime.now(tz=TZ).strftime("%Y-%m-%d"),
        "ob_type": ob_type,
        "name":    name,
        "amount":  amt,
        "notes":   "",
        "currency": "",
    }
    try:
        await _sh(save_opening_balance, entry)
        await update.effective_message.reply_text(
            f"✅ <b>Opening balance saved</b>\n{SEP}\n"
            f"{OB_TYPE_EMOJI.get(ob_type, '📊')} {ob_type}: <b>{name}</b>  "
            f"→  <b>{_fmt(amt)}</b>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await update.effective_message.reply_text(f"❌ Failed to save.\n{SEP}\n{str(e)[:200]}")
    context.user_data.pop("ob", None)
    return ConversationHandler.END


# ─── Transfer Flow ─────────────────────────────────────────────────────────────
@authorized
async def xfer_start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.effective_message.reply_text(f"🔄 <b>Transfer</b>\n{SEP}\nEnter amount:",
                                        parse_mode=ParseMode.HTML)
    return XFER_AMOUNT


async def xfer_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(f"🔄 <b>Transfer</b>\n{SEP}\nEnter amount:", parse_mode=ParseMode.HTML)
    return XFER_AMOUNT


async def xfer_amount_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amt = parse_amount(update.effective_message.text.strip())
    if amt is None:
        await update.effective_message.reply_text("❌ Invalid amount. Try again:")
        return XFER_AMOUNT
    context.user_data["xfer"] = {"amount": amt}
    settings = await _sh(get_settings)
    accts    = settings.get("accounts", [])
    if not accts:
        await update.effective_message.reply_text(
            "⚠️ No accounts found. Add accounts to Settings tab col A and /reload."
        )
        return ConversationHandler.END
    rows_kb  = []
    for i in range(0, len(accts), 2):
        row = [_btn(accts[i], f"xfrom_{accts[i]}")]
        if i + 1 < len(accts):
            row.append(_btn(accts[i + 1], f"xfrom_{accts[i + 1]}"))
        rows_kb.append(row)
    await update.effective_message.reply_text(
        f"💳 <b>From which account?</b>\n{SEP}",
        reply_markup=InlineKeyboardMarkup(rows_kb), parse_mode=ParseMode.HTML
    )
    return XFER_FROM


async def xfer_from_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    acc_from = q.data.replace("xfrom_", "")
    context.user_data["xfer"]["from"] = acc_from
    settings = await _sh(get_settings)
    accts    = settings.get("accounts", [])
    rows_kb  = []
    for i in range(0, len(accts), 2):
        row = []
        for acc in accts[i:i+2]:
            if acc == acc_from:
                row.append(_btn(f"🚫 {acc}", f"xto_{acc}"))
            else:
                row.append(_btn(acc, f"xto_{acc}"))
        rows_kb.append(row)
    await q.edit_message_text(
        f"💳 <b>To which account?</b>\n{SEP}",
        reply_markup=InlineKeyboardMarkup(rows_kb), parse_mode=ParseMode.HTML
    )
    return XFER_TO


async def xfer_to_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    acc_to   = q.data.replace("xto_", "")
    xfer     = context.user_data.get("xfer", {})
    acc_from = xfer.get("from", "")
    amt      = xfer.get("amount", 0.0)
    if acc_to == acc_from:
        await q.edit_message_text("❌ Source and destination accounts must be different. Use /transfer to start again.")
        context.user_data.pop("xfer", None)
        return ConversationHandler.END
    now  = datetime.now(tz=TZ)
    data = {
        "date":     now.strftime("%Y-%m-%d"),
        "type":     "Transfer",
        "category": "Balance Transfer",
        "acc_from": acc_from,
        "acc_to":   acc_to,
        "amount":   amt,
        "project":  "",
        "scope":    "Transfer",
    }
    try:
        row_num = await _sh(save_transaction, data)
        context.user_data["last_tx_row"] = row_num
        await q.edit_message_text(
            f"✅ <b>Transfer saved</b>\n{SEP}\n"
            f"🔄 <b>{_fmt(amt)}</b>\n"
            f"   💳 {acc_from}  →  {acc_to}\n"
            f"   {now.strftime('%d %b %Y')}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await q.edit_message_text(f"❌ Failed.\n{SEP}\n{str(e)[:200]}")
    context.user_data.pop("xfer", None)
    return ConversationHandler.END


# ─── Settle Flow ──────────────────────────────────────────────────────────────
@authorized
async def settle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["settle"] = {}
    kb = InlineKeyboardMarkup([[
        _btn("📥 Collect Receivable", "settle_Receivable"),
        _btn("📤 Pay Debt",           "settle_Payable"),
    ]])
    await update.effective_message.reply_text(
        f"⚖️ <b>Settle</b>\n{SEP}\nWhat would you like to do?",
        reply_markup=kb, parse_mode=ParseMode.HTML
    )
    return SETTLE_TYPE


async def settle_type_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q       = update.callback_query
    await q.answer()
    ob_type = q.data.replace("settle_", "")
    context.user_data.setdefault("settle", {})["ob_type"] = ob_type
    try:
        ob_rows = await _sh(_fetch_all_ob_rows)
    except Exception as e:
        await q.edit_message_text(
            f"❌ Could not load debt records.\n{SEP}\n{str(e)[:200]}"
        )
        return ConversationHandler.END
    # Compute net balance per person for display
    net: dict[str, float] = {}
    for row in ob_rows:
        if len(row) < 4:
            continue
        t = str(row[1]).strip().lower()
        if t != ob_type.lower():
            continue
        name = str(row[2]).strip()
        if not name:
            continue
        try:
            amt = float(row[3])
        except (ValueError, TypeError):
            amt = 0.0
        net[name] = net.get(name, 0.0) + amt
    # Show only persons with non-zero outstanding balance
    persons = [n for n, v in net.items() if abs(v) > 0.01]
    if not persons:
        await q.edit_message_text(f"✅ No outstanding {ob_type} records.")
        return ConversationHandler.END
    rows_kb = []
    for i in range(0, len(persons), 2):
        p0  = persons[i]
        lbl = f"{p0}  ({_fmt(abs(net[p0]))})"
        row = [_btn(lbl, f"sperson_{p0}")]
        if i + 1 < len(persons):
            p1  = persons[i + 1]
            lbl1 = f"{p1}  ({_fmt(abs(net[p1]))})"
            row.append(_btn(lbl1, f"sperson_{p1}"))
        rows_kb.append(row)
    emoji = "📥" if ob_type == "Receivable" else "📤"
    await q.edit_message_text(
        f"{emoji} <b>Select person</b>\n{SEP}",
        reply_markup=InlineKeyboardMarkup(rows_kb), parse_mode=ParseMode.HTML
    )
    return SETTLE_PERSON


async def settle_person_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q      = update.callback_query
    await q.answer()
    person = q.data.replace("sperson_", "")
    if "settle" not in context.user_data:
        context.user_data["settle"] = {}
    context.user_data["settle"]["person"] = person
    await q.edit_message_text(f"💰 Amount for <b>{person}</b>:", parse_mode=ParseMode.HTML)
    return SETTLE_AMT


async def settle_amt_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amt = parse_amount(update.effective_message.text.strip())
    if amt is None:
        await update.effective_message.reply_text("❌ Invalid amount. Try again:")
        return SETTLE_AMT
    context.user_data["settle"]["amount"] = amt
    settings = await _sh(get_settings)
    accts    = settings.get("accounts", [])
    if not accts:
        await update.effective_message.reply_text(
            "⚠️ No accounts found. Add accounts to Settings tab col A and /reload."
        )
        return ConversationHandler.END
    rows_kb  = []
    for i in range(0, len(accts), 2):
        row = [_btn(accts[i], f"sacc_{accts[i]}")]
        if i + 1 < len(accts):
            row.append(_btn(accts[i + 1], f"sacc_{accts[i + 1]}"))
        rows_kb.append(row)
    await update.effective_message.reply_text(
        f"💳 <b>Account?</b>\n{SEP}",
        reply_markup=InlineKeyboardMarkup(rows_kb), parse_mode=ParseMode.HTML
    )
    return SETTLE_ACC


async def settle_acc_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q      = update.callback_query
    await q.answer()
    account = q.data.replace("sacc_", "")
    settle  = context.user_data.get("settle", {})
    ob_type = settle.get("ob_type", "Payable")
    person  = settle.get("person", "")
    amt     = settle.get("amount", 0.0)
    now     = datetime.now(tz=TZ)
    ob_entry = {
        "date":    now.strftime("%Y-%m-%d"),
        "ob_type": ob_type,
        "name":    person,
        "amount":  -amt,
        "notes":   "Settlement",
        "currency": "",
    }
    is_receivable = ob_type == "Receivable"
    tx_data = {
        "date":     now.strftime("%Y-%m-%d"),
        "type":     "Income" if is_receivable else "Expense",
        "category": f"Settle {ob_type}",
        "acc_from": "" if is_receivable else account,
        "acc_to":   account if is_receivable else "",
        "amount":   amt,
        "project":  "",
        "scope":    "Income" if is_receivable else "Personal",
    }
    try:
        await _sh(save_opening_balance, ob_entry)
        row_num = await _sh(save_transaction, tx_data)
        context.user_data["last_tx_row"] = row_num
        emoji = "📥" if is_receivable else "📤"
        await q.edit_message_text(
            f"✅ <b>Settlement saved</b>\n{SEP}\n"
            f"{emoji} {ob_type}: <b>{person}</b>  →  <b>{_fmt(amt)}</b>\n"
            f"   💳 {account}  ·  {now.strftime('%d %b %Y')}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await q.edit_message_text(f"❌ Failed.\n{SEP}\n{str(e)[:200]}")
    context.user_data.pop("settle", None)
    return ConversationHandler.END


# ─── Borrow Flow ──────────────────────────────────────────────────────────────
@authorized
async def borrow_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ob_rows = await _sh(_fetch_all_ob_rows)
    persons = []
    for row in ob_rows:
        if len(row) < 3:
            continue
        if str(row[1]).strip().lower() == "payable":
            name = str(row[2]).strip()
            if name and name not in persons:
                persons.append(name)
    rows_kb = [[_btn("➕ New Person", "bperson_new")]]
    for i in range(0, len(persons), 2):
        row = [_btn(persons[i], f"bperson_{persons[i]}")]
        if i + 1 < len(persons):
            row.append(_btn(persons[i + 1], f"bperson_{persons[i + 1]}"))
        rows_kb.append(row)
    await update.effective_message.reply_text(
        f"📤 <b>Borrow (new payable)</b>\n{SEP}\nBorrow from who?",
        reply_markup=InlineKeyboardMarkup(rows_kb), parse_mode=ParseMode.HTML
    )
    context.user_data["borrow"] = {}
    return BORROW_PERSON


async def borrow_person_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "bperson_new":
        await q.edit_message_text("✏️ Enter person's name:")
        return BORROW_NAME
    person = q.data.replace("bperson_", "")
    context.user_data["borrow"]["person"] = person
    await q.edit_message_text(f"💰 Amount borrowed from <b>{person}</b>:", parse_mode=ParseMode.HTML)
    return BORROW_AMT


async def borrow_name_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_message.text.strip()
    context.user_data["borrow"]["person"] = name
    await update.effective_message.reply_text(f"💰 Amount borrowed from <b>{name}</b>:", parse_mode=ParseMode.HTML)
    return BORROW_AMT


async def borrow_amt_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amt = parse_amount(update.effective_message.text.strip())
    if amt is None:
        await update.effective_message.reply_text("❌ Invalid amount. Try again:")
        return BORROW_AMT
    context.user_data["borrow"]["amount"] = amt
    settings = await _sh(get_settings)
    accts    = settings.get("accounts", [])
    if not accts:
        await update.effective_message.reply_text(
            "⚠️ No accounts found. Add accounts to Settings tab col A and /reload."
        )
        return ConversationHandler.END
    rows_kb  = []
    for i in range(0, len(accts), 2):
        row = [_btn(accts[i], f"bacc_{accts[i]}")]
        if i + 1 < len(accts):
            row.append(_btn(accts[i + 1], f"bacc_{accts[i + 1]}"))
        rows_kb.append(row)
    await update.effective_message.reply_text(
        f"💳 Which account receives the money?\n{SEP}",
        reply_markup=InlineKeyboardMarkup(rows_kb), parse_mode=ParseMode.HTML
    )
    return BORROW_ACC


async def borrow_acc_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q        = update.callback_query
    await q.answer()
    account  = q.data.replace("bacc_", "")
    borrow   = context.user_data.get("borrow", {})
    person   = borrow.get("person", "")
    amt      = borrow.get("amount", 0.0)
    now      = datetime.now(tz=TZ)
    ob_entry = {
        "date":    now.strftime("%Y-%m-%d"),
        "ob_type": "Payable",
        "name":    person,
        "amount":  amt,
        "notes":   "Borrow",
        "currency": "",
    }
    xfer_data = {
        "date":     now.strftime("%Y-%m-%d"),
        "type":     "Transfer",
        "category": "Borrow",
        "acc_from": "",
        "acc_to":   account,
        "amount":   amt,
        "project":  "",
        "scope":    "Transfer",
    }
    try:
        await _sh(save_opening_balance, ob_entry)
        row_num = await _sh(save_transaction, xfer_data)
        context.user_data["last_tx_row"] = row_num
        await q.edit_message_text(
            f"✅ <b>Borrow saved</b>\n{SEP}\n"
            f"📤 Payable: <b>{person}</b>  →  <b>{_fmt(amt)}</b>\n"
            f"   💳 → {account}  ·  {now.strftime('%d %b %Y')}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await q.edit_message_text(f"❌ Failed.\n{SEP}\n{str(e)[:200]}")
    context.user_data.pop("borrow", None)
    return ConversationHandler.END


# ─── Lend Flow ────────────────────────────────────────────────────────────────
@authorized
async def lend_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ob_rows = await _sh(_fetch_all_ob_rows)
    persons = []
    for row in ob_rows:
        if len(row) < 3:
            continue
        if str(row[1]).strip().lower() == "receivable":
            name = str(row[2]).strip()
            if name and name not in persons:
                persons.append(name)
    rows_kb = [[_btn("➕ New Person", "lperson_new")]]
    for i in range(0, len(persons), 2):
        row = [_btn(persons[i], f"lperson_{persons[i]}")]
        if i + 1 < len(persons):
            row.append(_btn(persons[i + 1], f"lperson_{persons[i + 1]}"))
        rows_kb.append(row)
    await update.effective_message.reply_text(
        f"📥 <b>Lend (new receivable)</b>\n{SEP}\nLend to who?",
        reply_markup=InlineKeyboardMarkup(rows_kb), parse_mode=ParseMode.HTML
    )
    context.user_data["lend"] = {}
    return LEND_PERSON


async def lend_person_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "lperson_new":
        await q.edit_message_text("✏️ Enter person's name:")
        return LEND_NAME
    person = q.data.replace("lperson_", "")
    context.user_data["lend"]["person"] = person
    await q.edit_message_text(f"💰 Amount lent to <b>{person}</b>:", parse_mode=ParseMode.HTML)
    return LEND_AMT


async def lend_name_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_message.text.strip()
    context.user_data["lend"]["person"] = name
    await update.effective_message.reply_text(f"💰 Amount lent to <b>{name}</b>:", parse_mode=ParseMode.HTML)
    return LEND_AMT


async def lend_amt_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amt = parse_amount(update.effective_message.text.strip())
    if amt is None:
        await update.effective_message.reply_text("❌ Invalid amount. Try again:")
        return LEND_AMT
    context.user_data["lend"]["amount"] = amt
    settings = await _sh(get_settings)
    accts    = settings.get("accounts", [])
    if not accts:
        await update.effective_message.reply_text(
            "⚠️ No accounts found. Add accounts to Settings tab col A and /reload."
        )
        return ConversationHandler.END
    rows_kb  = []
    for i in range(0, len(accts), 2):
        row = [_btn(accts[i], f"lacc_{accts[i]}")]
        if i + 1 < len(accts):
            row.append(_btn(accts[i + 1], f"lacc_{accts[i + 1]}"))
        rows_kb.append(row)
    await update.effective_message.reply_text(
        f"💳 Which account does the money come from?\n{SEP}",
        reply_markup=InlineKeyboardMarkup(rows_kb), parse_mode=ParseMode.HTML
    )
    return LEND_ACC


async def lend_acc_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q        = update.callback_query
    await q.answer()
    account  = q.data.replace("lacc_", "")
    lend     = context.user_data.get("lend", {})
    person   = lend.get("person", "")
    amt      = lend.get("amount", 0.0)
    now      = datetime.now(tz=TZ)
    ob_entry = {
        "date":    now.strftime("%Y-%m-%d"),
        "ob_type": "Receivable",
        "name":    person,
        "amount":  amt,
        "notes":   "Lend",
        "currency": "",
    }
    xfer_data = {
        "date":     now.strftime("%Y-%m-%d"),
        "type":     "Transfer",
        "category": "Lend",
        "acc_from": account,
        "acc_to":   "",
        "amount":   amt,
        "project":  "",
        "scope":    "Transfer",
    }
    try:
        await _sh(save_opening_balance, ob_entry)
        row_num = await _sh(save_transaction, xfer_data)
        context.user_data["last_tx_row"] = row_num
        await q.edit_message_text(
            f"✅ <b>Lend saved</b>\n{SEP}\n"
            f"📥 Receivable: <b>{person}</b>  →  <b>{_fmt(amt)}</b>\n"
            f"   💳 {account}  ·  {now.strftime('%d %b %Y')}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await q.edit_message_text(f"❌ Failed.\n{SEP}\n{str(e)[:200]}")
    context.user_data.pop("lend", None)
    return ConversationHandler.END


# ─── Photo / Receipt Flow ─────────────────────────────────────────────────────
@authorized
async def receipt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"📷 <b>Receipt</b>\n{SEP}\nSend a photo of your receipt.",
        parse_mode=ParseMode.HTML
    )
    return PHOTO_SCOPE


async def receipt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[
        _btn("🏢 Business", "scope_Business Expense"),
        _btn("👤 Personal", "scope_Personal Expense"),
        _btn("💵 Income",   "scope_Income"),
    ]])
    await update.effective_message.reply_text(
        f"📷 <b>Receipt received.</b>\n{SEP}\nExpense or income?",
        reply_markup=kb, parse_mode=ParseMode.HTML
    )
    context.user_data["tx"] = {"amount": 0.0}
    return PHOTO_SCOPE


# ─── Command Handlers ─────────────────────────────────────────────────────────
@authorized
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m    = await update.effective_message.reply_text("⏳")
    now  = datetime.now(tz=TZ)
    name = update.effective_user.first_name if update.effective_user else "Friend"
    try:
        s    = await _sh(get_monthly_summary, now.year, now.month)
        inc  = s.get("income", 0.0)
        exp  = s.get("expense", 0.0)
        net  = s.get("net", 0.0)
        cnt  = s.get("tx_count", 0)
        rate = (inc - exp) / inc * 100 if inc > 0 else 0.0
        msg  = (
            f"👋 <b>Hi, {name}!</b>  —  {now.strftime('%B %Y')}\n"
            f"{SEP}\n"
            f"💵 Income    <b>{_fmt(inc)}</b>\n"
            f"💸 Expense   <b>{_fmt(exp)}</b>\n"
            f"{_sign_emoji(net)} Net      <b>{_fmt(net)}</b>\n"
            f"💰 Savings   <b>{rate:.0f}%</b>   ·   {cnt} transactions\n"
            f"{SEP}\n"
            f"{_month_progress(now)}\n"
            f"\n<i>Type an amount to log a transaction</i>"
        )
    except Exception as e:
        msg = f"👋 <b>Hi, {name}!</b>\n{SEP}\n❌ Failed to load data.\n{str(e)[:150]}"
    kb = InlineKeyboardMarkup([
        [_btn("💹 Balance",   "qs_balance"),  _btn("📊 Summary",  "qs_summary")],
        [_btn("🗓 Today",     "qs_today"),    _btn("📅 Weekly",   "qs_weekly")],
        [_btn("💳 Accounts",  "qs_accounts"), _btn("⚖️ Debts",    "qs_debts")],
        [_btn("🔄 Transfer",  "xfer_start"),  _btn("❓ Help",     "qs_help")],
    ])
    await m.edit_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)


@authorized
async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m   = await update.effective_message.reply_text("⏳")
    now = datetime.now(tz=TZ)
    try:
        s   = await _sh(get_monthly_summary, now.year, now.month)
        inc = s.get("income", 0.0)
        exp = s.get("expense", 0.0)
        net = s.get("net", 0.0)
        cnt = s.get("tx_count", 0)
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        days_elapsed  = now.day
        days_left     = days_in_month - days_elapsed
        avg_daily     = exp / days_elapsed if days_elapsed > 0 else 0.0
        rate          = (inc - exp) / inc * 100 if inc > 0 else 0.0
        msg = (
            f"💹 <b>Balance — {now.strftime('%B %Y')}</b>\n{SEP}\n"
            f"💵 Income       <b>{_fmt(inc)}</b>\n"
            f"💸 Expense      <b>{_fmt(exp)}</b>\n"
            f"{_sign_emoji(net)} Net        <b>{_fmt(net)}</b>\n"
            f"💰 Savings rate <b>{rate:.0f}%</b>\n"
            f"📊 Transactions <b>{cnt}</b>\n"
            f"{SEP}\n"
            f"📆 Daily avg    <b>{_fmt(avg_daily)}</b>\n"
            f"📅 Days left    <b>{days_left}</b>\n"
            f"{_month_progress(now)}"
        )
    except Exception as e:
        msg = f"❌ Failed to load balance.\n{SEP}\n{str(e)[:200]}"
    await m.edit_text(msg, parse_mode=ParseMode.HTML)


@authorized
async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m    = await update.effective_message.reply_text("⏳")
    args = context.args or []
    now  = datetime.now(tz=TZ)
    if args:
        try:
            year, month = map(int, args[0].split("-"))
        except Exception:
            await m.edit_text("❌ Usage: /summary YYYY-MM")
            return
    else:
        year, month = now.year, now.month
    try:
        s    = await _sh(get_monthly_summary, year, month)
        inc  = s.get("income", 0.0)
        exp  = s.get("expense", 0.0)
        net  = s.get("net", 0.0)
        biz  = s.get("biz_expense", 0.0)
        per  = s.get("per_expense", 0.0)
        cats = sorted(s.get("categories", {}).items(), key=lambda x: -x[1])[:6]
        max_cat = cats[0][1] if cats else 1.0
        lines = [
            f"📊 <b>Summary — {year}-{month:02d}</b>\n{SEP}",
            f"💵 Income   <b>{_fmt(inc)}</b>",
            f"💸 Expense  <b>{_fmt(exp)}</b>",
            f"{_sign_emoji(net)} Net      <b>{_fmt(net)}</b>",
        ]
        if biz or per:
            lines.append(f"   🏢 Business <b>{_fmt(biz)}</b>  ·  👤 Personal <b>{_fmt(per)}</b>")
        if cats:
            lines.append(f"{SEP}\n🏷 <b>Top expenses:</b>")
            for cat, amt in cats:
                bar = _bar(amt, max_cat, 8)
                lines.append(f"  {bar} {cat}  <b>{_fmt(amt)}</b>")
        await m.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        await m.edit_text(f"❌ Failed to load summary.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_lastmonth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(tz=TZ)
    first = now.replace(day=1)
    prev  = first - timedelta(days=1)
    context.args = [f"{prev.year}-{prev.month:02d}"]
    await cmd_summary(update, context)


@authorized
async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m   = await update.effective_message.reply_text("⏳")
    now = datetime.now(tz=TZ)
    today_str = now.strftime("%Y-%m-%d")
    try:
        tx_rows = await _sh(get_tx_rows)
        today_rows = []
        for i, row in enumerate(tx_rows):
            if len(row) < 9:
                continue
            d = _parse_row_date(row)
            if d and d.strftime("%Y-%m-%d") == today_str:
                today_rows.append((i + 2, row))
        if not today_rows:
            await m.edit_text(f"🗓 No transactions today ({now.strftime('%d %b %Y')}).")
            return
        inc = sum(float(r[8]) for _, r in today_rows if len(r) > 8 and str(r[4]).strip() == "Income"  and r[8] != "")
        exp = sum(float(r[8]) for _, r in today_rows if len(r) > 8 and str(r[4]).strip() == "Expense" and r[8] != "")
        lines = [f"🗓 <b>Today — {now.strftime('%d %b %Y')}</b>  ({len(today_rows)} transactions)\n{SEP}"]
        for row_num, row in today_rows[-10:]:
            lines.append(_tx_card(row_num, row))
            lines.append("")
        lines.append(SEP)
        lines.append(f"💵 In: <b>{_fmt(inc)}</b>  ·  💸 Out: <b>{_fmt(exp)}</b>")
        await m.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        await m.edit_text(f"❌ Failed to load today's data.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = await update.effective_message.reply_text("⏳")
    now  = datetime.now(tz=TZ)
    try:
        tx_rows = await _sh(get_tx_rows)
        day_totals: dict[str, float] = {}
        for i in range(6, -1, -1):
            d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            day_totals[d] = 0.0
        for row in tx_rows:
            if len(row) < 9:
                continue
            d = _parse_row_date(row)
            if not d:
                continue
            ds = d.strftime("%Y-%m-%d")
            if ds not in day_totals:
                continue
            if str(row[4]).strip() == "Transfer":
                continue
            try:
                amt = float(row[8]) if row[8] != "" else 0.0
            except Exception:
                amt = 0.0
            if str(row[4]).strip() == "Expense":
                day_totals[ds] += amt
        max_day = max(day_totals.values()) if day_totals else 1.0
        today   = now.strftime("%Y-%m-%d")
        peak    = max(day_totals, key=day_totals.get) if day_totals else today
        lines   = [f"📅 <b>Last 7 Days</b>\n{SEP}"]
        for ds, amt in day_totals.items():
            d_obj    = datetime.strptime(ds, "%Y-%m-%d")
            day_name = d_obj.strftime("%a %d")
            bar      = _bar(amt, max_day, 10)
            suffix   = " ⭐" if ds == peak else (" 📍" if ds == today else "")
            lines.append(f"{day_name}  {bar}  <b>{_fmt(amt)}</b>{suffix}")
        total = sum(day_totals.values())
        lines.append(f"{SEP}\nTotal: <b>{_fmt(total)}</b>")
        await m.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        await m.edit_text(f"❌ Failed to load weekly data.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_cashflow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lm = await update.effective_message.reply_text("⏳")
    now = datetime.now(tz=TZ)
    try:
        months = []
        for i in range(4, -1, -1):
            d = now.replace(day=1) - timedelta(days=i * 28)
            months.append((d.year, d.month))
        results = await asyncio.gather(*[_sh(get_monthly_summary, y, m) for y, m in months])
        lines = [f"📈 <b>5-Month Cashflow</b>\n{SEP}"]
        max_val = max((max(r["income"], r["expense"]) for r in results), default=1.0)
        for (y, mth), r in zip(months, results):
            label   = f"{y}-{mth:02d}"
            inc     = r.get("income", 0.0)
            exp     = r.get("expense", 0.0)
            net     = inc - exp
            inc_bar = _bar(inc, max_val, 7)
            exp_bar = _bar(exp, max_val, 7)
            lines.append(f"<b>{label}</b>  {_sign_emoji(net)} {_fmt(net)}")
            lines.append(f"  💵 {inc_bar} {_fmt(inc)}")
            lines.append(f"  💸 {exp_bar} {_fmt(exp)}")
        await lm.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        await lm.edit_text(f"❌ Failed to load cashflow.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lm   = await update.effective_message.reply_text("⏳")
    now  = datetime.now(tz=TZ)
    args = context.args or []
    try:
        if len(args) >= 2:
            y1, m1 = map(int, args[0].split("-"))
            y2, m2 = map(int, args[1].split("-"))
        else:
            first  = now.replace(day=1)
            prev   = first - timedelta(days=1)
            y1, m1 = prev.year, prev.month
            y2, m2 = now.year, now.month
        r1, r2 = await asyncio.gather(
            _sh(get_monthly_summary, y1, m1),
            _sh(get_monthly_summary, y2, m2),
        )
        l1, l2 = f"{y1}-{m1:02d}", f"{y2}-{m2:02d}"
        rows = [
            ("",              f"<b>{l1}</b>",                       f"<b>{l2}</b>"),
            ("💵 Income",    f"<b>{_fmt(r1['income'])}</b>",       f"<b>{_fmt(r2['income'])}</b>"),
            ("💸 Expense",   f"<b>{_fmt(r1['expense'])}</b>",      f"<b>{_fmt(r2['expense'])}</b>"),
            (f"{_sign_emoji(r1['net'])} Net", f"<b>{_fmt(r1['net'])}</b>", f"<b>{_fmt(r2['net'])}</b>"),
            ("📊 Txns",      f"{r1['tx_count']}",                  f"{r2['tx_count']}"),
        ]
        lines = [f"📊 <b>Compare</b>\n{SEP}"]
        for label, a, b in rows:
            lines.append(f"{label}  {a}  ·  {b}" if label else f"{a}  ·  {b}")
        await lm.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        await lm.edit_text(f"❌ Failed to compare.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lm  = await update.effective_message.reply_text("⏳")
    now = datetime.now(tz=TZ)
    try:
        s = await _sh(get_monthly_summary, now.year, now.month)
        inc        = s.get("income", 0.0)
        exp        = s.get("expense", 0.0)
        days_in    = calendar.monthrange(now.year, now.month)[1]
        days_gone  = now.day
        daily_rate = exp / days_gone if days_gone > 0 else 0.0
        proj_exp   = daily_rate * days_in
        proj_net   = inc - proj_exp
        msg = (
            f"🔮 <b>Forecast — {now.strftime('%B %Y')}</b>\n{SEP}\n"
            f"💸 Spent so far    <b>{_fmt(exp)}</b>  (day {days_gone}/{days_in})\n"
            f"📆 Daily avg       <b>{_fmt(daily_rate)}</b>\n"
            f"{SEP}\n"
            f"📉 Projected spend <b>{_fmt(proj_exp)}</b>\n"
            f"💵 Income so far   <b>{_fmt(inc)}</b>\n"
            f"{_sign_emoji(proj_net)} Projected net  <b>{_fmt(proj_net)}</b>"
        )
        await lm.edit_text(msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        await lm.edit_text(f"❌ Failed to forecast.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_split(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lm   = await update.effective_message.reply_text("⏳")
    args = context.args or []
    now  = datetime.now(tz=TZ)
    if args:
        try:
            year, month = map(int, args[0].split("-"))
        except Exception:
            await lm.edit_text("❌ Usage: /split YYYY-MM")
            return
    else:
        year, month = now.year, now.month
    try:
        s   = await _sh(get_monthly_summary, year, month)
        biz = s.get("biz_expense", 0.0)
        per = s.get("per_expense", 0.0)
        tot = biz + per
        biz_pct = biz / tot * 100 if tot > 0 else 0.0
        per_pct = per / tot * 100 if tot > 0 else 0.0
        msg = (
            f"📊 <b>Business vs Personal — {year}-{month:02d}</b>\n{SEP}\n"
            f"🏢 Business  {_bar(biz, tot, 8)}  <b>{biz_pct:.0f}%</b>  {_fmt(biz)}\n"
            f"👤 Personal  {_bar(per, tot, 8)}  <b>{per_pct:.0f}%</b>  {_fmt(per)}\n"
            f"{SEP}\n"
            f"Total: <b>{_fmt(tot)}</b>"
        )
        await lm.edit_text(msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        await lm.edit_text(f"❌ Failed to load data.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lm   = await update.effective_message.reply_text("⏳")
    args = context.args or []
    n    = 5
    if args:
        try:
            n = int(args[0])
        except Exception:
            pass
    now = datetime.now(tz=TZ)
    try:
        s    = await _sh(get_monthly_summary, now.year, now.month)
        cats = sorted(s.get("categories", {}).items(), key=lambda x: -x[1])[:n]
        if not cats:
            await lm.edit_text("No expense data for this month.")
            return
        max_c = cats[0][1]
        lines = [f"🏆 <b>Top {n} — {now.strftime('%B %Y')}</b>\n{SEP}"]
        for i, (cat, amt) in enumerate(cats, 1):
            bar = _bar(amt, max_c, 8)
            lines.append(f"{i}. {bar} {cat}  <b>{_fmt(amt)}</b>")
        await lm.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        await lm.edit_text(f"❌ Failed to load top categories.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lm = await update.effective_message.reply_text("⏳")
    try:
        balances = await _sh(get_account_balances)
        if not balances:
            await lm.edit_text("No account data found.")
            return
        fx_rates = await _sh(get_fx_rates)
        by_currency: dict[str, list] = {}
        for acc, info in balances.items():
            cur = info.get("currency", "MMK")
            by_currency.setdefault(cur, []).append((acc, info["balance"]))
        lines = [f"💳 <b>Account Balances</b>\n{SEP}"]
        grand_total_mmk = 0.0
        for cur, accs in sorted(by_currency.items()):
            total = sum(bal for _, bal in accs)
            if cur == "MMK":
                grand_total_mmk += total
            else:
                rate = fx_rates.get(cur, 0.0)
                if rate > 0:
                    grand_total_mmk += total * rate
                else:
                    grand_total_mmk += total  # fallback: treat as MMK
            for acc, bal in sorted(accs, key=lambda x: -abs(x[1])):
                lines.append(f"  {_sign_emoji(bal)} {acc}   <b>{_fmt(bal)}</b> {cur}")
        lines.append(f"{SEP}\nTotal MMK  <b>{_fmt(grand_total_mmk)}</b>")
        await lm.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        await lm.edit_text(f"❌ Failed to load account data.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_networth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lm = await update.effective_message.reply_text("⏳")
    try:
        balances = await _sh(get_account_balances)
        fx_rates = await _sh(get_fx_rates)
        ob_rows  = await _sh(_fetch_all_ob_rows)
        # Sum account balances, converting non-MMK via FX rates
        total_accounts = 0.0
        for info in balances.values():
            cur = info.get("currency", "MMK")
            bal = info["balance"]
            if cur == "MMK":
                total_accounts += bal
            else:
                rate = fx_rates.get(cur, 0.0)
                if rate > 0:
                    total_accounts += bal * rate
                else:
                    total_accounts += bal
        total_payables    = 0.0
        total_receivables = 0.0
        total_assets      = 0.0
        for row in ob_rows:
            if len(row) < 4:
                continue
            ob_type = str(row[1]).strip().lower()
            try:
                amt = float(row[3])
            except Exception:
                amt = 0.0
            if ob_type == "payable":
                total_payables += amt
            elif ob_type == "receivable":
                total_receivables += amt
            elif ob_type in ("asset", "real estate", "business"):
                total_assets += amt
        net_worth = total_accounts + total_receivables + total_assets - total_payables
        msg = (
            f"🏦 <b>Net Worth</b>\n{SEP}\n"
            f"💳 Accounts:    <b>{_fmt(total_accounts)}</b>\n"
            f"📥 Receivables: <b>{_fmt(total_receivables)}</b>\n"
            f"🏠 Assets:      <b>{_fmt(total_assets)}</b>\n"
            f"📤 Payables:    <b>-{_fmt(total_payables)}</b>\n"
            f"{SEP}\n"
            f"{_sign_emoji(net_worth)} <b>Net Worth: {_fmt(net_worth)}</b>"
        )
        await lm.edit_text(msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        await lm.edit_text(f"❌ Failed to load net worth.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_debts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lm = await update.effective_message.reply_text("⏳")
    try:
        ob_rows = await _sh(_fetch_all_ob_rows)
        receivables: dict[str, float] = {}
        payables: dict[str, float]    = {}
        for row in ob_rows:
            if len(row) < 4:
                continue
            ob_type = str(row[1]).strip().lower()
            name    = str(row[2]).strip()
            try:
                amt = float(row[3])
            except Exception:
                amt = 0.0
            if ob_type == "receivable" and name:
                receivables[name] = receivables.get(name, 0.0) + amt
            elif ob_type == "payable" and name:
                payables[name] = payables.get(name, 0.0) + amt
        lines = [f"⚖️ <b>Debts Summary</b>\n{SEP}"]
        if receivables:
            total_recv = sum(receivables.values())
            lines.append(f"📥 <b>Owed to you</b>  ({_fmt(total_recv)})")
            for name, amt in sorted(receivables.items(), key=lambda x: -x[1]):
                if amt != 0:
                    lines.append(f"   {name}   <b>{_fmt(amt)}</b>")
        if payables:
            total_pay = sum(payables.values())
            lines.append(f"\n📤 <b>You owe</b>  ({_fmt(total_pay)})")
            for name, amt in sorted(payables.items(), key=lambda x: -x[1]):
                if amt != 0:
                    lines.append(f"   {name}   <b>{_fmt(amt)}</b>")
        if not receivables and not payables:
            lines.append("No debt records found.")
        await lm.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        await lm.edit_text(f"❌ Failed to load debt data.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_fx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    if len(args) < 2:
        rates = await _sh(get_fx_rates)
        lines = [f"💱 <b>FX Rates (to MMK)</b>\n{SEP}"]
        for cur, rate in rates.items():
            lines.append(f"  {cur}: <b>{_fmt(rate)}</b>")
        if not rates:
            lines.append("No FX rates set yet.")
        lines.append(f"\nUsage: /fx 100 USD")
        await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
        return
    try:
        amount = float(args[0])
        currency = args[1].upper()
    except Exception:
        await update.effective_message.reply_text("Usage: /fx 100 USD")
        return
    rates = await _sh(get_fx_rates)
    if currency not in rates:
        await update.effective_message.reply_text(f"❌ No rate for {currency}. Use /setrate {currency} <rate> to add it.")
        return
    mmk = amount * rates[currency]
    await update.effective_message.reply_text(
        f"💱 <b>{_fmt(amount)} {currency}</b>  =  <b>{_fmt(mmk)} MMK</b>\n"
        f"Rate: 1 {currency} = {_fmt(rates[currency])} MMK",
        parse_mode=ParseMode.HTML
    )


@authorized
async def cmd_setrate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    if len(args) < 2:
        await update.effective_message.reply_text("Usage: /setrate USD 4500")
        return
    try:
        currency = args[0].upper()
        rate     = float(args[1])
    except Exception:
        await update.effective_message.reply_text("❌ Invalid. Usage: /setrate USD 4500")
        return
    await update.effective_message.reply_text("⏳ Updating...")
    try:
        await _sh(update_fx_rate, currency, rate)
        await update.effective_message.reply_text(
            f"✅ Rate updated: 1 {currency} = <b>{_fmt(rate)} MMK</b>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await update.effective_message.reply_text(f"❌ Failed.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_saas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = await update.effective_message.reply_text("⏳")
    try:
        rows = await _sh(get_saas_rows)
        if not rows:
            await m.edit_text("No SaaS records found.")
            return
        total   = 0.0
        active  = []
        for row in rows:
            if len(row) < 6:
                continue
            status = str(row[5]).strip().lower() if len(row) > 5 else "active"
            if status == "cancelled":
                continue
            name    = str(row[0]).strip()
            try:
                cost = float(row[1]) if row[1] != "" else 0.0
            except Exception:
                cost = 0.0
            renewal = str(row[2]).strip() if len(row) > 2 else ""
            billing = str(row[3]).strip() if len(row) > 3 else ""
            account = str(row[4]).strip() if len(row) > 4 else ""
            total  += cost
            active.append((name, cost, renewal, billing, account))
        lines = [f"📱 <b>SaaS Services</b>\n{SEP}"]
        for name, cost, renewal, billing, account in sorted(active, key=lambda x: -x[1]):
            lines.append(
                f"• <b>{name}</b>  {_fmt(cost)}/mo"
                + (f"  [{billing}]" if billing else "")
                + (f"\n  💳 {account}  📅 Renews: {renewal}" if account or renewal else "")
            )
        lines.append(f"{SEP}\nTotal: <b>{_fmt(total)}/mo</b>")
        await m.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        await m.edit_text(f"❌ Failed to load SaaS data.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    if args:
        try:
            budget = float(args[0].replace(",", "").replace("k", "000"))
        except Exception:
            await update.effective_message.reply_text("❌ Usage: /budget 500000")
            return
        context.bot_data["budget"] = budget
        await update.effective_message.reply_text(
            f"✅ Budget set: <b>{_fmt(budget)} MMK/mo</b>", parse_mode=ParseMode.HTML
        )
    else:
        budget = context.bot_data.get("budget")
        if not budget:
            await update.effective_message.reply_text("No budget set. Use /budget 500000 to set one.")
            return
        now = datetime.now(tz=TZ)
        try:
            s   = await _sh(get_monthly_summary, now.year, now.month)
            exp = s.get("expense", 0.0)
            remaining = budget - exp
            pct       = exp / budget * 100
            bar       = _bar(exp, budget, 10)
            msg = (
                f"💰 <b>Budget — {now.strftime('%B %Y')}</b>\n{SEP}\n"
                f"Budget:    <b>{_fmt(budget)}</b>\n"
                f"Spent:     <b>{_fmt(exp)}</b>\n"
                f"Remaining: {_sign_emoji(remaining)} <b>{_fmt(remaining)}</b>\n"
                f"{bar} {pct:.0f}%"
            )
            await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.effective_message.reply_text(f"❌ Failed.\n{str(e)[:200]}")


@authorized
async def cmd_remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    if not args:
        await update.effective_message.reply_text("Usage: /remind HH:MM  (e.g. /remind 21:00)")
        return
    try:
        h, m = map(int, args[0].split(":"))
        assert 0 <= h <= 23 and 0 <= m <= 59
    except Exception:
        await update.effective_message.reply_text("❌ Invalid time. Use HH:MM format.")
        return
    user_id = update.effective_user.id
    context.bot_data.setdefault("reminders", {})[user_id] = {"hour": h, "minute": m}
    _schedule_reminder(context.application, user_id, h, m)
    await update.effective_message.reply_text(
        f"⏰ Daily reminder set for <b>{h:02d}:{m:02d}</b>", parse_mode=ParseMode.HTML
    )


def _schedule_reminder(app, user_id: int, hour: int, minute: int):
    import datetime as _dt
    job_name = f"remind_{user_id}"
    existing = app.job_queue.get_jobs_by_name(job_name)
    for job in existing:
        job.schedule_removal()
    target_time = _dt.time(hour=hour, minute=minute, tzinfo=TZ)
    app.job_queue.run_daily(_remind_job, time=target_time, name=job_name, data={"user_id": user_id})


async def _remind_job(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.job.data["user_id"]
    now     = datetime.now(tz=TZ)
    try:
        s   = await _sh(get_monthly_summary, now.year, now.month)
        exp = s.get("expense", 0.0)
        tx_rows = await _sh(get_tx_rows)
        today_str = now.strftime("%Y-%m-%d")
        today_exp = sum(
            float(r[8]) for r in tx_rows
            if len(r) > 8 and str(r[4]).strip() == "Expense"
            and (_parse_row_date(r) or date.min).strftime("%Y-%m-%d") == today_str
            and r[8] != ""
        )
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"⏰ <b>Daily Reminder</b>\n{SEP}\n"
                f"💸 Today:     <b>{_fmt(today_exp)}</b>\n"
                f"💸 This month: <b>{_fmt(exp)}</b>"
            ),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Reminder job error: {e}")


@authorized
async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lm    = await update.effective_message.reply_text("⏳")
    args  = context.args or []
    page  = 0
    limit = HISTORY_PAGE_SIZE
    if args:
        try:
            limit = min(int(args[0]), 20)
        except Exception:
            pass
    try:
        tx_rows   = await _sh(get_tx_rows)
        data_rows = [(i + 2, r) for i, r in enumerate(tx_rows) if len(r) >= 9]
        data_rows = [(n, r) for n, r in data_rows if str(r[4]).strip() != ""]
        data_rows = list(reversed(data_rows))
        total     = len(data_rows)
        page_rows = data_rows[page * limit:(page + 1) * limit]
        lines     = [f"📜 <b>History</b>  (last {limit}/{total})\n{SEP}"]
        for row_num, row in page_rows:
            lines.append(_tx_card(row_num, row))
            lines.append("")
        nav_btns = []
        if (page + 1) * limit < total:
            nav_btns.append(_btn("▶ More", f"hist_{page+1}_{limit}"))
        kb = InlineKeyboardMarkup([nav_btns]) if nav_btns else None
        await lm.edit_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception as e:
        await lm.edit_text(f"❌ Failed.\n{SEP}\n{str(e)[:200]}")


async def cb_history_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    await q.answer()
    _, page_s, limit_s = q.data.split("_")
    page  = int(page_s)
    limit = int(limit_s)
    try:
        tx_rows   = await _sh(get_tx_rows)
        data_rows = [(i + 2, r) for i, r in enumerate(tx_rows) if len(r) >= 9]
        data_rows = [(n, r) for n, r in data_rows if str(r[4]).strip() != ""]
        data_rows = list(reversed(data_rows))
        total     = len(data_rows)
        page_rows = data_rows[page * limit:(page + 1) * limit]
        lines     = [f"📜 <b>History</b> — Page {page + 1}\n{SEP}"]
        for row_num, row in page_rows:
            lines.append(_tx_card(row_num, row))
            lines.append("")
        lines.append(f"Showing {page*limit+1}-{page*limit+len(page_rows)}/{total}")
        nav_btns = []
        if page > 0:
            nav_btns.append(_btn("◀ Back", f"hist_{page-1}_{limit}"))
        if (page + 1) * limit < total:
            nav_btns.append(_btn("▶ More", f"hist_{page+1}_{limit}"))
        kb = InlineKeyboardMarkup([nav_btns]) if nav_btns else None
        await q.edit_message_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception as e:
        await q.edit_message_text(f"❌ Failed.\n{str(e)[:200]}")


@authorized
async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    if not args:
        await update.effective_message.reply_text("Usage: /search <keyword>")
        return
    keyword = " ".join(args).lower()
    await update.effective_message.reply_text("⏳ Searching...")
    try:
        tx_rows = await _sh(get_tx_rows)
        matches = []
        for i, row in enumerate(tx_rows):
            if len(row) < 9:
                continue
            searchable = " ".join(str(c).lower() for c in row)
            if keyword in searchable:
                matches.append((i + 2, row))
        if not matches:
            await update.effective_message.reply_text(f"No results for «{keyword}».")
            return
        lines = [f"🔍 <b>Search: {keyword}</b>  ({len(matches)} results)\n{SEP}"]
        for row_num, row in matches[-10:]:
            lines.append(_tx_card(row_num, row))
            lines.append("")
        await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.effective_message.reply_text(f"❌ Search failed.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args  = context.args or []
    now   = datetime.now(tz=TZ)
    if args:
        try:
            year, month = map(int, args[0].split("-"))
        except Exception:
            await update.effective_message.reply_text("❌ Usage: /export YYYY-MM")
            return
    else:
        year, month = now.year, now.month
    await update.effective_message.reply_text("⏳ Exporting...")
    try:
        tx_rows     = await _sh(get_tx_rows)
        target_pref = f"{year}-{month:02d}"
        month_rows  = []
        for row in tx_rows:
            if len(row) < 9:
                continue
            month_col = str(row[3]).strip() if len(row) > 3 else ""
            if month_col:
                if month_col != target_pref:
                    continue
            else:
                d = _parse_row_date(row)
                if d is None or d.year != year or d.month != month:
                    continue
            month_rows.append(row)
        buf = io.StringIO()
        w   = csv.writer(buf)
        w.writerow(["Row", "Date", "DayOfWeek", "MonthKey", "Type", "Category",
                    "AccountFrom", "AccountTo", "Amount", "Project", "Scope"])
        for i, row in enumerate(month_rows, 1):
            padded = row + [""] * (14 - len(row))
            w.writerow([i, padded[1], padded[2], padded[3], padded[4], padded[5],
                        padded[6], padded[7], padded[8], padded[9], padded[13]])
        buf.seek(0)
        filename = f"transactions_{year}-{month:02d}.csv"
        await update.effective_message.reply_document(
            document=InputFile(buf, filename=filename),
            caption=f"📤 {target_pref} — {len(month_rows)} transactions"
        )
    except Exception as e:
        await update.effective_message.reply_text(f"❌ Export failed.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last_row = context.user_data.get("last_tx_row")
    if not last_row:
        await update.effective_message.reply_text("❌ No recent transaction to edit.")
        return ConversationHandler.END
    context.user_data["edit_row"] = last_row
    context.user_data["tx"]       = {}
    await update.effective_message.reply_text(
        f"✏️ <b>Edit transaction #{last_row}</b>\n{SEP}\nEnter new amount:",
        parse_mode=ParseMode.HTML
    )
    return EXPENSE_AMT


async def tx_edit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amt = parse_amount(update.effective_message.text.strip())
    if amt is None:
        await update.effective_message.reply_text("❌ Invalid amount. Try again:")
        return EXPENSE_AMT
    context.user_data["tx"]["amount"] = amt
    kb = InlineKeyboardMarkup([[
        _btn("🏢 Business", "scope_Business Expense"),
        _btn("👤 Personal", "scope_Personal Expense"),
        _btn("💵 Income",   "scope_Income"),
    ]])
    await update.effective_message.reply_text(
        f"💰 <b>{_fmt(amt)} MMK</b>\n{SEP}\nExpense or income?",
        reply_markup=kb, parse_mode=ParseMode.HTML
    )
    return SCOPE_STEP


@authorized
async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last_row = context.user_data.get("last_tx_row")
    if not last_row:
        await update.effective_message.reply_text("❌ No recent transaction to delete.")
        return
    await update.effective_message.reply_text("⏳ Deleting...")
    try:
        await _sh(delete_tx_row, last_row)
        context.user_data.pop("last_tx_row", None)
        await update.effective_message.reply_text(f"✅ Transaction #{last_row} deleted.")
    except Exception as e:
        await update.effective_message.reply_text(f"❌ Failed.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m   = await update.effective_message.reply_text("⏳")
    now = datetime.now(tz=TZ)
    try:
        s     = await _sh(get_monthly_summary, now.year, now.month)
        projs = sorted(s.get("projects", {}).items(), key=lambda x: -x[1])
        if not projs:
            await m.edit_text("No project data for this month.")
            return
        lines = [f"📁 <b>Projects — {now.strftime('%B %Y')}</b>\n{SEP}"]
        max_p = projs[0][1] if projs else 1.0
        for proj, amt in projs:
            bar = _bar(amt, max_p, 10)
            lines.append(f"  {bar}  {proj}  <b>{_fmt(amt)}</b>")
        rows_kb = []
        for i in range(0, len(projs), 2):
            row = [_btn(projs[i][0], f"proj_{projs[i][0]}")]
            if i + 1 < len(projs):
                row.append(_btn(projs[i + 1][0], f"proj_{projs[i + 1][0]}"))
            rows_kb.append(row)
        await m.edit_text(
            "\n".join(lines), parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(rows_kb)
        )
    except Exception as e:
        await m.edit_text(f"❌ Failed to load project data.\n{SEP}\n{str(e)[:200]}")


async def cb_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q       = update.callback_query
    await q.answer()
    project = q.data.replace("proj_", "")
    now     = datetime.now(tz=TZ)
    try:
        tx_rows  = await _sh(get_tx_rows)
        proj_txs = []
        income   = 0.0
        expense  = 0.0
        for i, row in enumerate(tx_rows):
            if len(row) < 10:
                continue
            if str(row[9]).strip() != project:
                continue
            d = _parse_row_date(row)
            if not d or d.year != now.year or d.month != now.month:
                continue
            try:
                amt = float(row[8]) if row[8] != "" else 0.0
            except Exception:
                amt = 0.0
            if str(row[4]).strip() == "Income":
                income += amt
            else:
                expense += amt
            proj_txs.append((i + 2, row))
        lines = [f"📁 <b>{project}</b> — {now.strftime('%B %Y')}\n{SEP}",
                 f"💵 Income:  <b>{_fmt(income)}</b>",
                 f"💸 Expense: <b>{_fmt(expense)}</b>",
                 f"{_sign_emoji(income-expense)} P&L: <b>{_fmt(income - expense)}</b>",
                 SEP]
        for row_num, row in proj_txs[-5:]:
            lines.append(_tx_card(row_num, row))
        await q.edit_message_text("\n".join(lines), parse_mode=ParseMode.HTML)
    except Exception as e:
        await q.edit_message_text(f"❌ Failed.\n{str(e)[:200]}")


@authorized
async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("🟢 Online")


@authorized
async def cmd_reload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("🔄 Reloading settings from Google Sheets...")
    try:
        invalidate_all_caches()
        s  = await _sh(get_settings)
        tx = await _sh(get_tx_rows)
        ob = await _sh(get_opening_balances)
        accts = s.get("accounts", [])
        cats  = s.get("biz_cats", []) + s.get("per_cats", [])
        await update.effective_message.reply_text(
            f"✅ <b>Cache refreshed</b>\n{SEP}\n"
            f"💳 Accounts ({len(accts)}): {', '.join(accts) or 'none'}\n"
            f"🏷 Categories ({len(cats)}): {', '.join(cats[:5])}{'…' if len(cats)>5 else ''}\n"
            f"📋 Transactions: {len(tx)}\n"
            f"📊 OB records: {len(ob.get('balances', {}))}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await update.effective_message.reply_text(f"❌ Reload failed.\n{SEP}\n{str(e)[:200]}")


@authorized
async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("tx", None)
    context.user_data.pop("ob", None)
    context.user_data.pop("xfer", None)
    context.user_data.pop("settle", None)
    context.user_data.pop("borrow", None)
    context.user_data.pop("lend", None)
    await update.effective_message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


@authorized
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"📖 <b>Help — Commands</b>\n{SEP}\n"
        f"<b>📝 Logging</b>\n"
        f"  Send a number → start a transaction\n"
        f"  /expense 50k food — quick expense\n"
        f"  /ob — opening balance\n"
        f"  /transfer — transfer between accounts\n"
        f"  /receipt — log from receipt photo\n"
        f"  /borrow — record money borrowed\n"
        f"  /lend — record money lent\n"
        f"  /settle — settle a debt\n"
        f"{SEP}\n"
        f"<b>📊 Reports</b>\n"
        f"  /start — dashboard\n"
        f"  /balance — monthly balance\n"
        f"  /summary [YYYY-MM] — monthly summary\n"
        f"  /lastmonth — last month\n"
        f"  /today — today's transactions\n"
        f"  /weekly — last 7 days\n"
        f"  /cashflow — 5-month cashflow\n"
        f"  /compare [M1] [M2] — compare two months\n"
        f"  /forecast — month-end forecast\n"
        f"  /split [YYYY-MM] — business vs personal\n"
        f"  /top [N] — top expense categories\n"
        f"  /project — project P&L\n"
        f"{SEP}\n"
        f"<b>💳 Accounts & Assets</b>\n"
        f"  /accounts — account balances\n"
        f"  /networth — net worth\n"
        f"  /debts — debts summary\n"
        f"{SEP}\n"
        f"<b>💱 FX</b>\n"
        f"  /fx 100 USD — convert currency\n"
        f"  /setrate USD 4500 — set exchange rate\n"
        f"{SEP}\n"
        f"<b>📱 SaaS & Budget</b>\n"
        f"  /saas — SaaS services list\n"
        f"  /budget [amount] — set or view budget\n"
        f"  /remind HH:MM — set daily reminder\n"
        f"{SEP}\n"
        f"<b>🔧 Management</b>\n"
        f"  /history [n] — view transactions\n"
        f"  /search [keyword] — search transactions\n"
        f"  /export [YYYY-MM] — export CSV\n"
        f"  /edit — edit last transaction\n"
        f"  /delete — delete last transaction\n"
        f"  /ping — check bot status\n"
        f"  /reload — reload settings\n"
        f"  /cancel — cancel current action"
    )
    await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)


# ─── Edit / Delete Last Transaction ──────────────────────────────────────────
async def cb_edit_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    row_num = context.user_data.get("last_tx_row")
    if not row_num:
        await q.answer("No transaction found.", show_alert=True)
        return
    await q.answer()
    await q.edit_message_text(
        f"✏️ <b>Edit transaction #{row_num}</b>\n{SEP}\n"
        "Type the new amount — or use /history to browse transactions.",
        parse_mode=ParseMode.HTML
    )


async def cb_del_last(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    row_num = context.user_data.get("last_tx_row")
    if not row_num:
        await q.answer("No transaction found.", show_alert=True)
        return
    await q.answer()
    kb = InlineKeyboardMarkup([[
        _btn("✅ Yes, delete", f"delconfirm_{row_num}"),
        _btn("❌ No, keep",    "delcancel"),
    ]])
    await q.edit_message_text(
        f"🗑 Delete transaction <b>#{row_num}</b>? This cannot be undone.",
        parse_mode=ParseMode.HTML, reply_markup=kb
    )


async def cb_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    row_num = int(q.data.replace("delconfirm_", ""))
    try:
        await _sh(delete_tx_row, row_num)
        context.user_data.pop("last_tx_row", None)
        await q.edit_message_text(f"🗑 Transaction <b>#{row_num}</b> deleted.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await q.edit_message_text(f"❌ Delete failed.\n{str(e)[:200]}")


async def cb_del_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("Cancelled.")
    await q.edit_message_text("↩️ Delete cancelled.")


# ─── Quick-Start Button Callbacks ─────────────────────────────────────────────
async def cb_quickstart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    await q.answer()
    action = q.data.replace("qs_", "")
    dispatch = {
        "balance":  cmd_balance,
        "summary":  cmd_summary,
        "today":    cmd_today,
        "weekly":   cmd_weekly,
        "accounts": cmd_accounts,
        "debts":    cmd_debts,
        "help":     cmd_help,
    }
    fn = dispatch.get(action)
    if fn:
        await fn(update, context)


async def cb_today_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()


# ─── Error Handler ────────────────────────────────────────────────────────────
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled exception", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An error occurred. Use /cancel to reset and try again."
            )
        except Exception:
            pass


# ─── Command Menu Registration ────────────────────────────────────────────────
async def post_init(application):
    await application.bot.set_my_commands([
        BotCommand("start",     "Dashboard & summary"),
        BotCommand("balance",   "Monthly income/expense balance"),
        BotCommand("summary",   "Monthly summary [YYYY-MM]"),
        BotCommand("lastmonth", "Last month summary"),
        BotCommand("today",     "Today's transactions"),
        BotCommand("weekly",    "Last 7 days"),
        BotCommand("cashflow",  "5-month cashflow"),
        BotCommand("compare",   "Compare two months"),
        BotCommand("forecast",  "Month-end forecast"),
        BotCommand("split",     "Business vs personal split"),
        BotCommand("top",       "Top expense categories"),
        BotCommand("accounts",  "Account balances"),
        BotCommand("networth",  "Net worth"),
        BotCommand("debts",     "Debts summary"),
        BotCommand("project",   "Project P&L"),
        BotCommand("expense",   "Quick expense: /expense 50k food"),
        BotCommand("transfer",  "Record a transfer"),
        BotCommand("ob",        "Add opening balance"),
        BotCommand("settle",    "Settle a debt"),
        BotCommand("borrow",    "Record money borrowed"),
        BotCommand("lend",      "Record money lent"),
        BotCommand("receipt",   "Log from receipt photo"),
        BotCommand("history",   "View transactions"),
        BotCommand("search",    "Search transactions"),
        BotCommand("export",    "Export CSV [YYYY-MM]"),
        BotCommand("budget",    "Set or view budget"),
        BotCommand("saas",      "View SaaS services"),
        BotCommand("fx",        "Convert currency: /fx 100 USD"),
        BotCommand("setrate",   "Set exchange rate: /setrate USD 4500"),
        BotCommand("remind",    "Set daily reminder: /remind 21:00"),
        BotCommand("reload",    "Reload settings"),
        BotCommand("ping",      "Check bot status"),
        BotCommand("cancel",    "Cancel current action"),
    ])

    # Start the async cache warmer inside the event loop
    asyncio.create_task(_async_cache_warmer_loop())


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")

    _bot_dir = os.path.dirname(os.path.abspath(__file__))
    pkl_path = os.path.join(_bot_dir, "conversation_state.pkl")
    sa_path  = os.path.join(_bot_dir, "service_account.json")
    # Update global SA path so _sheet_client() finds it
    global _SA_PATH
    _SA_PATH = sa_path

    persistence = PicklePersistence(filepath=pkl_path)
    app = (
        Application.builder()
        .token(token)
        .persistence(persistence)
        .post_init(post_init)
        .build()
    )

    # ── Restore saved reminders ──
    reminders = app.bot_data.get("reminders", {})
    for uid, info in reminders.items():
        _schedule_reminder(app, uid, info["hour"], info["minute"])

    # ── ConversationHandlers (must be before simple handlers) ──
    ob_conv = ConversationHandler(
        entry_points=[CommandHandler("ob", ob_start)],
        states={
            OB_SELECT_TYPE:  [CallbackQueryHandler(ob_type_cb, pattern=r"^ob_")],
            OB_ENTER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ob_amount_entry)],
            OB_ENTER_NAME:   [MessageHandler(filters.TEXT & ~filters.COMMAND, ob_name_entry)],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        per_message=False,
        persistent=True,
        name="ob_conv",
    )

    xfer_conv = ConversationHandler(
        entry_points=[
            CommandHandler("transfer", xfer_start_cmd),
            CallbackQueryHandler(xfer_start_cb, pattern=r"^xfer_start$"),
        ],
        states={
            XFER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, xfer_amount_entry)],
            XFER_FROM:   [CallbackQueryHandler(xfer_from_cb, pattern=r"^xfrom_")],
            XFER_TO:     [CallbackQueryHandler(xfer_to_cb,   pattern=r"^xto_")],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        per_message=False,
        persistent=True,
        name="xfer_conv",
    )

    settle_conv = ConversationHandler(
        entry_points=[CommandHandler("settle", settle_start)],
        states={
            SETTLE_TYPE:   [CallbackQueryHandler(settle_type_cb,   pattern=r"^settle_")],
            SETTLE_PERSON: [CallbackQueryHandler(settle_person_cb, pattern=r"^sperson_")],
            SETTLE_AMT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, settle_amt_entry)],
            SETTLE_ACC:    [CallbackQueryHandler(settle_acc_cb,    pattern=r"^sacc_")],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        per_message=False,
        persistent=True,
        name="settle_conv",
    )

    borrow_conv = ConversationHandler(
        entry_points=[CommandHandler("borrow", borrow_start)],
        states={
            BORROW_PERSON: [CallbackQueryHandler(borrow_person_cb, pattern=r"^bperson_"),
                            MessageHandler(filters.TEXT & ~filters.COMMAND, borrow_name_entry)],
            BORROW_NAME:   [MessageHandler(filters.TEXT & ~filters.COMMAND, borrow_name_entry)],
            BORROW_AMT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, borrow_amt_entry)],
            BORROW_ACC:    [CallbackQueryHandler(borrow_acc_cb, pattern=r"^bacc_")],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        per_message=False,
        persistent=True,
        name="borrow_conv",
    )

    lend_conv = ConversationHandler(
        entry_points=[CommandHandler("lend", lend_start)],
        states={
            LEND_PERSON: [CallbackQueryHandler(lend_person_cb, pattern=r"^lperson_"),
                          MessageHandler(filters.TEXT & ~filters.COMMAND, lend_name_entry)],
            LEND_NAME:   [MessageHandler(filters.TEXT & ~filters.COMMAND, lend_name_entry)],
            LEND_AMT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, lend_amt_entry)],
            LEND_ACC:    [CallbackQueryHandler(lend_acc_cb, pattern=r"^lacc_")],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        per_message=False,
        persistent=True,
        name="lend_conv",
    )

    receipt_conv = ConversationHandler(
        entry_points=[CommandHandler("receipt", receipt_start)],
        states={
            PHOTO_SCOPE: [MessageHandler(filters.PHOTO, receipt_photo)],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        per_message=False,
        name="receipt_conv",
    )

    tx_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^[0-9]") & ~filters.COMMAND, tx_amount_entry),
            CommandHandler("expense", expense_start),
            CommandHandler("edit",    cmd_edit),
        ],
        states={
            SCOPE_STEP:    [CallbackQueryHandler(tx_scope_cb,    pattern=r"^scope_")],
            PROJECT_STEP:  [CallbackQueryHandler(tx_project_cb,  pattern=r"^proj_")],
            CATEGORY_STEP: [CallbackQueryHandler(tx_category_cb, pattern=r"^cat_"),
                            CallbackQueryHandler(tx_category_cb, pattern=r"^__back__$")],
            ACCOUNT_STEP:  [CallbackQueryHandler(tx_account_cb,  pattern=r"^acc_"),
                            CallbackQueryHandler(tx_account_cb,  pattern=r"^__back__$")],
            EXPENSE_AMT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, tx_edit_amount)],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        per_message=False,
        persistent=True,
        name="tx_conv",
    )

    # Register conversation handlers FIRST
    app.add_handler(ob_conv)
    app.add_handler(xfer_conv)
    app.add_handler(settle_conv)
    app.add_handler(borrow_conv)
    app.add_handler(lend_conv)
    app.add_handler(receipt_conv)
    app.add_handler(tx_conv)

    # Simple command handlers
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("balance",   cmd_balance))
    app.add_handler(CommandHandler("summary",   cmd_summary))
    app.add_handler(CommandHandler("monthly",   cmd_summary))
    app.add_handler(CommandHandler("lastmonth", cmd_lastmonth))
    app.add_handler(CommandHandler("today",     cmd_today))
    app.add_handler(CommandHandler("weekly",    cmd_weekly))
    app.add_handler(CommandHandler("history",   cmd_history))
    app.add_handler(CommandHandler("export",    cmd_export))
    app.add_handler(CommandHandler("search",    cmd_search))
    app.add_handler(CommandHandler("budget",    cmd_budget))
    app.add_handler(CommandHandler("remind",    cmd_remind))
    app.add_handler(CommandHandler("debts",     cmd_debts))
    app.add_handler(CommandHandler("networth",  cmd_networth))
    app.add_handler(CommandHandler("fx",        cmd_fx))
    app.add_handler(CommandHandler("setrate",   cmd_setrate))
    app.add_handler(CommandHandler("saas",      cmd_saas))
    app.add_handler(CommandHandler("project",   cmd_project))
    app.add_handler(CommandHandler("split",     cmd_split))
    app.add_handler(CommandHandler("accounts",  cmd_accounts))
    app.add_handler(CommandHandler("cashflow",  cmd_cashflow))
    app.add_handler(CommandHandler("compare",   cmd_compare))
    app.add_handler(CommandHandler("forecast",  cmd_forecast))
    app.add_handler(CommandHandler("top",       cmd_top))
    app.add_handler(CommandHandler("delete",    cmd_delete))
    app.add_handler(CommandHandler("ping",      cmd_ping))
    app.add_handler(CommandHandler("reload",    cmd_reload))
    app.add_handler(CommandHandler("cancel",    cmd_cancel))

    # Callback query routers
    app.add_handler(CallbackQueryHandler(cb_quickstart,  pattern=r"^qs_"))
    app.add_handler(CallbackQueryHandler(cb_edit_last,   pattern=r"^edit_last$"))
    app.add_handler(CallbackQueryHandler(cb_del_last,    pattern=r"^del_last$"))
    app.add_handler(CallbackQueryHandler(cb_del_confirm, pattern=r"^delconfirm_\d+$"))
    app.add_handler(CallbackQueryHandler(cb_del_cancel,  pattern=r"^delcancel$"))
    app.add_handler(CallbackQueryHandler(cb_today_nav,   pattern=r"^today_\d{4}-\d{2}-\d{2}$"))
    app.add_handler(CallbackQueryHandler(cb_history_nav, pattern=r"^hist_"))
    app.add_handler(CallbackQueryHandler(cb_project,     pattern=r"^proj_"))

    app.add_error_handler(error_handler)

    logger.info("Bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    import sys

    # Ensure bot/ directory is on the path so keep_alive can be imported
    _bot_dir = os.path.dirname(os.path.abspath(__file__))
    if _bot_dir not in sys.path:
        sys.path.insert(0, _bot_dir)

    # Single-instance lock
    _lock_path = os.path.join(_bot_dir, "bot.lock")
    lock_file = open(_lock_path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        logger.error("Another bot instance is already running.")
        sys.exit(1)

    # Validate required env vars upfront — fail fast before entering the loop
    _token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    _sid   = os.environ.get("SHEET_ID", "")
    if not _token:
        logger.error("TELEGRAM_BOT_TOKEN not set. Set it in Secrets and restart.")
        sys.exit(1)
    if not _sid:
        logger.error("SHEET_ID not set. Set it in Secrets and restart.")
        sys.exit(1)

    # Start keep-alive Flask server
    def _today_data():
        now = datetime.now(tz=TZ)
        try:
            s = get_monthly_summary(now.year, now.month)
            tx_rows_all = get_tx_rows()
            today_str   = now.strftime("%Y-%m-%d")
            today_exp   = sum(
                float(r[8]) for r in tx_rows_all
                if len(r) > 8 and str(r[4]).strip() == "Expense"
                and (_parse_row_date(r) or date.min).strftime("%Y-%m-%d") == today_str
                and r[8] != ""
            )
            return {
                "today_expense": today_exp,
                "month_income":  s.get("income", 0.0),
                "month_expense": s.get("expense", 0.0),
                "month_net":     s.get("net", 0.0),
            }
        except Exception as e:
            return {"error": str(e)}

    import keep_alive
    keep_alive.start(invalidate_all_caches, _today_data)

    # Self-healing loop
    while True:
        try:
            main()
        except KeyboardInterrupt:
            break
        except SystemExit:
            break
        except RuntimeError as e:
            if "event loop is closed" in str(e).lower():
                break
            logger.error("Crash — restarting in 5s", exc_info=True)
            time.sleep(5)
        except Exception:
            logger.error("Crash — restarting in 5s", exc_info=True)
            time.sleep(5)
