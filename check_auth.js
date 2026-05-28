#!/usr/bin/env node
const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec(`
echo '=== fetch_allowed_staff_ids definition ==='
grep -n -A15 'def fetch_allowed_staff_ids' /root/Sales-Tele-Bot_refactored/bot/__init__.py

echo ''
echo '=== In monolithic V.1, how was auth done? ==='
grep -n 'is_allowed\|_ALLOWED_USER_IDS\|fetch_allowed_staff' /root/staging/monolithic_ref/main.py | head -10

echo ''
echo '=== Does V.1 have the _auth_middleware pattern? ==='
grep -n 'ApplicationHandlerStop\|TypeHandler(' /root/staging/monolithic_ref/main.py | head -5

echo ''
echo '=== V.1: How is auth checked on /start? ==='
grep -n -B2 -A15 'def show_main_menu' /root/staging/monolithic_ref/main.py | head -40
`, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d.toString());
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
