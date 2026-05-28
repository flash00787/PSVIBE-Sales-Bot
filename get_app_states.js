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

  // Get FULL app.py states section
  const r1 = await execCmd(conn, `cd ${BOT_DIR} && sed -n '95,250p' bot/app.py`);
  console.log('=== APP.PY STATES SECTION (lines 95-250) ===');
  console.log(r1.stdout);

  // Also check if handlers return states by calling show_main_menu (which returns states)
  const r2 = await execCmd(conn, `cd ${BOT_DIR} && grep -rn 'return await show_main_menu\\|return await show_admin\\|return await show_' bot/handlers/ --include='*.py' | head -20`);
  console.log('\n=== INDIRECT STATE RETURNS ===');
  console.log(r2.stdout);

  // Get states from app.py - check the states dict format
  const r3 = await execCmd(conn, `cd ${BOT_DIR} && python3 -c "
import re
with open('bot/app.py') as f:
    content = f.read()
# Find the states dict
start = content.find('states={')
if start == -1:
    start = content.find('states = {')
if start == -1:
    print('states dict not found')
else:
    # Extract until balanced braces
    depth = 0
    for i in range(start, len(content)):
        if content[i] == '{': depth += 1
        elif content[i] == '}': depth -= 1
        if depth == 0:
            print(content[start:i+1])
            break
"`);
  console.log('\n=== STATES DICT FROM APP.PY ===');
  console.log(r3.stdout);

  conn.end();
})().catch(err => { console.error('FATAL:', err); process.exit(1); });
