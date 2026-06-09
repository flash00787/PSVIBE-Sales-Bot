const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const LOG = '/tmp/fix_console_mgmt.txt';

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  fs.appendFileSync(LOG, line + '\n');
}

function execCmd(cmd) {
  return new Promise((resolve, reject) => {
    let stdout = '', stderr = '';
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      stream.on('data', d => stdout += d.toString());
      stream.stderr.on('data', d => stderr += d.toString());
      stream.on('close', code => resolve({ code, stdout, stderr }));
    });
  });
}

conn.on('ready', async () => {
  log('SSH connected');
  try {
    // Read full console_mgmt.py
    log('=== Full console_mgmt.py ===');
    let r = await execCmd('cat /root/psvibe-sales-bot/bot/handlers/console_mgmt.py');
    log(r.stdout);
    if (r.stderr) log('STDERR:' + r.stderr);

    // Also check what bot/__init__.py exports (the * items)
    log('=== bot/__init__.py __all__ or top-level symbols ===');
    r = await execCmd('cd /root/psvibe-sales-bot && grep -n "__all__" bot/__init__.py | head -5');
    log(r.stdout);
    
    // Check current state - does bot import fail?
    log('=== Current bot import test ===');
    r = await execCmd('cd /root/psvibe-sales-bot && python3 -c "import bot; print(\'BOT OK\')" 2>&1');
    log('STDOUT:' + r.stdout);
    log('STDERR:' + r.stderr);

  } catch(e) {
    log('ERROR: ' + e.message);
  }
  conn.end();
});

conn.on('error', e => log('SSH error: ' + e.message));
conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
