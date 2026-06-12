"""Persistent session reminder store — survives bot restarts.

Module-level functions for saving/loading active session reminders to/from a
JSON file on disk.

Usage:
    from bot.session_reminder_store import (
        persist_reminder, remove_persisted_reminder,
        restore_reminders_async,
    )

    # Save when a remind_loop starts
    persist_reminder(cid, chat_id, member_id, planned_mins, end_t, end_dt_iso)

    # Remove when session ends / extend re-creates
    remove_persisted_reminder(cid, chat_id)

    # Restore on startup — set as post_init in app.py:
    app.post_init = restore_reminders_async
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

_REMINDER_FILE = "/root/psvibe-sales-bot/data/session_reminders.json"


# ── Low-level file helpers ──────────────────────────────────────────────────

def _read_store() -> dict:
    try:
        if not os.path.isfile(_REMINDER_FILE):
            return {}
        with open(_REMINDER_FILE, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("reminder_store read error: %s", e)
        return {}


def _write_store(data: dict) -> None:
    tmp = _REMINDER_FILE + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, _REMINDER_FILE)
    except OSError as e:
        logger.error("reminder_store write error: %s", e)
        try:
            if os.path.isfile(tmp):
                os.remove(tmp)
        except OSError:
            pass


# ── Key helpers ─────────────────────────────────────────────────────────────

def remind_key(cid: str, chat_id: int) -> str:
    return f"{cid}|{abs(chat_id)}"


# ── Public API ──────────────────────────────────────────────────────────────

def persist_reminder(
    cid: str, chat_id: int, member_id: str,
    planned_mins: int, end_t: str, end_dt_iso: str,
    message_thread_id: int = 0,
) -> None:
    """Save / update a single reminder entry to the JSON store."""
    key = remind_key(cid, chat_id)
    store = _read_store()
    store[key] = {
        "cid":               cid,
        "chat_id":           chat_id,
        "member_id":         member_id,
        "planned_mins":      planned_mins,
        "end_t":             end_t,
        "end_dt_iso":        end_dt_iso,
        "message_thread_id": message_thread_id,
        "updated_at":        datetime.now(timezone.utc).isoformat(),
    }
    _write_store(store)


def remove_persisted_reminder(cid: str, chat_id: int) -> None:
    """Remove a single reminder entry from the store."""
    key = remind_key(cid, chat_id)
    store = _read_store()
    if store.pop(key, None) is not None:
        _write_store(store)
        logger.info("reminder_store removed: %s", key)


# ── Startup restoration (async — suitable as `app.post_init`) ───────────────

async def restore_reminders_async(app) -> None:
    """Called once on bot startup (as post_init).

    Reads the JSON store, validates each entry, and re-creates remind_loop
    tasks for sessions that are still active and haven't fully expired.
    """
    from bot import STAFF_NOTIFY_CHAT, now_mmt
    from bot.handlers.booking_flow import (
        _remind_loop, _REMIND_TASKS, _remind_key,
        _NO_TIMER_CONSOLES, _is_session_active,
    )

    store = _read_store()
    if not store:
        logger.info("reminder_store: nothing to restore")
        return

    bot = app.bot
    target_chat = int(STAFF_NOTIFY_CHAT) if STAFF_NOTIFY_CHAT else 0
    now = now_mmt()

    restored = 0
    discarded = 0

    for key, entry in list(store.items()):
        cid       = entry.get("cid", "")
        chat_id   = entry.get("chat_id", target_chat)
        member_id = entry.get("member_id", "Guest")
        planned   = int(entry.get("planned_mins", 0))
        end_t     = entry.get("end_t", "")

        # ── Discard conditions ──────────────────────────────────────────────
        if not cid or cid in _NO_TIMER_CONSOLES:
            store.pop(key, None)
            discarded += 1
            continue

        # Parse end_dt_iso
        end_dt_iso = entry.get("end_dt_iso", "")
        end_dt = _parse_end_iso(end_dt_iso, end_t, now)
        if end_dt is None:
            store.pop(key, None)
            discarded += 1
            continue

        seconds_left = (end_dt - now).total_seconds()

        # Discard if ended more than 15 min ago
        if seconds_left < -900:
            store.pop(key, None)
            discarded += 1
            continue

        # ── Verify via API ──────────────────────────────────────────────────
        try:
            still_active = await _is_session_active(cid)
        except Exception as e:
            logger.warning("reminder_store: active check %s failed: %s", cid, e)
            still_active = True  # assume active so we don't lose the reminder

        if not still_active:
            store.pop(key, None)
            discarded += 1
            continue

        # ── Restore the reminder loop ───────────────────────────────────────
        delay = max(0, int(seconds_left - 300))  # seconds until 5-min-before-end
        if chat_id == 0:
            chat_id = target_chat
        if chat_id == 0:
            logger.warning("reminder_store: no chat_id for %s — skipping", key)
            store.pop(key, None)
            discarded += 1
            continue

        logger.info(
            "reminder_store restoring: %s | %s | end=%s | delay=%ds",
            cid, member_id, end_t, delay,
        )
        _mtid = entry.get("message_thread_id", 0)
        task = asyncio.get_event_loop().create_task(
            _remind_loop(bot, chat_id, cid, member_id, planned, end_t, delay, _mtid)
        )
        _REMIND_TASKS[_remind_key(cid, chat_id)] = task
        restored += 1

    _write_store(store)
    logger.info("reminder_store restore done: %d restored, %d discarded", restored, discarded)


def _parse_end_iso(end_dt_iso: str, end_t: str, now) -> Optional[datetime]:
    """Try to parse end_dt_iso; fall back to end_t + today."""
    if end_dt_iso:
        try:
            dt = datetime.fromisoformat(end_dt_iso)
            if dt.tzinfo is None:
                # Assume Myanmar time (UTC+6:30)
                from bot import MMT
                dt = dt.replace(tzinfo=MMT)
            return dt
        except (ValueError, TypeError):
            pass
    # Fallback: parse end_t as HH:MM today
    if end_t:
        try:
            eh, em = map(int, end_t.split(":"))
            return now.replace(hour=eh, minute=em, second=0, microsecond=0)
        except (ValueError, AttributeError):
            pass
    return None


# ── Periodic background cleanup ────────────────────────────────────────────

async def cleanup_stale_reminders_async(app) -> None:
    """Background task: every 15 minutes, scan the reminder store and purge
    any entries whose sessions are no longer active.
    Also cancels orphaned in-memory `_REMIND_TASKS` that no longer have
    a corresponding active session.

    Runs until the bot shuts down.
    """
    from bot import STAFF_NOTIFY_CHAT, now_mmt
    from bot.handlers.booking_flow import (
        _REMIND_TASKS, _remind_key, _NO_TIMER_CONSOLES, _is_session_active,
    )

    while True:
        try:
            await asyncio.sleep(15 * 60)  # every 15 min

            store = _read_store()
            if not store:
                continue  # nothing to clean

            target_chat = int(STAFF_NOTIFY_CHAT) if STAFF_NOTIFY_CHAT else 0
            now = now_mmt()
            purged = 0

            for key, entry in list(store.items()):
                cid = entry.get("cid", "")
                chat_id = entry.get("chat_id", target_chat)

                # ── Skip conditions (fast-path) ─────
                if not cid or cid in _NO_TIMER_CONSOLES:
                    store.pop(key, None)
                    purged += 1
                    # Cancel in-memory task if any
                    task = _REMIND_TASKS.pop(_remind_key(cid, chat_id), None)
                    if task and not task.done():
                        task.cancel()
                    continue

                # ── Check if session is still active ──
                try:
                    still_active = await _is_session_active(cid)
                except Exception as e:
                    logger.warning(
                        "cleanup_stale: active check %s failed: %s", cid, e
                    )
                    continue  # can't verify — keep

                if not still_active:
                    store.pop(key, None)
                    purged += 1
                    # Cancel in-memory task
                    task = _REMIND_TASKS.pop(_remind_key(cid, chat_id), None)
                    if task and not task.done():
                        task.cancel()
                    logger.info(
                        "cleanup_stale: purged %s (session inactive)", key
                    )

            if purged > 0:
                _write_store(store)
                logger.info(
                    "cleanup_stale: %d stale entries purged", purged
                )
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("cleanup_stale: %s", e, exc_info=True)


# Import asyncio at module level for the restore function
import asyncio
