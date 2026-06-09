const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  const cmds = [
    'echo "===PSVIBE-API SERVICE==="',
    'systemctl cat psvibe-api.service 2>/dev/null',
    'echo "===PSVIBE-SALES SERVICE==="',
    'systemctl cat psvibe-sale-bot.service 2>/dev/null',
    'echo "===PSVIBE-CUSTOMER SERVICE==="',
    'systemctl cat psvibe_customer_bot.service 2>/dev/null',
    'echo "===WALLET SERVICE==="',
    'systemctl cat psvibe-wallet.service 2>/dev/null',
    'echo "===CUSTOMER BOT MAIN.PY API KEY==="',
    'grep -n "API_KEY\|API_BASE\|api_base\|_API_KEY" /root/psvibe-sale-bot/customer_bot/main.py 2>/dev/null',
    'echo "===CUSTOMER BOT API.PY KEY==="',
    'grep -n "API_KEY\|API_BASE\|api_key" /root/psvibe-sale-bot/customer_bot/api.py 2>/dev/null | head -10',
    'echo "===API SERVER CERTS==="',
    'ls -la /root/psvibe_api_server/',
    'echo "===TEST API CALL==="',
    'curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health',
    'echo ""',
    'curl -s http://localhost:8000/api/health 2>/dev/null',
  ];
  conn.exec(cmds.join('; '), (err, stream) => {
    if (err) { console.error('exec err:', err); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out); conn.end(); });
  });
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
});
