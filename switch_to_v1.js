const {Client} = require('ssh2');
const c = new Client();
c.on('ready', () => {
  const commands = [
    'echo "=== SWITCHING BACK TO V.1 (MONOLITHIC) ==="',
    'echo "Step 1: Stop V.2 refactored service"',
    'systemctl stop psvibe-bot-refactored',
    'systemctl disable psvibe-bot-refactored',
    '',
    'echo "Step 2: Start V.1 monolithic service"',
    'systemctl enable psvibe-bot',
    'systemctl start psvibe-bot',
    '',
    'echo "Step 3: Clear stale bot.log"',
    '> /root/Sales-Tele-Bot/logs/bot.log',
    '',
    'echo "Step 4: Wait and verify"',
  ].join(' && ');

  c.exec(commands, (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => {
      console.log(o);
      setTimeout(() => {
        c.exec('systemctl is-active psvibe-bot', (e2, s2) => {
          if (e2) { console.error(e2); c.end(); return; }
          let o2 = '';
          s2.on('data', d => o2 += d);
          s2.on('close', () => {
            const st = o2.trim();
            console.log('\nV.1 Status:', st);
            if (st === 'active') {
              c.exec('tail -8 /root/Sales-Tele-Bot/logs/bot.log', (e3, s3) => {
                if (e3) { console.error(e3); c.end(); return; }
                let o3 = '';
                s3.on('data', d => o3 += d);
                s3.on('close', () => { console.log('LOG:\n' + o3); c.end(); });
              });
            } else {
              c.exec('journalctl -u psvibe-bot -n 10 --no-pager 2>&1 | tail -10', (e3, s3) => {
                if (e3) { console.error(e3); c.end(); return; }
                let o3 = '';
                s3.on('data', d => o3 += d);
                s3.on('close', () => { console.log('Journal:\n' + o3); c.end(); });
              });
            }
          });
        });
      }, 10000);
    });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 30000});
