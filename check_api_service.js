const {Client} = require('ssh2');
const conn = new Client();
conn.on('ready', () => {
  const cmds = `cat /etc/systemd/system/psvibe-api.service 2>&1`;
  conn.exec(cmds, (err, stream) => {
    if (err) { console.log('ERR:', err.message); conn.end(); return; }
    let out='';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += d.toString());
    stream.on('close', () => { console.log(out); conn.end(); });
  });
}).connect({ host:'5.223.81.16', port:22, username:'root', privateKey: require('fs').readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa') });
