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

  // Search for _bg, _sale_, background, or bg in function names
  const r1 = await execCmd(conn, `cd ${BOT_DIR} && grep -n '_bg\\|def.*sale\\|def.*Sale\\|def.*bg\\|def.*Bg\\|def.*background' bot/handlers/sales.py`);
  console.log('=== BG/SALE function names ===');
  console.log(r1.stdout);

  // Search for step_sale_confirm content around line 979
  const r2 = await execCmd(conn, `cd ${BOT_DIR} && sed -n '810,1090p' bot/handlers/sales.py | head -5; echo '...'; sed -n '975,1088p' bot/handlers/sales.py`);
  console.log('=== Around step_sale_confirm lines 975-1088 ===');
  console.log(r2.stdout);

  // Search for _sale_bg in ALL files
  const r3 = await execCmd(conn, `cd ${BOT_DIR} && grep -rn '_sale_bg' . --include='*.py'`);
  console.log('=== _sale_bg references in project ===');
  console.log(r3.stdout);

  conn.end();
})().catch(err => { console.error('FATAL:', err); process.exit(1); });
