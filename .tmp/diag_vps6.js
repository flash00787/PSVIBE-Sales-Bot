const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();
conn.on('ready', () => {
  conn.exec(`
echo "=== API Server status ==="
systemctl is-active psvibe-api 2>&1

echo ""
echo "=== API Server crash log check ==="
journalctl -u psvibe-api --no-pager --since "4 hours ago" 2>&1 | tail -30

echo ""
echo "=== Try Docker MySQL with psvibe_user ==="
docker exec psvibe-mysql mysql -u psvibe_user -p"PsVibe@2026_Rotated!" psvibe_api -e "SHOW TABLES;" 2>&1

echo ""
echo "=== Docker MySQL: promotions table ==="
docker exec psvibe-mysql mysql -u psvibe_user -p"PsVibe@2026_Rotated!" psvibe_api -e "SELECT * FROM promotions;" 2>&1

echo ""
echo "=== Docker MySQL: member_coupons table ==="
docker exec psvibe-mysql mysql -u psvibe_user -p"PsVibe@2026_Rotated!" psvibe_api -e "DESCRIBE member_coupons;" 2>&1

echo ""
echo "=== Docker MySQL: member_coupons data ==="
docker exec psvibe-mysql mysql -u psvibe_user -p"PsVibe@2026_Rotated!" psvibe_api -e "SELECT * FROM member_coupons LIMIT 5;" 2>&1

echo ""
echo "=== Test coupon endpoint ==="
curl -s "http://localhost:8000/api/coupons/generate?api_key=JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" -X POST -H "Content-Type: application/json" -d '{"member_id":"5","session_minutes":60}' 2>&1

echo ""
echo "=== Check promotions endpoint ==="
curl -s "http://localhost:8000/api/promotions/active?api_key=JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" 2>&1
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
