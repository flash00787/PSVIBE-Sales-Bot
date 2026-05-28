const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  // Get _replit functions from V1 (lines 8309-8400 area)
  // and build a catalog of all API call sites
  const cmds = [
    'echo "=== _REPLIT_GET ==="',
    'sed -n "8309,8323p" /root/staging/monolithic_ref/main.py',
    'echo "=== _REPLIT_PATCH ==="',
    'sed -n "8324,8354p" /root/staging/monolithic_ref/main.py',
    'echo "=== _REPLIT_POST ==="',
    'sed -n "8355,8380p" /root/staging/monolithic_ref/main.py',
    'echo "=== API_BASE ==="',
    'grep -n "def _api_base" /root/staging/monolithic_ref/main.py',
    'echo "=== save_receipt_json ==="',
    'grep -n "def save_receipt_json" /root/staging/monolithic_ref/main.py',
    'echo "=== ALL _replit CALLERS ==="',
    'grep -rn "_replit_get\\|_replit_post\\|_replit_patch" /root/staging/monolithic_ref/main.py | head -40',
    'echo "=== HANDLER MODULE LIST IN V2 ==="',
    'ls /root/Sales-Tele-Bot_refactored/bot/handlers/*.py',
    'echo "=== V2 __init__.py LINE COUNT ==="',
    'wc -l /root/Sales-Tele-Bot_refactored/bot/__init__.py',
    'echo "=== V2 __init__.py FUNCTION LIST ==="',
    'grep -n "^def \\|^async def" /root/Sales-Tele-Bot_refactored/bot/__init__.py',
    'echo "=== V2 main_menu.py ==="',
    'cat /root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py',
  ];
  conn.exec(cmds.join('; '), (err, stream) => {
    if (err) { console.log('ERR:', err.message); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d);
    stream.on('close', () => { console.log(out); conn.end(); process.exit(0); });
  });
}).on('error', e => console.log('CONN_ERR:', e.message))
.connect({
  host: '167.71.196.120',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
