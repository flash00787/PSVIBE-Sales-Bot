const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const LOG = '/tmp/fix_console_mgmt.txt';

// Clear log
fs.writeFileSync(LOG, '');

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
    // Step 1: Read current console_mgmt.py
    log('=== STEP 1: Read current console_mgmt.py ===');
    let r = await execCmd('cd /root/psvibe-sales-bot && head -40 bot/handlers/console_mgmt.py');
    log('STDOUT:' + r.stdout);
    if (r.stderr) log('STDERR:' + r.stderr);

    log('=== Read full file (line count + grep for bot imports) ===');
    r = await execCmd('cd /root/psvibe-sales-bot && wc -l bot/handlers/console_mgmt.py && grep -n "from bot import\|from bot\." bot/handlers/console_mgmt.py');
    log('STDOUT:' + r.stdout);
    if (r.stderr) log('STDERR:' + r.stderr);

    // Show all lines that reference b, existing, i, lines, mult, n
    log('=== All lines referencing bot globals ===');
    r = await execCmd("cd /root/psvibe-sales-bot && grep -n '\\bb\\b\\|\\bexisting\\b\\|\\bi\\b\\|\\blines\\b\\|\\bmult\\b\\|\\bn\\b' bot/handlers/console_mgmt.py | head -60");
    log('STDOUT:' + r.stdout);
    if (r.stderr) log('STDERR:' + r.stderr);

  } catch(e) {
    log('ERROR: ' + e.message);
  }
  conn.end();
  log('Done - SSH session closed');
});

conn.on('error', e => log('SSH error: ' + e.message));

conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa')
});
