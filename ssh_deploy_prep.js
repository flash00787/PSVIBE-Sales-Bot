const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  const cmds = `
echo "=== Check .env in staging ==="
ls -la /root/staging/bot_src/.env 2>&1
cat /root/staging/bot_src/.env 2>/dev/null || echo "(not found)"

echo ""
echo "=== Check verify_imports.py ==="
cat /root/staging/scripts/verify_imports.py 2>/dev/null | head -30

echo ""
echo "=== Check if logs dir exists in staging ==="
ls -la /root/staging/bot_src/logs/ 2>&1

echo ""
echo "=== List top-level files in staging vs refactored ==="
echo "--- staging top-level ---"
ls -la /root/staging/bot_src/ | grep -v '^d'
echo ""
echo "--- refactored top-level ---"
ls -la /root/Sales-Tele-Bot_refactored/ | grep -v '^d'
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
