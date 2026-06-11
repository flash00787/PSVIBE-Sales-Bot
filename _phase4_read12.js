#!/usr/bin/env node
const { Client } = require('ssh2');
const fs = require('fs');

const conn = new Client();
const pk = fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa');

const commands = [
  // Check bot __init__.py exports
  'grep "STAFF_NOTIFY_CHAT" /root/psvibe-sales-bot/bot/__init__.py | head -5',
  // Check how the service is managed
  'cat /etc/systemd/system/psvibe-sale-bot.service 2>/dev/null | head -20',
  // Check Python version
  'python3 --version 2>&1',
  // Check pip packages available
  'python3 -c "import mysql.connector; print(mysql.connector.__version__)" 2>&1 || python3 -c "import pymysql; print(pymysql.__version__)" 2>&1 || echo "No mysql connector found"',
  // Verify the import path for STAFF_NOTIFY_CHAT
  'python3 -c "import sys; sys.path.insert(0,\"/root/psvibe-sales-bot\"); from bot import STAFF_NOTIFY_CHAT; print(STAFF_NOTIFY_CHAT)" 2>&1',
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
    stream.on('close', () => { console.log(out.substring(0, 4000)); runNext(); });
  });
}

conn.on('ready', runNext);
conn.on('error', e => { console.error('SSH ERR:', e.message); process.exit(1); });
conn.connect({ host: '5.223.81.16', port: 22, username: 'root', privateKey: pk, readyTimeout: 30000 });
