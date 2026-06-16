"""
Input logging middleware — DISABLED (GSheet removed).
Registered at group=-998 for backward compat, both functions are no-ops.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def input_logger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """No-op: GSheet input logger removed."""
    pass


async def input_logger_batcher():
    """No-op: GSheet batcher removed."""
    pass
