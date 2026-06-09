const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

function execCmd(conn, cmd, timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, { timeout: timeoutMs }, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', d => stdout += d.toString());
      stream.stderr.on('data', d => stderr += d.toString());
      stream.on('close', () => resolve({ stdout: stdout.trim(), stderr: stderr.trim() }));
    });
  });
}

async function main() {
  const key = fs.readFileSync(KEY_PATH);
  
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({ host: '5.223.81.16', username: 'root', privateKey: key });
  });

  console.log('=== CONNECTED ===\n');

  // Get MySQL password from env or secrets
  console.log('=== Find MySQL credentials ===');
  console.log((await execCmd(conn, 'cat /etc/psvibe/secrets.env 2>/dev/null || echo "no secrets.env"')).stdout);
  console.log('---');
  console.log((await execCmd(conn, 'cat /root/psvibe-sales-bot/.env 2>/dev/null | grep -i mysql')).stdout);
  console.log('---');
  console.log((await execCmd(conn, 'cat /root/psvibe_api_server/config.py 2>/dev/null')).stdout);
  console.log('---');
  console.log((await execCmd(conn, 'cat /root/psvibe_api_server/mysql_db.py 2>/dev/null')).stdout);
  console.log('---');
  console.log((await execCmd(conn, 'cat /root/psvibe_api_server/db_client.py 2>/dev/null')).stdout);
  console.log('');

  // Try connecting via Docker exec to MySQL
  console.log('=== Try MySQL via Docker ===');
  console.log((await execCmd(conn, 'docker exec psvibe-mysql mysql -u psvibe_user -p$(docker exec psvibe-mysql printenv MYSQL_PASSWORD 2>/dev/null || echo "") -e "SHOW DATABASES;" 2>&1 | head -20')).stdout);
  console.log('---');
  // Try finding password
  console.log((await execCmd(conn, 'docker inspect psvibe-mysql 2>/dev/null | grep -A5 "Env" | head -20')).stdout);
  console.log('');

  // Try mysql with no password or different methods
  console.log('=== Try MySQL access ===');
  console.log((await execCmd(conn, 'docker exec psvibe-mysql mysql -u root -e "SHOW DATABASES;" 2>&1 | head -20')).stdout);
  console.log('---');
  console.log((await execCmd(conn, 'docker exec psvibe-mysql mysql -u psvibe_user -e "SHOW DATABASES;" 2>&1 | head -20')).stdout);
  console.log('---');
  // Check if there's a .my.cnf
  console.log((await execCmd(conn, 'cat /root/.my.cnf 2>/dev/null || echo "no .my.cnf"')).stdout);
  console.log('');

  // Try grep for password across config files
  console.log('=== Search for MySQL password ===');
  console.log((await execCmd(conn, 'grep -rn "MYSQL_PASSWORD\|mysql_password\|MYSQL_ROOT" /root/psvibe_api_server/ /root/psvibe-sales-bot/ 2>/dev/null | grep -v ".bak\|.backup\|__pycache__" | head -20')).stdout);
  console.log('---');
  console.log((await execCmd(conn, 'grep -rn "MYSQL_PASSWORD\|mysql_password\|MYSQL_ROOT" /etc/ 2>/dev/null | head -10')).stdout);
  console.log('');

  conn.end();
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
