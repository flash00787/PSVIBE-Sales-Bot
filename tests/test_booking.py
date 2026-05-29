"""Tests for booking.py — Staff booking flow handlers."""
import pytest, sys
from unittest.mock import MagicMock


class TestStaffBooking:

    @pytest.mark.asyncio
    async def test_cmd_staff_book_hub(self, mock_update, mock_context):
        """Staff booking hub shows pending/confirmed counts."""
        sys.modules['bot']._replit_get = MagicMock(return_value=[])
        from bot.handlers.booking import cmd_staff_book_hub
        result = await cmd_staff_book_hub(mock_update, mock_context)
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_sbk_console_kb(self):
        """_sbk_console_kb returns valid keyboard."""
        sys.modules['bot']._replit_get = MagicMock(return_value={
            'consoles': [{'id': 'C - 01', 'type': 'PS5', 'liveStatus': 'Free'}]
        })
        from bot.handlers.booking import _sbk_console_kb
        kb = _sbk_console_kb()
        assert isinstance(kb, list)
        assert len(kb) > 0

    @pytest.mark.asyncio
    async def test_sbk_parse_console_label(self):
        """Parses console label correctly."""
        from bot.handlers.booking import _sbk_parse_console_label
        cid, ctype = _sbk_parse_console_label("C - 01 (PS5 Pro)")
        assert cid == "C - 01"
        assert "PS5" in ctype
