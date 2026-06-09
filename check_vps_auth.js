const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  const cmds = [
    'echo "===API HEALTH==="',
    'curl -s http://localhost:8000/api/health',
    'echo ""',
    'echo "===API SHEETS/CONFIG WITH KEY==="',
    'curl -s -H "X-API-Key: JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" http://localhost:8000/api/sheets/config',
    'echo ""',
    'echo "===API FETCH MEMBERS WITH KEY==="',
    'curl -s -H "X-API-Key: JWIErd82Apo3j-KKWW8HjOjfizo9s_tpJZhcSb7D-AQ" http://localhost:8000/api/fetch_members | head -c 1000',
    'echo ""',
    'echo "===API WITHOUT KEY==="',
    'curl -s http://localhost:8000/api/sheets/config',
    'echo ""',
    'echo "===SALES BOT RECENT LOGS==="',
    'tail -30 /root/psvibe-sale-bot/bot_status.log 2>/dev/null | grep -i "api_base\|connection\|401\|error\|API" | tail -10',
    'echo "===CUSTOMER BOT RECENT LOGS==="',
    'journalctl -u psvibe_customer_bot.service --no-pager -n 20 2>/dev/null | grep -i "api\|401\|error\|auth\|key" | tail -10',
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
