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

  // Find 'def main' in bot/app.py
  await execOk(`grep -n "def main" ${TARGET}/bot/app.py`);

  // Find keep_alive module  
  await execOk(`grep -rn "def keep_alive\|def main" ${TARGET}/bot/ --include='*.py'`);

  // Check for keep_alive.py in the bot dir
  await execOk(`find ${TARGET} -name 'keep_alive*'`);

  // Look at end of bot/app.py for main function
  await execOk(`tail -80 ${TARGET}/bot/app.py`);

  conn.end();
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
