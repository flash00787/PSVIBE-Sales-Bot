const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

conn.on('ready', () => {
  console.log('SSH connected');
  
  // Read lines 1190-1250 to verify the fix
  conn.exec("sed -n '1190,1260p' /root/psvibe-sales-bot/bot/handlers/members.py", (err, stream) => {
    if (err) { console.error('ERROR:', err); conn.end(); return; }
    let out = '';
    stream.on('data', (d) => { out += d.toString(); });
    stream.stderr.on('data', (d) => { console.error('STDERR:', d.toString()); });
    stream.on('close', () => {
      console.log('=== LINES 1190-1260 (after fix) ===');
      console.log(out);
      console.log('=== END ===');
      
      // Also check around return TU_CONFIRM
      conn.exec("grep -n 'return TU_CONFIRM\\|# Try to parse\\|# Show review' /root/psvibe-sales-bot/bot/handlers/members.py | grep -A5 -B5 'step_tu_kpay\\|TU_CONFIRM\\|Try to parse\\|Show review' | tail -20", (err2, stream2) => {
        if (err2) { console.error('ERROR2:', err2); conn.end(); return; }
        let out2 = '';
        stream2.on('data', (d) => { out2 += d.toString(); });
        stream2.on('close', () => {
          console.log('=== MARKER POSITIONS ===');
          console.log(out2);
          console.log('=== END ===');
          
          // Final syntax check
          conn.exec('cd /root/psvibe-sales-bot && python3 -c "import ast; ast.parse(open(\'bot/handlers/members.py\').read()); print(\'SYNTAX OK\')" && python3 -c "import py_compile; py_compile.compile(\'bot/handlers/members.py\', doraise=True); print(\'COMPILE OK\')"', (err3, stream3) => {
            if (err3) { console.error('ERROR3:', err3); conn.end(); return; }
            let out3 = '';
            stream3.on('data', (d) => { out3 += d.toString(); });
            stream3.on('close', () => {
              console.log('=== VERIFY ===');
              console.log(out3);
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
