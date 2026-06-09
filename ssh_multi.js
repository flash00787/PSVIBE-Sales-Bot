const { Client } = require('ssh2');
const fs = require('fs');

const COMMANDS = [
  // 1. sheets_client.py
  'cat /root/psvibe_api_server/sheets_client.py',
  // 2. mysql_db.py
  'cat /root/psvibe_api_server/mysql_db.py',
  // 3. app.py
  'cat /root/psvibe_api_server/app.py',
  // 4. sync_service.py
  'cat /root/psvibe_api_server/sync_service.py',
  // 5. config.py
  'cat /root/psvibe_api_server/config.py',
  // 6. db_client.py
  'cat /root/psvibe_api_server/db_client.py',
  // 7. MySQL tables
  'mysql -u psvibe_user -p"PsVibe@2026_Rotated!" psvibe_api -e "SHOW TABLES;" 2>&1',
  // 8. MySQL describe all tables
  'for t in $(mysql -u psvibe_user -p"PsVibe@2026_Rotated!" psvibe_api -N -e "SHOW TABLES;"); do echo "=== $t ==="; mysql -u psvibe_user -p"PsVibe@2026_Rotated!" psvibe_api -e "DESCRIBE $t;" 2>&1; done',
  // 9. Sales bot directory
  'find /root/psvibe-sales-bot/bot/ -name "*.py" | head -30',
  // 10. Customer bot directory
  'find /root/psvibe-sales-bot/customer_bot/ -name "*.py" | head -30',
  // 11. Bot data source files
  'rg -l "sheets_client\|google_sheets\|gspread\|GSheet\|googleapis\|spreadsheet" /root/psvibe-sales-bot/ --include "*.py" 2>/dev/null | head -20',
  // 12. Bot API usage
  'rg -l "requests\.\|api_server\|psvibe_api\|http://.*:5000\|localhost:5000\|api.psvibe" /root/psvibe-sales-bot/ --include "*.py" 2>/dev/null | head -20',
  // 13. Sync service status
  'systemctl status sync_service 2>&1; systemctl status psvibe_api 2>&1',
  // 14. API logs for 429 errors
  'journalctl -u psvibe_api --no-pager -n 200 2>&1 | grep -i "429\|quota\|rate.limit\|RESOURCE_EXHAUSTED" | tail -30',
  // 15. Sync service logs
  'journalctl -u sync_service --no-pager -n 100 2>&1 | tail -30',
  // 16. models.py
  'cat /root/psvibe_api_server/models.py',
  // 17. dashboard_bot.py
  'cat /root/psvibe_api_server/dashboard_bot.py',
  // 18. Row counts in MySQL
  'for t in $(mysql -u psvibe_user -p"PsVibe@2026_Rotated!" psvibe_api -N -e "SHOW TABLES;"); do cnt=$(mysql -u psvibe_user -p"PsVibe@2026_Rotated!" psvibe_api -N -e "SELECT COUNT(*) FROM \`$t\`;"); echo "$t: $cnt rows"; done',
  // 19. Check for caching
  'rg -r -l "cache\|lru_cache\|ttl\|redis\|Cache" /root/psvibe_api_server/ --include "*.py" 2>/dev/null',
  // 20. API usage in bots
  'rg -r "import.*api\|from.*api\|API_BASE\|API_URL\|api_url\|base_url" /root/psvibe-sales-bot/ --include "*.py" -n 2>/dev/null | head -40',
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
  // Run in parallel batches of 5
  for (let i = 0; i < COMMANDS.length; i += 5) {
    const batch = [];
    for (let j = i; j < i+5 && j < COMMANDS.length; j++) {
      batch.push(runCmd(conn, COMMANDS[j], j));
    }
    await Promise.all(batch);
    console.log('Batch', i/5+1, 'done');
  }
  conn.end();
}).on('error', (err) => { console.log('ERR:' + err.message); }).on('close', () => {
  for (let i = 0; i < COMMANDS.length; i++) {
    console.log('\n=== COMMAND', i+1, '===');
    console.log('CMD:', COMMANDS[i].substring(0, 200));
    console.log(results[i] ? results[i].substring(0, 4000) : 'NO OUTPUT');
    if (results[i] && results[i].length > 4000) console.log('... [TRUNCATED, total ' + results[i].length + ' chars]');
  }
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
