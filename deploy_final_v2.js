const {Client} = require('ssh2');
const fs = require('fs');
const c = new Client();
c.on('ready', () => {
  const cmds = [
    'echo "=== FULL CLEAN DEPLOY: V.2 with ALL fixes ==="',
    '',
    'echo "[1/5] Backup current production"',
    'rm -rf /root/Sales-Tele-Bot_refactored.predeploy5',
    'cp -a /root/Sales-Tele-Bot_refactored /root/Sales-Tele-Bot_refactored.predeploy5',
    'echo "  ✅ Backup: predeploy5"',
    '',
    'echo "[2/5] Sync all fixes to staging"',
    'cp -a /root/Sales-Tele-Bot_refactored/bot /root/staging/bot_src/bot',
    'python3 /tmp/fix_pytz.py',
    'python3 /tmp/add_replit_to_handlers.py',
    'echo "  ✅ Staging synced"',
    '',
    'echo "[3/5] Clean copy staging to production"',
    'rm -rf /root/Sales-Tele-Bot_refactored',
    'cp -a /root/staging/bot_src /root/Sales-Tele-Bot_refactored',
    'echo "  ✅ Production replaced from staging"',
    '',
    'echo "[4/5] Apply all fixes on production"',
    'python3 /tmp/fix_pytz.py',
    'python3 /tmp/add_replit_to_handlers.py',
    'python3 /tmp/fixmm2.py',
    'for f in /root/Sales-Tele-Bot_refactored/bot/handlers/*.py; do',
    '  if grep -q "from bot import now_mmt" "$f"; then',
    '    sed -i "s/from bot import now_mmt/from bot.handlers import */" "$f"',
    '    echo "  fix: $(basename $f)"',
    '  fi',
    'done',
    'echo "  ✅ All fixes applied"',
    '',
    'echo "[5/5] Clean cache and restart"',
    'rm -rf /root/Sales-Tele-Bot_refactored/bot/__pycache__ /root/Sales-Tele-Bot_refactored/bot/handlers/__pycache__',
    'systemctl restart psvibe-bot-refactored',
    'echo "  ✅ Service restarted"',
  ].join('\n');
  
  c.exec(cmds, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      console.log('Deploy output:\n' + o);
      console.log('Waiting 12s...');
      setTimeout(() => {
        c.exec('systemctl is-active psvibe-bot-refactored', (e2, s2) => {
          if (e2) { console.error(e2); c.end(); return; }
          let o2 = '';
          s2.on('data', d => o2 += d);
          s2.on('close', () => {
            const st = o2.trim();
            console.log('Status:', st);
            if (st === 'active') {
              c.exec('tail -12 /root/Sales-Tele-Bot_refactored/logs/bot.log', (e3, s3) => {
                if (e3) { console.error(e3); c.end(); return; }
                let o3 = '';
                s3.on('data', d => o3 += d);
                s3.on('close', () => { console.log('LOG:\n' + o3); c.end(); });
              });
            } else {
              c.exec('journalctl -u psvibe-bot-refactored -n 15 --no-pager 2>&1 | grep "Error\\|Traceback\\|Python" | tail -10', (e3, s3) => {
                if (e3) { console.error(e3); c.end(); return; }
                let o3 = '';
                s3.on('data', d => o3 += d);
                s3.on('close', () => { console.log(o3); c.end(); });
              });
            }
          });
        });
      }, 12000);
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 60000});
