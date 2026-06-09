const { Client } = require('ssh2');
const fs = require('fs');

const COMMANDS = [
  'grep -n "def _load_cfg\|def _load_members\|def _bg_cache_refresh\|def _get_cfg\|def _get_member\|def fetch_allowed_staff\|_cfg_cache\|_members_cache\|_cfg_ts\|_members_ts\|_CFG_TTL\|_MEMBERS_TTL\|_BK_TTL" /root/psvibe-sales-bot/bot/__init__.py',
  'grep -n "ALLOWED_USER_IDS\|allowed_staff\|fetch_allowed_staff" /root/psvibe-sales-bot/bot/app.py | head -20',
  'sed -n "1,120p" /root/psvibe-sales-bot/bot/app.py | grep "auth_middleware\|allowed\|fetch_allowed" ',
  'cat /root/psvibe_api_server/app.py | grep -A5 -B2 "fetch_allowed_staff_ids_from_mysql" ',
  'grep -n "def _load_cfg\|def _load_members\|def _bg_cache\|_cfg_cache\|_members_cache\|_BK_TTL" /root/psvibe-sales-bot/bot/__init__.py',
  'wc -l /root/psvibe-sales-bot/bot/__init__.py',
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
    console.log((results[i] || 'NO OUTPUT'));
  }
}).connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
