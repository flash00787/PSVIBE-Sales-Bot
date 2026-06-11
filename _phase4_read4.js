#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Read first 100 lines of members.py
  'head -100 /root/psvibe-sales-bot/bot/handlers/members.py',
  // Read last 100 lines of members.py
  'tail -100 /root/psvibe-sales-bot/bot/handlers/members.py',
  // Read booking_flow.py first 100 lines
  'head -100 /root/psvibe-sales-bot/bot/handlers/booking_flow.py',
  // Check for the actual topup function
  `python3 -c "
import ast, sys
with open('/root/psvibe-sales-bot/bot/handlers/members.py') as f:
    tree = ast.parse(f.read())
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        print(f'{node.lineno}: def {node.name}()')
" | head -50`,
  // Check console_booking table
  `docker exec psvibe-mysql mysql -upsvibe_user -p"$(grep MYSQL_PASSWORD /root/psvibe-sales-bot/.env | cut -d= -f2)" psvibe_api -e "SHOW TABLES;" 2>&1`,
];

let idx = 0;
function runNext() {
  if (idx >= commands.length) { conn.end(); process.exit(0); }
  const cmd = commands[idx++];
  console.log(`\n=== CMD ${idx} ===`);
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('ERR:', err); runNext(); return; }
    let out = '';
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { out += d.toString(); });
    stream.on('close', () => { console.log(out); runNext(); });
  });
}

conn.on('ready', runNext);
conn.on('error', e => { console.error('SSH ERR:', e.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 30000 });
