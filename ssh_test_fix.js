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
    // First, find the env vars needed
    log('=== Find env vars ===');
    let r = await execCmd('cat /etc/systemd/system/psvibe-sale-bot.service 2>/dev/null || cat /etc/systemd/system/psvibe*.service 2>/dev/null | head -20');
    log(r.stdout);
    if (r.stderr) log('STDERR:' + r.stderr);

    // Read Environment from systemd
    r = await execCmd("grep -A 20 '\\[Service\\]' /etc/systemd/system/psvibe-sale-bot.service 2>/dev/null");
    log('Service env:' + r.stdout);

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
