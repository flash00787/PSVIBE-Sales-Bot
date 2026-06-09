const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  const cmd = `
echo "=== IMPORT TEST ==="
cd /root/Sales-Tele-Bot_refactored && /root/Sales-Tele-Bot_refactored/.venv/bin/python3 << 'PYEOF'
from bot import app, main, keep_alive, ensure_sheet_headers
from bot import _load_cfg, _load_members, _bg_cache_refresh
print("All imports OK")
PYEOF

echo ""
echo "=== NEW LOGS (since restart) ==="
grep "2026-05-27 04:0" /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null || echo "(no new log entries)"

echo ""
echo "=== LAST 5 LOG LINES ==="
tail -5 /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null

echo ""
echo "=== V2 SERVICE FULL STATUS ==="
systemctl status psvibe-bot-refactored.service 2>&1

echo ""
echo "=== ACTIVE PS VIBE PROCESSES ==="
ps aux | grep -E "python3.*main.py|python3.*customer_bot" | grep -v grep
`;

  conn.exec(cmd, { pty: true }, (err, stream) => {
    if (err) { console.error('EXEC ERR:', err.message); conn.end(); process.exit(1); return; }
    let out = '';
    stream.on('data', d => { out += d; process.stderr.write(d); });
    stream.on('close', (code) => {
      console.log('===VERIFY_OUTPUT===');
      console.log(out);
      console.log('===END_VERIFY===');
      conn.end();
      process.exit(code || 0);
    });
  });
});

conn.on('error', e => { console.error('SSH error:', e.message); process.exit(1); });
conn.connect({
  host: '167.71.196.120',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
