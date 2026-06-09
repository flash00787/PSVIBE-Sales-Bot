const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const keyPath = '/home/node/.openclaw/workspace/.ssh/id_rsa';

const commands = [
  'hostname',
  'echo "=== FILE_LIST ==="',
  'find /root/psvibe-sale-bot -type f \\( -name "*.py" -o -name "*.sh" -o -name "*.env" -o -name "*.md" -o -name "*.json" -o -name "*.yaml" -o -name "*.txt" \\) 2>/dev/null | sort',
  'echo "=== MYSQL_REF ==="',
  'grep -rnl "mysql\\|pymysql\\|MySQLdb\\|mysql-connector\\|sqlalchemy" /root/psvibe-sale-bot/ 2>/dev/null; echo "exit:$?"',
  'echo "=== SQLITE_DIR ==="',
  'ls -la /root/psvibe-sale-bot/sqlite/ 2>/dev/null',
  'echo "=== SQLITE_FILES ==="',
  'cat /root/psvibe-sale-bot/sqlite/db_manager.py 2>/dev/null || echo "NO FILE"',
  'echo "=== SQLITE_SETUP ==="',
  'cat /root/psvibe-sale-bot/sqlite/setup.py 2>/dev/null || echo "NO FILE"',
  'echo "=== ENV ==="',
  'cat /root/psvibe-sale-bot/.env 2>/dev/null || cat /root/psvibe-sale-bot/.env.* 2>/dev/null || echo "NO ENV"',
  'echo "=== SYNC_LOG ==="',
  'tail -50 /root/psvibe-sale-bot/sync.log 2>/dev/null || echo "NO SYNC LOG"',
  'echo "=== DOCKER_COMPOSE ==="',
  'cat /root/psvibe-sale-bot/docker-compose.yml 2>/dev/null; cat /root/psvibe-sale-bot/docker-compose.yaml 2>/dev/null || echo "NO DOCKER-COMPOSE"',
  'echo "=== DOCKER_PS ==="',
  'docker ps -a 2>/dev/null || echo "NO DOCKER"',
  'echo "=== MYSQL_CHECK ==="',
  'docker exec psvibe-mysql mysql -e "SHOW DATABASES;" 2>/dev/null || echo "MYSQL_UNREACHABLE"',
  'echo "=== MYSQL_TABLES_psvibe_api ==="',
  'docker exec psvibe-mysql mysql -e "USE psvibe_api; SHOW TABLES;" 2>/dev/null || echo "NO_DB_ACCESS"',
  'echo "=== SYNC_STATUS_TABLE ==="',
  'docker exec psvibe-mysql mysql -e "USE psvibe_api; DESCRIBE sync_status;" 2>/dev/null || echo "NO_TABLE"',
  'echo "=== SYNC_STATUS_DATA ==="',
  'docker exec psvibe-mysql mysql -e "USE psvibe_api; SELECT * FROM sync_status;" 2>/dev/null || echo "NO_DATA"',
  'echo "=== OTHER_TABLES ==="',
  'docker exec psvibe-mysql mysql -e "USE psvibe_api; DESCRIBE console_status;" 2>/dev/null; docker exec psvibe-mysql mysql -e "USE psvibe_api; DESCRIBE games_library;" 2>/dev/null; docker exec psvibe-mysql mysql -e "USE psvibe_api; DESCRIBE member_wallets;" 2>/dev/null; docker exec psvibe-mysql mysql -e "USE psvibe_api; DESCRIBE staff_records;" 2>/dev/null',
  'echo "=== CONSOLE_STATUS_DATA ==="',
  'docker exec psvibe-mysql mysql -e "USE psvibe_api; SELECT * FROM console_status LIMIT 20;" 2>/dev/null || echo "NO_DATA"',
  'echo "=== MAIN_ENTRY ==="',
  'head -80 /root/psvibe-sale-bot/main.py 2>/dev/null || head -80 /root/psvibe-sale-bot/bot.py 2>/dev/null || echo "NO_MAIN"',
  'echo "=== REQ ==="',
  'cat /root/psvibe-sale-bot/requirements.txt 2>/dev/null || echo "NO_REQ"',
  'echo "=== API_DIR ==="',
  'ls -la /root/psvibe-sale-bot/api/ 2>/dev/null || echo "NO_API_DIR"',
  'echo "=== ALL_PY_IMPORTS ==="',
  'grep -rn "^import\\|^from" /root/psvibe-sale-bot/ 2>/dev/null | grep -v __pycache__ | sort -u'
];

const conn = new Client();
let output = '';
let cmdIdx = 0;

conn.on('ready', () => {
  console.log('SSH connected');
  runNext();
});

function runNext() {
  if (cmdIdx >= commands.length) {
    conn.end();
    console.log('\n=== COMPLETE ===');
    console.log(output);
    return;
  }
  conn.exec(commands[cmdIdx], (err, stream) => {
    if (err) {
      output += `\n[ERR cmd ${cmdIdx}]: ${err.message}\n`;
      cmdIdx++;
      runNext();
      return;
    }
    let data = '';
    stream.on('data', d => data += d.toString());
    stream.stderr.on('data', d => data += d.toString());
    stream.on('close', () => {
      output += data + '\n';
      cmdIdx++;
      runNext();
    });
  });
}

conn.connect({
  host: '5.223.81.16',
  username: 'root',
  privateKey: fs.readFileSync(keyPath),
  readyTimeout: 15000
});

setTimeout(() => {
  try { conn.end(); } catch(e) {}
  console.log('TIMEOUT');
  console.log(output);
  process.exit(0);
}, 30000);
