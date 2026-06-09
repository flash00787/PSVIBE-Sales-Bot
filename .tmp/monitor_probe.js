const { Client } = require('ssh2');
const fs = require('fs');
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

function run(cmd) {
  return new Promise((resolve, reject) => {
    const c = new Client();
    c.on('ready', () => {
      c.exec(cmd, (err, stream) => {
        if (err) { c.end(); reject(err); }
        let o = '', e = '';
        stream.on('data', d => o += d.toString());
        stream.stderr.on('data', d => e += d.toString());
        stream.on('close', code => { c.end(); resolve({ stdout: o, stderr: e, code }); });
      });
    });
    c.on('error', reject);
    c.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: KEY });
  });
}

async function main() {
  const cmds = [
    'ls -la /root/monitoring/ 2>&1',
    'find /root -maxdepth 2 -name "*monitor*" -o -name "*alert*" -o -name "*health*" 2>/dev/null | head -20',
    'ls -la /root/coordination/ 2>&1 | head -30',
    'systemctl list-units --type=service --state=running | grep -i monitor 2>&1',
  ];
  
  for (const cmd of cmds) {
    console.log(`\n=== ${cmd} ===`);
    const r = await run(cmd);
    console.log(r.stdout.trim());
    if (r.stderr) console.error('STDERR:', r.stderr.trim());
  }
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
