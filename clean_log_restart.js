const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('truncate -s 0 /root/Sales-Tele-Bot_refactored/logs/bot.log && systemctl restart psvibe-bot-refactored && sleep 10 && tail -15 /root/Sales-Tele-Bot_refactored/logs/bot.log', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => { console.log('Clean log + restart:\n' + (o || '(ok)')); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 25000});
