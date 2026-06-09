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

  // ── Check food.py full ──
  const foodPy = await sshExec(conn, "wc -l /root/psvibe-sales-bot/bot/handlers/food.py && cat /root/psvibe-sales-bot/bot/handlers/food.py 2>/dev/null");
  console.log('=== FOOD.PY FULL ===');
  console.log(foodPy.stdout);

  // ── Check fetch_food_prices in __init__.py ──
  const fetchFoodPrices = await sshExec(conn, "grep -n -A 15 'def fetch_food_prices' /root/psvibe-sales-bot/bot/__init__.py 2>/dev/null");
  console.log('\n=== fetch_food_prices ===');
  console.log(fetchFoodPrices.stdout);
  
  // ── Check MySQL container status ──
  const mysqlContainer = await sshExec(conn, "docker ps 2>/dev/null | grep -i mysql; docker ps -a 2>/dev/null | grep -i mysql");
  console.log('\n=== MySQL container ===');
  console.log(mysqlContainer.stdout);

  // ── Create tables in MySQL (psvibe_api) ──
  const mysqlTables = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' psvibe_api -e 'SHOW TABLES;' 2>/dev/null");
  console.log('\n=== psvibe_api MySQL tables ===');
  console.log(mysqlTables.stdout);
  
  const mysqlInvTables = await sshExec(conn, "mysql -u root -p'Freedom2024#psvibe123' psvibe_api -e 'SHOW TABLES LIKE \"%inventory%\"; SHOW TABLES LIKE \"%stock%\";' 2>/dev/null");
  console.log('\n=== MySQL inventory/stock tables ===');
  console.log(mysqlInvTables.stdout);

  // ── Check SQLite food_items table ──
  const sqliteFood = await sshExec(conn, "sqlite3 /root/psvibe-sales-bot/psvibe.db '.headers on' '.mode column' 'SELECT * FROM food_items LIMIT 20;' 2>/dev/null");
  console.log('\n=== SQLite food_items ===');
  console.log(sqliteFood.stdout);

  const sqliteInv = await sshExec(conn, "sqlite3 /root/psvibe-sales-bot/psvibe.db '.headers on' '.mode column' 'SELECT * FROM inventory LIMIT 20;' 2>/dev/null");
  console.log('\n=== SQLite inventory ===');
  console.log(sqliteInv.stdout);

  const sqliteStockOut = await sshExec(conn, "sqlite3 /root/psvibe-sales-bot/psvibe.db '.headers on' '.mode column' 'SELECT * FROM stock_out LIMIT 10;' 2>/dev/null");
  console.log('\n=== SQLite stock_out ===');
  console.log(sqliteStockOut.stdout);

  // ── Check recent logs for customer bot errors ──
  const recentCustomerLogs = await sshExec(conn, "journalctl -u psvibe_customer_bot --no-pager -n 100 2>&1 | grep -i 'error\\|exception\\|traceback\\|fail\\|crash\\|gemini\\|api_key' | tail -20");
  console.log('\n=== Customer bot errors ===');
  console.log(recentCustomerLogs.stdout);

  // ── Check if AI replies are actually being called ──
  const aiCallLogs = await sshExec(conn, "journalctl -u psvibe_customer_bot --no-pager -n 200 2>&1 | grep -i 'ai_reply\\|gemini\\|search_member\\|Gemini' | tail -20");
  console.log('\n=== AI call logs ===');
  console.log(aiCallLogs.stdout);

  // Check MySQL API connectivity
  const mysqlApiCheck = await sshExec(conn, "mysql -u psvibe_user -p'PsVibe@2026_Rotated!' -h 127.0.0.1 psvibe_api -e 'SHOW TABLES;' 2>&1");
  console.log('\n=== MySQL via psvibe_user ===');
  console.log(mysqlApiCheck.stdout + mysqlApiCheck.stderr);

  conn.end();
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
