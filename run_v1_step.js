const {Client} = require('ssh2');
const fs = require('fs');
const s = fs.readFileSync('/home/node/.openclaw/workspace/v1_step_functions.py', 'utf8');
const b = Buffer.from(s).toString('base64');
const c = new Client();
c.on('ready', () => {
  c.exec('base64 -d > /tmp/v1_step_funcs.py <<< "' + b + '" && python3 /tmp/v1_step_funcs.py', (e, s) => {
    if (e) { console.error(e); c.end(); return; }
    let o = '';
    s.on('data', d => o += d);
    s.on('close', () => { console.log(o || '(no output)'); c.end(); });
  });
}).connect({host: '167.71.196.120', port: 22, username: 'root', password: 'Freedom2024#RevFlash', readyTimeout: 15000});
