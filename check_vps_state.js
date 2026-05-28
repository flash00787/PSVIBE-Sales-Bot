const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  const cmds = [
    'echo "=== STAGING PY FILES ==="',
    'find /root/staging/bot_src/ -type f -name "*.py" | sort',
    'echo "=== DUPLICATE DIRS ==="',
    'ls -la /root/staging/bot_src/bot/bot/ 2>/dev/null | head -3',
    'echo "=== TOP-LEVEL HANDLERS ==="',
    'ls -la /root/staging/bot_src/handlers/ 2>/dev/null | head -3',
    'echo "=== SQLITE ==="',
    'ls /root/staging/bot_src/sqlite/ 2>/dev/null',
    'echo "=== KEEP_ALIVE_SRC ==="',
    'find /root/Personal-Wallet-Tele-Bot/ -name "keep_alive.py" 2>/dev/null',
    'echo "=== REFACTORED DIRS ==="',
    'find /root/Sales-Tele-Bot_refactored/ -type d | head -20',
    'echo "=== APP.PY ==="',
    'ls -la /root/Sales-Tele-Bot_refactored/app.py 2>/dev/null',
    'echo "=== MAIN.PY ==="',
    'head -20 /root/Sales-Tele-Bot_refactored/main.py 2>/dev/null',
  ];
  const fullCmd = cmds.join('; ');
  conn.exec(fullCmd, (err, stream) => {
    if (err) { console.log('ERR:', err.message); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out); conn.end(); });
  });
}).on('error', e => console.log('CONN_ERR:', e.message))
.connect({
  host: '167.71.196.120',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
