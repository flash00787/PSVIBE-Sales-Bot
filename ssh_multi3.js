const { Client } = require('ssh2');
const fs = require('fs');

const COMMANDS = [
  // 1. Bot __init__.py - the data layer
  'cat /root/psvibe-sales-bot/bot/__init__.py',
  // 2. app.py - search for B30, allowed_user, setting
  'cat /root/psvibe_api_server/app.py | grep -n "B30\|allowed_user\|SETTING\|setting_tab\|Setting\|get_setting\|fetch_allowed" ',
  // 3. app.py GET routes
  'cat /root/psvibe_api_server/app.py | grep -n "@app\.\|async def\|def " | head -80',
  // 4. sync_service full key functions
  'cat /root/psvibe_api_server/sync_service.py | grep -n "def sync_\|def start_\|def stop_\|CREATE TABLE\|class Sync" ',
  // 5. API server process details
  'cat /proc/748923/cmdline 2>/dev/null | tr "\\0" " "; echo; ls -la /root/psvibe_api_server/start*.sh 2>/dev/null; cat /root/psvibe_api_server/start*.sh 2>/dev/null; find /root/ -name "*psvibe*" -path "*/systemd*" 2>/dev/null',
  // 6. Member data path in app.py
  'cat /root/psvibe_api_server/app.py | grep -n "member\|wallet\|mysql_query\|get_member" | head -40',
  // 7. Customer bot api.py cache constants
  'grep -n "_CACHE_TTL\|cache\|_fetch_\|API_BASE\|def _api_" /root/psvibe-sales-bot/customer_bot/api.py',
  // 8. Bot __init__ key functions
  'grep -n "def \|_load_\|_get_\|_bg_\|fetch_\|SHEET\|\\.env\|gspread\|service_account\|worksheet\|spreadsheet" /root/psvibe-sales-bot/bot/__init__.py | head -40',
  // 9. API logs for uvicorn
  'cat /root/psvibe_api_server/nohup.out 2>/dev/null | tail -50; ls /root/psvibe_api_server/*.log 2>/dev/null',
  // 10. Bot logging
  'cat /root/psvibe-sales-bot/nohup.out 2>/dev/null | tail -50; ls /root/psvibe-sales-bot/*.log 2>/dev/null',
  // 11. B30 in sheets_client or app.py
  'grep -rn "B30\|B29\|B31\|allowed_user\|ALLOWED_USER" /root/psvibe_api_server/ --include "*.py" 2>/dev/null | head -20',
  // 12. app.py endpoints list full
  'cat /root/psvibe_api_server/app.py | grep -n "@app\.\|async def \|def " | head -120',
  // 13. API server env vars
  'cat /root/psvibe_api_server/.env 2>/dev/null; cat /etc/psvibe/secrets.env 2>/dev/null',
];

const results = [];

function runCmd(client, cmd, idx) {
  return new Promise((resolve) => {
    client.exec(cmd, (err, stream) => {
      if (err) { results[idx] = 'ERR:' + err.message; resolve(); return; }
      let out = '';
      stream.on('data', d => out += d.toString());
      stream.stderr.on('data', d => out += d.toString());
      stream.on('close', () => { results[idx] = out; resolve(); });
    });
  });
}

const conn = new Client();
conn.on('ready', async () => {
  console.log('Connected. Running', COMMANDS.length, 'commands...');
  for (let i = 0; i < COMMANDS.length; i += 6) {
    const batch = [];
    for (let j = i; j < i+6 && j < COMMANDS.length; j++) {
      batch.push(runCmd(conn, COMMANDS[j], j));
    }
    await Promise.all(batch);
    console.log('Batch', i/6+1, 'done');
  }
  conn.end();
}).on('error', (err) => { console.log('ERR:' + err.message); }).on('close', () => {
  for (let i = 0; i < COMMANDS.length; i++) {
    console.log('\n=== COMMAND', i+1, '===');
    console.log('CMD:', COMMANDS[i].substring(0, 200));
    console.log((results[i] || 'NO OUTPUT').substring(0, 5000));
  }
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
