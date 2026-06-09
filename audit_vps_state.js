const { Client } = require('ssh2');
const conn = new Client();
const fs = require('fs');

const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  { label: 'SYSTEMD_SERVICES', cmd: 'systemctl list-units --type=service --state=running | grep -iE "bot|psvibe|agri|n8n|caddy|mysql|mariadb|postgres|pm2"' },
  { label: 'DOCKER_PS', cmd: 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "NO_DOCKER"' },
  { label: 'PROCESSES', cmd: 'ps aux | grep -iE "python.*bot|node.*bot|telegram" | grep -v grep || echo "NO_BOT_PROCS"' },
  { label: 'MYSQL_DBS', cmd: `mysql -e "SHOW DATABASES;" 2>/dev/null || mysql -e "SHOW DATABASES;" 2>/dev/null || mariadb -e "SHOW DATABASES;" 2>/dev/null || echo "MYSQL_FAIL"` },
  { label: 'MYSQL_TABLES', cmd: `for db in $(mysql -e "SHOW DATABASES;" 2>/dev/null | grep -vE "^(Database|information_schema|performance_schema|mysql|sys)$"); do echo "=== DB: $db ==="; mysql -e "USE $db; SHOW TABLES;" 2>/dev/null; done || echo "MYSQL_TABLES_FAIL"` },
  { label: 'SALES_BOT_DIR', cmd: 'ls -la /root/Sales-Tele-Bot/ 2>/dev/null | head -40' },
  { label: 'AGRI_BOT_DIR', cmd: 'ls -la /root/agri-bot/ 2>/dev/null | head -40' },
  { label: 'WALLET_BOT_DIR', cmd: 'ls -la /root/Personal-Wallet-Tele-Bot/ 2>/dev/null | head -40' },
  { label: 'SALES_CONFIG', cmd: 'cat /root/Sales-Tele-Bot/config.py 2>/dev/null | grep -v "^#" | grep -v "^$" | head -40 || echo "NO_SALES_CONFIG"' },
  { label: 'AGRI_CONFIG', cmd: 'cat /root/agri-bot/config.py 2>/dev/null | grep -v "^#" | grep -v "^$" | head -40 || echo "NO_AGRI_CONFIG"' },
  { label: 'WALLET_CONFIG', cmd: 'cat /root/Personal-Wallet-Tele-Bot/config.py 2>/dev/null | grep -v "^#" | grep -v "^$" | head -40 || echo "NO_WALLET_CONFIG"' },
  { label: 'SALES_ENV', cmd: 'cat /root/Sales-Tele-Bot/.env 2>/dev/null | grep -v "^#" | grep -v "^$" | head -20 || echo "NO_SALES_ENV"' },
  { label: 'AGRI_ENV', cmd: 'cat /root/agri-bot/.env 2>/dev/null | grep -v "^#" | grep -v "^$" | head -20 || echo "NO_AGRI_ENV"' },
  { label: 'WALLET_ENV', cmd: 'cat /root/Personal-Wallet-Tele-Bot/.env 2>/dev/null | grep -v "^#" | grep -v "^$" | head -20 || echo "NO_WALLET_ENV"' },
  { label: 'SALES_MAIN_CHECK', cmd: 'wc -l /root/Sales-Tele-Bot/main.py 2>/dev/null || echo "NO_MAIN_PY"; ls /root/Sales-Tele-Bot/handlers/ 2>/dev/null || echo "NO_HANDLERS_DIR"' },
  { label: 'AGRI_MAIN_CHECK', cmd: 'wc -l /root/agri-bot/main.py 2>/dev/null || echo "NO_MAIN_PY"; ls /root/agri-bot/handlers/ 2>/dev/null || echo "NO_HANDLERS_DIR"' },
  { label: 'WALLET_MAIN_CHECK', cmd: 'wc -l /root/Personal-Wallet-Tele-Bot/main.py 2>/dev/null || echo "NO_MAIN_PY"' },
  { label: 'SALES_SERVICE', cmd: 'systemctl status psvibe-bot.service 2>/dev/null | head -15 || echo "NO_PSVIBE_SERVICE"; systemctl status sales-tele-bot.service 2>/dev/null | head -15 || echo "NO_SALES_SERVICE"' },
  { label: 'AGRI_SERVICE', cmd: 'systemctl status agri-bot.service 2>/dev/null | head -15 || echo "NO_AGRI_SERVICE"' },
  { label: 'WALLET_SERVICE', cmd: 'systemctl status wallet-bot.service 2>/dev/null | head -15 || echo "NO_WALLET_SERVICE"' },
  { label: 'CERTBOT_CERTS', cmd: 'certbot certificates 2>/dev/null | head -20 || echo "NO_CERTBOT"' },
  { label: 'N8N_CHECK', cmd: 'systemctl status n8n 2>/dev/null | head -10 || echo "NO_N8N_SERVICE"; docker ps 2>/dev/null | grep n8n || echo "NO_N8N_DOCKER"' },
  { label: 'NGINX_SITES', cmd: 'ls /etc/nginx/sites-enabled/ 2>/dev/null | head -20 || echo "NO_NGINX_SITES"; ls /etc/caddy/ 2>/dev/null | head -20 || echo "NO_CADDY_DIR"' },
  { label: 'CRONTAB', cmd: 'crontab -l 2>/dev/null | head -30 || echo "NO_CRONTAB"' },
  { label: 'DISK_MEM', cmd: 'df -h / | tail -1; free -h | grep Mem; uptime' },
  { label: 'HOSTNAME_OS', cmd: 'uname -a; cat /etc/os-release | head -5' },
];

let results = {};
let idx = 0;

conn.on('ready', () => {
  console.log('SSH Connected!');
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
    if (err) {
      results[label] = `ERROR: ${err.message}`;
      idx++;
      runNext();
      return;
    }
    stream.on('data', (d) => { out += d.toString(); });
    stream.stderr.on('data', (d) => { errOut += d.toString(); });
    stream.on('close', () => {
      results[label] = out || errOut || '(empty)';
      idx++;
      runNext();
    });
  });
}

function printResults() {
  for (const { label } of commands) {
    console.log(`\n========== ${label} ==========`);
    console.log(results[label] || '(no result)');
  }
}

conn.connect({
  host: '5.223.81.16',
  username: 'root',
  privateKey: key,
  readyTimeout: 15000,
});
