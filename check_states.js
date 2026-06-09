#!/usr/bin/env node
const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`
echo '=== V.1: check for TypeHandler or auth middleware ==='
grep -n 'TypeHandler\\|is_allowed\\|_ALLOWED_USER\\|auth\\|check_auth' /root/staging/monolithic_ref/main.py | head -20

echo ''
echo '=== V.1: how does the bot start (build_app) ==='
sed -n '11760,11780p' /root/staging/monolithic_ref/main.py

echo ''
echo '=== V.2 app.py: ALL ConversationHandler lines ==='
grep -n 'ConversationHandler\\|MessageHandler\\|CallbackQueryHandler\\|CommandHandler\\|TypeHandler\\|add_handler' /root/Sales-Tele-Bot_refactored/bot/app.py | head -80

echo ''
echo '=== V.1: state names (constants) ==='
grep -n '^[A-Z_][A-Z_]*$' /root/staging/monolithic_ref/main.py | grep -v 'BTN_\\|NAV_\\|SSD_\\|STOCK_\\|SAL_ADV\\|ATTEND\\|BOOK_\\|FOOD_' | head -40

echo ''
echo '=== V.2: state names ==='
grep -n '^[A-Z_][A-Z_]*$' /root/Sales-Tele-Bot_refactored/bot/__init__.py | grep -v 'BTN_\\|NAV_\\|SSD_\\|STOCK_\\|SAL_ADV\\|ATTEND\\|BOOK_\\|FOOD_' | head -40
`, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d.toString());
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
