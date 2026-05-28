const { Client } = require('ssh2');
const conn = new Client();
const fs = require('fs');
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

// Simple single-line commands only
const commands = [
  { label: 'ENV_FILE', cmd: 'cat /root/psvibe-sale-bot/.env' },
  { label: 'SALES_MAIN', cmd: 'cat /root/psvibe-sale-bot/main.py 2>/dev/null | head -60' },
  { label: 'CUSTOMER_MAIN', cmd: 'cat /root/psvibe-sale-bot/customer_bot/main.py 2>/dev/null | head -60' },
  { label: 'HANDLERS', cmd: 'ls /root/psvibe-sale-bot/handlers/ 2>/dev/null; echo "==="; ls /root/psvibe-sale-bot/bot/ 2>/dev/null | head -30' },
  { label: 'APP_PY', cmd: 'head -80 /root/psvibe-sale-bot/app.py 2>/dev/null' },
  { label: 'API_DIR', cmd: 'ls -la /root/psvibe_api_server/ 2>/dev/null; echo "---"; ls /root/psvibe_api_server/*.py 2>/dev/null | head -10' },
  { label: 'API_LOG', cmd: 'cat /root/psvibe_api_server/server.log 2>/dev/null | tail -40' },
  { label: 'API_APP', cmd: 'cat /root/psvibe_api_server/app.py 2>/dev/null | head -80' },
  { label: 'MYSQL_DOCKER', cmd: "docker exec psvibe-mysql mysql -upsvibe_user -pPsVibe@User2024! -e 'SHOW DATABASES;' 2>&1; echo '==='; docker exec psvibe-mysql mysql -upsvibe_user -pPsVibe@User2024! psvibe_api -e 'SHOW TABLES;' 2>&1; echo '==='; docker exec psvibe-mysql mysql -uroot -pPsVibe@MySQL2024! -e 'SHOW DATABASES;' 2>&1" },
  { label: 'N8N_WF', cmd: "curl -s http://127.0.0.1:5678/rest/workflows 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); ws=d.get(\"data\",[]); print(f\"Count: {len(ws)}\"); [print(f\"  - {w.get(\"name\",\"?\")} (active: {w.get(\"active\")})\") for w in ws]' 2>/dev/null; echo 'N8N_FAIL'" },
  { label: 'AGRI_BOT', cmd: "find / -maxdepth 3 -name 'agri*' -type d 2>/dev/null | head -10; systemctl list-units --type=service --state=all | grep agri 2>/dev/null; echo 'DONE'" },
  { label: 'PIP_LIST', cmd: "/root/venv/bin/pip3 list 2>/dev/null | head -80" },
  { label: 'WALLET_PIP', cmd: "/root/Personal-Wallet-Tele-Bot/bot/venv/bin/pip3 list 2>/dev/null | head -80" },
  { label: 'WALLET_BOT_DIR', cmd: "cat /root/Personal-Wallet-Tele-Bot/bot/main.py 2>/dev/null | head -60" },
  { label: 'ALL_SERVICE_FILES', cmd: "for f in /etc/systemd/system/psvibe-*.service; do echo '=== $f ==='; cat \"$f\"; echo; done" },
];

let results = {};
let idx = 0;

conn.on('ready', () => { console.log('Connected'); runNext(); });

function runNext() {
  if (idx >= commands.length) { conn.end(); printResults(); return; }
  const { label, cmd } = commands[idx];
  conn.exec(cmd, (err, stream) => {
    let out = '', errOut = '';
    if (err) { results[label] = 'ERROR: ' + err.message; idx++; runNext(); return; }
    stream.on('data', (d) => out += d.toString());
    stream.stderr.on('data', (d) => errOut += d.toString());
    stream.on('close', () => { results[label] = (out || errOut || '(empty)').slice(0,3000); idx++; runNext(); });
  });
}

function printResults() {
  const keys = ['ENV_FILE','SALES_MAIN','CUSTOMER_MAIN','HANDLERS','API_DIR','API_LOG','API_APP','MYSQL_DOCKER','N8N_WF','AGRI_BOT','PIP_LIST','WALLET_PIP','WALLET_BOT_DIR','ALL_SERVICE_FILES'];
  let all = '';
  for (const k of keys) {
    const v = results[k] || '(no result)';
    all += '\n========== ' + k + ' ==========\n' + v;
    console.log('\n### ' + k + ':');
    console.log(v.slice(0,1200));
  }
  fs.writeFileSync('/home/node/.openclaw/workspace/vps_detail2.txt', all);
}

conn.connect({ host: '5.223.81.16', username: 'root', privateKey: key, readyTimeout: 15000 });
