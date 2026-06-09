const { Client } = require('ssh2');
const fs = require('fs');
const KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa', 'utf8');

function run(cmd) {
  return new Promise((resolve, reject) => {
    const c = new Client();
    c.on('ready', () => {
      c.exec(cmd, (err, stream) => {
        if (err) { c.end(); reject(err); }
        let o='', e='';
        stream.on('data', d => o+=d.toString());
        stream.stderr.on('data', d => e+=d.toString());
        stream.on('close', code => { c.end(); resolve({stdout:o,stderr:e,code}); });
      });
    });
    c.on('error', reject);
    c.connect({host:'5.223.81.16',port:22,username:'root',privateKey:KEY});
  });
}

async function main() {
  const cmds = JSON.parse(process.argv[2]);
  for (const c of cmds) {
    console.log('---CMD:', c.slice(0,80).replace(/\n/g,' '), '---');
    const r = await run(c);
    if (r.stdout) console.log(r.stdout.trim());
    if (r.stderr) console.error('STDERR:', r.stderr.trim());
    console.log('EXIT:', r.code);
  }
}
main().catch(e => { console.error(e.message); process.exit(1); });
