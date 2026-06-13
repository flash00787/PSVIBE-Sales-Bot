const { Client } = require('ssh2');
const fs = require('fs');

const pyCode = fs.readFileSync('/home/node/.openclaw/workspace/formula_check.py', 'utf8');

const conn = new Client();
conn.on('ready', () => {
  conn.exec('cat > /tmp/formula_check.py', (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let out = '';
    stream.stdin.write(pyCode);
    stream.stdin.end();
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { out += 'E:' + d.toString(); });
    stream.on('close', (code) => {
      // Now run it
      conn.exec('python3 /tmp/formula_check.py', (err2, stream2) => {
        if (err2) { console.error(err2); conn.end(); return; }
        let out2 = '';
        stream2.on('data', d => out2 += d.toString());
        stream2.stderr.on('data', d => out2 += d.toString());
        stream2.on('close', () => {
          console.log(out2.trimEnd());
          conn.end();
        });
      });
    });
  });
});
conn.on('error', (e) => { console.error('SSH:', e); process.exit(1); });
conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
