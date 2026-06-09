"""PS VIBE API Server — Google Sheets Client"""
import time
import logging
import functools
from typing import Optional

import gspread
from gspread.exceptions import APIError

from config import (
    SERVICE_ACCOUNT_FILE, SHEETS_SCOPES, SHEET_ID,
    SHEET_CARD_WALLET, SHEET_CONSOLE_BOOKING,
    SHEET_GAME_LIBRARY, SHEET_CONSOLE_GAMES,
    CACHE_TTL_MEMBERS, CACHE_TTL_BOOKINGS,
    CACHE_TTL_GAMES, CACHE_TTL_CONSOLE_GAMES,
)

logger = logging.getLogger(__name__)

# ── Retry Decorator ──
_SHEETS_RETRY_CODES = (429, 500, 503)
_SHEETS_MAX_RETRIES = 3
_SHEETS_BASE_DELAY = 1


def _sheets_retry(func):
    """Retry gspread calls on transient API errors with exponential backoff."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        last_exc = None
        for attempt in range(_SHEETS_MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                code = e.response.status_code if hasattr(e, "response") else 0
                if code in _SHEETS_RETRY_CODES and attempt < _SHEETS_MAX_RETRIES:
                    delay = _SHEETS_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "Sheets API %d error (attempt %d/%d), retrying in %ds",
                        code, attempt + 1, _SHEETS_MAX_RETRIES, delay,
                    )
                    time.sleep(delay)
                    last_exc = e
                else:
                    raise
            except (ConnectionError, TimeoutError, OSError) as e:
                if attempt < _SHEETS_MAX_RETRIES:
                    delay = _SHEETS_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "Sheets network error (attempt %d/%d), retrying in %ds",
                        attempt + 1, _SHEETS_MAX_RETRIES, delay,
                    )
                    time.sleep(delay)
                    last_exc = e
                else:
                    raise
        raise last_exc or RuntimeError("max retries exceeded")
    return wrapper


# ── Singleton Sheet Client ──
_gc: Optional[gspread.Client] = None
_wb: Optional[gspread.Spreadsheet] = None
_worksheets: dict = {}


def _authorize() -> gspread.Client:
    global _gc
    if _gc is not None:
        return _gc
    logger.info("Authorizing Google Sheets with SA: %s", SERVICE_ACCOUNT_FILE)
    _gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE, scopes=SHEETS_SCOPES)
    return _gc


def get_workbook() -> gspread.Spreadsheet:
    global _wb
    if _wb is not None:
        return _wb
    gc = _authorize()
    _wb = gc.open_by_key(SHEET_ID)
    return _wb


def get_worksheet(name: str) -> gspread.Worksheet:
    global _worksheets
    if name in _worksheets:
        return _worksheets[name]
    wb = get_workbook()
    try:
        ws = wb.worksheet(name)
    except Exception:
        logger.info("Creating worksheet: %s", name)
        ws = wb.add_worksheet(name, rows=1000, cols=20)
    _worksheets[name] = ws
    return ws


def int_safe(val) -> int:
    if val is None:
        return 0
    try:
        s = str(val).replace(",", "").strip()
        return int(float(s)) if s else 0
    except (ValueError, TypeError):
        return 0


def float_safe(val) -> float:
    if val is None:
        return 0.0
    try:
        s = str(val).replace(",", "").strip()
        return float(s) if s else 0.0
    except (ValueError, TypeError):
        return 0.0


# ── Caches ──
_CFG: dict = {}
_CFG_TS: float = 0.0

_MBR_ROWS: list = []
_MBR_TS: float = 0.0

_BK_ROWS: list = []
_BK_TS: float = 0.0

_GAME_ROWS: list = []
_GAME_TS: float = 0.0

_CGAME_ROWS: list = []
_CGAME_TS: float = 0.0


def _cache_valid(ts: float, ttl: int) -> bool:
    return ts > 0 and (time.time() - ts) < ttl


def get_member_rows() -> list:
    global _MBR_ROWS, _MBR_TS
    if not _cache_valid(_MBR_TS, CACHE_TTL_MEMBERS):
        try:
            ws = get_worksheet(SHEET_CARD_WALLET)
            _MBR_ROWS = ws.get_all_values()
            _MBR_TS = time.time()
        except Exception as e:
            logger.warning("Member cache refresh failed: %s", e)
    return _MBR_ROWS


def get_booking_rows() -> list:
    global _BK_ROWS, _BK_TS
    if not _cache_valid(_BK_TS, CACHE_TTL_BOOKINGS):
        try:
            _BK_ROWS = get_worksheet(SHEET_CONSOLE_BOOKING).get_all_values()
            _BK_TS = time.time()
        except Exception as e:
            logger.warning("Booking cache refresh failed: %s", e)
    return _BK_ROWS


def get_game_rows() -> list:
    global _GAME_ROWS, _GAME_TS
    if not _cache_valid(_GAME_TS, CACHE_TTL_GAMES):
        try:
            _GAME_ROWS = get_worksheet(SHEET_GAME_LIBRARY).get_all_values()
            _GAME_TS = time.time()
        except Exception as e:
            logger.warning("Game cache refresh failed: %s", e)
    return _GAME_ROWS


def get_console_game_rows() -> list:
    global _CGAME_ROWS, _CGAME_TS
    if not _cache_valid(_CGAME_TS, CACHE_TTL_CONSOLE_GAMES):
        try:
            _CGAME_ROWS = get_worksheet(SHEET_CONSOLE_GAMES).get_all_values()
            _CGAME_TS = time.time()
        except Exception as e:
            logger.warning("Console games cache refresh failed: %s", e)
    return _CGAME_ROWS


def invalidate_cache(*names: str) -> None:
    global _MBR_TS, _BK_TS, _GAME_TS, _CGAME_TS
    for name in names:
        if name == "members":
            _MBR_TS = 0.0
        elif name == "bookings":
            _BK_TS = 0.0
        elif name == "games":
            _GAME_TS = 0.0
        elif name == "console_games":
            _CGAME_TS = 0.0
        elif name == "all":
            _MBR_TS = _BK_TS = _GAME_TS = _CGAME_TS = 0.0
