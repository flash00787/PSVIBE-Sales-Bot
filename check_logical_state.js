const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  // Check if V.2 is still running, check its log for recent errors
  c.exec('systemctl is-active psvibe-bot-refactored', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      const st = o.trim();
      console.log('V.2 status:', st);
      if (st === 'active') {
        c.exec('tail -30 /root/Sales-Tele-Bot_refactored/logs/bot.log', (e2, s2) => {
          if (e2) { console.error(e2); c.end(); return; }
          let o2 = '';
          s2.on('data', d => o2 += d);
          s2.on('close', () => { console.log('LOG:\n' + o2); c.end(); });
        });
      } else {
        // Try to restart, but also start V.1 as parallel
        c.exec('systemctl restart psvibe-bot-refactored', () => {
          console.log('Restarting V.2... also checking V.1 path');
          c.exec('ls -la /root/Sales-Tele-Bot/main.py /root/Sales-Tele-Bot/bot/app.py 2>&1', (e3, s3) => {
            if (e3) { console.error(e3); c.end(); return; }
            let o3 = '';
            s3.on('data', d => o3 += d);
            s3.on('close', () => { console.log('V.1 files:\n' + o3); c.end(); });
          });
        });
      }
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
