const {Client} = require('ssh2');
const fs = require('fs');
const task = fs.readFileSync('/home/node/.openclaw/workspace/TASK_payment_design.md', 'utf8');
const c = new Client();
c.on('ready', () => {
  // Write via base64 to avoid quoting issues
  const b64 = Buffer.from(task).toString('base64');
  c.exec(`echo ${b64} | base64 -d > "/root/Aung Chan Myint/.coordination/TASK_payment_design.md" && echo UPLOADED`, (e, s) => {
    let o = '';
    s.on('data', d => o += d);
    s.stderr.on('data', d => o += d);
    s.on('close', () => { console.log(o); c.end(); });
  });
}).connect({host:'5.223.81.16', username:'root', privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')});
