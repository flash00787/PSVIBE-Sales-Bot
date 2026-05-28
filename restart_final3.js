const {Client} = require('ssh2');
const fs = require('fs');
const c = new Client();
c.on('ready', () => {
  c.exec('systemctl restart psvibe-bot-refactored', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
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
                c.exec("grep -cE '(ERROR|Traceback|NameError|ModuleNotFound|ImportError)' /root/Sales-Tele-Bot_refactored/logs/bot.log", (e4, s4) => {
                  if (e4) { console.error(e4); c.end(); return; }
                  let o4 = '';
                  s4.on('data', d => o4 += d);
                  s4.on('close', () => {
                    const ec = parseInt(o4.trim()) || 0;
                    console.log('\nTotal errors in log:', ec);
                    if (ec > 3) {
                      c.exec("grep 'Traceback\\|NameError\\|ImportError' /root/Sales-Tele-Bot_refactored/logs/bot.log", (e5, s5) => {
                        if (e5) { console.error(e5); c.end(); return; }
                        let o5 = '';
                        s5.on('data', d => o5 += d);
                        s5.on('close', () => { console.log('Error details:\n' + o5); c.end(); });
                      });
                    } else {
                      c.end();
                    }
                  });
                });
              });
            });
          } else {
            c.exec('journalctl -u psvibe-bot-refactored -n 20 --no-pager 2>&1 | tail -20', (e3, s3) => {
              if (e3) { console.error(e3); c.end(); return; }
              let o3 = '';
              s3.on('data', d => o3 += d);
              s3.on('close', () => { console.log(o3); c.end(); });
            });
          }
        });
      });
    }, 12000);
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 30000});
