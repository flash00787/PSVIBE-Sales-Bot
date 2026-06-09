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
  // 1. Run the alert checker
  console.log('=== ALERT CHECK ===');
  const r1 = await run('bash /root/monitoring/check_alerts.sh');
  console.log('STDOUT:', r1.stdout.trim());
  if (r1.stderr) console.error('STDERR:', r1.stderr.trim());
  console.log('EXIT:', r1.code);
  
  // 2. Check last 3 lines of each log
  const logs = [
    '/root/monitoring/health.log',
    '/root/monitoring/resources.log',
    '/root/monitoring/ratelimit.log',
    '/root/monitoring/uptime.log'
  ];
  
  for (const log of logs) {
    console.log(`\n=== ${log} (last 3 lines) ===`);
    const r = await run(`tail -3 ${log} 2>&1`);
    console.log(r.stdout.trim() || '(empty or not found)');
    if (r.stderr) console.error('STDERR:', r.stderr.trim());
  }
}

main().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
