"""Tests for console_mgmt.py — Console management handlers."""
import pytest, sys
from unittest.mock import AsyncMock, MagicMock


# ── Helper to inject values into console_mgmt module namespace ──
def _inject_console_mgmt_defaults():
    """Ensure console_mgmt module has all needed names resolved.
    The module uses __getattr__ for lazy loading from bot, but cached
    values or import-timing can bypass it. This forces resolution."""
    cm = sys.modules.get('bot.handlers.console_mgmt')
    if cm is None:
        return
    # Force __getattr__ to resolve each name
    needed = [
        'get_consoles_from_setting', 'BTN_BACK', 'BTN_CANCEL',
        'BTN_LIST_CONSOLE', 'BTN_ADD_CONSOLE', 'BTN_DEL_CONSOLE', 'BTN_EDIT_MULT',
        'CON_MGMT_MENU', 'CON_ADD_ID', 'CON_ADD_TYPE', 'CON_ADD_MULT',
        'CON_DEL_SELECT', 'CON_EDIT_MULT_SELECT', 'CON_EDIT_MULT_VALUE',
        'add_console_to_setting', 'remove_console_from_setting',
        'update_console_multiplier', 'VALID_CONSOLES',
    ]
    for name in needed:
        if name not in cm.__dict__:
            try:
                val = getattr(cm, name, None)
            except Exception:
                pass


class TestShowConMgmtMenu:

    @pytest.mark.asyncio
    async def test_show_con_mgmt_menu_displays_keyboard(self, mock_update, mock_context):
        """show_con_mgmt_menu sends reply with keyboard markup."""
        from bot.handlers import console_mgmt
        _inject_console_mgmt_defaults()
        console_mgmt.get_consoles_from_setting = MagicMock(return_value=[])
        console_mgmt.BTN_LIST_CONSOLE = '📋 List'
        console_mgmt.BTN_ADD_CONSOLE = '➕ Add Console'
        console_mgmt.BTN_DEL_CONSOLE = '❌ Delete'
        console_mgmt.BTN_EDIT_MULT = '⚙️ Edit Mult'
        console_mgmt.BTN_BACK = '🔙 Back'
        result = await console_mgmt.show_con_mgmt_menu(mock_update, mock_context)
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_show_con_mgmt_menu_returns_state(self, mock_update, mock_context):
        """Returns CON_MGMT_MENU conversation state."""
        from bot.handlers import console_mgmt
        _inject_console_mgmt_defaults()
        console_mgmt.get_consoles_from_setting = MagicMock(return_value=[])
        console_mgmt.BTN_LIST_CONSOLE = '📋 List'
        console_mgmt.BTN_ADD_CONSOLE = '➕ Add Console'
        console_mgmt.BTN_DEL_CONSOLE = '❌ Delete'
        console_mgmt.BTN_EDIT_MULT = '⚙️ Edit Mult'
        console_mgmt.BTN_BACK = '🔙 Back'
        console_mgmt.CON_MGMT_MENU = 500
        result = await console_mgmt.show_con_mgmt_menu(mock_update, mock_context)
        assert result == 500

    @pytest.mark.asyncio
    async def test_show_con_mgmt_menu_shows_console_count(self, mock_update, mock_context):
        """Menu text includes console count."""
        from bot.handlers import console_mgmt
        _inject_console_mgmt_defaults()
        console_mgmt.BTN_LIST_CONSOLE = '📋 List'
        console_mgmt.BTN_ADD_CONSOLE = '➕ Add Console'
        console_mgmt.BTN_DEL_CONSOLE = '❌ Delete'
        console_mgmt.BTN_EDIT_MULT = '⚙️ Edit Mult'
        console_mgmt.BTN_BACK = '🔙 Back'
        cons = [{'id': 'C-01', 'type': 'PS5'}]
        console_mgmt.get_consoles_from_setting = MagicMock(return_value=cons)
        await console_mgmt.show_con_mgmt_menu(mock_update, mock_context)
        call_args = mock_update.message.reply_text.call_args
        assert '1' in call_args[0][0]


