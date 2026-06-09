const { Client } = require('ssh2');
const fs = require('fs');
const privateKey = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

function sshExec(commands) {
  return new Promise((resolve, reject) => {
    const conn = new Client();
    let output = '';
    conn.on('ready', () => {
      const cmdStr = Array.isArray(commands) ? commands.join(' && ') : commands;
      conn.exec(cmdStr, (err, stream) => {
        if (err) { conn.end(); reject(err); return; }
        stream.on('data', (d) => { output += d.toString(); });
        stream.stderr.on('data', (d) => { output += d.toString(); });
        stream.on('close', () => { conn.end(); resolve(output); });
      });
    });
    conn.on('error', reject);
    conn.connect({ host: '167.71.196.120', port: 22, username: 'root', privateKey });
  });
}

async function main() {
  console.log('=== Fixing console.py ===');
  console.log(await sshExec(
    `python3 -c "
c = open('/root/staging/bot_src/bot/handlers/console.py').read()
if c.startswith('from bot import *'):
    c = c.replace('from bot import *', '', 1)
    idx = c.find('from datetime import')
    eol = c.find('\\n', idx)
    eol2 = c.find('\\n', eol + 1)
    c = c[:eol2+1] + 'from bot import *\\n' + c[eol2+1:]
if 'import asyncio' not in c:
    c = c.replace('import logging, re, json', 'import asyncio, logging, re, json')
open('/root/staging/bot_src/bot/handlers/console.py','w').write(c)
print('OK')
"
`));

  console.log('=== Fixing console_mgmt.py ===');
  console.log(await sshExec(
    `python3 -c "
c = open('/root/staging/bot_src/bot/handlers/console_mgmt.py').read()
if 'from bot import *' not in c:
    c = c.replace('from datetime import datetime, timezone, timedelta', 'from datetime import datetime, timezone, timedelta\\nfrom bot import *')
open('/root/staging/bot_src/bot/handlers/console_mgmt.py','w').write(c)
print('OK')
"
`));

  console.log('=== Fixing games.py ===');
  console.log(await sshExec(
    `python3 -c "
c = open('/root/staging/bot_src/bot/handlers/games.py').read()
if 'from bot import *' not in c:
    c = c.replace('from datetime import datetime, timezone, timedelta', 'from datetime import datetime, timezone, timedelta\\nfrom bot import *')
open('/root/staging/bot_src/bot/handlers/games.py','w').write(c)
print('OK')
"
`));

  console.log('=== Fixing ginst.py ===');
  console.log(await sshExec(
    `python3 -c "
c = open('/root/staging/bot_src/bot/handlers/ginst.py').read()
if 'from bot import *' not in c:
    c = c.replace('from datetime import datetime, timezone, timedelta', 'from datetime import datetime, timezone, timedelta\\nfrom bot import *')
if 'import asyncio' not in c:
    c = c.replace('import logging, re, json', 'import asyncio, logging, re, json')
open('/root/staging/bot_src/bot/handlers/ginst.py','w').write(c)
print('OK')
"
`));

  // Verify
  console.log('=== Verification ===');
  console.log(await sshExec("grep -n 'from bot import' /root/staging/bot_src/bot/handlers/console.py /root/staging/bot_src/bot/handlers/console_mgmt.py /root/staging/bot_src/bot/handlers/games.py /root/staging/bot_src/bot/handlers/ginst.py"));
  console.log(await sshExec("grep -n 'import asyncio' /root/staging/bot_src/bot/handlers/console.py /root/staging/bot_src/bot/handlers/ginst.py"));
}

main().catch(console.error);
