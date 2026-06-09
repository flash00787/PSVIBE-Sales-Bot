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

  // 1. Read dashboard_financial_report function
  console.log('=== dashboard_financial_report (line 1378) ===');
  const { stdout: fin } = await execCmd(conn, `sed -n '1378,1700p' /root/psvibe_api_server/dashboard_routes.py 2>/dev/null`);
  console.log(fin);
  console.log('\n=== END finance ===\n');

  // 2. Read dashboard_get_opex_summary
  console.log('=== dashboard_get_opex_summary (line 1671) ===');
  const { stdout: opexSum } = await execCmd(conn, `sed -n '1671,1800p' /root/psvibe_api_server/dashboard_routes.py 2>/dev/null`);
  console.log(opexSum);
  console.log('\n=== END opex_summary ===\n');

  // 3. Read get_dashboard_stats function
  console.log('=== get_dashboard_stats (line 16) ===');
  const { stdout: stats } = await execCmd(conn, `sed -n '16,100p' /root/psvibe_api_server/dashboard_routes.py 2>/dev/null`);
  console.log(stats);
  console.log('\n=== END stats ===\n');

  // 4. Check app.py for finance routes
  console.log('=== Grep app.py for finance/balance routes ===');
  const { stdout: appGrep } = await execCmd(conn, `grep -n "finance\|balance\|accounts\|cash_movement\|opex" /root/psvibe_api_server/app.py 2>/dev/null | head -30`);
  console.log(appGrep || '(no matches)');
  console.log('');

  // 5. Check for any accounts/cash routes in app.py
  console.log('=== Grep app.py for cash/account routes ===');
  const { stdout: appGrep2 } = await execCmd(conn, `grep -n "cash_movement\|cash_transfer\|accounts\|/api/accounts\|@app" /root/psvibe_api_server/app.py 2>/dev/null | head -40`);
  console.log(appGrep2 || '(no matches)');
  console.log('');

  // 6. Read cash_movement/accounts routes from dashboard_routes.py
  console.log('=== Grep dashboard_routes.py for cash/account routes ===');
  const { stdout: dashGrep } = await execCmd(conn, `grep -n "cash_movement\|cash_transfer\|account\|/api/" /root/psvibe_api_server/dashboard_routes.py 2>/dev/null | head -40`);
  console.log(dashGrep || '(no matches)');
  console.log('');

  // 7. Get the full list of routes from dashboard_routes.py
  console.log('=== All @app.route in dashboard_routes.py ===');
  const { stdout: routes } = await execCmd(conn, `grep -n "@app.route\|@router" /root/psvibe_api_server/dashboard_routes.py 2>/dev/null | head -50`);
  console.log(routes || '(no matches)');
  console.log('');

  // 8. Check app.py and dashboard_routes.py for imports
  console.log('=== dashboard_routes.py imports ===');
  const { stdout: imports } = await execCmd(conn, `head -16 /root/psvibe_api_server/dashboard_routes.py 2>/dev/null`);
  console.log(imports);
  console.log('');

  // 9. Check app.py for any register/finance blueprint
  console.log('=== app.py router includes ===');
  const { stdout: appIncludes } = await execCmd(conn, `grep -n "include_router\|APIRouter\|dashboard_routes\|finance_routes\|from" /root/psvibe_api_server/app.py 2>/dev/null | head -30`);
  console.log(appIncludes || '(no matches)');
  console.log('');

  // 10. Check for any separate finance_routes.py
  console.log('=== Check for finance_routes.py ===');
  const { stdout: finRoutes } = await execCmd(conn, `ls -la /root/psvibe_api_server/finance_routes.py 2>/dev/null; cat /root/psvibe_api_server/finance_routes.py 2>/dev/null | head -40`);
  console.log(finRoutes || '(no finance_routes.py)');
  console.log('');

  // 11. Get full dashboard_get_opex function
  console.log('=== dashboard_get_opex (line 1587) ===');
  const { stdout: opexGet } = await execCmd(conn, `sed -n '1587,1670p' /root/psvibe_api_server/dashboard_routes.py 2>/dev/null`);
  console.log(opexGet);
  console.log('');

  // 12. Check sales_bot api_client.py for any finance/balance calls
  console.log('=== API client finance references ===');
  const { stdout: apiClient } = await execCmd(conn, `grep -n "finance\|balance\|accounts\|opex\|cash" /root/psvibe-sales-bot/bot/api_client.py 2>/dev/null | head -30`);
  console.log(apiClient || '(no matches)');
  console.log('');

  // 13. Check app.py in sales bot for balance display
  console.log('=== Sales bot app.py balance references ===');
  const { stdout: botApp } = await execCmd(conn, `grep -n "balance\|Balance\|income\|Income\|expense\|Expense\|finance\|Finance" /root/psvibe-sales-bot/bot/app.py 2>/dev/null | head -20`);
  console.log(botApp || '(no matches)');
  console.log('');

  // 14. Check __init__.py for balance
  console.log('=== Sales bot __init__.py balance references ===');
  const { stdout: botInit } = await execCmd(conn, `grep -n "balance\|Balance\|income\|Income\|expense\|Expense\|finance\|Finance\|accounts\|Accounts" /root/psvibe-sales-bot/bot/__init__.py 2>/dev/null | head -20`);
  console.log(botInit || '(no matches)');
  console.log('');

  // 15. Check the full financial_report function more carefully
  console.log('=== dashboard_financial_report (full, from 1378) ===');
  const { stdout: fullFin } = await execCmd(conn, `python3 -c "
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    content = f.read()
# Find all function defs
import re
funcs = list(re.finditer(r'^(async def |def )(\w+)', content, re.MULTILINE))
# Find financial_report
for i, m in enumerate(funcs):
    if 'financial_report' in m.group(2):
        start = m.start()
        end = funcs[i+1].start() if i+1 < len(funcs) else len(content)
        # Go back to find @app or @router decorator
        decorator_start = content.rfind('@', max(0, m.start()-500), m.start())
        snippet = content[decorator_start if decorator_start > 0 else start:end]
        print(snippet)
        break
" 2>&1`).stdout;
  console.log(fullFin || '(not found)');
  console.log('');

  // 16. Check get_dashboard_stats
  console.log('=== get_dashboard_stats (full) ===');
  const { stdout: fullStats } = await execCmd(conn, `python3 -c "
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    content = f.read()
import re
funcs = list(re.finditer(r'^(async def |def )(\w+)', content, re.MULTILINE))
for i, m in enumerate(funcs):
    if 'get_dashboard_stats' in m.group(2):
        start = m.start()
        end = funcs[i+1].start() if i+1 < len(funcs) else len(content)
        decorator_start = content.rfind('@', max(0, m.start()-500), m.start())
        snippet = content[decorator_start if decorator_start > 0 else start:end]
        print(snippet)
        break
" 2>&1`).stdout;
  console.log(fullStats || '(not found)');
  console.log('');

  // 17. Get revenue trend function
  console.log('=== get_revenue_trend (full) ===');
  const { stdout: revTrend } = await execCmd(conn, `python3 -c "
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    content = f.read()
import re
funcs = list(re.finditer(r'^(async def |def )(\w+)', content, re.MULTILINE))
for i, m in enumerate(funcs):
    if 'get_revenue_trend' in m.group(2):
        start = m.start()
        end = funcs[i+1].start() if i+1 < len(funcs) else len(content)
        decorator_start = content.rfind('@', max(0, m.start()-500), m.start())
        snippet = content[decorator_start if decorator_start > 0 else start:end]
        print(snippet)
        break
" 2>&1`).stdout;
  console.log(revTrend || '(not found)');
  console.log('');

  // 18. Check what app.py exposes for finance
  console.log('=== Grep app.py for all route decorators ===');
  const { stdout: allRoutes } = await execCmd(conn, `grep -n "@app\.\|@router\." /root/psvibe_api_server/app.py 2>/dev/null | head -60`);
  console.log(allRoutes || '(no matches)');
  console.log('');

  // 19. Check if there's a separate cash/accounts route file
  console.log('=== Search for cash/accounts route files ===');
  const { stdout: cashRoutes } = await execCmd(conn, `find /root/psvibe_api_server -name "*cash*" -o -name "*account*" -o -name "*finance*" 2>/dev/null`);
  console.log(cashRoutes || '(no files found)');
  console.log('');

  // 20. Get the opex create route
  console.log('=== dashboard_create_opex (line 1646) ===');
  const { stdout: createOpex } = await execCmd(conn, `python3 -c "
with open('/root/psvibe_api_server/dashboard_routes.py') as f:
    content = f.read()
import re
funcs = list(re.finditer(r'^(async def |def )(\w+)', content, re.MULTILINE))
for i, m in enumerate(funcs):
    if 'dashboard_create_opex' in m.group(2):
        start = m.start()
        end = funcs[i+1].start() if i+1 < len(funcs) else min(len(content), start+2000)
        decorator_start = content.rfind('@', max(0, m.start()-500), m.start())
        snippet = content[decorator_start if decorator_start > 0 else start:end]
        print(snippet[:2000])
        break
" 2>&1`).stdout;
  console.log(createOpex || '(not found)');
  console.log('');

  conn.end();
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
