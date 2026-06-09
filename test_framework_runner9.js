const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const commands = [];

function cmd(c) { commands.push(c); }

// ============================================================
// FINAL APPROACH: Pre-register bot.handlers so __init__.py is SKIPPED,
// but __path__ allows submodule discovery from disk.
// Also add ALL missing constants needed by handler files.
// ============================================================
cmd("cat > /root/psvibe-sales-bot/tests/conftest.py << 'CONFTESTEOF'\n\"\"\"Shared fixtures — PS VIBE bot test framework.\n\nStrategy:\n1. Mock `bot` in sys.modules with ALL constants/functions handlers need\n2. Pre-register `bot.handlers` with __path__ pointing to real dir\n   (skips handlers/__init__.py which cascades 25 imports)\n3. Python discovers bot.handlers.xxx from filesystem; \"from bot import *\"\n   resolves from our mock. Handlers that import internally via \"from bot.handlers.X\"\n   also work since bot.handlers is registered.\n\"\"\"\nimport pytest, sys, types, os\nfrom unittest.mock import AsyncMock, MagicMock, patch\n\n_BOT_DIR = '/root/psvibe-sales-bot/bot'\n\n\ndef _build_bot_mock():\n    bot = types.ModuleType('bot')\n    bot.__package__ = 'bot'\n    # No __path__ — prevents auto-discovery of bot/handlers/__init__.py\n    bot.__file__ = os.path.join(_BOT_DIR, '__init__.py')\n\n    # ── Version ──\n    bot.BOT_VERSION = '6.0.0-test'\n\n    # ── All button labels ──\n    bot.BTN_BACK_MAIN = '🔙 Main Menu'\n    bot.BTN_BACK = '🔙 Back'\n    bot.BTN_CANCEL = '❌ Cancel'\n    bot.BTN_DAILY_SALES = '📊 Daily Sales'\n    bot.BTN_MEMBER_MGMT = '👥 Members'\n    bot.BTN_CONSOLES = '🎮 Consoles'\n    bot.BTN_TODAY_REPORT = '📈 Today'\n    bot.BTN_STAFF_BOOK = '📅 Booking'\n    bot.BTN_INVENTORY_VIEW = '📦 Inventory'\n    bot.BTN_FINANCIAL_REPORT = '💰 Financial'\n    bot.BTN_ADMIN = '⚙️ Admin'\n    bot.BTN_SBK_WAITLIST = '⏳ Waitlist'\n    bot.BTN_SBK_NEW = '📝 New'\n    bot.BTN_SBK_CONFIRMED = '✅ Confirmed'\n    bot.BTN_GAME_LIB_MENU = '🎮 GameLib'\n    bot.BTN_GAMES = '🎮 Games'\n    bot.BTN_STOCK_MGMT = '📊 Stock'\n    bot.BTN_DISC_MGMT = '🏷️ Discount'\n    bot.BTN_SSD_DISC = '🔄 SSD'\n    bot.BTN_FOOD_SETUP = '🍽️ Food'\n    bot.BTN_FIRST_PURCHASE = '🆕 First Purchase'\n    bot.BTN_TOP_UP = '💰 Top Up'\n    bot.BTN_CHECK_MEMBER = '🔍 Check'\n    bot.BTN_VIEW_RANKS = '🏆 Ranks'\n    bot.BTN_PROMO_APPLY = '🎁 Promo'\n    bot.BTN_MANUAL_DISC = '✏️ Manual %'\n    bot.BTN_SKIP_DISC = '⏭️ Skip'\n    bot.BTN_FIN_CAPITAL = '💰 Capital'\n    bot.BTN_FIN_SHAREHOLDER = '👥 SH'\n    bot.BTN_FIN_TRANSFER = '↔️ Transfer'\n    bot.BTN_FIN_OPEX = '📋 OPEX'\n    bot.BTN_FIN_ASSET = '🏗️ Asset'\n    bot.BTN_FIN_ASSET_DISPOSE = '🗑️ Dispose'\n    bot.BTN_FIN_PREPAID = '📆 Prepaid'\n    bot.BTN_FIN_PAYABLE = '📝 Payable'\n    bot.BTN_FIN_SETTLE_PAY = '✅ SettlePay'\n    bot.BTN_FIN_RECEIVABLE = '📥 Receivable'\n    bot.BTN_FIN_SETTLE_REC = '✅ SettleRec'\n    bot.BTN_FIN_ADVPAY = '💵 Advance'\n    bot.BTN_FIN_SETTLE_ADVPAY = '✅ SettleAdv'\n    bot.BTN_FIN_ACCTS = '📊 Accounts'\n    bot.BTN_FIN_REPORT = '📈 FinReport'\n    bot.BTN_FIN_SETUP = '⚙️ Setup'\n    bot.BTN_GINST_VIEW = '👁️ View'\n    bot.BTN_GINST_ADD = '➕ Add'\n    bot.BTN_GINST_REMOVE = '❌ Remove'\n    bot.BTN_LIST_CONSOLE = '📋 List'\n    bot.BTN_ADD_CONSOLE = '➕ Add Console'\n    bot.BTN_DEL_CONSOLE = '❌ Delete'\n\n    # ── State constants ──\n    bot.MAIN_MENU = 0\n    bot.MEMBER = 1\n    bot.CONSOLE = 2\n    bot.MINS = 3\n    bot.MM_MENU = 100\n    bot.FINANCE_MENU = 200\n    bot.STAFF_SELECT = 10\n    bot.STOCK_PIN = 300\n    bot.STOCK_MENU = 301\n    bot.GINST_MENU = 400\n    bot.CON_MGMT_MENU = 500\n    bot.ADMIN_PIN = '1234'\n    bot.STOCK_ACCESS_PIN = '1234'\n    bot.CUSTOMER_BOT_TOKEN = 'fake-token'\n    bot.NAV_ROW = ['🔙 Back', '❌ Cancel']\n    bot.VALID_CONSOLES = ['C-01', 'C-02', 'C-03', 'C-04', 'C-05']\n    bot.ConversationHandler = MagicMock()\n    bot.ConversationHandler.END = -1\n\n    # ── Time ──\n    from datetime import datetime, timezone, timedelta\n    def _now_mmt():\n        return datetime.now(timezone(timedelta(hours=6, minutes=30)))\n    bot.now_mmt = _now_mmt\n\n    # ── Fetch functions ──\n    bot.fetch_allowed_staff_ids = MagicMock(return_value=[12345])\n    bot.fetch_members = MagicMock(return_value=['PSV_A001', 'PSV_A002', 'PSV_A003'])\n    bot.fetch_staff = MagicMock(return_value=['Staff1', 'Staff2', 'Staff3'])\n    bot.fetch_console_status = MagicMock(return_value=[\n        {'id': 'C-01', 'type': 'PS5', 'status': 'Free'},\n        {'id': 'C-02', 'type': 'PS5 Pro', 'status': 'Free'},\n    ])\n    bot.fetch_base_rate = MagicMock(return_value=5000)\n    bot.fetch_rank_table_display = MagicMock(return_value='Rank Table')\n    bot.fetch_rank_thresholds = MagicMock(return_value=(100000, 500000))\n    bot.fetch_console_games = MagicMock(return_value=[])\n    bot.get_consoles_from_setting = MagicMock(return_value=[])\n    bot.fetch_promotions_cached = MagicMock(return_value=[])\n    bot.step_hdr = MagicMock(return_value='📋 Step 1/6\\n')\n\n    # ── Handler refs (for cross-module calls) ──\n    bot.cmd_cancel = AsyncMock(return_value=-1)\n    bot.show_main_menu = AsyncMock(return_value=0)\n    bot.answer_callback_query = AsyncMock()\n    bot.show_shareholder_menu = AsyncMock(return_value=0)\n    bot.prompt_cap_acct = AsyncMock(return_value=0)\n    bot.prompt_opex_cat = AsyncMock(return_value=0)\n    bot.prompt_asset_name = AsyncMock(return_value=0)\n    bot.prompt_asset_dispose_sel = AsyncMock(return_value=0)\n\n    # ── gspread workbook mock ──\n    mock_ws = MagicMock()\n    mock_ws.get_all_values.return_value = [['H1', 'H2'], ['v1', 'v2']]\n    mock_ws.append_row = MagicMock()\n    mock_ws.update_cell = MagicMock()\n    mock_ws.update = MagicMock()\n    mock_ws.col_values.return_value = ['1000', '2000']\n    mock_ws.row_values.return_value = []\n    mock_ws.row_count = 2\n    mock_ws.title = 'Sales'\n    mock_wb = MagicMock()\n    mock_wb.worksheet.return_value = mock_ws\n    mock_wb.worksheet_by_title.return_value = mock_ws\n    mock_wb.sheet1 = mock_ws\n    bot.wb = mock_wb\n    bot.inv_sh = mock_ws\n\n    # ── API helpers ──\n    bot._replit_get = MagicMock(return_value=[])\n    bot._replit_post = MagicMock(return_value={'ok': True})\n    bot._replit_put = MagicMock(return_value={'ok': True})\n    bot._replit_delete = MagicMock(return_value={'ok': True})\n\n    # ── Stdlib ──\n    bot.logging = __import__('logging')\n    bot.re = __import__('re')\n    bot.json = __import__('json')\n    bot.asyncio = __import__('asyncio')\n\n    return bot\n\n\n# ── Install mocks BEFORE any test import ──\n_bot = _build_bot_mock()\nsys.modules['bot'] = _bot\n\n# Pre-register bot.handlers as a namespace package so __init__.py is skipped\n# but __path__ allows discovery of bot.handlers.xxx from disk\n_handlers = types.ModuleType('bot.handlers')\n_handlers.__package__ = 'bot.handlers'\n_handlers.__path__ = [os.path.join(_BOT_DIR, 'handlers')]\n_handlers.__file__ = os.path.join(_BOT_DIR, 'handlers', '__init__.py')\nsys.modules['bot.handlers'] = _handlers\n\n# Also pre-register bot.utils for modules that import it\n_utils = types.ModuleType('bot.utils')\n_utils.__package__ = 'bot.utils'\n_utils.__path__ = [os.path.join(_BOT_DIR, 'utils')]\n_utils.__file__ = os.path.join(_BOT_DIR, 'utils', '__init__.py')\nsys.modules['bot.utils'] = _utils\n\n# Mock gspread to prevent import errors\nsys.modules['gspread'] = MagicMock()\n\n\n# ────────────────────────────────────────────────────────────────\n# Fixtures\n# ────────────────────────────────────────────────────────────────\n\n@pytest.fixture\ndef mock_user():\n    user = MagicMock()\n    user.id = 12345\n    user.first_name = \"Test\"\n    user.last_name = \"User\"\n    user.username = \"test_user\"\n    user.is_bot = False\n    user.language_code = \"my\"\n    return user\n\n\n@pytest.fixture\ndef mock_chat():\n    chat = MagicMock()\n    chat.id = 67890\n    chat.type = \"private\"\n    chat.first_name = \"Test\"\n    chat.username = \"test_user\"\n    return chat\n\n\n@pytest.fixture\ndef mock_message(mock_user, mock_chat):\n    message = MagicMock()\n    message.message_id = 1\n    message.chat = mock_chat\n    message.from_user = mock_user\n    message.text = \"/start\"\n    message.date = None\n    message.reply_text = AsyncMock()\n    message.delete = AsyncMock()\n    message.edit_text = AsyncMock()\n    return message\n\n\n@pytest.fixture\ndef mock_update(mock_user, mock_chat, mock_message):\n    update = MagicMock()\n    update.update_id = 1\n    update.message = mock_message\n    update.effective_user = mock_user\n    update.effective_chat = mock_chat\n    update.callback_query = None\n    return update\n\n\n@pytest.fixture\ndef mock_context():\n    context = MagicMock()\n    context.user_data = {}\n    context.bot_data = {}\n    context.args = []\n    context.bot = AsyncMock()\n    context.bot.send_message = AsyncMock()\n    context.bot.edit_message_text = AsyncMock()\n    context.bot.answer_callback_query = AsyncMock()\n    context.bot.delete_message = AsyncMock()\n    context.bot.send_photo = AsyncMock()\n    context.bot.send_document = AsyncMock()\n    return context\n\n\n@pytest.fixture(autouse=True)\ndef _reset():\n    yield\n    _bot.fetch_allowed_staff_ids.return_value = [12345]\n    _bot.fetch_members.return_value = ['PSV_A001', 'PSV_A002']\n    _bot._replit_get.return_value = []\nCONFTESTEOF\n");

