const {Client} = require('ssh2');
const conn = new Client();
conn.on('ready', () => {
  const cmds = `
echo "=== WALLET BOT ==="
ls /root/psvibe-sale-bot/.env* 2>&1
echo "=== SECRETS ==="
cat /etc/psvibe/secrets.env 2>&1
echo "=== API SERVER ENV ==="
ls /root/psvibe_api_server/.env* 2>&1
cat /root/psvibe_api_server/config.py 2>&1 | grep -E '^[A-Z_]+=' | head -20
echo "=== WORKING DIRECTORY ==="
pwd
echo "=== API SERVER PYTHON ==="
which python3
ls /root/psvibe_api_server/venv/bin/python3 2>&1
`.trim();
  conn.exec(cmds, (err, stream) => {
    if (err) { console.log('ERR:', err.message); conn.end(); return; }
    let out='';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out); conn.end(); });
  });
}).connect({ host:'5.223.81.16', port:22, username:'root', privateKey: require('fs').readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
