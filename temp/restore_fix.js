const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  // Check git status and restore
  conn.exec('cd /root/psvibe-sales-bot && git status bot/handlers/members.py && git diff bot/handlers/members.py | head -100', (err, stream) => {
    if (err) { console.error('ERROR:', err); conn.end(); return; }
    let out = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.stderr.on('data', (d) => { out += d.toString(); });
    stream.on('close', (code) => {
      console.log('GIT STATUS:', out.substring(0, 500));
      
      // Restore original
      conn.exec('cd /root/psvibe-sales-bot && git checkout bot/handlers/members.py', (err2, stream2) => {
        if (err2) { console.error('RESTORE ERROR:', err2); conn.end(); return; }
        let out2 = '';
        stream2.on('data', (d) => { out2 += d.toString(); });
        stream2.stderr.on('data', (d) => { out2 += d.toString(); });
        stream2.on('close', (code2) => {
          console.log('RESTORE:', out2, 'exit:', code2);
          
          // Verify restored file - check lines around the issue
          conn.exec("sed -n '1245,1275p' /root/psvibe-sales-bot/bot/handlers/members.py", (err3, stream3) => {
            if (err3) { console.error('VERIFY ERR:', err3); conn.end(); return; }
            let out3 = '';
            stream3.on('data', (d) => { out3 += d.toString(); });
            stream3.on('close', () => {
              console.log('=== RESTORED LINES 1245-1275 ===');
              console.log(out3);
              console.log('=== END ===');
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
