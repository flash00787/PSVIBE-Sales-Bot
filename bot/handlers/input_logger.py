"""
Input logging middleware: logs ALL authorized user interactions to Input_Log sheet.
Uses async queue + batch flusher to avoid gspread rate limits.
Registered at group=-998 (after auth at -999, before conversation at 0).
"""
import asyncio
import logging
import time
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

_log_queue: asyncio.Queue = asyncio.Queue()
_batch_size = 10
_flush_interval = 5.0  # seconds

# Columns:
# A: Timestamp (MMT), B: Staff ID, C: Staff Name, D: Message Type,
# E: Input Text, F: Conversation State, G: Active Voucher,
# H: Processing Time (ms), I: Flags


async def input_logger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log all inputs asynchronously - non-blocking, zero I/O in hot path."""
    t0 = time.perf_counter()
    try:
        user = update.effective_user
        if not user:
            return

        # Determine message type and text
        if update.message and update.message.text:
            msg_type = "text"
            input_text = update.message.text
        elif update.callback_query and update.callback_query.data:
            msg_type = "callback"
            input_text = update.callback_query.data
        elif update.message and update.message.text is None:
            msg_type = "other"
            input_text = ""
        else:
            return  # not a text/callback input

        # Get conversation state
        state = ""
        if context.user_data and "_state" in context.user_data:
            state = str(context.user_data["_state"])
        elif context.user_data:
            # Fallback: check conversation data
            for k in list(context.user_data.keys())[:3]:
                if "state" in k.lower() or "step" in k.lower():
                    state = str(context.user_data[k])
                    break

        voucher = context.user_data.get("voucher_no", "") if context.user_data else ""
        proc_ms = int((time.perf_counter() - t0) * 1000)

        entry = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "staff_id": str(user.id),
            "staff_name": (user.full_name or "Unknown")[:100],
            "msg_type": msg_type,
            "input_text": input_text[:500],
            "state": state[:50],
            "voucher": str(voucher)[:50] if voucher else "",
            "proc_ms": str(proc_ms),
            "flags": "authorized"
        }

        await _log_queue.put(entry)
    except Exception:
        pass  # Never break the main flow


async def input_logger_batcher():
    """Background batcher: flush queue to GSheets every 5s or 10 entries."""
    buffer = []
    while True:
        try:
            entry = await asyncio.wait_for(_log_queue.get(), timeout=_flush_interval)
            buffer.append(entry)
            while len(buffer) < _batch_size and not _log_queue.empty():
                buffer.append(_log_queue.get_nowait())
        except asyncio.TimeoutError:
            pass

        if buffer:
            try:
                # Import here to avoid circular at module level
                from bot import get_input_log_sh
                sh = get_input_log_sh()
                rows = [[
                    e["ts"], e["staff_id"], e["staff_name"],
                    e["msg_type"], e["input_text"],
                    e["state"], e["voucher"], e["proc_ms"], e["flags"]
                ] for e in buffer]
                if sh is not None:
                    sh.append_rows(rows, value_input_option="USER_ENTERED")
                logger.debug("Flushed %d input log entries to sheet", len(buffer))
            except Exception as e:
                logger.error("Input log batch write failed: %s", e)
            buffer.clear()
