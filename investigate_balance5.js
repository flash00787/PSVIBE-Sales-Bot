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

  const { stdout: rootPwd } = await execCmd(conn, 
    `docker inspect psvibe-mysql 2>/dev/null | python3 -c "import sys,json; data=json.load(sys.stdin); env=data[0]['Config']['Env']; [print(e.split('=',1)[1]) for e in env if e.startswith('MYSQL_ROOT_PASSWORD=')]" 2>/dev/null`
  );
  const MYSQL = `docker exec psvibe-mysql mysql -u root '-p${rootPwd}' psvibe_api -e`;

  // 1. cash_movements table
  console.log('=== cash_movements DESCRIBE ===');
  console.log((await execCmd(conn, `${MYSQL} "DESCRIBE cash_movements;" 2>&1`)).stdout);
  console.log('\n=== cash_movements all rows ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT * FROM cash_movements ORDER BY id;" 2>&1`)).stdout);
  console.log('');

  // 2. cash_transfers table
  console.log('=== cash_transfers DESCRIBE ===');
  console.log((await execCmd(conn, `${MYSQL} "DESCRIBE cash_transfers;" 2>&1`)).stdout);
  console.log('\n=== cash_transfers all rows ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT * FROM cash_transfers ORDER BY id;" 2>&1`)).stdout);
  console.log('');

  // 3. opex table
  console.log('=== opex DESCRIBE ===');
  console.log((await execCmd(conn, `${MYSQL} "DESCRIBE opex;" 2>&1`)).stdout);
  console.log('\n=== opex all rows ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT * FROM opex ORDER BY id;" 2>&1`)).stdout);
  console.log('');

  // 4. Fix sales_daily summary (correct column name is net, not net_amount)
  console.log('=== sales_daily: payment method summary ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT payment_method, COUNT(*) as cnt, SUM(net) as total_net, SUM(gross) as total_gross, SUM(discount) as total_discount FROM sales_daily GROUP BY payment_method;" 2>&1`)).stdout);
  console.log('\n=== sales_daily: date summary ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT sale_date, COUNT(*) as cnt, SUM(net) as total_net FROM sales_daily GROUP BY sale_date ORDER BY sale_date DESC LIMIT 10;" 2>&1`)).stdout);
  console.log('');

  // 5. Check for income_by_acct or similar table/views
  console.log('=== Check for views ===');
  console.log((await execCmd(conn, `${MYSQL} "SHOW FULL TABLES WHERE TABLE_TYPE='VIEW';" 2>&1`)).stdout);
  console.log('');

  // 6. stock_out correct summary
  console.log('=== stock_out summary ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT item_name, COUNT(*) as cnt, SUM(total) as total_revenue FROM stock_out GROUP BY item_name ORDER BY total_revenue DESC LIMIT 10;" 2>&1`)).stdout);
  console.log('\n=== stock_out recent ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT * FROM stock_out ORDER BY id DESC LIMIT 10;" 2>&1`)).stdout);
  console.log('');

  // 7. member_wallets summary
  console.log('=== member_wallets summary ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT COUNT(*) as total_members, SUM(balance_mins) as total_bal_mins, SUM(total_spend) as total_spend FROM member_wallets;" 2>&1`)).stdout);
  console.log('');

  // 8. card_wallet summary
  console.log('=== card_wallet summary ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT COUNT(*) as cnt, SUM(balance_mins) as total_mins, SUM(total_spend) as total_spend FROM card_wallet;" 2>&1`)).stdout);
  console.log('');

  // 9. API server routes - look for all route files
  console.log('=== API server file listing ===');
  console.log((await execCmd(conn, `ls -la /root/psvibe_api_server/ 2>/dev/null`)).stdout);
  console.log('');

  // 10. Grep deeply for finance, balance, income, expense in API
  console.log('=== Grep API for finance/balance/income/expense ===');
  console.log((await execCmd(conn, `grep -rn "finance\|balance\|Balance\|income\|Income\|expense\|Expense\|opex\|Opex\|cash_movement\|Cash" /root/psvibe_api_server/ --include="*.py" 2>/dev/null | grep -v "__pycache__\|.bak\|.backup" | head -60`)).stdout);
  console.log('');

  // 11. Grep sales bot more broadly
  console.log('=== Grep sales bot for finance/balance ===');
  console.log((await execCmd(conn, `grep -rn "finance\|balance\|income\|expense\|opex\|accounts" /root/psvibe-sales-bot/bot/ --include="*.py" 2>/dev/null | head -60`)).stdout);
  console.log('');
  console.log('=== Grep sales bot customer_bot ===');
  console.log((await execCmd(conn, `grep -rn "finance\|balance\|income\|expense\|opex\|accounts" /root/psvibe-sales-bot/customer_bot/ --include="*.py" 2>/dev/null | head -40`)).stdout);
  console.log('');

  // 12. Check API server main file
  console.log('=== API server main.py ===');
  console.log((await execCmd(conn, `head -100 /root/psvibe_api_server/main.py 2>/dev/null`)).stdout);
  console.log('');

  // 13. finance_opex_log with payment_method or account
  console.log('=== finance_opex_log: check for account/payment columns ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT * FROM finance_opex_log ORDER BY id DESC LIMIT 5;" 2>&1`)).stdout);
  console.log('\n=== finance_opex_log date summary ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT date, COUNT(*) as cnt, SUM(amount) as total FROM finance_opex_log GROUP BY date ORDER BY date DESC LIMIT 15;" 2>&1`)).stdout);
  console.log('');

  // 14. Check if any code writes to accounts table
  console.log('=== Search for accounts table writes ===');
  console.log((await execCmd(conn, `grep -rn "INSERT.*accounts\|UPDATE.*accounts\|accounts.*SET\|'accounts'" /root/psvibe_api_server/ /root/psvibe-sales-bot/ --include="*.py" 2>/dev/null | grep -v "__pycache__\|.bak\|.git" | head -20`)).stdout);
  console.log('');

  // 15. Full DB_SCHEMA accounts section
  console.log('=== DB_SCHEMA accounts section ===');
  console.log((await execCmd(conn, `sed -n '/^### .accounts.$/,/^---$/p' /root/psvibe-sales-bot/DB_SCHEMA.md 2>/dev/null | head -40`)).stdout);
  console.log('');

  // 16. Check sales bot for Google Sheets sync (could explain psvibe_dashboard names)
  console.log('=== Sales bot Sheets integration ===');
  console.log((await execCmd(conn, `grep -rn "sheet\|Sheet\|google\|spreadsheet" /root/psvibe-sales-bot/bot/app.py 2>/dev/null | head -20`)).stdout);
  console.log('');
  console.log((await execCmd(conn, `grep -rn "income_by_acct\|WALLET_SHEET\|WALLET\|wallet" /root/psvibe-sales-bot/ --include="*.py" -r 2>/dev/null | head -20`)).stdout);
  console.log('');

  // 17. accounts table - who updates it?
  console.log('=== Check accounts updated_at timing ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT account_name, account_type, balance, updated_at FROM accounts ORDER BY account_name;" 2>&1`)).stdout);
  console.log('');

  // 18. How many rows in cash_movements?
  console.log('=== cash_movements count ===');
  console.log((await execCmd(conn, `${MYSQL} "SELECT COUNT(*) FROM cash_movements;" 2>&1`)).stdout);
  console.log('');

  // 19. Check API server for dashboard route functions
  console.log('=== API dashboard_routes.py function list ===');
  console.log((await execCmd(conn, `python3 -c "
import ast, sys
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    tree = ast.parse(f.read())
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        print(f'{node.name} (line {node.lineno})')
" 2>&1 | head -40`)).stdout);
  console.log('');

  // 20. Check for Google Sheets income tracking (WALLET_SHEET)
  console.log('=== Grep for Google Sheets wallet/income ===');
  console.log((await execCmd(conn, `grep -rn "WALLET_SHEET\|income\|Income\|opex\|Opex" /root/psvibe-sales-bot/bot/api_client.py 2>/dev/null | head -30`)).stdout);
  console.log('');

  conn.end();
  console.log('=== DONE ===');
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
