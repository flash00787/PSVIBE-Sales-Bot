const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  // Fix main_menu.py: add from bot.handlers import * after from bot import *
  c.exec('head -3 /root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      console.log('Before:', o);
      c.exec('sed -i "1a from bot.handlers import *" /root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py', (e2, s2) => {
        if (e2) { console.error(e2); c.end(); return; }
        let o2 = '';
        s2.on('data', d => o2 += d);
        s2.on('close', () => {
          c.exec('head -4 /root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py', (e3, s3) => {
            if (e3) { console.error(e3); c.end(); return; }
            let o3 = '';
            s3.on('data', d => o3 += d);
            s3.on('close', () => { console.log('After:', o3); c.end(); });
          });
        });
      });
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
