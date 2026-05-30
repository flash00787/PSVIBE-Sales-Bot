"""Shared fixtures — PS VIBE bot test framework."""
import pytest, sys, types, os, re
from unittest.mock import AsyncMock, MagicMock, patch

_BOT_DIR = '/root/psvibe-sales-bot/bot'

def _build_bot_mock():
    bot = types.ModuleType('bot')
    bot.__package__ = 'bot'
    bot.__file__ = os.path.join(_BOT_DIR, '__init__.py')

    bot.BOT_VERSION = '6.0.0-test'
    bot.BTN_BACK_MAIN = '🔙 Main Menu'
    bot.BTN_BACK = '🔙 Back'
    bot.BTN_CANCEL = '❌ Cancel'
    bot.BTN_DAILY_SALES = '📊 Daily Sales'
    bot.BTN_MEMBER_MGMT = '👥 Members'
    bot.BTN_CONSOLES = '🎮 Consoles'
    bot.BTN_TODAY_REPORT = '📈 Today'
    bot.BTN_STAFF_BOOK = '📅 Booking'
    bot.BTN_INVENTORY_VIEW = '📦 Inventory'
    bot.BTN_FINANCIAL_REPORT = '💰 Financial'
    bot.BTN_ADMIN = '⚙️ Admin'
    bot.BTN_SBK_WAITLIST = '⏳ Waitlist'
    bot.BTN_SBK_NEW = '📝 New'
    bot.BTN_SBK_CONFIRMED = '✅ Confirmed'
    bot.BTN_GAME_LIB_MENU = '🎮 GameLib'
    bot.BTN_GAMES = '🎮 Games'
    bot.BTN_STOCK_MGMT = '📊 Stock'
    bot.BTN_DISC_MGMT = '🏷️ Discount'
    bot.BTN_SSD_DISC = '🔄 SSD'
    bot.BTN_FOOD_SETUP = '🍽️ Food'
    bot.BTN_FIRST_PURCHASE = '🆕 First Purchase'
    bot.BTN_TOP_UP = '💰 Top Up'
    bot.BTN_CHECK_MEMBER = '🔍 Check'
    bot.BTN_VIEW_RANKS = '🏆 Ranks'
    bot.BTN_PROMO_APPLY = '🎁 Promo'
    bot.BTN_MANUAL_DISC = '✏️ Manual %'
    bot.BTN_SKIP_DISC = '⏭️ Skip'
    bot.BTN_FIN_CAPITAL = '💰 Capital'
    bot.BTN_FIN_SHAREHOLDER = '👥 SH'
    bot.BTN_FIN_TRANSFER = '↔️ Transfer'
    bot.BTN_FIN_OPEX = '📋 OPEX'
    bot.BTN_FIN_ASSET = '🏗️ Asset'
    bot.BTN_FIN_ASSET_DISPOSE = '🗑️ Dispose'
    bot.BTN_FIN_PREPAID = '📆 Prepaid'
    bot.BTN_FIN_PAYABLE = '📝 Payable'
    bot.BTN_FIN_SETTLE_PAY = '✅ SettlePay'
    bot.BTN_FIN_RECEIVABLE = '📥 Receivable'
    bot.BTN_FIN_SETTLE_REC = '✅ SettleRec'
    bot.BTN_FIN_ADVPAY = '💵 Advance'
    bot.BTN_FIN_SETTLE_ADVPAY = '✅ SettleAdv'
    bot.BTN_FIN_ACCTS = '📊 Accounts'
    bot.BTN_FIN_REPORT = '📈 FinReport'
    bot.BTN_FIN_SETUP = '⚙️ Setup'
    bot.BTN_GINST_VIEW = '👁️ View'
    bot.BTN_GINST_ADD = '➕ Add'
    bot.BTN_GINST_REMOVE = '❌ Remove'
    bot.BTN_LIST_CONSOLE = '📋 List'
    bot.BTN_ADD_CONSOLE = '➕ Add Console'
    bot.BTN_DEL_CONSOLE = '❌ Delete'
    bot.BTN_ASSIGN_REFERRAL = '🔗 Assign Referral'

    bot.MAIN_MENU = 0
    bot.MEMBER = 1
    bot.CONSOLE = 2
    bot.MINS = 3
    bot.MM_MENU = 100
    bot.FINANCE_MENU = 200
    bot.STAFF_SELECT = 10
    bot.STOCK_PIN = 300
    bot.STOCK_MENU = 301
    bot.GINST_MENU = 400
    bot.CON_MGMT_MENU = 500
    bot.ADMIN_PIN = '1234'
    bot.STOCK_ACCESS_PIN = '1234'
    bot.CUSTOMER_BOT_TOKEN = 'fake-token'
    bot.NAV_ROW = ['🔙 Back', '❌ Cancel']
    bot.VALID_CONSOLES = ['C-01', 'C-02', 'C-03', 'C-04', 'C-05']
    bot.ConversationHandler = MagicMock()
    bot.ConversationHandler.END = -1

    from datetime import datetime, timezone, timedelta
    def _now_mmt():
        return datetime.now(timezone(timedelta(hours=6, minutes=30)))
    bot.now_mmt = _now_mmt

    bot.fetch_allowed_staff_ids = MagicMock(return_value=[12345])
    bot.fetch_members = MagicMock(return_value=['PSV_A001', 'PSV_A002', 'PSV_A003'])
    bot.fetch_staff = MagicMock(return_value=['Staff1', 'Staff2', 'Staff3'])
    bot.fetch_console_status = MagicMock(return_value=[
        {'id': 'C-01', 'type': 'PS5', 'status': 'Free'},
        {'id': 'C-02', 'type': 'PS5 Pro', 'status': 'Free'},
    ])
    bot.fetch_base_rate = MagicMock(return_value=5000)
    bot.fetch_rank_table_display = MagicMock(return_value='Rank Table')
    bot.fetch_rank_thresholds = MagicMock(return_value=(100000, 500000))
    bot.fetch_console_games = MagicMock(return_value=[])
    bot.get_consoles_from_setting = MagicMock(return_value=[])
    bot.fetch_promotions_cached = MagicMock(return_value=[])
    # -- Async hot-path mocks (Phase: async migration) --
    bot.fetch_base_rate_async = AsyncMock(return_value=5000)
    bot.fetch_wallet_mins_async = AsyncMock(return_value=100)
    bot.fetch_food_prices_async = AsyncMock(return_value={})
    bot.fetch_food_costs_async = AsyncMock(return_value={})
    bot.fetch_console_multiplier_async = AsyncMock(return_value=1.5)
    bot.fetch_members_async = AsyncMock(return_value=['PSV_A001', 'PSV_A002', 'PSV_A003'])
    bot.fetch_allowed_staff_ids_async = AsyncMock(return_value=[12345])
    bot.step_hdr = MagicMock(return_value='📋 Step 1/6\n')

    bot.cmd_cancel = AsyncMock(return_value=-1)
    bot.show_main_menu = AsyncMock(return_value=0)
    bot.answer_callback_query = AsyncMock()
    bot.show_shareholder_menu = AsyncMock(return_value=0)
    bot.prompt_cap_acct = AsyncMock(return_value=0)
    bot.prompt_opex_cat = AsyncMock(return_value=0)
    bot.prompt_asset_name = AsyncMock(return_value=0)
    bot.prompt_asset_dispose_sel = AsyncMock(return_value=0)

    mock_ws = MagicMock()
    mock_ws.get_all_values.return_value = [['H1', 'H2'], ['v1', 'v2']]
    mock_ws.append_row = MagicMock()
    mock_ws.update_cell = MagicMock()
    mock_ws.update = MagicMock()
    mock_ws.col_values.return_value = ['1000', '2000']
    mock_ws.row_values.return_value = []
    mock_ws.row_count = 2
    mock_ws.title = 'Sales'
    mock_wb = MagicMock()
    mock_wb.worksheet.return_value = mock_ws
    mock_wb.worksheet_by_title.return_value = mock_ws
    mock_wb.sheet1 = mock_ws
    bot.wb = mock_wb
    bot.inv_sh = mock_ws

    # _replit_get — underscore prefixed, needs __all__ for star import
    _replit_get = MagicMock(return_value=[])
    _replit_post = MagicMock(return_value={'ok': True})
    _replit_put = MagicMock(return_value={'ok': True})
    _replit_delete = MagicMock(return_value={'ok': True})
    bot._replit_get = _replit_get
    bot._replit_post = _replit_post
    bot._replit_put = _replit_put
    bot._replit_delete = _replit_delete

    # __all__ ensures these export via "from bot import *"
    bot.__all__ = [k for k in dir(bot) if not k.startswith('_') or k.startswith('_replit')]

    bot.logging = __import__('logging')
    bot.re = __import__('re')
    bot.json = __import__('json')
    bot.asyncio = __import__('asyncio')


    # ── Auto-populate all __all__ entries not yet defined ──
    # Parse the real bot/__init__.py __all__ list
    _init_path = os.path.join(_BOT_DIR, '__init__.py')
    if os.path.exists(_init_path):
        with open(_init_path) as _f:
            _init_src = _f.read()
        _idx = _init_src.find("__all__")
        _start = _init_src.find("[", _idx)
        _end = _init_src.find("]", _start)
        _all_str = _init_src[_start:_end+1]
        _all_list = re.findall(r"'([^']+)'", _all_str)
        for _name in _all_list:
            if not hasattr(bot, _name):
                if _name.startswith("BTN_") or _name in ("NAV_ROW", "VALID_CONSOLES", "RECEIPTS_DIR"):
                    setattr(bot, _name, f"[{_name}]")
                elif _name.isupper():
                    setattr(bot, _name, 9999)
                elif _name.startswith("_"):
                    setattr(bot, _name, MagicMock())
                elif _name.startswith(("cmd_", "show_")):
                    setattr(bot, _name, AsyncMock(return_value=-1))
                elif _name.startswith(("fetch_", "get_", "save_", "build_", "display_", "rank_", "update_", "ensure_", "next_", "step_", "calc_", "check_", "create_", "end_", "cancel_", "add_", "remove_", "set_", "today_", "keep_")):
                    setattr(bot, _name, MagicMock())
                else:
                    setattr(bot, _name, MagicMock())
        # Also scan module-level function definitions in bot/__init__.py
        # (these may not be in __all__ but are importable)
        import ast as _ast
        try:
            with open(_init_path) as _f:
                _tree = _ast.parse(_f.read())
            for _node in _ast.walk(_tree):
                if isinstance(_node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                    _fname = _node.name
                    if not hasattr(bot, _fname):
                        if _fname.startswith("_"):
                            setattr(bot, _fname, MagicMock())
                        elif _fname.startswith(("cmd_", "show_")):
                            setattr(bot, _fname, AsyncMock(return_value=-1))
                        else:
                            setattr(bot, _fname, MagicMock())
        except Exception:
            pass
        # Handler re-exports (not defined in bot/__init__.py itself)
        _handler_reexports = [
            "cmd_cancel", "show_main_menu", "show_admin_menu",
            "show_console_menu", "show_game_menu", "show_ginst_menu",
            "cmd_payroll", "cmd_staff_kpi", "cmd_setattend", "cmd_setattend_cmd",
        ]
        for _name in _handler_reexports:
            if not hasattr(bot, _name):
                if _name.startswith(("cmd_", "show_")):
                    setattr(bot, _name, AsyncMock(return_value=-1))
                else:
                    setattr(bot, _name, MagicMock())

    return bot

_bot = _build_bot_mock()
sys.modules['bot'] = _bot

_handlers = types.ModuleType('bot.handlers')
_handlers.__package__ = 'bot.handlers'
_handlers.__path__ = [os.path.join(_BOT_DIR, 'handlers')]
_handlers.__file__ = os.path.join(_BOT_DIR, 'handlers', '__init__.py')
sys.modules['bot.handlers'] = _handlers

_utils = types.ModuleType('bot.utils')
_utils.__package__ = 'bot.utils'
_utils.__path__ = [os.path.join(_BOT_DIR, 'utils')]
_utils.__file__ = os.path.join(_BOT_DIR, 'utils', '__init__.py')
sys.modules['bot.utils'] = _utils

sys.modules['gspread'] = MagicMock()

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 12345
    user.first_name = "Test"
    user.last_name = "User"
    user.username = "test_user"
    user.is_bot = False
    user.language_code = "my"
    return user

@pytest.fixture
def mock_chat():
    chat = MagicMock()
    chat.id = 67890
    chat.type = "private"
    chat.first_name = "Test"
    chat.username = "test_user"
    return chat

@pytest.fixture
def mock_message(mock_user, mock_chat):
    message = MagicMock()
    message.message_id = 1
    message.chat = mock_chat
    message.from_user = mock_user
    message.text = "/start"
    message.date = None
    message.reply_text = AsyncMock()
    message.delete = AsyncMock()
    message.edit_text = AsyncMock()
    return message

@pytest.fixture
def mock_update(mock_user, mock_chat, mock_message):
    update = MagicMock()
    update.update_id = 1
    update.message = mock_message
    update.effective_user = mock_user
    update.effective_chat = mock_chat
    update.callback_query = None
    return update

@pytest.fixture
def mock_context():
    context = MagicMock()
    context.user_data = {}
    context.bot_data = {}
    context.args = []
    context.bot = AsyncMock()
    context.bot.send_message = AsyncMock()
    context.bot.edit_message_text = AsyncMock()
    context.bot.answer_callback_query = AsyncMock()
    context.bot.delete_message = AsyncMock()
    context.bot.send_photo = AsyncMock()
    context.bot.send_document = AsyncMock()
    return context

@pytest.fixture(autouse=True)
def _reset():
    yield
    _bot.fetch_allowed_staff_ids.return_value = [12345]
    _bot.fetch_members.return_value = ['PSV_A001', 'PSV_A002']
    _bot._replit_get.return_value = []