// Verify + run all tests
cmd('echo "=== SYNTAX ==="');
cmd('cd /root/psvibe-sales-bot && python3 -m py_compile tests/conftest.py 2>&1 && echo OK || echo FAIL');

cmd('echo "=== PYTEST ==="');
cmd('cd /root/psvibe-sales-bot && python3 -m pytest tests/ -v --tb=line --no-header 2>&1; echo "EXIT=$?"');

cmd('echo "=== FINAL COUNTS ==="');
cmd('cd /root/psvibe-sales-bot && python3 -m pytest tests/ --tb=no -q 2>&1');

conn.on('ready', () => {
    let cmdIndex = 0;
    let outputBuffer = '';

    function runNext() {
        if (cmdIndex >= commands.length) { conn.end(); return; }
        const c = commands[cmdIndex]; cmdIndex++;
        conn.exec(c, (err, stream) => {
            if (err) { outputBuffer += 'ERR:' + err + '\n'; runNext(); return; }
            stream.on('data', (d) => { outputBuffer += d.toString(); });
            stream.stderr.on('data', (d) => { outputBuffer += d.toString(); });
            stream.on('close', () => runNext());
        });
    }

    conn.on('close', () => {
        fs.writeFileSync('/home/node/.openclaw/workspace/test_framework_final.txt', outputBuffer);
        console.log('\nDone.');
    });

    runNext();
});

conn.connect({
    host: '5.223.81.16',
    port: 22,
    username: 'root',
    privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
