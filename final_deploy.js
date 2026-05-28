const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  c.exec('systemctl is-active psvibe-bot-refactored', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      const active = o.trim() === 'active';
      console.log('V.2 currently:', o.trim());
      if (active) {
        console.log('Already running — checking code matches staging...');
        c.exec('diff -r /root/staging/bot_src/bot /root/Sales-Tele-Bot_refactored/bot | head -5', (e2, s2) => {
          if (e2) { console.error(e2); c.end(); return; }
          let o2 = '';
          s2.on('data', d => o2 += d);
          s2.on('close', () => {
            if (o2.trim()) {
              console.log('Differences found — re-deploying:\n', o2.slice(0, 500));
              fullDeploy(c);
            } else {
              console.log('Production matches staging. Already deployed.');
              c.end();
            }
          });
        });
      } else {
        fullDeploy(c);
      }
    });
  });
  
  function fullDeploy(client) {
    const deploy = [
      'echo "=== FULL CLEAN DEPLOY ==="',
      'echo "1. Backup current production"',
      'rm -rf /root/Sales-Tele-Bot_refactored.predeploy4',
      'cp -a /root/Sales-Tele-Bot_refactored /root/Sales-Tele-Bot_refactored.predeploy4',
      'echo "Backup: predeploy4"',
      '',
      'echo "2. Clean copy staging to production"',
      'rm -rf /root/Sales-Tele-Bot_refactored',
      'cp -a /root/staging/bot_src /root/Sales-Tele-Bot_refactored',
      'echo "Copied"',
      '',
      'echo "3. Re-apply all fixes"',
      'for f in /root/Sales-Tele-Bot_refactored/bot/handlers/*.py; do',
      '  if grep -q "from bot import now_mmt" "$f"; then',
      '    sed -i "s/from bot import now_mmt/from bot import */" "$f"',
      '    echo "  import: $(basename $f)"',
      '  fi',
      'done',
      'python3 /tmp/fix_btn_constants.py',
      'python3 /tmp/fix_vars.py',
      'python3 /tmp/fixmm2.py',
      'echo "All fixes applied"',
      '',
      'echo "4. Restart service"',
      'systemctl restart psvibe-bot-refactored',
    ].join(' && ');
    
    client.exec(deploy, (e2, s2) => {
      if (e2) { console.error(e2); client.end(); return; }
      let o2 = '';
      s2.on('data', d => o2 += d);
      s2.on('close', () => {
        console.log(o2);
        console.log('Restarting, waiting 10s...');
        setTimeout(() => {
          client.exec('systemctl is-active psvibe-bot-refactored', (e3, s3) => {
            if (e3) { console.error(e3); client.end(); return; }
            let o3 = '';
            s3.on('data', d => o3 += d);
            s3.on('close', () => {
              console.log('Status:', o3.trim());
              client.exec('tail -5 /root/Sales-Tele-Bot_refactored/logs/bot.log', (e4, s4) => {
                if (e4) { console.error(e4); client.end(); return; }
                let o4 = '';
                s4.on('data', d => o4 += d);
                s4.on('close', () => { console.log('Log:\n' + o4); client.end(); });
              });
            });
          });
        }, 10000);
      });
    });
  }
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 30000});
