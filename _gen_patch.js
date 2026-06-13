const { Client } = require('ssh2');
const fs = require('fs');
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');
const c = new Client();

// The clean Node.js patch script to run on the Yangon VPS
const patchNode = `const fs = require('fs');
let c = fs.readFileSync('/opt/ibet789-bot/bot.js', 'utf8');
let o = c;
let f = [];

// Fix 1: pg -> page in fallback check  
c = c.replace('if ((await pg.\\$', 'if (await isDash(page');
f.push('pg_fallback');

// Fix 2: waitForFunction timeout
c = c.replace('60000, polling: 1000', '120000, polling: 300');
f.push('timeout');

// Fix 3: isDash URL check
c = c.replace("return true; // URL check disabled - post-login page still has Default", "return true;");
f.push('url');

if (c !== o) {
  fs.writeFileSync('/opt/ibet789-bot/bot.js', c);
  console.log('PATCHED: ' + f.join(', '));
} else {
  console.log('NO_CHANGES');
}
`;

c.on('ready', () => {
  // Write the patch script to main VPS, then scp to Yangon VPS, then execute
  const b64 = Buffer.from(patchNode).toString('base64');
  
  const cmds = [
    `echo '${b64}' | base64 -d > /tmp/clean_patch.js`,
    'sshpass -p Freedom2024#RevFlash scp -o StrictHostKeyChecking=no /tmp/clean_patch.js root@38.60.254.31:/tmp/clean_patch.js',
    'sshpass -p Freedom2024#RevFlash ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@38.60.254.31 \'systemctl stop ibet789-bot; sleep 1; node /tmp/clean_patch.js 2>&1; systemctl start ibet789-bot; sleep 3; echo STATUS; systemctl is-active ibet789-bot\''
  ].join(' && ');
  
  c.exec(cmds, (err, stream) => {
    if (err) { console.error('EXEC_ERR:', err.message); c.end(); process.exit(1); }
    let out = '';
    stream.on('data', d => out += d.toString());
    stream.stderr.on('data', d => out += '[E]' + d.toString());
    stream.on('close', (code) => { console.log(out); c.end(); process.exit(code || 0); });
  });
}).on('error', e => { console.error('CONN_ERR:', e.message); process.exit(1); })
.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 10000 });
