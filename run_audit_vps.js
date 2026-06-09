const { Client } = require('ssh2');
const fs = require('fs');
const key = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
const scriptContent = fs.readFileSync('/home/node/.openclaw/workspace/run_audit_vps.py', 'utf8');
const b64Script = Buffer.from(scriptContent).toString('base64');

const conn = new Client();
conn.on('ready', () => {
  conn.exec(`echo '${b64Script}' | base64 -d > /root/run_audit.py && chmod +x /root/run_audit.py`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => {
      console.log('Write result:', out.slice(0,300));
      
      // Now run it
      conn.exec('cd /root && python3 run_audit.py 2>&1', (err2, stream2) => {
        if (err2) { console.error(err2); conn.end(); return; }
        let result = '';
        stream2.on('data', d => result += d.toString());
        stream2.stderr.on('data', d => result += d.toString());
        stream2.on('close', (code) => {
          console.log(`Exit code: ${code}, result length: ${result.length}`);
          fs.writeFileSync('/home/node/.openclaw/workspace/audit_data.json', result);
          console.log('Audit data saved to audit_data.json');
          // Check if it's valid JSON
          try {
            const parsed = JSON.parse(result);
            console.log('Valid JSON with', Object.keys(parsed).length, 'keys');
          } catch(e) {
            console.log('Not valid JSON:', e.message);
            // Save raw output
            fs.writeFileSync('/home/node/.openclaw/workspace/audit_raw.txt', result.slice(0,5000));
          }
          conn.end();
        });
      });
    });
  });
});
conn.connect({ host: '5.223.81.16', username: 'root', privateKey: key, readyTimeout: 15000 });
