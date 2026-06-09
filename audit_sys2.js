const { Client } = require('ssh2');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH CONNECTED');

  const commands = [
    // Monitoring scripts
    "ls -la /root/monitoring/ 2>/dev/null || echo 'NO monitoring'",
    "ls -la /root/backups/ 2>/dev/null || echo 'NO backups'",
    "cat /root/monitoring/health.sh 2>/dev/null",
    "cat /root/monitoring/ratelimit.sh 2>/dev/null",
    "cat /root/monitoring/check_alerts.sh 2>/dev/null",
    // Refactored dir
    "find /root/Sales-Tele-Bot_refactored -name '*.py' -type f 2>/dev/null | sort",
    "ls -la /root/Sales-Tele-Bot_refactored/ 2>/dev/null",
    "for f in $(find /root/Sales-Tele-Bot_refactored -name '*.py' -type f 2>/dev/null | sort); do echo \"$(wc -l < \"$f\") $f\"; done",
    // Service status
    "systemctl status psvibe-bot --no-pager 2>/dev/null | head -20",
    "systemctl status psvibe-customer --no-pager 2>/dev/null | head -20",
    "systemctl status psvibe-customer-refactored --no-pager 2>/dev/null | head -20",
  ];

  let idx = 0;
  function runNext() {
    if (idx >= commands.length) {
      conn.end();
      return;
    }
    const cmd = commands[idx++];
    console.log('\n=== #' + idx + ': ' + cmd.substring(0, 100) + ' ===');
    conn.exec(cmd, (err, stream) => {
      if (err) { console.error('err:', err); conn.end(); return; }
      let out = '';
      stream.on('data', d => out += d.toString());
      stream.stderr.on('data', d => out += d.toString());
      stream.on('close', () => {
        console.log(out.slice(0, 30000));
        runNext();
      });
    });
  }
  runNext();
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err);
  process.exit(1);
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  password: 'Freedom2024#RevFlash',
  readyTimeout: 15000,
});
