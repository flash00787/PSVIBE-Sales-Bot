const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  const cmds = `
echo "=== Syntax compile check (no runtime) ==="
cd /root/staging/bot_src && python3 -m py_compile bot/handlers/main_menu.py && echo "OK main_menu.py"
python3 -m py_compile bot/handlers/__init__.py && echo "OK handlers/__init__.py"
python3 -m py_compile bot/__init__.py && echo "OK bot/__init__.py"
python3 -m py_compile bot/app.py && echo "OK bot/app.py"
python3 -m py_compile main.py && echo "OK main.py"

echo ""
echo "=== Check all handler files for syntax ==="
for f in /root/staging/bot_src/bot/handlers/*.py; do
  python3 -m py_compile "\$f" 2>&1 && echo "OK: \$(basename \$f)" || echo "FAIL: \$(basename \$f)"
done

echo ""
echo "=== Current service status ==="
systemctl status psvibe-bot-refactored --no-pager -l 2>&1 | head -20

echo ""
echo "=== Service env file ==="
cat /root/Sales-Tele-Bot_refactored/.env 2>/dev/null || echo "No .env file"
cat /etc/systemd/system/psvibe-bot-refactored.service 2>/dev/null | head -40 || cat /etc/systemd/system/psvibe-bot-refactored.service.d/*.conf 2>/dev/null
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
