#!/usr/bin/env node
const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`
echo '=== Where is show_alert used in app.py? ==='
grep -n 'show_alert' /root/Sales-Tele-Bot_refactored/bot/app.py
echo ''
echo '=== Where was show_alert in monolithic V.1? ==='
grep -n 'show_alert' /root/staging/monolithic_ref/main.py
echo ''
grep -n -B2 'def show_alert' /root/staging/monolithic_ref/main.py
echo ''
echo '=== Where is show_alert defined in V.2? ==='
grep -rn 'def show_alert' /root/Sales-Tele-Bot_refactored/bot/ --include='*.py'
echo ''
echo '=== Check auth_middleware in app.py (which references show_alert) ==='
grep -n -A30 'def _auth_middleware' /root/Sales-Tele-Bot_refactored/bot/app.py
`, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d.toString());
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
