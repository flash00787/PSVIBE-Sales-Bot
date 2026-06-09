const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();
conn.on('ready', () => {
  conn.exec(`
echo "=== mysql_db.py config ==="
cat /root/psvibe_api_server/mysql_db.py | head -80

echo ""
echo "=== Docker MySQL: try env-based password ==="
docker exec psvibe-mysql mysql -u root -p"psvibe_root_2024" -e "SHOW DATABASES;" 2>&1

echo ""
echo "=== Docker MySQL env ==="
docker inspect psvibe-mysql 2>&1 | grep -A5 "MYSQL_ROOT_PASSWORD\|MYSQL_USER\|MYSQL_PASSWORD" | head -15

echo ""
echo "=== Recent API server full logs ==="
journalctl -u psvibe-api --no-pager -n 20 2>&1

echo ""
echo "=== Recent sale bot full logs ==="
journalctl -u psvibe-sale-bot --no-pager -n 20 2>&1
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
