const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();

const commands = [];

function cmd(c) { commands.push(c); }

// ============================================================
// STEP 1: Explore existing codebase structure
// ============================================================
cmd('echo "=== EXPLORING CODEBASE ==="');
cmd('ls -la /root/psvibe-sales-bot/ 2>/dev/null || echo "No /root/psvibe-sales-bot dir"');
cmd('ls -la /root/psvibe-sales-bot/bot/ 2>/dev/null || echo "No bot/ dir"');
cmd('ls -la /root/psvibe-sales-bot/bot/handlers/ 2>/dev/null || ls -la /root/psvibe-sales-bot/handlers/ 2>/dev/null || echo "No handlers dir found"');
cmd('find /root/psvibe-sales-bot -maxdepth 3 -name "*.py" -type f | sort 2>/dev/null || echo "No python files"');
cmd('python3 -m pytest --version 2>&1');
cmd('grep -r "from telegram" /root/psvibe-sales-bot/ --include="*.py" -l 2>/dev/null | sort');
cmd('head -100 /root/psvibe-sales-bot/bot.py 2>/dev/null || head -100 /root/psvibe-sales-bot/main.py 2>/dev/null || echo "No main bot file found"');
cmd('cat /root/psvibe-sales-bot/requirements.txt 2>/dev/null || echo "No requirements.txt"');

// ============================================================
// STEP 2: Create directory structure
// ============================================================
cmd('echo "=== CREATING DIRECTORIES ==="');
cmd('mkdir -p /root/psvibe-sales-bot/tests');
cmd('mkdir -p /root/coordination/findings');

// ============================================================
// STEP 3: Create pytest.ini
// ============================================================
cmd("cat > /root/psvibe-sales-bot/pytest.ini << 'PYTESTINI'\n[pytest]\nasyncio_mode = auto\ntestpaths = tests\npython_files = test_*.py\nmarkers =\n    asyncio: asyncio-based tests\nPYTESTINI\n");

