"""
PS VIBE Sales Bot — HTTP API Client
====================================
Wraps all 48 endpoints from the local FastAPI server (localhost:8000).

Uses only stdlib (urllib, json, os, logging) — no external dependencies.

API key auth is sent as an ``?api_key=...`` query parameter on every call,
which the server accepts alongside the ``X-API-Key`` header.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
import urllib.parse
import time

# ---------------------------------------------------------------------------
# Module-level config
# ---------------------------------------------------------------------------
API_BASE_URL = os.environ.get("API_BASE_URL", "").rstrip("/")
API_KEY = os.environ.get("API_KEY", "")

logger = logging.getLogger("psvibe_api_client")

DEFAULT_TIMEOUT = 15  # Increased for reliability
DEFAULT_MAX_RETRIES = 2  # Exponential backoff: 3 total attempts (1 + 2 retries)
DEFAULT_RETRY_BASE_DELAY = 0.5  # Seconds, doubles each retry


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _api_call(
    method: str,
    path: str,
    params: dict | None = None,
    json_data: dict | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict | None:
    """Generic API call.

    Parameters
    ----------
    method : str
        HTTP method (GET / POST / PUT / DELETE).
    path : str
        API path relative to ``/api/``, e.g. ``"health"`` or ``"fetch_members"``.
        May include a leading slash (ignored).
    params : dict | None
        Extra query-string parameters.
    json_data : dict | None
        JSON body for POST / PUT / DELETE requests.
    timeout : int
        Seconds before the request times out (default 10).

    Returns
    -------
    dict | None
        Parsed JSON response on success; ``None`` on any error.
    """
    if not API_BASE_URL:
        logger.warning("API_BASE_URL is not set – skipping API call %s %s", method, path)
        return None

    # Build URL:  {base}/api/{path}?api_key=...&...
    path_clean = path.lstrip("/")
    url = f"{API_BASE_URL}/api/{path_clean}"

    qs_parts = {}
    if API_KEY:
        qs_parts["api_key"] = API_KEY
    if params:
        qs_parts.update(params)

    if qs_parts:
        query = urllib.parse.urlencode(qs_parts)
        url = f"{url}?{query}"

    # Build request
    data_bytes = None
    headers: dict[str, str] = {}

    if json_data is not None:
        data_bytes = json.dumps(json_data, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data_bytes, method=method, headers=headers)

    last_error: Exception | None = None
    for attempt in range(DEFAULT_MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body)
                # Unwrap API envelope: {success: true, data: ...}
                if isinstance(data, dict) and 'success' in data:
                    if not data.get('success'):
                        logger.warning(
                            'API %s %s responded success=false: %s',
                            method, path_clean, data.get('error', 'unknown'),
                        )
                        return None
                    return data.get('data')
                return data
        except Exception as exc:
            last_error = exc
            if attempt < DEFAULT_MAX_RETRIES:
                delay = DEFAULT_RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    'API %s %s attempt %d/%d failed: %s, retrying in %.1fs...',
                    method, path_clean, attempt + 1, DEFAULT_MAX_RETRIES + 1, exc, delay,
                )
                time.sleep(delay)
            else:
                logger.warning(
                    'API %s %s failed after %d attempts: %s',
                    method, path_clean, DEFAULT_MAX_RETRIES + 1, exc,
                )
    return None


# ===================================================================
#  GET  endpoints
# ===================================================================


def api_health() -> dict | None:
    """Check API server health."""
    return _api_call("GET", "health")


def api_fetch_console_status() -> dict | None:
    """Fetch active/free status for all consoles."""
    return _api_call("GET", "fetch_console_status")


def api_fetch_members() -> dict | None:
    """Fetch all member records."""
    return _api_call("GET", "fetch_members")


def api_fetch_member_data(member_id: str) -> dict | None:
    """Fetch full data for a single member."""
    return _api_call("GET", f"fetch_member_data/{member_id}")


def api_fetch_wallet_mins(member_id: str) -> dict | None:
    """Fetch wallet minutes for a member."""
    return _api_call("GET", f"fetch_wallet_mins/{member_id}")


def api_fetch_balance_mins(member_id: str) -> dict | None:
    """Fetch remaining balance minutes for a member."""
    return _api_call("GET", f"fetch_balance_mins/{member_id}")


def api_fetch_member_tier(member_id: str) -> dict | None:
    """Fetch tier/rank info for a member."""
    return _api_call("GET", f"fetch_member_tier/{member_id}")


def api_fetch_staff() -> list | None:
    """Fetch staff list (raw)."""
    return _api_call("GET", "fetch_staff")


def api_fetch_staff_names() -> list | None:
    """Fetch display-friendly staff names."""
    return _api_call("GET", "fetch_staff_names")


def api_fetch_food_prices() -> dict | None:
    """Fetch food price table."""
    return _api_call("GET", "fetch_food_prices")


def api_fetch_food_costs() -> dict | None:
    """Fetch food cost table."""
    return _api_call("GET", "fetch_food_costs")


def api_fetch_games() -> dict | None:
    """Fetch games list."""
    return _api_call("GET", "fetch_games")


def api_fetch_game_library() -> dict | None:
    """Fetch full game library."""
    return _api_call("GET", "fetch_game_library")


def api_fetch_console_games() -> dict | None:
    """Fetch all console-games mapping."""
    return _api_call("GET", "fetch_console_games")


def api_get_games_on_console(console_id: str) -> dict | None:
    """Get games installed on a specific console."""
    return _api_call("GET", f"get_games_on_console/{console_id}")


def api_get_consoles_with_game(game_title: str | None = None) -> dict | None:
    """Search which consoles have a given game installed."""
    params = {}
    if game_title:
        params["game_title"] = game_title
    return _api_call("GET", "get_consoles_with_game", params=params)


def api_fetch_base_rate() -> dict | None:
    """Fetch the default hourly rate."""
    return _api_call("GET", "fetch_base_rate")


def api_fetch_console_multiplier(console_id: str) -> dict | None:
    """Fetch rate multiplier for a console."""
    return _api_call("GET", f"fetch_console_multiplier/{console_id}")


def api_fetch_new_member_defaults() -> dict | None:
    """Fetch default values for new members."""
    return _api_call("GET", "fetch_new_member_defaults")


def api_fetch_rank_thresholds() -> dict | None:
    """Fetch rank/tier thresholds."""
    return _api_call("GET", "fetch_rank_thresholds")


def api_fetch_bonus_table() -> dict | None:
    """Fetch bonus minutes table."""
    return _api_call("GET", "fetch_bonus_table")


def api_fetch_rank_table_display() -> dict | None:
    """Fetch formatted rank table for display."""
    return _api_call("GET", "fetch_rank_table_display")


def api_fetch_alltime_effective_rate() -> dict | None:
    """Fetch the all-time effective rate."""
    return _api_call("GET", "fetch_alltime_effective_rate")


def api_fetch_member_effective_rate(member_id: str) -> dict | None:
    """Fetch effective rate for a specific member."""
    return _api_call("GET", f"fetch_member_effective_rate/{member_id}")


def api_build_member_rate_dict() -> dict | None:
    """Build a dict of member_id → effective_rate."""
    return _api_call("GET", "build_member_rate_dict")


def api_fetch_base_salaries() -> dict | None:
    """Fetch staff base salary table."""
    return _api_call("GET", "fetch_base_salaries")


def api_fetch_attendance(month_str: str) -> dict | None:
    """Fetch attendance log for a given month (e.g. '5/2026')."""
    return _api_call("GET", f"fetch_attendance/{month_str}")


def api_fetch_salary_advances(month_str: str) -> dict | None:
    """Fetch salary advance log for a given month."""
    return _api_call("GET", f"fetch_salary_advances/{month_str}")


def api_fetch_promotions_cached() -> dict | None:
    """Fetch cached promotions."""
    return _api_call("GET", "fetch_promotions_cached")


def api_fetch_allowed_staff_ids() -> dict | None:
    """Fetch the list of allowed staff Telegram IDs."""
    return _api_call("GET", "fetch_allowed_staff_ids")


def api_next_voucher() -> dict | None:
    """Get the next available voucher number."""
    return _api_call("GET", "next_voucher")


def api_next_member_id() -> dict | None:
    """Get the next auto-generated member ID."""
    return _api_call("GET", "next_member_id")


def api_next_member_row_no() -> dict | None:
    """Get the next available member row number."""
    return _api_call("GET", "next_member_row_no")


def api_fetch_referral_code(member_id: str) -> dict | None:
    """Fetch the referral code for a member."""
    return _api_call("GET", f"fetch_referral_code/{member_id}")


def api_fetch_sheets_config() -> dict | None:
    """Fetch spreadsheet configuration metadata."""
    return _api_call("GET", "sheets/config")


# ===================================================================
#  POST endpoints
# ===================================================================


def api_create_booking(
    console_id: str,
    member_id: str,
    staff: str,
    notes: str = "",
    planned_end: str = "",
) -> dict | None:
    """Create a new console booking. Returns booking_id on success."""
    payload: dict = {
        "console_id": console_id,
        "member_id": member_id,
        "staff": staff,
        "notes": notes,
    }
    if planned_end:
        payload["planned_end"] = planned_end
    return _api_call("POST", "create_booking", json_data=payload)


def api_save_attendance(
    month_str: str,
    staff: str,
    leave_days: int = 0,
    late_count: int = 0,
    deduct_per_late: int = 500,
) -> dict | None:
    """Save or update a staff attendance record."""
    return _api_call(
        "POST",
        "save_attendance",
        json_data={
            "month_str": month_str,
            "staff": staff,
            "leave_days": leave_days,
            "late_count": late_count,
            "deduct_per_late": deduct_per_late,
        },
    )


def api_save_receipt_json(voucher_id: str, data: dict) -> dict | None:
    """Persist receipt JSON data via the API."""
    return _api_call(
        "POST",
        "save_receipt_json",
        json_data={"voucher_id": voucher_id, "data": data},
    )


def api_add_console_game(
    console_id: str,
    game_title: str,
    install_type: str,
    notes: str = "",
) -> dict | None:
    """Add a game installation record to a console."""
    return _api_call(
        "POST",
        "add_console_game",
        json_data={
            "console_id": console_id,
            "game_title": game_title,
            "install_type": install_type,
            "notes": notes,
        },
    )


def api_save_referral_code(member_id: str, code: str) -> dict | None:
    """Save/update a member's referral code."""
    return _api_call(
        "POST",
        "save_referral_code",
        json_data={"member_id": member_id, "code": code},
    )


