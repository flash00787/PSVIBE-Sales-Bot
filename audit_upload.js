const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();

conn.on('ready', () => {
  console.log('Connected');
  conn.sftp((err, sftp) => {
    if (err) { console.error('SFTP error:', err); conn.end(); return; }
    
    // First create directory
    conn.exec('mkdir -p "/root/Aung Chan Myint/.coordination"', (err) => {
      if (err) { console.error('mkdir error:', err); }
      
      const localFile = '/home/node/.openclaw/workspace/AUDIT_PARITY.md';
      const remoteFile = '/root/Aung Chan Myint/.coordination/AUDIT_PARITY.md';
      
      sftp.fastPut(localFile, remoteFile, (err) => {
        if (err) {
          console.error('Upload error:', err.message);
        } else {
          const stat = fs.statSync(localFile);
          console.log(`Uploaded ${localFile} -> ${remoteFile} (${stat.size} bytes)`);
        }
        conn.end();
      });
    });
  });
});

conn.on('error', (err) => {
  console.error('Connection error:', err.message);
  process.exit(1);
});

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 30000,
});
