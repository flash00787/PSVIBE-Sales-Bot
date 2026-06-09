const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  // Step 1: Verify current state - read the critical section
  conn.exec("sed -n '1180,1280p' /root/psvibe-sales-bot/bot/handlers/members.py", (err, stream) => {
    if (err) { console.error('ERROR:', err); conn.end(); return; }
    let out = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.on('close', (code) => {
      console.log('=== CURRENT STATE (1180-1280) ===');
      console.log(out);
      console.log('=== END ===');
      
      // Check line numbers for key markers
      conn.exec("grep -n 'def step_tu_kpay\\|def step_tu_confirm\\|return TU_CONFIRM\\|# Try to parse as amount\\|# Show review (common for both BTN_PAY_DONE' /root/psvibe-sales-bot/bot/handlers/members.py", (err2, s2) => {
        if (err2) { console.error('ERR2:', err2); conn.end(); return; }
        let o2 = '';
        s2.on('data', (d) => { o2 += d.toString(); });
        s2.on('close', () => {
          console.log('=== KEY MARKERS ===');
          console.log(o2);
          conn.end();
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
