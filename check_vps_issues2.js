const { readFileSync, writeFileSync } = require('fs');
const { Client } = require('ssh2');

const key = readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const host = '5.223.81.16';
const user = 'root';

function sshExec(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let out = '', errOut = '';
      stream.on('data', d => out += d.toString());
      stream.stderr.on('data', d => errOut += d.toString());
      stream.on('close', () => resolve({ stdout: out, stderr: errOut }));
    });
  });
}

async function main() {
  const conn = new Client();
  const connPromise = new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
  });
  conn.connect({ host, username: user, privateKey: key, readyTimeout: 15000 });
  await connPromise;
  console.log('=== ADDITIONAL INVESTIGATION ===\n');

  let extra = '';

  // ── Issue 1: MySQL deeper check ──
  extra += '## Issue 1 Extra\n\n';

  // Full database list
  const dbs = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' -e 'SHOW DATABASES;' 2>/dev/null");
  console.log('Databases:\n' + dbs.stdout);
  extra += '### All databases\n```\n' + dbs.stdout + '```\n\n';

  // Check psvibe_sales tables in detail
  const psvTables = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' psvibe_sales -e 'SHOW TABLES;' 2>/dev/null");
  console.log('psvibe_sales tables:\n' + psvTables.stdout);
  extra += '### psvibe_sales tables\n```\n' + psvTables.stdout + '```\n\n';

  // Check SQLite
  const sqliteFiles = await sshExec(conn, "find /root/psvibe-sales-bot/sqlite -type f 2>/dev/null && ls -la /root/psvibe-sales-bot/sqlite/ 2>/dev/null");
  console.log('SQLite files:\n' + sqliteFiles.stdout);
  extra += '### SQLite setup\n```\n' + (sqliteFiles.stdout || 'Not found') + '```\n\n';

  const sqliteSetup = await sshExec(conn, "cat /root/psvibe-sales-bot/sqlite/setup.py 2>/dev/null | head -60");
  console.log('Sqlite setup.py:\n' + sqliteSetup.stdout);
  extra += '### sqlite/setup.py\n```\n' + sqliteSetup.stdout + '```\n\n';

  // Check mysql_db.py
  const mysqlDb = await sshExec(conn, "ls -la /root/psvibe-sales-bot/mysql_db.py 2>/dev/null && cat /root/psvibe-sales-bot/mysql_db.py 2>/dev/null | head -40");
  console.log('mysql_db.py:\n' + mysqlDb.stdout);
  extra += '### mysql_db.py\n```\n' + mysqlDb.stdout + '```\n\n';

  // Check if stock_out table exists
  const stockExist = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' psvibe_sales -e 'SELECT COUNT(*) as cnt FROM stock_out;' 2>/dev/null");
  console.log('stock_out exists?:\n' + stockExist.stdout);
  extra += '### stock_out check\n```\n' + stockExist.stdout + '```\n\n';

  const invExist = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' psvibe_sales -e 'SELECT COUNT(*) as cnt FROM inventory;' 2>/dev/null");
  console.log('inventory exists?:\n' + invExist.stdout);

  // Check the Setting sheet from Google Sheets
  const settingSheet = await sshExec(conn, "grep -n 'Setting\\|setting_sheet\\|SETTING_SHEET\\|get_setting_sh' /root/psvibe-sales-bot/bot/services/sheets_service.py 2>/dev/null | head -20");
  console.log('Setting sheet refs:\n' + settingSheet.stdout);
  extra += '### Setting sheet refs in sheets_service.py\n```\n' + settingSheet.stdout + '```\n\n';

  // Check stock_in.py and stock.py
  const stockPy = await sshExec(conn, "cat /root/psvibe-sales-bot/bot/handlers/stock.py 2>/dev/null | head -50");
  console.log('stock.py:\n' + stockPy.stdout);
  extra += '### stock.py headers\n```\n' + stockPy.stdout + '```\n\n';

  const stockInPy = await sshExec(conn, "cat /root/psvibe-sales-bot/bot/handlers/stock_in.py 2>/dev/null | head -50");
  console.log('stock_in.py:\n' + stockInPy.stdout);
  extra += '### stock_in.py headers\n```\n' + stockInPy.stdout + '```\n\n';

  // Check API endpoint for receiving stock data
  const apiEndpoints = await sshExec(conn, "grep -n 'inventory\\|stock' /root/psvibe_api_server/app.py 2>/dev/null | head -30");
  console.log('API inventory/stock endpoints:\n' + apiEndpoints.stdout);
  extra += '### API inventory endpoints\n```\n' + apiEndpoints.stdout + '```\n\n';

  // ── Issue 2: Receipt deeper check ──
  extra += '\n## Issue 2 Extra\n\n';

  // Check what step_sale_save does
  const saleSave = await sshExec(conn, "awk '/async def step_sale_save\\(/,/^async def step_/' /root/psvibe-sales-bot/bot/handlers/sales.py 2>/dev/null | head -100");
  console.log('step_sale_save (if exists):\n' + saleSave.stdout);
  extra += '### step_sale_save\n```\n' + (saleSave.stdout || 'Function does not exist') + '```\n\n';

  // Check what happens after step_sale_confirm - the end of the function
  const confirmEnd = await sshExec(conn, "awk '/async def step_sale_confirm\\(/,/^async def step_/' /root/psvibe-sales-bot/bot/handlers/sales.py 2>/dev/null");
  console.log('Full step_sale_confirm:\n' + confirmEnd.stdout);
  extra += '### Full step_sale_confirm\n```\n' + confirmEnd.stdout + '```\n\n';

  // Check state machine transitions
  const stateTransitions = await sshExec(conn, "grep -n 'BotState\\|SALE_CONFIRM\\|PAYMENT\\|PAY_AMOUNT\\|PAY_METHOD\\|SAVE\\|RECEIPT\\|SALES' /root/psvibe-sales-bot/bot/handlers/sales.py 2>/dev/null | head -40");
  console.log('State transitions:\n' + stateTransitions.stdout);
  extra += '### State transitions in sales.py\n```\n' + stateTransitions.stdout + '```\n\n';

  // Check what handlers/__init__.py exports for sales
  const handlersInit = await sshExec(conn, "grep -n 'sales\\|step_sale' /root/psvibe-sales-bot/bot/handlers/__init__.py 2>/dev/null");
  console.log('handler init exports:\n' + handlersInit.stdout);
  extra += '### handlers/__init__.py sales refs\n```\n' + handlersInit.stdout + '```\n\n';

  // Check app.py state machine registration
  const appPySales = await sshExec(conn, "grep -n 'sale\\|SALE\\|step_sale' /root/psvibe-sales-bot/bot/app.py 2>/dev/null | head -30");
  console.log('app.py sales registration:\n' + appPySales.stdout);
  extra += '### app.py sales registration\n```\n' + appPySales.stdout + '```\n\n';

  // Check receipts directory
  const receiptsDir = await sshExec(conn, "ls -la /root/psvibe-sales-bot/bot/receipts/ 2>/dev/null && find /root/psvibe-sales-bot/bot/receipts -type f 2>/dev/null | head -20");
  console.log('Receipts dir:\n' + receiptsDir.stdout);
  extra += '### receipts directory\n```\n' + (receiptsDir.stdout || 'Empty or does not exist') + '```\n\n';

  // ── Issue 3: Extra checks ──
  extra += '\n## Issue 3 Extra\n\n';

  // Check GEMINI_API_KEY
  const geminiKey = await sshExec(conn, "grep -ri 'GEMINI_API_KEY' /root/psvibe-sales-bot/customer_bot/ 2>/dev/null | head -5");
  console.log('GEMINI_API_KEY refs:\n' + geminiKey.stdout);
  extra += '### GEMINI_API_KEY\n```\n' + geminiKey.stdout + '```\n\n';

  // Check env or .env
  const envKey = await sshExec(conn, "grep -i 'GEMINI' /root/psvibe-sales-bot/.env 2>/dev/null; grep -i 'GEMINI' /root/psvibe-sales-bot/customer_bot/.env 2>/dev/null; systemctl cat psvibe_customer_bot 2>/dev/null | grep -i 'GEMINI'");
  console.log('GEMINI in env/service:\n' + envKey.stdout);
  extra += '### GEMINI in env/service\n```\n' + (envKey.stdout || 'Not found in .env or service file') + '```\n\n';

  // Check service file
  const svcFile = await sshExec(conn, "systemctl cat psvibe_customer_bot 2>/dev/null");
  console.log('Service file:\n' + svcFile.stdout);
  extra += '### Service file\n```\n' + svcFile.stdout + '```\n\n';

  // Check prompts.py for System prompt
  const systemPrompt = await sshExec(conn, "cat /root/psvibe-sales-bot/customer_bot/data/prompts.py 2>/dev/null | head -250");
  console.log('Prompts.py:\n' + systemPrompt.stdout);
  extra += '### data/prompts.py\n```\n' + systemPrompt.stdout + '```\n\n';

  // Check data/__init__.py
  const dataInit = await sshExec(conn, "cat /root/psvibe-sales-bot/customer_bot/data/__init__.py 2>/dev/null");
  console.log('data/__init__.py:\n' + dataInit.stdout);
  extra += '### data/__init__.py\n```\n' + dataInit.stdout + '```\n\n';

  // Check api.py for config/contacts
  const apiPy = await sshExec(conn, "grep -n 'def _fetch_config\\|def _fetch_contacts\\|def _fetch_members\\|def _fetch_promotions\\|def _fetch_consoles\\|def _fetch_games_full\\|def _build_rate_lines\\|def _build_bonus_table_text\\|STAF' /root/psvibe-sales-bot/customer_bot/api.py 2>/dev/null | head -30");
  console.log('api.py function defs:\n' + apiPy.stdout);
  extra += '### api.py function defs\n```\n' + apiPy.stdout + '```\n\n';

  // Check for duplicate or conflicting instances
  const otherInstances = await sshExec(conn, "ps aux | grep customer_bot | grep -v grep 2>/dev/null");
  console.log('Running customer_bot processes:\n' + otherInstances.stdout);
  extra += '### Running processes\n```\n' + (otherInstances.stdout || 'None') + '```\n\n';

  writeFileSync('/tmp/vps_extra_findings.md', extra);
  conn.end();
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
