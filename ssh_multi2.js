const { Client } = require('ssh2');
const fs = require('fs');

const COMMANDS = [
  // 1. rest of sheets_client.py
  'cat /root/psvibe_api_server/sheets_client.py',
  // 2. How services run
  'ps aux | grep -v grep | grep -E "psvibe|python|uvicorn|sync"',
  // 3. Find the API/uvicorn process
  'netstat -tlnp 2>/dev/null | grep -E "8000|5000|8080" || ss -tlnp | grep -E "8000|5000|8080"',
  // 4. Bot main file - how it starts
  'head -100 /root/psvibe-sales-bot/bot/app.py',
  // 5. Customer bot main - how it starts
  'cat /root/psvibe-sales-bot/customer_bot/main.py',
  // 6. Bot members handler
  'head -100 /root/psvibe-sales-bot/bot/handlers/members.py',
  // 7. Bot wallet/data access patterns
  'rg -n "get_member\|get_wallet\|balance\|member_data\|Member\|sheet\|worksheet" /root/psvibe-sales-bot/bot/handlers/members.py 2>/dev/null',
  // 8. How bot accesses data - grep for calls
  'rg -rn "googleapiclient\|gspread\|build_spreadsheet\|service_account\|Spreadsheet\|open_by_key\|worksheet" /root/psvibe-sales-bot/ --include "*.py" 2>/dev/null | head -30',
  // 9. Bot config file
  'find /root/psvibe-sales-bot/ -name "config*" -o -name ".env" | head -10',
  // 10. Bot .env or config
  'find /root/psvibe-sales-bot/ -maxdepth 2 -name ".env" -o -name "config.py" -o -name "settings.py" | xargs -I{} sh -c "echo === {} ===; head -50 {}"',
  // 11. API logs (any)
  'journalctl --no-pager -n 100 2>&1 | grep -i "429\|quota\|sheets\|gspread\|psvibe\|api" | tail -30',
  // 12. Where is the uvicorn command
  'cat /root/psvibe-sales-bot/start.sh 2>/dev/null; cat /root/psvibe-sales-bot/run.sh 2>/dev/null; find /root/ -name "*.service" | head -10',
  // 13. Customer bot handlers
  'cat /root/psvibe-sales-bot/customer_bot/handlers.py',
  // 14. Customer bot API module
  'cat /root/psvibe-sales-bot/customer_bot/api.py',
  // 15. Check MySQL service
  'systemctl status mysql 2>&1; systemctl status mariadb 2>&1; which mysqld 2>&1; ls /etc/mysql/ 2>/dev/null',
  // 16. API server full app.py - routes section
  'rg -n "@app\.\|def .*api\|B30\|allowed_user\|setting.*tab\|SETTING" /root/psvibe_api_server/app.py 2>/dev/null | head -40',
  // 17. Full sync_service.py - key parts
  'rg -n "def sync_\|CREATE TABLE\|TABLE\|member\|wallet\|setting" /root/psvibe_api_server/sync_service.py 2>/dev/null | head -30',
  // 18. Bot main menu/general data access
  'rg -n "import\|from" /root/psvibe-sales-bot/bot/handlers/sales.py 2>/dev/null | head -20',
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
    const out = results[i] || 'NO OUTPUT';
    console.log(out.substring(0, 5000));
  }
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
