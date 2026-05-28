const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  // Check state values between V.1 and V.2
  c.exec("echo '=== V.1 STATES ===' && grep -n '^[A-Z_][A-Z_]*$' /root/staging/monolithic_ref/main.py | grep -v 'BTN_\\|NAV_\\|SSD_\\|STOCK_\\|SAL_ADV\\|ATTEND\\|BOOK_\\|FOOD_\\|^[0-9]' | head -50", (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      console.log(o);
      c.exec("echo '=== V.2 STATES (BotState) ===' && grep -n '^    [A-Z_][A-Z_]* ' /root/Sales-Tele-Bot_refactored/bot/__init__.py | grep -v 'BTN_\\|NAV_\\|SSD_\\|STOCK_\\|SAL_ADV\\|ATTEND\\|BOOK_\\|FOOD_'" , (e2, s2) => {
        if (e2) { console.error(e2); c.end(); return; }
        let o2 = '';
        s2.on('data', d => o2 += d);
        s2.on('close', () => { console.log(o2); c.end(); });
      });
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
