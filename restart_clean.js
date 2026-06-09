const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('rm -rf /root/Sales-Tele-Bot_refactored/bot/__pycache__ /root/Sales-Tele-Bot_refactored/bot/handlers/__pycache__ && systemctl restart psvibe-bot-refactored', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    setTimeout(() => {
      c.exec('systemctl is-active psvibe-bot-refactored', (e2, s2) => {
        if (e2) { console.error(e2); c.end(); return; }
        let o = '';
        s2.on('data', d => o += d);
        s2.on('close', () => {
          const st = o.trim();
          console.log('Status:', st);
          if (st === 'active') {
            c.exec('tail -10 /root/Sales-Tele-Bot_refactored/logs/bot.log', (e3, s3) => {
              if (e3) { console.error(e3); c.end(); return; }
              let o2 = '';
              s3.on('data', d => o2 += d);
              s3.on('close', () => { console.log('LOG:\n' + o2); c.end(); });
            });
          } else {
            c.exec("tail -20 /root/Sales-Tele-Bot_refactored/logs/bot.log | grep -A2 'Error\\|Traceback' | head -20", (e3, s3) => {
              if (e3) { console.error(e3); c.end(); return; }
              let o2 = '';
              s3.on('data', d => o2 += d);
              s3.on('close', () => { console.log('Errors:\n' + o2); c.end(); });
            });
          }
        });
      });
    }, 10000);
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 30000});
