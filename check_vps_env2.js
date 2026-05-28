const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  const cmds = [
    'echo "===CUSTOMER BOT ENV==="',
    'find /root -maxdepth 3 -name ".env" -not -path "*/node_modules/*" -not -path "*/.venv/*" 2>/dev/null',
    'echo "===API KEY ENV==="',
    'cat /etc/psvibe/secrets.env 2>/dev/null || echo "no secrets.env"',
    'echo "===SALES BOT API KEY SEARCH==="',
    'grep -n "API_KEY" /root/psvibe-sale-bot/bot/__init__.py 2>/dev/null | head -20',
    'echo "===CUSTOMER BOT API KEY SEARCH==="',
    'find /root -path "*/customer_bot*" -name "*.py" -exec grep -l "API_KEY" {} \\; 2>/dev/null | head -10',
    'echo "===CUSTOMER BOT DIRECTORIES==="',
    'find /root -maxdepth 4 -name "customer_bot*" -type d 2>/dev/null | head -10',
    'find /root -maxdepth 4 -name "psvibe_customer*" -type d 2>/dev/null | head -10',
    'ls -la /root/psvibe-sale-bot/ | head -20',
    'echo "===WALLET BOT==="',
    'find /root -maxdepth 3 -name "psvibe-wallet*" -type d 2>/dev/null',
    'find /root -maxdepth 4 -name "Personal-Wallet*" -type d 2>/dev/null | head -5',
    'ls -la /root/psvibe-wallet/ 2>/dev/null || echo "no /root/psvibe-wallet"',
    'find /root -name "psvibe-wallet.service" -type f 2>/dev/null',
    'echo "===API SERVER CONFIG API_KEY==="',
    'grep -n "API_KEY" /root/psvibe_api_server/config.py 2>/dev/null',
    'echo "===SALES BOT .ENV FULL==="',
    'cat /root/psvibe-sale-bot/.env',
  ];
  conn.exec(cmds.join('; '), (err, stream) => {
    if (err) { console.error('exec err:', err); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += '[ERR]' + d.toString());
    stream.on('close', () => { console.log(out); conn.end(); });
  });
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
});
