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
  
  conn.connect({
    host, username: user, privateKey: key,
    readyTimeout: 15000
  });
  
  await connPromise;
  console.log('Connected to VPS\n');
  
  let report = '# VPS Issue Investigation Report\n\n';
  
  // === ISSUE 1: Inventory Stock ===
  console.log('=== ISSUE 1: INVENTORY STOCK ===');
  report += '## Issue 1: Inventory Stock = All 10\n\n';
  
  // Check MySQL tables
  const tables = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' psvibe_sales -e 'SHOW TABLES;' 2>/dev/null");
  console.log('MySQL tables:\n' + tables.stdout);
  report += '### MySQL Tables\n```\n' + tables.stdout + '```\n\n';

  // Check if food_items table exists
  let foodItemsResult = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' psvibe_sales -e 'DESCRIBE food_items;' 2>/dev/null");
  console.log('food_items columns:\n' + foodItemsResult.stdout);
  if (foodItemsResult.stdout.trim()) {
    const foodItemsData = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' psvibe_sales -e 'SELECT * FROM food_items;' 2>/dev/null");
    console.log('food_items data:\n' + foodItemsData.stdout);
    report += '### food_items table\n```\n' + foodItemsResult.stdout + '\n```\nData:\n```\n' + foodItemsData.stdout + '```\n\n';
  }

  // Check inventory table
  let invResult = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' psvibe_sales -e 'DESCRIBE inventory;' 2>/dev/null");
  console.log('inventory columns:\n' + invResult.stdout);
  if (invResult.stdout.trim()) {
    const invData = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' psvibe_sales -e 'SELECT * FROM inventory LIMIT 25;' 2>/dev/null");
    console.log('inventory data:\n' + invData.stdout);
    report += '### inventory table\n```\n' + invResult.stdout + '\n```\nData:\n```\n' + invData.stdout + '```\n\n';
  } else {
    report += '### inventory table\nDoes not exist.\n\n';
  }

  // Check stock_out table
  let stockResult = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' psvibe_sales -e 'DESCRIBE stock_out;' 2>/dev/null");
  console.log('stock_out columns:\n' + stockResult.stdout);
  if (stockResult.stdout.trim()) {
    const stockData = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' psvibe_sales -e 'SELECT * FROM stock_out LIMIT 10;' 2>/dev/null");
    console.log('stock_out data:\n' + stockData.stdout);
    report += '### stock_out table\n```\n' + stockResult.stdout + '\n```\nData:\n```\n' + stockData.stdout + '```\n\n';
  } else {
    report += '### stock_out table\nDoes not exist.\n\n';
  }

  // Check settings table  
  const settingsResult = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' psvibe_sales -e 'DESCRIBE settings;' 2>/dev/null");
  console.log('settings columns:\n' + settingsResult.stdout);
  if (settingsResult.stdout.trim()) {
    const settingsData = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' psvibe_sales -e 'SELECT * FROM settings LIMIT 25;' 2>/dev/null");
    console.log('settings data:\n' + settingsData.stdout);
    report += '### settings table\n```\n' + settingsResult.stdout + '\n```\nData:\n```\n' + settingsData.stdout + '```\n\n';
  }

  // Check API inventory endpoint
  const apiInvEndpoint = await sshExec(conn, "grep -n -A 30 '/api/sheets/inventory' /root/psvibe_api_server/app.py 2>/dev/null | head -40");
  console.log('API inventory endpoint:\n' + apiInvEndpoint.stdout);
  report += '### API /api/sheets/inventory endpoint\n```\n' + apiInvEndpoint.stdout + '```\n\n';

  // Check API stock_out endpoint if exists
  const apiStockEndpoint = await sshExec(conn, "grep -n -A 20 '/api/sheets/stock' /root/psvibe_api_server/app.py 2>/dev/null | head -25");
  if (apiStockEndpoint.stdout.trim()) {
    console.log('API stock endpoint:\n' + apiStockEndpoint.stdout);
    report += '### API stock endpoint\n```\n' + apiStockEndpoint.stdout + '```\n\n';
  }

  // Check food.py stock fetching
  const foodStockFetch = await sshExec(conn, "grep -n -B 2 -A 10 'stock\\|inventory\\|Stock\\|Inven' /root/psvibe-sales-bot/bot/handlers/food.py 2>/dev/null | head -40");
  console.log('food.py stock references:\n' + foodStockFetch.stdout);
  report += '### food.py stock/inventory handling\n```\n' + foodStockFetch.stdout + '```\n\n';

  // Check sheets_service.py for stock/setting
  const sheetsStock = await sshExec(conn, "grep -n 'stock\\|Stock\\|inventory\\|Inven\\|Setting\\|setting' /root/psvibe-sales-bot/bot/services/sheets_service.py 2>/dev/null | head -30");
  console.log('sheets_service stock/setting:\n' + sheetsStock.stdout);
  report += '### sheets_service.py stock/setting\n```\n' + sheetsStock.stdout + '```\n\n';

  // Find all files with inventory/stock references
  const filesWithStock = await sshExec(conn, "find /root/psvibe-sales-bot -name '*.py' -not -path '*/__pycache__/*' -exec grep -l 'inventory\\|stock' {} \\; 2>/dev/null");
  console.log('Files with inventory/stock:\n' + filesWithStock.stdout);
  report += '### Files referencing inventory/stock\n```\n' + filesWithStock.stdout + '```\n\n';

  // === ISSUE 2: RECEIPT ===
  console.log('\n=== ISSUE 2: RECEIPT ===');
  report += '## Issue 2: Missing Receipt Step\n\n';
  
  // Check states.py for SAVE/RECEIPT
  const stateDefs = await sshExec(conn, "cat /root/psvibe-sales-bot/bot/states.py 2>/dev/null");
  console.log('State definitions:\n' + stateDefs.stdout);
  report += '### BotState definitions\n```\n' + stateDefs.stdout + '```\n\n';

  // Check sales.py step functions
  const salesSteps = await sshExec(conn, "grep -n 'def step_sale' /root/psvibe-sales-bot/bot/handlers/sales.py 2>/dev/null");
  console.log('Sales step functions:\n' + salesSteps.stdout);
  report += '### Sales step functions\n```\n' + salesSteps.stdout + '```\n\n';

  // Check step_sale_confirm full function
  const confirmFunc = await sshExec(conn, "awk '/async def step_sale_confirm\\(/,/^async def step_/' /root/psvibe-sales-bot/bot/handlers/sales.py 2>/dev/null | head -100");
  console.log('step_sale_confirm function:\n' + confirmFunc.stdout);
  report += '### step_sale_confirm function\n```\n' + confirmFunc.stdout + '```\n\n';

  // Check step_sale_save full function
  const saveFunc = await sshExec(conn, "awk '/async def step_sale_save\\(/,/^async def step_/' /root/psvibe-sales-bot/bot/handlers/sales.py 2>/dev/null | head -100");
  console.log('step_sale_save function:\n' + saveFunc.stdout);
  report += '### step_sale_save function\n```\n' + saveFunc.stdout + '```\n\n';

  // After SAVE - what happens?
  const afterSave = await sshExec(conn, "grep -n -A 5 'step_sale_save\\|SAVE' /root/psvibe-sales-bot/bot/handlers/sales.py 2>/dev/null | head -40");
  console.log('After SAVE:\n' + afterSave.stdout);
  report += '### After SAVE\n```\n' + afterSave.stdout + '```\n\n';

  // Search for receipt generation anywhere
  const receiptSearch = await sshExec(conn, "grep -rn 'receipt\\|Receipt\\|receipt_img\\|Invoice\\|generate_receipt' /root/psvibe-sales-bot/ --include='*.py' 2>/dev/null | grep -v __pycache__ | head -30");
  console.log('Receipt references:\n' + receiptSearch.stdout);
  report += '### Receipt references in codebase\n```\n' + receiptSearch.stdout + '```\n\n';

  // Check if receipt files exist
  const receiptFiles = await sshExec(conn, "find /root/psvibe-sales-bot -name '*receipt*' -o -name '*Receipt*' -o -name '*invoice*' -o -name '*Invoice*' -not -path '*/__pycache__/*' 2>/dev/null");
  console.log('Receipt files:\n' + receiptFiles.stdout);
  report += '### Receipt template/image files\n```\n' + (receiptFiles.stdout || 'None found') + '```\n\n';

  // Check receipt-related code in deploy files
  const deployReceipt = await sshExec(conn, "find /root -name 'deploy_receipt*' -o -name '*receipt*' -not -path '*/__pycache__/*' 2>/dev/null | head -10");
  console.log('Deploy receipt files:\n' + deployReceipt.stdout);
  report += '### Deploy receipt scripts\n```\n' + (deployReceipt.stdout || 'None found') + '```\n\n';

  // === ISSUE 3: CUSTOMER BOT AI ===
  console.log('\n=== ISSUE 3: CUSTOMER BOT ===');
  report += '## Issue 3: Customer Bot Ko VIBE Broken\n\n';
  
  // Service status
  const serviceStatus = await sshExec(conn, "echo '=== IS-ACTIVE ===' && systemctl is-active psvibe_customer_bot 2>&1 && echo '=== STATUS HEAD ===' && systemctl status psvibe_customer_bot 2>&1 | head -20");
  console.log('Service status:\n' + serviceStatus.stdout);
  report += '### Service Status\n```\n' + serviceStatus.stdout + '```\n\n';

  // Recent logs
  const logs = await sshExec(conn, "journalctl -u psvibe_customer_bot --no-pager -n 40 2>&1");
  console.log('Recent logs:\n' + logs.stdout);
  report += '### Recent Logs (last 40)\n```\n' + logs.stdout + '```\n\n';

  // Check for error patterns in logs
  const errorLogs = await sshExec(conn, "journalctl -u psvibe_customer_bot --no-pager -n 100 2>&1 | grep -i 'error\\|fail\\|exception\\|traceback\\|crash' | tail -20");
  console.log('Error patterns:\n' + errorLogs.stdout);
  report += '### Error Patterns in Logs\n```\n' + (errorLogs.stdout || 'None found') + '```\n\n';

  // File timestamps
  const timestamps = await sshExec(conn, "stat --format='%Y %y %n' /root/psvibe-sales-bot/customer_bot/main.py /root/psvibe-sales-bot/customer_bot/ai.py /root/psvibe-sales-bot/customer_bot/handlers.py 2>&1");
  console.log('File timestamps:\n' + timestamps.stdout);
  const now = Math.floor(Date.now() / 1000);
  report += '### File Modification Times (current ts: ' + now + ')\n```\n' + timestamps.stdout + '```\n\n';

  // Compile checks
  const compAI = await sshExec(conn, "python3 -m py_compile /root/psvibe-sales-bot/customer_bot/ai.py 2>&1; echo 'EXIT_CODE:'$?");
  console.log('ai.py compile:\n' + compAI.stdout);
  report += '### ai.py Compile\n```\n' + compAI.stdout + '```\n\n';

  const compMain = await sshExec(conn, "python3 -m py_compile /root/psvibe-sales-bot/customer_bot/main.py 2>&1; echo 'EXIT_CODE:'$?");
  console.log('main.py compile:\n' + compMain.stdout);
  report += '### main.py Compile\n```\n' + compMain.stdout + '```\n\n';

  const compHandlers = await sshExec(conn, "python3 -m py_compile /root/psvibe-sales-bot/customer_bot/handlers.py 2>&1; echo 'EXIT_CODE:'$?");
  console.log('handlers.py compile:\n' + compHandlers.stdout);
  report += '### handlers.py Compile\n```\n' + compHandlers.stdout + '```\n\n';

  // Full ai.py content
  const aiPy = await sshExec(conn, "cat /root/psvibe-sales-bot/customer_bot/ai.py 2>&1");
  console.log('ai.py content:\n' + aiPy.stdout);
  report += '### ai.py Full Content\n```python\n' + aiPy.stdout + '```\n\n';

  // handlers.py key sections
  const handlersPy = await sshExec(conn, "cat /root/psvibe-sales-bot/customer_bot/handlers.py 2>&1");
  console.log('handlers.py content:\n' + handlersPy.stdout);
  report += '### handlers.py Full Content\n```python\n' + handlersPy.stdout + '```\n\n';

  // main.py key sections
  const mainPy = await sshExec(conn, "cat /root/psvibe-sales-bot/customer_bot/main.py 2>&1");
  console.log('main.py content:\n' + mainPy.stdout);
  report += '### main.py Full Content\n```python\n' + mainPy.stdout + '```\n\n';

  // Search for Ko VIBE persona
  const vibeSearch = await sshExec(conn, "grep -rni 'ko.vibe\\|kovibe\\|Ko VIBE\\|persona\\|system_prompt\\|SYSTEM_PROMPT' /root/psvibe-sales-bot/customer_bot/ 2>/dev/null");
  console.log('Vibe persona search:\n' + vibeSearch.stdout);
  report += '### "Ko VIBE" Persona Search\n```\n' + (vibeSearch.stdout || 'NOT FOUND') + '```\n\n';

  // Check imports
  const imports = await sshExec(conn, "head -30 /root/psvibe-sales-bot/customer_bot/ai.py 2>&1");
  console.log('ai.py imports:\n' + imports.stdout);

  conn.end();
  
  writeFileSync('/tmp/vps_investigation_full.md', report);
  console.log('\n\n=== REPORT WRITTEN TO /tmp/vps_investigation_full.md ===');
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
