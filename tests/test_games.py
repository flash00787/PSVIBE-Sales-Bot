"""Tests for games.py — Game Library handlers."""
import pytest, sys
from unittest.mock import AsyncMock, MagicMock


class TestShowGameMenu:

    @pytest.mark.asyncio
    async def test_show_game_menu_displays_keyboard(self, mock_update, mock_context):
        """show_game_menu sends reply with keyboard markup."""
        from bot.handlers import games
        games.fetch_games = MagicMock(return_value=[])
        result = await games.show_game_menu(mock_update, mock_context)
        assert mock_update.message.reply_text.called
        call_args = mock_update.message.reply_text.call_args
        assert call_args[1].get('reply_markup') is not None

    @pytest.mark.asyncio
    async def test_show_game_menu_returns_game_menu_state(self, mock_update, mock_context):
        """Returns GAME_MENU conversation state."""
        from bot.handlers import games
        games.fetch_games = MagicMock(return_value=[])
        import bot
        result = await games.show_game_menu(mock_update, mock_context)
        assert result == bot.GAME_MENU

    @pytest.mark.asyncio
    async def test_show_game_menu_shows_game_count(self, mock_update, mock_context):
        """Menu text includes game count."""
        from bot.handlers import games
        games.fetch_games = MagicMock(return_value=[
            {'title': 'Game1'}, {'title': 'Game2'}
        ])
        await games.show_game_menu(mock_update, mock_context)
        call_args = mock_update.message.reply_text.call_args
        assert '2' in call_args[0][0]

    @pytest.mark.asyncio
    async def test_show_game_menu_empty_zero(self, mock_update, mock_context):
        """Zero games shows count 0."""
        from bot.handlers import games
        games.fetch_games = MagicMock(return_value=[])
        await games.show_game_menu(mock_update, mock_context)
        call_args = mock_update.message.reply_text.call_args
        assert '0' in call_args[0][0]


class TestStepGameMenu:

    @pytest.mark.asyncio
    async def test_step_game_menu_back_to_main(self, mock_update, mock_context):
        """Back button returns to main menu."""
        mock_update.message.text = '🔙 Back'
        from bot.handlers import games
        games.BTN_BACK = '🔙 Back'
        games.BTN_BACK_MAIN = '🔙 Main Menu'
        games.show_main_menu = AsyncMock(return_value=0)
        result = await games.step_game_menu(mock_update, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_step_game_menu_view_games_empty(self, mock_update, mock_context):
        """View Games with empty library shows message."""
        mock_update.message.text = '👁️ View Games'
        from bot.handlers import games
        games.BTN_BACK = '🔙 Back'
        games.BTN_BACK_MAIN = '🔙 Main Menu'
        games.BTN_VIEW_GAMES = '👁️ View Games'
        games.fetch_games = MagicMock(return_value=[])
        result = await games.step_game_menu(mock_update, mock_context)
        assert result is not None
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_step_game_menu_view_games_with_data(self, mock_update, mock_context):
        """View Games with data displays game list."""
        mock_update.message.text = '👁️ View Games'
        from bot.handlers import games
        games.BTN_BACK = '🔙 Back'
        games.BTN_BACK_MAIN = '🔙 Main Menu'
        games.BTN_VIEW_GAMES = '👁️ View Games'
        games.fetch_games = MagicMock(return_value=[
            {'title': 'Test Game', 'discs': '2', 'solo_multi': 'Solo', 'genre': 'Action'}
        ])
        games.fetch_console_games = MagicMock(return_value=[
            {'game_title': 'Test Game', 'console_id': 'C-01'}
        ])
        result = await games.step_game_menu(mock_update, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_step_game_menu_add_game_title(self, mock_update, mock_context):
        """Add Game button asks for title."""
        mock_update.message.text = '➕ Add Game'
        from bot.handlers import games
        games.BTN_BACK = '🔙 Back'
        games.BTN_BACK_MAIN = '🔙 Main Menu'
        games.BTN_ADD_GAME = '➕ Add Game'
        games.BTN_CANCEL = '❌ Cancel'
        games.GAME_ADD_TITLE = 401
        result = await games.step_game_menu(mock_update, mock_context)
        assert result is not None
        assert 'new_game' in mock_context.user_data

    @pytest.mark.asyncio
    async def test_step_game_menu_del_game_empty(self, mock_update, mock_context):
        """Delete Game with no games shows info message."""
        mock_update.message.text = '🗑️ Delete Game'
        from bot.handlers import games
        games.BTN_BACK = '🔙 Back'
        games.BTN_BACK_MAIN = '🔙 Main Menu'
        games.BTN_DEL_GAME = '🗑️ Delete Game'
        games.fetch_games = MagicMock(return_value=[])
        result = await games.step_game_menu(mock_update, mock_context)
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_step_game_menu_del_game_with_data(self, mock_update, mock_context):
        """Delete Game with games shows selection keyboard."""
        mock_update.message.text = '🗑️ Delete Game'
        from bot.handlers import games
        games.BTN_BACK = '🔙 Back'
        games.BTN_BACK_MAIN = '🔙 Main Menu'
        games.BTN_DEL_GAME = '🗑️ Delete Game'
        games.GAME_DEL_SELECT = 405
        games.fetch_games = MagicMock(return_value=[{'title': 'Game1', 'row': 2}])
        result = await games.step_game_menu(mock_update, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_step_game_menu_unknown_falls_back(self, mock_update, mock_context):
        """Unknown choice re-shows game menu."""
        mock_update.message.text = 'Unknown Choice XYZ'
        from bot.handlers import games
        games.BTN_BACK = '🔙 Back'
        games.BTN_BACK_MAIN = '🔙 Main Menu'
        games.fetch_games = MagicMock(return_value=[])
        result = await games.step_game_menu(mock_update, mock_context)
        assert result is not None


class TestGameAddFlow:

    @pytest.mark.asyncio
    async def test_step_game_add_title_valid(self, mock_update, mock_context):
        """Valid title advances to platform selection."""
        mock_update.message.text = 'Test Game'
        mock_context.user_data['new_game'] = {}
        from bot.handlers import games
        games.BTN_CANCEL = '❌ Cancel'
        games.GAME_ADD_PLATFORM = 402
        result = await games.step_game_add_title(mock_update, mock_context)
        assert result is not None
        assert mock_context.user_data['new_game']['title'] == 'Test Game'

    @pytest.mark.asyncio
    async def test_step_game_add_title_cancel(self, mock_update, mock_context):
        """Cancel returns to game menu."""
        mock_update.message.text = '❌ Cancel'
        from bot.handlers import games
        games.BTN_CANCEL = '❌ Cancel'
        result = await games.step_game_add_title(mock_update, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_step_game_add_genre_valid(self, mock_update, mock_context):
        """Valid genre selection advances to status/copies."""
        mock_update.message.text = 'Action'
        mock_context.user_data['new_game'] = {}
        from bot.handlers import games
        games.BTN_CANCEL = '❌ Cancel'
        games.GAME_ADD_STATUS = 404
        result = await games.step_game_add_genre(mock_update, mock_context)
        assert result is not None
        assert mock_context.user_data.get('new_game', {}).get('genre') == 'Action'

    @pytest.mark.asyncio
    async def test_step_game_add_genre_empty(self, mock_update, mock_context):
        """Empty genre stays on genre step."""
        mock_update.message.text = ''
        from bot.handlers import games
        games.BTN_CANCEL = '❌ Cancel'
        result = await games.step_game_add_genre(mock_update, mock_context)
        assert result is not None
