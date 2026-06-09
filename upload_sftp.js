const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const conn = new Client();
conn.on('ready', () => {
  console.log('Connected');
  conn.sftp((err, sftp) => {
    if (err) { console.error('SFTP error:', err); conn.end(); return; }
    
    var localFile = '/home/node/.openclaw/workspace/vps_init.py';
    var remoteFile = '/root/psvibe-sale-bot/bot/__init__.py';
    
    var readStream = fs.createReadStream(localFile);
    var writeStream = sftp.createWriteStream(remoteFile, { flags: 'w', mode: 0o644 });
    
    writeStream.on('close', () => {
      console.log('Upload complete');
      
      // Verify
      conn.exec('wc -l /root/psvibe-sale-bot/bot/__init__.py && grep -c "_HAS_API" /root/psvibe-sale-bot/bot/__init__.py', (e, stream) => {
        if (e) { console.error(e); conn.end(); return; }
        var out = '';
        stream.on('data', d => out += d.toString());
        stream.on('close', () => {
          console.log('Verify:', out.trim());
          
          // Restart bot
          conn.exec('systemctl restart psvibe-sale-bot && sleep 2 && systemctl status psvibe-sale-bot --no-pager | head -15', (e2, s2) => {
            if (e2) { console.error(e2); conn.end(); return; }
            var out2 = '';
            s2.on('data', d => out2 += d.toString());
            s2.on('close', () => {
              console.log('Restart:', out2);
              conn.end();
            });
          });
        });
      });
    });
    
    writeStream.on('error', (e) => { console.error('Write error:', e); conn.end(); });
    readStream.pipe(writeStream);
  });
});
conn.on('error', e => console.error('Connect error:', e));
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
