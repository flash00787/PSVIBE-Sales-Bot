const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();
conn.on('ready', () => {
  conn.exec(`
echo "=== FIXED: launch_session_sale coupon block ==="
grep -n -A20 "CashBack Coupon: Auto-generate via MySQL API" /root/psvibe-sales-bot/bot/handlers/sales.py

echo ""
echo "=== VERIFY: Dead code removed from _end_single_session_and_launch ==="
sed -n '583,595p' /root/psvibe-sales-bot/bot/handlers/sales.py

echo ""
echo "=== VERIFY: console.py coupon code intact ==="
sed -n '305,330p' /root/psvibe-sales-bot/bot/handlers/console.py
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