def api_add_console_to_setting(
    console_id: str,
    ctype: str,
    multiplier: float = 1.0,
) -> dict | None:
    """Add a new console entry to the Setting sheet."""
    return _api_call(
        "POST",
        "add_console_to_setting",
        json_data={
            "console_id": console_id,
            "ctype": ctype,
            "multiplier": multiplier,
        },
    )


# ===================================================================
#  PUT  endpoints
# ===================================================================


def api_end_booking(booking_id: str) -> dict | None:
    """Mark a booking as Done and record the end time."""
    return _api_call("PUT", f"end_booking/{booking_id}")


def api_cancel_booking(booking_id: str) -> dict | None:
    """Cancel an active booking."""
    return _api_call("PUT", f"cancel_booking/{booking_id}")


def api_set_game_disc_count(row_num: int, count: int) -> dict | None:
    """Update the available-disc count for a game library row."""
    return _api_call(
        "PUT",
        "set_game_disc_count",
        json_data={"row_num": row_num, "count": count},
    )


def api_update_game_library_install(
    game_title: str,
    console_id: str,
    installed: bool,
) -> dict | None:
    """Toggle the install checkbox for a game on a console."""
    return _api_call(
        "PUT",
        "update_game_library_install",
        json_data={
            "game_title": game_title,
            "console_id": console_id,
            "installed": installed,
        },
    )


