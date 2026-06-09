const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  const cmds = [
    'echo "=== CHECK .env file ==="',
    'cat /root/Sales-Tele-Bot_refactored/.env | grep -v "^#" | head -5',
    'echo "=== Service env ==="',
    'systemctl show -p Environment psvibe-bot-refactored',
    'echo "=== Service file ==="',
    'cat /etc/systemd/system/psvibe-bot-refactored.service | grep -E "Environment|WorkingDirectory|ExecStart"',
  ].join(' && ');
  c.exec(cmds, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 10000});
