const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  conn.exec("echo '=== KEY MARKERS ===' && grep -n 'def step_tu_kpay\\|def step_tu_confirm\\|# Try to parse as amount\\|# Check if text is BTN_PAY_DONE\\|# Show review (common\\|return TU_CONFIRM' /root/psvibe-sales-bot/bot/handlers/members.py | grep -A1 -B1 'step_tu_kpay' && echo '=== 1180-1200 ===' && sed -n '1180,1200p' /root/psvibe-sales-bot/bot/handlers/members.py && echo '=== 1265-1275 ===' && sed -n '1265,1275p' /root/psvibe-sales-bot/bot/handlers/members.py", (err, stream) => {
    let out = ''; stream.on('data', d => out += d); stream.on('close', () => { console.log(out); conn.end(); });
  });
});
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'), readyTimeout: 15000 });
