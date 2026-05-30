"""Tests for main_menu.py — Main menu navigation handlers."""
import pytest, sys
from unittest.mock import AsyncMock, MagicMock


class TestMainMenuHandler:

    @pytest.mark.asyncio
    async def test_show_main_menu_authorized(self, mock_update, mock_context):
        """Authorized user should get menu with keyboard."""
        sys.modules['bot'].fetch_allowed_staff_ids_async = AsyncMock(return_value=[12345])
        mock_update.effective_user.id = 12345
        from bot.handlers.main_menu import show_main_menu
        result = await show_main_menu(mock_update, mock_context)
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_show_main_menu_unauthorized(self, mock_update, mock_context):
        """Unauthorized user gets access denied."""
        sys.modules['bot'].fetch_allowed_staff_ids_async = AsyncMock(return_value=[99999])
        mock_update.effective_user.id = 99998
        from bot.handlers.main_menu import show_main_menu
        result = await show_main_menu(mock_update, mock_context)
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_step_main_menu_routing(self, mock_update, mock_context):
        """Test menu routing with valid choice."""
        mock_update.message.text = "📊 Daily Sales"
        from bot.handlers.main_menu import step_main_menu
        result = await step_main_menu(mock_update, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_main_menu_clears_user_data(self, mock_update, mock_context):
        """show_main_menu should clear user_data."""
        sys.modules['bot'].fetch_allowed_staff_ids_async = AsyncMock(return_value=[12345])
        mock_context.user_data = {"old": "state"}
        mock_update.effective_user.id = 12345
        from bot.handlers.main_menu import show_main_menu
        await show_main_menu(mock_update, mock_context)
        assert mock_context.user_data == {}

    @pytest.mark.asyncio
    async def test_main_menu_keyboard_layout(self, mock_update, mock_context):
        """Menu should include keyboard markup."""
        sys.modules['bot'].fetch_allowed_staff_ids_async = AsyncMock(return_value=[12345])
        mock_update.effective_user.id = 12345
        from bot.handlers.main_menu import show_main_menu
        await show_main_menu(mock_update, mock_context)
        call_args = mock_update.message.reply_text.call_args
        assert call_args[1].get('reply_markup') is not None
