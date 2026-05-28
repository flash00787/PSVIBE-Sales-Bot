const { Client } = require('ssh2');
const conn = new Client();
const fs = require('fs');
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  { label: 'ENV_FILE', cmd: 'cat /root/psvibe-sale-bot/.env 2>/dev/null || echo "NO_ENV"' },
  { label: 'SALES_MAIN', cmd: 'cat /root/psvibe-sale-bot/main.py 2>/dev/null || echo "NO_FILE"' },
  { label: 'SALES_APP_PY', cmd: 'head -100 /root/psvibe-sale-bot/app.py 2>/dev/null || echo "NO_FILE"' },
  { label: 'CUSTOMER_MAIN', cmd: 'cat /root/psvibe-sale-bot/customer_bot/main.py 2>/dev/null || echo "NO_FILE"' },
  { label: 'WALLET_MAIN', cmd: 'cat /root/Personal-Wallet-Tele-Bot/bot/main.py 2>/dev/null | head -100 || echo "NO_FILE"' },
  { label: 'API_SERVER_CHECK', cmd: 'ls -la /root/psvibe_api_server/ 2>/dev/null; echo "---"; ls /root/psvibe_api_server/*.py 2>/dev/null | head -10; echo "---"; cat /root/psvibe_api_server/server.log 2>/dev/null | tail -30 || echo "NO_LOG"; echo "---"; cat /root/psvibe_api_server/app.py 2>/dev/null | head -80 || echo "NO_APP"' },
  { label: 'MYSQL_FROM_DOCKER', cmd: 'docker exec psvibe-mysql mysql -upsvibe_user -p"PsVibe@User2024!" -e "SHOW DATABASES;" 2>/dev/null; echo "---"; docker exec psvibe-mysql mysql -upsvibe_user -p"PsVibe@User2024!" psvibe_api -e "SHOW TABLES;" 2>/dev/null; echo "---"; docker exec psvibe-mysql mysql -u root -p"PsVibe@MySQL2024!" -e "SHOW DATABASES;" 2>/dev/null' },
  { label: 'N8N_WORKFLOWS', cmd: 'curl -s http://127.0.0.1:5678/rest/workflows 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); ws=d.get(\"data\",[]); print(f\"Count: {len(ws)}\"); [print(f\"  - {w.get(\"name\",\"?\")} (active: {w.get(\"active\")})\") for w in ws]" 2>/dev/null || echo "N8N_FAIL"' },
  { label: 'N8N_CREDENTIALS', cmd: 'curl -s http://127.0.0.1:5678/rest/credentials 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); cs=d.get(\"data\",[]); print(f\"Credentials: {len(cs)}\"); [print(f\"  - {c.get(\"name\",\"?\")} ({c.get(\"type\",\"?\")})\") for c in cs]" 2>/dev/null || echo "N8N_CRED_FAIL"' },
  { label: 'API_LOG_DETAIL', cmd: 'cat /root/psvibe_api_server/server.log 2>/dev/null | tail -50 || echo "NO_LOG"' },
  { label: 'SERVICE_FILE_FULL', cmd: 'for f in /etc/systemd/system/psvibe-*.service; do echo "=== $f ==="; cat "$f"; echo; done' },
  { label: 'GSHEET_ACCESS_TEST', cmd: 'cd /root/psvibe-sale-bot && /root/venv/bin/python3 -c "
try:
    import gspread
    from google.oauth2.service_account import Credentials
    scope = [\"https://www.googleapis.com/auth/spreadsheets\", \"https://www.googleapis.com/auth/drive\"]
    creds = Credentials.from_service_account_file(\"/root/psvibe_api_server/service_account.json\", scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(\"1VFNvhdcYVlVrr5TS49n2peIZa3U6y_AI-Mfo7q7gVsA\")
    print(f\"Sheet name: {sheet.title}\")
    worksheets = sheet.worksheets()
    print(f\"Worksheets: {len(worksheets)}\")
    for ws in worksheets:
        print(f\"  - {ws.title} ({ws.row_count}x{ws.col_count})\")
except Exception as e:
    print(f\"GSHEET_ERROR: {e}\")
" 2>&1' },
  { label: 'WALLET_GSHEET_TEST', cmd: 'cd /root/Personal-Wallet-Tele-Bot && /root/Personal-Wallet-Tele-Bot/bot/venv/bin/python3 -c "
try:
    import gspread
    from google.oauth2.service_account import Credentials
    import json, os
    # Try loading SA from various locations
    for p in [\"/root/psvibe_api_server/service_account.json\", \"/root/Personal-Wallet-Tele-Bot/service_account.json\", \"/root/psvibe-sale-bot/service_account.json\"]:
        if os.path.exists(p):
            print(f\"Found SA: {p}\")
            try:
                scope = [\"https://www.googleapis.com/auth/spreadsheets\"]
                creds = Credentials.from_service_account_file(p, scopes=scope)
                client = gspread.authorize(creds)
                sheets = client.openall()
                print(f\"Accessible sheets: {len(sheets)}\")
                for s in sheets:
                    print(f\"  - {s.title}\")
                break
            except Exception as e:
                print(f\"  Error: {e}\")
    else:
        print(\"NO_SA_FILE_FOUND\")
except Exception as e:
    print(f\"WALLET_GSHEET_ERROR: {e}\")
" 2>&1' },
  { label: 'FULL_PIP_LIST', cmd: '/root/venv/bin/pip3 list 2>/dev/null | head -60; echo "==="; /root/Personal-Wallet-Tele-Bot/bot/venv/bin/pip3 list 2>/dev/null | head -60' },
  { label: 'AGRI_BOT_CHECK', cmd: 'find / -maxdepth 3 -name "agri*" -type d 2>/dev/null | head -10; find / -maxdepth 4 -name "agri*" -type f 2>/dev/null | head -10; systemctl list-units --type=service --state=all | grep agri 2>/dev/null || echo "NO_AGRI_SERVICE"' },
  { label: 'HANDLERS_CHECK', cmd: 'ls /root/psvibe-sale-bot/handlers/ 2>/dev/null; echo "---"; ls /root/psvibe-sale-bot/bot/ 2>/dev/null | head -30' },
];

let results = {};
let idx = 0;

conn.on('ready', () => {
  console.log('Connected');
  runNext();
});

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
  let all = '';
  for (const { label } of commands) {
    all += '\n========== ' + label + ' ==========\n' + (results[label] || '(no result)');
  }
  fs.writeFileSync('/home/node/.openclaw/workspace/vps_detail2.txt', all);
  // Print key findings
  const keys = ['ENV_FILE','SALES_MAIN','API_SERVER_CHECK','MYSQL_FROM_DOCKER','GSHEET_ACCESS_TEST',
    'WALLET_GSHEET_TEST','FULL_PIP_LIST','AGRI_BOT_CHECK','API_LOG_DETAIL','N8N_WORKFLOWS','HANDLERS_CHECK'];
  for (const k of keys) {
    console.log('\n### ' + k + ':');
    console.log((results[k] || '').slice(0,1500));
  }
}

conn.connect({ host: '5.223.81.16', username: 'root', privateKey: key, readyTimeout: 15000 });
