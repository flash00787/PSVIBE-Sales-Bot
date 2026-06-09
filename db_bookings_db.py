"""
PS VIBE V2 — Bookings Database Module
CRUD operations for Console_Booking with SQLite cache layer.
"""

import json
import logging
import time
from datetime import datetime, timezone, timedelta

from .core import (
    get_sheet_safe, _get_conn, _cursor,
    cache_get, cache_set,
)

logger = logging.getLogger("psvibe.db.bookings")

MMT = timezone(timedelta(hours=6, minutes=30))

def now_mmt():
    return datetime.now(MMT)

def today_str():
    return now_mmt().strftime("%-m/%-d/%Y")


# ── Booking Helpers ──────────────────────────────────────────────────────────

def _row_to_booking(row: list) -> dict:
    """Convert a sheet row to booking dict."""
    return {
        "booking_id": row[0].strip() if len(row) > 0 else "",
        "date": row[1].strip() if len(row) > 1 else "",
        "console_id": row[2].strip() if len(row) > 2 else "",
        "member_id": row[3].strip() if len(row) > 3 else "",
        "start_time": row[4].strip() if len(row) > 4 else "",
        "end_time": row[5].strip() if len(row) > 5 else "",
        "status": row[6].strip() if len(row) > 6 else "",
        "staff": row[7].strip() if len(row) > 7 else "",
        "notes": row[8].strip() if len(row) > 8 else "",
    }


def _get_all_bookings() -> list[dict]:
    """Fetch all bookings from Console_Booking sheet."""
    sh = get_sheet_safe("Console_Booking", rows=1000, cols=9,
                        headers=["BookingID", "Date", "ConsoleID", "MemberID",
                                 "StartTime", "EndTime", "Status", "Staff", "Notes"])
    rows = sh.get_all_values()
    bookings = []
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        bookings.append(_row_to_booking(row))
    return bookings


# ── CRUD Functions ───────────────────────────────────────────────────────────

def database_bookings_list(status: str = "", member_id: str = "") -> list[dict]:
    """List bookings, optionally filtered by status or member_id."""
    try:
        bookings = _get_all_bookings()

        if status:
            status = status.strip().lower()
            # Map API status to sheet status
            status_map = {
                "pending": "Scheduled",
                "confirmed": "Scheduled",
                "active": "Active",
                "done": "Done",
                "cancelled": "Cancelled",
            }
            sheet_status = status_map.get(status, status.capitalize())
            bookings = [b for b in bookings if b["status"].lower() == sheet_status.lower()]

        if member_id:
            bookings = [b for b in bookings if b["member_id"].strip().lower() == member_id.strip().lower()]

        return bookings
    except Exception as e:
        logger.warning("Failed to list bookings: %s", e)
        return []


def database_bookings_get(booking_id: str) -> dict | None:
    """Get single booking by ID."""
    try:
        # Try cache first
        cached = cache_get("booking_cache", "booking_id", booking_id)
        if cached:
            return json.loads(cached)

        bookings = _get_all_bookings()
        for b in bookings:
            if b["booking_id"] == booking_id.strip():
                # Cache it
                cache_set("booking_cache", "booking_id", booking_id, json.dumps(b, ensure_ascii=False))
                return b
        return None
    except Exception as e:
        logger.warning("Failed to get booking %s: %s", booking_id, e)
        return None


def database_bookings_create(data: dict) -> dict:
    """Create new booking. Returns created booking with ID."""
    try:
        now = now_mmt()
        date = now.strftime("%-m/%-d/%Y")
        time_s = now.strftime("%H:%M")
        console_id = data.get("console_id", "").strip()
        member_id = data.get("member_id", "").strip()
        seq = now.strftime("%H%M")
        bk_id = f"BK-{now.strftime('%Y%m%d')}-{console_id.replace(' ','').replace('-','')}-{seq}"

        staff = data.get("staff", "")
        notes = data.get("notes", "")
        planned_end = data.get("planned_end", "")

        # Check for conflicts
        bookings = _get_all_bookings()
        for b in bookings:
            if b["status"] == "Active" and b["console_id"] == console_id and b["date"] == date:
                return {"error": "booking conflict", "__status__": 409,
                        "message": f"Console {console_id} is already booked"}

        sh = get_sheet_safe("Console_Booking", rows=1000, cols=9,
                            headers=["BookingID", "Date", "ConsoleID", "MemberID",
                                     "StartTime", "EndTime", "Status", "Staff", "Notes"])
        sh.append_row([bk_id, date, console_id, member_id, time_s, planned_end, "Active", staff, notes],
                      value_input_option="USER_ENTERED")

        booking = {
            "booking_id": bk_id,
            "date": date,
            "console_id": console_id,
            "member_id": member_id,
            "start_time": time_s,
            "end_time": planned_end,
            "status": "Active",
            "staff": staff,
            "notes": notes,
        }

        # Cache it
        cache_set("booking_cache", "booking_id", bk_id, json.dumps(booking, ensure_ascii=False))
        return booking
    except Exception as e:
        logger.warning("Failed to create booking: %s", e)
        return {"error": "create failed", "message": str(e)}