def api_update_member_effective_rate(
    member_id: str,
    new_rate: float,
) -> dict | None:
    """Update the effective rate for a member."""
    return _api_call(
        "PUT",
        "update_member_effective_rate",
        json_data={"member_id": member_id, "rate": new_rate},
    )


# ===================================================================
#  DELETE endpoints
# ===================================================================


def api_remove_console_game(console_id: str, game_title: str) -> dict | None:
    """Remove a game installation from a console."""
    return _api_call(
        "DELETE",
        "remove_console_game",
        json_data={"console_id": console_id, "game_title": game_title},
    )


def api_remove_console_from_setting(console_id: str) -> dict | None:
    """Remove a console entry from the Setting sheet."""
    return _api_call("DELETE", f"remove_console_from_setting/{console_id}")

# ===================================================================
#  Phase 2 – New POST endpoints
# ===================================================================


def api_add_opex(data: dict) -> dict | None:
    """Add an operational expense record."""
    return _api_call("POST", "finance/opex", json_data=data)


def api_add_salary_advance(data: dict) -> dict | None:
    """Add a salary advance record."""
    return _api_call("POST", "staff/salary-advance", json_data=data)


def api_add_sales_record(data: dict) -> dict | None:
    """Add a sales record.

    Transforms caller field names to match /api/sales/record endpoint expectations.
    """
    # Map caller field names → endpoint field names
    mapped: dict = {
        "receipt_no": data.get("voucher_no", ""),
        "receipt_date": data.get("date", ""),
        "member_id": data.get("member_id", ""),
        "amount": data.get("net_total", 0),
        "items": f"Console:{data.get('console_id','')}|Play:{data.get('play_mins',0)}min|Game:{data.get('game_amount',0)}",
        "payment_method": f"KPay:{data.get('kpay',0)}|Cash:{data.get('cash',0)}",
        "staff_name": data.get("staff", ""),
        "food_items": str(data.get("food_total", "")),
        "food_cost": data.get("food_total", 0),
    }
    return _api_call("POST", "sales/record", json_data=mapped)


def api_add_stock_out(data: dict) -> dict | None:
    """Add a stock-out (sale/consumption) record."""
    return _api_call("POST", "inventory/stock-out", json_data=data)


def api_add_stock_in(data: dict) -> dict | None:
    """Add a stock-in (restock) record."""
    return _api_call("POST", "inventory/stock-in", json_data=data)


def api_add_member(data: dict) -> dict | None:
    """Register a new member."""
    return _api_call("POST", "members/register", json_data=data)


def api_add_topup(data: dict) -> dict | None:
    """Log a top-up transaction."""
    return _api_call("POST", "topup/log", json_data=data)
