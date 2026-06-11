#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Read exact import area (lines 1-30)
  'sed -n "1,30p" /root/psvibe-sales-bot/bot/handlers/members.py',
  // Read lines 1378-1395 (around get_receipt_kb area)
  'sed -n "1378,1420p" /root/psvibe-sales-bot/bot/handlers/members.py',
  // Check that STAFF_NOTIFY_CHAT is in bot __init__.py
  'grep "STAFF_NOTIFY_CHAT" /root/psvibe-sales-bot/bot/__init__.py',
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
