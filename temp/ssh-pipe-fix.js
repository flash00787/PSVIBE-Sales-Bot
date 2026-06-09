const { Client } = require('ssh2');
const fs = require('fs');

const script = fs.readFileSync('/home/node/.openclaw/workspace/temp/fix_bug3.py', 'utf8');

const conn = new Client();
conn.on('ready', () => {
  // First write the script to VPS
  conn.exec('cat > /tmp/fix_bug3.py && python3 /tmp/fix_bug3.py', (err, stream) => {
    if (err) throw err;
    let output = '';
    let errOutput = '';
    stream.on('data', (d) => { output += d.toString(); });
    stream.stderr.on('data', (d) => { errOutput += d.toString(); });
    stream.on('close', (code) => {
      if (errOutput) process.stderr.write(errOutput);
      process.stdout.write(output);
      // Clean up
      conn.exec('rm /tmp/fix_bug3.py', () => { conn.end(); });
    });
    // Pipe the script into stdin
    stream.end(script);
  });
});
conn.on('error', (err) => { console.error('SSH Error:', err.message); process.exit(1); });
conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
