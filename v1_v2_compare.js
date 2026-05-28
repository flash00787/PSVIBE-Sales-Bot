#!/usr/bin/env node
const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`
echo '=== V.1 CONVERSATION HANDLER BLOCKS ==='
grep -n 'ConversationHandler(' /root/staging/monolithic_ref/main.py

echo ''
echo '=== V.1: lookup table/dict between BTN and functions ==='
grep -n 'BTN_.*:' /root/staging/monolithic_ref/main.py | head -30

echo ''
echo '=== V.1: The main_menu dispatcher (step_main_menu) ==='
sed -n '1101,1150p' /root/staging/monolithic_ref/main.py

echo ''
echo '=== V.1: how BTN_ compare to callback patterns ==='
grep -n 'if choice in\|elif choice in\|if choice ==\|elif choice ==' /root/staging/monolithic_ref/main.py | head -30
`, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d.toString());
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 20000});
