const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const commands = [
  { label: 'SYSTEMCTL_STATUS', cmd: 'systemctl status psvibe-bot.service 2>/dev/null | head -20' },
  { label: 'SYSTEMCTL_IS_ACTIVE', cmd: 'systemctl is-active psvibe-bot.service 2>/dev/null' },
  { label: 'SERVICE_FILE', cmd: 'cat /etc/systemd/system/psvibe-bot.service 2>/dev/null' },
  { label: 'LIST_PSVI_SERVICES', cmd: 'systemctl list-units --type=service 2>/dev/null | grep psvi; systemctl list-unit-files --type=service 2>/dev/null | grep psvi' },
  { label: 'DEPLOY_SCRIPT', cmd: 'cat /root/staging/scripts/deploy.sh 2>/dev/null' },
  { label: 'REFACTORED_DIR', cmd: 'ls -la /root/Sales-Tele-Bot_refactored/ 2>/dev/null' },
  { label: 'REFACTORED_VENV', cmd: 'ls /root/Sales-Tele-Bot_refactored/.venv/bin/python* 2>/dev/null' },
  { label: 'V1_VENV', cmd: 'ls -la /root/Sales-Tele-Bot/.venv/ 2>/dev/null' },
  { label: 'REFACTORED_ENV', cmd: 'ls -la /root/Sales-Tele-Bot_refactored/.env 2>/dev/null' },
  { label: 'REFACTORED_LOGS', cmd: 'ls -la /root/Sales-Tele-Bot_refactored/logs/ 2>/dev/null' },
  { label: 'REFACTORED_MAIN', cmd: 'ls -la /root/Sales-Tele-Bot_refactored/main.py 2>/dev/null' },
  { label: 'STAGING_SRC', cmd: 'ls /root/staging/bot_src/ 2>/dev/null' },
  { label: 'REFACTORED_BOT_DIR', cmd: 'ls /root/Sales-Tele-Bot_refactored/bot/ 2>/dev/null' },
  { label: 'PYTHON3_PATH', cmd: 'which python3 && python3 --version' },
];

let idx = 0;
const results = {};

function runNext() {
  if (idx >= commands.length) {
    console.log('\n=== STEP 1 RESULTS ===\n');
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
