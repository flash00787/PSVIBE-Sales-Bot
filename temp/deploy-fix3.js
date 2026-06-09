const { Client } = require('ssh2');
const fs = require('fs');
const fixScript = fs.readFileSync('/home/node/.openclaw/workspace/temp/fix_bug3.py', 'utf8');
const newFunc = fs.readFileSync('/home/node/.openclaw/workspace/temp/new_cmd_mybookings.txt', 'utf8');

const conn = new Client();
conn.on('ready', () => {
  // Step 1: Write the new function file
  conn.exec('cat > /tmp/new_cmd_mybookings.txt', (err, stream) => {
    if (err) throw err;
    stream.end(newFunc);
    let leftover = '';
    stream.on('data', d => { leftover += d.toString(); });
    stream.on('close', () => {
      // Step 2: Write and run the fix script
      conn.exec('cat > /tmp/fix_bug3.py && python3 /tmp/fix_bug3.py', (err2, stream2) => {
        if (err2) throw err2;
        let out = '', eout = '';
        stream2.on('data', d => out += d.toString());
        stream2.stderr.on('data', d => eout += d.toString());
        stream2.on('close', code => {
          if (eout) process.stderr.write(eout);
          process.stdout.write(out);
          // Cleanup
          conn.exec('rm /tmp/fix_bug3.py /tmp/new_cmd_mybookings.txt', () => conn.end());
        });
        stream2.end(fixScript);
      });
    });
  });
});
conn.on('error', err => { console.error(err.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'), readyTimeout: 15000 });
