const { Client } = require('ssh2');
const fs = require('fs');

const COMMANDS = [
  'grep -n "_load_members\|_load_cfg\|_bg_cache_refresh\|def _get_cfg\|def _get_member\|def fetch_\|def cmd_\|fetch_allowed_staff\|ALLOWED_USER" /root/psvibe-sales-bot/bot/__init__.py | head -40',
  'grep -rn "429\|rate.limit\|quota\|RESOURCE_EXHAUSTED\|too_many\|APICallError" /root/psvibe-sales-bot/ --include "*.py" 2>/dev/null | head -20',
  'grep -rn "background_cache\|bg_cache\|cache_refresh\|_refresh\|SYNC_INTERVAL\|sync_interval" /root/psvibe-sales-bot/bot/ --include "*.py" 2>/dev/null | head -20',
  'sed -n "1,100p" /root/psvibe-sales-bot/main.py',
  'grep -n "def _api_get\|def _api_post\|CACHE_TTL\|_CACHE\|cache_get\|cache_set\|def _fetch_" /root/psvibe-sales-bot/customer_bot/api.py | head -30',
  'grep -rn "sheets_client\|gspread\|worksheet\|open_by_key\|service_account" /root/psvibe-sales-bot/customer_bot/ --include "*.py" 2>/dev/null | head -20',
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
  for (let i = 0; i < COMMANDS.length; i += 2) {
    const batch = [];
    for (let j = i; j < i+2 && j < COMMANDS.length; j++) batch.push(runCmd(conn, COMMANDS[j], j));
    await Promise.all(batch);
  }
  conn.end();
}).on('error', (err) => { console.log('ERR:' + err.message); }).on('close', () => {
  for (let i = 0; i < COMMANDS.length; i++) {
    console.log('\n===', i+1, '===');
    console.log((results[i] || 'NO OUTPUT').substring(0, 5000));
  }
}).connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
