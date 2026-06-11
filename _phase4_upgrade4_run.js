#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');
const { execSync } = require('child_process');

const scriptB64 = execSync('base64 -w0 /home/node/.openclaw/workspace/_auto_release_consoles.py').toString().trim();

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

// Shell command: transfer script, test, create cron
const cmd = 
  'mkdir -p /root/scripts && ' +
  'echo "' + scriptB64 + '" | base64 -d > /root/scripts/auto_release_consoles.py && ' +
  'chmod +x /root/scripts/auto_release_consoles.py && ' +
  'echo "=== Testing auto_release_consoles.py ===" && ' +
  'python3 /root/scripts/auto_release_consoles.py && ' +
  'echo "=== Creating cron job ===" && ' +
  'cat > /etc/cron.d/kora-auto-release << \'CRONEOF\'\n' +
  '# Auto-release consoles when booking end_time passes (runs every 5 min)\n' +
  '*/5 * * * * root /usr/bin/python3 /root/scripts/auto_release_consoles.py >> /var/log/auto_release_consoles.log 2>&1\n' +
  'CRONEOF\n' +
  'chmod 644 /etc/cron.d/kora-auto-release && ' +
  'echo "Cron file created:" && ' +
  'cat /etc/cron.d/kora-auto-release && ' +
  'echo "=== Restarting cron ===" && ' +
  'systemctl restart cron 2>&1 || service cron restart 2>&1 || echo "Warning: cron restart failed" && ' +
  'echo "=== Verifying cron is running ===" && ' +
  'systemctl status cron 2>&1 | head -5 || echo "status check N/A"';

conn.on('ready', () => {
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC ERR:', err); conn.end(); process.exit(1); }
    let out = '';
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { out += d.toString(); });
    stream.on('close', (code) => {
      console.log(out);
      if (code) console.error('Exit code:', code);
      conn.end();
    });
  });
});
conn.on('error', e => { console.error('SSH ERR:', e.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 60000 });
