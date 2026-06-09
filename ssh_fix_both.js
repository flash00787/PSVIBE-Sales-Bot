const { Client } = require('ssh2');
const fs = require('fs');
const path = require('path');

const HOST = '5.223.81.16';
const USER = 'root';
const KEY_PATH = path.join(__dirname, '.ssh', 'id_rsa');

async function sshExec(command, timeout = 60000) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let output = '';
    let errOutput = '';
    let timer = setTimeout(() => {
      conn.end();
      reject(new Error(`Timeout after ${timeout}ms: ${command.substring(0,100)}`));
    }, timeout);

    conn.on('ready', () => {
      conn.exec(command, (err, stream) => {
        if (err) {
          clearTimeout(timer);
          conn.end();
          return reject(err);
        }
        stream.on('close', (code, signal) => {
          clearTimeout(timer);
          conn.end();
          resolve({ code, stdout: output, stderr: errOutput });
        }).on('data', (data) => { output += data.toString(); })
          .stderr.on('data', (data) => { errOutput += data.toString(); });
      });
    });

    conn.on('error', (err) => {
      clearTimeout(timer);
      reject(err);
    });

    conn.connect({
      host: HOST,
      port: 22,
      username: USER,
      privateKey: fs.readFileSync(KEY_PATH),
      readyTimeout: 15000,
    });
  });
}

async function runFixes() {
  // Fix 1: Python to fix regex
  const fixRegexPy = `python3 -c "
import re
with open('/root/psvibe_api_server/dashboard_routes.py', 'r') as f:
    content = f.read()
old = 'm = re.match(r\\\"([^:]+):s*([d.]+)\\\", part)'
new = 'm = re.match(r\\\"([^:]+):\\\\\\\\s*([\\\\\\\\d.]+)\\\", part)'
if old in content:
    content = content.replace(old, new)
    with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
        f.write(content)
    print('REGEX FIXED')
else:
    print('OLD PATTERN NOT FOUND - searching...')
    for i, line in enumerate(content.split(chr(10)), 1):
        if 're.match' in line:
            print(f'Line {i}: {line}')
"`;

  // Fix 2: Python to fix Vue file
  const fixVuePy = `python3 -c "
with open('/root/psvibe-dashboard/src/views/FinanceBalance.vue', 'r') as f:
    content = f.read()
old_div = '<div class=\\\"min-h-screen bg-gray-50 dark:bg-gray-900 p-4 lg:p-6\\\">'
new_div = '<div class=\\\"p-4 lg:p-6\\\">'
if old_div in content:
    content = content.replace(old_div, new_div)
    with open('/root/psvibe-dashboard/src/views/FinanceBalance.vue', 'w') as f:
        f.write(content)
    print('VUE FIXED')
else:
    print('OLD DIV NOT FOUND')
    for i, line in enumerate(content.split(chr(10)), 1):
        if 'min-h-screen' in line:
            print(f'Line {i}: {line.strip()[:120]}')
"`;

  const commands = [
    { label: 'FIX 1: Regex fix', cmd: fixRegexPy },
    { label: 'FIX 2: Vue fix', cmd: fixVuePy },
    { label: 'VERIFY 1: Check regex', cmd: 'grep -n "re.match" /root/psvibe_api_server/dashboard_routes.py' },
    { label: 'VERIFY 2: Check Vue', cmd: 'grep -n "min-h-screen\|class=\\"p-4" /root/psvibe-dashboard/src/views/FinanceBalance.vue' },
  ];

  for (const { label, cmd } of commands) {
    console.log(`\n=== ${label} ===`);
    try {
      const r = await sshExec(cmd, 30000);
      console.log(`Exit: ${r.code}`);
      console.log(r.stdout);
      if (r.stderr) console.log('STDERR:', r.stderr);
    } catch (e) {
      console.log(`ERROR: ${e.message}`);
    }
  }
}

runFixes().catch(e => console.error('FATAL:', e));
