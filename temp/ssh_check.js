const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const keyPath = path.resolve('/home/node/.openclaw/workspace/.ssh/id_rsa');
const privateKey = fs.readFileSync(keyPath, 'utf8');

const commands = [
  'echo "=== SERVICE STATUS ==="',
  'systemctl is-active psvibe-sale-bot psvibe_customer_bot psvibe-api psvibe-watchdog cloudflared-tunnel',
  'echo ""',
  'echo "=== RESTART COUNTS ==="',
  'systemctl show psvibe-sale-bot -p NRestarts',
  'systemctl show psvibe_customer_bot -p NRestarts',
  'systemctl show psvibe-api -p NRestarts',
  'systemctl show psvibe-watchdog -p NRestarts',
  'systemctl show cloudflared-tunnel -p NRestarts',
  'echo ""',
  'echo "=== COORDINATION DIR ==="',
  'ls -la /root/coordination/ 2>&1 | head -25',
  'echo ""',
  'echo "=== FILE COUNT ==="',
  'ls /root/coordination/*.py 2>/dev/null | wc -l',
  'echo ""',
  'echo "=== SYSTEMD UNIT FILES EXIST ==="',
  'for u in psvibe-sale-bot psvibe_customer_bot psvibe-api psvibe-watchdog cloudflared-tunnel; do echo "$u: $(systemctl show -p LoadState $u 2>/dev/null | cut -d= -f2)"; done'
].join(' && ');

const conn = new Client();
conn.on('ready', () => {
  conn.exec(commands, (err, stream) => {
    if (err) {
      console.error('EXEC ERROR:', err.message);
      process.exit(1);
    }
    let output = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { output += '[STDERR] ' + data.toString(); });
    stream.on('close', (code) => {
      console.log(output);
      conn.end();
      process.exit(code || 0);
    });
  });
}).on('error', (err) => {
  console.error('CONNECTION ERROR:', err.message);
  process.exit(1);
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: privateKey
});
