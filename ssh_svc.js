const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  conn.exec('cat /etc/systemd/system/psvibe-api.service', (err, s) => {
    let d=''; s.on('data',c=>d+=c); s.on('close',()=>{ console.log(d); conn.end(); });
  });
});
conn.connect({host:'5.223.81.16',port:22,username:'root',privateKey:fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),readyTimeout:15000});
