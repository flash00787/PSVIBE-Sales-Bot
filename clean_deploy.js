const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  const cmds = [
    'echo "=== PRE-DEPLOY BACKUP ==="',
    'rm -rf /root/Sales-Tele-Bot_refactored.predeploy3',
    'cp -a /root/Sales-Tele-Bot_refactored /root/Sales-Tele-Bot_refactored.predeploy3',
    'echo "Backup: Sales-Tele-Bot_refactored.predeploy3"',
    '',
    'echo "=== CLEAN STAGING->PRODUCTION COPY ==="',
    'rm -rf /root/Sales-Tele-Bot_refactored',
    'cp -a /root/staging/bot_src /root/Sales-Tele-Bot_refactored',
    'echo "Staging fully copied to production"',
    '',
    'echo "=== APPLY ALL FIXES TO PRODUCTION ==="',
    'for f in /root/Sales-Tele-Bot_refactored/bot/handlers/*.py; do',
    '  if grep -q "from bot import now_mmt" "$f"; then',
    '    sed -i "s/from bot import now_mmt/from bot import */" "$f"',
    '    echo "  import fixed: $(basename $f)"',
    '  fi',
    'done',
    '',
    'python3 /tmp/fix_btn_constants.py',
    'python3 /tmp/fix_vars.py',
    '',
    'echo "=== RESTART ==="',
    'systemctl restart psvibe-bot-refactored',
  ].join(' && ');
  
  c.exec(cmds, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      console.log(o);
      // Wait for restart
      setTimeout(() => {
        c.exec('systemctl is-active psvibe-bot-refactored && echo "---" && tail -3 /root/Sales-Tele-Bot_refactored/logs/bot.log', (e2, s2) => {
          if (e2) { console.error(e2); c.end(); return; }
          let o2 = '';
          s2.on('data', d => o2 += d);
          s2.on('close', () => { console.log(o2); c.end(); });
        });
      }, 8000);
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 30000});
