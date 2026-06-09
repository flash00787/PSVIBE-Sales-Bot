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
    // Test 2: Import console_mgmt directly with env vars
    log('=== Test: Import bot.handlers.console_mgmt ===');
    let r = await execCmd('cd /root/psvibe-sales-bot && set -a && source /etc/psvibe/secrets.env && python3 -c "import bot.handlers.console_mgmt; print(\'CONSOLE_MGMT IMPORT: OK\')" 2>&1');
    log('STDOUT:' + r.stdout);
    log('STDERR:' + r.stderr);

    // Test 3: Import all handlers
    log('=== Test: Import all handlers ===');
    r = await execCmd(`cd /root/psvibe-sales-bot && set -a && source /etc/psvibe/secrets.env && python3 -c "
import bot.handlers.sales
import bot.handlers.booking
import bot.handlers.admin
import bot.handlers.members
import bot.handlers.stock
import bot.handlers.stock_in
import bot.handlers.finance
import bot.handlers.salary_adv
import bot.handlers.attendance
import bot.handlers.console_mgmt
print('ALL HANDLERS IMPORT: OK')
" 2>&1`);
    log('STDOUT:' + r.stdout);
    log('STDERR:' + r.stderr);

    // Test 4: Full bot import
    log('=== Test: Full bot import ===');
    r = await execCmd('cd /root/psvibe-sales-bot && set -a && source /etc/psvibe/secrets.env && python3 -c "import bot; print(\'FULL BOT IMPORT: OK\')" 2>&1');
    log('STDOUT:' + r.stdout);
    log('STDERR:' + r.stderr);

    // Test 5: Run tests
    log('=== Test: Pytest ===');
    r = await execCmd('cd /root/psvibe-sales-bot && set -a && source /etc/psvibe/secrets.env && python3 -m pytest tests/ -q 2>&1 | tail -10');
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
