const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  // Find what handler functions step_main_menu calls
  c.exec('grep -o "[a-z_][a-z_]*" /root/Sales-Tele-Bot_refactored/bot/handlers/main_menu.py | grep "^cmd_\|^fetch_\|^cb_\|^show_\|^step_\|^launch_" | sort -u | grep -v "step_main_menu"', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      console.log('Functions used by main_menu.py:');
      console.log(o);
      
      // Check which ones are defined WHERE
      const funcs = o.trim().split('\n');
      let count = 0;
      const checkNext = () => {
        if (count >= funcs.length) { c.end(); return; }
        const fn = funcs[count++].trim();
        if (!fn) { checkNext(); return; }
        c.exec('grep -rn "def ' + fn + '" /root/Sales-Tele-Bot_refactored/bot/ --include="*.py" | head -1', (e2, s2) => {
          if (e2) { console.error(e2); checkNext(); return; }
          let o2 = '';
          s2.on('data', d => o2 += d);
          s2.on('close', () => {
            if (o2.trim()) {
              console.log(fn + ' -> ' + o2.trim());
            } else {
              console.log(fn + ' -> NOT FOUND ❌');
            }
            checkNext();
          });
        });
      };
      checkNext();
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
