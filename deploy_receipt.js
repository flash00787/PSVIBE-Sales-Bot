const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
const KEY_PATH = '/home/node/.openclaw/workspace/.ssh/id_rsa';
const privateKey = fs.readFileSync(KEY_PATH, 'utf8');
const scriptContent = fs.readFileSync('/home/node/.openclaw/workspace/setup_receipt.sh', 'utf8');

conn.on('ready', () => {
  // First upload the script, then run it
  conn.exec('cat > /root/setup_receipt.sh && chmod +x /root/setup_receipt.sh', (err, stream) => {
    if (err) { console.error(err); process.exit(1); }
    stream.stdin.write(scriptContent);
    stream.stdin.end();
    
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => {
      console.log(out);
      
      // Now run the script
      conn.exec('bash /root/setup_receipt.sh 2>&1', (err2, stream2) => {
        if (err2) { console.error(err2); process.exit(1); }
        let out2 = '';
        stream2.on('data', d => out2 += d.toString());
        stream2.stderr.on('data', d => out2 += d.toString());
        stream2.on('close', (code) => {
          console.log(out2);
          console.log(`\nExit code: ${code}`);
          conn.end();
        });
      });
    });
  });
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey,
});
