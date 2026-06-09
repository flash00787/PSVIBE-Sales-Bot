const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();
conn.on('ready', () => {
  conn.exec(`
echo "=== MySQL DB list ==="
mysql -u root -p"Psvibe@2025" -e "SHOW DATABASES;" 2>&1

echo ""
echo "=== MySQL Tables in psvibe_api ==="
mysql -u root -p"Psvibe@2025" psvibe_api -e "SHOW TABLES;" 2>&1

echo ""
echo "=== Promotions Table (force error output) ==="
mysql -u root -p"Psvibe@2025" psvibe_api -e "SELECT * FROM promotions;" 2>&1

echo ""
echo "=== Member Coupons Table ==="
mysql -u root -p"Psvibe@2025" psvibe_api -e "SELECT * FROM member_coupons LIMIT 5;" 2>&1

echo ""
echo "=== Recent bot logs (coupon) ==="
journalctl -u psvibe-sale-bot --no-pager -n 20 2>&1 | grep -i "coupon\|cashback" || echo "No coupon logs found"

echo ""
echo "=== psvibe-sale-bot status ==="
systemctl is-active psvibe-sale-bot 2>&1

echo ""
echo "=== psvibe_customer_bot status ==="
systemctl is-active psvibe_customer_bot 2>&1

echo ""
echo "=== psvibe-api status ==="
systemctl is-active psvibe-api 2>&1
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
conn.on('error', (err) => { console.error('Error:', err.message); });
conn.connect({ host: HOST, username: 'root', privateKey: fs.readFileSync(KEY_PATH), readyTimeout: 20000 });
