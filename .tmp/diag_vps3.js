const { Client } = require('/home/node/.openclaw/workspace/node_modules/ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const conn = new Client();
conn.on('ready', () => {
  conn.exec(`
echo "=== MySQL Service Status ==="
systemctl status mysql 2>&1 | head -10
echo ""
systemctl status mariadb 2>&1 | head -10 || echo "mariadb not installed"
echo ""

echo "=== Is MySQL installed? ==="
which mysql mysqld 2>&1
dpkg -l | grep mysql 2>&1 | head -5

echo ""
echo "=== Trying to start MySQL ==="
systemctl start mysql 2>&1
sleep 2
systemctl is-active mysql 2>&1

echo ""
echo "=== MySQL socket ==="
ls -la /run/mysqld/ 2>&1 || echo "No /run/mysqld/"
ls -la /var/run/mysqld/ 2>&1 || echo "No /var/run/mysqld/"

echo ""
echo "=== Check for Docker MySQL ==="
docker ps 2>&1 | grep mysql || echo "No docker mysql"
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