def database_bookings_update_status(booking_id: str, status: str) -> dict:
    """Update booking status. Return 409 on conflict."""
    try:
        sh = get_sheet_safe("Console_Booking", rows=1000, cols=9)
        rows = sh.get_all_values()
        found = False

        # Map status
        status_map = {
            "confirmed": "Scheduled",
            "active": "Active",
            "done": "Done",
            "cancelled": "Cancelled",
        }
        sheet_status = status_map.get(status.lower(), status.capitalize())

        for i, row in enumerate(rows[1:], start=2):
            if row and row[0].strip() == booking_id:
                current_status = row[6].strip() if len(row) > 6 else ""

                # Conflict check: can't activate an already-active console
                if sheet_status == "Active" and current_status != "Active":
                    # Check if console already has an active booking
                    console_id = row[2].strip() if len(row) > 2 else ""
                    date = row[1].strip() if len(row) > 1 else ""
                    for j, r2 in enumerate(rows[1:], start=2):
                        if j != i and len(r2) > 6 and r2[6].strip() == "Active" \
                                and len(r2) > 2 and r2[2].strip() == console_id \
                                and len(r2) > 1 and r2[1].strip() == date:
                            return {"error": "booking conflict", "__status__": 409,
                                    "message": f"Console {console_id} already has an active booking"}

                sh.update(f"G{i}", [[sheet_status]])
                if sheet_status == "Done":
                    now = now_mmt()
                    sh.update(f"F{i}", [[now.strftime("%H:%M")]])

                found = True
                # Invalidate cache
                cache_set("booking_cache", "booking_id", booking_id,
                          json.dumps({**_row_to_booking(row), "status": sheet_status}, ensure_ascii=False))
                break

        if not found:
            return {"error": "not found", "message": f"Booking {booking_id} not found"}

        return {"status": "ok", "booking_id": booking_id, "new_status": sheet_status}
    except Exception as e:
        logger.warning("Failed to update booking %s: %s", booking_id, e)
        return {"error": "update failed", "message": str(e)}


def database_bookings_get_broadcast_targets() -> list[dict]:
    """Get list of broadcast recipients from member data."""
    try:
        from .core import get_sheet
        member_sh = get_sheet("Card_Wallet")
        rows = member_sh.get_all_values()
        targets = []
        for row in rows[1:]:
            if len(row) < 2:
                continue
            member_id = row[1].strip() if len(row) > 1 else ""
            name = row[2].strip() if len(row) > 2 else ""
            phone = row[3].strip() if len(row) > 3 else ""
            if not member_id:
                continue
            targets.append({
                "member_id": member_id,
                "name": name,
                "phone": phone,
            })
        return targets
    except Exception as e:
        logger.warning("Failed to get broadcast targets: %s", e)
        return []


# ── WAITLIST ─────────────────────────────────────────────────────────────────

def database_waitlist_notify(console_id: str) -> dict:
    """Notify next waiting customer for a console."""
    try:
        sh = get_sheet_safe("Waitlist", rows=200, cols=6,
                            headers=["Date", "ConsoleID", "MemberID", "Phone", "Status", "Notes"])
        rows = sh.get_all_values()

        # Find next waiting entry for this console
        for i, row in enumerate(rows[1:], start=2):
            if len(row) < 3:
                continue
            row_console = row[1].strip() if len(row) > 1 else ""
            status = row[4].strip() if len(row) > 4 else ""

            if row_console == console_id and status.lower() in ("waiting", ""):
                member_id = row[2].strip() if len(row) > 2 else ""
                phone = row[3].strip() if len(row) > 3 else ""
                # Mark as notified
                sh.update(f"E{i}", [["Notified"]])
                return {
                    "status": "ok",
                    "notified": True,
                    "console_id": console_id,
                    "member_id": member_id,
                    "phone": phone,
                    "message": f"Notified {member_id} for console {console_id}",
                }

        return {
            "status": "ok",
            "notified": False,
            "console_id": console_id,
            "message": f"No waiting customers for console {console_id}",
        }
    except Exception as e:
        logger.warning("Failed to notify waitlist: %s", e)
        return {"status": "error", "notified": False, "message": str(e)}
