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
    console.log(`\n>>> ${cmd.slice(0, 120)}`);
    conn.exec(cmd, (err, stream) => {
      if (err) { rej(err); return; }
      let out = '';
      stream.on('data', d => { out += d.toString(); process.stdout.write(d.toString()); });
      stream.stderr.on('data', d => { process.stderr.write('E:'+d); out += d.toString(); });
      stream.on('close', code => {
        if (code === 0) res(out);
        else rej(new Error(`exit ${code}: ${out.slice(-200)}`));
      });
    });
  });

  // Check imports across refactored code
  await exec(`cd ${TARGET} && grep -rh "^import\|^from" *.py bot/ handlers/ 2>/dev/null | grep -v "^\s*#" | sort -u`);

  // Check if /root/venv has the packages needed
  await exec(`/root/venv/bin/pip list 2>/dev/null | grep -iE "telegram|gspread|flask|google|oauth|aiohttp|requests|dotenv"`);

  // Install missing packages into existing venv or system
  await exec(`/root/venv/bin/pip install python-telegram-bot==22.7 gspread==6.2.1 oauth2client==4.1.3 Flask==3.1.3 google-genai python-dotenv aiohttp 2>&1 | tail -20`);

  conn.end();
  console.log('\n=== Phase 2 complete ===');
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
