const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  // Get full context around the latest KeyError
  c.exec('sed -n "1995,2010p" /root/Sales-Tele-Bot_refactored/logs/bot.log 2>/dev/null', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      console.log('Error context:\n' + (o || '(empty)'));
      c.end();
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
