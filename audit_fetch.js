const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
const files = [
  '/root/Aung Chan Myint/Sales-Tele-Bot/main.py',
  '/root/Aung Chan Myint/Sales-Tele-Bot/bot/__init__.py',
  '/root/Aung Chan Myint/Sales-Tele-Bot/bot/app.py',
  '/root/Aung Chan Myint/Sales-Tele-Bot/bot/handlers.py',
];

const localDir = '/home/node/.openclaw/workspace/audit_files';
if (!fs.existsSync(localDir)) fs.mkdirSync(localDir, { recursive: true });

conn.on('ready', () => {
  console.log('Connected');
  let pending = files.length;
  files.forEach((remotePath) => {
    conn.sftp((err, sftp) => {
      if (err) { console.error('SFTP error:', err); return; }
      sftp.stat(remotePath, (err, stat) => {
        if (err) {
          console.error(`STAT ERROR for ${remotePath}:`, err.message);
          pending--;
          if (pending === 0) conn.end();
          return;
        }
        console.log(`${remotePath}: ${stat.size} bytes`);
        
        // Use fastGet for large files
        const localName = remotePath.replace(/\//g, '_').replace(/\s/g, '_');
        const localPath = path.join(localDir, localName);
        
        sftp.fastGet(remotePath, localPath, (err) => {
          if (err) {
            console.error(`FASTGET ERROR for ${remotePath}:`, err.message);
          } else {
            console.log(`Downloaded ${remotePath} -> ${localPath} (${stat.size} bytes)`);
          }
          pending--;
          if (pending === 0) conn.end();
        });
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
