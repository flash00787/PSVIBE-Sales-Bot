const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  // Read the Python script
  const script = fs.readFileSync('/home/node/.openclaw/workspace/temp/apply_fix.py', 'utf8');
  
  // First write the file via stdin
  conn.exec('cat > /tmp/apply_fix.py && python3 /tmp/apply_fix.py', (err, stream) => {
    if (err) { console.error('exec err:', err); process.exit(1); }
    
    let out = '';
    let errOut = '';
    stream.on('data', (d) => out += d.toString());
    stream.stderr.on('data', (d) => errOut += d.toString());
    
    // Write script to stdin
    stream.write(script);
    stream.end();
    
    stream.on('close', (code) => {
      console.log('STDOUT:', out);
      console.log('STDERR:', errOut);
      console.log('EXIT:', code);
      process.exit(code);
    });
  });
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
});
