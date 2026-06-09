const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('systemctl is-active psvibe-bot-refactored', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      const st = o.trim();
      console.log('Status:', st);
      if (st === 'active') {
        c.exec("ps aux | grep 'python3' | grep 'Sales-Tele-Bot_refactored/main' | head -3", (e2, s2) => {
          if (e2) { console.error(e2); c.end(); return; }
          let o2 = '';
          s2.on('data', d => o2 += d);
          s2.on('close', () => { console.log('PID info:\n' + o2); c.end(); });
        });
      } else {
        c.exec("tail -15 /root/Sales-Tele-Bot_refactored/logs/bot.log | grep -A1 'Error\\|Traceback\\|ModuleNotFound'", (e2, s2) => {
          if (e2) { console.error(e2); c.end(); return; }
          let o2 = '';
          s2.on('data', d => o2 += d);
          s2.on('close', () => { console.log('Latest errors:\n' + o2); c.end(); });
        });
      }
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 10000});
