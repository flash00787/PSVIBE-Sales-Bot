#!/usr/bin/env node
const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`
echo '=== V.1: How buttons get routed to functions ==='
echo '--- ALL app.add_handler or handler registration in V.1 ---'
grep -n 'add_handler\\|Application\\|TypeHandler\\|MessageHandler\\|CallbackQueryHandler\\|CommandHandler' /root/staging/monolithic_ref/main.py | grep -v 'def \\|"\\|#' | head -40

echo ''
echo '--- V.1 step_main_menu (line ~1492) ---'
sed -n '1492,1546p' /root/staging/monolithic_ref/main.py

echo ''
echo '--- V.1 main menu keyboard builder ---'
grep -n -A20 'def show_main_menu\\|def build_main_menu\\|BTN_DAILY' /root/staging/monolithic_ref/main.py | head -50

echo ''
echo '--- V.1 ConversationHandler block at line 11779 ---'
sed -n '11779,11860p' /root/staging/monolithic_ref/main.py
`, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d.toString());
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
