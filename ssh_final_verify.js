const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  const cmds = `
echo "=== Wait 15s and recheck stability ==="
sleep 15
systemctl is-active psvibe-bot-refactored && echo "STABLE ✓" || echo "FAILED ✗"

echo ""
echo "=== Service detailed status ==="
systemctl status psvibe-bot-refactored --no-pager 2>&1 | head -15

echo ""
echo "=== Recent bot log (last 30 lines) ==="
tail -30 /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null || journalctl -u psvibe-bot-refactored --no-pager -n 20

echo ""
echo "=== All psvibe services ==="
systemctl list-units --type=service | grep psvibe

echo ""
echo "=== Final tree of refactored directory ==="
find /root/Sales-Tele-Bot_refactored -maxdepth 3 -type d | sort

echo ""
echo "=== V1 main.py line count ==="
wc -l /root/staging/monolithic_ref/main.py

echo ""
echo "=== Check for 'replit' references in V2 bot code ==="
grep -r "replit\|_replit_get\|_replit_post\|_replit_patch" /root/Sales-Tele-Bot_refactored/bot/ --include="*.py" -l 2>/dev/null
echo ""
grep -r "API_BASE_URL\|_api_base" /root/Sales-Tele-Bot_refactored/bot/ --include="*.py" -l 2>/dev/null
`;
  conn.exec(cmds, (err, stream) => {
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out); conn.end(); process.exit(0); });
  });
}).connect({
  host: '167.71.196.120',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
