const {Client} = require('ssh2');
const c = new Client();
let idx = 0;
const cmds = [
  // Check what handlers/__init__.py exports via __all__
  'echo "=== handlers/__init__.py __all__ ===" && head -50 /root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py',
  // Check what __all__ exports from other modules
  'echo "=== handlers/__init__.py individual imports ===" && grep "from ." /root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py',
];
c.on('ready', () => {
  c.exec(cmds.join(' && '), (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      console.log(o);
      // Now fix main_menu.py
      c.exec("head -12 /root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py", (e2, s2) => {
        if (e2) { console.error(e2); c.end(); return; }
        let o2 = '';
        s2.on('data', d => o2 += d);
        s2.on('close', () => { console.log('Current main_menu imports:', o2); c.end(); });
      });
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
