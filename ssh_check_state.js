const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  const cmds = `
echo "=== 1. Refactored main_menu.py (already fixed?) ===" && head -25 /root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py
echo ""
echo "=== 2. Staging main_menu.py (needs fix) ===" && head -25 /root/staging/bot_src/bot/handlers/main_menu.py
echo ""
echo "=== 3. check keep_alive.py locations ===" && find /root/ -name "keep_alive.py" 2>/dev/null
echo ""
echo "=== 4. Refactored __init__.py first 10 lines ===" && head -10 /root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py
echo ""
echo "=== 5. Check duplicate directories ===" && echo "--- bot/bot/" && ls /root/Sales-Tele-Bot_refactored/bot/bot/ 2>/dev/null && echo "--- staging bot/bot/" && ls /root/staging/bot_src/bot/bot/ 2>/dev/null && echo "--- staging handlers/" && ls /root/staging/bot_src/handlers/ 2>/dev/null
echo ""
echo "=== 6. Top-level app.py check ===" && ls -la /root/Sales-Tele-Bot_refactored/app.py 2>/dev/null && ls -la /root/staging/bot_src/app.py 2>/dev/null
echo ""
echo "=== 7. Systemd service check ===" && systemctl list-units --type=service --all | grep -i psvibe
echo ""
echo "=== 8. Deploy script ===" && head -50 /root/staging/scripts/deploy.sh 2>/dev/null
echo ""
echo "=== 9. V1 main.py first 20 lines ===" && head -20 /root/staging/monolithic_ref/main.py
echo ""
echo "=== 10. Personal-Wallet keep_alive.py check ===" && head -20 /root/Personal-Wallet-Tele-Bot/bot/keep_alive.py 2>/dev/null
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
