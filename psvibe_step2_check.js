const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const commands = [
  { label: 'REFACTORED_SERVICE_FILE', cmd: 'cat /etc/systemd/system/psvibe-bot-refactored.service 2>/dev/null' },
  { label: 'CURRENT_PROCESS', cmd: 'ps aux | grep -E "main.py|Sales-Tele-Bot" | grep -v grep' },
  { label: 'REFACTORED_VENV_DETAIL', cmd: 'ls -la /root/Sales-Tele-Bot_refactored/.venv/ 2>/dev/null; ls /root/Sales-Tele-Bot_refactored/.venv/bin/python* 2>/dev/null' },
  { label: 'REFACTORED_BOT_APP', cmd: 'head -20 /root/Sales-Tele-Bot_refactored/bot/app.py 2>/dev/null' },
  { label: 'REFACTORED_MAIN_CONTENT', cmd: 'cat /root/Sales-Tele-Bot_refactored/main.py 2>/dev/null' },
  { label: 'STAGING_MAIN_CONTENT', cmd: 'cat /root/staging/bot_src/main.py 2>/dev/null' },
  { label: 'STAGING_BOT_APP', cmd: 'head -20 /root/staging/bot_src/bot/app.py 2>/dev/null' },
  { label: 'VERIFY_IMPORTS_SCRIPT', cmd: 'cat /root/staging/scripts/verify_imports.py 2>/dev/null' },
  { label: 'ROLLBACK_SCRIPT', cmd: 'cat /root/staging/scripts/rollback.sh 2>/dev/null' },
];

let idx = 0;
const results = {};

function runNext() {
  if (idx >= commands.length) {
    console.log('\n=== STEP 2 RESULTS ===\n');
    for (const [label, output] of Object.entries(results)) {
      console.log(`\n--- ${label} ---`);
      console.log(output.trim() || '(empty/no output)');
    }
    conn.end();
    process.exit(0);
    return;
  }
  const { label, cmd } = commands[idx];
  idx++;
  console.error(`[${idx}/${commands.length}] Running: ${label}`);
  conn.exec(cmd, (err, stream) => {
    if (err) { results[label] = `EXEC ERR: ${err.message}`; runNext(); return; }
    let out = '';
    stream.on('data', d => out += d);
    stream.stderr.on('data', d => out += d);
    stream.on('close', () => { results[label] = out; runNext(); });
  });
}

conn.on('ready', runNext);
conn.on('error', e => { console.error('SSH error:', e.message); process.exit(1); });
conn.connect({
  host: '167.71.196.120',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
