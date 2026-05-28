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

  const execOk = (cmd) => new Promise((res) => {
    console.log(`\n>>> ${cmd.slice(0, 120)}`);
    conn.exec(cmd, (err, stream) => {
      if (err) { console.error('exec err:', err); res(''); return; }
      let out = '';
      stream.on('data', d => { out += d.toString(); process.stdout.write(d.toString()); });
      stream.stderr.on('data', d => { process.stderr.write('E:'+d); out += d.toString(); });
      stream.on('close', () => res(out));
    });
  });

  // Check imports
  await execOk(`grep -rn "^import\|^from" ${TARGET}/main.py ${TARGET}/bot/app.py ${TARGET}/bot/__init__.py 2>/dev/null; echo "---"; head -100 ${TARGET}/bot/__init__.py`);
  await execOk(`head -30 ${TARGET}/bot/app.py`);

  // Install deps - upgrade pip first
  await execOk(`/root/venv/bin/pip install --upgrade pip 2>&1 | tail -5`);
  await execOk(`/root/venv/bin/pip install python-telegram-bot==22.7 gspread==6.2.1 oauth2client==4.1.3 Flask==3.1.3 google-genai python-dotenv aiohttp 2>&1 | tail -30`);

  // Verify
  await execOk(`/root/venv/bin/pip list 2>/dev/null | grep -iE "telegram|gspread|flask|google|oauth|aiohttp|requests|dotenv"`);

  conn.end();
  console.log('\n=== Phase 2 complete ===');
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
