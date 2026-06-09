const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const outDir = '/home/node/.openclaw/workspace/.tmp/vps_files';
const fs2 = require('fs');

const conn = new Client();
conn.on('ready', () => {
  // Check multiple things
  conn.exec(`
echo "=== Python Version ==="
python3 --version

echo ""
echo "=== Promotions Table ==="
mysql -u root -p"Psvibe@2025" psvibe_api -e "SELECT * FROM promotions;"

echo ""
echo "=== Member Coupons Table ==="
mysql -u root -p"Psvibe@2025" psvibe_api -e "SELECT * FROM member_coupons LIMIT 5;"

echo ""
echo "=== member_coupons table schema ==="
mysql -u root -p"Psvibe@2025" psvibe_api -e "DESCRIBE member_coupons;"

echo ""
echo "=== API_BASE_URL env ==="
grep -r "API_BASE_URL" /etc/psvibe/ 2>/dev/null || echo "Not found in /etc/psvibe/"
grep -r "API_KEY" /etc/psvibe/ 2>/dev/null | head -5
  `, (err, stream) => {
    let data = '';
    stream.on('data', (chunk) => { data += chunk.toString(); });
    stream.on('close', () => {
      console.log(data);
      fs2.writeFileSync(`${outDir}/vps_diag.txt`, data);
      conn.end();
    });
  });
});
conn.on('error', (err) => { console.error('Error:', err.message); });
conn.connect({ host: HOST, username: 'root', privateKey: fs.readFileSync(KEY_PATH), readyTimeout: 20000 });
