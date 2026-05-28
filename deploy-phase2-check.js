const { Client } = require('ssh2');
const fs = require('fs');

const HOST = '5.223.81.16';
const PRIVATE_KEY = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');
const TARGET = '/root/Sales-Tele-Bot_refactored';

async function main() {
  const conn = new Client();
  await new Promise((res, rej) => {
    conn.on('ready', res);
    conn.on('error', rej);
    conn.connect({ host: HOST, port: 22, username: 'root', privateKey: PRIVATE_KEY, readyTimeout: 30000 });
  });
  console.log('SSH connected');

  const exec = (cmd) => new Promise((res, rej) => {
    console.log(`\n>>> ${cmd.slice(0, 100)}`);
    conn.exec(cmd, (err, stream) => {
      if (err) { rej(err); return; }
      let out = '';
      stream.on('data', d => { out += d.toString(); process.stdout.write(d.toString()); });
      stream.stderr.on('data', d => { process.stderr.write('E:'+d); out += d.toString(); });
      stream.on('close', code => {
        if (code === 0) res(out);
        else rej(new Error(`${cmd.slice(0,40)} exit ${code}: ${out}`));
      });
    });
  });

  // Check imports in all py files
  await exec(`grep -rh "^import\|^from" ${TARGET}/main.py ${TARGET}/bot/ ${TARGET}/handlers/ 2>/dev/null | sort -u | head -80`);

  // Check old bot's requirements
  await exec(`ls /root/Sales-Tele-Bot/requirements*.txt 2>&1; cat /root/Sales-Tele-Bot/requirements*.txt 2>&1 | head -50`);

  // Check if venv exists anywhere
  await exec(`find /root -maxdepth 3 -name 'activate' -path '*/bin/activate' 2>/dev/null | head -5`);

  // Check pip packages
  await exec(`pip3 list 2>&1 | head -30`);

  // Check .env for needed vars
  await exec(`cat ${TARGET}/.env`);

  conn.end();
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
