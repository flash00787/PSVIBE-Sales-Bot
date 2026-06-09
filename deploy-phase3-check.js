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

  // Find where the 'main' function is defined
  await execOk(`grep -n "^async def main\|^def main" ${TARGET}/bot/app.py ${TARGET}/bot/__init__.py ${TARGET}/main.py 2>/dev/null`);

  // Check main.py completely
  await execOk(`cat ${TARGET}/main.py`);

  // Check what keep_alive module exists
  await execOk(`find ${TARGET} -name 'keep_alive*' -type f 2>/dev/null; grep -r "def main" ${TARGET}/bot/ --include='*.py' -l`);

  // Check bot/app.py for main function definition
  await execOk(`grep -n "async def main\|def main\|def run\|if __name__" ${TARGET}/bot/app.py | head -20`);

  // Also check app.py at target root
  await execOk(`grep -n "async def main\|def main\|def run\|if __name__" ${TARGET}/app.py | head -20`);

  conn.end();
  console.log('\nDone checking');
}

main().catch(e => { console.error('FATAL:', e); process.exit(1); });
