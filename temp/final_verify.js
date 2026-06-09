const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  conn.exec("cd /root/psvibe-sales-bot && python3 -c \"import ast; ast.parse(open('bot/handlers/members.py').read()); print('SYNTAX OK')\" && grep -n '# Try to parse as amount\\|# Check if text is BTN_PAY_DONE\\|return TU_CONFIRM' bot/handlers/members.py | grep -A2 -B2 'step_tu_kpay' | head -20; echo '---'; grep -c 'def step_tu_kpay\\|def step_tu_confirm' bot/handlers/members.py", (err, stream) => {
    let out = ''; stream.on('data', d => out += d); stream.on('close', () => { console.log(out); conn.end(); });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'), readyTimeout: 15000 });
