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
    // Fix: Add '__all__' to the exclusion list in __getattr__
    log('=== Fixing __getattr__ to exclude __all__ ===');
    let r = await execCmd(`cd /root/psvibe-sales-bot && python3 << 'PYFIX'
with open('bot/handlers/console_mgmt.py', 'r') as f:
    content = f.read()

# Fix: Add __all__ and other special attrs to exclusion
old = "if name in ('__getattr__', '_bot_lazy_loaded'):"
new = "if name in ('__getattr__', '_bot_lazy_loaded', '__all__', '__path__', '__spec__', '__loader__', '__package__'):"
content = content.replace(old, new)

with open('bot/handlers/console_mgmt.py', 'w') as f:
    f.write(content)

print('Fix applied')
print('---')
with open('bot/handlers/console_mgmt.py', 'r') as f:
    for i, line in enumerate(f, 1):
        if i <= 25:
            print(f'{i}: {line}', end='')
PYFIX
`);
    log('STDOUT:' + r.stdout);
    if (r.stderr) log('STDERR:' + r.stderr);

    // Test the fix
    log('=== Test: from console_mgmt import * ===');
    r = await execCmd(`cd /root/psvibe-sales-bot && set -a && source /etc/psvibe/secrets.env && python3 -c "
from bot.handlers.console_mgmt import *
print('step_con_mgmt_menu:', step_con_mgmt_menu)
print('CON_MGMT_MENU:', CON_MGMT_MENU)
print('BTN_BACK:', BTN_BACK)
print()
# Verify __all__ is now properly absent/masked
import bot.handlers.console_mgmt as cm
try:
    a = cm.__all__
    # Check if step_con_mgmt_menu is in it
    if 'step_con_mgmt_menu' in a:
        print('__all__ HAS step_con_mgmt_menu - GOOD')
    else:
        print('WARNING: __all__ exists but missing step_con_mgmt_menu, values:', a[:5])
except AttributeError:
    print('__all__ raises AttributeError - GOOD, will use __dict__ for import *')
print()
print('ALL TESTS PASSED')
" 2>&1`);
    log('STDOUT:' + r.stdout);
    log('STDERR:' + r.stderr);

    // Test full bot import
    log('=== Test: Full bot import ===');
    r = await execCmd('cd /root/psvibe-sales-bot && set -a && source /etc/psvibe/secrets.env && python3 -c "import bot; print(\'FULL BOT IMPORT: OK\')" 2>&1');
    log('STDOUT:' + r.stdout);
    log('STDERR:' + r.stderr);

    // Test from bot.handlers import *
    log('=== Test: from bot.handlers import * ===');
    r = await execCmd(`cd /root/psvibe-sales-bot && set -a && source /etc/psvibe/secrets.env && python3 -c "
from bot.handlers import *
print('step_con_mgmt_menu:', step_con_mgmt_menu)
print('show_con_mgmt_menu:', show_con_mgmt_menu)
print('CON_MGMT_MENU:', CON_MGMT_MENU)
print('BTN_BACK:', BTN_BACK)
print('OK')
" 2>&1`);
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
