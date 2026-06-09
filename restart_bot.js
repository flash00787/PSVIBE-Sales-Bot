const { Client } = require('ssh2');
const conn = new Client();
conn.on('ready', () => {
  conn.exec('systemctl restart psvibe-sale-bot.service', (err, stream) => {
    let out = '';
    stream.on('data', d => out += d);
    stream.stderr.on('data', d => out += d);
    stream.on('close', () => { console.log('Restart cmd done:', out); conn.end(); });
  });
});
conn.connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: require('fs').readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
