const { Client } = require('ssh2');
const conn = new Client();
const fs = require('fs');
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  { label: 'SALES_BOT_DIR', cmd: 'ls -la /root/psvibe-sale-bot/ 2>/dev/null || echo "NOT_FOUND"' },
  { label: 'SALES_BOT_STRUCTURE', cmd: 'find /root/psvibe-sale-bot -maxdepth 2 -type f -name "*.py" | head -50; echo "---"; find /root/psvibe-sale-bot -maxdepth 2 -type d | sort' },
  { label: 'CUSTOMER_BOT_DIR', cmd: 'ls -la /root/psvibe-sale-bot/customer_bot/ 2>/dev/null | head -30' },
  
  { label: 'SALES_CONFIG_FILES', cmd: 'find /root/psvibe-sale-bot -name "config*" -o -name ".env" -o -name "*.env" -o -name "settings*" -o -name "credentials*" -o -name "token*" -o -name "secret*" 2>/dev/null | grep -v __pycache__ | head -20' },
  { label: 'WALLET_CONFIG_FILES', cmd: 'find /root/Personal-Wallet-Tele-Bot -name "config*" -o -name ".env" -o -name "*.env" -o -name "settings*" -o -name "credentials*" -o -name "token*" -o -name "secret*" 2>/dev/null | grep -v __pycache__ | head -20' },
  
  { label: 'SALES_MAIN_HEAD', cmd: 'head -60 /root/psvibe-sale-bot/main.py 2>/dev/null' },
  { label: 'CUSTOMER_MAIN_HEAD', cmd: 'head -60 /root/psvibe-sale-bot/customer_bot/main.py 2>/dev/null' },
  { label: 'WALLET_MAIN_HEAD', cmd: 'head -60 /root/Personal-Wallet-Tele-Bot/bot/main.py 2>/dev/null' },
  
  { label: 'DOCKER_COMPOSE', cmd: 'cat /root/docker-compose.yml 2>/dev/null | head -100 || echo "NO_FILE"' },
  { label: 'MYSQL_ENV', cmd: 'docker exec psvibe-mysql env 2>/dev/null | grep -iE "PASS|ROOT|USER|PASSWORD|DATABASE" | head -10 || echo "DOCKER_EXEC_FAIL"' },
  { label: 'MYSQL_DATABASES', cmd: 'docker exec psvibe-mysql mysql -u root -p"$(docker inspect psvibe-mysql 2>/dev/null | grep -A5 MYSQL_ROOT_PASSWORD | grep -oP "(?<==).*" | tr -d "\"\", " | head -1)" -e "SHOW DATABASES;" 2>/dev/null || docker exec psvibe-mysql mysql -u root -e "SHOW DATABASES;" 2>/dev/null || echo "MYSQL_AUTH_FAIL"' },
  { label: 'MYSQL_USERS', cmd: 'docker exec psvibe-mysql mysql -u root -e "SELECT User, Host FROM mysql.user;" 2>/dev/null || echo "MYSQL_USERS_FAIL"' },
  
  { label: 'GSHEET_REFS_SALES', cmd: 'grep -rn "gspread\|sheets\|sheet\|spreadsheet\|google.*sheet\|GOOGLE_SHEET\|SHEET_ID\|spreadsheet_id\|SHEET_NAME\|worksheet" /root/psvibe-sale-bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -30' },
  { label: 'GSHEET_REFS_WALLET', cmd: 'grep -rn "gspread\|sheets\|sheet\|spreadsheet\|google.*sheet\|GOOGLE_SHEET\|SHEET_ID\|spreadsheet_id\|SHEET_NAME\|worksheet" /root/Personal-Wallet-Tele-Bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -30' },
  
  { label: 'MYSQL_REFS_SALES', cmd: 'grep -rn "mysql\|pymysql\|mysql.connector\|sqlalchemy\|database.*url\|DB_HOST\|DB_USER\|DB_PASS\|DATABASE_URL\|db_host\|db_user\|db_password\|MYSQL_\|aiomysql\|asyncmy" /root/psvibe-sale-bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -30' },
  { label: 'MYSQL_REFS_WALLET', cmd: 'grep -rn "mysql\|pymysql\|mysql.connector\|sqlalchemy\|database.*url\|DB_HOST\|DB_USER\|DB_PASS\|DATABASE_URL\|db_host\|db_user\|db_password\|MYSQL_\|aiomysql\|asyncmy" /root/Personal-Wallet-Tele-Bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -30' },
  
  { label: 'API_REFS_SALES', cmd: 'grep -rn "requests\.\(get\|post\|put\|delete\)\|httpx\|aiohttp\|urllib\|api\.\|API_URL\|api_url\|API_KEY\|api_key\|BOT_TOKEN\|bot_token\|TELEGRAM_TOKEN\|telegram_token\|token =" /root/psvibe-sale-bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -40' },
  { label: 'API_REFS_WALLET', cmd: 'grep -rn "requests\.\(get\|post\|put\|delete\)\|httpx\|aiohttp\|urllib\|api\.\|API_URL\|api_url\|API_KEY\|api_key\|BOT_TOKEN\|bot_token\|TELEGRAM_TOKEN\|telegram_token\|token =" /root/Personal-Wallet-Tele-Bot/ 2>/dev/null | grep -v __pycache__ | grep -v ".pyc" | head -40' },
  
  { label: 'SERVICE_FILES', cmd: 'for f in /etc/systemd/system/psvibe-*.service; do echo "=== $f ==="; cat "$f" 2>/dev/null; done; echo "=== psvibe_customer_bot ==="; cat /etc/systemd/system/psvibe_customer_bot.service 2>/dev/null || echo "NOT_FOUND"' },
  
  { label: 'VENV_CHECK', cmd: 'ls /root/venv/bin/python3 2>/dev/null && /root/venv/bin/pip3 list 2>/dev/null | grep -iE "gspread|google|mysql|pymysql|sqlalchemy|requests|httpx|aiohttp|telegram|python-telegram" | head -20 || echo "VENV_NOT_FOUND"' },
  { label: 'WALLET_VENV_CHECK', cmd: 'ls /root/Personal-Wallet-Tele-Bot/bot/venv/bin/python3 2>/dev/null && /root/Personal-Wallet-Tele-Bot/bot/venv/bin/pip3 list 2>/dev/null | grep -iE "gspread|google|mysql|pymysql|sqlalchemy|requests|httpx|aiohttp|telegram|python-telegram" | head -20 || echo "WALLET_VENV_NOT_FOUND"' },
  
  { label: 'N8N_WEBHOOKS', cmd: 'curl -s -H "accept: application/json" http://127.0.0.1:5678/rest/workflows 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); ws=d.get(\"data\",[]); print(f\"Workflows: {len(ws)}\"); [print(f\"  - {w.get(\"name\",\"?\")}\") for w in ws]" 2>/dev/null || echo "N8N_API_FAIL"' },
  
  // Test API endpoints
  { label: 'TEST_SALES_BOT_API', cmd: 'curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:8080/health 2>/dev/null || curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:5000/ 2>/dev/null || echo "HEALTH_CHECK_FAIL"' },
  { label: 'TEST_API_SERVICE', cmd: 'journalctl -u psvibe-api.service --no-pager -n 20 2>/dev/null | tail -20' },
  { label: 'TEST_SALES_LOGS', cmd: 'journalctl -u psvibe-sale-bot.service --no-pager -n 20 2>/dev/null | tail -20' },
  { label: 'TEST_CUSTOMER_LOGS', cmd: 'journalctl -u psvibe_customer_bot.service --no-pager -n 20 2>/dev/null | tail -20' },
  { label: 'TEST_WALLET_LOGS', cmd: 'journalctl -u psvibe-wallet.service --no-pager -n 20 2>/dev/null | tail -20' },
];

