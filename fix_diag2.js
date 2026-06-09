const { Client } = require('ssh2');
const fs = require('fs'), path = require('path');

function sshExec(conn, cmd) {
  return new Promise((resolve, reject) => {
    console.log(`\n>>> ${cmd.substring(0, 200)}`);
    conn.exec(cmd, { pty: true }, (err, stream) => {
      if (err) return reject(err);
      let o = '', e = '';
      stream.on('data', d => { o += d.toString(); });
      stream.stderr.on('data', d => { e += d.toString(); });
      stream.on('close', (code) => {
        const out = (o + e).trim();
        console.log(out.substring(0, 5000));
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
  console.log('=== Diagnosing handler circular imports ===');

  try {
    // Check handlers/__init__.py
    await sshExec(conn, 'cd /root/psvibe-sales-bot && cat -n bot/handlers/__init__.py');
    
    // Check which handler files import from bot at module level
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -rn '^from bot import' bot/handlers/ | head -30`);
    
    // Check attendance.py import line
    await sshExec(conn, 'cd /root/psvibe-sales-bot && head -5 bot/handlers/attendance.py');
    
    // Check if handlers import was always at end of __init__.py (look at git history)
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git log --oneline -10');
    
    // Check what ee61e89 changed
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git show ee61e89 --stat 2>&1 | head -20');
    
    // Check how main.py imports things
    await sshExec(conn, 'cd /root/psvibe-sales-bot && head -20 main.py');
    
    // The KEY fix: move `from bot.handlers import *` OUT of __init__.py into main.py
    // But first check if main.py already imports handlers
    await sshExec(conn, 'cd /root/psvibe-sales-bot && grep "handlers" main.py');
    
    // Check where `amt` is defined in __init__.py
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -n '^amt\\b' bot/__init__.py`);
    
    // Check where handlers are called from
    await sshExec(conn, `cd /root/psvibe-sales-bot && grep -rn 'from bot.handlers' --include='*.py' | head -20`);
    
  } finally {
    conn.end();
    console.log('\n=== DIAGNOSIS COMPLETE ===');
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
