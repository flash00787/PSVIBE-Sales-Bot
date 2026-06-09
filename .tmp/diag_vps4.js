const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();
conn.on('ready', () => {
  conn.exec(`
echo "=== Docker MySQL check ==="
docker exec psvibe-mysql mysql -u root -p"Psvibe@2025" -e "SHOW DATABASES;" 2>&1

echo ""
echo "=== Docker MySQL: SHOW TABLES in psvibe_api ==="
docker exec psvibe-mysql mysql -u root -p"Psvibe@2025" psvibe_api -e "SHOW TABLES;" 2>&1

echo ""
echo "=== Docker MySQL: promotions ==="
docker exec psvibe-mysql mysql -u root -p"Psvibe@2025" psvibe_api -e "SELECT * FROM promotions;" 2>&1

echo ""
echo "=== Docker MySQL: member_coupons ==="
docker exec psvibe-mysql mysql -u root -p"Psvibe@2025" psvibe_api -e "DESCRIBE member_coupons;" 2>&1

echo ""
echo "=== Docker MySQL: member_coupons data ==="
docker exec psvibe-mysql mysql -u root -p"Psvibe@2025" psvibe_api -e "SELECT * FROM member_coupons LIMIT 5;" 2>&1

echo ""
echo "=== MySQL config (Python API) ==="
grep -A5 "MYSQL_CFG\\|mysql.*host\\|mysql.*port\\|mysql.*user" /root/psvibe_api_server/mysql_db.py 2>&1 | head -20

echo ""
echo "=== Check if API uses socket vs TCP ==="
grep -n "host\|port\|socket\|unix_socket" /root/psvibe_api_server/mysql_db.py 2>&1 | head -10

echo ""
echo "=== API server logs (coupon) ==="
journalctl -u psvibe-api --no-pager -n 30 2>&1 | grep -i "coupon\|mysql\|error\|connect" | head -15
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
