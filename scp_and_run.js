const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  conn.sftp((err, sftp) => {
    if (err) { console.error('SFTP error:', err); conn.end(); process.exit(1); }
    const readStream = fs.createReadStream('/home/node/.openclaw/workspace/fix_sales.py');
    const writeStream = sftp.createWriteStream('/tmp/fix_sales.py');
    writeStream.on('close', () => {
      console.log('File copied. Now running...');
      conn.exec('python3 /tmp/fix_sales.py', { timeout: 30000 }, (err, stream) => {
        if (err) { console.error('Exec error:', err); conn.end(); process.exit(1); }
        let out = '';
        stream.on('data', (d) => { out += d.toString(); });
        stream.stderr.on('data', (d) => { out += d.toString(); });
        stream.on('close', (code) => {
          console.log(out.trim());
          conn.end();
          process.exit(code || 0);
        });
      });
    });
    readStream.pipe(writeStream);
  });
}).on('error', (e) => { console.error('SSH error:', e.message); process.exit(1); }).connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
