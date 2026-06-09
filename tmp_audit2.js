const { Client } = require('ssh2');
const fs = require('fs');

const commands = [
  'echo "=== SQLITE_DB_MANAGER ==="',
  'cat /root/psvibe-sale-bot/sqlite/db_manager.py',
  'echo "=== SQLITE_SETUP ==="',
  'cat /root/psvibe-sale-bot/sqlite/setup.py',
  'echo "=== SYNC_CRON ==="',
  'cat /root/psvibe-sale-bot/sqlite/sync_cron.sh',
  'echo "=== ENV ==="',
  'cat /root/psvibe-sale-bot/.env 2>/dev/null; cat /root/psvibe-sale-bot/.env.* 2>/dev/null; cat /root/psvibe-sale-bot/.env.sale* 2>/dev/null || echo "NO_ENV_FILE"',
  'echo "=== SYNC_LOG ==="',
  'tail -100 /root/psvibe-sale-bot/sync.log 2>/dev/null || echo "NO_SYNC_LOG"',
  'echo "=== MYSQL_TABLES ==="',
  'docker exec psvibe-mysql mysql -e "USE psvibe_api; SHOW TABLES; SELECT * FROM sync_status; SELECT * FROM console_status;" 2>/dev/null || echo "MYSQL_ERR"',
  'echo "=== MYSQL_OTHER_TABLES ==="',
  'docker exec psvibe-mysql mysql -e "USE psvibe_api; DESCRIBE member_wallets; DESCRIBE staff_records; DESCRIBE games_library;" 2>/dev/null || echo "MYSQL_ERR"',
  'echo "=== MYSQL_GAMES_DATA ==="',
  'docker exec psvibe-mysql mysql -e "USE psvibe_api; SELECT * FROM games_library LIMIT 10;" 2>/dev/null || echo "MYSQL_ERR"',
  'echo "=== MYSQL_MEMBERS_DATA ==="',
  'docker exec psvibe-mysql mysql -e "USE psvibe_api; SELECT * FROM member_wallets LIMIT 10;" 2>/dev/null || echo "MYSQL_ERR"',
  'echo "=== BOT_INIT_GSHEET ==="',
  'grep -n "gspread\\|sheet\\|SHEET\\|SHEET_ID\\|GOOGLE" /root/psvibe-sale-bot/bot/__init__.py | head -40',
  'echo "=== API_SERVER ==="',
  'grep -rn "localhost:3000\\|localhost:8000\\|PORT\\|uvicorn\\|fastapi\\|flask" /root/psvibe-sale-bot/bot/__init__.py | head -20',
  'echo "=== CUSTOMER_API ==="',
  'cat /root/psvibe-sale-bot/customer_bot/api.py',
  'echo "=== DOCKER_COMPOSE ==="',
  'cat /root/psvibe-sale-bot/docker-compose.yml 2>/dev/null; cat /root/psvibe-sale-bot/docker-compose.yaml 2>/dev/null; echo "==="; ls /root/psvibe-sale-bot/docker* 2>/dev/null || echo "NO_DOCKER_FILES"',
  'echo "=== REQUIREMENTS ==="',
  'cat /root/psvibe-sale-bot/requirements.txt 2>/dev/null || echo "NO_REQ"',
  'echo "=== DOCKER_MYSQL_DETAILS ==="',
  'docker inspect psvibe-mysql --format "{{json .Config.Env}}" 2>/dev/null; echo "==="; docker inspect psvibe-mysql --format "{{json .Mounts}}" 2>/dev/null',
  'echo "=== DOCKER_OTHER ==="',
  'docker ps --format "table {{.Names}}\\t{{.Image}}\\t{{.Status}}\\t{{.Ports}}" 2>/dev/null || echo "NO_DOCKER"',
  'echo "=== PROCESS_CHECK ==="',
  'ps aux | grep -E "python|uvicorn|gunicorn" | grep -v grep | head -20',
  'echo "=== SYNC_STATUS_DETAIL ==="',
  'docker exec psvibe-mysql mysql -e "USE psvibe_api; DESCRIBE sync_status; SELECT * FROM sync_status;" 2>/dev/null || echo "ERR"'
];

const conn = new Client();
let output = '';
let cmdIdx = 0;

conn.on('ready', () => {
  runNext();
});

function runNext() {
  if (cmdIdx >= commands.length) {
    conn.end();
    setTimeout(() => {
      console.log(output);
      process.exit(0);
    }, 500);
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
    stream.stderr.on('data', d => data += '[STDERR] ' + d.toString());
    stream.on('close', () => {
      output += data + '\n---\n';
      cmdIdx++;
      runNext();
    });
  });
}

conn.on('error', e => {
  console.log('CONN_ERR:', e.message);
  process.exit(1);
});

conn.connect({
  host: '5.223.81.16',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});

setTimeout(() => {
  try { conn.end(); } catch(e) {}
  console.log(output);
  process.exit(0);
}, 60000);
