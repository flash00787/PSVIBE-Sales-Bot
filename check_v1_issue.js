const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  const cmds = [
    'echo "=== V.1 Service Check ==="',
    'systemctl cat psvibe-bot',
    'echo "---",
    'ls -la /root/Sales-Tele-Bot/main.py 2>&1 || echo "main.py not found in Sales-Tele-Bot"',
    'echo "---",
    'ls /root/Sales-Tele-Bot/ | head -10',
  ].join(' && ');
  c.exec(cmds, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
