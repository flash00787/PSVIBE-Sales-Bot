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
  console.log('=== FINAL DETAILS ===\n');

  let extra = '';

  // ── 1: Check GEMINI_API_KEY in secrets.env ──
  const secrets = await sshExec(conn, "cat /etc/psvibe/secrets.env 2>/dev/null");
  console.log('secrets.env:\n' + secrets.stdout);
  extra += '### secrets.env\n```\n' + (secrets.stdout || 'FILE NOT FOUND') + '```\n\n';

  // ── 2: Check how food.py fetches stock ──
  const foodPy = await sshExec(conn, "cat /root/psvibe-sales-bot/bot/handlers/food.py 2>/dev/null | head -120");
  console.log('food.py (head 120):\n' + foodPy.stdout);
  extra += '### food.py stock\n```\n' + foodPy.stdout + '```\n\n';

  // ── 3: Check full step_sale_confirm (lines around 1007-1160) ──
  const salesConfirmFull = await sshExec(conn, "sed -n '1007,1200p' /root/psvibe-sales-bot/bot/handlers/sales.py 2>/dev/null");
  console.log('step_sale_confirm full (lines 1007-1200):\n' + salesConfirmFull.stdout);
  extra += '### step_sale_confirm lines 1007-1200\n```\n' + salesConfirmFull.stdout + '```\n\n';

  // ── 4: Check how Setting sheet is used ──
  const settingSheetUsage = await sshExec(conn, "grep -rn 'Setting\\|setting_sh\\|food_prices\\|fetch_food_prices' /root/psvibe-sales-bot/bot/__init__.py 2>/dev/null | head -20");
  console.log('Setting sheet refs in init:\n' + settingSheetUsage.stdout);
  extra += '### Setting sheet/food prices\n```\n' + settingSheetUsage.stdout + '```\n\n';

  // ── 5: Check API server mysql_db.py ──
  const mysqlDbPy = await sshExec(conn, "ls -la /root/psvibe_api_server/mysql_db.py 2>/dev/null; cat /root/psvibe_api_server/mysql_db.py 2>/dev/null");
  console.log('mysql_db.py:\n' + mysqlDbPy.stdout);
  extra += '### mysql_db.py (API server)\n```\n' + (mysqlDbPy.stdout || 'NOT FOUND') + '```\n\n';

  // ── 6: Check if SQLite DB exists and food_items table ──
  const sqliteCheck = await sshExec(conn, "ls -la /root/psvibe-sales-bot/psvibe.db 2>/dev/null");
  console.log('SQLite DB:\n' + sqliteCheck.stdout);
  extra += '### SQLite DB existence\n```\n' + (sqliteCheck.stdout || 'NOT FOUND') + '```\n\n';

  const sqliteTables = await sshExec(conn, "sqlite3 /root/psvibe-sales-bot/psvibe.db '.tables' 2>/dev/null");
  console.log('SQLite tables:\n' + sqliteTables.stdout);
  extra += '### SQLite tables\n```\n' + (sqliteTables.stdout || 'DB not accessible') + '```\n\n';

  if (sqliteTables.stdout) {
    const foodItemsSqlite = await sshExec(conn, "sqlite3 /root/psvibe-sales-bot/psvibe.db '.headers on' 'SELECT * FROM food_items LIMIT 20;' 2>/dev/null");
    console.log('SQLite food_items:\n' + foodItemsSqlite.stdout);
    extra += '### SQLite food_items\n```\n' + foodItemsSqlite.stdout + '```\n\n';

    const inventorySqlite = await sshExec(conn, "sqlite3 /root/psvibe-sales-bot/psvibe.db '.headers on' 'SELECT * FROM inventory LIMIT 20;' 2>/dev/null");
    console.log('SQLite inventory:\n' + inventorySqlite.stdout);
    extra += '### SQLite inventory\n```\n' + inventorySqlite.stdout + '```\n\n';

    const stockOutSQLite = await sshExec(conn, "sqlite3 /root/psvibe-sales-bot/psvibe.db '.headers on' 'SELECT * FROM stock_out LIMIT 10;' 2>/dev/null");
    console.log('SQLite stock_out:\n' + stockOutSQLite.stdout);
    extra += '### SQLite stock_out\n```\n' + stockOutSQLite.stdout + '```\n\n';
  }

  // Check api_client.py for how bot connects
  const apiClient = await sshExec(conn, "cat /root/psvibe-sales-bot/bot/api_client.py 2>/dev/null | head -80");
  console.log('api_client.py:\n' + apiClient.stdout);
  extra += '### api_client.py\n```\n' + apiClient.stdout + '```\n\n';

  // Check the Receipt endpoint in app.py
  const receiptEndpoint = await sshExec(conn, "grep -n -A 30 'api/receipt' /root/psvibe_api_server/app.py 2>/dev/null | head -40");
  console.log('Receipt API endpoint:\n' + receiptEndpoint.stdout);
  extra += '### Receipt API endpoint\n```\n' + receiptEndpoint.stdout + '```\n\n';

  // Check if the secrets file has all needed vars
  const secretsExtra = await sshExec(conn, "grep -v '^#' /etc/psvibe/secrets.env 2>/dev/null | grep -v '^$' | head -20");
  console.log('secrets.env vars:\n' + secretsExtra.stdout);

  // Check the actual food.py completely for stock handling
  const foodPyFullStock = await sshExec(conn, "grep -n 'stock\\|inventory\\|food_prices\\|prices\\|menu' /root/psvibe-sales-bot/bot/handlers/food.py 2>/dev/null | head -30");
  console.log('food.py ALL stock/inventory references:\n' + foodPyFullStock.stdout);
  extra += '### food.py stock references (all)\n```\n' + foodPyFullStock.stdout + '```\n\n';

  // Check if there's an `inv_sh` etc. in __init__.py
  const initInvRefs = await sshExec(conn, "grep -n 'inv_sh\\|stock_sh\\|food_sh\\|setting\\|setting_sh\\|Setting' /root/psvibe-sales-bot/bot/__init__.py 2>/dev/null | head -20");
  console.log('Sheet refs in __init__:\n' + initInvRefs.stdout);
  extra += '### Sheet refs in __init__.py\n```\n' + initInvRefs.stdout + '```\n\n';

  writeFileSync('/tmp/vps_final_details.md', extra);
  conn.end();
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
