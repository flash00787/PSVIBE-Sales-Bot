const { Client } = require('ssh2');
const fs = require('fs'), path = require('path');

function ss(cmd) { return cmd.substring(0, 180); }
function sshExec(conn, cmd) {
  return new Promise((resolve, reject) => {
    console.log(`\n>>> ${ss(cmd)}`);
    conn.exec(cmd, { pty: true }, (err, stream) => {
      if (err) return reject(err);
      let o = '', e = '';
      stream.on('data', d => { o += d.toString(); });
      stream.stderr.on('data', d => { e += d.toString(); });
      stream.on('close', (code) => {
        const out = (o + e).trim();
        console.log(out.substring(0, 3000));
        resolve({ code, out });
      });
    });
  });
}

async function main() {
  const conn = new Client();
  await new Promise((r, x) => { conn.on('ready', r); conn.on('error', x); conn.connect({
    host: '5.223.81.16', port: 22, username: 'root',
    privateKey: fs.readFileSync(path.resolve('/home/node/.openclaw/workspace/.ssh/id_rsa')),
    readyTimeout: 15000,
  });});
  console.log('=== SSH CONNECTED ===');

  try {
    // STEP 1: Check current state
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git log --oneline -3');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git status');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && wc -l bot/constants.py bot/helpers.py bot/__init__.py');

    // STEP 2: Check what each file looks like
    await sshExec(conn, 'cd /root/psvibe-sales-bot && sed -n "1,10p" bot/constants.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && sed -n "1,10p" bot/helpers.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && sed -n "128,145p" bot/__init__.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && grep -n "from bot\\.\" bot/__init__.py');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && grep -n "from bot.handlers\|from bot.app\|from bot.constants\|from bot.helpers" bot/__init__.py');

    // STEP 3: Check if helpers.py re-defines names it imports from bot
    await sshExec(conn, 'cd /root/psvibe-sales-bot && grep -n "^def \|^def now\|^def today\|^def step" bot/helpers.py');
    
    // STEP 4: See what BOT_VERSION, MMT etc are and where they are in __init__.py
    await sshExec(conn, 'cd /root/psvibe-sales-bot && grep -n "^BOT_VERSION\|^MMT\|^RECEIPTS_DIR\|^now_mmt\|^today_str\|^now =" bot/__init__.py | head -20');

    // STEP 5: Check full helpers.py to understand what it imports vs defines
    await sshExec(conn, 'cd /root/psvibe-sales-bot && cat -n bot/helpers.py');
  } finally {
    conn.end();
    console.log('\n=== DONE ===');
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
