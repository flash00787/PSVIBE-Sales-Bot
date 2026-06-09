const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  // Reset to clean local master version (the one with dynamic payment support)
  conn.exec('cd /root/psvibe-sales-bot && git checkout HEAD -- bot/handlers/members.py && echo "CLEAN"', (err, stream) => {
    if (err) { console.error('ERR:', err); conn.end(); return; }
    let out = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.stderr.on('data', (d) => { out += d.toString(); });
    stream.on('close', () => {
      console.log('Reset:', out.trim());
      
      // Read the step_tu_kpay function
      conn.exec("sed -n '1140,1280p' /root/psvibe-sales-bot/bot/handlers/members.py", (err2, s2) => {
        if (err2) { console.error('ERR2:', err2); conn.end(); return; }
        let o2 = '';
        s2.on('data', (d) => { o2 += d.toString(); });
        s2.on('close', () => {
          console.log('=== CLEAN LOCAL MASTER (1140-1280) ===');
          console.log(o2);
          console.log('=== END ===');
          
          // Also get markers
          conn.exec("grep -n 'def step_tu_kpay\\|def step_tu_confirm\\|# Try to parse as amount\\|# Check if text is BTN_PAY_DONE\\|# Show review (common for both.*BTN_PAY_DONE' /root/psvibe-sales-bot/bot/handlers/members.py", (err3, s3) => {
            if (err3) { console.error('ERR3:', err3); conn.end(); return; }
            let o3 = '';
            s3.on('data', (d) => { o3 += d.toString(); });
            s3.on('close', () => {
              console.log('=== MARKERS ===');
              console.log(o3);
              conn.end();
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
