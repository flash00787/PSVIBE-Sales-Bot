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

  // Upload analyze_sales.py via SFTP
  const pyContent = fs.readFileSync('/home/node/.openclaw/workspace/analyze_sales.py', 'utf8');
  await new Promise((resolve, reject) => {
    conn.sftp((err, sftp) => {
      if (err) return reject(err);
      const buf = Buffer.from(pyContent, 'utf8');
      const stream = sftp.createWriteStream('/tmp/analyze_sales.py', { mode: 0o644 });
      stream.on('error', reject);
      stream.on('close', resolve);
      stream.write(buf);
      stream.end();
    });
  });
  console.log('analyze_sales.py uploaded');

  const r1 = await execCmd(conn, 'python3 /tmp/analyze_sales.py');
  console.log('=== PYTHON ANALYSIS ===');
  console.log(r1.stdout);
  if (r1.stderr) console.error('ERR:', r1.stderr);

  const r2 = await execCmd(conn, `cd ${BOT_DIR} && grep -n 'STATE' bot/app.py | head -30`);
  console.log('=== APP STATE FORMAT (STATE refs) ===');
  console.log(r2.stdout);

  const r3 = await execCmd(conn, `cd ${BOT_DIR} && grep -n '_replit_' bot/handlers/sales.py`);
  console.log('=== REPLIT CALLS ===');
  console.log(r3.stdout);

  const r4 = await execCmd(conn, `cd ${BOT_DIR} && grep -nE 'app\\.(get|post|patch|delete|put)\\(' api_server/server.py 2>/dev/null || echo 'no api_server'`);
  console.log('=== API ENDPOINTS ===');
  console.log(r4.stdout);

  const r5 = await execCmd(conn, `cd ${BOT_DIR} && grep -n '^def \\|^async def ' bot/handlers/sales.py`);
  console.log('=== SALES.PY FUNCTIONS ===');
  console.log(r5.stdout);

  const r6 = await execCmd(conn, `cd ${BOT_DIR} && grep -n 'batch_update\\|append_row\\|update_cell\\|col_values' bot/handlers/sales.py`);
  console.log('=== SHEET OPS ===');
  console.log(r6.stdout);

  // Also get app.py state registry more broadly
  const r7 = await execCmd(conn, `cd ${BOT_DIR} && grep -n '=' bot/app.py | grep -iE 'state|step|page' | head -30`);
  console.log('=== APP STATE DEFS ===');
  console.log(r7.stdout);

  conn.end();
})().catch(err => { console.error('FATAL:', err); process.exit(1); });
