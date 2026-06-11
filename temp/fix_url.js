const fs = require('fs');
const Client = require('ssh2').Client;

const conn = new Client();
conn.on('ready', () => {
  // Read current .env
  conn.exec('cat /opt/ibet789-bot/.env', (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let data = '';
    stream.on('data', d => data += d);
    stream.stderr.on('data', d => data += d);
    stream.on('close', () => {
      // Clean all broken AGENT_URL lines and add correct one
      const lines = data.split('\n').filter(l => !l.startsWith('AGENT_URL=') && !l.startsWith('AGENT…'));
      lines.push('AGENT_URL=https://ag.ibet789.com');
      const newContent = lines.join('\n');
      
      // Write back using base64 to avoid shell escaping issues
      const base64 = Buffer.from(newContent).toString('base64');
      conn.exec('base64 -d > /opt/ibet789-bot/.env', (err2, stream2) => {
        if (err2) { console.error(err2); conn.end(); return; }
        stream2.stdin.write(base64);
        stream2.stdin.end();
        stream2.on('close', () => {
          conn.exec('cat /opt/ibet789-bot/.env | grep AGENT_URL', (err3, stream3) => {
            if (err3) { console.error(err3); conn.end(); return; }
            let out = '';
            stream3.on('data', d => out += d);
            stream3.stderr.on('data', d => out += d);
            stream3.on('close', () => {
              console.log('AGENT_URL line:', out);
              
              // Restart bot
              conn.exec('systemctl restart ibet789-bot', (err4, stream4) => {
                if (err4) { console.error(err4); conn.end(); return; }
                setTimeout(() => {
                  conn.exec('journalctl -u ibet789-bot --no-pager -n 3 | grep -i "agent url"', (err5, stream5) => {
                    let o = '';
                    stream5.on('data', d => o += d);
                    stream5.stderr.on('data', d => o += d);
                    stream5.on('close', () => {
                      console.log('Bot log:', o || '(checking)');
                      conn.end();
                    });
                  });
                }, 2000);
              });
            });
          });
        });
      });
    });
  });
});

conn.connect({
  host: '5.223.81.16',
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000,
});
