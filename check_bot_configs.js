const {Client} = require('ssh2');
const conn = new Client();
conn.on('ready', () => {
  // Check all .env files and key configurations
  const cmds = [
    'echo "=== SALES BOT .ENV ===" && cat /root/psvibe-sale-bot/.env 2>&1',
    'echo "=== CUSTOMER BOT .ENV ===" && ls /root/psvibe-sale-bot/customer_bot/ 2>&1',
    'echo "=== WALLET BOT ===" && ls /root/psvibe-sale-bot/ 2>&1 | head -20 && cat /root/psvibe-sale-bot/*.env 2>&1',
    'echo "=== API SERVER ENV ===" && cat /root/psvibe_api_server/.env 2>&1',
    'echo "=== SERVICE FILES ===" && ls /etc/systemd/system/ | grep psvibe',
  ].join(' && ');
  
  conn.exec(cmds, (err, stream) => {
    if (err) { console.log('ERR:', err.message); conn.end(); return; }
    let out='';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out); conn.end(); });
  });
}).connect({ host:'5.223.81.16', port:22, username:'root', privateKey: require('fs').readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
