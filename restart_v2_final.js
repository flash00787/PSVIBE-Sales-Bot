const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('systemctl restart psvibe-bot-refactored', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      console.log('Restart command sent...');
      setTimeout(() => {
        c.exec('systemctl is-active psvibe-bot-refactored', (e2, s2) => {
          if (e2) { console.error(e2); c.end(); return; }
          let o2 = '';
          s2.on('data', d => o2 += d);
          s2.on('close', () => {
            const status = o2.trim();
            console.log('Status:', status);
            if (status === 'active') {
              c.exec('tail -20 /root/Sales-Tele-Bot_refactored/logs/bot.log', (e3, s3) => {
                if (e3) { console.error(e3); c.end(); return; }
                let o3 = '';
                s3.on('data', d => o3 += d);
                s3.on('close', () => {
                  console.log('LOG:\n' + o3);
                  // Check for errors
                  // If error count > 0, show them
                  c.exec("grep -c 'ERROR\\|Traceback\\|ImportError' /root/Sales-Tele-Bot_refactored/logs/bot.log", (e4, s4) => {
                    if (e4) { console.error(e4); c.end(); return; }
                    let o4 = '';
                    s4.on('data', d => o4 += d);
                    s4.on('close', () => { console.log('Error count:', o4.trim()); c.end(); });
                  });
                });
              });
            } else {
              console.log('FAILED TO START');
              c.exec('systemctl status psvibe-bot-refactored --no-pager -l 2>/dev/null | head -20', (e3, s3) => {
                if (e3) { console.error(e3); c.end(); return; }
                let o3 = '';
                s3.on('data', d => o3 += d);
                s3.on('close', () => { console.log('Status output:', o3); c.end(); });
              });
            }
          });
        });
      }, 10000);
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 30000});
