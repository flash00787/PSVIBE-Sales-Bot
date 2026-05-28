const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec("head -3 /root/Sales-Tele-Bot_refactored/bot/handlers/admin.py", (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      console.log('admin.py line 1:', o.trim());
      c.exec("head -3 /root/Sales-Tele-Bot_refactored/bot/handlers/help.py", (e2, s2) => {
        if (e2) { console.error(e2); c.end(); return; }
        let o2 = '';
        s2.on('data', d => o2 += d);
        s2.on('close', () => {
          console.log('help.py line 1:', o2.trim());
          c.exec("head -3 /root/Sales-Tele-Bot_refactored/bot/handlers/sales.py", (e3, s3) => {
            if (e3) { console.error(e3); c.end(); return; }
            let o3 = '';
            s3.on('data', d => o3 += d);
            s3.on('close', () => {
              console.log('sales.py line 1:', o3.trim());
              c.end();
            });
          });
        });
      });
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
