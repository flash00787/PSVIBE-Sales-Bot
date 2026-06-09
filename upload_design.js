const {Client} = require('ssh2');
const fs = require('fs');
const design = fs.readFileSync('/home/node/.openclaw/workspace/payment_design.md', 'utf8');
const c = new Client();
c.on('ready', () => {
  const b64 = Buffer.from(design).toString('base64');
  c.exec(`echo ${b64} | base64 -d > "/root/Aung Chan Myint/.coordination/payment_design.md" && echo UPLOADED`, (e, s) => {
    let o = '';
    s.on('data', d => o += d);
    s.stderr.on('data', d => o += d);
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host:'5.223.81.16', username:'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')});
