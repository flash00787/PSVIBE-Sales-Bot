const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const conn = new Client();

conn.on('ready', () => {
  const commands = [
    'ls -la /root/monitoring/ 2>&1 || echo "DIR_NOT_FOUND"',
    'ls -la /root/ | grep -i monit 2>&1 || echo "NO_MONIT_IN_ROOT"',
    'ls -la /etc/monitoring/ 2>&1 || echo "NO_ETC_MONIT"',
    'find /root -name "*alert*" -o -name "*monitor*" -o -name "*health*" -o -name "*check*alerts*" 2>/dev/null | head -20',
    'ls -la /root/ 2>&1 | head -30',
    'ls -la /root/psvibe-sales-bot/ 2>&1 | head -10',
    'cat /root/crontab 2>/dev/null || crontab -l 2>/dev/null || echo "NO_CRONTAB"',
    'systemctl list-timers --all 2>/dev/null | head -20',
    'journalctl -n 50 --no-pager 2>/dev/null | grep -i -E "(monitor|alert|health|check)" | tail -20 || echo "NO_JOURNAL_MATCH"',
    'ls -la /root/backups/ 2>&1 | head -10',
    'ls -la /root/staging/ 2>&1 | head -10'
  ];

  let idx = 0;
  runNext();

  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    const cmd = commands[idx];
    conn.exec(cmd, (err, stream) => {
      let out = '';
      if (err) { out = `EXEC_ERR: ${err.message}`; }
      stream.on('data', (d) => out += d.toString());
      stream.stderr.on('data', (d) => out += d.toString());
      stream.on('close', () => {
        console.log(`=== CMD ${idx}: ${cmd.substring(0, 80)} ===`);
        console.log(out.trim());
        console.log('');
        idx++;
        runNext();
      });
    });
  }
}).connect({
  host: HOST,
  port: 22,
  username: USER,
  privateKey: KEY,
  readyTimeout: 15000
});
