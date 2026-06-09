const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const commands = [];

function cmd(c) { commands.push(c); }

// ============================================================
// Rewrite conftest.py to use hybrid mock: bot package is mocked
// but bot.handlers.* resolves from real filesystem
// ============================================================
cmd("cat > /root/psvibe-sales-bot/tests/conftest.py << 'CONFTESTEOF'\n\"\"\"Shared fixtures and mocks for PS VIBE bot tests.\n\nStrategy: mock `bot` package in sys.modules with all constants/functions,\ngive it __path__ pointing to the real bot directory so \"bot.handlers.xxx\"\nresolves to actual files on disk. Handler files do \"from bot import *\" —\nwith bot mocked in sys.modules, those imports resolve from our mock.\n\"\"\"\nimport pytest, sys, types, os\nfrom unittest.mock import AsyncMock, MagicMock, patch\n\n\n# Determine the real bot package path\n_BOT_DIR = '/root/psvibe-sales-bot/bot'\n\n\ndef _create_mock_bot_package():\n    \"\"\"Create a proper mock for the 'bot' package that sits in sys.modules.\"\"\"\n    # Use a real module so Python recognizes it as a package\n    bot = types.ModuleType('bot')\n    bot.__package__ = 'bot'\n    bot.__path__ = [_BOT_DIR]           # Allows discovery of bot.handlers, bot.utils\n    bot.__file__ = os.path.join(_BOT_DIR, '__init__.py')\n\n    # ── All constants that handlers import via \"from bot import *\" ──\n    bot.BTN_BACK_MAIN = '🔙 Back'\n    bot.BTN_BACK = '🔙 Back'\n    bot.BTN_CANCEL = '❌ Cancel'\n    bot.BTN_DAILY_SALES = '📊 Daily Sales'\n    bot.BTN_MEMBER_MGMT = '👥 Members'\n    bot.BTN_CONSOLES = '🎮 Consoles'\n    bot.BTN_TODAY_REPORT = '📈 Today Report'\n    bot.BTN_STAFF_BOOK = '📅 Staff Book'\n    bot.BTN_INVENTORY_VIEW = '📦 Inventory'\n    bot.BTN_FINANCIAL_REPORT = '💰 Financial'\n    bot.BTN_ADMIN = '⚙️ Admin'\n    bot.BTN_SBK_WAITLIST = '⏳ Waitlist'\n    bot.BTN_SBK_NEW = '📝 New Booking'\n    bot.BTN_SBK_CONFIRMED = '✅ Confirmed'\n    bot.BTN_GAME_LIB_MENU = '🎮 Game Library'\n    bot.BTN_GAMES = '🎮 Games'\n    bot.BTN_STOCK_MGMT = '📊 Stock Management'\n    bot.BTN_DISC_MGMT = '🏷️ Discount Management'\n    bot.BTN_SSD_DISC = '🔄 SSD Discount'\n    bot.BTN_FOOD_SETUP = '🍽️ Food Setup'\n    bot.BTN_FIRST_PURCHASE = '🆕 First Purchase'\n    bot.BTN_TOP_UP = '💰 Top Up'\n    bot.BTN_CHECK_MEMBER = '🔍 Check Member'\n    bot.BTN_VIEW_RANKS = '🏆 View Ranks'\n    bot.BTN_PROMO_APPLY = '🎁 Promo Apply'\n    bot.BTN_MANUAL_DISC = '✏️ Manual Discount'\n    bot.BTN_SKIP_DISC = '⏭️ Skip Discount'\n    bot.BTN_FIN_CAPITAL = '💰 Capital'\n    bot.BTN_FIN_SHAREHOLDER = '👥 Shareholder'\n    bot.BTN_FIN_TRANSFER = '↔️ Transfer'\n    bot.BTN_FIN_OPEX = '📋 OPEX'\n    bot.BTN_FIN_ASSET = '🏗️ Asset'\n    bot.BTN_FIN_ASSET_DISPOSE = '🗑️ Dispose'\n    bot.BTN_FIN_PREPAID = '📆 Prepaid'\n    bot.BTN_FIN_PAYABLE = '📝 Payable'\n    bot.BTN_FIN_SETTLE_PAY = '✅ Settle Pay'\n    bot.BTN_FIN_RECEIVABLE = '📥 Receivable'\n    bot.BTN_FIN_SETTLE_REC = '✅ Settle Rec'\n    bot.BTN_FIN_ADVPAY = '💵 Advance'\n    bot.BTN_FIN_SETTLE_ADVPAY = '✅ Settle Adv'\n    bot.BTN_FIN_ACCTS = '📊 Accounts'\n    bot.BTN_FIN_REPORT = '📈 Fin Report'\n    bot.BTN_FIN_SETUP = '⚙️ Fin Setup'\n\n    # State constants\n    bot.MAIN_MENU = 0\n    bot.MEMBER = 1\n    bot.CONSOLE = 2\n    bot.MINS = 3\n    bot.MM_MENU = 100\n    bot.FINANCE_MENU = 200\n    bot.STAFF_SELECT = 10\n    bot.STOCK_PIN = 300\n    bot.STOCK_MENU = 301\n    bot.STOCK_ACCESS_PIN = '1234'\n    bot.ADMIN_PIN = '1234'\n    bot.NAV_ROW = ['🔙 Back', '❌ Cancel']\n    bot.VALID_CONSOLES = ['C-01', 'C-02', 'C-03', 'C-04', 'C-05']\n\n    # Time helper\n    from datetime import datetime, timezone, timedelta\n    def _now_mmt():\n        return datetime.now(timezone(timedelta(hours=6, minutes=30)))\n    bot.now_mmt = _now_mmt\n\n    # Fetch functions (mock returns)\n    bot.fetch_allowed_staff_ids = MagicMock(return_value=[12345])\n    bot.fetch_members = MagicMock(return_value=['PSV_A001', 'PSV_A002', 'PSV_A003'])\n    bot.fetch_staff = MagicMock(return_value=['Staff1', 'Staff2', 'Staff3'])\n    bot.fetch_console_status = MagicMock(return_value=[\n        {'id': 'C-01', 'type': 'PS5', 'status': 'Free'},\n        {'id': 'C-02', 'type': 'PS5 Pro', 'status': 'Free'},\n    ])\n    bot.fetch_base_rate = MagicMock(return_value=5000)\n    bot.fetch_rank_table_display = MagicMock(return_value='Rank Table')\n    bot.fetch_rank_thresholds = MagicMock(return_value=(100000, 500000))\n    bot.step_hdr = MagicMock(return_value='📋 Step 1/6\\n')\n    bot.cmd_cancel = AsyncMock()\n    bot.show_main_menu = AsyncMock()\n    bot.answer_callback_query = AsyncMock()\n    bot.show_shareholder_menu = AsyncMock(return_value=0)\n    bot.prompt_cap_acct = AsyncMock(return_value=0)\n    bot.prompt_opex_cat = AsyncMock(return_value=0)\n    bot.prompt_asset_name = AsyncMock(return_value=0)\n    bot.prompt_asset_dispose_sel = AsyncMock(return_value=0)\n\n    # gspread workbook mock (used by finance, stock)\n    mock_ws = MagicMock()\n    mock_ws.get_all_values.return_value = []\n    mock_ws.append_row = MagicMock()\n    mock_ws.update_cell = MagicMock()\n    mock_ws.update = MagicMock()\n    mock_ws.col_values.return_value = []\n    mock_wb = MagicMock()\n    mock_wb.worksheet.return_value = mock_ws\n    mock_wb.worksheet_by_title.return_value = mock_ws\n    mock_wb.sheet1 = mock_ws\n    bot.wb = mock_wb\n    bot.inv_sh = mock_ws\n\n    # API helpers (mocked)\n    bot._replit_get = MagicMock(return_value=[])\n    bot._replit_post = MagicMock(return_value={'ok': True})\n    bot._replit_put = MagicMock(return_value={'ok': True})\n    bot._replit_delete = MagicMock(return_value={'ok': True})\n\n    # Standard library imports that handlers use\n    bot.logging = __import__('logging')\n    bot.re = __import__('re')\n    bot.json = __import__('json')\n    bot.asyncio = __import__('asyncio')\n\n    # Markdown mode constant\n    bot.MD = 'Markdown'\n\n    return bot\n\n\n# ── Install the mock bot BEFORE any test import ──\n_bot = _create_mock_bot_package()\nsys.modules['bot'] = _bot\n\n# Also mock gspread to prevent import errors\nsys.modules['gspread'] = MagicMock()\nsys.modules['gspread'].service_account = MagicMock()\n\n# Mock telegram modules that aren't installed but referenced\nfor _mod in ['telegram.constants', 'telegram.ext.filters']:\n    if _mod not in sys.modules:\n        sys.modules[_mod] = MagicMock()\n\n\n# ────────────────────────────────────────────────────────────────\n# Fixtures\n# ────────────────────────────────────────────────────────────────\n\n@pytest.fixture\ndef mock_user():\n    user = MagicMock()\n    user.id = 12345\n    user.first_name = \"Test\"\n    user.last_name = \"User\"\n    user.username = \"test_user\"\n    user.is_bot = False\n    user.language_code = \"my\"\n    return user\n\n\n@pytest.fixture\ndef mock_chat():\n    chat = MagicMock()\n    chat.id = 67890\n    chat.type = \"private\"\n    chat.first_name = \"Test\"\n    chat.username = \"test_user\"\n    return chat\n\n\n@pytest.fixture\ndef mock_message(mock_user, mock_chat):\n    message = MagicMock()\n    message.message_id = 1\n    message.chat = mock_chat\n    message.from_user = mock_user\n    message.text = \"/start\"\n    message.date = None\n    message.reply_text = AsyncMock()\n    message.delete = AsyncMock()\n    message.edit_text = AsyncMock()\n    return message\n\n\n@pytest.fixture\ndef mock_update(mock_user, mock_chat, mock_message):\n    update = MagicMock()\n    update.update_id = 1\n    update.message = mock_message\n    update.effective_user = mock_user\n    update.effective_chat = mock_chat\n    update.callback_query = None\n    return update\n\n\n@pytest.fixture\ndef mock_context():\n    context = MagicMock()\n    context.user_data = {}\n    context.bot_data = {}\n    context.args = []\n    context.bot = AsyncMock()\n    context.bot.send_message = AsyncMock()\n    context.bot.edit_message_text = AsyncMock()\n    context.bot.answer_callback_query = AsyncMock()\n    context.bot.delete_message = AsyncMock()\n    context.bot.send_photo = AsyncMock()\n    context.bot.send_document = AsyncMock()\n    context.bot.send_contact = AsyncMock()\n    context.bot.copy_message = AsyncMock()\n    return context\n\n\n@pytest.fixture(autouse=True)\ndef _reset_after_test():\n    \"\"\"Reset mocks between tests.\"\"\"\n    yield\n    _bot.fetch_allowed_staff_ids.return_value = [12345]\n    _bot.fetch_members.return_value = ['PSV_A001', 'PSV_A002']\n    _bot._replit_get.return_value = []\n    _bot.wb.worksheet.return_value.get_all_values.return_value = []\nCONFTESTEOF\n");

