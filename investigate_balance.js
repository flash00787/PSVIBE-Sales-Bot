const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
const HOST = '5.223.81.16';
const USER = 'root';
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

async function runSql(conn, query) {
  const sql = query.replace(/\n/g, ' ').replace(/"/g, '\\"');
  const fullCmd = `mysql --default-character-set=utf8mb4 -e "${sql}"`;
  const { stdout, stderr } = await execCmd(conn, fullCmd, 60000);
  if (stderr && !stderr.includes('Warning')) console.log('STDERR:', stderr);
  return stdout;
}

async function main() {
  const key = fs.readFileSync(KEY_PATH);
  
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({ host: HOST, username: USER, privateKey: key });
  });

  console.log('=== CONNECTED TO VPS ===\n');

  // === STEP 1: Check account/balance tables ===
  console.log('=== STEP 1: Account/Balance Tables ===');
  console.log(await runSql(conn, `
    SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_COMMENT 
    FROM information_schema.TABLES 
    WHERE TABLE_SCHEMA IN ('psvibe', 'psvibe_dashboard') 
    AND (TABLE_NAME LIKE '%acc%' OR TABLE_NAME LIKE '%bal%' OR TABLE_NAME LIKE '%financ%' OR TABLE_NAME LIKE '%wallet%' OR TABLE_NAME LIKE '%income%' OR TABLE_NAME LIKE '%expense%' OR TABLE_NAME LIKE '%cash%');
  `));
  console.log('');

  // === STEP 1b: All tables in psvibe_dashboard ===
  console.log('=== STEP 1b: All psvibe_dashboard tables ===');
  console.log(await runSql(conn, `
    SELECT TABLE_NAME, TABLE_COMMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'psvibe_dashboard';
  `));
  console.log('');

  // === STEP 2: income_by_acct ===
  console.log('=== STEP 2a: DESCRIBE income_by_acct ===');
  console.log(await runSql(conn, `DESCRIBE psvibe_dashboard.income_by_acct;`));
  console.log('\n=== STEP 2b: SELECT * income_by_acct ===');
  console.log(await runSql(conn, `SELECT * FROM psvibe_dashboard.income_by_acct;`));
  console.log('');

  // === STEP 2c: opex_expenses ===
  console.log('=== STEP 2c: DESCRIBE opex_expenses ===');
  console.log(await runSql(conn, `DESCRIBE psvibe_dashboard.opex_expenses;`));
  console.log('\n=== STEP 2d: opex_expenses by payment_method ===');
  console.log(await runSql(conn, `SELECT payment_method, COUNT(*) as cnt, SUM(amount) as total FROM psvibe_dashboard.opex_expenses GROUP BY payment_method;`));
  console.log('\n=== STEP 2e: opex_expenses all data ===');
  console.log(await runSql(conn, `SELECT * FROM psvibe_dashboard.opex_expenses ORDER BY created_at DESC LIMIT 30;`));
  console.log('');

  // === STEP 2f: cash_movements ===
  console.log('=== STEP 2f: DESCRIBE cash_movements ===');
  console.log(await runSql(conn, `DESCRIBE psvibe_dashboard.cash_movements;`));
  console.log('\n=== STEP 2g: cash_movements ORDER BY id DESC LIMIT 20 ===');
  console.log(await runSql(conn, `SELECT * FROM psvibe_dashboard.cash_movements ORDER BY id DESC LIMIT 20;`));
  console.log('');

  // === STEP 2h: psvibe.accounts ===
  console.log('=== STEP 2h: DESCRIBE psvibe.accounts ===');
  try {
    console.log(await runSql(conn, `DESCRIBE psvibe.accounts;`));
    console.log('\n=== STEP 2i: SELECT * psvibe.accounts LIMIT 30 ===');
    console.log(await runSql(conn, `SELECT * FROM psvibe.accounts LIMIT 30;`));
  } catch(e) {
    console.log('psvibe.accounts does not exist or error:', e.message);
  }
  console.log('');

  // === STEP 3: All tables in psvibe ===
  console.log('=== STEP 3a: SHOW TABLES FROM psvibe ===');
  console.log(await runSql(conn, `SHOW TABLES FROM psvibe;`));
  console.log('');

  // === STEP 3b: Check sales tables ===
  console.log('=== STEP 3b: Look for sales/transaction tables ===');
  // Try common names
  for (const tbl of ['sales_records', 'sales', 'transactions', 'orders', 'deposits', 'payments']) {
    try {
      const desc = await runSql(conn, `DESCRIBE psvibe.${tbl};`);
      if (desc) {
        console.log(`\n--- psvibe.${tbl} ---`);
        console.log(desc);
      }
    } catch(e) {
      // table doesn't exist
    }
  }
  console.log('');

  // === STEP 3c: Try psvibe_dashboard sales tables too ===
  console.log('=== STEP 3c: Check psvibe_dashboard sales/transaction tables ===');
  for (const tbl of ['sales_records', 'sales', 'transactions', 'orders', 'deposits', 'payments', 'revenue']) {
    try {
      const desc = await runSql(conn, `DESCRIBE psvibe_dashboard.${tbl};`);
      if (desc) {
        console.log(`\n--- psvibe_dashboard.${tbl} ---`);
        console.log(desc);
        const count = await runSql(conn, `SELECT COUNT(*) as cnt FROM psvibe_dashboard.${tbl};`);
        console.log(`Row count: ${count}`);
      }
    } catch(e) {
      // table doesn't exist
    }
  }
  console.log('');

  // === STEP 4: grep dashboard API endpoints ===
  console.log('=== STEP 4: Dashboard API finance/balance endpoints ===');
  const { stdout: api1 } = await execCmd(conn, `grep -rn "Finance\|finance\|balance\|Balance\|account_balance\|acc.*bal" /root/psvibe_api_server/dashboard_routes.py 2>/dev/null | head -20`);
  console.log(api1 || '(no matches or file not found)');
  console.log('');

  // === STEP 4b: Also check all Python files in API ===
  console.log('=== STEP 4b: All API finance references ===');
  const { stdout: api2 } = await execCmd(conn, `grep -rn "Finance\|finance\|balance\|Balance" /root/psvibe_api_server/ --include="*.py" 2>/dev/null | head -30`);
  console.log(api2 || '(no matches)');
  console.log('');

  // === STEP 5: cash_movements full ===
  console.log('=== STEP 5: cash_movements all data ORDER BY created_at DESC ===');
  console.log(await runSql(conn, `SELECT * FROM psvibe_dashboard.cash_movements ORDER BY created_at DESC;`));
  console.log('');

  // === STEP 5b: cash_movements summary ===
  console.log('=== STEP 5b: cash_movements summary ===');
  console.log(await runSql(conn, `SELECT type, COUNT(*) as cnt, SUM(amount) as total FROM psvibe_dashboard.cash_movements GROUP BY type;`));
  console.log('');

  // === STEP 6: wallet bot balance references ===
  console.log('=== STEP 6: Wallet bot balance references ===');
  const { stdout: wallet1 } = await execCmd(conn, `grep -rn "balance\|Balance\|total_income\|total_expense" /root/yyo-personal-wallet/*.py 2>/dev/null | head -20`);
  console.log(wallet1 || '(no matches or file not found)');
  console.log('');

  // === STEP 6b: List wallet bot files ===
  console.log('=== STEP 6b: Wallet bot file listing ===');
  const { stdout: walletFiles } = await execCmd(conn, `ls -la /root/yyo-personal-wallet/ 2>/dev/null || echo "(directory not found)"`);
  console.log(walletFiles);
  console.log('');

  // === STEP 7: Sales bot income references ===
  console.log('=== STEP 7: Sales bot income references ===');
  const { stdout: sales1 } = await execCmd(conn, `grep -rn "income_by_acct\|total_income\|insert.*income\|income" /root/psvibe-sales-bot/*.py 2>/dev/null | head -20`);
  console.log(sales1 || '(no matches or file not found)');
  console.log('');

  // === STEP 7b: List sales bot files ===
  console.log('=== STEP 7b: Sales bot file listing ===');
  const { stdout: salesFiles } = await execCmd(conn, `ls -la /root/psvibe-sales-bot/ 2>/dev/null || echo "(directory not found)"`);
  console.log(salesFiles);
  console.log('');

  // === BONUS: Check income_by_acct summary ===
  console.log('=== BONUS: income_by_acct summary ===');
  console.log(await runSql(conn, `SELECT account_name, SUM(received) as total_received FROM psvibe_dashboard.income_by_acct GROUP BY account_name;`));
  console.log('');

  // === BONUS: Check for any view or stored procedure re:balance ===
  console.log('=== BONUS: Views & routines ===');
  console.log(await runSql(conn, `
    SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE 
    FROM information_schema.TABLES 
    WHERE TABLE_SCHEMA IN ('psvibe', 'psvibe_dashboard') 
    AND TABLE_TYPE = 'VIEW';
  `));
  console.log('');

  conn.end();
  console.log('=== DONE ===');
}

main().catch(e => {
  console.error('ERROR:', e.message);
  process.exit(1);
});
