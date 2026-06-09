const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

function execCmd(conn, cmd, timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, { timeout: timeoutMs }, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', d => stdout += d.toString());
      stream.stderr.on('data', d => stderr += d.toString());
      stream.on('close', () => resolve({ stdout: stdout.trim(), stderr: stderr.trim() }));
    });
  });
}

async function main() {
  const key = fs.readFileSync(KEY_PATH);
  
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({ host: '5.223.81.16', username: 'root', privateKey: key });
  });

  console.log('=== CONNECTED ===\n');

  // Get the actual MySQL root password from docker inspect
  console.log('=== Step 0: Get MySQL root password ===');
  const { stdout: rootPwd } = await execCmd(conn, 
    `docker inspect psvibe-mysql 2>/dev/null | python3 -c "import sys,json; data=json.load(sys.stdin); env=data[0]['Config']['Env']; [print(e.split('=',1)[1]) for e in env if e.startswith('MYSQL_ROOT_PASSWORD=')]" 2>/dev/null`
  );
  console.log('root password found:', rootPwd ? 'yes' : 'no');
  
  // Use the password directly
  const MYSQL = `docker exec psvibe-mysql mysql -u root '-p${rootPwd}' psvibe_api -e`;
  
  // Verify connection
  console.log('=== Verify connection ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT VERSION();" 2>&1`)).stdout);
  console.log('');

  // === STEP 1: All tables in the database ===
  console.log('=== STEP 1: All tables in psvibe_api ===');
  console.log((await execCmd(conn, `${MYSQL} "SHOW TABLES;" 2>&1`)).stdout);
  console.log('');

  // Find account/balance/finance related tables
  console.log('=== STEP 1b: Account/Balance/Finance related tables ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT TABLE_NAME, TABLE_COMMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA='psvibe_api' AND (TABLE_NAME LIKE '%acc%' OR TABLE_NAME LIKE '%bal%' OR TABLE_NAME LIKE '%financ%' OR TABLE_NAME LIKE '%wallet%' OR TABLE_NAME LIKE '%income%' OR TABLE_NAME LIKE '%expense%' OR TABLE_NAME LIKE '%cash%');" 2>&1`)).stdout);
  console.log('');

  // === STEP 2: Explore accounts table ===
  console.log('=== STEP 2a: DESCRIBE accounts ===');
  console.log((await execCmd(conn, `${MYSQL} "DESCRIBE accounts;" 2>&1`)).stdout);
  console.log('');
  
  console.log('=== STEP 2b: SELECT * FROM accounts ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT * FROM accounts ORDER BY id;" 2>&1`)).stdout);
  console.log('');

  // === STEP 3: Explore finance tables ===
  const financeTables = ['finance_advances','finance_assets','finance_opex_log','finance_payables','finance_prepaid','finance_receivables'];
  for (const tbl of financeTables) {
    console.log(`=== DESCRIBE ${tbl} ===`);
    console.log((await execCmd(conn, `${MYSQL} "DESCRIBE ${tbl};" 2>&1`)).stdout);
    console.log(`=== SELECT * FROM ${tbl} LIMIT 10 ===`);
    console.log((await execCmd(conn, `${MYSQL} "SELECT * FROM ${tbl} ORDER BY id DESC LIMIT 10;" 2>&1`)).stdout);
    console.log('');
  }

  // === STEP 4: sales_daily table ===
  console.log('=== STEP 4a: DESCRIBE sales_daily ===');
  console.log((await execCmd(conn, `${MYSQL} "DESCRIBE sales_daily;" 2>&1`)).stdout);
  console.log('');
  console.log('=== STEP 4b: sales_daily recent 10 ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT * FROM sales_daily ORDER BY id DESC LIMIT 10;" 2>&1`)).stdout);
  console.log('');

  // === STEP 5: topup_log ===
  console.log('=== STEP 5a: DESCRIBE topup_log ===');
  console.log((await execCmd(conn, `${MYSQL} "DESCRIBE topup_log;" 2>&1`)).stdout);
  console.log('');
  console.log('=== STEP 5b: topup_log summary ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT payment_method, COUNT(*) as cnt, SUM(amount) as total FROM topup_log GROUP BY payment_method;" 2>&1`)).stdout);
  console.log('');

  // === STEP 6: card_wallet & member_wallets ===
  console.log('=== STEP 6a: DESCRIBE card_wallet ===');
  console.log((await execCmd(conn, `${MYSQL} "DESCRIBE card_wallet;" 2>&1`)).stdout);
  console.log('');
  console.log('=== STEP 6b: DESCRIBE member_wallets ===');
  console.log((await execCmd(conn, `${MYSQL} "DESCRIBE member_wallets;" 2>&1`)).stdout);
  console.log('');

  // === STEP 7: Check for psvibe_dashboard database ===
  console.log('=== STEP 7: Check other databases ===');
  console.log((await execCmd(conn, `docker exec psvibe-mysql mysql -u root '-p${rootPwd}' -e "SHOW DATABASES;" 2>&1`)).stdout);
  console.log('');

  // === STEP 8: Account balance summary queries ===
  console.log('=== STEP 8: Account balance summary ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT account_type, COUNT(*) as cnt, SUM(balance) as total_balance FROM accounts GROUP BY account_type;" 2>&1`)).stdout);
  console.log('');

  console.log('=== STEP 8b: Finance opex summary ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT category, COUNT(*) as cnt, SUM(amount) as total FROM finance_opex_log GROUP BY category ORDER BY total DESC;" 2>&1`)).stdout);
  console.log('');

  console.log('=== STEP 8c: Sales daily summary ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT payment_method, COUNT(*) as cnt, SUM(net_amount) as total_net, SUM(gross_amount) as total_gross FROM sales_daily GROUP BY payment_method;" 2>&1`)).stdout);
  console.log('');

  // === STEP 9: Grep API code ===
  console.log('=== STEP 9: Dashboard API endpoints ===');
  console.log((await execCmd(conn, `grep -rn "Finance\|finance\|balance\|Balance\|account_balance\|acc.*bal\|income\|expense\|opex\|cash_flow\|cash_movement\|net_cash" /root/psvibe_api_server/dashboard_routes.py 2>/dev/null | head -30`)).stdout);
  console.log('');

  // === STEP 10: Sales bot income/expense tracking ===
  console.log('=== STEP 10: Sales bot income/expense ===');
  console.log((await execCmd(conn, `grep -rn "income\|total_income\|expense\|opex\|balance\|finance" /root/psvibe-sales-bot/bot/ --include="*.py" 2>/dev/null | head -40`)).stdout);
  console.log('');

  // === STEP 11: Check stock_in, stock_out for revenue data ===
  console.log('=== STEP 11a: DESCRIBE stock_out ===');
  console.log((await execCmd(conn, `${MYSQL} "DESCRIBE stock_out;" 2>&1`)).stdout);
  console.log('');
  console.log('=== STEP 11b: stock_out summary ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT payment_method, COUNT(*) as cnt, SUM(total) as total_revenue FROM stock_out GROUP BY payment_method;" 2>&1`)).stdout);
  console.log('');

  // === STEP 12: Get dashboard_routes.py content (finance sections) ===
  console.log('=== STEP 12: Dashboard routes finance ===');
  console.log((await execCmd(conn, `grep -n "def \|class \|@app" /root/psvibe_api_server/dashboard_routes.py 2>/dev/null | head -60`)).stdout);
  console.log('');

  // === STEP 13: Check receipts table ===
  console.log('=== STEP 13: DESCRIBE receipts ===');
  console.log((await execCmd(conn, `${MYSQL} "DESCRIBE receipts;" 2>&1`)).stdout);
  console.log('');

  console.log('=== STEP 13b: receipts summary ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT payment_method, COUNT(*) as cnt, SUM(amount) as total FROM receipts GROUP BY payment_method;" 2>&1`)).stdout);
  console.log('');
  
  console.log('=== STEP 13c: receipts recent 10 ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT * FROM receipts ORDER BY id DESC LIMIT 10;" 2>&1`)).stdout);
  console.log('');

  // === Load full DB_SCHEMA.md ===
  console.log('=== DB_SCHEMA.md (full finance section) ===');
  console.log((await execCmd(conn, `sed -n '/finance_advances/,/^### /p' /root/psvibe-sales-bot/DB_SCHEMA.md 2>/dev/null | head -200`)).stdout);
  console.log('');

  conn.end();
  console.log('=== DONE ===');
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
