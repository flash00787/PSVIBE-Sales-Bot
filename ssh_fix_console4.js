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
    // Check handlers/__init__.py
    log('=== handlers/__init__.py ===');
    let r = await execCmd('cat /root/psvibe-sales-bot/bot/handlers/__init__.py');
    log(r.stdout);

    // Also check what bot/__init__.py does around line 2558
    log('=== bot/__init__.py around line 2558 ===');
    r = await execCmd("cd /root/psvibe-sales-bot && sed -n '2550,2570p' bot/__init__.py");
    log(r.stdout);

    // Check if there's an __all__ in console_mgmt.py
    log('=== console_mgmt.py __all__ ===');
    r = await execCmd("cd /root/psvibe-sales-bot && grep -n '__all__' bot/handlers/console_mgmt.py");
    log(r.stdout);

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
