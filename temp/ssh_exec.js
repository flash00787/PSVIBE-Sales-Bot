const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  const cmd = process.argv[2] || 'hostname';
  conn.exec(cmd, (err, stream) => {
    if (err) throw err;
    let out = '';
    let errOut = '';
    stream.on('data', (d) => out += d.toString());
    stream.stderr.on('data', (d) => errOut += d.toString());
    stream.on('close', (code) => {
      console.log(out);
      if (errOut) console.error(errOut);
      process.exit(code);
    });
  });
}).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
});