let results = {};
let idx = 0;

conn.on('ready', () => {
  console.log('Connected');
  runNext();
});

function runNext() {
  if (idx >= commands.length) {
    conn.end();
    printResults();
    return;
  }
  const { label, cmd } = commands[idx];
  conn.exec(cmd, (err, stream) => {
    let out = '';
    let errOut = '';
    if (err) { results[label] = 'ERROR: ' + err.message; idx++; runNext(); return; }
    stream.on('data', (d) => out += d.toString());
    stream.stderr.on('data', (d) => errOut += d.toString());
    stream.on('close', () => { results[label] = (out || errOut || '(empty)').slice(0,2500); idx++; runNext(); });
  });
}

function printResults() {
  let all = '';
  for (const { label } of commands) {
    all += '\n========== ' + label + ' ==========\n' + (results[label] || '(no result)');
  }
  fs.writeFileSync('/home/node/.openclaw/workspace/vps_detail.txt', all);
  console.log('Done. Written to vps_detail.txt');
  
  // Print key findings to stdout
  const keys = ['SALES_BOT_DIR','CUSTOMER_BOT_DIR','SALES_CONFIG_FILES','WALLET_CONFIG_FILES',
    'MYSQL_DATABASES','MYSQL_ENV','DOCKER_COMPOSE','VENV_CHECK','WALLET_VENV_CHECK',
    'SERVICE_FILES','TEST_API_SERVICE','TEST_SALES_LOGS','TEST_CUSTOMER_LOGS','TEST_WALLET_LOGS'];
  for (const k of keys) {
    console.log('\n### ' + k + ':');
    const v = (results[k] || '').slice(0,1200);
    console.log(v);
  }
}

conn.connect({ host: '5.223.81.16', username: 'root', privateKey: key, readyTimeout: 15000 });
