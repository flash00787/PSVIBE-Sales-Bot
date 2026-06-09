const { Client } = require('ssh2');
const fs = require('fs');

const host = '167.71.196.120';
const BOT_DIR = '/root/Sales-Tele-Bot_refactored';

function execCmd(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', d => stdout += d.toString());
      stream.stderr.on('data', d => stderr += d.toString());
      stream.on('close', code => resolve({ stdout: stdout.trim(), stderr: stderr.trim(), code }));
    });
  });
}

(async () => {
  const conn = new Client();
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve).on('error', reject);
    conn.connect({
      host, username: 'root',
      privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8')
    });
  });

  // Get all handler states (direct returns + show_* calls that return states indirectly)
  const r1 = await execCmd(conn, `cd ${BOT_DIR} && grep -rn "return [A-Z_]*$" bot/handlers/ --include="*.py" | grep -oP "return \\K[A-Z_]+" | sort -u`);
  const r1b = await execCmd(conn, `cd ${BOT_DIR} && grep -rn "return await show_" bot/handlers/ --include="*.py" | grep -oP "show_\\w+" | sort -u`);

  // Get app states
  const r2 = await execCmd(conn, `cd ${BOT_DIR} && python3 -c "
import re
with open('bot/app.py') as f:
    content = f.read()
states = set()
for m in re.finditer(r'^\\s+([A-Z][A-Z_0-9]+):', content, re.MULTILINE):
    key = m.group(1)
    if not any(key.startswith(x) for x in ['HTTP','TEL','Logger','Comman','Filter','Updat','DEFAU','Conv','Inte','Mess']):
        states.add(key)
for s in sorted(states):
    print(s)
" 2>&1`);

  // Get BTN defs and usage
  const r3 = await execCmd(conn, `cd ${BOT_DIR} && grep -oP '^BTN_[A-Z_]+' bot/__init__.py | sort -u`);
  const r4 = await execCmd(conn, `cd ${BOT_DIR} && grep -rn 'BTN_' bot/handlers/ --include="*.py" | grep -oP 'BTN_[A-Z_]+' | sort -u`);

  // Get sales analysis (column write detail)
  const r5 = await execCmd(conn, `cd ${BOT_DIR} && python3 /tmp/analyze_sales.py`);
  
  // Get _replit calls
  const r6 = await execCmd(conn, `cd ${BOT_DIR} && grep -n '_replit_' bot/handlers/sales.py`);

  // Get API endpoints
  const r7 = await execCmd(conn, `cd ${BOT_DIR} && grep -nE 'app\\.(get|post|patch|delete|put)\\(' api_server/server.py`);

  // Get functions list
  const r8 = await execCmd(conn, `cd ${BOT_DIR} && grep -n '^def \\|^async def ' bot/handlers/sales.py`);

  // Get all sheet operations
  const r9 = await execCmd(conn, `cd ${BOT_DIR} && grep -n 'batch_update\\|append_row\\|update_cell\\|col_values' bot/handlers/sales.py`);

  console.log('=== HANDLER DIRECT RETURNS ===');
  console.log(r1.stdout);
  console.log('\n=== SHOW FUNCTIONS (indirect returns) ===');
  console.log(r1b.stdout);
  console.log('\n=== APP STATES COUNT ===');
  const appStates = r2.stdout.split('\n').filter(Boolean);
  console.log(appStates.length);
  console.log('\n=== BTN DEFINED COUNT ===');
  console.log(r3.stdout.split('\n').filter(Boolean).length);
  console.log('\n=== BTN USED COUNT ===');
  console.log(r4.stdout.split('\n').filter(Boolean).length);

  conn.end();

  // Now BUILD the files with all collected data
  // ============================================
  
  // Parse data
  const handlerStates = r1.stdout.split('\n').filter(Boolean);
  const appStatesArr = r2.stdout.split('\n').filter(Boolean);
  const btnDefined = r3.stdout.split('\n').filter(Boolean);
  const btnUsed = r4.stdout.split('\n').filter(Boolean);

  const statesInHandlersNotApp = handlerStates.filter(s => !appStatesArr.includes(s));
  const statesInAppNotHandlers = appStatesArr.filter(s => !handlerStates.includes(s));
  const btnDefinedNotUsed = btnDefined.filter(b => !btnUsed.includes(b));
  const btnUsedNotDefined = btnUsed.filter(b => !btnDefined.includes(b));

  // Write CONFIG data out so we can use it
  const config = JSON.stringify({
    handlerStates,
    appStatesArr,
    statesInHandlersNotApp,
    statesInAppNotHandlers,
    btnDefined,
    btnUsed,
    btnDefinedNotUsed,
    btnUsedNotDefined,
    handlerDirectReturns: r1.stdout,
    showFunctions: r1b.stdout,
    salesAnalysis: r5.stdout,
    replitCalls: r6.stdout,
    apiEndpoints: r7.stdout,
    salesFunctions: r8.stdout,
    sheetOps: r9.stdout
  }, null, 2);
  fs.writeFileSync('/home/node/.openclaw/workspace/audit_data.json', config);
  console.log('\n=== DATA SAVED TO audit_data.json ===');
})().catch(err => { console.error('FATAL:', err); process.exit(1); });
