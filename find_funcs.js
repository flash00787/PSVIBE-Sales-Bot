const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  const cmds = [
    'cmd_confirmed_bookings',
    'cmd_financial_report',
    'cmd_inventory',
    'cmd_staff_book_hub',
    'cmd_staff_booking',
    'cmd_today_report',
    'cmd_waitlist_mgmt',
    'show_console_menu',
    'show_game_menu',
    'show_main_menu',
    'show_mm_menu',
  ];
  let idx = 0;
  const next = () => {
    if (idx >= cmds.length) { c.end(); return; }
    const fn = cmds[idx++];
    c.exec('grep -rn "def ' + fn + '" /root/Sales-Tele-Bot_refactored/bot/ --include="*.py" | head -1', (e, s) => {
      if (e) { console.error(e); next(); return; }
      let o = '';
      s.on('data', d => o += d);
      s.on('close', () => { console.log(fn, '→', o.trim() || 'NOT FOUND ❌'); next(); });
    });
  };
  next();
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
