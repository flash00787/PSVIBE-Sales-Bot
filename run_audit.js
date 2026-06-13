const { Client } = require('ssh2');
const fs = require('fs');

const script = fs.readFileSync('/home/node/.openclaw/workspace/cashflow_audit.py', 'utf8');

const conn = new Client();
conn.on('ready', () => {
  conn.exec('python3 /dev/stdin', (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let out = '';
    stream.stdin.write(script);
    stream.stdin.end();
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { out += 'STDERR:' + d.toString(); });
    stream.on('close', (code) => {
      console.log(out.trimEnd());
      conn.end();
      if (code !== 0) process.exitCode = code;
    });
  });
});
conn.on('error', (e) => { console.error('SSH error:', e); process.exit(1); });
conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