class TestStepConMgmtMenu:

    def _setup(self):
        from bot.handlers import console_mgmt
        _inject_console_mgmt_defaults()
        console_mgmt.BTN_BACK = '🔙 Back'
        console_mgmt.BTN_LIST_CONSOLE = '📋 List'
        console_mgmt.BTN_ADD_CONSOLE = '➕ Add Console'
        console_mgmt.BTN_DEL_CONSOLE = '❌ Delete'
        console_mgmt.BTN_EDIT_MULT = '⚙️ Edit Mult'
        console_mgmt.BTN_CANCEL = '❌ Cancel'
        console_mgmt.CON_ADD_ID = 501
        console_mgmt.CON_DEL_SELECT = 504
        console_mgmt.CON_EDIT_MULT_SELECT = 505
        console_mgmt.get_consoles_from_setting = MagicMock(return_value=[])
        return console_mgmt

    @pytest.mark.asyncio
    async def test_step_con_mgmt_menu_back(self, mock_update, mock_context):
        """Back button navigates to console menu."""
        mock_update.message.text = '🔙 Back'
        cm = self._setup()
        from unittest.mock import patch
        with patch('bot.handlers.console.show_console_menu', new_callable=AsyncMock) as mock_show:
            mock_show.return_value = 2
            result = await cm.step_con_mgmt_menu(mock_update, mock_context)
            assert result == 2

    @pytest.mark.asyncio
    async def test_step_con_mgmt_menu_list_empty(self, mock_update, mock_context):
        """List consoles with none shows info message."""
        mock_update.message.text = '📋 List'
        cm = self._setup()
        result = await cm.step_con_mgmt_menu(mock_update, mock_context)
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_step_con_mgmt_menu_list_with_data(self, mock_update, mock_context):
        """List consoles with data displays console list."""
        mock_update.message.text = '📋 List'
        cm = self._setup()
        cons = [{'id': 'C-01', 'type': 'PS5', 'mult': 1.5},
                {'id': 'C-02', 'type': 'PS4', 'mult': None}]
        cm.get_consoles_from_setting = MagicMock(return_value=cons)
        result = await cm.step_con_mgmt_menu(mock_update, mock_context)
        assert mock_update.message.reply_text.called
        # List handler sends list then menu; check list call (first call)
        all_calls = [c[0][0] for c in mock_update.message.reply_text.call_args_list]
        console_list_text = all_calls[0] if all_calls else ''
        assert 'C-01' in console_list_text

    @pytest.mark.asyncio
    async def test_step_con_mgmt_menu_add_console(self, mock_update, mock_context):
        """Add Console button asks for ID."""
        mock_update.message.text = '➕ Add Console'
        cm = self._setup()
        result = await cm.step_con_mgmt_menu(mock_update, mock_context)
        assert result == cm.CON_ADD_ID

    @pytest.mark.asyncio
    async def test_step_con_mgmt_menu_del_console_empty(self, mock_update, mock_context):
        """Delete console with none shows info message."""
        mock_update.message.text = '❌ Delete'
        cm = self._setup()
        result = await cm.step_con_mgmt_menu(mock_update, mock_context)
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_step_con_mgmt_menu_del_console_with_data(self, mock_update, mock_context):
        """Delete console with data shows selection keyboard."""
        mock_update.message.text = '❌ Delete'
        cm = self._setup()
        cons = [{'id': 'C-01', 'type': 'PS5'}]
        cm.get_consoles_from_setting = MagicMock(return_value=cons)
        result = await cm.step_con_mgmt_menu(mock_update, mock_context)
        assert result == cm.CON_DEL_SELECT

    @pytest.mark.asyncio
    async def test_step_con_mgmt_menu_edit_mult(self, mock_update, mock_context):
        """Edit multiplier with consoles shows selection."""
        mock_update.message.text = '⚙️ Edit Mult'
        cm = self._setup()
        cons = [{'id': 'C-01', 'type': 'PS5', 'mult': 1.5}]
        cm.get_consoles_from_setting = MagicMock(return_value=cons)
        result = await cm.step_con_mgmt_menu(mock_update, mock_context)
        assert result == cm.CON_EDIT_MULT_SELECT

    @pytest.mark.asyncio
    async def test_step_con_mgmt_menu_unknown(self, mock_update, mock_context):
        """Unknown choice re-shows console management menu."""
        mock_update.message.text = 'Unknown'
        cm = self._setup()
        result = await cm.step_con_mgmt_menu(mock_update, mock_context)
        assert result is not None


class TestConsoleAddFlow:

    def _setup(self):
        from bot.handlers import console_mgmt
        _inject_console_mgmt_defaults()
        console_mgmt.BTN_CANCEL = '❌ Cancel'
        console_mgmt.CON_ADD_ID = 501
        console_mgmt.CON_ADD_TYPE = 502
        console_mgmt.get_consoles_from_setting = MagicMock(return_value=[{'id': 'C-01', 'type': 'PS5'}])
        return console_mgmt

    @pytest.mark.asyncio
    async def test_step_con_add_id_valid(self, mock_update, mock_context):
        """Valid new ID advances to type selection."""
        mock_update.message.text = 'C-11'
        mock_context.user_data['new_con'] = {}
        cm = self._setup()
        result = await cm.step_con_add_id(mock_update, mock_context)
        assert result == cm.CON_ADD_TYPE

    @pytest.mark.asyncio
    async def test_step_con_add_id_duplicate(self, mock_update, mock_context):
        """Duplicate ID shows warning."""
        mock_update.message.text = 'C-01'
        cm = self._setup()
        result = await cm.step_con_add_id(mock_update, mock_context)
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_step_con_add_id_cancel(self, mock_update, mock_context):
        """Cancel returns to management menu."""
        mock_update.message.text = '❌ Cancel'
        cm = self._setup()
        result = await cm.step_con_add_id(mock_update, mock_context)
        assert result is not None
