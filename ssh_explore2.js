const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const conn = new Client();

conn.on('ready', () => {
  const commands = [
    'ls -la /root/scripts/ 2>&1',
    'cat /root/scripts/check-coco-telegram.sh 2>&1 | head -30',
    'cat /root/scripts/clean-coco-processing.sh 2>&1 | head -30',
    'find /root -maxdepth 3 -name "*.sh" -type f 2>/dev/null | head -20',
    'systemctl is-active psvibe-sale-bot.service psvibe_customer_bot.service psvibe-api.service 2>&1',
    'free -h 2>&1',
    'df -h / 2>&1',
    'uptime 2>&1',
    'find /root -maxdepth 2 -type d -name "monitoring" 2>/dev/null',
    'dpkg -l | grep -i monit 2>/dev/null | head -5',
    'journalctl -u psvibe-sale-bot.service --no-pager -n 10 2>&1',
    'journalctl -u psvibe_customer_bot --no-pager -n 10 2>&1',
    'journalctl -u psvibe-api.service --no-pager -n 10 2>&1'
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
        console.log(`=== CMD ${idx} ===`);
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
