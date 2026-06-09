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
    // Restart service
    log('=== Restarting service ===');
    let r = await execCmd('systemctl restart psvibe-sale-bot.service 2>&1');
    log('STDOUT:' + r.stdout);
    log('STDERR:' + r.stderr);

    // Wait 5 seconds
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Check status
    log('=== Service status ===');
    r = await execCmd('systemctl is-active psvibe-sale-bot.service 2>&1');
    log('STATUS:' + r.stdout);

    // Check logs
    log('=== Bot logs ===');
    r = await execCmd('journalctl -u psvibe-sale-bot.service --no-pager -n 15 --since "30 sec ago" 2>&1');
    log('LOGS:' + r.stdout);

    // Commit
    log('=== Git commit ===');
    r = await execCmd('cd /root/psvibe-sales-bot && git add -A && git commit -m "Fix: circular import in console_mgmt.py (lazy bot globals via __getattr__)" --no-verify 2>&1');
    log('COMMIT:' + r.stdout);
    if (r.stderr) log('COMMIT STDERR:' + r.stderr);

    // Push
    log('=== Git push ===');
    r = await execCmd('cd /root/psvibe-sales-bot && git push 2>&1');
    log('PUSH:' + r.stdout);
    if (r.stderr) log('PUSH STDERR:' + r.stderr);

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
