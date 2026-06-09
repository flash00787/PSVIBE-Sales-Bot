const {Client} = require('ssh2');
const fs = require('fs');

// Step 1: Also fix staging
const s = fs.readFileSync('/home/node/.openclaw/workspace/fix_pytz.py', 'utf8');
const staging_script = s.replace(
  "/root/Sales-Tele-Bot_refactored/bot/handlers/__init__.py",
  "/root/staging/bot_src/bot/handlers/__init__.py"
);

fs.writeFileSync('/tmp/fix_pytz_staging.py', staging_script);

const c = new Client();
c.on('ready', () => {
  // Fix staging + restart
  c.exec('python3 /tmp/fix_pytz.py && python3 /tmp/fix_pytz_staging.py && systemctl restart psvibe-bot-refactored', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      console.log('Fixes applied, restarting...');
      setTimeout(() => {
        c.exec('systemctl is-active psvibe-bot-refactored', (e2, s2) => {
          if (e2) { console.error(e2); c.end(); return; }
          let o2 = '';
          s2.on('data', d => o2 += d);
          s2.on('close', () => {
            const status = o2.trim();
            console.log('Status:', status);
            if (status === 'active') {
              c.exec('tail -15 /root/Sales-Tele-Bot_refactored/logs/bot.log', (e3, s3) => {
                if (e3) { console.error(e3); c.end(); return; }
                let o3 = '';
                s3.on('data', d => o3 += d);
                s3.on('close', () => { console.log('LOG:\n' + o3); c.end(); });
              });
            } else {
              c.exec('systemctl status psvibe-bot-refactored 2>&1 | tail -20', (e3, s3) => {
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
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 30000});
