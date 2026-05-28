const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();

conn.on('ready', () => {
  console.log('SSH Connected — preparing file uploads');

  conn.sftp((err, sftp) => {
    if (err) {
      console.error('SFTP Error:', err);
      conn.end();
      return;
    }

    const uploads = [
      { local: '/home/node/.openclaw/workspace/token.json', remote: '/root/token.json' },
      { local: '/home/node/.openclaw/workspace/psvibe_bots_audit_report.md', remote: '/root/psvibe_bots_audit_report.md' },
      { local: '/home/node/.openclaw/workspace/send_audit_with_attachment.py', remote: '/root/send_audit_with_attachment.py' }
    ];

    let uploadIdx = 0;

    function uploadNext() {
      if (uploadIdx >= uploads.length) {
        console.log('All files uploaded successfully!');
        executeEmailScript();
        return;
      }

      const item = uploads[uploadIdx++];
      console.log(`Uploading ${item.local} -> ${item.remote}`);
      sftp.fastPut(item.local, item.remote, {}, (uploadErr) => {
        if (uploadErr) {
          console.error(`Upload error for ${item.local}:`, uploadErr);
          conn.end();
          return;
        }
        uploadNext();
      });
    }

    uploadNext();
  });

  function executeEmailScript() {
    console.log('\nInstalling google-api-python-client in VPS Wallet Bot venv...');
    const pipCmd = '/root/Personal-Wallet-Tele-Bot-2/bot/venv/bin/pip install google-api-python-client';
    
    conn.exec(pipCmd, { pty: false }, (err, stream) => {
      if (err) {
        console.error('SSH Pip Exec Error:', err);
        conn.end();
        return;
      }
      let pipOutput = '';
      stream.on('data', (data) => { 
        pipOutput += data.toString();
        process.stdout.write(data.toString()); // print real-time to log
      });
      stream.stderr.on('data', (data) => { 
        pipOutput += data.toString();
        process.stderr.write(data.toString());
      });
      stream.on('close', (pipCode) => {
        console.log(`\nPip install exited with code: ${pipCode}`);
        
        console.log('\nExecuting send_audit_with_attachment.py on VPS using Wallet Bot venv...');
        const cmd = '/root/Personal-Wallet-Tele-Bot/bot/venv/bin/python3 /root/send_audit_with_attachment.py';
        
        conn.exec(cmd, { pty: false }, (err2, stream2) => {
          if (err2) {
            console.error('SSH Exec Error:', err2);
            conn.end();
            return;
          }
          let output = '';
          stream2.on('data', (data) => { output += data.toString(); });
          stream2.stderr.on('data', (data) => { output += data.toString(); });
          stream2.on('close', (code) => {
            console.log('--- REMOTE EXECUTION OUTPUT ---');
            console.log(output.trim() || '(No output)');
            console.log('-------------------------------');
            console.log(`Exit code: ${code}`);
            cleanupRemoteFiles();
          });
        });
      });
    });
  }

  function cleanupRemoteFiles() {
    console.log('\nCleaning up send_audit_with_attachment.py and token.json on VPS...');
    const cleanupCmd = 'rm -f /root/send_audit_with_attachment.py /root/token.json';
    conn.exec(cleanupCmd, { pty: false }, (err, stream) => {
      conn.end();
      console.log('SSH connection closed. Done!');
    });
  }
});

conn.on('error', (err) => {
  console.error('SSH ERROR:', err);
  process.exit(1);
});

conn.connect({
  host: '167.71.196.120',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
