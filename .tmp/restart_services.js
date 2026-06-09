const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();
conn.on('ready', () => {
  conn.exec(`
echo "=== RESTARTING SERVICES ==="

echo ""
echo "--- Restart psvibe-sale-bot ---"
systemctl restart psvibe-sale-bot
sleep 3
systemctl is-active psvibe-sale-bot && echo "✓ psvibe-sale-bot ACTIVE" || echo "✗ psvibe-sale-bot FAILED"

echo ""
echo "--- Restart psvibe_customer_bot ---"
systemctl restart psvibe_customer_bot
sleep 3
systemctl is-active psvibe_customer_bot && echo "✓ psvibe_customer_bot ACTIVE" || echo "✗ psvibe_customer_bot FAILED"

echo ""
echo "--- Run API sync ---"
/root/psvibe_api_server/run_sync.sh 2>&1 | tail -5

echo ""
echo "--- API server status ---"
systemctl is-active psvibe-api 2>&1

echo ""
echo "--- Recent sale bot logs ---"
journalctl -u psvibe-sale-bot --no-pager -n 10 2>&1

echo ""
echo "--- Verify coupon endpoint still works ---"
curl -s "http://localhost:8000/api/coupons/generate?api_key=JWIErd…D-AQ" -X POST -H "Content-Type: application/json" -d '{"member_id":"99","session_minutes":30}' 2>&1

echo ""
echo "============================================"
echo " ALL DONE"
echo "============================================"
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
conn.connect({ host: HOST, username: 'root', privateKey: fs.readFileSync(KEY_PATH), readyTimeout: 30000 });
