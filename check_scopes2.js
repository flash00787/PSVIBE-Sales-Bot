const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('grep -in "scope\\|aud\\|drive\\|spreadsheet" /root/Sales-Tele-Bot_refactored/bot/__init__.py | head -20', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 10000});
