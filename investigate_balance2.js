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

  // Check MySQL status
  console.log('=== MySQL Status ===');
  console.log((await execCmd(conn, 'systemctl status mysql 2>&1 | head -10 || service mysql status 2>&1 | head -10')).stdout);
  console.log((await execCmd(conn, 'which mysql; mysqld --version 2>&1; ls /run/mysqld/ 2>&1; ls /var/run/mysqld/ 2>&1')).stdout);
  console.log('');

  // Check if it's using SQLite
  console.log('=== Check DB config ===');
  console.log((await execCmd(conn, 'cat /root/psvibe-sales-bot/.env 2>/dev/null')).stdout);
  console.log('---');
  console.log((await execCmd(conn, 'cat /root/psvibe_api_server/.env 2>/dev/null || cat /root/psvibe_api_server/.env* 2>/dev/null')).stdout);
  console.log('---');
  console.log((await execCmd(conn, 'grep -rn "DB_\|DATABASE\|MYSQL\|mysql\|sqlite\|psvibe.db\|psvibe_dashboard" /root/psvibe-sales-bot/bot/*.py /root/psvibe-sales-bot/customer_bot/*.py 2>/dev/null | head -40')).stdout);
  console.log('');

  // Check SQLite
  console.log('=== SQLite DB ===');
  console.log((await execCmd(conn, 'ls -la /root/psvibe-sales-bot/psvibe.db 2>/dev/null; file /root/psvibe-sales-bot/psvibe.db 2>/dev/null')).stdout);
  console.log('---');
  console.log((await execCmd(conn, 'ls -la /root/psvibe-sales-bot/sqlite/ 2>/dev/null')).stdout);
  console.log('');

  // Dump SQLite schema
  console.log('=== SQLite Schema ===');
  console.log((await execCmd(conn, 'sqlite3 /root/psvibe-sales-bot/psvibe.db ".tables" 2>/dev/null || echo "(no sqlite3 or no tables)"')).stdout);
  console.log('---');
  console.log((await execCmd(conn, 'sqlite3 /root/psvibe-sales-bot/psvibe.db ".schema" 2>/dev/null | head -200')).stdout);
  console.log('');

  // Check DB_SCHEMA.md
  console.log('=== DB_SCHEMA.md ===');
  console.log((await execCmd(conn, 'head -200 /root/psvibe-sales-bot/DB_SCHEMA.md 2>/dev/null')).stdout);
  console.log('');

  // Check for Docker MySQL
  console.log('=== Docker Check ===');
  console.log((await execCmd(conn, 'docker ps 2>/dev/null | grep mysql || echo "(no mysql docker)"')).stdout);
  console.log((await execCmd(conn, 'docker ps 2>/dev/null')).stdout);
  console.log('');

  // Search all Python files for income/balance/expense
  console.log('=== Search income/balance/expense in sales bot ===');
  console.log((await execCmd(conn, 'grep -rn "income\|total_income\|expense\|balance\|acc.*bal\|cash_movement\|opex" /root/psvibe-sales-bot/bot/ --include="*.py" 2>/dev/null | head -40')).stdout);
  console.log('---');
  console.log((await execCmd(conn, 'grep -rn "income\|total_income\|expense\|balance" /root/psvibe-sales-bot/customer_bot/ --include="*.py" 2>/dev/null | head -40')).stdout);
  console.log('');

  // Check API server
  console.log('=== API server files ===');
  console.log((await execCmd(conn, 'ls -la /root/psvibe_api_server/ 2>/dev/null; ls -la /root/psvibe_api_server/*.py 2>/dev/null')).stdout);
  console.log('');

  // Search API for any finance/balance/dashboard
  console.log('=== Search API for finance/dashboard/balance ===');
  console.log((await execCmd(conn, 'grep -rn "finance\|balance\|income\|expense\|dashboard" /root/psvibe_api_server/ --include="*.py" 2>/dev/null | head -40')).stdout);
  console.log('');

  // Check for MySQL config files
  console.log('=== MySQL/DB config search ===');
  console.log((await execCmd(conn, 'find /root -name "*.cnf" -o -name "my.cnf" 2>/dev/null | head -10; cat /etc/mysql/my.cnf 2>/dev/null | head -20; cat /etc/mysql/mysql.conf.d/mysqld.cnf 2>/dev/null | head -20')).stdout);
  console.log('');

  // Check git repo for DB schema in sales bot
  console.log('=== key Python files in sales_bot ===');
  console.log((await execCmd(conn, 'ls -la /root/psvibe-sales-bot/bot/*.py 2>/dev/null')).stdout);
  console.log('');

  // Check main.py
  console.log('=== main.py ===');
  console.log((await execCmd(conn, 'cat /root/psvibe-sales-bot/main.py 2>/dev/null')).stdout);
  console.log('');

  conn.end();
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
