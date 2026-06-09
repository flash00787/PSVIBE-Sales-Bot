const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  const cmds = `
echo "=== Check if refactored directory exists ==="
ls -la /root/Sales-Tele-Bot_refactored/ 2>&1 | head -5
ls /root/Sales-Tele-Bot_refactored/bot/handlers/ 2>&1 | head -5

echo ""
echo "=== Service status ==="
systemctl status psvibe-bot-refactored --no-pager 2>&1 | head -10

echo ""
echo "=== Check recent logs ==="
journalctl -u psvibe-bot-refactored --no-pager -n 5 2>&1
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
