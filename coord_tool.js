#!/usr/bin/env node
/**
 * coord_tool.js — Run VPS coordination tools via SSH
 * Usage: node coord_tool.js <tool_name> [args...]
 * Example: node coord_tool.js check_alerts.py
 *          node coord_tool.js notifier.py list --unread
 *          node coord_tool.js queue_manager.py --dead-letter
 */
const { Client } = require('ssh2');
const fs = require('fs');

const args = process.argv.slice(2);
if (args.length === 0) {
  console.log("Usage: node coord_tool.js <tool_name> [args...]");
  console.log("Available tools:");
  console.log("  check_alerts.py    — Check service health alerts");
  console.log("  notifier.py        — Read/send notifications");
  console.log("  queue_manager.py   — Manage task queue");
  console.log("  task_bridge.py     — Bridge pending tasks");
  console.log("  status_reporter.py — System health report");
  console.log("  auto_doc_updater.py— Auto documentation");
  console.log("  git_sync_agent.py  — Git sync operations");
  process.exit(1);
}

const toolName = args[0];
const toolArgs = args.slice(1).join(' ');
const cmd = `cd /root/coordination && python3 ${toolName} ${toolArgs}`;

const conn = new Client();
conn.on('ready', () => {
  conn.exec(cmd, (err, stream) => {
    if (err) { console.error('EXEC_ERROR:', err.message); conn.end(); process.exit(1); return; }
    let out = '';
    stream.on('data', d => { out += d.toString(); });
    stream.stderr.on('data', d => { out += 'STDERR:' + d.toString(); });
    stream.on('close', (code) => {
      console.log(out.trimEnd());
      conn.end();
      process.exit(code || 0);
    });
  });
});
conn.on('error', (e) => { console.error('SSH_ERROR:', e.message); process.exit(1); });
conn.connect({
  host: '5.223.81.16',
  port: 22,
  username: 'root',
  privateKey: fs.readFileSync('/home/node/.openclaw/workspace/.ssh/id_rsa'),
  readyTimeout: 15000,
});
