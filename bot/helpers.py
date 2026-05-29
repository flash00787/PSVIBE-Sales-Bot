# bot/helpers.py — Pure utility functions (no database, no API calls)
#
# Extracted from bot/__init__.py to improve modularity.
# Imported back by __init__.py for 100% backward compatibility.
from bot import BOT_VERSION, MMT, RECEIPTS_DIR, base, cleaned, data, date, empty, filled, get_receipt_kb, get_receipt_url, m, n, now, now_mmt, path, payload, req, s, safe_id, save_receipt_json, secret, step_hdr, today, today_str, total, url, val, w

import json
import logging
import os
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ═════════════════════════════════════════
#  DATETIME HELPERS
# ═════════════════════════════════════════

# Myanmar Time — GMT+6:30
MMT = timezone(timedelta(hours=6, minutes=30))

def now_mmt() -> datetime:
    """Return current time in Myanmar Time (UTC+6:30)."""
    return datetime.now(MMT)

BOT_VERSION = "2026.05.05-r1"   # Console double-booking conflict check (409 guard)

def today_str() -> str:
    """Return today's date in M/D/YYYY format (Myanmar Time)."""
    return now_mmt().strftime("%-m/%-d/%Y")


# ═════════════════════════════════════════
#  UI / FORMAT HELPERS
# ═════════════════════════════════════════

def _int(val):
    """Safe int from sheet value — strips commas, 'Ks', spaces, handles floats."""
    try:
        cleaned = str(val).replace(",", "").replace("Ks", "").strip()
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0

def step_hdr(step: int, total: int, label: str) -> str:
    """Return a Form Wizard progress header for every prompt message."""
    filled = "▰" * step
    empty  = "▱" * (total - step)
    return f"*{label}*\n`{filled}{empty}` _({step}/{total})_\n━━━━━━━━━━━━━━━━━━\n"


# ═════════════════════════════════════════
#  RECEIPT HELPERS
# ═════════════════════════════════════════

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
