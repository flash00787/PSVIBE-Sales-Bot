const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  const commands = [
    { label: 'IMPORT_TEST', cmd: 'cd /root/Sales-Tele-Bot_refactored && /root/Sales-Tele-Bot_refactored/.venv/bin/python3 -c "from bot import *; print(\"Import OK\")" 2>&1' },
    { label: 'FRESH_LOGS', cmd: 'tail -30 /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null' },
    { label: 'SERVICE_STATUS', cmd: 'systemctl status psvibe-bot-refactored.service 2>&1 | head -20' },
    { label: 'SERVICE_FILE_FINAL', cmd: 'cat /etc/systemd/system/psvibe-bot-refactored.service' },
    { label: 'PROCESS_CHECK', cmd: 'ps aux | grep "Sales-Tele-Bot_refactored/main.py" | grep -v grep' },
    { label: 'V1_SERVICE_STATUS', cmd: 'systemctl status psvibe-bot.service 2>&1 | head -5' },
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

  runNext();
});

conn.on('error', e => { console.error('SSH error:', e.message); process.exit(1); });
conn.connect({
  host: '167.71.196.120',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
