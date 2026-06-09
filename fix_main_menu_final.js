const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  // Fix: replace 'from bot import *' with 'from bot.handlers import *' in main_menu.py
  // Then also add 'from bot import BTN_*, now_mmt, fetch_allowed_staff_ids' explicitly
  c.exec([
    "echo '=== Fixing main_menu.py ==='",
    "cd /root/Sales-Tele-Bot_refactored/bot/handlers",
    "sed -i 's/from bot import \\*/from bot.handlers import */' main_menu.py",
    "head -3 main_menu.py",
    "",
    "echo '=== Also apply to staging ==='",
    "cd /root/staging/bot_src/bot/handlers",
    "sed -i 's/from bot import \\*/from bot.handlers import */' main_menu.py",
    "head -3 main_menu.py",
  ].join(' && '), (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      console.log(o);
      // Now check if main_menu.py still needs BTN constants
      c.exec("grep -c 'BTN_' /root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py", (e2, s2) => {
        if (e2) { console.error(e2); c.end(); return; }
        let o2 = '';
        s2.on('data', d => o2 += d);
        s2.on('close', () => {
          console.log('BTN references in main_menu:', o2.trim());
          // We need bot imports for BTN constants too
          // handlers/__init__.py imports from handlers, not from bot
          // So BTN constants from bot/__init__.py won't be available
          // Fix: also import from bot
          c.exec("sed -i '1s/^/from bot import BTN_DAILY_SALES, BTN_NEW_SALE, BTN_MEMBER_MGMT, BTN_CONSOLES, BTN_TODAY_REPORT, BTN_STAFF_BOOK, BTN_INVENTORY_VIEW, BTN_FINANCIAL_REPORT, BTN_ADMIN, BTN_GAMES, BTN_STOCK_MGMT, BTN_DISC_MGMT, BTN_SSD_DISC, BTN_FOOD_SETUP\\\\\\n/' /root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py && head -4 /root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py", (e3, s3) => {
            if (e3) { console.error(e3); c.end(); return; }
            let o3 = '';
            s3.on('data', d => o3 += d);
            s3.on('close', () => { console.log('After fix:', o3); c.end(); });
          });
        });
      });
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
