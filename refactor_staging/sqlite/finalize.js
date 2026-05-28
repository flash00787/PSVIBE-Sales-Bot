const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '167.71.196.120';
const USER = 'root';
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';

async function sshExec(conn, command) {
  return new Promise((resolve, reject) => {
    conn.exec(command, (err, stream) => {
      if (err) return reject(err);
      let stdout = '', stderr = '';
      stream.on('data', (d) => { stdout += d.toString(); });
      stream.stderr.on('data', (d) => { stderr += d.toString(); });
      stream.on('close', (code) => resolve({ stdout, stderr, code }));
    });
  });
}

async function run() {
  const privateKey = await fs.promises.readFile(KEY_PATH, 'utf8');
  const conn = new Client();
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve);
    conn.on('error', reject);
    conn.connect({ host: HOST, port: 22, username: USER, privateKey });
  });
  console.log('[CONNECT] OK');

  try {
    // 1. Write crontab helper script to VPS
    console.log('\n--- Writing crontab helper ---');
    await sshExec(conn, `cat > /root/Sales-Tele-Bot_refactored/sqlite/cron_wrapper.sh << 'CRONEOF'
#!/bin/bash
# Cron wrapper — sources .env before sync
cd /root/Sales-Tele-Bot_refactored/sqlite
if [ -f /root/Sales-Tele-Bot/.env ]; then
  export $(grep -v '^#' /root/Sales-Tele-Bot/.env | grep -E 'SHEET_ID|GOOGLE_APPLICATION_CREDENTIALS' | xargs)
fi
[ -z "$GOOGLE_APPLICATION_CREDENTIALS" ] && export GOOGLE_APPLICATION_CREDENTIALS="/root/Sales-Tele-Bot/service_account.json"
[ -z "$SQLITE_DB_PATH" ] && export SQLITE_DB_PATH="/root/Sales-Tele-Bot_refactored/psvibe.db"
bash sync_cron.sh
CRONEOF
chmod +x /root/Sales-Tele-Bot_refactored/sqlite/cron_wrapper.sh
`);
    console.log('[OK] cron_wrapper.sh created');

    // 2. Add crontab entry
    console.log('\n--- Installing crontab ---');
    const crontabResult = await sshExec(conn, `
if crontab -l 2>/dev/null | grep -q 'cron_wrapper.sh'; then
  echo "Crontab entry already exists"
else
  (crontab -l 2>/dev/null; echo "*/5 * * * * /root/Sales-Tele-Bot_refactored/sqlite/cron_wrapper.sh >> /root/Sales-Tele-Bot_refactored/sqlite/sync.log 2>&1") | crontab -
  echo "Crontab entry added"
fi
echo "=== PSVibe crontab entries ==="
crontab -l 2>/dev/null | grep -i psvibe || echo "(no psvibe entries)"
`);
    console.log(crontabResult.stdout);

    // 3. List VPS files
    console.log('\n--- VPS file structure ---');
    const ls = await sshExec(conn, `
echo "=== SQLite directory ==="
ls -la /root/Sales-Tele-Bot_refactored/sqlite/
echo ""
echo "=== Database ==="
ls -la /root/Sales-Tele-Bot_refactored/psvibe.db
echo ""
echo "=== DB size ==="
python3 -c "
import sqlite3, os
conn = sqlite3.connect('/root/Sales-Tele-Bot_refactored/psvibe.db')
cur = conn.cursor()
for table in ['members','bookings','sales','topups','settings','consoles','console_games','game_library','staff']:
    cur.execute(f'SELECT COUNT(*) FROM [{table}]')
    print(f'  {table}: {cur.fetchone()[0]} rows')
conn.close()
print(f'  DB file: {os.path.getsize(\"/root/Sales-Tele-Bot_refactored/psvibe.db\")} bytes')
"
`);
    console.log(ls.stdout);

    console.log('\n[DONE] SQLite fully deployed and cron scheduled!');
  } finally {
    conn.end();
  }
}

run().catch(err => { console.error('[FATAL]', err); process.exit(1); });
