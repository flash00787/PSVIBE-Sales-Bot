const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
conn.on('ready', () => {
  conn.exec(`cd /root/psvibe-sale-bot && grep -c "ConversationHandler" bot/handlers/*.py`, (err, stream) => {
    if (err) { console.error(err); conn.end(); return; }
    let data = '';
    stream.on('data', chunk => data += chunk.toString());
    stream.on('close', () => { console.log('Match counts:', data); conn.end(); process.exit(0); });
  });
}).connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000
});
