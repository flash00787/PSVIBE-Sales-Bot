const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const commands = [
  { label: 'DIR_EXISTS', cmd: 'ls /root/Sales-Tele-Bot_refactored/ 2>&1 | head -20' },
  { label: 'MAIN_EXISTS', cmd: 'ls -la /root/Sales-Tele-Bot_refactored/main.py 2>&1' },
  { label: 'STAGING_CHECK', cmd: 'ls /root/staging/bot_src/ 2>&1 | head -20' },
  { label: 'SERVICE_STATUS', cmd: 'systemctl status psvibe-bot-refactored.service 2>&1 | head -15' },
  { label: 'JOURNAL_TAIL', cmd: 'journalctl -u psvibe-bot-refactored --no-pager -n 20 2>&1' },
  { label: 'DISK_SPACE', cmd: 'df -h / 2>&1' },
];

let idx = 0;
const results = {};

function runNext() {
  if (idx >= commands.length) {
    for (const [label, output] of Object.entries(results)) {
      console.log(`\n--- ${label} ---`);
      console.log(output.trim() || '(empty)');
    }
    conn.end();
    process.exit(0);
    return;
  }
  const { label, cmd } = commands[idx];
  idx++;
  console.error(`[${idx}/${commands.length}] ${label}`);
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