// ============================================================
// STEP 4: Create conftest.py
// ============================================================
cmd("cat > /root/psvibe-sales-bot/tests/conftest.py << 'CONFTESTEOF'\nimport pytest\nimport asyncio\nimport json\nfrom unittest.mock import AsyncMock, MagicMock, patch\n\n\n@pytest.fixture\ndef mock_user():\n    user = MagicMock()\n    user.id = 12345\n    user.first_name = \"Test\"\n    user.last_name = \"User\"\n    user.username = \"test_user\"\n    user.is_bot = False\n    user.language_code = \"my\"\n    return user\n\n\n@pytest.fixture\ndef mock_chat():\n    chat = MagicMock()\n    chat.id = 67890\n    chat.type = \"private\"\n    chat.first_name = \"Test\"\n    chat.username = \"test_user\"\n    return chat\n\n\n@pytest.fixture\ndef mock_chat_group():\n    chat = MagicMock()\n    chat.id = -1001234567890\n    chat.type = \"supergroup\"\n    chat.title = \"PS VIBE Test Group\"\n    return chat\n\n\n@pytest.fixture\ndef mock_message(mock_user, mock_chat):\n    message = MagicMock()\n    message.message_id = 1\n    message.chat = mock_chat\n    message.from_user = mock_user\n    message.text = \"/start\"\n    message.date = None\n    return message\n\n\n@pytest.fixture\ndef mock_update(mock_user, mock_chat, mock_message):\n    update = MagicMock()\n    update.update_id = 1\n    update.message = mock_message\n    update.effective_user = mock_user\n    update.effective_chat = mock_chat\n    update.callback_query = None\n    return update\n\n\n@pytest.fixture\ndef mock_context():\n    context = MagicMock()\n    context.user_data = {}\n    context.bot_data = {}\n    context.args = []\n    context.bot = AsyncMock()\n    context.bot.send_message = AsyncMock()\n    context.bot.edit_message_text = AsyncMock()\n    context.bot.answer_callback_query = AsyncMock()\n    context.bot.delete_message = AsyncMock()\n    context.bot.send_photo = AsyncMock()\n    context.bot.send_document = AsyncMock()\n    context.bot.send_poll = AsyncMock()\n    context.bot.send_contact = AsyncMock()\n    context.bot.copy_message = AsyncMock()\n    return context\n\n\n@pytest.fixture\ndef mock_callback_update(mock_update):\n    update = MagicMock()\n    update.update_id = 2\n    update.message = None\n    update.effective_user = mock_update.effective_user\n    update.effective_chat = mock_update.effective_chat\n    cq = MagicMock()\n    cq.id = \"cb_12345\"\n    cq.from_user = mock_update.effective_user\n    cq.message = MagicMock()\n    cq.message.message_id = 99\n    cq.message.chat = mock_update.effective_chat\n    cq.data = \"main_menu\"\n    cq.chat_instance = \"abc123\"\n    cq.answer = AsyncMock()\n    update.callback_query = cq\n    return update, cq\n\n\n@pytest.fixture\ndef mock_db_worksheet():\n    ws = MagicMock()\n    ws.get_all_values = MagicMock(return_value=[\n        [\"Date\", \"Staff\", \"Member\", \"Sales\", \"Amount\"],\n        [\"2026-05-01\", \"Staff1\", \"Member1\", \"5\", \"50000\"]\n    ])\n    ws.get_all_records = MagicMock(return_value=[\n        {\"Date\": \"2026-05-01\", \"Staff\": \"Staff1\", \"Member\": \"Member1\", \"Sales\": \"5\", \"Amount\": \"50000\"}\n    ])\n    ws.append_row = MagicMock()\n    ws.update_cell = MagicMock()\n    ws.update = MagicMock()\n    ws.row_values = MagicMock(return_value=[\"2026-05-01\", \"Staff1\", \"Member1\", \"5\", \"50000\"])\n    ws.col_values = MagicMock(return_value=[\"Member1\", \"Member2\"])\n    ws.find = MagicMock()\n    ws.cell = MagicMock()\n    ws.row_count = 2\n    ws.col_count = 5\n    ws.title = \"Sales\"\n    return ws\n\n\n@pytest.fixture\ndef mock_db(mock_db_worksheet):\n    with patch('bot.wb') as mock_wb:\n        mock_wb.worksheet = MagicMock(return_value=mock_db_worksheet)\n        mock_wb.worksheet_by_title = MagicMock(return_value=mock_db_worksheet)\n        mock_wb.worksheets = MagicMock(return_value=[mock_db_worksheet])\n        mock_wb.sheet1 = mock_db_worksheet\n        yield mock_wb\n\n\n@pytest.fixture\ndef assert_state(mock_context):\n    def _assert(key, expected_value):\n        actual = mock_context.user_data.get(key)\n        assert actual == expected_value, f\"Expected user_data['{key}'] = '{expected_value}', got '{actual}'\"\n    return _assert\n\n\n@pytest.fixture(autouse=True)\ndef reset_between_tests():\n    pass\nCONFTESTEOF\n");
cmd('echo "conftest.py created"');

console.log("Phase 1 commands loaded. Connecting...");

conn.on('ready', () => {
    console.log('SSH connected');
    let cmdIndex = 0;
    let outputBuffer = '';

    function runNext() {
        if (cmdIndex >= commands.length) {
            conn.end();
            return;
        }
        const c = commands[cmdIndex];
        cmdIndex++;
        console.log(`\n### CMD ${cmdIndex}/${commands.length}`);
        conn.exec(c, (err, stream) => {
            if (err) { outputBuffer += `ERROR: ${err}\n`; runNext(); return; }
            stream.on('data', (data) => { outputBuffer += data.toString(); });
            stream.stderr.on('data', (data) => { outputBuffer += data.toString(); });
            stream.on('close', () => { runNext(); });
        });
    }

    conn.on('close', () => {
        fs.writeFileSync('/home/node/.openclaw/workspace/test_framework_output1.txt', outputBuffer);
        console.log('\nPhase 1 complete. Output saved.');
    });

    runNext();
});

conn.connect({
    host: '5.223.81.16',
    port: 22,
    username: 'root',
    privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
