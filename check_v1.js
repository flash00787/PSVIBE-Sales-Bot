const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  const cmds = [
    'systemctl cat psvibe-bot',
    'ls -la /root/Sales-Tele-Bot/main.py 2>&1',
    'ls /root/Sales-Tele-Bot/ | head -10',
  ].join(' && ');
  c.exec(cmds, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
