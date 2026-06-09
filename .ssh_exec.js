const { Client } = require('ssh2');
const fs = require('fs');
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

function run(cmd, opts = {}) {
  return new Promise((resolve, reject) => {
    const c = new Client();
    c.on('ready', () => {
      c.exec(cmd, opts, (err, stream) => {
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
  const script = process.argv[2];
  const r = await run(script, {});
  if (r.stdout) process.stdout.write(r.stdout);
  if (r.stderr) process.stderr.write(r.stderr);
  process.exit(r.code || 0);
}
main().catch(e => { console.error(e.message); process.exit(1); });
