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
        console.log(out.substring(0, 6000));
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
  console.log('=== DIAGNOSIS: Why did c729a08 work but current fails? ===');

  try {
    // Check what changed in attendance.py between c729a08 and HEAD
    console.log('\n--- attendance.py diff c729a08..HEAD ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git diff c729a08 HEAD -- bot/handlers/attendance.py 2>&1');
    
    // Check c729a08's attendance.py line 1
    console.log('\n--- c729a08 attendance.py line 1 ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git show c729a08:bot/handlers/attendance.py | head -3');
    
    // Check current attendance.py line 1
    console.log('\n--- Current attendance.py line 1 ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && head -3 bot/handlers/attendance.py');
    
    // Check if amt is defined anywhere at module level in c729a08 vs current __init__.py
    console.log('\n--- c729a08 __init__.py grep amt ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git show c729a08:bot/__init__.py | grep -n "^amt\\b\\|amt =" | head -10');
    
    console.log('\n--- Current __init__.py grep amt ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && grep -n "^amt\\b\\|amt =" bot/__init__.py | head -10');
    
    // Full ee61e89 diff for attendance
    console.log('\n--- ee61e89 attendance diff ---');
    await sshExec(conn, 'cd /root/psvibe-sales-bot && git show ee61e89 -- bot/handlers/attendance.py 2>&1 | head -30');
    
  } finally {
    conn.end();
    console.log('\n=== DONE ===');
  }
}

main().catch(err => { console.error('FATAL:', err.message); process.exit(1); });
