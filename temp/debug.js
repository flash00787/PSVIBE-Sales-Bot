const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  // Check what's at line 1205-1215
  conn.exec("sed -n '1200,1220p' /root/psvibe-sales-bot/bot/handlers/members.py", (err, stream) => {
    if (err) { console.error('ERR:', err); conn.end(); return; }
    let out = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.on('close', () => {
      console.log('=== CURRENT LINES 1200-1220 ===');
      console.log(out);
      console.log('=== END ===');
      
      // Also check 1180-1200
      conn.exec("sed -n '1175,1205p' /root/psvibe-sales-bot/bot/handlers/members.py", (err2, s2) => {
        if (err2) { console.error('ERR:', err2); conn.end(); return; }
        let o2 = '';
        s2.on('data', (d) => { o2 += d.toString(); });
        s2.on('close', () => {
          console.log('=== 1175-1205 ===');
          console.log(o2);
          console.log('=== END ===');
          
          // Run Python syntax checker with more detail
          conn.exec("cd /root/psvibe-sales-bot && python3 -c \"import ast; ast.parse(open('bot/handlers/members.py').read()); print('OK')\" 2>&1", (err3, s3) => {
            if (err3) { console.error('ERR:', err3); conn.end(); return; }
            let o3 = '';
            s3.on('data', (d) => { o3 += d.toString(); });
            s3.stderr.on('data', (d) => { o3 += d.toString(); });
            s3.on('close', () => {
              console.log('SYNTAX:', o3.trim());
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