// Run syntax check + full pytest
cmd('echo "=== SYNTAX CHECK ==="');
cmd('cd /root/psvibe-sales-bot && python3 -m py_compile tests/conftest.py 2>&1 && echo "conftest.py: OK" || echo "conftest.py: FAIL"');

cmd('echo "=== RUNNING ALL TESTS ==="');
cmd('cd /root/psvibe-sales-bot && python3 -m pytest tests/ -v --tb=short --no-header 2>&1; echo "EXIT=$?"');

console.log("Phase 7 commands ready.");

conn.on('ready', () => {
    let cmdIndex = 0;
    let outputBuffer = '';

    function runNext() {
        if (cmdIndex >= commands.length) { conn.end(); return; }
        const c = commands[cmdIndex];
        cmdIndex++;
        conn.exec(c, (err, stream) => {
            if (err) { outputBuffer += 'ERR: ' + err + '\n'; runNext(); return; }
            stream.on('data', (d) => { outputBuffer += d.toString(); });
            stream.stderr.on('data', (d) => { outputBuffer += d.toString(); });
            stream.on('close', () => runNext());
        });
    }

    conn.on('close', () => {
        fs.writeFileSync('/home/node/.openclaw/workspace/test_framework_output7.txt', outputBuffer);
        console.log('\nPhase 7 complete.');
    });

    runNext();
});

conn.connect({
    host: '5.223.81.16',
    port: 22,
    username: 'root',
    privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
