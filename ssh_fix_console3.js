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
    // Check Python version
    log('=== Python version ===');
    let r = await execCmd('python3 --version');
    log(r.stdout);

    // Check if __getattr__ works for modules (3.7+)
    r = await execCmd('python3 -c "import sys; print(sys.version_info)"');
    log(r.stdout);

    // Show exact line 9
    log('=== Line 9 exactly ===');
    r = await execCmd("cd /root/psvibe-sales-bot && sed -n '8,12p' bot/handlers/console_mgmt.py");
    log(r.stdout);

    // Confirm the real circular import chain
    log('=== Test: import handlers/__init__ ===');
    r = await execCmd('cd /root/psvibe-sales-bot && python3 -c "import bot.handlers" 2>&1');
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
