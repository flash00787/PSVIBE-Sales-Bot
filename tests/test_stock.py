"""Tests for stock.py — Stock management handlers."""
import pytest, sys
from unittest.mock import MagicMock


class TestStockManagement:

    @pytest.mark.asyncio
    async def test_cmd_stockin_direct_pin_prompt(self, mock_update, mock_context):
        """Stock-in prompts for PIN."""
        from bot.handlers.stock import cmd_stockin_direct
        await cmd_stockin_direct(mock_update, mock_context)
        assert mock_update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_cmd_stockin_sets_dest(self, mock_update, mock_context):
        """Stock-in sets destination in user_data."""
        from bot.handlers.stock import cmd_stockin_direct
        await cmd_stockin_direct(mock_update, mock_context)
        assert mock_context.user_data.get('stock_dest') == 'stockin'

    @pytest.mark.asyncio
    async def test_cmd_stockout_direct(self, mock_update, mock_context):
        """Stock-out prompts for PIN."""
        from bot.handlers.stock import cmd_stockout_direct
        await cmd_stockout_direct(mock_update, mock_context)
        assert mock_update.message.reply_text.called
        assert mock_context.user_data.get('stock_dest') == 'stockout'

    @pytest.mark.asyncio
    async def test_cmd_stock_menu(self, mock_update, mock_context):
        """Stock menu prompts for PIN."""
        from bot.handlers.stock import cmd_stock_menu
        await cmd_stock_menu(mock_update, mock_context)
        assert mock_context.user_data.get('stock_dest') == 'menu'

    @pytest.mark.skip(reason="update_inv_total_k1 removed — GSheet fallback dead code")
    @pytest.mark.asyncio
    async def test_update_inv_total_k1(self):
        """update_inv_total_k1 returns non-negative int."""
        from bot.handlers.stock import update_inv_total_k1
        total = update_inv_total_k1()
        assert isinstance(total, int)
        assert total >= 0
