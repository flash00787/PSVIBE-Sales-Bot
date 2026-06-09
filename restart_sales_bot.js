const { Client } = require('ssh2');

const conn = new Client();
conn.on('ready', () => {
  conn.exec('systemctl restart psvibe-sale-bot.service 2>&1; sleep 5; systemctl is-active psvibe-sale-bot.service 2>&1; echo "---PID: $(systemctl show psvibe-sale-bot.service --property MainPID --value)---"', (err, stream) => {
    let out = '';
    stream.on('data', d => out += d);
    stream.on('close', () => { console.log(out); conn.end(); });
  });
});
conn.connect({
  host: '5.223.81.16', port: 22, username: 'root',
  privateKey: require('fs').readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
