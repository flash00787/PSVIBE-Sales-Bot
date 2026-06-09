const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
const keyPath = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const privateKey = fs.readFileSync(keyPath, 'utf8');

// Use single quotes with explicit \n to avoid template literal issues
const commands = [
  'set -e',
  'echo "=== CURRENT STATE ==="',
  'echo "PID: $(systemctl show psvibe-bot.service --property=MainPID --value 2>/dev/null)"',
  'echo "Active: $(systemctl is-active psvibe-bot.service 2>/dev/null)"',
  'echo ""',
  'echo "=== SALES-TELE-BOT DIR ==="',
  'ls -la /root/Sales-Tele-Bot/ 2>/dev/null | head -30',
  'echo ""',
  'echo "Lines in main.py: $(wc -l < /root/Sales-Tele-Bot/main.py 2>/dev/null)"',
  'echo ""',
  '',
  'echo "=== STEP 1: FRESH BACKUP ==="',
  'BACKUP_NAME="psvibe-V1-fresh-$(date +%Y%m%d_%H%M%S).tar.gz"',
  'tar -czf /root/backups/${BACKUP_NAME} -C /root Sales-Tele-Bot 2>/dev/null',
  'echo "Backup created: /root/backups/${BACKUP_NAME}"',
  'ls -lh /root/backups/${BACKUP_NAME}',
  'echo ""',
  'echo "Existing V1/V2 backups:"',
  'ls -lh /root/backups/ | grep -i "monolith\\|V1\\|v1\\|original\\|fresh" 2>/dev/null || echo "(none matching)"',
  'echo ""',
  '',
  'echo "=== STEP 2: DELETE V1 FROM VPS ==="',
  'echo "Stopping service first..."',
  'systemctl stop psvibe-bot.service 2>/dev/null',
  'echo "Service stopped: $(systemctl is-active psvibe-bot.service 2>/dev/null)"',
  '',
  'if [ -f /root/Sales-Tele-Bot/main.py ]; then',
  '  echo "Deleting /root/Sales-Tele-Bot/main.py..."',
  '  rm -f /root/Sales-Tele-Bot/main.py',
  '  echo "Deleted."',
  'else',
  '  echo "main.py not found at expected location."',
  'fi',
  '',
  'echo ""',
  'echo "=== VERIFY ==="',
  'ls -la /root/Sales-Tele-Bot/main.py 2>/dev/null && echo "⚠️ Still exists!" || echo "✅ main.py deleted successfully."',
  'echo ""',
  '',
  'echo "=== REMAINING FILES IN SALES-TELE-BOT ==="',
  'ls -la /root/Sales-Tele-Bot/ | head -20',
  'echo ""',
  '',
  'echo "=== BACKUPS INVENTORY ==="',
  'ls -lh /root/backups/',
].join('\n');

conn.on('ready', () => {
  conn.exec(commands, { pty: false }, (err, stream) => {
    if (err) { console.error(err); process.exit(1); }
    let output = '';
    stream.on('data', d => output += d.toString());
    stream.stderr.on('data', d => output += d.toString());
    stream.on('close', () => { console.log(output); conn.end(); process.exit(0); });
  });
}).connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey });
