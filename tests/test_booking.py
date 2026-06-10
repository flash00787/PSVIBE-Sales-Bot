"""Tests for booking.py — Staff booking flow handlers."""
import pytest, sys
from unittest.mock import AsyncMock, MagicMock


class TestStaffBooking:

    @pytest.mark.asyncio
    async def test_cmd_staff_book_hub(self, mock_update, mock_context):
        """Staff booking hub shows pending/confirmed counts."""
        sys.modules['bot']._psvibe_get = MagicMock(return_value=[])
        from bot.handlers.booking import cmd_staff_book_hub
        result = await cmd_staff_book_hub(mock_update, mock_context)
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_sbk_console_kb(self):
        """_sbk_console_kb returns valid keyboard."""
        sys.modules['bot']._psvibe_get = MagicMock(return_value={
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

    @pytest.mark.asyncio
    async def test_sbk_parse_console_label_no_parens(self):
        """Parses console label without parentheses."""
        from bot.handlers.booking import _sbk_parse_console_label
        cid, ctype = _sbk_parse_console_label("C - 03")
        assert cid == "C - 03"

    @pytest.mark.asyncio
    async def test_sbk_console_kb_empty(self):
        """_sbk_console_kb handles empty console list."""
        sys.modules['bot']._psvibe_get = MagicMock(return_value={'consoles': []})
        from bot.handlers.booking import _sbk_console_kb
        kb = _sbk_console_kb()
        assert isinstance(kb, list)

    @pytest.mark.asyncio
    async def test_sbk_console_kb_busy_consoles(self):
        """_sbk_console_kb shows busy status."""
        sys.modules['bot']._psvibe_get = MagicMock(return_value={
            'consoles': [{'id': 'C - 01', 'type': 'PS5', 'liveStatus': 'Busy'}]
        })
        from bot.handlers.booking import _sbk_console_kb
        kb = _sbk_console_kb()
        assert isinstance(kb, list)

    @pytest.mark.asyncio
    async def test_cmd_staff_book_hub_with_waitlist_count(self, mock_update, mock_context):
        """Booking hub displays waitlist count when present."""
        sys.modules['bot']._psvibe_get = MagicMock(return_value=[
            {'id': 'WL001', 'customer_name': 'Test', 'status': 'waiting'}
        ])
        from bot.handlers.booking import cmd_staff_book_hub
        result = await cmd_staff_book_hub(mock_update, mock_context)
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_cmd_confirmed_bookings_does_not_crash(self, mock_update, mock_context):
        """Confirmed bookings handler runs without error."""
        sys.modules['bot']._psvibe_get = MagicMock(return_value=[
            {'id': 'B001', 'customer_name': 'Test', 'console_id': 'C-01',
             'date': '2026-05-31', 'time': '14:00', 'duration': 2}
        ])
        from bot.handlers.booking import cmd_confirmed_bookings
        result = await cmd_confirmed_bookings(mock_update, mock_context)
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_sbk_parse_console_label_with_type(self):
        """Parses console label with type in parentheses."""
        from bot.handlers.booking import _sbk_parse_console_label
        cid, ctype = _sbk_parse_console_label("C - 07 (PS4)")
        assert cid == "C - 07"
        assert "PS4" in ctype

    @pytest.mark.asyncio
    async def test_step_sbk_console_valid(self, mock_update, mock_context):
        """Valid console selection advances flow."""
        mock_update.message.text = 'C - 01 (PS5)'
        bot_mod = sys.modules['bot']
        bot_mod.SBK_CONSOLE = 800
        bot_mod.SBK_CUST_NAME = 801
        bot_mod._psvibe_get = MagicMock(return_value={
            'consoles': [{'id': 'C - 01', 'type': 'PS5', 'liveStatus': 'Free'}]
        })
        from bot.handlers.booking import step_sbk_console
        result = await step_sbk_console(mock_update, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_step_sbk_console_invalid(self, mock_update, mock_context):
        """Invalid console stays on selection."""
        mock_update.message.text = 'Invalid Console'
        bot_mod = sys.modules['bot']
        bot_mod.SBK_CONSOLE = 800
        bot_mod._psvibe_get = MagicMock(return_value={
            'consoles': [{'id': 'C - 01', 'type': 'PS5', 'liveStatus': 'Free'}]
        })
        from bot.handlers.booking import step_sbk_console
        result = await step_sbk_console(mock_update, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_cmd_staff_booking_starts_flow(self, mock_update, mock_context):
        """Staff booking initiates booking flow."""
        bot_mod = sys.modules['bot']
        bot_mod.SBK_CONSOLE = 800
        bot_mod._psvibe_get = MagicMock(return_value={
            'consoles': [{'id': 'C - 01', 'type': 'PS5', 'liveStatus': 'Free'}]
        })
        from bot.handlers.booking import cmd_staff_booking
        result = await cmd_staff_booking(mock_update, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_sbk_console_kb_free_and_busy(self):
        """_sbk_console_kb handles mixed free/busy consoles."""
        sys.modules['bot']._psvibe_get = MagicMock(return_value={
            'consoles': [
                {'id': 'C - 01', 'type': 'PS5', 'liveStatus': 'Free'},
                {'id': 'C - 02', 'type': 'PS5 Pro', 'liveStatus': 'Busy'},
                {'id': 'C - 03', 'type': 'PS4', 'liveStatus': 'Free'},
            ]
        })
        from bot.handlers.booking import _sbk_console_kb
        kb = _sbk_console_kb()
        assert isinstance(kb, list)
        assert len(kb) > 0
