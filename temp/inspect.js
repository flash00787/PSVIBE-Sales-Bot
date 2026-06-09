const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  // Check the function around step_tu_kpay
  conn.exec("sed -n '1030,1150p' /root/psvibe-sales-bot/bot/handlers/members.py", (err, stream) => {
    if (err) { console.error('ERR:', err); conn.end(); return; }
    let out = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.on('close', () => {
      console.log('=== step_tu_kpay in origin ===');
      console.log(out);
      console.log('=== END ===');
      
      // Check git log for this file
      conn.exec("cd /root/psvibe-sales-bot && git log --oneline -10 -- bot/handlers/members.py", (err2, s2) => {
        if (err2) { console.error('ERR2:', err2); conn.end(); return; }
        let o2 = '';
        s2.on('data', (d) => { o2 += d.toString(); });
        s2.on('close', () => {
          console.log('=== GIT LOG ===');
          console.log(o2);
          
          // Restore to the latest LOCAL commit (not origin)
          conn.exec("cd /root/psvibe-sales-bot && git checkout master -- bot/handlers/members.py && git stash pop 2>/dev/null; echo 'restored to master'", (err3, s3) => {
            if (err3) { console.error('ERR3:', err3); conn.end(); return; }
            let o3 = '';
            s3.on('data', (d) => { o3 += d.toString(); });
            s3.on('close', () => {
              console.log('RESTORE:', o3.trim());
              
              // Verify markers in local master
              conn.exec("grep -n 'def step_tu_kpay\\|# Try to parse as amount\\|def step_tu_confirm\\|# Check if text is BTN_PAY_DONE\\|# Show review (common for both.*BTN_PAY_DONE' /root/psvibe-sales-bot/bot/handlers/members.py", (err4, s4) => {
                if (err4) { console.error('ERR4:', err4); conn.end(); return; }
                let o4 = '';
                s4.on('data', (d) => { o4 += d.toString(); });
                s4.on('close', () => {
                  console.log('=== LOCAL MASTER MARKERS ===');
                  console.log(o4);
                  conn.end();
                });
              });
            });
          });
        });
      });
    });
  });
});

conn.on('error', (err) => { console.error('SSH ERROR:', err); });

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: privateKey,
  readyTimeout: 15000,
});
