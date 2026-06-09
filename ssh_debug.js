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
    // Show the full file
    log('=== Full fixed console_mgmt.py ===');
    let r = await execCmd('cd /root/psvibe-sales-bot && cat -n bot/handlers/console_mgmt.py');
    log(r.stdout);

    // Test: Is step_con_mgmt_menu in dict?
    log('=== Test: step_con_mgmt_menu in dict ===');
    r = await execCmd(`cd /root/psvibe-sales-bot && set -a && source /etc/psvibe/secrets.env && python3 -c "
import bot.handlers.console_mgmt as cm
print('step_con_mgmt_menu in __dict__:', 'step_con_mgmt_menu' in cm.__dict__)
print('show_con_mgmt_menu in __dict__:', 'show_con_mgmt_menu' in cm.__dict__)
print('CON_MGMT_MENU in __dict__:', 'CON_MGMT_MENU' in cm.__dict__)
print('CON_ADD_ID in __dict__:', 'CON_ADD_ID' in cm.__dict__)
print('BTN_BACK in __dict__:', 'BTN_BACK' in cm.__dict__)
# Try accessing
print()
print('Access step_con_mgmt_menu:', cm.step_con_mgmt_menu)
print('Access CON_MGMT_MENU:', cm.CON_MGMT_MENU)
print()
# Check __all__
print('__all__:', cm.__all__ if hasattr(cm, '__all__') else 'NOT SET')
" 2>&1`);
    log('STDOUT:' + r.stdout);
    log('STDERR:' + r.stderr);

    // Test: from console_mgmt import *
    log('=== Test: from console_mgmt import * ===');
    r = await execCmd(`cd /root/psvibe-sales-bot && set -a && source /etc/psvibe/secrets.env && python3 -c "
from bot.handlers.console_mgmt import *
print('step_con_mgmt_menu:', step_con_mgmt_menu)
print('show_con_mgmt_menu:', show_con_mgmt_menu)
print('CON_MGMT_MENU:', CON_MGMT_MENU)
print('CON_ADD_ID:', CON_ADD_ID)
print('BTN_BACK:', BTN_BACK)
print('get_consoles_from_setting:', get_consoles_from_setting)
" 2>&1`);
    log('STDOUT:' + r.stdout);
    log('STDERR:' + r.stderr);

    // Test: what does bot.handlers export?
    log('=== Test: bot.handlers names ===');
    r = await execCmd(`cd /root/psvibe-sales-bot && set -a && source /etc/psvibe/secrets.env && python3 -c "
import bot.handlers as bh
print('step_con_mgmt_menu in handlers:', hasattr(bh, 'step_con_mgmt_menu'))
print('CON_MGMT_MENU in handlers:', hasattr(bh, 'CON_MGMT_MENU'))
# Try from bot.handlers import step_con_mgmt_menu
from bot.handlers import step_con_mgmt_menu
print('imported step_con_mgmt_menu:', step_con_mgmt_menu)
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
