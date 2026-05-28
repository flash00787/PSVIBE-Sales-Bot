const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH connected');
  
  const backupCmd = 'tar -czf /root/Sales-Tele-Bot_backup_$(date +%F_%H-%M-%S).tar.gz -C /root Sales-Tele-Bot 2>&1';
  console.log(`Executing backup command: ${backupCmd}`);
  
  conn.exec(backupCmd, (err, stream) => {
    if (err) {
      console.error('EXEC ERROR:', err);
      conn.end();
      return;
    }
    let output = '';
    stream.on('data', (data) => { output += data.toString(); });
    stream.stderr.on('data', (data) => { output += data.toString(); });
    stream.on('close', (code) => {
      console.log('Output:', output || '(none)');
      console.log(`Exit code: ${code}`);
      
      // Verify backup exists and show its size
      conn.exec('ls -lh /root/Sales-Tele-Bot_backup_*.tar.gz', (err2, stream2) => {
        let verifyOutput = '';
        stream2.on('data', (data) => { verifyOutput += data.toString(); });
        stream2.on('close', () => {
          console.log('\n===== VERIFY BACKUPS =====');
          console.log(verifyOutput);
          conn.end();
        });
      });
    });
  });
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err);
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
