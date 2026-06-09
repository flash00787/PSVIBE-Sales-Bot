const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('systemctl restart psvibe-bot-refactored', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      console.log('Restarted:', o);
      setTimeout(() => {
        c.exec('systemctl is-active psvibe-bot-refactored', (e2, s2) => {
          if (e2) { console.error(e2); c.end(); return; }
          let o2 = '';
          s2.on('data', d => o2 += d);
          s2.on('close', () => {
            console.log('Status:', o2.trim());
            c.exec('tail -8 /root/Sales-Tele-Bot_refactored/logs/bot.log', (e3, s3) => {
              if (e3) { console.error(e3); c.end(); return; }
              let o3 = '';
              s3.on('data', d => o3 += d);
              s3.on('close', () => { console.log('LOG:\n' + o3); c.end(); });
            });
          });
        });
      }, 8000);
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 25000});
