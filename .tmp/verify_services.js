const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();
conn.on('ready', () => {
  conn.exec(`
echo "=== Service Status ==="
systemctl is-active psvibe-sale-bot psvibe_customer_bot psvibe-api 2>&1

echo ""
echo "=== Recent bot startup logs ==="
journalctl -u psvibe-sale-bot --no-pager --since "1 minute ago" 2>&1 | tail -10

echo ""
echo "=== Verify coupon endpoint ==="
curl -s --connect-timeout 5 "http://localhost:8000/api/coupons/generate?api_key=JWIErd…D-AQ" -X POST -H "Content-Type: application/json" -d '{"member_id":"99","session_minutes":30}' 2>&1
  `, (err, stream) => {
    let data = '';
    stream.on('data', (chunk) => { data += chunk.toString(); });
    stream.stderr.on('data', (chunk) => { data += 'STDERR: ' + chunk.toString(); });
    stream.on('close', () => {
      console.log(data);
      conn.end();
    });
  });
});
conn.on('error', (err) => { console.error('SSH Error:', err.message); });
conn.connect({ host: HOST, username: 'root', privateKey: fs.readFileSync(KEY_PATH), readyTimeout: 20000 });
