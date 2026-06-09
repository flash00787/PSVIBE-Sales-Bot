const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

conn.on('ready', () => {
  console.log('SSH connected\n');

  // Step 1: Count bare excepts - look for "except:" without any Exception type
  // More precise: "except:" with nothing or just whitespace+comment after
  const cmd = `
echo "=== __init__.py bare excepts ==="
grep -n "^\\s*except\\s*:" /root/psvibe-sale-bot/bot/__init__.py 2>/dev/null || echo "(no matches or file not found)"
echo ""
echo "=== app.py bare excepts ==="
grep -n "^\\s*except\\s*:" /root/psvibe-sale-bot/bot/app.py 2>/dev/null || echo "(no matches or file not found)"
echo ""
echo "=== __init__.py any except ==="
grep -n "except" /root/psvibe-sale-bot/bot/__init__.py 2>/dev/null || echo "(no matches or file not found)"
echo ""
echo "=== app.py any except ==="
grep -n "except" /root/psvibe-sale-bot/bot/app.py 2>/dev/null || echo "(no matches or file not found)"
`;

  conn.exec(cmd, (err, stream) => {
    if (err) throw err;
    let out = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.stderr.on('data', (d) => { console.error('STDERR:', d.toString()); });
    stream.on('close', () => {
      console.log(out);
      conn.end();
    });
  });
});

conn.on('error', (err) => { console.error('SSH error:', err); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey, readyTimeout: 15000 });
