const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected');
  const cmds = `
echo "=== Sales-Tele-Bot_refactored ==="
ls -la /root/Sales-Tele-Bot_refactored/ 2>&1 | tail -20
echo "=== staging/bot_src ==="
ls -la /root/staging/bot_src/ 2>&1 | tail -20
echo "=== systemd psvibe files ==="
ls -la /etc/systemd/system/psvibe* 2>&1
echo "=== psvibe-bot.service status ==="
systemctl status psvibe-bot.service 2>&1 | head -5 || true
echo "=== .env files ==="
ls -la /root/Sales-Tele-Bot/.env /root/Sales-Tele-Bot_refactored/.env 2>&1
echo "=== existing py/pip ==="
which python3 && python3 --version
which pip3 && pip3 --version
echo "=== disk ==="
df -h / | tail -1
`;

  conn.exec(cmds, (err, stream) => {
    if (err) throw err;
    stream.on('data', data => process.stdout.write(data.toString()));
    stream.stderr.on('data', data => process.stderr.write(data.toString()));
    stream.on('close', () => { conn.end(); console.log('\nDone.'); });
  });
});

conn.on('error', err => { console.error('SSH error:', err); process.exit(1); });

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000,
});
