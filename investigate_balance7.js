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

  const { stdout: rootPwd } = await execCmd(conn, 
    `docker inspect psvibe-mysql 2>/dev/null | python3 -c "import sys,json; data=json.load(sys.stdin); env=data[0]['Config']['Env']; [print(e.split('=',1)[1]) for e in env if e.startswith('MYSQL_ROOT_PASSWORD=')]" 2>/dev/null`
  );
  const MYSQL = `docker exec psvibe-mysql mysql -u root '-p${rootPwd}' psvibe_api -e`;

  // 1. revenue_trend function
  console.log('=== get_revenue_trend ===');
  const { stdout: revTrend } = await execCmd(conn, `sed -n '131,200p' /root/psvibe_api_server/dashboard_routes.py`);
  console.log(revTrend);
  console.log('');

  // 2. Check constants.py for finance stuff
  console.log('=== Sales bot constants.py ===');
  const { stdout: consts } = await execCmd(conn, `cat /root/psvibe-sales-bot/bot/constants.py`);
  console.log(consts || '(empty)');
  console.log('');

  // 3. Check member_wallets table structure
  console.log('=== member_wallets ===');
  const { stdout: mw } = await execCmd(conn, `${MYSQL} "DESCRIBE member_wallets; SELECT * FROM member_wallets LIMIT 10;"`);
  console.log(mw);
  console.log('');

  // 4. Check members table
  console.log('=== members (first 5) ===');
  const { stdout: members } = await execCmd(conn, `${MYSQL} "DESCRIBE members; SELECT * FROM members LIMIT 5;"`);
  console.log(members);
  console.log('');

  // 5. Check total sales for all time
  console.log('=== Sales summary all time ===');
  const { stdout: salesAll } = await execCmd(conn, `${MYSQL} "SELECT COUNT(*) as total_txns, SUM(net) as total_net, SUM(gross) as total_gross FROM sales_daily;"`);
  console.log(salesAll);
  console.log('');

  // 6. Check opex/opex merge/finance_opex_log summary
  console.log('=== opex total ===');
  const { stdout: opexTotal } = await execCmd(conn, `${MYSQL} "SELECT COUNT(*) as cnt, SUM(amount) as total FROM opex;"`);
  console.log(opexTotal);
  console.log('');

  // 7. Check finance_opex_log total 
  console.log('=== finance_opex_log total ===');
  const { stdout: finOpex } = await execCmd(conn, `${MYSQL} "SELECT COUNT(*) as cnt, SUM(amount) as total FROM finance_opex_log;"`);
  console.log(finOpex);
  console.log('');

  // 8. Check if there's any code manually syncing accounts table
  console.log('=== Grep for accounts balance updates ===');
  const { stdout: acctUpdate } = await execCmd(conn, `grep -rn "UPDATE.*accounts\|INSERT.*accounts\|accounts.*balance" /root/psvibe_api_server/ /root/psvibe-sales-bot/ --include="*.py" 2>/dev/null | grep -v "__pycache__\|.bak\|.git" | head -20`);
  console.log(acctUpdate || '(none)');
  console.log('');

  // 9. Check report_generator.py in sales bot
  console.log('=== Sales bot report_generator.py finance references ===');
  const { stdout: repGen } = await execCmd(conn, `grep -n "finance\|income\|expense\|balance\|opex\|sales\|revenue\|chart\|daily" /root/psvibe-sales-bot/bot/report_generator.py 2>/dev/null | head -30`);
  console.log(repGen || '(none)');
  console.log('');

  // 10. Check how sales are recorded (app.py in sales bot)
  console.log('=== Sales bot: sales recording ===');
  const { stdout: salesRec } = await execCmd(conn, `grep -n "sales_daily\|INSERT.*sales\|record.*sale\|save.*sale\|create.*sale" /root/psvibe-sales-bot/bot/app.py 2>/dev/null | head -20`);
  console.log(salesRec || '(none)');
  console.log('');

  // 11. Check analytics.py for balance
  console.log('=== API analytics.py finance references ===');
  const { stdout: analytics } = await execCmd(conn, `grep -n "finance\|balance\|income\|expense\|opex\|revenue" /root/psvibe_api_server/analytics.py 2>/dev/null | head -30`);
  console.log(analytics || '(none)');
  console.log('');

  // 12. Check the dashboard-dist (frontend) for any balance display
  console.log('=== Dashboard frontend files ===');
  const { stdout: dashDist } = await execCmd(conn, `ls -la /root/psvibe_api_server/dashboard-dist/ 2>/dev/null`);
  console.log(dashDist);
  console.log('');
  const { stdout: dashIndex } = await execCmd(conn, `grep -rn "balance\|Balance\|finance\|Finance\|income\|Income\|expense\|Expense" /root/psvibe_api_server/dashboard-dist/ --include="*.html" --include="*.js" 2>/dev/null | head -30`);
  console.log(dashIndex || '(none)');
  console.log('');

  // 13. Check if any gsheet syncs income data
  console.log('=== Google Sheets sync ===');
  const { stdout: gsheet } = await execCmd(conn, `grep -rn "income\|opex\|finance\|expense\|balance" /root/psvibe_api_server/gsheet_to_mysql.py /root/psvibe_api_server/analytics_sync.py 2>/dev/null | head -30`);
  console.log(gsheet || '(none)');
  console.log('');

  // 14. Check what Google Sheets are synced
  console.log('=== Google Sheets sheet names in sync ===');
  const { stdout: syncSheets } = await execCmd(conn, `grep -rn "SHEET\|sheet_name\|'Sheet'" /root/psvibe_api_server/gsheet_to_mysql.py 2>/dev/null | head -30`);
  console.log(syncSheets || '(none)');
  console.log('');

  conn.end();
  console.log('\n=== DONE ===');
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
